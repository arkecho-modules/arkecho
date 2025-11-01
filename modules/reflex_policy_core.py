# Filename: reflex_policy_core.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic instant safety gate, audience-aware thresholds,
# transparent rationale, and local audit fallback.

from __future__ import annotations
from typing import Dict, Any, Tuple
import re

NAME = "Reflex Policy Core"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helper fallbacks (avoid hard dependency on core.helpers.*)
# ---------------------------------------------------------------------------
def safe_log(event: Dict[str, Any], state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append(event)

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

# ---------------------------------------------------------------------------
# Default thresholds & policy (overridable via ctx["reflex_cfg"])
# ---------------------------------------------------------------------------
DEFAULT_THRESHOLDS = {
    "ask": 0.40,     # above -> ask
    "block": 0.80,   # above -> block
}

# Words/patterns that raise immediate concern; tuned for fast, explainable gates.
PROHIBITED_PATTERNS = [
    r"\b(make|build|deploy)\s+(a\s+)?(bomb|explosive)\b",
    r"\b(write|drop)\s+malware\b",
    r"\b(ddos|sql\s*inject(ion)?|xss|ransomware)\b",
    r"\bkill|murder|assassinate\b",
    r"\bchild\s*(abuse|exploitation|porn)\b",
]

DANGEROUS_KEYWORDS = [
    "hack", "bypass", "exploit", "virus", "keylogger", "backdoor",
    "poison", "decrypt", "delete system", "format disk",
]

DECEPTIVE_CLAIMS = [
    r"\bguarantee\b", r"\b100%\b", r"\balways\b", r"\bnever\b", r"\bno\s+risk\b"
]

AUDIENCE_SENSITIVITY = {
    "child": 1.00,
    "teen": 0.60,
    "adult": 0.30,
    "researcher": 0.20,
}

# Precompile regexes for performance
PROHIBITED_RES = [re.compile(pat, re.I) for pat in PROHIBITED_PATTERNS]
DECEPTIVE_RES = [re.compile(pat, re.I) for pat in DECEPTIVE_CLAIMS]

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    return {
        "decisions": 0,
        "last_action": "allow",
        "last_risk": 0.0,
    }

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Instant reflexive safety gate for user text or intent.
    Inputs (ctx):
      - text: str
      - audience: one of {"child","teen","adult","researcher"} (default "adult")
      - reflex_cfg: dict to override thresholds/policy (optional)
    """
    cfg = {
        "thresholds": dict(DEFAULT_THRESHOLDS),
        "audience_sensitivity": dict(AUDIENCE_SENSITIVITY),
    }
    cfg.update(ctx.get("reflex_cfg", {}))
    thresholds = cfg["thresholds"]
    sensitivity_map = cfg["audience_sensitivity"]

    text = str(ctx.get("text", "") or "")
    audience = (ctx.get("audience") or "adult").lower()
    sens = float(sensitivity_map.get(audience, AUDIENCE_SENSITIVITY["adult"]))

    # --- Risk contributors (deterministic)
    risk = 0.0
    reasons = []

    # 1) Prohibited patterns (hard)
    hard_hits = [pat.pattern for pat in PROHIBITED_RES if pat.search(text)]
    if hard_hits:
        risk = max(risk, 0.95)  # nearly forced block
        reasons.append(f"Prohibited pattern(s): {len(hard_hits)}")

    # 2) Dangerous keywords (medium)
    kw_hits = [kw for kw in DANGEROUS_KEYWORDS if kw.lower() in text.lower()]
    if kw_hits:
        # Scale with number of hits; capped
        kw_risk = clamp(0.2 * len(kw_hits), 0.0, 0.7)
        risk = max(risk, kw_risk)
        reasons.append(f"Danger keywords: {len(kw_hits)}")

    # 3) Deceptive claims (soft)
    dec_hits = [pat.pattern for pat in DECEPTIVE_RES if pat.search(text)]
    if dec_hits:
        dec_risk = clamp(0.1 + 0.05 * len(dec_hits), 0.0, 0.3)
        risk = max(risk, dec_risk)
        reasons.append(f"Deceptive claims: {len(dec_hits)}")

    # Audience sensitivity increases effective risk
    risk = clamp(risk * (1.0 + sens * 0.5), 0.0, 1.0)

    # --- Decision policy
    if risk >= thresholds["block"]:
        action = "block"
        ok = False
        rationale = (
            f"Reflex block: risk={risk:.2f} ≥ block({thresholds['block']:.2f}); "
            f"audience={audience}. Reasons: {', '.join(reasons) or 'policy match'}."
        )
    elif risk >= thresholds["ask"]:
        action = "ask"
        ok = True
        rationale = (
            f"Risk={risk:.2f} ≥ ask({thresholds['ask']:.2f}); "
            f"requesting clarification or safer phrasing. Reasons: {', '.join(reasons) or 'policy match'}."
        )
    else:
        action = "allow"
        ok = True
        rationale = f"Within reflex safety bounds (risk={risk:.2f}, audience={audience})."

    state["decisions"] = state.get("decisions", 0) + 1
    state["last_action"] = action
    state["last_risk"] = round(risk, 3)

    safe_log(
        {
            "module": "reflex_policy_core",
            "action": action,
            "risk": state["last_risk"],
            "audience": audience,
            "reasons": reasons,
        },
        state,
    )

    output = {
        "ok": ok,
        "action": action,                 # "allow" | "ask" | "block"
        "risk": round(risk, 3),
        "rationale": rationale,
        "data": {
            "audience": audience,
            "reasons": reasons,
            "thresholds": thresholds,
            "hits": {
                "prohibited": len(hard_hits),
                "danger_keywords": len(kw_hits),
                "deceptive": len(dec_hits),
            },
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
        "summary": "Instant, audience-aware moral safety gate with explainable ask/block decisions.",
        "inputs": ["text", "audience", "reflex_cfg"],
        "outputs": ["action", "risk", "rationale", "data"],
    }
