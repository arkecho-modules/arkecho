#!/usr/bin/env python3
"""
ArkEcho v13 — Temporal Policy Demo (stand-alone)
This demo prints a timing-aware decision (proceed / batch / halt) and a
Moral Integrity Ledger (MIL) temporal payload. It has **no external imports**
from your codebase, so it will always print something when executed.
"""

import sys
import json
from dataclasses import dataclass
from datetime import datetime, time, timezone

# ---------- Utilities (stand-alone) ----------

def _parse_hhmm(s: str) -> time:
    s = s.strip()
    hh, mm = s.split(":")
    return time(hour=int(hh), minute=int(mm))

def _now_local_iso() -> str:
    # Use local machine time; format ISO with timezone if available
    try:
        return datetime.now().astimezone().isoformat(timespec="seconds")
    except Exception:
        return datetime.now().isoformat(timespec="seconds")

def _now_universal_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def _in_window(now: time, window: str) -> bool:
    """
    window format: 'HH:MM-HH:MM'  (can cross midnight).
    """
    start_s, end_s = window.split("-")
    start = _parse_hhmm(start_s)
    end   = _parse_hhmm(end_s)

    if start <= end:
        # normal same-day window
        return start <= now <= end
    else:
        # crosses midnight, e.g. 22:00-07:00
        return now >= start or now <= end

def _first_matching_window(now_local: time, windows: list[str]) -> str | None:
    for w in windows:
        if _in_window(now_local, w):
            return w
    return None

# ---------- Demo policy logic (mirrors what a temporal governor would do) ----------

@dataclass
class UserProfile:
    user_id: str
    is_minor: bool
    jurisdiction: str
    quiet_windows: list[str]  # e.g. ["22:00-07:00"]
    focus_windows: list[str]  # e.g. ["09:00-12:00","13:00-17:00"]

@dataclass
class Decision:
    decision: str          # "proceed" | "batch" | "halt" | "proceed-override"
    reason: str
    mil_temporal: dict

def temporal_decide(user: UserProfile, protection_index: float, urgency: str, reason: str) -> Decision:
    """
    Very small, deterministic decision tree for demo:
      - If PI >= 0.80 and user is minor -> HALT
      - Else if in quiet window and urgency == 'non-urgent' -> BATCH
      - Else -> PROCEED
    Also emits a MIL-style temporal block with human/universal time and rationale.
    """
    now_local_dt = datetime.now().astimezone()
    now_local = now_local_dt.time()
    now_local_iso = _now_local_iso()
    now_universal_iso = _now_universal_iso()

    in_quiet = _first_matching_window(now_local, user.quiet_windows)
    in_focus = _first_matching_window(now_local, user.focus_windows)

    # Baseline legal basis label (adjust as needed)
    legal_basis = "Ethical Governance"

    if user.is_minor and protection_index >= 0.80:
        decision = "halt"
        why_now  = "Child context + high protection index triggers Guardian stop."
    elif in_quiet and urgency == "non-urgent":
        decision = "batch"
        why_now  = f"In quiet window {in_quiet}; deferring non-urgent task."
    else:
        decision = "proceed"
        why_now  = "No quiet constraint conflict and/or urgent enough to proceed."

    # Build MIL-temporal flattened dict (dot-keys) to mirror your extension
    mil_temporal = {
        "temporal.explain.why_now": why_now,
        "temporal.explain.alternatives": (
            "Batch until focus window" if in_quiet else
            "Proceed now; monitor PI and user status"
        ),
        "temporal.human_time": now_local_iso,
        "temporal.universal_time": now_universal_iso,
        "temporal.window_type": (
            "quiet" if in_quiet else ("focus" if in_focus else "none")
        ),
        "temporal.batch_id": (
            f"{user.user_id}:{now_universal_iso[:19].replace(':','-')}"
            if decision == "batch" else None
        ),
        "temporal.quiet_override_reason": None,
        "temporal.legal_basis": legal_basis,
    }

    # Compose a readable reason if none supplied
    out_reason = reason or why_now

    return Decision(decision=decision, reason=out_reason, mil_temporal=mil_temporal)

# ---------- Pretty printing ----------

def _print_header():
    print("="*72)
    print(" ArkEcho v13 — Temporal Policy Demo (stand-alone) ".center(72, "="))
    print("="*72)

def _print_result(title: str, result: Decision):
    print(f"\n{title}")
    print("-"*72)
    print(f"Decision : {result.decision}")
    print(f"Reason   : {result.reason}")
    print("MIL.temporal:")
    print(json.dumps(result.mil_temporal, indent=2))
    print("-"*72)

# ---------- Main ----------

def main():
    _print_header()

    # Sample users (tweak to test)
    adult = UserProfile(
        user_id="user-adult-001",
        is_minor=False,
        jurisdiction="UK",
        quiet_windows=["22:00-07:00"],
        focus_windows=["09:00-12:00","13:00-17:00"],
    )
    child = UserProfile(
        user_id="user-child-007",
        is_minor=True,
        jurisdiction="EU",
        quiet_windows=["20:00-07:00"],
        focus_windows=["09:00-12:00","13:00-16:00"],
    )

    # 1) Adult, non-urgent (may batch if now is inside quiet window)
    r1 = temporal_decide(
        user=adult,
        protection_index=0.25,
        urgency="non-urgent",
        reason="Demo: adult, non-urgent message."
    )
    _print_result("CASE 1 — Adult / non-urgent", r1)

    # 2) Adult, urgent (should proceed even if inside quiet)
    r2 = temporal_decide(
        user=adult,
        protection_index=0.25,
        urgency="urgent",
        reason="Demo: adult, urgent message."
    )
    _print_result("CASE 2 — Adult / urgent", r2)

    # 3) Child, high PI (should halt)
    r3 = temporal_decide(
        user=child,
        protection_index=0.85,
        urgency="non-urgent",
        reason="Demo: child context with high protection index."
    )
    _print_result("CASE 3 — Child / high PI", r3)

    print("\nDone.\n")

if __name__ == "__main__":
    # Force unbuffered output if someone runs via python -u, but also be explicit
    try:
        main()
    except Exception as e:
        # If anything goes wrong, we still print something
        print("!! DEMO ERROR:", repr(e))
        sys.exit(1)
