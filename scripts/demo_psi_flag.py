# scripts/demo_psi_flag.py
# ArkEcho Systems © 2025 — Demonstrate PSI flag path and evidence packaging.

from __future__ import annotations
import os, sys, json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from modules import law_ethics_and_explainability as ethics  # type: ignore
from modules import safety_audit_core as audit               # type: ignore

def main():
    # Craft a ctx with exploitative design notes to trigger PSI non-punitive flag
    ctx = {
        "legal": [],
        "ethical": [],
        "audience": "adult",
        "base_risk": 0.0,
        "design_notes": {
            "monetization": "loot box with variable reward + limited time offer",
            "engagement": "streak loss pressure",
        },
        "telemetry": {"session_len": 120, "purchases": 3},
    }

    est = {}
    out, est = ethics.run(ctx, est)

    print("ETHICS DECISION:")
    print(json.dumps(out, indent=2))
    psi = out["data"].get("psychological_integrity", {})
    psi_hits = len(psi.get("hits", []))
    psi_score = psi.get("score", 0.0)

    # Send PSI to safety audit to package evidence
    a_ctx = {
        "psi": {"hits": psi_hits, "score": psi_score, "details": psi},
        "note": "Demo packaging: PSI flagged patterns for redesign.",
    }
    ast = {}
    a_out, ast = audit.run(a_ctx, ast)
    print("\nSAFETY AUDIT:")
    print(json.dumps(a_out, indent=2))

if __name__ == "__main__":
    main()
