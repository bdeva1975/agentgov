"""Agent registry lookups for the proxy."""
import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path("db") / "agentgov.db"


def get_agent(agent_id: str) -> Optional[dict]:
    """Return {agent_id, display_name, team} or None if unknown."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT agent_id, display_name, team FROM agents WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()