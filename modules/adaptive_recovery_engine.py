# Filename: adaptive_recovery_engine.py
# ArkEcho Systems © 2025
# v11r1 deterministic refactor — adds safe State adapter and rationale compliance.

from __future__ import annotations
from typing import Dict, Any, Tuple


# ---------------------------------------------------------
# Shared State Adapter (minimal dict compatibility)
# ---------------------------------------------------------
class State(dict):
    """Hybrid dict/object state with safe attribute access."""
    def __getattr__(self, name):
        return self.get(name, None)
    def __setattr__(self, name, value):
        self[name] = value
    def get(self, key, default=None):  # ensure compatibility
        return dict.get(self, key, default)
    def setdefault(self, key, default=None):
        return dict.setdefault(self, key, default)


# ---------------------------------------------------------
# Core Logic
# ---------------------------------------------------------
def init() -> State:
    """Initialize engine state."""
    return State({"recoveries": 0, "last_ok": True})


def run(ctx: Dict[str, Any], state: State) -> Tuple[Dict[str, Any], State]:
    """Adaptive recovery based on module errors or signal disruptions."""
    errors = int(ctx.get("errors", 0))
    threshold = int(ctx.get("threshold", 3))

    # Recovery logic
    recovered = errors <= threshold
    state["recoveries"] = state.get("recoveries", 0) + (0 if recovered else 1)
    state["last_ok"] = recovered

    risk = min(1.0, 0.2 * errors)
    action = "stabilize" if not recovered else "maintain"
    rationale = "Recovered successfully" if recovered else "Initiated stabilization protocol"

    output = {
        "ok": recovered,
        "action": action,
        "risk": risk,
        "rationale": rationale,
        "data": {
            "errors": errors,
            "recoveries": state["recoveries"],
            "stable": recovered,
        },
    }
    return output, state
