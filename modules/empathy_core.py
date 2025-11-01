# Filename: empathy_core.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic schema, fatigue decay, moral resonance, safe audit fallback.

from __future__ import annotations
from typing import Dict, Any, Tuple
import math

NAME = "Empathy Core"
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
    "fatigue_decay": 0.02,    # empathy decays slightly each step
    "resonance_gain": 0.4,    # how strongly shared affect amplifies empathy
    "stress_penalty": 0.3,    # reduces empathy under stress
    "stability_threshold": 0.7
}


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    return {
        "empathy_level": 0.5,
        "fatigue": 0.0,
        "steps": 0,
        "mode": "neutral"
    }


def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Core empathy engine: blends self-awareness and external emotion input to compute balanced empathy.
    Inputs:
      - self_affect: float [0,1]
      - external_affect: float [0,1]
      - stress: float [0,1]
      - empathy_cfg: dict (optional override)
    """
    cfg = dict(DEFAULT_CFG)
    cfg.update(ctx.get("empathy_cfg", {}))

    self_affect = clamp(float(ctx.get("self_affect", 0.5)), 0.0, 1.0)
    external_affect = clamp(float(ctx.get("external_affect", 0.5)), 0.0, 1.0)
    stress = clamp(float(ctx.get("stress", 0.0)), 0.0, 1.0)
    fatigue = state.get("fatigue", 0.0)

    state["steps"] = state.get("steps", 0) + 1

    # Empathic resonance computation
    shared_resonance = (self_affect + external_affect) / 2.0
    amplified_empathy = shared_resonance + cfg["resonance_gain"] * (1 - abs(self_affect - external_affect))
    decayed_empathy = amplified_empathy * (1 - fatigue) * (1 - cfg["stress_penalty"] * stress)
    empathy_level = clamp(decayed_empathy, 0.0, 1.0)

    # Fatigue accumulates slightly each step
    fatigue = clamp(fatigue + cfg["fatigue_decay"], 0.0, 0.5)
    state.update({"empathy_level": empathy_level, "fatigue": fatigue})

    # Determine moral mode and action
    if empathy_level < 0.3:
        mode = "detached"
        action = "increase_empathy"
        rationale = f"Empathy low ({empathy_level:.2f}); promoting compassionate focus."
        risk = 0.6
    elif empathy_level > cfg["stability_threshold"]:
        mode = "harmonized"
        action = "stabilize"
        rationale = f"Empathy stable ({empathy_level:.2f}); maintaining balance."
        risk = 0.2
    else:
        mode = "neutral"
        action = "observe"
        rationale = f"Empathy moderate ({empathy_level:.2f}); continuing observation."
        risk = 0.4

    state["mode"] = mode
    safe_log(f"Empathy:{mode}:{action}", state)

    output = {
        "ok": True,
        "action": action,
        "risk": risk,
        "rationale": rationale,
        "data": {
            "empathy_level": round(empathy_level, 3),
            "fatigue": round(fatigue, 3),
            "mode": mode,
            "stress": stress,
        },
    }
    return output, state


def describe() -> Dict[str, Any]:
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Computes dynamic empathy by blending self/external affect with stress and fatigue modulation.",
        "inputs": ["self_affect", "external_affect", "stress", "empathy_cfg"],
        "outputs": ["empathy_level", "mode", "action", "risk"],
    }
