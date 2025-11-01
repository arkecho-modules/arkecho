# Filename: resonance_pacing_core.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic pacing regulator for moral/emotional resonance across system cycles.

from __future__ import annotations
from typing import Dict, Any, Tuple
import math
import time

NAME = "Resonance Pacing Core"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event, "t": round(time.time(), 3)})

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    "target_resonance": 0.7,     # desired resonance balance
    "adapt_rate": 0.15,          # correction rate toward target
    "tempo_gain": 0.2,           # influence of cognitive tempo
    "stress_factor": 0.25,       # how stress disturbs pacing
    "recover_rate": 0.3,         # natural recovery to target
}

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    return {
        "resonance": 0.7,
        "tempo": 0.5,
        "stress": 0.0,
        "cycles": 0,
        "phase": "stable",
    }

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Regulates system pacing and emotional resonance to prevent moral fatigue or impulsive overreaction.
    Inputs:
      - cognitive_tempo: float [0,1]
      - emotional_resonance: float [0,1]
      - stress_load: float [0,1]
      - pacing_cfg: dict (optional overrides)
    """
    cfg = dict(DEFAULT_CFG)
    cfg.update(ctx.get("pacing_cfg", {}))

    cognitive_tempo = clamp(float(ctx.get("cognitive_tempo", 0.5)), 0.0, 1.0)
    emotional_resonance = clamp(float(ctx.get("emotional_resonance", 0.7)), 0.0, 1.0)
    stress_load = clamp(float(ctx.get("stress_load", 0.3)), 0.0, 1.0)
    state["cycles"] = state.get("cycles", 0) + 1

    prev_res = state.get("resonance", 0.7)
    prev_tempo = state.get("tempo", 0.5)

    # Step 1: Compute drift
    resonance_gap = emotional_resonance - prev_res
    tempo_gap = cognitive_tempo - prev_tempo

    # Step 2: Stress impact
    stress_penalty = cfg["stress_factor"] * stress_load

    # Step 3: Adjust resonance toward target using adapt_rate and recovery
    adjusted_res = prev_res + cfg["adapt_rate"] * resonance_gap - stress_penalty
    adjusted_res += cfg["recover_rate"] * (cfg["target_resonance"] - adjusted_res)

    # Step 4: Adjust tempo harmonically toward resonance
    adjusted_tempo = prev_tempo + cfg["tempo_gain"] * (adjusted_res - prev_tempo)

    # Step 5: Determine phase state
    if stress_load > 0.6:
        phase = "strained"
    elif abs(resonance_gap) < 0.05 and abs(tempo_gap) < 0.05:
        phase = "stable"
    else:
        phase = "adjusting"

    adjusted_res = round(clamp(adjusted_res, 0.0, 1.0), 3)
    adjusted_tempo = round(clamp(adjusted_tempo, 0.0, 1.0), 3)

    # Risk inversely proportional to alignment
    alignment = 1.0 - abs(cfg["target_resonance"] - adjusted_res)
    risk = round(1.0 - alignment, 3)

    rationale = (
        f"Resonance={adjusted_res:.2f}, Tempo={adjusted_tempo:.2f}, Stress={stress_load:.2f}, "
        f"Phase={phase}. Adjusted pacing to sustain harmonic balance."
    )

    state.update({
        "resonance": adjusted_res,
        "tempo": adjusted_tempo,
        "stress": stress_load,
        "phase": phase,
    })
    safe_log(f"ResonancePacing:{phase}", state)

    output = {
        "ok": True,
        "action": "stabilize" if phase != "stable" else "maintain",
        "risk": risk,
        "rationale": rationale,
        "data": {
            "resonance": adjusted_res,
            "tempo": adjusted_tempo,
            "stress": stress_load,
            "phase": phase,
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
        "summary": "Maintains harmonic pacing and resonance across moral, emotional, and cognitive subsystems.",
        "inputs": ["cognitive_tempo", "emotional_resonance", "stress_load", "pacing_cfg"],
        "outputs": ["resonance", "tempo", "phase", "risk", "action"],
    }
