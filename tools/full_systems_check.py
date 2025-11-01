#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArkEcho v13 — Full Systems Check (orchestrator)

What it does:
  1) Runs a default temporal smoke.
  2) Runs a "night override" temporal smoke (quiet window + urgent + high PI).
  3) Exports HTML for any UK logs (if present).
  4) Exports HTML for any US logs (if present).
  5) Prints a compact summary.

Note: This script does not import your core modules; it orchestrates tools.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
LOGS = ROOT / "logs"
HTML = ROOT / "html"


def _run(cmd: list[str]) -> int:
    proc = subprocess.run(cmd, text=True, cwd=str(ROOT))
    return proc.returncode


def main() -> int:
    # 1) Temporal smoke (default)
    rc1 = _run([sys.executable, str(TOOLS / "smoke_all_systems.py")])

    # 2) Night override scenario
    rc2 = _run([
        sys.executable, str(TOOLS / "smoke_all_systems.py"),
        "--pi", "0.85", "--urgency", "urgent",
        "--why", "night emergency", "--alts", "wait;batch;call-guardian",
        "--force-window", "quiet"
    ])

    # 3) Export UK logs
    uk = sorted(LOGS.glob("integrity_UK_*.json"))
    rc3 = 0 if not uk else _run([sys.executable, str(TOOLS / "export_html_audit.py"), *map(str, uk)])

    # 4) Export US logs
    us = sorted(LOGS.glob("integrity_US_*.json"))
    rc4 = 0 if not us else _run([sys.executable, str(TOOLS / "export_html_audit.py"), *map(str, us)])

    # Summary
    print("--- SUMMARY ---")
    print(f"smoke default: rc={rc1}")
    print(f"smoke night  : rc={rc2}")
    print(f"export UK    : rc={rc3}")
    print(f"export US    : rc={rc4}")
    print("HTML outdir  :", HTML)

    return 0 if all(rc == 0 for rc in (rc1, rc2, rc3, rc4)) else 1


if __name__ == "__main__":
    sys.exit(main())
