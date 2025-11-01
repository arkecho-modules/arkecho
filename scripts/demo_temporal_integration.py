#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArkEcho v13 — Temporal Integration Demo
- Uses new_modules.temporal_governor.TemporalGovernor
- Loads configs/temporal_policy.cov if present (JSON)
- Prints deterministic decisions and MIL-temporal payloads
- Writes a demo JSON to logs/integrity_temporal_demo.json
"""

from __future__ import annotations
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

# Local import (new module you just added)
try:
    from new_modules.temporal_governor import TemporalGovernor
except Exception as e:
    print("FATAL: Cannot import new_modules.temporal_governor:", repr(e))
    print("Make sure the file exists at: new_modules/temporal_governor.py")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "temporal_policy.cov"
LOGS_DIR = REPO_ROOT / "logs"

def load_policy() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            text = CONFIG_PATH.read_text(encoding="utf-8")
            # Treat .cov as JSON for v13 demo; no external deps.
            return json.loads(text)
        except Exception as e:
            print("WARN: Failed to parse configs/temporal_policy.cov as JSON, using defaults.", repr(e))
            return {}
    else:
        print("INFO: configs/temporal_policy.cov not found; using default policy.")
        return {}

def print_case(title: str, result: Dict[str, Any]) -> None:
    print(f"\n{title}")
    print("-" * 72)
    print("Decision :", result["decision"])
    print("MIL.temporal:")
    print(json.dumps(result["mil_temporal"], indent=2))
    print("-" * 72)

def main() -> int:
    print("=" * 72)
    print(" ArkEcho v13 — Temporal Integration Demo ".center(72, "="))
    print("=" * 72)

    policy = load_policy()
    tg = TemporalGovernor(policy)

    # Sample user profiles (adjust to test)
    adult = {
        "user_id": "user-adult-001",
        "is_minor": False,
        "jurisdiction": "UK",
        "quiet_windows": ["22:00-07:00"],
        "focus_windows": ["09:00-12:00","13:00-17:00"]
    }
    child = {
        "user_id": "user-child-007",
        "is_minor": True,
        "jurisdiction": "EU",
        "quiet_windows": ["20:00-07:00"],
        "focus_windows": ["09:00-12:00","13:00-16:00"]
    }

    # Run three canonical cases
    r1 = tg.decide(adult, protection_index=0.25, urgency="non-urgent",
                   reason="Demo: adult, non-urgent.")
    r2 = tg.decide(adult, protection_index=0.25, urgency="urgent",
                   reason="Demo: adult, urgent.")
    r3 = tg.decide(child, protection_index=0.85, urgency="non-urgent",
                   reason="Demo: child, high protection index.")

    print_case("CASE 1 — Adult / non-urgent", {"decision": r1.decision, "mil_temporal": r1.mil_temporal})
    print_case("CASE 2 — Adult / urgent", {"decision": r2.decision, "mil_temporal": r2.mil_temporal})
    print_case("CASE 3 — Child / high PI", {"decision": r3.decision, "mil_temporal": r3.mil_temporal})

    # Persist a small demo snapshot (does not alter your normal logs)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "kind": "temporal_demo",
        "created": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "cases": [
            {"title": "adult_non_urgent", "decision": r1.decision, "mil_temporal": r1.mil_temporal},
            {"title": "adult_urgent", "decision": r2.decision, "mil_temporal": r2.mil_temporal},
            {"title": "child_high_pi", "decision": r3.decision, "mil_temporal": r3.mil_temporal}
        ]
    }
    out_path = LOGS_DIR / "integrity_temporal_demo.json"
    out_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"\nSaved snapshot → {out_path}")

    print("\nDone.\n")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise
