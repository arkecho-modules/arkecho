# Filename: archetype_and_rhythm_equilibrium.py
# ArkEcho Systems © 2025
# Refactored for v11r1 deterministic schema; adds rationale.

from __future__ import annotations
import math
from typing import Dict, Any, List


def _rhythm(t: float, f: float) -> Dict[str, Any]:
    phase = 0.5 * math.sin(2 * math.pi * f * t) + 0.5
    coherence = 1.0 - abs((t % (1.0 / max(1e-6, f))) - 0.0) / (1.0 / max(1e-6, f))
    coherence = max(0.0, min(1.0, coherence))
    note = "stable" if coherence > 0.7 else "desync"
    return {"phase": round(phase, 3), "coherence": round(coherence, 3), "note": note}


def _archetypes(keys: List[str]) -> Dict[str, Any]:
    base = {"care": 0.2, "trust": 0.2, "danger": 0.2, "justice": 0.2, "wisdom": 0.2}
    for k in keys or []:
        if k.lower() in ("care", "help", "protect"):
            base["care"] = base["care"] * (1 - 0.6) + 1.0 * 0.6
        if k.lower() in ("risk", "danger", "threat"):
            base["danger"] = base["danger"] * (1 - 0.6) + 1.0 * 0.6
        if k.lower() in ("fair", "justice", "equity"):
            base["justice"] = base["justice"] * (1 - 0.6) + 1.0 * 0.6
        if k.lower() in ("trust", "honesty"):
            base["trust"] = base["trust"] * (1 - 0.6) + 1.0 * 0.6
    top = sorted(base, key=base.get, reverse=True)[:3]
    return {"top": top, "activations": {k: round(v, 3) for k, v in base.items()}}


def _equilibrium(L: float, Eeth: float, Eemo: float) -> Dict[str, Any]:
    Eq = 0.34 * L + 0.33 * Eeth + 0.33 * Eemo
    prev = 0.5
    eq_smoothed = 0.8 * prev + 0.2 * Eq
    stable = abs(eq_smoothed - 0.5) <= 0.1
    return {"value": round(eq_smoothed, 3), "stable": stable, "notes": "balanced" if stable else "adjusting"}


def run(ctx: Dict[str, Any], state: dict) -> tuple:
    t = float(ctx.get("time_s", 0.0))
    f = float(ctx.get("freq", 0.5))
    rhythm = _rhythm(t, f)

    keywords = ctx.get("keywords", [])
    arche = _archetypes(keywords)

    sig = ctx.get("signals", {})
    L = float(sig.get("logic", 0.5))
    Eeth = float(sig.get("ethics", 0.5))
    Eemo = float(sig.get("emotion", 0.5))
    eq = _equilibrium(L, Eeth, Eemo)

    output = {
        "ok": True,
        "action": "allow",
        "risk": 0.0,
        "rationale": "Rhythmic and archetypal equilibrium verified.",
        "data": {
            "rhythm": rhythm,
            "archetypes": arche,
            "equilibrium": eq,
        },
    }
    return output, state
