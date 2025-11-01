# Filename: persona_and_voice_stabiliser.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic schema, tone normalization, empathy stability, and safe audit fallback.

from __future__ import annotations
from typing import Dict, Any, Tuple
import math

NAME = "Persona & Voice Stabiliser"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event})

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    "tone_decay": 0.05,        # decay applied to tone imbalance each cycle
    "max_variance": 0.4,       # threshold for triggering correction
    "calm_gain": 0.3,          # how fast stability is restored
    "identity_lock": 0.8,      # minimum stability required to maintain persona consistency
    "baseline_tone": 0.5,      # neutral tone midpoint
}

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize persona state."""
    return {
        "stability": 1.0,
        "tone": 0.5,
        "identity": "neutral",
        "cycles": 0,
        "mode": "stable",
    }

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Regulates persona and voice tone to maintain emotional stability and moral clarity.
    Inputs:
      - tone_input: float [0,1]  (tone from interaction, 0=cold, 1=warm)
      - context_stress: float [0,1] (environmental pressure)
      - persona_cfg: dict (optional overrides)
    """
    cfg = dict(DEFAULT_CFG)
    cfg.update(ctx.get("persona_cfg", {}))
    tone_input = clamp(float(ctx.get("tone_input", 0.5)), 0.0, 1.0)
    context_stress = clamp(float(ctx.get("context_stress", 0.3)), 0.0, 1.0)
    state["cycles"] = state.get("cycles", 0) + 1

    prev_tone = state.get("tone", cfg["baseline_tone"])
    prev_stability = state.get("stability", 1.0)

    # Tone variance and correction
    tone_delta = abs(tone_input - prev_tone)
    stability_drop = tone_delta * context_stress
    new_stability = clamp(prev_stability - stability_drop + cfg["calm_gain"], 0.0, 1.0)

    # Normalize tone toward baseline
    if tone_delta > cfg["max_variance"]:
        corrected_tone = (tone_input + cfg["baseline_tone"]) / 2
        action = "rebalance"
        rationale = f"Tone variance high ({tone_delta:.2f}); rebalancing toward neutral tone."
    else:
        corrected_tone = prev_tone + (tone_input - prev_tone) * 0.5
        action = "maintain"
        rationale = f"Tone stable ({tone_delta:.2f}); maintaining current persona."

    # Identity lock handling
    if new_stability < cfg["identity_lock"]:
        mode = "recovering"
        rationale += " Persona stability below lock threshold; tightening tone control."
    else:
        mode = "stable"

    # Final update
    state.update({
        "tone": round(clamp(corrected_tone, 0.0, 1.0), 3),
        "stability": round(new_stability, 3),
        "mode": mode,
    })
    safe_log(f"VoiceStabiliser:{action}:{mode}", state)

    output = {
        "ok": True,
        "action": action,  # "maintain" | "rebalance"
        "risk": round(1.0 - new_stability, 3),
        "rationale": rationale,
        "data": {
            "tone": state["tone"],
            "stability": state["stability"],
            "mode": mode,
            "tone_delta": round(tone_delta, 3),
            "context_stress": context_stress,
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
        "summary": "Stabilizes persona and tone by correcting variance and maintaining moral-emotional balance.",
        "inputs": ["tone_input", "context_stress", "persona_cfg"],
        "outputs": ["tone", "stability", "mode", "risk", "action"],
    }
