# Filename: integrity_monitor.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic schema, coherence integrity scoring, and audit fallback.

from __future__ import annotations
from typing import Dict, Any, Tuple

NAME = "Integrity Monitor"
VERSION = "1.1.0"


# ---------------------------------------------------------------------------
# Helper fallback
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event})


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize state for integrity tracking."""
    return {"last_outputs": [], "coherence_score": 1.0, "contradictions": 0}


def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Check for logical or moral contradictions in outputs to maintain system coherence.
    Inputs:
      ctx["output"]: optional string from last system action
    """
    last_output = ctx.get("output", "")
    outputs = state.get("last_outputs", [])
    outputs.append(last_output)
    state["last_outputs"] = outputs[-10:]  # keep short history

    contradictions = False
    if len(outputs) >= 2 and outputs[-1] != "" and outputs.count(outputs[-1]) > 1:
        contradictions = True

    coherence_score = 1.0 - (0.2 * outputs.count(outputs[-1])) if contradictions else 1.0

    if contradictions:
        action = "pause"
        rationale = "Detected repeated or conflicting output; pausing for self-alignment."
        risk = 0.5
    else:
        action = "allow"
        rationale = "No contradiction found; coherence intact."
        risk = 0.1

    state["coherence_score"] = round(coherence_score, 3)
    state["contradictions"] = contradictions
    safe_log(f"Integrity:{action}", state)

    output = {
        "ok": not contradictions,
        "action": action,
        "risk": risk,
        "rationale": rationale,
        "data": {
            "contradictions": contradictions,
            "coherence_score": coherence_score,
            "recent_outputs": outputs[-3:]
        },
    }
    return output, state


def describe() -> Dict[str, Any]:
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Monitors output stream for contradictions or incoherence to preserve system integrity.",
        "inputs": ["output"],
        "outputs": ["contradictions", "coherence_score", "action", "risk"]
    }
