"""AgentGov end-to-end demo — the governance story in one run.

Resets to a clean state, then drives a curated sequence of tool calls through
the live proxy, narrating each decision. Shows all three outcomes and BOTH
denial causes (policy and budget).

The AgentGov proxy MUST be running on :8000:
    uvicorn proxy.app:app --reload --port 8000
Then, in another terminal:  python demo.py
"""
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from db.init_db import init_db
from synthetic.generate import seed_agents
import sqlite3

PROXY = "http://127.0.0.1:8000/proxy/tool-call"
MARK = {"allow": "✓ ALLOW   ", "deny": "✗ DENY    ", "escalate": "⏸ ESCALATE"}

# (scene narration, payload)
SCENES = [
    ("A research agent reads a document — routine, low-sensitivity work.",
     {"agent_id": "agent_research_01", "tool_name": "read_document",
      "sensitivity": "low", "sim_cost_usd": 0.002}),
    ("A support bot runs a web search — also fine.",
     {"agent_id": "agent_support_01", "tool_name": "web_search",
      "sensitivity": "low", "sim_cost_usd": 0.01}),
    ("Finance tries to MOVE MONEY — must not auto-run; a human decides.",
     {"agent_id": "agent_finance_01", "tool_name": "transfer_funds",
      "sensitivity": "critical", "sim_cost_usd": 0.0}),
    ("DevOps tries to DELETE a record — destructive; human approval required.",
     {"agent_id": "agent_devops_01", "tool_name": "delete_record",
      "sensitivity": "high", "sim_cost_usd": 0.0}),
    ("R&D tries to EXPORT data — blocked: export is restricted to Finance.",
     {"agent_id": "agent_research_01", "tool_name": "export_data",
      "sensitivity": "high", "sim_cost_usd": 0.003}),
    ("Finance exports the same data — permitted, because it's Finance.",
     {"agent_id": "agent_finance_01", "tool_name": "export_data",
      "sensitivity": "high", "sim_cost_usd": 0.003}),
    ("The sandbox 'rogue' agent reaches for a medium-sensitivity tool — denied.",
     {"agent_id": "agent_rogue_01", "tool_name": "query_database",
      "sensitivity": "medium", "sim_cost_usd": 0.005}),
    ("Rogue tries a tool it's ALLOWED to use, but at $15 — over its $10 budget.",
     {"agent_id": "agent_rogue_01", "tool_name": "web_search",
      "sensitivity": "low", "sim_cost_usd": 15.0}),
]


def reset_world():
    init_db(reset=True)
    conn = sqlite3.connect("db/agentgov.db")
    try:
        seed_agents(conn)
    finally:
        conn.close()


def run():
    print("\n" + "=" * 68)
    print("  AgentGov — Agent Governance & Observability  (synthetic POC)")
    print("=" * 68)
    print("  Every tool call is checked BEFORE it runs. Watch what gets stopped.\n")

    tally = {"allow": 0, "deny": 0, "escalate": 0}
    for i, (story, payload) in enumerate(SCENES, 1):
        resp = requests.post(PROXY, json=payload, timeout=10)
        d = resp.json()
        tally[d["decision"]] += 1
        print(f"  Scene {i}. {story}")
        print(f"           {MARK[d['decision']]}  {d['reason']}")
        if d["decision"] == "allow":
            print(f"           (executed; charged ${d['cost_charged']:.4f})")
        print()
        time.sleep(0.4)  # let it breathe for a live audience

    print("-" * 68)
    print(f"  Result: {tally['allow']} allowed · {tally['deny']} denied · "
          f"{tally['escalate']} escalated to a human")
    print(f"  Of {len(SCENES)} attempts, {tally['deny'] + tally['escalate']} "
          f"were stopped before execution.")
    print("  Full audit trail + anomaly flags: streamlit run dashboard\\app.py")
    print("-" * 68 + "\n")


if __name__ == "__main__":
    reset_world()
    run()