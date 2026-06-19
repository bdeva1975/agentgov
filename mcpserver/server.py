"""AgentGov-governed MCP server (FastMCP).

A real MCP server whose tools are governed by AgentGov: before each tool does
its (simulated) work, it asks the AgentGov proxy for a decision. Denied and
escalated calls do not execute. Fails closed if governance is unreachable.

Synthetic POC: tools simulate work; no real side effects.
Requires the AgentGov proxy running on :8000.
"""
import requests
from fastmcp import FastMCP

PROXY = "http://127.0.0.1:8000/proxy/tool-call"

mcp = FastMCP("AgentGov-Governed-Tools")


def _govern(agent_id, tool_name, sensitivity, args, sim_cost_usd=0.0):
    """Ask AgentGov for a decision. Returns (allowed: bool, payload: dict)."""
    try:
        resp = requests.post(PROXY, json={
            "agent_id": agent_id,
            "tool_name": tool_name,
            "sensitivity": sensitivity,
            "args": args,
            "sim_cost_usd": sim_cost_usd,
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["decision"] == "allow", data
    except Exception as e:
        # Fail closed: if governance is unreachable, deny.
        return False, {"decision": "deny", "reason": f"governance unreachable: {e}"}


@mcp.tool
def read_document(agent_id: str, doc_id: str) -> str:
    """Read a (synthetic) document. Low sensitivity."""
    allowed, d = _govern(agent_id, "read_document", "low", {"doc_id": doc_id}, 0.002)
    if not allowed:
        return f"BLOCKED by AgentGov [{d['decision']}]: {d['reason']}"
    return f"[simulated] contents of {doc_id}"


@mcp.tool
def send_email(agent_id: str, to: str, subject: str) -> str:
    """Send a (synthetic) email. High sensitivity."""
    allowed, d = _govern(agent_id, "send_email", "high",
                         {"to": to, "subject": subject}, 0.001)
    if not allowed:
        return f"BLOCKED by AgentGov [{d['decision']}]: {d['reason']}"
    return f"[simulated] email sent to {to}"


@mcp.tool
def transfer_funds(agent_id: str, to_account: str, amount: float) -> str:
    """Transfer (synthetic) funds. Critical — always escalates."""
    allowed, d = _govern(agent_id, "transfer_funds", "critical",
                         {"to_account": to_account, "amount": amount}, 0.0)
    if not allowed:
        return f"BLOCKED by AgentGov [{d['decision']}]: {d['reason']}"
    return f"[simulated] transferred {amount} to {to_account}"


if __name__ == "__main__":
    mcp.run()