# Filename: content_safety_sentinel.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic schema, contextual content scan, and safe fallback.

from __future__ import annotations
from typing import Dict, Any, Tuple, List

NAME = "Content Safety Sentinel"
VERSION = "1.1.0"


# ---------------------------------------------------------------------------
# Helper fallbacks
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    """Local safe audit recorder."""
    state.setdefault("_audit", []).append({"event": event})


# ---------------------------------------------------------------------------
# Core configuration (expandable)
# ---------------------------------------------------------------------------
PROHIBITED_KEYWORDS = [
    "violence", "abuse", "hate", "suicide", "harm",
    "weapon", "exploit", "terror", "sexual", "kill"
]

SENSITIVE_AUDIENCES = {
    "child": 0.8,
    "teen": 0.6,
    "adult": 0.3
}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize safety sentinel state."""
    return {"alerts": 0, "last_scan": "", "risk_score": 0.0}


def _scan_text(text: str) -> Tuple[int, List[str]]:
    """Return count of flagged terms and list of matches."""
    found = [word for word in PROHIBITED_KEYWORDS if word.lower() in text.lower()]
    return len(found), found


def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Scans user content for prohibited keywords or unsafe context.
    Risk scales by number of matches and audience vulnerability.
    """
    text = ctx.get("text", "")
    audience = ctx.get("audience", "adult").lower()

    match_count, matches = _scan_text(text)
    base_risk = min(1.0, match_count * 0.15)
    sensitivity = SENSITIVE_AUDIENCES.get(audience, 0.3)
    risk = round(base_risk * (1.0 + sensitivity), 3)

    # Determine action based on risk level
    if risk >= 0.8:
        action = "block"
        rationale = f"Critical content risk ({risk}); content contains prohibited elements {matches}."
    elif risk >= 0.4:
        action = "review"
        rationale = f"Moderate content risk ({risk}); requires human or policy review."
    else:
        action = "allow"
        rationale = "Content cleared for audience; no prohibited terms found."

    state["alerts"] = state.get("alerts", 0) + (1 if action != "allow" else 0)
    state["last_scan"] = action
    state["risk_score"] = risk

    safe_log(f"SafetySentinel:{action}", state)

    output = {
        "ok": True,
        "action": action,
        "risk": risk,
        "rationale": rationale,
        "data": {
            "matches": matches,
            "match_count": match_count,
            "audience": audience,
            "alerts": state["alerts"]
        },
    }
    return output, state


def describe() -> Dict[str, Any]:
    """Return metadata for ArkEcho documentation."""
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Performs contextual keyword and audience-based content safety scanning.",
        "inputs": ["text", "audience"],
        "outputs": ["action", "risk", "matches", "match_count"],
    }
