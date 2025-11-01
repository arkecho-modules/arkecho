#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArkEcho v13 — Temporal Governor (integration-safe, stand-alone)
- No imports from ArkEcho internals required
- Consumes a "policy" dict and a "user_profile" dict
- Produces a decision and a flattened MIL "temporal" payload
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Any, Dict, Optional, List

# ------------------------------ Utilities ------------------------------

def _parse_hhmm(s: str) -> time:
    s = s.strip()
    hh, mm = s.split(":")
    return time(hour=int(hh), minute=int(mm))

def _now_local_iso() -> str:
    try:
        return datetime.now().astimezone().isoformat(timespec="seconds")
    except Exception:
        return datetime.now().isoformat(timespec="seconds")

def _now_universal_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _in_window(now: time, window: str) -> bool:
    """
    window format: 'HH:MM-HH:MM'  (supports crossing midnight, e.g. 22:00-07:00).
    """
    start_s, end_s = window.split("-")
    start = _parse_hhmm(start_s)
    end   = _parse_hhmm(end_s)
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end  # crosses midnight

def _first_match(now_local: time, windows: List[str]) -> Optional[str]:
    for w in windows:
        try:
            if _in_window(now_local, w):
                return w
        except Exception:
            # Skip malformed window; governor must remain deterministic
            continue
    return None

# ------------------------------ Data types ------------------------------

@dataclass
class UserProfile:
    user_id: str
    is_minor: bool
    jurisdiction: str
    quiet_windows: List[str]
    focus_windows: List[str]

@dataclass
class Decision:
    decision: str               # "proceed" | "batch" | "halt" | "proceed-override"
    reason: str
    mil_temporal: Dict[str, Any]
    status: str = "ok"

# ------------------------------ Policy ------------------------------

_DEFAULT_POLICY: Dict[str, Any] = {
    "version": "v13",
    "legal_basis_default": "Ethical Governance",
    "respect_quiet_windows": True,
    "respect_focus_windows": True,
    "allow_urgent_override": True,
    "child_halt_pi": 0.80,
    "batch_label": "quiet-batch",
}

# ------------------------------ Governor ------------------------------

class TemporalGovernor:
    def __init__(self, policy: Optional[Dict[str, Any]] = None) -> None:
        self.policy = dict(_DEFAULT_POLICY)
        if policy:
            # shallow merge; defaults remain if policy omits fields
            self.policy.update({k: v for k, v in policy.items() if v is not None})

    # Deterministic batch key
    def batch_key(self, user_id: str, universal_iso: Optional[str] = None) -> str:
        if not universal_iso:
            universal_iso = _now_universal_iso()
        # Strip colons for file-system safety
        safe_ts = universal_iso[:19].replace(":", "-")
        return f"{user_id}:{safe_ts}"

    def decide(
        self,
        user_profile: Dict[str, Any],
        protection_index: float,
        urgency: str,
        reason: str = "",
    ) -> Decision:
        """
        Core deterministic decision tree:
          1) If child + PI >= child_halt_pi -> HALT
          2) Else if in quiet and non-urgent -> BATCH
          3) Else if in quiet and urgent and allow_urgent_override -> PROCEED-OVERRIDE
          4) Else -> PROCEED
        Emits a flattened MIL temporal payload (dot-keys).
        """
        # Normalize user
        u = UserProfile(
            user_id=str(user_profile.get("user_id") or "unknown"),
            is_minor=bool(user_profile.get("is_minor", False)),
            jurisdiction=str(user_profile.get("jurisdiction") or "UK"),
            quiet_windows=list(user_profile.get("quiet_windows") or []),
            focus_windows=list(user_profile.get("focus_windows") or []),
        )

        now_local_dt = datetime.now().astimezone()
        now_local = now_local_dt.time()
        now_local_iso = _now_local_iso()
        now_universal_iso = _now_universal_iso()

        in_quiet = _first_match(now_local, u.quiet_windows)
        in_focus = _first_match(now_local, u.focus_windows)

        legal_basis = str(self.policy.get("legal_basis_default", "Ethical Governance"))
        child_pi = float(self.policy.get("child_halt_pi", 0.80))
        respect_quiet = bool(self.policy.get("respect_quiet_windows", True))
        allow_override = bool(self.policy.get("allow_urgent_override", True))

        urgency_norm = str(urgency or "non-urgent").lower().strip()
        is_urgent = urgency_norm in {"urgent", "critical", "high"}

        # --- Decision tree ---
        if u.is_minor and protection_index >= child_pi:
            decision = "halt"
            why_now = "Child context + high protection index ≥ threshold."
        elif respect_quiet and in_quiet and not is_urgent:
            decision = "batch"
            why_now = f"In quiet window {in_quiet}; deferring non-urgent task."
        elif respect_quiet and in_quiet and is_urgent and allow_override:
            decision = "proceed-override"
            why_now = f"In quiet window {in_quiet}, but urgent override permitted."
        else:
            decision = "proceed"
            why_now = "No quiet constraint conflict or override not required."

        alternatives = (
            "Batch until next focus window"
            if in_quiet and decision in {"batch", "proceed-override"}
            else "Proceed now; monitor PI and context"
        )

        batch_id = self.batch_key(u.user_id, now_universal_iso) if decision == "batch" else None

        mil_temporal = {
            "temporal.explain.why_now": why_now,
            "temporal.explain.alternatives": alternatives,
            "temporal.human_time": now_local_iso,
            "temporal.universal_time": now_universal_iso,
            "temporal.window_type": ("quiet" if in_quiet else ("focus" if in_focus else "none")),
            "temporal.batch_id": batch_id,
            "temporal.quiet_override_reason": (
                "Urgent task allowed during quiet window"
                if decision == "proceed-override" else None
            ),
            "temporal.legal_basis": legal_basis,
        }

        out_reason = reason or why_now
        return Decision(decision=decision, reason=out_reason, mil_temporal=mil_temporal)

# Back-compat shim used by some callers that expect a module-level function
def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload = {
      "policy": {...},                # dict
      "user_profile": {...},          # dict
      "protection_index": 0.10,       # float
      "urgency": "non-urgent",        # str
      "reason": "..."                 # str
    }
    """
    policy = payload.get("policy") or {}
    tg = TemporalGovernor(policy)
    user = payload.get("user_profile") or {}
    pi = float(payload.get("protection_index") or 0.0)
    urgency = str(payload.get("urgency") or "non-urgent")
    reason = str(payload.get("reason") or "")
    dec = tg.decide(user, pi, urgency, reason)
    return {"status": dec.status, "result": {"decision": dec.decision, "mil_temporal": dec.mil_temporal}}
