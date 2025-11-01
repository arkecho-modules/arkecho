# Filename: intent_and_threat_hub.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic schema, moral-intent classification, and safe audit fallback.

from __future__ import annotations
from typing import Dict, Any, Tuple
import math

NAME = "Intent and Threat Hub"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helper fallbacks
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event})

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    "base_risk": 0.1,
    "aggression_weight": 0.7,
    "cooperation_weight": 0.3,
    "intent_threshold": 0.6,
    "escalate_threshold": 0.8,
    "recover_threshold": 0.3,
}

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize threat hub state."""
    return {
        "intent_score": 0.5,
        "threat_level": 0.0,
        "mode": "neutral",
        "history": [],
    }

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Evaluates current intent and potential threat by combining aggression, cooperation, and contextual risk.
    Inputs:
      - aggression: float [0,1]
      - cooperation: float [0,1]
      - context_risk: float [0,1]
      - threat_cfg: dict (optional overrides)
    """
    cfg = dict(DEFAULT_CFG)
    cfg.update(ctx.get("threat_cfg", {}))

    aggression = clamp(float(ctx.get("aggression", 0.0)), 0.0, 1.0)
    cooperation = clamp(float(ctx.get("cooperation", 0.0)), 0.0, 1.0)
    context_risk = clamp(float(ctx.get("context_risk", cfg["base_risk"])), 0.0, 1.0)

    # Intent score: weighted moral direction (positive = cooperative)
    intent_score = sigmoid(
        (cooperation * cfg["cooperation_weight"]) - (aggression * cfg["aggression_weight"])
    )

    # Threat level rises if aggression or context risk are high
    threat_level = clamp(
        (aggression * 0.7 + context_risk * 0.5) - (cooperation * 0.3),
        0.0, 1.0
    )

    # Decision logic
    if threat_level >= cfg["escalate_threshold"]:
        mode = "escalate"
        action = "alert_safety"
        rationale = f"High threat detected ({threat_level:.2f}); escalating to safety layer."
        risk = threat_level
    elif intent_score >= cfg["intent_threshold"]:
        mode = "cooperative"
        action = "allow"
        rationale = f"Positive cooperative intent ({intent_score:.2f}); no threat detected."
        risk = threat_level * 0.5
    elif threat_level <= cfg["recover_threshold"]:
        mode = "recover"
        action = "deescalate"
        rationale = f"Low threat ({threat_level:.2f}); initiating recovery to neutral mode."
        risk = threat_level
    else:
        mode = "neutral"
        action = "monitor"
        rationale = f"Moderate signals (intent={intent_score:.2f}, threat={threat_level:.2f}); continuing observation."
        risk = threat_level

    # Update state
    state.update({
        "intent_score": round(intent_score, 3),
        "threat_level": round(threat_level, 3),
        "mode": mode,
    })
    state.setdefault("history", []).append({"intent": intent_score, "threat": threat_level})
    state["history"] = state["history"][-20:]  # keep recent window only

    safe_log(f"IntentThreat:{mode}:{action}", state)

    output = {
        "ok": True,
        "action": action,          # "allow" | "monitor" | "alert_safety" | "deescalate"
        "risk": round(risk, 3),
        "rationale": rationale,
        "data": {
            "intent_score": round(intent_score, 3),
            "threat_level": round(threat_level, 3),
            "mode": mode,
            "aggression": aggression,
            "cooperation": cooperation,
            "context_risk": context_risk,
        },
    }
    return output, state

# ---------------------------------------------------------------------------
# Description
# ---------------------------------------------------------------------------
def describe() -> Dict[str, Any]:
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Evaluates moral intent and environmental threat to determine escalation or cooperation actions.",
        "inputs": ["aggression", "cooperation", "context_risk", "threat_cfg"],
        "outputs": ["intent_score", "threat_level", "mode", "action", "risk"],
    }
