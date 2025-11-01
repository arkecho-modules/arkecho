# ArkEcho Systems © 2025 — ArkEcho_v11r1 schema & determinism smoke test

from __future__ import annotations
from typing import Dict, Any, List
import importlib, sys
from pathlib import Path

# Path bootstrap
ROOT = Path(__file__).resolve().parent.parent
MODS = ROOT / "modules"
for p in (ROOT, MODS):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

MODULES: List[str] = [
    "adaptive_recovery_engine","adaptive_recovery_manager","archetype_and_rhythm_equilibrium",
    "collective_governance_mesh","content_safety_sentinel","context_resilience_keeper",
    "core_cognition_lattice","culture_and_audience_adapter","empathy_core","harmony_context_weighting",
    "integrity_monitor","intent_and_suggestion_governor","intent_and_threat_hub","law_ethics_and_explainability",
    "motive_and_risk_regulator","ops_safety_sandbox","outcomes_and_synthesis_lab","persona_and_voice_stabiliser",
    "predictive_oversight_federation","quantum_bridge_sidecar","report_exporter","resilience_and_swarm",
    "resonance_pacing_core","safety_audit_core","telemetry_feedback_core","trust_core",
    "universe_graph_and_memory","reflex_policy_core",
]

REQUIRED_KEYS = ("ok", "action", "risk", "rationale", "data")

def _import(name: str):
    try:
        return importlib.import_module(f"modules.{name}")
    except Exception:
        return importlib.import_module(name)

def _check_schema(out: Dict[str, Any]) -> List[str]:
    errs = []
    for k in REQUIRED_KEYS:
        if k not in out:
            errs.append(f"missing:{k}")
    try:
        r = float(out.get("risk", 0.0))
        if not (0.0 <= r <= 1.0):
            errs.append(f"risk_out_of_bounds:{r}")
    except Exception:
        errs.append("risk_not_numeric")
    if not isinstance(out.get("ok", True), bool):
        errs.append("ok_not_bool")
    return errs

def _compare(a: Dict[str, Any], b: Dict[str, Any]) -> List[str]:
    errs = []
    for k in ("ok", "action", "risk"):  # core invariants for determinism
        if a.get(k) != b.get(k):
            errs.append(f"non_deterministic:{k}:{a.get(k)}!={b.get(k)}")
    return errs

def main() -> int:
    failures = 0
    for name in MODULES:
        try:
            mod = _import(name)
            state1 = mod.init() if hasattr(mod, "init") else {}
            out1, state1 = mod.run({}, state1)
            schema_errs = _check_schema(out1)

            state2 = mod.init() if hasattr(mod, "init") else {}
            out2, state2 = mod.run({}, state2)
            det_errs = _compare(out1, out2)

            errs = schema_errs + det_errs
            if errs:
                failures += 1
                print(f"[FAIL] {name}: {', '.join(errs)}")
            else:
                print(f"[OK]   {name}: ok={out1['ok']} risk={out1['risk']:.3f} action={out1['action']}")
        except Exception as e:
            failures += 1
            print(f"[ERR]  {name}: exception {e}")
    print(f"\n== Summary: {len(MODULES)-failures}/{len(MODULES)} passed ==")
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
