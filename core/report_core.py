# core/report_core.py
# ArkEcho Systems © 2025
# Deterministic integrity reporter for ArkEcho_v11r1 (28 modules).
# Provides summarize(), to_json(), print_summary(), and CLI entrypoint.

from __future__ import annotations
from typing import Dict, Any, List, Optional, Iterable
import importlib, json, sys
from pathlib import Path
import datetime

# --- Path bootstrap: allow running this file directly or via -m ---
ROOT = Path(__file__).resolve().parent.parent
MODS = ROOT / "modules"
for p in (ROOT, MODS):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

# --- Default module set (28) ---
DEFAULT_MODULES: List[str] = [
    # 1–10
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
    # 11–20
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
    # 21–28
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

def _safe_run(mod_name: str) -> Dict[str, Any]:
    try:
        mod = _import_module(mod_name)
        state = mod.init() if hasattr(mod, "init") else {}
        out, state = mod.run({}, state)
        return {
            "module": mod_name,
            "ok": bool(out.get("ok", True)),
            "risk": float(out.get("risk", 0.0)),
            "action": str(out.get("action", "none")),
            "rationale": str(out.get("rationale", ""))[:500],
        }
    except Exception as e:
        return {"module": mod_name, "ok": False, "risk": 1.0, "action": "error", "rationale": f"{e}"}

def _calc_indices(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(results)
    ok_count = sum(1 for r in results if r.get("ok"))
    avg_risk = round(sum(float(r.get("risk", 0.0)) for r in results) / max(n, 1), 3)
    reliability = round(ok_count / max(n, 1), 3)
    stability = round((1.0 - avg_risk) * reliability, 3)
    coherence = round(reliability * (1 - avg_risk * 0.5), 3)
    return {"modules": n, "ok": ok_count, "avg_risk": avg_risk,
            "reliability": reliability, "stability": stability, "coherence": coherence}

def summarize(modules: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    mod_list = list(modules) if modules is not None else list(DEFAULT_MODULES)
    results = [_safe_run(m) for m in mod_list]
    indices = _calc_indices(results)
    # timezone-aware UTC (no deprecation)
    now = datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")
    return {"time": now, **indices, "results": results}

def to_json(summary: Dict[str, Any], pretty: bool = False) -> str:
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2 if pretty else None)

def print_summary(summary: Dict[str, Any]) -> None:
    print("\n" + "=" * 65)
    print(f" ArkEcho_v11r1 Integrity Summary — {summary['time']}")
    print("=" * 65)
    print(f"  Modules OK   : {summary['ok']}/{summary['modules']}")
    print(f"  Avg Risk     : {summary['avg_risk']:.3f}")
    print(f"  Reliability  : {summary['reliability']:.3f}")
    print(f"  Stability    : {summary['stability']:.3f}")
    print(f"  Coherence    : {summary['coherence']:.3f}\n")
    for r in summary["results"]:
        print(f"  - {r['module']:<32} {r['action']:<10} risk={float(r['risk']):.2f} ok={bool(r['ok'])}")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    rep = summarize()
    print_summary(rep)
