# ArkEcho Systems © 2025
# v11r1 deterministic refactor — cultural and audience adaptation module
# Ensures message alignment with empathy and context; now includes rationale.

from __future__ import annotations
from typing import Dict, Any, Tuple

def init() -> Dict[str, Any]:
    """Initialize audience adapter state."""
    return {"last_action": "none", "adjustments": 0}


def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Aligns system outputs with cultural and audience sensitivity parameters.
    Evaluates language tone, inclusivity, and empathy balance.
    """
    culture = ctx.get("culture", "general")
    tone = ctx.get("tone", "neutral")
    audience = ctx.get("audience", "public")

    sensitivity = 0.2 if culture == "general" else 0.1
    tone_factor = 0.2 if tone == "neutral" else 0.3
    audience_factor = 0.3 if audience in ("public", "youth") else 0.2

    risk = min(1.0, sensitivity + tone_factor + audience_factor)
    ok = risk < 0.8
    action = "allow" if ok else "revise"

    rationale = (
        "Cultural and audience parameters balanced successfully."
        if ok else
        "Cultural mismatch detected; revision recommended to ensure empathy and clarity."
    )

    state["last_action"] = action
    state["adjustments"] = state.get("adjustments", 0) + (0 if ok else 1)

    output = {
        "ok": ok,
        "action": action,
        "risk": risk,
        "rationale": rationale,
        "data": {
            "culture": culture,
            "tone": tone,
            "audience": audience,
            "adjustments": state["adjustments"],
        },
    }
    return output, state
