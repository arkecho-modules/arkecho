# Filename: telemetry_feedback_core.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic telemetry capture, moral feedback weighting,
# and audit-safe performance reflection (no hardware I/O required).

from __future__ import annotations
from typing import Dict, Any, Tuple
import time
import math

NAME = "Telemetry & Feedback Core"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event, "t": round(time.time(), 3)})

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    "decay": 0.05,              # how fast telemetry stabilizes
    "feedback_gain": 0.3,       # how much user moral feedback adjusts metrics
    "max_cycles": 10000,        # rolling window
    "risk_weight": 0.4,         # risk weight on feedback signals
}

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize telemetry state."""
    return {
        "cpu_load": 0.0,
        "mem_load": 0.0,
        "moral_feedback": 0.5,
        "health": 1.0,
        "cycles": 0,
    }

# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Collects system diagnostics and moral feedback into a single deterministic health score.
    Inputs:
      - cpu_load: float [0,1]
      - mem_load: float [0,1]
      - feedback_signal: float [0,1] (user moral feedback)
      - telemetry_cfg: dict (optional overrides)
    """
    cfg = dict(DEFAULT_CFG)
    cfg.update(ctx.get("telemetry_cfg", {}))

    cpu = clamp(float(ctx.get("cpu_load", state.get("cpu_load", 0.2))), 0.0, 1.0)
    mem = clamp(float(ctx.get("mem_load", state.get("mem_load", 0.3))), 0.0, 1.0)
    feedback = clamp(float(ctx.get("feedback_signal", state.get("moral_feedback", 0.5))), 0.0, 1.0)
    state["cycles"] = (state.get("cycles", 0) + 1) % cfg["max_cycles"]

    # Smooth decay toward steady state
    state["cpu_load"] = round(cpu * (1 - cfg["decay"]), 3)
    state["mem_load"] = round(mem * (1 - cfg["decay"]), 3)
    state["moral_feedback"] = round(
        state.get("moral_feedback", 0.5) * (1 - cfg["decay"]) + feedback * cfg["feedback_gain"], 3
    )

    # Health metric combines inverse load and moral feedback
    load_penalty = (state["cpu_load"] + state["mem_load"]) / 2
    moral_gain = (state["moral_feedback"] - 0.5) * 2  # -1 to +1 scale
    health = clamp(1.0 - load_penalty * 0.5 + moral_gain * 0.25, 0.0, 1.0)
    state["health"] = round(health, 3)

    # Derived risk inversely proportional to health
    risk = round(cfg["risk_weight"] * (1.0 - health), 3)

    rationale = (
        f"CPU={state['cpu_load']:.2f}, MEM={state['mem_load']:.2f}, "
        f"Moral feedback={state['moral_feedback']:.2f}, Health={health:.2f}."
    )

    safe_log("Telemetry:cycle", state)

    output = {
        "ok": True,
        "action": "monitor",
        "risk": risk,
        "rationale": rationale,
        "data": {
            "cpu_load": state["cpu_load"],
            "mem_load": state["mem_load"],
            "moral_feedback": state["moral_feedback"],
            "health": health,
            "cycles": state["cycles"],
        },
    }
    return output, state

# ---------------------------------------------------------------------------
# Describe
# ---------------------------------------------------------------------------
def describe() -> Dict[str, Any]:
    return {
        "name": NAME,
        "version": VERSION,
        "summary": "Monitors system load and user moral feedback to maintain transparent performance health.",
        "inputs": ["cpu_load", "mem_load", "feedback_signal", "telemetry_cfg"],
        "outputs": ["health", "moral_feedback", "cpu_load", "mem_load", "risk"],
    }
