"""AgentGov observability: replay and anomaly detection.

Pure read-side analysis over the audit trail. No side effects.
Transparent, explainable rules only — every flag must be defensible to an auditor.
"""
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path("db") / "agentgov.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def replay_agent(agent_id: str) -> list[dict]:
    """Return every action an agent took, in chronological order (oldest first).
    This is the audit-investigation view: the full story of one agent."""
    conn = _connect()
    try:
        rows = conn.execute(
            """SELECT id, ts, tool_name, decision, reason, cost_usd
               FROM audit_log WHERE agent_id = ? ORDER BY id ASC""",
            (agent_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@dataclass
class AnomalyFlag:
    agent_id: str
    total_calls: int
    denied: int
    denial_rate: float
    flagged: bool
    reason: str


def detect_anomalies(denial_threshold: float = 0.30,
                     min_calls: int = 5) -> list[AnomalyFlag]:
    """Flag agents whose denial rate exceeds the threshold.

    A high denial rate means an agent is repeatedly attempting actions it
    isn't permitted to take — the classic signature of a misconfigured or
    compromised ('rogue') agent. min_calls avoids flagging on tiny samples.
    """
    conn = _connect()
    try:
        rows = conn.execute(
            """SELECT agent_id,
                      COUNT(*) AS total,
                      SUM(CASE WHEN decision='deny' THEN 1 ELSE 0 END) AS denied
               FROM audit_log
               GROUP BY agent_id""",
        ).fetchall()
    finally:
        conn.close()

    flags = []
    for r in rows:
        total, denied = r["total"], r["denied"]
        rate = denied / total if total else 0.0
        flagged = total >= min_calls and rate > denial_threshold
        reason = (
            f"denial rate {rate:.0%} exceeds {denial_threshold:.0%} "
            f"over {total} calls" if flagged
            else f"normal ({rate:.0%} denial rate)"
        )
        flags.append(AnomalyFlag(
            agent_id=r["agent_id"], total_calls=total, denied=denied,
            denial_rate=round(rate, 3), flagged=flagged, reason=reason,
        ))
    # most suspicious first
    flags.sort(key=lambda f: f.denial_rate, reverse=True)
    return flags