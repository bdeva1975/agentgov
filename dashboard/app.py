"""AgentGov dashboard (Streamlit).

Renders the audit trail as a filterable table with decision breakdown and
per-agent spend. Reads the same SQLite DB the proxy writes to.

Run from project root:  streamlit run dashboard\\app.py
"""
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DB_PATH = Path("db") / "agentgov.db"

st.set_page_config(page_title="AgentGov", page_icon="🛡️", layout="wide")


def load_audit() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query("SELECT * FROM audit_log ORDER BY id DESC", conn)
    finally:
        conn.close()
    return df


def load_budgets() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            """SELECT b.agent_id, a.display_name, a.team,
                      b.spent, b.monthly_limit
               FROM budgets b JOIN agents a ON a.agent_id = b.agent_id
               ORDER BY b.spent DESC""", conn)
    finally:
        conn.close()
    return df


st.title("🛡️ AgentGov — Agent Governance & Observability")
st.caption("Synthetic-data POC. Every governed tool call, every decision, every dollar.")

audit = load_audit()
budgets = load_budgets()

if audit.empty:
    st.warning("No audit events yet. Run the proxy and replay the synthetic requests.")
    st.stop()

# --- top-line metrics ---
total = len(audit)
allows = (audit["decision"] == "allow").sum()
denies = (audit["decision"] == "deny").sum()
escalations = (audit["decision"] == "escalate").sum()
spend = audit["cost_usd"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total calls", total)
c2.metric("Allowed", int(allows))
c3.metric("Denied", int(denies))
c4.metric("Escalated", int(escalations))
c5.metric("Total spend", f"${spend:,.2f}")

# --- anomaly flags ---
from core.observe import detect_anomalies
st.subheader("🚩 Anomaly flags")
flags = detect_anomalies()
flagged = [f for f in flags if f.flagged]
if flagged:
    for f in flagged:
        st.error(f"**{f.agent_id}** — {f.reason}")
else:
    st.success("No anomalies detected.")

st.divider()

# --- decision breakdown + spend side by side ---
left, right = st.columns(2)
with left:
    st.subheader("Decisions")
    st.bar_chart(audit["decision"].value_counts())
with right:
    st.subheader("Per-agent spend vs. limit")
    bdf = budgets.copy()
    bdf["used_%"] = (bdf["spent"] / bdf["monthly_limit"] * 100).round(1)
    st.dataframe(
        bdf[["display_name", "team", "spent", "monthly_limit", "used_%"]],
        width='stretch', hide_index=True,
    )

st.divider()

# --- the audit trail, filterable ---
st.subheader("Audit trail")
f1, f2 = st.columns(2)
with f1:
    agent_filter = st.multiselect(
        "Filter by agent", sorted(audit["agent_id"].unique()))
with f2:
    decision_filter = st.multiselect(
        "Filter by decision", ["allow", "deny", "escalate"])

view = audit
if agent_filter:
    view = view[view["agent_id"].isin(agent_filter)]
if decision_filter:
    view = view[view["decision"].isin(decision_filter)]

st.caption(f"Showing {len(view)} of {total} events")
st.dataframe(
    view[["id", "ts", "agent_id", "tool_name", "decision", "reason", "cost_usd"]],
    use_container_width=True, hide_index=True,
)