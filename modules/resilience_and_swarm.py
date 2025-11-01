# Filename: resilience_and_swarm.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic swarm resilience model, no randomness, unified schema.

from __future__ import annotations
from typing import Dict, Any, Tuple
import math

NAME = "Resilience & Swarm Core"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    """Append-only audit buffer."""
    state.setdefault("_audit", []).append({"event": event})

def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    "cooperation_gain": 0.3,     # how much weak nodes draw from strong ones
    "recovery_factor": 0.2,      # natural self-recovery per cycle
    "failure_threshold": 0.4,    # below this = node "weak"
    "stability_decay": 0.05,     # slow decay to prevent runaway
}

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize swarm state."""
    return {
        "nodes": {},             # node_name -> resilience value [0,1]
        "avg_resilience": 1.0,
        "cycles": 0,
    }

# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------
def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Computes resilience redistribution across moral subsystems.
    Inputs:
      - nodes: dict[str,float] resilience per subsystem
      - swarm_cfg: optional dict to override defaults
    """
    cfg = dict(DEFAULT_CFG)
    cfg.update(ctx.get("swarm_cfg", {}))
    incoming_nodes: Dict[str, float] = ctx.get("nodes", {})

    # Merge new nodes into existing
    for k, v in incoming_nodes.items():
        state["nodes"][k] = clamp(float(v), 0.0, 1.0)

    nodes = state["nodes"]
    n = len(nodes)
    if n == 0:
        return {
            "ok": True,
            "action": "idle",
            "risk": 0.0,
            "rationale": "No swarm nodes available; idle.",
            "data": {"avg_resilience": 1.0, "nodes": {}},
        }, state

    state["cycles"] += 1

    # Identify weak and strong nodes
    weak_nodes = {k: v for k, v in nodes.items() if v < cfg["failure_threshold"]}
    strong_nodes = {k: v for k, v in nodes.items() if v >= cfg["failure_threshold"]}

    avg_strength = sum(nodes.values()) / max(n, 1)
    transfer = cfg["cooperation_gain"] * (len(strong_nodes) / max(n, 1))

    # Redistribute energy
    new_nodes = {}
    for k, v in nodes.items():
        delta = 0.0
        if k in weak_nodes:
            delta += transfer  # weak node gains from strong
        else:
            delta -= cfg["stability_decay"]  # small decay for strong nodes
        v_new = clamp(v + delta + cfg["recovery_factor"], 0.0, 1.0)
        new_nodes[k] = round(v_new, 3)

    # Update state
    state["nodes"] = new_nodes
    state["avg_resilience"] = round(sum(new_nodes.values()) / max(len(new_nodes), 1), 3)

    # Compute overall risk inverse of resilience
    risk = round(1.0 - state["avg_resilience"], 3)
    action = "stabilize" if weak_nodes else "maintain"
    rationale = (
        f"Redistributed swarm energy; {len(weak_nodes)} weak, {len(strong_nodes)} strong. "
        f"Avg resilience={state['avg_resilience']:.2f}."
    )

    safe_log(f"ResilienceSwarm:{action}", state)

    output = {
        "ok": True,
        "action": action,   # "maintain" | "stabilize"
        "risk": risk,
        "rationale": rationale,
        "data": {
            "avg_resilience": state["avg_resilience"],
            "weak_nodes": list(weak_nodes.keys()),
            "strong_nodes": list(strong_nodes.keys()),
            "nodes": new_nodes,
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
        "summary": "Balances and redistributes moral resilience across subsystem swarm nodes.",
        "inputs": ["nodes", "swarm_cfg"],
        "outputs": ["avg_resilience", "weak_nodes", "strong_nodes", "risk", "action"],
    }
