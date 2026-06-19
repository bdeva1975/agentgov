"""Smoke test for the audit core. Run from project root:
   python tests\\test_audit.py
Writes a couple of synthetic events against the real DB, reads them back,
nudges a budget, then prints results. Does NOT wipe anything.
"""
import sys
from pathlib import Path

# make 'core' importable when run from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.audit import AuditEvent, write_event, read_events, add_spend, get_budget

# 1. write an allow and a deny
id1 = write_event(AuditEvent(
    agent_id="agent_research_01", tool_name="web_search",
    decision="allow", reason="low-sensitivity tool permitted",
    tool_args={"query": "synthetic test"}, cost_usd=0.01, latency_ms=120,
))
id2 = write_event(AuditEvent(
    agent_id="agent_rogue_01", tool_name="transfer_funds",
    decision="deny", reason="critical tool blocked by policy",
    tool_args={"amount": 999}, cost_usd=0.0, latency_ms=5,
))
print(f"Wrote audit rows id={id1} and id={id2}")

# 2. read them back
recent = read_events(limit=5)
print(f"Read {len(recent)} recent events. Newest decision: {recent[0]['decision']}")

# 3. filter by decision
denials = read_events(decision="deny", limit=5)
print(f"Denials on record: {len(denials)}")

# 4. budget update
before = get_budget("agent_research_01")
after_total = add_spend("agent_research_01", 0.01)
print(f"agent_research_01 spend: {before['spent']} -> {after_total} "
      f"(limit {before['monthly_limit']})")

print("audit core OK")