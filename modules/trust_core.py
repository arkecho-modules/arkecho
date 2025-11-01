# ArkEcho Systems © 2025
# v11r1: deterministic trust evaluation with safe defaults

from __future__ import annotations
from typing import Dict, Any, Tuple

NAME = "Trust Core"
VERSION = "1.1.1"

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

DEFAULT_CFG = {
    "gain_rate": 0.15,
    "decay_rate": 0.05,
    "penalty_rate": 0.25,
    "risk_threshold": 0.6,
    "max_history": 250,
    "baseline_trust": 0.9,   # NEW: safe default if no history/updates
}

def init() -> Dict[str, Any]:
    return {"ledger": {}, "cycles": 0, "avg_trust": DEFAULT_CFG["baseline_trust"]}

def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    cfg = dict(DEFAULT_CFG)
    if isinstance(ctx.get("trust_cfg"), dict):
        cfg.update(ctx["trust_cfg"])

    updates = ctx.get("updates", [])
    state["cycles"] = state.get("cycles", 0) + 1
    ledger = state.get("ledger", {})
    changed = {}

    for entry in updates:
        name = str(entry.get("module", "unknown"))
        ok = bool(entry.get("ok", True))
        risk = clamp(float(entry.get("risk", 0.0)), 0.0, 1.0)
        trust = ledger.get(name, cfg["baseline_trust"])

        # decay every cycle
        trust *= (1.0 - cfg["decay_rate"])

        # positive reinforcement
        if ok and risk < cfg["risk_threshold"]:
            trust += cfg["gain_rate"] * (1.0 - trust)

        # penalties for failures/high risk
        if (not ok) or (risk >= cfg["risk_threshold"]):
            trust -= cfg["penalty_rate"] * risk

        trust = round(clamp(trust, 0.0, 1.0), 3)
        ledger[name] = trust
        changed[name] = trust

    # Safe default when ledger is empty
    if ledger:
        avg_trust = round(sum(ledger.values()) / len(ledger), 3)
    else:
        avg_trust = round(cfg["baseline_trust"], 3)

    state.update({"ledger": ledger, "avg_trust": avg_trust})

    risk_out = round(clamp(1.0 - avg_trust, 0.0, 1.0), 3)
    action = "stabilize" if risk_out > 0.3 else "maintain"
    rationale = f"Avg trust={avg_trust:.2f}, risk={risk_out:.2f}. Updated {len(changed)} entries."

    output = {
        "ok": True,
        "action": action,
        "risk": risk_out,
        "rationale": rationale,
        "data": {"ledger": changed, "avg_trust": avg_trust, "entries": len(changed)},
    }
    return output, state

def describe() -> Dict[str, Any]:
    return {
        "name": NAME, "version": VERSION,
        "summary": "Deterministic trust ledger with safe baseline defaults.",
        "inputs": ["updates", "trust_cfg"],
        "outputs": ["ledger", "avg_trust", "risk", "action"],
    }
