"""AgentGov governance proxy (FastAPI).

The chokepoint. Every tool call is POSTed here; the proxy enriches it,
runs policy, enforces the decision, audits it, and (if allowed) simulates
execution and accounts for cost.

Run from project root:
    uvicorn proxy.app:app --reload --port 8000
"""
import random
import time

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from core.policy import PolicyEngine, Decision
from core.agents import get_agent
from core.audit import AuditEvent, write_event, add_spend, get_budget

app = FastAPI(title="AgentGov Proxy", version="0.1.0")

# Load policy once at startup. (Restart to pick up YAML edits — fine for POC.)
engine = PolicyEngine("policies/default.yaml")


class ToolCall(BaseModel):
    agent_id: str
    tool_name: str
    sensitivity: str
    args: Optional[dict] = None
    sim_cost_usd: float = 0.0


class ProxyResponse(BaseModel):
    decision: str
    reason: str
    executed: bool
    result: Optional[str] = None
    cost_charged: float
    audit_id: int
    budget_spent: float = 0.0
    budget_limit: float = 0.0


def simulate_execution(tool_name: str) -> tuple[str, int]:
    """Pretend to run the tool. Returns (result_text, latency_ms).
    Pure fiction — no real side effects, ever."""
    latency = random.randint(20, 400)
    time.sleep(latency / 1000 / 10)  # token nod to latency, sped up 10x
    return f"[simulated] {tool_name} completed", latency


@app.get("/health")
def health():
    return {"status": "ok", "service": "agentgov-proxy"}


@app.post("/proxy/tool-call", response_model=ProxyResponse)
def govern_tool_call(call: ToolCall) -> ProxyResponse:
    # 1. ENRICH — resolve the agent's team for policy
    agent = get_agent(call.agent_id)
    team = agent["team"] if agent else "UNKNOWN"

    request = {
        "agent_id": call.agent_id,
        "tool_name": call.tool_name,
        "sensitivity": call.sensitivity,
        "team": team,
    }

    # 2. DECIDE
    decision: Decision = engine.evaluate(request)

    # 2b. Unknown agents are denied regardless of policy outcome —
    #     you cannot govern what you can't identify.
    if agent is None:
        decision = Decision(action="deny", reason="unknown agent — not in registry")

    executed = False
    result = None
    cost_charged = 0.0
    latency = 0

    # 2c. BUDGET GATE — a policy 'allow' can still be denied on cost.
    #     Enforce at the moment of spend: would this call breach the ceiling?
    budget = get_budget(call.agent_id) or {"monthly_limit": 0.0, "spent": 0.0}
    if decision.action == "allow":
        projected = budget["spent"] + call.sim_cost_usd
        if projected > budget["monthly_limit"]:
            decision = Decision(
                action="deny",
                reason=(f"budget exceeded: spent {budget['spent']:.4f} "
                        f"+ {call.sim_cost_usd:.4f} > limit {budget['monthly_limit']:.2f}"),
            )

    # 3. ENFORCE — only a surviving 'allow' runs
    if decision.action == "allow":
        result, latency = simulate_execution(call.tool_name)
        executed = True
        cost_charged = call.sim_cost_usd

    # 4. AUDIT — always, whatever the decision
    audit_id = write_event(AuditEvent(
        agent_id=call.agent_id,
        tool_name=call.tool_name,
        decision=decision.action,
        reason=decision.reason,
        tool_args=call.args,
        cost_usd=cost_charged,
        latency_ms=latency,
    ))

    # 5. ACCOUNT — charge spend only if it executed
    if executed:
        add_spend(call.agent_id, cost_charged)

    # re-read spend so the response reflects the charge we just made
    final_budget = get_budget(call.agent_id) or {"monthly_limit": 0.0, "spent": 0.0}
    return ProxyResponse(
        decision=decision.action,
        reason=decision.reason,
        executed=executed,
        result=result,
        cost_charged=cost_charged,
        audit_id=audit_id,
        budget_spent=final_budget["spent"],
        budget_limit=final_budget["monthly_limit"],
    )