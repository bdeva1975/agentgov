# AgentGov — Model & System Card

**Status:** Proof of Concept · **Data:** Synthetic only · **Version:** 0.1.0

## What AgentGov is

AgentGov is a governance and observability control plane for agentic systems.
It sits in front of agent tool calls as a proxy and, for every call, makes and
records an enforcement decision — **allow**, **deny**, or **escalate** — based on
a declarative policy and per-agent budgets. It produces a complete, queryable
audit trail and surfaces behavioural anomalies.

It answers one question reliably: "What did our agents do, were they permitted
to, and what did it cost?"

## What AgentGov is NOT — and will NOT decide

This is the most important section. AgentGov is a control and audit layer, not
a decision-maker for the actions themselves.

- It does NOT decide whether a business action is *correct* — only whether it
  is *permitted* under policy and budget.
- It does NOT replace human judgement on escalated calls. An `escalate`
  decision means a human must decide; AgentGov never auto-approves what it escalated.
- It does NOT execute real-world side effects in this POC. All tool execution
  is simulated. No emails are sent, no records deleted, no funds moved.
- It does NOT make claims about agent *intent*. A high denial rate is flagged
  as a pattern to investigate, never as a determination of malice.
- It is NOT a substitute for identity, secrets management, or network security.
  It governs tool-call decisions; it assumes those upstream controls exist.

## Decision model

| Decision | Meaning | Effect |
|----------|---------|--------|
| `allow` | Permitted by policy AND within budget | Executes (simulated), cost charged |
| `deny` | Forbidden by a policy rule OR over budget | Blocked, nothing charged |
| `escalate` | Requires human approval (fund transfer, deletion) | Blocked pending human; never auto-approved |

Unknown agents (not in the registry) are always denied — you cannot govern
what you cannot identify.

## Inputs and data

- Synthetic only. Agents, tool calls, arguments, and costs are fabricated via
  a seeded generator (`synthetic/generate.py`). No real PII, no real systems, no
  real credentials are present anywhere in this POC.
- Policy is human-authored YAML (`policies/default.yaml`), readable and editable
  by non-engineers — deliberately, so governance owners can inspect the rules.

## Abstention & failure posture

- On an unrecognised agent, AgentGov denies rather than guessing.
- On a malformed policy (bad action, bad default), the engine fails loudly at
  load rather than running with silent misconfiguration.
- The default decision is configurable; the POC ships permissive (`allow`) to make
  the carve-out rules legible, but a production deployment should default to `deny`.

## Anomaly detection

The anomaly flag is a transparent, explainable rule: an agent is flagged when
its denial rate exceeds a threshold (default 30%) over a minimum number of calls
(default 5). Every flag carries a defensible sentence (e.g. "denial rate 71%
exceeds 30% over 48 calls"). No opaque scoring is used, by design — in a
governance tool, every flag must be auditable.

## Known limitations (POC)

- Single-tenant, single-node, SQLite-backed. Not built for scale or concurrency.
- Policy loads once at startup; editing YAML requires a restart.
- Budgets are simple cumulative ceilings; no time-windowing or reset logic.
- Simulated execution only — integration with real agents/MCP is out of scope here.

## Intended audience

Platform engineering, security, and compliance teams evaluating how agentic
systems could be governed and audited. This POC demonstrates the control
model, not a production deployment.