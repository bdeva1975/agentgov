# AgentGov — Audit Event Schema

Every governed tool call produces exactly one immutable row in `audit_log`.
This is the single source of truth for "what happened."

| Field | Type | Meaning |
|-------|------|---------|
| `id` | integer | Monotonic event id; also the chronological order |
| `ts` | text (UTC) | When the decision was made |
| `agent_id` | text | Which agent made the call |
| `tool_name` | text | Tool requested |
| `tool_args` | text (JSON) | Synthetic arguments of the call |
| `decision` | text | `allow` \| `deny` \| `escalate` |
| `reason` | text | Plain-language cause: which rule or budget fired |
| `cost_usd` | real | Cost charged (0 unless executed) |
| `latency_ms` | integer | Simulated execution latency |

## Design guarantees

- **Every** decision is logged — allow, deny, and escalate alike. There is no
  path through the proxy that skips the audit write.
- The `reason` field makes the trail self-explaining: an auditor never has to ask
  "why was this blocked?" — the row says so.
- Denials from policy and denials from budget exhaustion are recorded uniformly,
  so "why was this stopped?" has one consistent answer regardless of cause.
- Reads go through a single chokepoint (`core/audit.py`); nothing else writes the trail.