"""Policy engine test. Run from project root:
   python tests\\test_policy.py
Loads the default policy and runs representative synthetic requests through it,
asserting each lands on the expected decision.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.policy import PolicyEngine

engine = PolicyEngine("policies/default.yaml")

# (description, request, expected_action)
cases = [
    ("rogue tries high-sensitivity export",
     {"agent_id": "agent_rogue_01", "tool_name": "export_data",
      "sensitivity": "high", "team": "Sandbox"}, "deny"),
    ("anyone transfers funds",
     {"agent_id": "agent_finance_01", "tool_name": "transfer_funds",
      "sensitivity": "critical", "team": "Finance"}, "escalate"),
    ("R&D tries data export",
     {"agent_id": "agent_research_01", "tool_name": "export_data",
      "sensitivity": "high", "team": "R&D"}, "deny"),
    ("Finance exports data (allowed)",
     {"agent_id": "agent_finance_01", "tool_name": "export_data",
      "sensitivity": "high", "team": "Finance"}, "allow"),
    ("routine web search",
     {"agent_id": "agent_support_01", "tool_name": "web_search",
      "sensitivity": "low", "team": "CustomerOps"}, "allow"),
    ("delete record needs human",
     {"agent_id": "agent_devops_01", "tool_name": "delete_record",
      "sensitivity": "high", "team": "Platform"}, "escalate"),
]

passed = 0
for desc, req, expected in cases:
    d = engine.evaluate(req)
    ok = d.action == expected
    passed += ok
    flag = "OK " if ok else "FAIL"
    print(f"[{flag}] {desc:38s} -> {d.action:8s} ({d.reason})")

print(f"\n{passed}/{len(cases)} cases passed")