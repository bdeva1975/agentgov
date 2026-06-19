"""AgentGov policy engine.

Loads a YAML policy and evaluates a tool-call request against it.
First matching rule wins; otherwise default_decision applies.

A 'request' is a dict with at least: agent_id, tool_name, sensitivity, team.
Returns a Decision: action in {allow, deny, escalate} + the rule that fired.
"""
from dataclasses import dataclass
from pathlib import Path

import yaml

VALID_ACTIONS = {"allow", "deny", "escalate"}


@dataclass
class Decision:
    action: str
    reason: str   # human-readable: which rule fired and why


class PolicyEngine:
    def __init__(self, policy_path: str | Path):
        self.policy_path = Path(policy_path)
        self._load()

    def _load(self) -> None:
        data = yaml.safe_load(self.policy_path.read_text(encoding="utf-8"))
        self.default_decision = data.get("default_decision", "deny")
        self.rules = data.get("rules", [])
        # validate up front so a typo in YAML fails loudly, not silently
        if self.default_decision not in VALID_ACTIONS:
            raise ValueError(f"bad default_decision: {self.default_decision}")
        for r in self.rules:
            if r.get("action") not in VALID_ACTIONS:
                raise ValueError(f"rule '{r.get('name')}' has bad action: {r.get('action')}")

    @staticmethod
    def _matches(rule: dict, request: dict) -> bool:
        """A rule matches only if ALL of its match conditions hold.
        A condition value may be a scalar (exact match) or a list (membership)."""
        match = rule.get("match", {})
        # map policy match-keys to request fields
        field_map = {
            "agent_id":    request.get("agent_id"),
            "tool":        request.get("tool_name"),
            "sensitivity": request.get("sensitivity"),
            "team":        request.get("team"),
        }
        for key, expected in match.items():
            actual = field_map.get(key)
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            else:
                if actual != expected:
                    return False
        return True

    def evaluate(self, request: dict) -> Decision:
        for rule in self.rules:
            if self._matches(rule, request):
                return Decision(
                    action=rule["action"],
                    reason=f"matched rule: {rule['name']}",
                )
        return Decision(
            action=self.default_decision,
            reason="no rule matched; default applied",
        )