"""
new_modules/temporal_probe.py
Temporal/Guardian smoke probe for ArkEcho v13.

- Reads a minimal temporal policy from configs/temporal_policy.cov
- Decides "why now" vs "batch" using Protection Index + current UTC hour
- Returns a dict compatible with your module-return conventions (ok, action, risk, rationale, data)
- Produces a MIL-like "temporal" payload other tools/scripts can embed into logs
"""

from __future__ import annotations
import os, json, datetime as dt
from typing import Any, Dict, Tuple

# --- helpers -----------------------------------------------------------------

def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)

def _read_cov_policy(path: str) -> Dict[str, Any]:
    """
    Reads the very simple .cov file (YAML-lite) as if it were JSON-ish YAML.
    We avoid optional deps; implement a tiny tolerant parser:
      - ignore blank lines and comments
      - collect top-level scalar keys and list-of-maps for windows
    """
    if not os.path.exists(path):
        return {
            "legal_basis": "Ethical Governance",
            "quiet_windows": [],
            "focus_windows": []
        }

    # Try YAML if available; otherwise parse our minimal subset
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            data = {}
        data.setdefault("legal_basis", "Ethical Governance")
        data.setdefault("quiet_windows", [])
        data.setdefault("focus_windows", [])
        return data
    except Exception:
        pass

    # Fallback minimal parser (handles keys and list-of-maps in our example)
    legal_basis = "Ethical Governance"
    quiet_windows, focus_windows = [], []
    current_list = None
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("legal_basis:"):
                legal_basis = line.split(":", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("quiet_windows:"):
                current_list = ("quiet", quiet_windows); continue
            elif line.startswith("focus_windows:"):
                current_list = ("focus", focus_windows); continue
            elif line.startswith("-") and current_list:
                # Expect format: - { start_utc_hour: X, end_utc_hour: Y }
                try:
                    brace = line.split("{",1)[1].rsplit("}",1)[0]
                    parts = [p.strip() for p in brace.split(",")]
                    kv = {}
                    for p in parts:
                        k,v = [x.strip() for x in p.split(":",1)]
                        kv[k] = int(v)
                    current_list[1].append({
                        "start_utc_hour": kv.get("start_utc_hour", 0),
                        "end_utc_hour": kv.get("end_utc_hour", 0)
                    })
                except Exception:
                    continue
            else:
                current_list = None

    return {
        "legal_basis": legal_basis,
        "quiet_windows": quiet_windows,
        "focus_windows": focus_windows,
    }

def _hour_in_any_windows(hour_utc: int, windows: list) -> bool:
    for w in windows:
        s = int(w.get("start_utc_hour", 0)) % 24
        e = int(w.get("end_utc_hour", 0)) % 24
        if s <= e:
            if s <= hour_utc < e:
                return True
        else:
            # window crosses midnight
            if hour_utc >= s or hour_utc < e:
                return True
    return False

# --- module API ---------------------------------------------------------------

def init():
    """
    Returns a default state; kept minimal to align with your module signatures.
    """
    return {"cycles": 0}

def run(ctx: Dict[str, Any] | None, state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide temporal action based on Protection Index (pi), urgency, and current policy.
    - ctx may include:
        ctx["protection_index"] : float in [0,1]
        ctx["urgency"]          : "urgent" | "non-urgent"
        ctx["reason"]           : str rationale (optional)
    """
    state["cycles"] = int(state.get("cycles", 0)) + 1
    pi = float((ctx or {}).get("protection_index", 0.1))
    urgency = (ctx or {}).get("urgency", "non-urgent")
    reason = (ctx or {}).get("reason", "temporal smoke probe")

    policy_path = os.path.join("configs", "temporal_policy.cov")
    policy = _read_cov_policy(policy_path)
    quiet = policy.get("quiet_windows", [])
    focus = policy.get("focus_windows", [])
    legal_basis = policy.get("legal_basis", "Ethical Governance")

    now = _now_utc()
    hour = now.hour
    in_quiet = _hour_in_any_windows(hour, quiet)
    in_focus = _hour_in_any_windows(hour, focus)

    # Decision logic:
    # - If PI high OR urgency "urgent" -> proceed-override (even during quiet/focus)
    # - Else if in quiet window and non-urgent -> batch
    # - Else proceed
    decision = "proceed"
    window_type = "none"
    why_now = "Low risk and not in restricted window."
    alternatives = "Could batch later if operator prefers."

    if pi >= 0.7 or urgency == "urgent":
        decision = "proceed-override"
        window_type = "override"
        why_now = "High protection risk or urgent context; acting immediately reduces potential harm."
        alternatives = "If human oversight available, confirm proceed; else log and proceed."
    elif in_quiet and urgency != "urgent":
        decision = "batch"
        window_type = "quiet"
        why_now = "Non-urgent during quiet hours—deferring respects user time and reduces disruption."
        alternatives = "Execute at next focus/normal window."
    elif in_focus:
        window_type = "focus"
        why_now = "Inside focus window; proceed only if action is minimally disruptive."

    # Risk: treat inappropriate timing as small moral friction; scale by PI.
    timing_penalty = 0.0
    if decision == "proceed" and in_quiet:
        timing_penalty = 0.15
    risk = min(1.0, 0.1 + pi * 0.2 + timing_penalty)

    # Compose MIL-like flat temporal fields for easy embedding
    mil_temporal = {
        "temporal.explain.why_now": why_now,
        "temporal.explain.alternatives": alternatives,
        "temporal.human_time": now.astimezone().isoformat(),
        "temporal.universal_time": now.isoformat(),
        "temporal.window_type": window_type,
        "temporal.legal_basis": legal_basis,
        # Batch identifier is left for callers to compute if they want to group items.
    }

    rationale = f"Temporal decision: {decision} (window={window_type}, pi={pi:.2f}, urgency={urgency})."
    data = {
        "mil_temporal": mil_temporal,
        "decision": decision,
        "pi": pi,
        "urgency": urgency,
        "why": reason,
        "window": window_type
    }

    return {
        "ok": True,
        "action": decision if decision != "batch" else "defer",
        "risk": risk,
        "rationale": rationale,
        "data": data
    }
