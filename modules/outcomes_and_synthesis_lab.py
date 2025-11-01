# ArkEcho Systems © 2025
# v11r1 deterministic refactor — Outcomes & Synthesis Lab
# Advisory engine: recommends next step from fused signals.
# Policy: "delay" is a SAFE, REVERSIBLE advisory => ok=True (not a failure).

from __future__ import annotations
from typing import Dict, Any, Tuple

NAME = "Outcomes & Synthesis Lab"
VERSION = "1.1.0"

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def init() -> Dict[str, Any]:
    return {
        "cycles": 0,
        "last_action": "maintain",
        "uncertainty": 0.0,
    }

def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Inputs (optional):
      - risk_inputs: list[float]         # 0..1 risk signals
      - trust_level: float               # 0..1 (default 0.7)
      - evidence_strength: float         # 0..1 (default 0.6)
      - urgency: float                   # 0..1 (default 0.4)
    """
    state["cycles"] = state.get("cycles", 0) + 1

    risks = [clamp(float(r), 0.0, 1.0) for r in ctx.get("risk_inputs", [])]
    trust = clamp(float(ctx.get("trust_level", 0.7)), 0.0, 1.0)
    evidence = clamp(float(ctx.get("evidence_strength", 0.6)), 0.0, 1.0)
    urgency = clamp(float(ctx.get("urgency", 0.4)), 0.0, 1.0)

    if risks:
        avg_risk = sum(risks) / len(risks)
        spread = max(risks) - min(risks) if len(risks) > 1 else 0.0
    else:
        avg_risk, spread = 0.2, 0.0

    uncertainty = clamp(0.5 * spread + 0.3 * (1 - evidence) + 0.2 * (1 - trust), 0.0, 1.0)

    if avg_risk >= 0.7 and evidence >= 0.5:
        action = "escalate"
        out_risk = clamp(0.8 * avg_risk, 0.0, 1.0)
        rationale = "High risk with sufficient evidence; escalate with safeguards."
    elif uncertainty > 0.45 and urgency < 0.6:
        action = "delay"   # advisory pause for more context
        out_risk = clamp(0.2 + 0.6 * uncertainty, 0.0, 1.0)
        rationale = "Uncertainty high and urgency moderate; delay for more context."
    elif avg_risk <= 0.2 and evidence >= 0.6:
        action = "proceed"
        out_risk = clamp(0.15 * (1 - evidence), 0.0, 1.0)
        rationale = "Low risk with strong evidence; proceed."
    else:
        action = "maintain"
        out_risk = clamp(0.3 * (uncertainty + avg_risk) / 2, 0.0, 1.0)
        rationale = "Maintain state; signals not decisive."

    state["last_action"] = action
    state["uncertainty"] = round(uncertainty, 3)

    output = {
        "ok": True,                         # advisory engine never marks failure
        "action": action,                   # escalate | delay | proceed | maintain
        "risk": round(out_risk, 3),
        "rationale": rationale,
        "data": {
            "avg_risk": round(avg_risk, 3),
            "uncertainty": state["uncertainty"],
            "trust": trust,
            "evidence": evidence,
            "urgency": urgency,
        },
    }
    return output, state
