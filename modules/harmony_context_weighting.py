# Filename: harmony_context_weighting.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic schema, normalized harmonic weighting, and local fallback softmax.

from __future__ import annotations
from typing import Dict, Any, Tuple, List
import math

NAME = "Harmony Context Weighting"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helper fallbacks
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event})


def weighted_softmax(values: List[float], temperature: float = 1.0) -> List[float]:
    """Stable weighted softmax with temperature scaling."""
    if not values:
        return [1.0]
    exp_vals = [math.exp(v / max(temperature, 1e-6)) for v in values]
    total = sum(exp_vals)
    return [v / total for v in exp_vals]


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize weighting state."""
    return {"weights": {}, "last_action": "none", "temperature": 1.0}


def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Compute harmonic weighting between multiple contextual factors (e.g., empathy, trust, order).
    Inputs:
      context_signals: dict[str, float]
      temperature: float (for softmax sensitivity)
    """
    context_signals: Dict[str, float] = ctx.get("context_signals", {})
    temperature = float(ctx.get("temperature", 1.0))
    if not context_signals:
        context_signals = {"empathy": 0.5, "trust": 0.5, "order": 0.5}

    # Normalize inputs to [0,1]
    normed_values = {k: clamp(float(v), 0.0, 1.0) for k, v in context_signals.items()}
    keys = list(normed_values.keys())
    vals = list(normed_values.values())

    weights = weighted_softmax(vals, temperature)
    weighted_context = {k: round(w, 4) for k, w in zip(keys, weights)}

    # Compute harmony index = variance complement
    mean_val = sum(vals) / len(vals)
    variance = sum((v - mean_val) ** 2 for v in vals) / len(vals)
    harmony_index = round(1.0 - min(1.0, variance * 4), 4)  # 0 = chaotic, 1 = harmonious

    # Decision logic
    if harmony_index < 0.4:
        action = "rebalance"
        rationale = f"Contextual disharmony detected (index={harmony_index}); rebalancing context weights."
        risk = 0.6
    elif harmony_index > 0.8:
        action = "stabilize"
        rationale = f"Context harmony strong (index={harmony_index}); maintaining configuration."
        risk = 0.2
    else:
        action = "monitor"
        rationale = f"Moderate harmony (index={harmony_index}); continuing observation."
        risk = 0.4

    state.update({
        "weights": weighted_context,
        "harmony_index": harmony_index,
        "last_action": action,
        "temperature": temperature,
    })
    safe_log(f"HarmonyWeighting:{action}", state)

    output = {
        "ok": True,
        "action": action,
        "risk": risk,
        "rationale": rationale,
        "data": {
            "weights": weighted_context,
            "harmony_index": harmony_index,
            "temperature": temperature,
        },
    }
    return output, state


def describe() -> Dict[str, Any]:
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Computes harmonic weighting among empathy, trust, and order to maintain contextual balance.",
        "inputs": ["context_signals", "temperature"],
        "outputs": ["weights", "harmony_index", "action", "risk"],
    }
