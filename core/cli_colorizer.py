# ArkEcho Systems © 2025
# Tiny ANSI colorizer for ArkEcho_v11r1 integrity summaries

from __future__ import annotations
from typing import Dict, Any

# --- ANSI helpers (no external deps) ---
RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"

FG = {
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

def _band_color_by_risk(r: float) -> str:
    # 0.00–0.20 green, 0.21–0.50 yellow, >0.50 red
    if r <= 0.20:
        return FG["green"]
    if r <= 0.50:
        return FG["yellow"]
    return FG["red"]

def colorize_risk(value: float, label: str = "risk") -> str:
    c = _band_color_by_risk(float(value))
    return f"{c}{label}={value:.2f}{RESET}"

def colorize_ok(ok: bool) -> str:
    return f"{FG['green']}ok=True{RESET}" if ok else f"{FG['red']}ok=False{RESET}"

def banner(text: str) -> str:
    return f"\n{BOLD}{FG['cyan']}{text}{RESET}"

def print_colored_summary(summary: Dict[str, Any]) -> None:
    """Pretty color summary. Safe to call even if running on plain TTY."""
    t = summary.get("time", "")
    modules = summary.get("modules", 0)
    ok_count = summary.get("ok", 0)
    avg_risk = float(summary.get("avg_risk", 0.0))
    reliability = float(summary.get("reliability", 0.0))
    stability = float(summary.get("stability", 0.0))
    coherence = float(summary.get("coherence", 0.0))

    print(banner(f" ArkEcho_v11r1 Integrity Summary — {t} "))
    print("=" * 65)
    print(f"  Modules OK   : {FG['green']}{ok_count}{RESET}/{modules}")
    print(f"  Avg Risk     : {_band_color_by_risk(avg_risk)}{avg_risk:.3f}{RESET}")
    print(f"  Reliability  : {FG['blue']}{reliability:.3f}{RESET}")
    print(f"  Stability    : {FG['magenta']}{stability:.3f}{RESET}")
    print(f"  Coherence    : {FG['magenta']}{coherence:.3f}{RESET}\n")

    for r in summary.get("results", []):
        mod   = f"{r['module']:<32}"
        act   = f"{FG['cyan']}{r['action']:<10}{RESET}"
        riskc = colorize_risk(float(r.get("risk", 0.0)))
        okc   = colorize_ok(bool(r.get("ok", False)))
        print(f"  - {mod} {act} {riskc} {okc}")
    print("=" * 65 + "\n")
