"""AgentGov audit core.

The single chokepoint for the audit trail. The proxy writes decisions here;
the dashboard reads them back. Nothing else should touch audit_log directly.

Synthetic-data POC: no real PII, no real systems.
"""
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DB_PATH = Path("db") / "agentgov.db"

VALID_DECISIONS = {"allow", "deny", "escalate"}


@dataclass
class AuditEvent:
    agent_id: str
    tool_name: str
    decision: str
    reason: str
    tool_args: Optional[dict] = None
    cost_usd: float = 0.0
    latency_ms: int = 0


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def write_event(event: AuditEvent) -> int:
    """Append one decision to the audit trail. Returns the new row id."""
    if event.decision not in VALID_DECISIONS:
        raise ValueError(
            f"decision must be one of {VALID_DECISIONS}, got '{event.decision}'"
        )
    conn = _connect()
    try:
        cur = conn.execute(
            """INSERT INTO audit_log
               (agent_id, tool_name, tool_args, decision, reason, cost_usd, latency_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                event.agent_id,
                event.tool_name,
                json.dumps(event.tool_args) if event.tool_args is not None else None,
                event.decision,
                event.reason,
                event.cost_usd,
                event.latency_ms,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def read_events(
    agent_id: Optional[str] = None,
    decision: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    """Read the audit trail, newest first, with optional filters."""
    clauses, params = [], []
    if agent_id:
        clauses.append("agent_id = ?")
        params.append(agent_id)
    if decision:
        clauses.append("decision = ?")
        params.append(decision)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params.append(limit)

    conn = _connect()
    try:
        rows = conn.execute(
            f"SELECT * FROM audit_log {where} ORDER BY id DESC LIMIT ?",
            params,
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_spend(agent_id: str, amount: float) -> float:
    """Add to an agent's running spend. Returns the new total."""
    conn = _connect()
    try:
        conn.execute(
            "UPDATE budgets SET spent = spent + ? WHERE agent_id = ?",
            (amount, agent_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT spent FROM budgets WHERE agent_id = ?", (agent_id,)
        ).fetchone()
        return row["spent"] if row else 0.0
    finally:
        conn.close()


def get_budget(agent_id: str) -> Optional[dict]:
    """Return {monthly_limit, spent} for an agent, or None if unknown."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT monthly_limit, spent FROM budgets WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()