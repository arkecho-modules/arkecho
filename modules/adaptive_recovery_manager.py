# Filename: adaptive_recovery_manager.py
# ArkEcho Systems © 2025
# v11r1 deterministic refactor — adds State adapter and rationale compliance.

from __future__ import annotations
from typing import Dict, Any, Tuple


class State(dict):
    def __getattr__(self, name): return self.get(name, None)
    def __setattr__(self, name, value): self[name] = value
    def get(self, key, default=None): return dict.get(self, key, default)
    def setdefault(self, key, default=None): return dict.setdefault(self, key, default)


def init() -> State:
    return State({"cycles": 0, "last_action": "none"})


def run(ctx: Dict[str, Any], state: State) -> Tuple[Dict[str, Any], State]:
    """Manages and supervises recovery events from the adaptive engine."""
    state["cycles"] = state.get("cycles", 0) + 1
    incident = ctx.get("incident", False)
    severity = float(ctx.get("severity", 0.0))

    if incident:
        action = "recover"
        ok = False
        risk = min(1.0, 0.5 + 0.5 * severity)
        rationale = f"Incident detected (severity={severity:.2f}); recovery triggered."
    else:
        action = "monitor"
        ok = True
        risk = 0.0
        rationale = "No incidents; monitoring steady state."

    state["last_action"] = action
    output = {
        "ok": ok,
        "action": action,
        "risk": risk,
        "rationale": rationale,
        "data": {
            "cycles": state["cycles"],
            "incident": incident,
            "severity": severity,
        },
    }
    return output, state
