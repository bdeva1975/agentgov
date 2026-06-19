"""Generate synthetic agents, budgets, and a stream of tool-call requests.

Seeds the DB with a fixed agent roster (idempotent) and writes a JSON file
of synthetic tool-call requests for the proxy to govern in Step 6.

Run from project root:  python synthetic\\generate.py
Options: --requests N   (how many tool-call requests to generate, default 200)
         --seed N       (RNG seed for reproducibility, default 42)
"""
import argparse
import json
import random
import sqlite3
from pathlib import Path

from faker import Faker

DB_PATH = Path("db") / "agentgov.db"
REQUESTS_PATH = Path("synthetic") / "requests.json"

# Fixed synthetic agent roster. Stable IDs so re-runs stay consistent.
AGENTS = [
    ("agent_research_01",  "Research Assistant",   "R&D",        50.0),
    ("agent_support_01",   "Support Triage Bot",   "CustomerOps", 25.0),
    ("agent_finance_01",   "Finance Close Helper",  "Finance",    40.0),
    ("agent_devops_01",    "Incident Responder",    "Platform",   60.0),
    ("agent_rogue_01",     "Unscoped Test Agent",   "Sandbox",    10.0),
]

# Synthetic tool catalog: (tool_name, base_cost_usd, sensitivity)
# 'sensitivity' will matter to the policy engine in Step 5.
TOOLS = [
    ("read_document",   0.002, "low"),
    ("web_search",      0.010, "low"),
    ("query_database",  0.005, "medium"),
    ("send_email",      0.001, "high"),
    ("delete_record",   0.000, "high"),
    ("transfer_funds",  0.000, "critical"),
    ("export_data",     0.003, "high"),
]


def seed_agents(conn: sqlite3.Connection) -> None:
    for agent_id, name, team, limit in AGENTS:
        conn.execute(
            "INSERT OR IGNORE INTO agents (agent_id, display_name, team) "
            "VALUES (?, ?, ?)",
            (agent_id, name, team),
        )
        conn.execute(
            "INSERT OR IGNORE INTO budgets (agent_id, monthly_limit, spent) "
            "VALUES (?, ?, 0)",
            (agent_id, limit),
        )
    conn.commit()
    print(f"Seeded {len(AGENTS)} agents and budgets.")


def make_args(fake: Faker, tool_name: str) -> dict:
    """Plausible synthetic args per tool. Pure fiction, no real data."""
    if tool_name == "read_document":
        return {"doc_id": f"DOC-{fake.random_int(1000, 9999)}"}
    if tool_name == "web_search":
        return {"query": fake.sentence(nb_words=4)}
    if tool_name == "query_database":
        return {"table": random.choice(["orders", "tickets", "ledger"]),
                "limit": fake.random_int(1, 500)}
    if tool_name == "send_email":
        return {"to": fake.email(), "subject": fake.sentence(nb_words=3)}
    if tool_name == "delete_record":
        return {"table": random.choice(["orders", "users"]),
                "record_id": fake.random_int(1, 9999)}
    if tool_name == "transfer_funds":
        return {"to_account": fake.iban(), "amount": fake.random_int(10, 5000)}
    if tool_name == "export_data":
        return {"dataset": random.choice(["customers", "transactions"]),
                "rows": fake.random_int(10, 10000)}
    return {}


def generate_requests(n: int, seed: int) -> list[dict]:
    random.seed(seed)
    fake = Faker()
    Faker.seed(seed)

    agent_ids = [a[0] for a in AGENTS]
    requests = []
    for i in range(n):
        agent_id = random.choice(agent_ids)
        tool_name, base_cost, sensitivity = random.choice(TOOLS)
        # jitter the cost a little so dashboards aren't flat
        cost = round(base_cost * random.uniform(0.5, 2.0), 4)
        requests.append({
            "request_id": i + 1,
            "agent_id": agent_id,
            "tool_name": tool_name,
            "sensitivity": sensitivity,
            "args": make_args(fake, tool_name),
            "sim_cost_usd": cost,
        })
    return requests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        seed_agents(conn)
    finally:
        conn.close()

    reqs = generate_requests(args.requests, args.seed)
    REQUESTS_PATH.write_text(json.dumps(reqs, indent=2), encoding="utf-8")
    print(f"Wrote {len(reqs)} synthetic requests to {REQUESTS_PATH}")

    # quick distribution peek
    from collections import Counter
    by_tool = Counter(r["tool_name"] for r in reqs)
    print("Requests per tool:", dict(by_tool))


if __name__ == "__main__":
    main()