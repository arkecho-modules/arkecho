# Filename: motive_and_risk_regulator.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic schema, moral motive control loop, and safe audit fallback.

from __future__ import annotations
from typing import Dict, Any, Tuple
import math

NAME = "Motive and Risk Regulator"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helper fallbacks
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event})

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    "motivation_gain": 0.4,      # how strongly new intent raises motive
    "risk_decay": 0.1,           # decay applied to risk each iteration
    "motivation_decay": 0.05,    # gradual drop in motive over time
    "stability_threshold": 0.6,  # above this, risk reduces more slowly
    "max_safe_risk": 0.7,
    "min_motive": 0.0,
    "max_motive": 1.0,
}

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize motive/risk regulation state."""
    return {
        "motive": 0.5,
        "risk": 0.3,
        "cycles": 0,
        "mode": "balanced"
    }

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Adjusts the system’s motive energy and risk tolerance over time.
    Inputs:
      - intent_signal: float [0,1]
      - external_risk: float [0,1]
      - motive_cfg: dict (optional overrides)
    """
    cfg = dict(DEFAULT_CFG)
    cfg.update(ctx.get("motive_cfg", {}))

    intent_signal = clamp(float(ctx.get("intent_signal", 0.5)), 0.0, 1.0)
    external_risk = clamp(float(ctx.get("external_risk", 0.3)), 0.0, 1.0)
    motive = clamp(float(state.get("motive", 0.5)), 0.0, 1.0)
    risk = clamp(float(state.get("risk", 0.3)), 0.0, 1.0)
    state["cycles"] = state.get("cycles", 0) + 1

    # Compute motive adjustment
    motive = motive + cfg["motivation_gain"] * (intent_signal - 0.5)
    motive -= cfg["motivation_decay"]
    motive = clamp(motive, cfg["min_motive"], cfg["max_motive"])

    # Risk evolution — decays slowly, but rises with external pressure
    decay_rate = cfg["risk_decay"] * (1.0 if motive < cfg["stability_threshold"] else 0.5)
    risk = risk * (1.0 - decay_rate) + external_risk * 0.5
    risk = clamp(risk, 0.0, 1.0)

    # Decision logic
    if risk >= cfg["max_safe_risk"]:
        action = "reduce_motive"
        rationale = f"Risk high ({risk:.2f}); lowering motive energy to stabilize system."
        motive -= 0.2
        motive = clamp(motive, cfg["min_motive"], cfg["max_motive"])
        mode = "cautious"
    elif motive <= 0.2:
        action = "boost_motive"
        rationale = f"Motive low ({motive:.2f}); boosting internal drive to maintain responsiveness."
        motive += 0.1
        mode = "recovering"
    else:
        action = "maintain"
        rationale = f"System balanced (motive={motive:.2f}, risk={risk:.2f}); maintaining state."
        mode = "balanced"

    # Final update
    state.update({
        "motive": round(motive, 3),
        "risk": round(risk, 3),
        "mode": mode,
    })

    safe_log(f"MotiveRegulator:{action}:{mode}", state)

    output = {
        "ok": True,
        "action": action,        # "maintain" | "reduce_motive" | "boost_motive"
        "risk": round(risk, 3),
        "rationale": rationale,
        "data": {
            "motive": round(motive, 3),
            "risk": round(risk, 3),
            "mode": mode,
            "intent_signal": intent_signal,
            "external_risk": external_risk,
        },
    }
    return output, state

# ---------------------------------------------------------------------------
# Describe
# ---------------------------------------------------------------------------
def describe() -> Dict[str, Any]:
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Balances system motive energy and risk tolerance; dampens overreaction and prevents stagnation.",
        "inputs": ["intent_signal", "external_risk", "motive_cfg"],
        "outputs": ["motive", "risk", "mode", "action"],
    }
