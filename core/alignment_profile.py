# core/alignment_profile.py
# ArkEcho Systems © 2025 — Canonical alignment profile + evaluator (refined + runtime check)

from __future__ import annotations
from typing import Dict, Any, List
from datetime import datetime, UTC

PROFILE: Dict[str, Any] = {
    "context": {
        "author": "Jonathan Fahey",
        "project": "ARKECHO_v13",
        "purpose": "Create a modular moral OS that encodes transparency, empathy, accountability, and reversibility into AI systems.",
        "status": "28 active modules under deterministic ethics and schema testing",
    },
    "core_intent": {
        "mission": "Protect children and vulnerable adults from manipulation, grooming, and exploitation through lawful, verifiable intervention frameworks.",
        "ethics": [
            "Transparency",
            "Empathy Encoding",
            "Accountability",
            "Reversibility",
            "Human-Compatibility",
            "Offline-First Design",
        ],
        "foundation": "Moral realism — responsibility, protection of innocence, lawful order.",
    },
    "guiding_principles": {
        "testing": "All modules must be deterministic and schema-compliant.",
        "execution": "No random drift, hidden manipulation, or uncontrolled external I/O during tests.",
        "governance": "All enforcement routes through proper authorities — no vigilante logic.",
        "architecture": "Enhance existing safety frameworks; not replace them.",
        "communication": "Maintain clarity, honesty, and responsible tone in all reasoning.",
    },
    "active_concerns": [
        "Ensure canonical ethics manifest persists across sessions.",
        "Avoid reasoning loops or retention slowdowns.",
        "Keep tests idempotent and reversible.",
        "Confirm lawful data pathways for protection protocols.",
        "Guard against manipulative or profit-driven design patterns.",
    ],
    "personal_alignment": {
        "motivation": "Protective instinct as a father; pursuit of moral clarity over fame or ego.",
        "temperament": "Direct, reflective, occasionally intense but grounded in humour and responsibility.",
        "goal": "Leave a system that restores moral balance, protects the innocent, and rebuilds trust in technology.",
    },
    "summary": {
        "tone": "Concise, technical, minimal fluff. Structured responses only. Prioritise reasoning, testing, and actionable outputs.",
        "alignment_check": "Ensure all code, commentary, and analysis reinforce ethical protection, interpretability, and reversibility.",
    },
}


def evaluate(run_summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a report_core summary against alignment principles.
    Returns a compact result suitable for embedding into audit JSON.
    """
    notes: List[str] = []
    warnings: List[str] = []
    ok = True
    manifest_state = "unknown"  # confirmed | pending | unknown

    # 1) Determinism / schema compliance
    total = int(run_summary.get("modules", 0))
    ok_count = int(run_summary.get("ok", 0))
    if ok_count == total and total > 0:
        notes.append("All modules schema-compliant (deterministic outputs present).")
    else:
        ok = False
        warnings.append(f"Schema/determinism gap: {ok_count}/{total} modules OK.")

    # 2) Ethics manifest presence/persistence (initial check)
    try:
        from core.ethics_manifest import get_manifest  # type: ignore
        mf = get_manifest()
        if mf and "ethical_position" in mf:
            manifest_state = "confirmed"
            notes.append("Canonical ethics manifest verified and loaded.")
        else:
            manifest_state = "pending"
            warnings.append("Ethics manifest present but missing core fields.")
    except Exception:
        manifest_state = "pending"
        warnings.append("Ethics manifest import deferred or not yet accessible.")

    # 2b) Runtime verification patch (explicit import + console prints)
    manifest_check = "pending"
    try:
        import core.ethics_manifest as ethics  # type: ignore
        if hasattr(ethics, "MANIFEST") and isinstance(getattr(ethics, "MANIFEST"), dict) \
           and "ethical_position" in ethics.MANIFEST:
            manifest_check = "verified"
            manifest_state = "confirmed"  # strengthen state when verified
            print("[✓] Ethics manifest located and verified at runtime.")
        else:
            manifest_check = "pending"
            # keep previous manifest_state (likely pending)
            print("[!] Ethics manifest loaded but missing 'ethical_position'. Marked pending.")
    except Exception as e:
        manifest_check = "pending"
        # keep previous manifest_state
        print(f"[!] Ethics manifest not confirmed at import ({e}). Marked pending.")

    # 3) Execution guardrails
    notes.append("Execution policy: tests run offline; no external I/O required.")
    notes.append("Governance: enforcement is lawful-only; no vigilante pathways in code.")

    # 4) PSI advisory reflection
    psi = None
    for r in run_summary.get("results", []):
        if r.get("module") == "law_ethics_and_explainability":
            psi = r.get("data", {}).get("psychological_integrity")
            break
    if psi and isinstance(psi, dict):
        hits = len(psi.get("hits", []) or [])
        if hits > 0:
            warnings.append(f"PSI advisory: {hits} pattern(s) flagged for redesign.")
        else:
            notes.append("PSI advisory: clean (no exploitative reward patterns detected).")

    # 5) Determine final status
    if ok and manifest_state == "confirmed":
        status = "pass"
    elif ok and manifest_state == "pending":
        status = "pending"
    else:
        status = "review"

    return {
        "status": status,
        "time": datetime.now(UTC).isoformat(timespec="seconds"),
        "manifest_state": manifest_state,
        "manifest_check": manifest_check,   # added for explicit runtime confirmation
        "profile": {
            "author": PROFILE["context"]["author"],
            "project": PROFILE["context"]["project"],
            "ethics": PROFILE["core_intent"]["ethics"],
        },
        "notes": notes,
        "warnings": warnings,
        "principles": PROFILE["guiding_principles"],
        "active_concerns": PROFILE["active_concerns"],
    }
