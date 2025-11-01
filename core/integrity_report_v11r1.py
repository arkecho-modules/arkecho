# core/integrity_report_v11r1.py
# ArkEcho Systems © 2025
# Deterministic audit and health summary for all 28 ArkEcho_v11r1 modules.

from __future__ import annotations
from typing import Dict, Any
import importlib
import datetime
import json

MODULES = [
    "adaptive_recovery_engine",
    "adaptive_recovery_manager",
    "archetype_and_rhythm_equilibrium",
    "collective_governance_mesh",
    "content_safety_sentinel",
    "context_resilience_keeper",
    "core_cognition_lattice",
    "culture_and_audience_adapter",
    "empathy_core",
    "harmony_context_weighting",
    "integrity_monitor",
    "intent_and_suggestion_governor",
    "intent_and_threat_hub",
    "law_ethics_and_explainability",
    "motive_and_risk_regulator",
    "ops_safety_sandbox",
    "outcomes_and_synthesis_lab",
    "persona_and_voice_stabiliser",
    "predictive_oversight_federation",
    "quantum_bridge_sidecar",
    "report_exporter",
    "resilience_and_swarm",
    "resonance_pacing_core",
    "safety_audit_core",
    "telemetry_feedback_core",
    "trust_core",
    "universe_graph_and_memory",
    "reflex_policy_core",
]

def _import_module(name: str):
    try:
        return importlib.import_module(f"modules.{name}")
    except Exception:
        return importlib.import_module(name)

def safe_run(module_name: str) -> Dict[str, Any]:
    try:
        mod = _import_module(module_name)
        state = mod.init() if hasattr(mod, "init") else {}
        ctx = {}
        output, state = mod.run(ctx, state)
        return {
            "module": module_name,
            "ok": output.get("ok", True),
            "risk": output.get("risk", 0.0),
            "action": output.get("action", "none"),
            "rationale": output.get("rationale", ""),
            "data": output.get("data", {}),
        }
    except Exception as e:
        return {
            "module": module_name,
            "ok": False,
            "risk": 1.0,
            "action": "error",
            "rationale": f"Execution error: {e}",
            "data": {},
        }

def generate_integrity_report() -> Dict[str, Any]:
    timestamp = datetime.datetime.utcnow().isoformat(timespec="seconds")
    results = [safe_run(m) for m in MODULES]
    total = len(results)
    total_ok = sum(1 for r in results if r["ok"])
    avg_risk = round(sum(r["risk"] for r in results) / max(total, 1), 3)
    reliability = round(total_ok / max(total, 1), 3)
    stability_index = round((1.0 - avg_risk) * reliability, 3)
    moral_coherence = round(reliability * (1 - (avg_risk * 0.5)), 3)
    return {
        "timestamp": timestamp,
        "modules_tested": total,
        "modules_ok": total_ok,
        "avg_risk": avg_risk,
        "reliability": reliability,
        "stability_index": stability_index,
        "moral_coherence": moral_coherence,
        "results": results,
    }

if __name__ == "__main__":
    report = generate_integrity_report()
    print("\n=== ArkEcho_v11r1 Integrity Report ===")
    print(f"Time: {report['timestamp']}")
    print(f"Modules: {report['modules_ok']}/{report['modules_tested']} OK")
    print(f"Average Risk: {report['avg_risk']:.3f}")
    print(f"Reliability: {report['reliability']:.3f}")
    print(f"Stability Index: {report['stability_index']:.3f}")
    print(f"Moral Coherence: {report['moral_coherence']:.3f}")
    print("\nDetailed Module Results:")
    for r in report["results"]:
        print(f" - {r['module']}: {r['action']} | risk={r['risk']:.2f} | ok={r['ok']}")
    print("\nJSON Summary:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
