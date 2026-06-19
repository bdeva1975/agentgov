"""Initialize the AgentGov SQLite database from schema.sql.
Run from the project root: python db\\init_db.py
Re-running is safe (CREATE TABLE IF NOT EXISTS), but --reset wipes it first.
"""
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("db") / "agentgov.db"
SCHEMA_PATH = Path("db") / "schema.sql"


def init_db(reset: bool = False) -> None:
    if reset and DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing {DB_PATH}")

    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(schema)
        conn.commit()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        print(f"Initialized {DB_PATH}")
        print("Tables:", ", ".join(t[0] for t in tables))
    finally:
        conn.close()


if __name__ == "__main__":
    init_db(reset="--reset" in sys.argv)