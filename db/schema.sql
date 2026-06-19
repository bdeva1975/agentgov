-- AgentGov POC schema (SQLite)
-- Synthetic data only. No real systems, no real PII.

-- Registry of agents under governance
CREATE TABLE IF NOT EXISTS agents (
    agent_id      TEXT PRIMARY KEY,         -- e.g. "agent_research_01"
    display_name  TEXT NOT NULL,
    team          TEXT NOT NULL,            -- owning team (synthetic)
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Per-agent spend ceiling (drives Step 7 cost caps)
CREATE TABLE IF NOT EXISTS budgets (
    agent_id        TEXT PRIMARY KEY REFERENCES agents(agent_id),
    monthly_limit   REAL NOT NULL,          -- USD ceiling
    spent           REAL NOT NULL DEFAULT 0 -- running total, updated by proxy
);

-- The core audit trail: one row per governed tool call
CREATE TABLE IF NOT EXISTS audit_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT NOT NULL DEFAULT (datetime('now')),
    agent_id      TEXT NOT NULL REFERENCES agents(agent_id),
    tool_name     TEXT NOT NULL,            -- e.g. "send_email", "read_db"
    tool_args     TEXT,                     -- JSON string of the call args
    decision      TEXT NOT NULL,            -- allow | deny | escalate
    reason        TEXT,                     -- which policy rule fired
    cost_usd      REAL NOT NULL DEFAULT 0,  -- simulated cost of the call
    latency_ms    INTEGER NOT NULL DEFAULT 0
);

-- Indexes for the dashboard's common filters (Step 8)
CREATE INDEX IF NOT EXISTS idx_audit_agent    ON audit_log(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_decision ON audit_log(decision);
CREATE INDEX IF NOT EXISTS idx_audit_ts       ON audit_log(ts);