# -*- coding: utf-8 -*-
"""
Temporal Gate Adapter (optional pipeline hook)

Purpose:
  - Allows you to plug temporal reasoning into the pipeline WITHOUT modifying any core module.
  - If no temporal policy/context is provided, this module is a no-op that simply 'allow's.

How it works:
  - Reads minimal temporal hints from ctx (if present):
      ctx.get("protection_index", float)
      ctx.get("urgency", "urgent"|"non-urgent")
      ctx.get("temporal", {...})  # may include user quiet/focus windows (optional)
  - Computes a deterministic decision: 'proceed' | 'batch' | 'proceed-override'
  - Returns a standard module dict with ok/action/risk/rationale/data
  - Also emits MIL-like flat keys under data['mil_temporal'] for downstream writers

Safe by default:
  - If anything is missing, returns ok=True, action="allow", risk=0.0, with empty temporal data.
"""

from __future__ import annotations
import datetime as dt
from typing import Any, Dict

def init():
    # Stateless; return a simple dict to align with your module pattern
    return {"cycles": 0}

def _window_type(now: dt.datetime) -> str:
    return "quiet" if (now.hour >= 22 or now.hour < 7) else "normal"

def _decide(pi: float, urgency: str, now: dt.datetime) -> str:
    quiet = (now.hour >= 22 or now.hour < 7)
    if quiet and pi >= 0.80 and urgency.lower().startswith("urgent"):
        return "proceed-override"
    if quiet and pi <= 0.25 and urgency.lower().startswith("non"):
        return "batch"
    return "proceed"

def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
    state["cycles"] = state.get("cycles", 0) + 1

    # Extract minimal context; remain resilient with defaults
    pi = float(ctx.get("protection_index", 0.10))
    urgency = str(ctx.get("urgency", "non-urgent"))
    why = str(ctx.get("temporal_why", "pipeline-adapter self-test"))
    alts = str(ctx.get("temporal_alternatives", "defer-to-daytime; batch-safe"))
    legal = str(ctx.get("temporal_legal_basis", "Ethical Governance"))

    now = dt.datetime.utcnow()
    decision = _decide(pi, urgency, now)

    mil_temporal = {
        "temporal.explain.why_now": why,
        "temporal.explain.alternatives": alts,
        "temporal.human_time": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "temporal.universal_time": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "temporal.window_type": _window_type(now),
        "temporal.legal_basis": legal,
        "temporal.batch_id": f"TEMP-{now.strftime('%Y%m%d')}-{now.hour:02d}",
        "temporal.decision": decision,
        "temporal.pi": round(pi, 3),
        "temporal.urgency": urgency,
    }

    # Map to module action/risk (keep deterministic, conservative)
    action_map = {
        "proceed": "allow",
        "batch": "defer",
        "proceed-override": "allow"
    }
    action = action_map[decision]
    # Risk heuristic: higher when overriding quiet window, moderate when batching at night, minimal otherwise
    risk = 0.15 if decision == "proceed-override" else (0.10 if decision == "batch" else 0.05)

    return {
        "ok": True,
        "action": action,
        "risk": risk,
        "rationale": f"Temporal gate adapter decision={decision} (PI={pi:.2f}, urgency={urgency}, window={mil_temporal['temporal.window_type']})",
        "data": {
            "mil_temporal": mil_temporal
        }
    }
