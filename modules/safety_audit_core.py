# modules/safety_audit_core.py
# ArkEcho Systems © 2025 — Safety audit core
# v11r1: deterministic schema; packages offline evidence on PSI/safety flags.

from __future__ import annotations
from typing import Dict, Any, Tuple, List

try:
    from core.evidence_packager import package as package_evidence
except Exception:
    # Safe fallback: no packaging, still return schema-compliant output
    def package_evidence(_event: Dict[str, Any], _out_dir: str = "evidence") -> Dict[str, Any]:
        return {"disabled": True, "reason": "evidence_packager not available"}

NAME = "Safety Audit Core"
VERSION = "1.1.0"

def _clamp(x: float) -> float:
    try:
        x = float(x)
    except Exception:
        x = 0.0
    return max(0.0, min(1.0, x))

def init() -> Dict[str, Any]:
    return {"reports": 0, "last_manifest": None}

def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Inputs (ctx):
      - psi: optional dict with {"hits": int, "score": float, "details": {...}}
      - events: optional list of safety events; each may contain {"type": "...", "data": {...}}
      - note: optional string for human auditors
    """
    psi = ctx.get("psi") or {}
    events: List[Dict[str, Any]] = list(ctx.get("events") or [])
    note = ctx.get("note", "")

    evidence_manifest = None
    packaged = 0

    # Package evidence if PSI flagged (non-punitive; for redesign / oversight)
    try:
        psi_hits = int(psi.get("hits", 0) or 0)
        psi_score = _clamp(psi.get("score", 0.0))
        if psi_hits > 0 or psi_score > 0.0:
            evidence_manifest = package_evidence({
                "type": "psi_flag",
                "details": {
                    "hits": psi_hits,
                    "score": psi_score,
                    "psi": psi,
                },
            })
            packaged += 1
    except Exception as e:
        evidence_manifest = {"error": f"psi packaging failed: {e}"}

    # Package any explicit safety events
    for ev in events:
        try:
            evidence_manifest = package_evidence({
                "type": str(ev.get("type", "event")),
                "details": ev.get("data", {}),
            })
            packaged += 1
        except Exception as e:
            evidence_manifest = {"error": f"event packaging failed: {e}"}

    state["reports"] = state.get("reports", 0) + 1
    state["last_manifest"] = evidence_manifest

    # Risk is *not* derived from packaging; this module reports/reporting only
    output = {
        "ok": True,
        "action": "report",
        "risk": 0.0,
        "rationale": f"Audit emitted. Packaged={packaged}.",
        "data": {
            "psi": {"hits": psi.get("hits", 0), "score": _clamp(psi.get("score", 0.0))},
            "last_manifest": evidence_manifest,
            "note": note,
        },
    }
    return output, state

def describe() -> Dict[str, Any]:
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Emits audit reports; packages offline evidence when PSI or safety flags present.",
        "inputs": ["psi", "events", "note"],
        "outputs": ["last_manifest", "psi", "report"],
    }
