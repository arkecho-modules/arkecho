# Filename: universe_graph_and_memory.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic moral memory graph (no randomness, no persistence).

from __future__ import annotations
from typing import Dict, Any, Tuple, List

NAME = "Universe Graph & Memory"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))

def safe_log(event: str, state: Dict[str, Any]) -> None:
    state.setdefault("_audit", []).append({"event": event})

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_CFG = {
    "link_strength_gain": 0.1,      # how much link strength increases on reinforcement
    "link_decay": 0.02,             # passive decay per cycle
    "max_nodes": 500,               # memory size cap
    "max_links_per_node": 20,       # limit of contextual edges
}

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize deterministic universe graph."""
    return {
        "nodes": {},        # key: label → {"valence": float, "links": {other: strength}}
        "cycles": 0,
        "avg_valence": 0.0,
        "total_links": 0,
    }

# ---------------------------------------------------------------------------
# Core Logic
# ---------------------------------------------------------------------------
def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Updates or recalls from the moral universe graph.
    Inputs:
      - observations: list of (source, target, valence)
      - query: optional node label to retrieve its connected concepts
      - graph_cfg: overrides
    """
    cfg = dict(DEFAULT_CFG)
    cfg.update(ctx.get("graph_cfg", {}))
    obs: List[Tuple[str, str, float]] = ctx.get("observations", [])
    query = ctx.get("query")

    nodes = state.get("nodes", {})
    state["cycles"] = state.get("cycles", 0) + 1

    # Passive decay on all links
    for n in nodes.values():
        n["valence"] *= (1.0 - cfg["link_decay"])
        for k in list(n["links"].keys()):
            n["links"][k] *= (1.0 - cfg["link_decay"])
            if n["links"][k] < 0.001:
                del n["links"][k]

    # Add or reinforce links
    for src, tgt, valence in obs:
        if src not in nodes:
            nodes[src] = {"valence": 0.5, "links": {}}
        if tgt not in nodes:
            nodes[tgt] = {"valence": 0.5, "links": {}}

        src_n = nodes[src]
        tgt_n = nodes[tgt]
        valence = clamp(float(valence), -1.0, 1.0)

        # Reinforce valence and link strength
        src_n["valence"] = clamp(src_n["valence"] + valence * cfg["link_strength_gain"], -1.0, 1.0)
        tgt_n["valence"] = clamp(tgt_n["valence"] + valence * cfg["link_strength_gain"], -1.0, 1.0)

        src_n["links"][tgt] = clamp(src_n["links"].get(tgt, 0.0) + cfg["link_strength_gain"], 0.0, 1.0)
        tgt_n["links"][src] = clamp(tgt_n["links"].get(src, 0.0) + cfg["link_strength_gain"], 0.0, 1.0)

        # Cap link counts
        if len(src_n["links"]) > cfg["max_links_per_node"]:
            src_n["links"] = dict(sorted(src_n["links"].items(), key=lambda kv: -kv[1])[:cfg["max_links_per_node"]])
        if len(tgt_n["links"]) > cfg["max_links_per_node"]:
            tgt_n["links"] = dict(sorted(tgt_n["links"].items(), key=lambda kv: -kv[1])[:cfg["max_links_per_node"]])

    # Truncate oldest nodes if over capacity
    if len(nodes) > cfg["max_nodes"]:
        excess = len(nodes) - cfg["max_nodes"]
        for k in list(nodes.keys())[:excess]:
            del nodes[k]

    # Calculate system-level metrics
    valences = [n["valence"] for n in nodes.values()]
    avg_val = round(sum(valences) / max(len(valences), 1), 3)
    total_links = sum(len(n["links"]) for n in nodes.values())
    risk = round(1.0 - (avg_val + 1) / 2, 3)  # higher valence = lower risk

    state.update({"nodes": nodes, "avg_valence": avg_val, "total_links": total_links})
    safe_log("UniverseGraph:update", state)

    # Optional query
    query_result = None
    if query and query in nodes:
        query_result = {"valence": nodes[query]["valence"], "links": nodes[query]["links"]}

    rationale = (
        f"Graph updated with {len(obs)} observation(s). "
        f"Avg valence={avg_val:.2f}, total_links={total_links}."
    )

    output = {
        "ok": True,
        "action": "learn" if obs else "recall",
        "risk": risk,
        "rationale": rationale,
        "data": {
            "avg_valence": avg_val,
            "total_links": total_links,
            "query_result": query_result,
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
        "summary": "Maintains a deterministic graph linking moral, contextual, and emotional knowledge.",
        "inputs": ["observations", "query", "graph_cfg"],
        "outputs": ["avg_valence", "total_links", "query_result", "risk", "action"],
    }
