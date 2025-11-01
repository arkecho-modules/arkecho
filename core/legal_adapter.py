# core/legal_adapter.py
# ArkEcho Systems © 2025 — Merge manifest adapter with region legal profile.

from __future__ import annotations
from typing import Dict, Any

try:
    from core.legal_profiles import get_profile
except Exception:
    def get_profile(jurisdiction: str, base_dir: str | None = None) -> Dict[str, Any]:
        return {"code": jurisdiction or "UK", "lawful_basis": "unknown", "dpia_required": False, "mou_required": False}

def _manifest_legal(mf: Dict[str, Any]) -> Dict[str, Any]:
    return (mf.get("legal") or {}) if isinstance(mf, dict) else {}

def _adapters(mf: Dict[str, Any]) -> Dict[str, Any]:
    return (_manifest_legal(mf).get("jurisdiction_adapters") or {}) if isinstance(mf, dict) else {}

def select_adapter(jurisdiction: str, manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a merged adapter:
      - manifest adapter (if present) + legal profile fields (basis/DPIA/MoU),
        with YAML/profile taking precedence for policy fields.
    """
    j = (jurisdiction or "").upper()
    pool = _adapters(manifest)
    base = dict(pool.get(j, {}))  # manifest-specified adapter for region (may be empty)

    prof = get_profile(j)
    merged = dict(base)  # start with manifest fields
    # profile policy fields take precedence unless manifest explicitly overrides with non-empty values
    for k in ("lawful_basis", "dpia_required", "mou_required", "name", "code", "notes"):
        pv = prof.get(k, None)
        bv = merged.get(k, None)
        if pv is not None and (bv is None or bv == "" or k in ("lawful_basis", "dpia_required", "mou_required")):
            merged[k] = pv
    merged.setdefault("code", j or prof.get("code", "UK"))
    return merged

def is_mou_required(adapter: Dict[str, Any]) -> bool:
    return bool(adapter.get("mou_required", False))

def lawful_basis(adapter: Dict[str, Any]) -> str:
    return str(adapter.get("lawful_basis", "unknown"))

def requires_dpia(adapter: Dict[str, Any]) -> bool:
    return bool(adapter.get("dpia_required", False))
