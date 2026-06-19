"""Feed the synthetic request stream through the live proxy.

Reads synthetic/requests.json and POSTs each to the running proxy, so the
audit trail fills with a realistic mix of allow/deny/escalate decisions.

Proxy must be running (uvicorn ... port 8000) in another terminal.
Run from project root:  python synthetic\\replay_requests.py
"""
import json
from collections import Counter
from pathlib import Path

import requests

PROXY = "http://127.0.0.1:8000/proxy/tool-call"
REQUESTS_PATH = Path("synthetic") / "requests.json"


def main() -> None:
    reqs = json.loads(REQUESTS_PATH.read_text(encoding="utf-8"))
    decisions = Counter()
    errors = 0

    for r in reqs:
        payload = {
            "agent_id": r["agent_id"],
            "tool_name": r["tool_name"],
            "sensitivity": r["sensitivity"],
            "args": r["args"],
            "sim_cost_usd": r["sim_cost_usd"],
        }
        try:
            resp = requests.post(PROXY, json=payload, timeout=10)
            resp.raise_for_status()
            decisions[resp.json()["decision"]] += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                print(f"  request {r['request_id']} failed: {e}")

    print(f"Replayed {len(reqs)} requests through the proxy.")
    print("Decisions:", dict(decisions))
    if errors:
        print(f"Errors: {errors}")


if __name__ == "__main__":
    main()