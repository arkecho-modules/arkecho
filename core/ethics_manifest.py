# core/ethics_manifest.py
# ArkEcho Systems © 2025 — Canonical ethics manifest for ArkEcho_v11r1

from __future__ import annotations
from typing import Dict, Any, List

MANIFEST: Dict[str, Any] = {
    "project": {
        "name": "ARKECHO_v11",
        "purpose": "Modular moral OS: transparency, empathy, accountability, reversibility.",
        "core_mission": "Protect children and vulnerable adults from manipulation, grooming, exploitation.",
    },
    "ethical_position": {
        "foundation": "Moral realism, responsibility, protection of innocence, lawful order.",
        "non_violence": "All enforcement lawful via proper authorities. No vigilantism or coercion.",
        "moral_intent": "Make doing the right thing efficient, verifiable, and scalable.",
        "psychological_integrity": {
            "purpose": "Protect children and users from psychological manipulation, coercion, or exploitative reward systems.",
            "examples": [
                "loot box gambling mechanics",
                "artificial scarcity loops",
                "coercive competition"
            ],
            "principle": "Systems must not use emotional or behavioural vulnerabilities for profit or engagement metrics.",
            "detection_pipeline": [
                "pattern_recognition",
                "reward_structure_audit",
                "user_empathy_feedback"
            ],
            "response": "Flag to developer or regulator for redesign; no punitive or user-facing intervention."
        },
    },
    "principles": [
        "Transparency",
        "Empathy Encoding",
        "Reversibility",
        "Accountability",
        "Human-Compatibility",
        "Offline-First"
    ],
    "child_protection": {
        "targets": {
            "time_to_quarantine_sec": 60,
            "time_to_triage_min": 15,
            "time_to_referral_min": 60
        },
        "pipeline": [
            "detection",
            "quarantine",
            "evidence_bundle",
            "human_triage",
            "referral",
            "audit"
        ]
    },
    "legal": {
        "default_jurisdiction": "UK",
        "jurisdiction_adapters": {
            "UK": {"dpia_required": True, "lawful_basis": "public_task", "mou_required": True},
            "EU": {"dpia_required": True, "lawful_basis": "legitimate_interest", "mou_required": True},
            "US": {"dpia_required": False, "lawful_basis": "consent_or_legal_obligation", "mou_required": True}
        }
    }
}

def get_manifest() -> Dict[str, Any]:
    return MANIFEST

def get_principles() -> List[str]:
    vals = MANIFEST.get("principles", [])
    return list(vals) if isinstance(vals, list) else []

def get_targets() -> Dict[str, int]:
    cp = MANIFEST.get("child_protection", {}) or {}
    tg = cp.get("targets", {}) or {}
    # ensure int-cast where possible
    out: Dict[str, int] = {}
    for k, v in tg.items():
        try:
            out[k] = int(v)
        except Exception:
            pass
    return out

def get_psychological_integrity() -> Dict[str, Any]:
    ep = MANIFEST.get("ethical_position", {}) or {}
    psi = ep.get("psychological_integrity", {}) or {}
    return dict(psi)
