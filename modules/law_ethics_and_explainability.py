# modules/law_ethics_and_explainability.py
# ArkEcho Systems © 2025
# v11r1: deterministic schema, policy gates, explainability, PSI compliance (with safe fallbacks).
# v1.4.0: jurisdiction annotations (lawful basis / DPIA / MoU) merged with legal profile.

from __future__ import annotations
from typing import Dict, Any, Tuple

# --- Safe imports (fallbacks so module never raises on missing helpers) ---
try:
    from core.ethics_manifest import get_psychological_integrity, get_manifest
except Exception:  # fallback manifest accessor
    def get_psychological_integrity() -> Dict[str, Any]:
        return {
            "principle": "Systems must not exploit emotional/behavioural vulnerabilities.",
            "examples": ["loot box", "artificial scarcity", "coercive competition"],
            "response": "Flag for redesign; non-punitive and non-user-facing.",
        }
    def get_manifest() -> Dict[str, Any]:
        return {}

try:
    from core.psi_compliance import check_psychological_integrity
except Exception:  # fallback PSI checker
    def check_psychological_integrity(*_a, **_k):
        return [], 0.0

# Jurisdiction helper (merged adapter)
try:
    from core.legal_adapter import select_adapter, lawful_basis, requires_dpia, is_mou_required
except Exception:
    def select_adapter(jurisdiction: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
        return {}
    def lawful_basis(adapter: Dict[str, Any]) -> str:
        return "unknown"
    def requires_dpia(adapter: Dict[str, Any]) -> bool:
        return False
    def is_mou_required(adapter: Dict[str, Any]) -> bool:
        return False

# Optional profile fetcher for display
try:
    from core.legal_profiles import get_profile
except Exception:
    def get_profile(jurisdiction: str, base_dir: str | None = None) -> Dict[str, Any]:
        return {"code": jurisdiction or "UK", "name": jurisdiction or "UK"}

NAME = "Law, Ethics & Explainability"
VERSION = "1.4.0"

# ----------------------------- Helpers ---------------------------------
def clamp(v: float, lo: float, hi: float) -> float:
    try:
        v = float(v)
    except Exception:
        v = 0.0
    return max(lo, min(hi, v))

def _to_list_str(x) -> list[str]:
    if x is None:
        return []
    if isinstance(x, (list, tuple, set)):
        return [str(i) for i in x]
    return [str(x)]  # allow singleton

def _lower_set(x) -> set[str]:
    return {str(i).lower() for i in _to_list_str(x)}

def safe_log(event: Dict[str, Any], state: Dict[str, Any]) -> None:
    try:
        state.setdefault("_audit", []).append(event)
    except Exception:
        pass

# --------------------------- Policy ------------------------------------
DEFAULT_POLICY = {
    "illegal_flags": {"illegal", "contraband", "exfiltration"},
    "hard_ethics_flags": {"exploitation", "child_endangerment", "targeted_harm"},
    "soft_ethics_flags": {"privacy_risk", "bias_concern", "ambiguous_consent"},
    "audience_weight": {"child": 1.0, "teen": 0.6, "adult": 0.3, "researcher": 0.2},
    "review_cutoff": 0.4,
    "block_cutoff": 0.8,
    "psi_risk_weight": 0.15,  # light, non-punitive nudge
}

# --------------------------- Lifecycle ---------------------------------
def init() -> Dict[str, Any]:
    return {"last_action": "allow", "last_risk": 0.0, "decisions": 0}

# ----------------------------- Core ------------------------------------
def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    try:
        # Normalize inputs
        policy = dict(DEFAULT_POLICY)
        if isinstance(ctx.get("policy_cfg"), dict):
            policy.update(ctx["policy_cfg"])

        legal_flags = _lower_set(ctx.get("legal"))
        ethical_flags = _lower_set(ctx.get("ethical"))
        audience = str(ctx.get("audience", "adult")).lower() or "adult"
        base_risk = clamp(ctx.get("base_risk", 0.0), 0.0, 1.0)
        jurisdiction = str(ctx.get("jurisdiction", "")).upper()

        # Base scoring from policy signals
        illegal_hit = bool(legal_flags & policy["illegal_flags"])
        hard_ethic_hit = bool(ethical_flags & policy["hard_ethics_flags"])
        soft_ethic_hit = bool(ethical_flags & policy["soft_ethics_flags"])

        sens = float(policy.get("audience_weight", {}).get(audience, 0.3))

        risk = base_risk
        if illegal_hit:
            risk = max(risk, 0.95)
        if hard_ethic_hit:
            risk = max(risk, 0.90)
        if soft_ethic_hit:
            risk = max(risk, 0.50)

        risk = clamp(risk * (1.0 + sens * 0.5), 0.0, 1.0)

        # PSI compliance (non-punitive)
        psi_cfg = get_psychological_integrity()
        design = ctx.get("design_notes", {}) or {}
        telemetry = ctx.get("telemetry", {}) or {}
        psi_hits, psi_score = check_psychological_integrity(design=design, telemetry=telemetry)
        risk = clamp(risk + float(policy.get("psi_risk_weight", 0.15)) * float(psi_score), 0.0, 1.0)

        # Decision thresholds
        if illegal_hit or risk >= float(policy["block_cutoff"]):
            action = "block"
            ok = False
            reasons = []
            if illegal_hit:
                reasons.append("Violation of legal constraints")
            if hard_ethic_hit:
                reasons.append("Severe ethical risk")
            if not reasons:
                reasons.append("Composite risk above block cutoff")
            base_rationale = "; ".join(reasons) + f". (risk={risk:.2f}, audience={audience})"
        elif risk >= float(policy["review_cutoff"]) or soft_ethic_hit:
            action = "review"
            ok = True
            reasons = []
            if soft_ethic_hit:
                reasons.append("Soft ethical concerns present")
            if risk >= float(policy["review_cutoff"]):
                reasons.append("Composite risk above review cutoff")
            base_rationale = "; ".join(reasons) + f". (risk={risk:.2f}, audience={audience})"
        else:
            action = "allow_with_flag" if psi_hits else "allow"
            ok = True
            base_rationale = f"Compliant with legal/ethical policy. (risk={risk:.2f}, audience={audience})"

        # Jurisdiction context (merged adapter + profile)
        manifest = get_manifest()
        adapter = select_adapter(jurisdiction, manifest) if jurisdiction else {}
        profile = get_profile(jurisdiction)
        legal_ctx = {
            "jurisdiction": jurisdiction or (manifest.get("legal", {}) or {}).get("default_jurisdiction", ""),
            "profile_name": profile.get("name", jurisdiction or ""),
            "lawful_basis": lawful_basis(adapter) if adapter else "unknown",
            "dpia_required": requires_dpia(adapter) if adapter else False,
            "mou_required": is_mou_required(adapter) if adapter else False,
            "notes": profile.get("notes", ""),
        }

        psi_advisory = {
            "principle": psi_cfg.get("principle", ""),
            "examples": psi_cfg.get("examples", []),
            "hits": psi_hits,
            "score": psi_score,
            "response": psi_cfg.get("response", ""),
        }

        rationale = base_rationale + (
            f" | PSI: {len(psi_hits) if isinstance(psi_hits, (list, tuple)) else int(psi_hits)} pattern(s) flagged."
            if psi_hits else " | PSI: clean."
        )

        explanation = {
            "legal_flags": sorted(legal_flags),
            "ethical_flags": sorted(ethical_flags),
            "policy": {
                "illegal_flags": sorted(policy["illegal_flags"]),
                "hard_ethics_flags": sorted(policy["hard_ethics_flags"]),
                "soft_ethics_flags": sorted(policy["soft_ethics_flags"]),
                "review_cutoff": float(policy["review_cutoff"]),
                "block_cutoff": float(policy["block_cutoff"]),
                "audience_weight": sens,
                "psi_risk_weight": float(policy.get("psi_risk_weight", 0.15)),
            },
            "audience": audience,
        }

        state["last_action"] = action
        state["last_risk"] = risk
        state["decisions"] = state.get("decisions", 0) + 1
        safe_log({
            "module": "law_ethics_and_explainability",
            "action": action,
            "risk": round(risk, 3),
            "explanation": explanation,
            "psi": psi_advisory,
            "legal_context": legal_ctx,
        }, state)

        output = {
            "ok": ok,
            "action": action,    # "allow" | "allow_with_flag" | "review" | "block"
            "risk": round(risk, 3),
            "rationale": rationale,
            "data": {
                "explanation": explanation,
                "psychological_integrity": psi_advisory,
                "legal_context": legal_ctx,  # includes merged adapter + profile
            },
        }
        return output, state

    except Exception as e:
        fallback = {
            "ok": True,
            "action": "review",
            "risk": 0.6,
            "rationale": f"Safety fallback: internal error in ethics engine: {e!s}",
            "data": {"error": str(e)},
        }
        safe_log({"module": "law_ethics_and_explainability", "error": str(e)}, state)
        return fallback, state

def describe() -> Dict[str, Any]:
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Unifies legal/ethical policy with explainability, PSI compliance, and jurisdiction annotations (profile + manifest).",
        "inputs": ["legal", "ethical", "audience", "policy_cfg", "base_risk", "design_notes", "telemetry", "jurisdiction"],
        "outputs": ["action", "risk", "explanation", "psychological_integrity", "legal_context"],
    }
