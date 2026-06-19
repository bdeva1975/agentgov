"""Exercise replay + anomaly detection over the real audit trail.
Run from project root:  python tests\\test_observe.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.observe import replay_agent, detect_anomalies

print("=== ANOMALY SCAN ===")
for f in detect_anomalies():
    mark = "🚩 FLAGGED" if f.flagged else "  ok"
    print(f"{mark}  {f.agent_id:20s} {f.denied:3d}/{f.total_calls:<3d} denied  — {f.reason}")

print("\n=== REPLAY: agent_rogue_01 (first 12 actions) ===")
trail = replay_agent("agent_rogue_01")
for e in trail[:12]:
    print(f"  #{e['id']:<4d} {e['tool_name']:15s} -> {e['decision']:8s}  {e['reason']}")
print(f"  ... {len(trail)} total actions for agent_rogue_01")