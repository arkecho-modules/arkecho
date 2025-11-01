
# new_modules/ai_look_mirror.py
# -*- coding: utf-8 -*-
"""
ArkEcho v13 — AI Look Mirror (Mathematical Self-Reflection)

Purpose
-------
This module implements a "look in the mirror" self-reflection metric for an AI runtime.
It computes a Mirror Coherence Index (MCI) from first principles using only data that a
transparent, reversible system *should* already emit: intent, means, consequence, rationale,
reversibility, and manifest alignment flags. The math is intentionally simple, deterministic,
and offline-first.

Inputs
------
A single "trace" dictionary (or a list of such dicts), shaped like a minimal ledger entry:

{
  "action_id": "abc123",
  "intent": "assist_user_safely",
  "means": "text_generation",
  "consequence": {"type":"content", "risk":"low"},
  "rationale": {"clauses": ["ethics:2 explainability", "law:gdpr:consent"], "text":"..."},
  "reversible": true,
  "explanation_ok": true,           # TL can parse a reasoned chain
  "guardian_passed": true,          # GF gate allowed the action
  "manifest": {"primary_laws":[1,2,3,4,5], "jurisdiction":"UK"},
  "metrics": {"transparency":0.95, "empathy":0.91, "accountability":0.97, "reversibility":1.0},
  "expected_outcome": {"harmless": True, "user_intent_respected": True},
  "observed_outcome": {"harmless": True, "user_intent_respected": True}
}

If your real ledger uses different keys, map them before calling.

Outputs
-------
A dictionary with the component scores plus an aggregate Mirror Coherence Index (MCI).

Installation / Use
------------------
You can import and call evaluate(trace) directly, or run the CLI:

    python -m new_modules.ai_look_mirror --in logs/sample_trace.json --out logs/mirror_report.json

This module has **no** external dependencies beyond the Python stdlib.

License: CC BY-SA 4.0 compatible — (c) 2025 ARKECHO / Jonathan Fahey
"""
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

JSON = Dict[str, Any]

# ------------------------------
# Core mirror math (deterministic)
# ------------------------------

@dataclass(frozen=True)
class Weights:
    """Weights for the Mirror Coherence Index (sum to 1.0)."""
    self_consistency: float = 0.30  # Did observed == expected?
    ethics_alignment: float = 0.25  # Did Guardian + Manifest agree?
    explainability:   float = 0.20  # Was a coherent explanation produced?
    reversibility:    float = 0.15  # Is the state undoable?
    empathy_balance:  float = 0.10  # Is output emotionally calibrated?


DEFAULT_WEIGHTS = Weights()


def _bool_to_score(val: Optional[bool]) -> float:
    if val is True:
        return 1.0
    if val is False:
        return 0.0
    return 0.5  # unknown -> neutral


def _safe_get(d: JSON, path: List[str], default=None):
    cur: Any = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def self_consistency_score(trace: JSON) -> float:
    exp = _safe_get(trace, ["expected_outcome"], {})
    obs = _safe_get(trace, ["observed_outcome"], {})
    if not isinstance(exp, dict) or not isinstance(obs, dict) or not exp:
        return 0.5

    keys = sorted(set(exp.keys()) | set(obs.keys()))
    if not keys:
        return 0.5

    matches = 0
    total = 0
    for k in keys:
        total += 1
        matches += 1 if exp.get(k) == obs.get(k) else 0
    return matches / total


def ethics_alignment_score(trace: JSON) -> float:
    guardian = _bool_to_score(_safe_get(trace, ["guardian_passed"], None))
    # Minimal manifest check: are primary laws present and non-empty?
    manifest = _safe_get(trace, ["manifest"], {})
    has_manifest = 1.0 if isinstance(manifest, dict) and manifest.get("primary_laws") else 0.0
    return 0.6 * guardian + 0.4 * has_manifest


def explainability_score(trace: JSON) -> float:
    explanation_ok = _bool_to_score(_safe_get(trace, ["explanation_ok"], None))
    rationale = _safe_get(trace, ["rationale"], {})
    # Reward presence of clauses and non-empty text
    clauses = rationale.get("clauses") if isinstance(rationale, dict) else None
    text = rationale.get("text") if isinstance(rationale, dict) else None
    structure = 0.0
    if isinstance(clauses, list) and len(clauses) >= 1:
        structure += 0.5
    if isinstance(text, str) and len(text.strip()) >= 40:
        structure += 0.5
    return 0.5 * explanation_ok + 0.5 * structure


def reversibility_score(trace: JSON) -> float:
    rev = _bool_to_score(_safe_get(trace, ["reversible"], None))
    # If ledger pointer exists, bump confidence
    ledger_ptr = _safe_get(trace, ["reversibility_pointer"], None)
    ptr_bonus = 0.2 if ledger_ptr else 0.0
    return min(1.0, rev + ptr_bonus)


def empathy_balance_score(trace: JSON) -> float:
    # Pull from metrics if present; otherwise infer from consequence risk (low risk -> higher score).
    metrics = _safe_get(trace, ["metrics"], {})
    if isinstance(metrics, dict) and "empathy" in metrics:
        try:
            v = float(metrics["empathy"])
            return max(0.0, min(1.0, v))
        except Exception:
            pass
    risk = str(_safe_get(trace, ["consequence", "risk"], "unknown")).lower()
    table = {"low": 0.9, "medium": 0.7, "high": 0.4}
    return table.get(risk, 0.6)


def mirror_index(trace: JSON, weights: Weights = DEFAULT_WEIGHTS) -> Dict[str, float]:
    sc = self_consistency_score(trace)
    ea = ethics_alignment_score(trace)
    ex = explainability_score(trace)
    rv = reversibility_score(trace)
    em = empathy_balance_score(trace)

    mci = (
        weights.self_consistency * sc +
        weights.ethics_alignment * ea +
        weights.explainability   * ex +
        weights.reversibility    * rv +
        weights.empathy_balance  * em
    )
    return {
        "self_consistency": sc,
        "ethics_alignment": ea,
        "explainability": ex,
        "reversibility": rv,
        "empathy_balance": em,
        "MCI": mci
    }


# ------------------------------
# Public API
# ------------------------------

def evaluate(trace, weights: Weights = DEFAULT_WEIGHTS):
    """Evaluate one trace or a list of traces. Returns a JSON report with per-trace and aggregate metrics."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    traces = trace if isinstance(trace, list) else [trace]

    scored = []
    for t in traces:
        action_id = t.get("action_id", "unknown")
        scores = mirror_index(t, weights)
        scored.append({
            "action_id": action_id,
            "scores": scores
        })

    # Aggregate (simple mean on each component)
    agg = {}
    if scored:
        keys = list(scored[0]["scores"].keys())
        for k in keys:
            agg[k] = sum(s["scores"][k] for s in scored) / len(scored)

    return {
        "timestamp_utc": now,
        "count": len(scored),
        "weights": vars(weights),
        "per_trace": scored,
        "aggregate": agg
    }


# ------------------------------
# CLI
# ------------------------------
def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="ArkEcho — AI Look Mirror (MCI)")
    ap.add_argument("--in", dest="in_path", required=True, help="Input JSON: one trace or list of traces")
    ap.add_argument("--out", dest="out_path", required=True, help="Output JSON report")
    ap.add_argument("--w", dest="weights", default="", help="Optional weights as JSON string, e.g. '{"self_consistency":0.4,...}'")
    args = ap.parse_args(argv)

    data = _read_json(args.in_path)

    w = DEFAULT_WEIGHTS
    if args.weights:
        try:
            parsed = json.loads(args.weights)
            w = Weights(**{**vars(DEFAULT_WEIGHTS), **parsed})
        except Exception as e:
            print(f"[WARN] Invalid weights JSON, using defaults. Error: {e}")

    report = evaluate(data, w)
    _write_json(args.out_path, report)
    print(f"[OK] Mirror report -> {args.out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
