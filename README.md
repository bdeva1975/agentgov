# 🛡️ AgentGov — Agent Governance & Observability

A governance control plane for agentic systems. Proxies agent tool calls, enforces
policy and budgets, audits every decision, and flags anomalies — so agentic
systems become auditable and controllable.

**Proof of concept. Synthetic data only. No real systems, no real PII.**

## The problem

Organizations deploy AI agents faster than they can govern them. Security and
compliance teams have no audit trail, no enforcement, and no cost ceiling — so
they block production. The bottleneck to enterprise agent adoption is governance,
not capability. AgentGov is that governance layer.

## What it does

- **Enforces** — every tool call is allowed, denied, or escalated to a human,
  per a declarative YAML policy.
- **Caps cost** — per-agent budgets; an allowed call is still denied if it would
  breach the ceiling.
- **Audits** — one immutable, self-explaining row per call. Every decision, every dollar.
- **Observes** — replay any agent's full action history; flag agents with
  abnormal denial rates.

## Architecture

```
   Agents / Apps
        |  (tool calls)
        v
   Governance Proxy (FastAPI)
     - enrich (agent -> team)
     - policy engine (allow/deny/escalate)
     - budget gate (cost cap)
     - audit write (always)
        |
        v
   SQLite audit trail  --->  Streamlit dashboard + observability
```

## Layout

```
agentgov/
├── core/        policy engine, audit core, agent lookup, observability
├── proxy/       FastAPI governance proxy
├── dashboard/   Streamlit audit/anomaly UI
├── synthetic/   seeded synthetic data + request replay
├── policies/    YAML policy rules
├── db/          schema + init
├── governance/  model card, audit schema (trust artifacts)
└── tests/       smoke tests for each component
```

## Run it

```powershell
# 1. environment
.\.venv\Scripts\Activate.ps1

# 2. build the database + synthetic data
python db\init_db.py --reset
python synthetic\generate.py

# 3. start the proxy (terminal 1)
uvicorn proxy.app:app --reload --port 8000

# 4. drive synthetic traffic through it (terminal 2)
python synthetic\replay_requests.py

# 5. open the dashboard (terminal 2)
streamlit run dashboard\app.py
```

## What it deliberately does not do

See `governance/MODEL_CARD.md`. In short: AgentGov decides what's *permitted*,
not what's *correct*; it never auto-approves an escalation; and in this POC all
execution is simulated.

## Roadmap (beyond POC)

- Real MCP proxy integration (intercept actual tool/MCP traffic)
- Hot-reloadable policy; policy versioning
- Multi-tenant, Postgres-backed, OpenTelemetry traces
- Time-windowed budgets; rate limiting
- Pluggable anomaly detectors with the same explainability contract