# Filename: collective_governance_mesh.py
# ArkEcho Systems © 2025
# Refactored for v11r1 deterministic schema, governance quorum logic, and safe audit fallback.

from __future__ import annotations
from typing import Dict, Any, Tuple, List
import statistics

NAME = "Collective Governance Mesh"
VERSION = "1.1.0"


# ---------------------------------------------------------------------------
# Helper fallbacks
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    """Append governance audit entries safely."""
    state.setdefault("_audit", []).append({"event": event})


def consensus(values: List[float]) -> float:
    """Compute a consensus confidence value (mean ± stability penalty)."""
    if not values:
        return 0.0
    mean_val = statistics.mean(values)
    deviation = statistics.pstdev(values)
    return round(max(0.0, mean_val - deviation), 4)


# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize governance mesh state."""
    return {"members": [], "last_decision": "none", "confidence": 0.0}


def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Simulate decentralized ethical governance consensus.
    Each participant provides a risk or trust rating; the mesh computes a stable consensus.
    """
    # Inputs
    inputs = ctx.get("member_scores", [])
    risk_context = float(ctx.get("risk", 0.0))
    members = state.setdefault("members", [])

    # Merge new members
    if isinstance(inputs, list):
        for val in inputs:
            if isinstance(val, (int, float)):
                members.append(float(val))
    # Keep last 10 members only (rolling window)
    members = members[-10:]

    confidence = consensus(members)
    adjusted_confidence = round(confidence * (1.0 - risk_context), 4)

    # Decision logic
    if adjusted_confidence > 0.75:
        action = "approve"
        rationale = f"Consensus strong ({adjusted_confidence:.2f}); decision approved."
        risk = 0.1
    elif adjusted_confidence < 0.4:
        action = "reject"
        rationale = f"Consensus weak ({adjusted_confidence:.2f}); deferring for re-evaluation."
        risk = 0.7
    else:
        action = "review"
        rationale = f"Consensus moderate ({adjusted_confidence:.2f}); routing for manual review."
        risk = 0.5

    state.update({
        "members": members,
        "last_decision": action,
        "confidence": adjusted_confidence
    })
    safe_log(f"GovernanceMesh:{action}", state)

    output = {
        "ok": True,
        "action": action,
        "risk": risk,
        "rationale": rationale,
        "data": {
            "members": members,
            "confidence": adjusted_confidence,
            "member_count": len(members),
        },
    }
    return output, state


def describe() -> Dict[str, Any]:
    """Describe module for registry and auto-docs."""
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Aggregates distributed trust and risk scores to reach ethical governance consensus.",
        "inputs": ["member_scores", "risk"],
        "outputs": ["action", "confidence", "member_count"],
    }
