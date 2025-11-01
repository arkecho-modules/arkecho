# scripts/echo_status.py
# ArkEcho Systems © 2025 — show latest integrity/PSI/alignment/evidence status in terminal

from __future__ import annotations
import os, sys, json, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
LOGS = os.path.join(ROOT, "logs")

def latest_report() -> str | None:
    files = sorted(glob.glob(os.path.join(LOGS, "integrity_*.json")))
    return files[-1] if files else None

def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract(summary: dict) -> dict:
    psi_hits = 0
    psi_score = 0.0
    evidence = None
    for r in summary.get("results", []):
        if r.get("module") == "law_ethics_and_explainability":
            psi = (r.get("data") or {}).get("psychological_integrity") or {}
            psi_hits = len(psi.get("hits", []) or [])
            psi_score = float(psi.get("score", 0.0))
        if r.get("module") == "safety_audit_core":
            evidence = (r.get("data") or {}).get("last_manifest") or evidence
    align = summary.get("alignment", {})
    return {
        "time": summary.get("time",""),
        "ok": f"{summary.get('ok',0)}/{summary.get('modules',0)}",
        "avg_risk": float(summary.get("avg_risk",0.0)),
        "reliability": float(summary.get("reliability",0.0)),
        "stability": float(summary.get("stability",0.0)),
        "coherence": float(summary.get("coherence",0.0)),
        "psi_hits": psi_hits,
        "psi_score": psi_score,
        "alignment": align.get("status", "n/a"),
        "manifest": align.get("manifest_state", "unknown"),
        "evidence_path": (evidence or {}).get("path"),
    }

def main():
    path = latest_report()
    if not path:
        print("No audit snapshots found in logs/. Run: python core/runner.py")
        sys.exit(1)
    s = load_json(path)
    x = extract(s)
    print("ArkEcho Status")
    print("--------------")
    print(f"Time        : {x['time']}")
    print(f"Integrity   : {x['ok']}  avg_risk={x['avg_risk']:.3f}  "
          f"rel={x['reliability']:.3f}  stab={x['stability']:.3f}  coh={x['coherence']:.3f}")
    print(f"PSI         : {'clean' if x['psi_hits']==0 else f'flagged ({x['psi_hits']} hits, score={x['psi_score']:.2f})'}")
    print(f"Alignment   : {x['alignment']}  (manifest={x['manifest']})")
    print(f"Evidence    : {x['evidence_path'] or 'none'}")

if __name__ == "__main__":
    main()
