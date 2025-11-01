# Filename: context_resilience_keeper.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic schema, stress-aware decay, and recovery trigger

from __future__ import annotations
from typing import Dict, Any, Tuple

NAME = "Context Resilience Keeper"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Config (override via ctx["resilience_cfg"])
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    "decay_per_step": 0.01,   # baseline decay each invocation
    "stress_gain": 0.25,      # how strongly external stress impacts decay
    "recover_gain": 0.20,     # recovery amount when in recovery action
    "recover_threshold": 0.35, # below this, trigger recovery
    "ok_threshold": 0.70,      # at/above this, mark stable
    "min_resilience": 0.0,
    "max_resilience": 1.0
}

# ---------------------------------------------------------------------------
# Helper fallback(s)
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event})


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """
    Initialize resilience state.
    """
    return {
        "resilience": 1.0,
        "mode": "stable",    # stable | recovering | degraded
        "steps": 0
    }


def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Maintain conversation/system context resilience against stress.
    - Decays under stress; can self-recover when critically low.
    - Emits allow/recover actions with a clear rationale.
    Inputs (optional in ctx):
      - stress: float in [0,1]  (external pressure/noise)
      - resilience_cfg: dict    (override DEFAULT_CFG keys)
    """
    cfg = dict(DEFAULT_CFG)
    cfg.update(ctx.get("resilience_cfg", {}))

    stress = float(clamp(ctx.get("stress", 0.0), 0.0, 1.0))
    r = float(state.get("resilience", 1.0))
    state["steps"] = int(state.get("steps", 0)) + 1

    # Compute new resilience
    decay = cfg["decay_per_step"] + cfg["stress_gain"] * stress
    new_r = clamp(r - decay, cfg["min_resilience"], cfg["max_resilience"])

    action = "allow"
    rationale = f"Resilience decayed by {decay:.2f} under stress={stress:.2f}."

    # Trigger recovery mode if critically low
    if new_r < cfg["recover_threshold"]:
        action = "recover"
        new_r = clamp(new_r + cfg["recover_gain"], cfg["min_resilience"], cfg["max_resilience"])
        state["mode"] = "recovering"
        rationale = (
            f"Resilience low ({new_r:.2f} after recovery). Entering recovery mode: "
            f"+{cfg['recover_gain']:.2f} applied."
        )
    elif new_r >= cfg["ok_threshold"]:
        state["mode"] = "stable"
        rationale += " Resilience stable."
    else:
        state["mode"] = "degraded"
        rationale += " Monitoring degradation."

    # Update state
    state["resilience"] = new_r

    # Risk is inverse of resilience
    risk = round(1.0 - new_r, 3)

    safe_log(f"Resilience:{state['mode']}:{action}", state)

    output = {
        "ok": True,
        "action": action,          # "allow" | "recover"
        "risk": risk,
        "rationale": rationale,
        "data": {
            "resilience": round(new_r, 3),
            "mode": state["mode"],
            "stress": stress,
            "step": state["steps"]
        },
    }
    return output, state


def describe() -> Dict[str, Any]:
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Tracks and stabilizes contextual resilience under stress; triggers recovery when critically low.",
        "inputs": ["stress", "resilience_cfg"],
        "outputs": ["resilience", "mode", "action", "risk"]
    }
