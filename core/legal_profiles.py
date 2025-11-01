# core/legal_profiles.py
# ArkEcho Systems © 2025 — Region legal profiles with built-in defaults, file overrides optional.

from __future__ import annotations
from typing import Dict, Any
import os

# ---- Built-in defaults (works even if no YAML is present) ----
_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "UK": {
        "code": "UK",
        "name": "United Kingdom",
        "lawful_basis": "public_task",       # common basis for child protection / safeguarding
        "dpia_required": True,
        "mou_required": True,
        "notes": "Safeguarding/public task; DPIA strongly recommended for automated detection."
    },
    "EU": {
        "code": "EU",
        "name": "European Union",
        "lawful_basis": "legitimate_interest",
        "dpia_required": True,
        "mou_required": True,
        "notes": "Legitimate interest balanced with safeguarding; DPIA required under GDPR for monitoring."
    },
    "US": {
        "code": "US",
        "name": "United States",
        "lawful_basis": "consent_or_legal_obligation",
        "dpia_required": False,
        "mou_required": True,
        "notes": "MoU/API with LE; cite relevant state/federal provisions; DPIA concept not standardized."
    }
}

def _yaml_available() -> bool:
    try:
        import yaml  # type: ignore
        return True
    except Exception:
        return False

def _load_yaml_profile(path: str) -> Dict[str, Any]:
    import yaml  # type: ignore
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        return {}
    return data

def get_profile(jurisdiction: str, base_dir: str | None = None) -> Dict[str, Any]:
    """
    Load a jurisdiction profile. Tries YAML file overrides in core/legal_profiles/*.yml,
    falls back to built-in defaults when files or PyYAML are unavailable.
    """
    code = (jurisdiction or "").upper().strip()
    if not code:
        return dict(_DEFAULTS["UK"])

    # Optional YAML override
    if _yaml_available():
        base = base_dir or os.path.dirname(__file__)
        yml_dir = os.path.join(base, "legal_profiles")
        yml_path = os.path.join(yml_dir, f"{code.lower()}.yml")
        if os.path.isfile(yml_path):
            try:
                data = _load_yaml_profile(yml_path)
                # ensure minimal keys
                data.setdefault("code", code)
                data.setdefault("lawful_basis", _DEFAULTS.get(code, {}).get("lawful_basis", "unknown"))
                data.setdefault("dpia_required", _DEFAULTS.get(code, {}).get("dpia_required", False))
                data.setdefault("mou_required", _DEFAULTS.get(code, {}).get("mou_required", False))
                return data
            except Exception:
                pass

    # Built-in defaults
    return dict(_DEFAULTS.get(code, _DEFAULTS["UK"]))
