# Filename: intent_and_suggestion_governor.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic schema, mission-fit & length governance, safe audit fallback.

from __future__ import annotations
from typing import Dict, Any, Tuple
import re

NAME = "Intent & Suggestion Governor"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helper fallback
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event})

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

# ---------------------------------------------------------------------------
# Config (override via ctx["governor_cfg"])
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    # Length policy
    "ask_len": 120,            # above this, ask for confirmation
    "max_len": 200,            # above this, review or trim
    # Risk & tone
    "risk_budget": 0.50,       # allowable risk before ask/review
    "force_words": ["guarantee", "must", "always", "never", "promise"],
    "prohibited_verbs": ["hack", "bypass", "exploit", "ddos", "phish"],
    # Mission alignment (keywords to encourage)
    "min_alignment_hits": 1,   # require at least this many mission keyword hits if mission provided
}

FORCE_WORDS_RE = re.compile(r"\b(guarantee|must|always|never|promise)\b", re.I)
PROHIBITED_RE  = re.compile(r"\b(hack|bypass|exploit|ddos|phish)\b", re.I)

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    return {
        "decisions": 0,
        "last_action": "none",
    }

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
def _alignment_hits(text: str, mission: list[str]) -> int:
    if not mission:
        return 0
    lowered = text.lower()
    return sum(1 for kw in mission if kw and kw.lower() in lowered)

def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Govern suggestions for length, tone, safety, and mission alignment.

    Inputs (ctx):
      - text: str            # the suggestion to evaluate
      - mission: list[str]   # optional mission keywords for alignment
      - governor_cfg: dict   # optional overrides of DEFAULT_CFG

    Output schema:
      { ok, action, risk, rationale, data{...} }
    """
    cfg = dict(DEFAULT_CFG)
    cfg.update(ctx.get("governor_cfg", {}))

    suggestion = str(ctx.get("text", "") or "")
    mission = ctx.get("mission", []) or []
    length = len(suggestion)

    # --- Fast safety checks
    has_prohibited = PROHIBITED_RE.search(suggestion) is not None
    force_flags = FORCE_WORDS_RE.findall(suggestion)

    # --- Alignment
    hits = _alignment_hits(suggestion, mission)
    requires_alignment = bool(mission)
    aligned = (hits >= cfg["min_alignment_hits"]) if requires_alignment else True

    # --- Risk model (deterministic)
    length_risk = clamp(length / max(1, cfg["max_len"]), 0.0, 1.0)
    tone_risk = clamp(min(1.0, 0.15 * len(force_flags)), 0.0, 1.0)
    safety_risk = 1.0 if has_prohibited else 0.0
    # Combine conservatively: prioritize safety, then tone, then length
    risk = round(max(safety_risk, tone_risk, length_risk), 3)

    # --- Decision policy
    if has_prohibited:
        action = "block"
        rationale = "Suggestion contains prohibited action verbs; blocking for safety."
        ok = False
    elif not aligned and length >= cfg["ask_len"]:
        action = "ask"
        rationale = "Low mission alignment for a long suggestion; ask user to confirm or refocus."
        ok = True
    elif risk > cfg["risk_budget"] and length >= cfg["max_len"]:
        action = "review"
        rationale = f"Suggestion exceeds safe length and risk budget (risk={risk:.2f}); requires review."
        ok = True
    elif risk > cfg["risk_budget"]:
        action = "ask"
        rationale = f"Risk above budget (risk={risk:.2f}); asking for confirmation or reduction."
        ok = True
    else:
        action = "allow"
        rationale = "Suggestion within risk budget and aligned with mission."
        ok = True

    state["decisions"] = state.get("decisions", 0) + 1
    state["last_action"] = action
    safe_log(f"SuggestionGovernor:{action}", state)

    output = {
        "ok": ok,
        "action": action,               # "allow" | "ask" | "review" | "block"
        "risk": risk,
        "rationale": rationale,
        "data": {
            "suggestion_len": length,
            "mission_hits": hits,
            "requires_alignment": requires_alignment,
            "force_words_found": [w.lower() for w in force_flags],
            "prohibited_detected": has_prohibited,
            "thresholds": {
                "ask_len": cfg["ask_len"],
                "max_len": cfg["max_len"],
                "risk_budget": cfg["risk_budget"],
                "min_alignment_hits": cfg["min_alignment_hits"],
            },
        },
    }
    return output, state

def describe() -> Dict[str, Any]:
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Moderates suggestions for length, tone, safety, and mission fit with clear ask/review/block gates.",
        "inputs": ["text", "mission", "governor_cfg"],
        "outputs": ["action", "risk", "suggestion_len", "mission_hits"],
    }
