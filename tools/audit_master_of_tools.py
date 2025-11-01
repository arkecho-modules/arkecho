#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArkEcho v13 — Master Audit of Audit Tools

Runs:
  1) smoke_test.py (expects JSON with ok=True)
  2) smoke_all_systems.py (default run)
  3) smoke_all_systems.py (override scenario)
  4) export_html_audit.py for UK/US using Path.glob (no shell globs)
  5) full_systems_check.py
  6) Validates last UK/US JSON metrics (if present) against canonical values

Writes a master audit JSON summary to logs/master_audit_*.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
LOGS = ROOT / "logs"
HTML = ROOT / "html"
LOGS.mkdir(parents=True, exist_ok=True)
HTML.mkdir(parents=True, exist_ok=True)

CANONICAL = {
    "avg_risk": 0.121,
    "reliability": 1.000,
    "coherence": 0.940,
}


def _run(cmd: list[str]) -> int:
    res = subprocess.run(cmd, text=True, capture_output=True, cwd=ROOT)
    print("\n$ " + " ".join(map(str, cmd)))
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip(), file=sys.stderr)
    return res.returncode


def _parse_last_json(prefix: str) -> Path | None:
    candidates = sorted(LOGS.glob(f"{prefix}*.json"))
    return candidates[-1] if candidates else None


def _load_metrics(path: Path | None) -> dict[str, Any] | None:
    if not path or not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    metrics = data.get("metrics")
    if isinstance(metrics, dict):
        return metrics
    # tolerate flat
    return {
        k: data.get(k)
        for k in ("avg_risk", "reliability", "stability", "coherence", "mhi", "MHI")
        if k in data
    } or None


def _meets_canonical(m: dict[str, Any] | None) -> bool:
    if not m:
        # If no metrics (no logs), do not fail the master audit.
        return True
    try:
        return (
            abs(float(m.get("avg_risk")) - CANONICAL["avg_risk"]) < 1e-9 and
            abs(float(m.get("reliability")) - CANONICAL["reliability"]) < 1e-9 and
            abs(float(m.get("coherence")) - CANONICAL["coherence"]) < 1e-9
        )
    except Exception:
        return False


def main(argv: list[str] | None = None) -> int:
    status: dict[str, bool] = {}

    print("[1] smoke_test.py default...")
    status["smoke_test"] = (_run([sys.executable, str(TOOLS / "smoke_test.py")]) == 0)

    print("[2] smoke_all_systems.py default...")
    status["smoke_all"] = (_run([sys.executable, str(TOOLS / "smoke_all_systems.py")]) == 0)

    print("[3] smoke_all_systems.py override...")
    status["smoke_override"] = (_run([
        sys.executable, str(TOOLS / "smoke_all_systems.py"),
        "--pi", "0.85", "--urgency", "urgent",
        "--why", "night emergency", "--alts", "wait;batch;call-guardian",
        "--force-window", "quiet",
    ]) == 0)

    print("[4] export_html_audit.py for UK/US...")
    uk_files = sorted(LOGS.glob("integrity_UK_*.json"))
    us_files = sorted(LOGS.glob("integrity_US_*.json"))
    rc_html_uk = 0 if not uk_files else _run([sys.executable, str(TOOLS / "export_html_audit.py"), *map(str, uk_files)])
    rc_html_us = 0 if not us_files else _run([sys.executable, str(TOOLS / "export_html_audit.py"), *map(str, us_files)])
    status["export_html"] = (rc_html_uk == 0 and rc_html_us == 0)

    print("[5] full_systems_check.py ...")
    status["full_check"] = (_run([sys.executable, str(TOOLS / "full_systems_check.py")]) == 0)

    print("[6] Validating last JSON results...")
    status["last_uk_metrics"] = _meets_canonical(_load_metrics(_parse_last_json("integrity_UK_")))
    status["last_us_metrics"] = _meets_canonical(_load_metrics(_parse_last_json("integrity_US_")))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out = LOGS / f"master_audit_{timestamp}.json"
    report = {
        "timestamp": timestamp,
        "tool_status": status,
        "passed": all(status.values()),
    }
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n--- MASTER AUDIT SUMMARY ---", flush=True)
    for k, v in status.items():
        print(f"{k}: {'✅' if v else '❌'}", flush=True)
    print(f"Master Audit Log: {out}", flush=True)

    return 0 if report["passed"] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
