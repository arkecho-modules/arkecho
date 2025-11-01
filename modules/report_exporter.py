# Filename: report_exporter.py
# ArkEcho Systems © 2025
# Refactored for v11r1: deterministic report synthesis (no file I/O), unified schema,
# and safe audit summary for downstream archiving.

from __future__ import annotations
from typing import Dict, Any, Tuple
import datetime
import json

NAME = "Report Exporter"
VERSION = "1.1.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_log(event: str, state: Dict[str, Any]) -> None:
    """Simple append-only in-memory audit log."""
    state.setdefault("_audit", []).append({"event": event, "time": datetime.datetime.utcnow().isoformat()})

def safe_serialize(obj: Any) -> str:
    """Deterministically serialize Python structures to compact JSON."""
    try:
        return json.dumps(obj, sort_keys=True, ensure_ascii=False)
    except Exception:
        return str(obj)

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------
def init() -> Dict[str, Any]:
    """Initialize reporting state."""
    return {
        "reports": [],
        "exports": 0,
        "last_summary": None,
    }

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
def run(ctx: Dict[str, Any], state: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generates a deterministic, reversible summary report of system performance and moral metrics.
    Inputs:
      - inputs: dict of modules' outputs
      - format: "dict" | "json" | "text"
      - tag: optional string label for report
    """
    inputs: Dict[str, Any] = ctx.get("inputs", {})
    fmt: str = ctx.get("format", "dict")
    tag: str = ctx.get("tag", "cycle")

    timestamp = datetime.datetime.utcnow().isoformat(timespec="seconds")
    summary = {
        "tag": tag,
        "timestamp": timestamp,
        "modules": {},
    }

    # Aggregate and normalize module summaries
    total_risk = 0.0
    total_ok = 0
    total_count = len(inputs)
    for name, out in inputs.items():
        mod_ok = bool(out.get("ok", True))
        risk = float(out.get("risk", 0.0))
        total_risk += risk
        total_ok += 1 if mod_ok else 0
        summary["modules"][name] = {
            "ok": mod_ok,
            "risk": round(risk, 3),
            "action": out.get("action"),
        }

    avg_risk = round(total_risk / max(total_count, 1), 3)
    reliability = round(total_ok / max(total_count, 1), 3)

    report_data = {
        "avg_risk": avg_risk,
        "reliability": reliability,
        "module_count": total_count,
        "time": timestamp,
        "tag": tag,
    }

    # Deterministic serialization
    if fmt == "json":
        output_data = safe_serialize(report_data)
    elif fmt == "text":
        output_data = f"[{timestamp}] {tag}: risk={avg_risk:.2f}, reliability={reliability:.2f}"
    else:
        output_data = report_data

    state["exports"] = state.get("exports", 0) + 1
    state["last_summary"] = report_data
    state.setdefault("reports", []).append(report_data)
    safe_log(f"ReportExporter:generated:{tag}", state)

    output = {
        "ok": True,
        "action": "export",
        "risk": avg_risk,
        "rationale": f"Generated summary report for {total_count} modules with reliability={reliability:.2f}.",
        "data": {
            "report": output_data,
            "avg_risk": avg_risk,
            "reliability": reliability,
            "format": fmt,
            "tag": tag,
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
        "summary": "Synthesizes deterministic, reversible reports summarizing moral and operational health.",
        "inputs": ["inputs", "format", "tag"],
        "outputs": ["report", "avg_risk", "reliability", "action"],
    }
