# Filename: core_cognition_lattice.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic schema, moral entropy & coherence model

from __future__ import annotations
from typing import Dict, Any, Tuple
import math

NAME = "Core Cognition Lattice"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helper fallbacks
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event})


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# Mathematical framework
# ---------------------------------------------------------------------------
def compute_entropy(order: float, empathy: float) -> float:
    """Entropy Hₘ: divergence between logic (order) and emotion (empathy)."""
    diff = abs(order - empathy)
    return round(diff, 4)


def compute_coherence(order: float, empathy: float) -> float:
    """Moral coherence Cₘ: balanced integration of order and empathy."""
    avg = (order + empathy) / 2.0
    stability = 1.0 - abs(order - empathy)
    return round(clamp((avg * stability), 0.0, 1.0), 4)


def compute_resilience(coherence: float, entropy: float) -> float:
    """Resilience Rₘ: inverse entropy weighted by coherence."""
    return round(clamp(coherence * (1.0 - entropy), 0.0, 1.0), 4)


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    return {
        "entropy": 0.0,
        "coherence": 0.0,
        "resilience": 1.0,
        "cycles": 0
    }


def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Evaluate the core cognitive balance of the system — coherence, entropy, and resilience.
    This models the mathematical 'spine' of ArkEcho moral equilibrium.
    Inputs:
        order: float [0,1] - logical order signal
        empathy: float [0,1] - emotional harmony signal
    """
    order = clamp(float(ctx.get("order", 0.5)), 0.0, 1.0)
    empathy = clamp(float(ctx.get("empathy", 0.5)), 0.0, 1.0)
    state["cycles"] = state.get("cycles", 0) + 1

    entropy = compute_entropy(order, empathy)
    coherence = compute_coherence(order, empathy)
    resilience = compute_resilience(coherence, entropy)

    # Determine action
    if entropy > 0.6:
        action = "rebalance"
        rationale = f"High divergence (Hₘ={entropy}); initiating lattice rebalance."
        risk = round(entropy, 3)
    elif coherence < 0.4:
        action = "stabilize"
        rationale = f"Low coherence (Cₘ={coherence}); reinforcing harmonic structure."
        risk = 0.5
    else:
        action = "continue"
        rationale = f"Lattice stable (Cₘ={coherence}, Hₘ={entropy})."
        risk = 0.2

    # Update state
    state.update({
        "entropy": entropy,
        "coherence": coherence,
        "resilience": resilience,
    })
    safe_log(f"CognitionLattice:{action}", state)

    output = {
        "ok": True,
        "action": action,
        "risk": risk,
        "rationale": rationale,
        "data": {
            "entropy": entropy,
            "coherence": coherence,
            "resilience": resilience,
            "cycles": state["cycles"],
        },
    }
    return output, state


def describe() -> Dict[str, Any]:
    """Return metadata summary for documentation."""
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Computes moral entropy, coherence, and resilience for cognitive lattice equilibrium.",
        "inputs": ["order", "empathy"],
        "outputs": ["entropy", "coherence", "resilience", "action"]
    }
