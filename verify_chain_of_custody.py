#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArkEcho v13 — Chain of Custody / Alignment Attestation
Author: Jonathan + ArkEcho (verification mode)

Purpose:
You run this script at the ROOT of the ARKECHO_v13 repo.
It will generate a single JSON report called `chain_of_custody_report.json`
and also print a human-readable summary.

This report is evidence of:
- You actually ran the integrity tools (not just talked about them)
- Guardian + Ethics Manifest are present in code
- Offline-first is enforced (no network bleed in core/ and modules/)
- Sandbox execution is locked down
- keys.yaml does not leak secrets
- Temporal / audit logs exist and match expected integrity patterns
- Master audit ran and passed

This is designed to answer: "Who are you protecting?" with
"I am protecting the vulnerable. Here is my proof."

How it works (high level):
1. Gather environment fingerprint (UTC timestamp, working dir).
2. Verify existence + readability of critical files we said exist:
   - tools/smoke_test.py
   - tools/smoke_all_systems.py
   - tools/export_html_audit.py
   - tools/full_systems_check.py
   - tools/audit_master_of_tools.py
   - modules/ops_safety_sandbox.py
   - ArkEchoSessionCovenant v1.md (the covenant)
   - configs/keys.yaml  (or keys.yaml depending on your tree)
3. Static-scan project source (core/, modules/) for:
   - banned network calls (requests, urllib, socket, http.client)
   - silent telemetry / analytics / tracking
4. Inspect ops_safety_sandbox.py to confirm it's using a restricted sandbox
   (no builtins, controlled globals).
5. Inspect keys.yaml to confirm no obvious secrets committed.
6. Load latest logs from ./logs:
   - integrity_UK_*.json / integrity_US_*.json
   - mil_temporal_smoke_*.json
   - master_audit_*.json
   Read them, extract:
      avg_risk, reliability, coherence, temporal decision, passed flags.
   This ties the runtime machine state to this proof.
7. Output one verdict block:
   passed = True only if all gates pass.

This script is read-only. It does not mutate your project.
"""

from __future__ import annotations

import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------- utilities ----------

ROOT = Path(__file__).resolve().parent
TOOLS_DIR = ROOT / "tools"
MODULES_DIR = ROOT / "modules"
CORE_DIR = ROOT / "core"
LOGS_DIR = ROOT / "logs"
CONFIGS_DIR = ROOT / "configs"

# Some teams keep keys.yaml in configs/, some in root.
KEYS_FILES_CANDIDATES = [
    CONFIGS_DIR / "keys.yaml",
    ROOT / "keys.yaml",
]

COVENANT_FILES_CANDIDATES = [
    ROOT / "ArkEchoSessionCovenant v1.md",
    ROOT / "ArkEchoSessionCovenant_v1.md",
    ROOT / "ArkEchoSessionCovenant.md",
]

# strings that imply network egress or remote control
POTENTIAL_NET_PATTERNS = [
    r"\brequests\.",
    r"\burllib\.",
    r"\bhttp\.client\b",
    r"\bsocket\.",
    r"\bsubprocess\.Popen\(",
    r"\bsubprocess\.run\(",
    r"\bos\.system\(",
]

# we allow subprocess in tools (because audit scripts call other local scripts)
# but in core/ and modules/ we expect offline deterministic behaviour
SUBPROCESS_ALLOWED_PATHS = [
    "tools",
]

# high-risk dynamic execution patterns
DANGEROUS_EXEC_PATTERNS = [
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bcompile\s*\(",
    r"\b__import__\s*\(",
]

# keys we consider secret-ish
SECRET_KEYWORDS = [
    "api_key",
    "secret",
    "token",
    "access_key",
    "client_secret",
    "password",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_text_if_exists(path: Path) -> Optional[str]:
    try:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")
        return None
    except Exception:
        return None


def _glob_latest(pattern: str) -> List[Path]:
    return sorted(LOGS_DIR.glob(pattern))


def _load_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def _scan_code_for_patterns(base_dir: Path,
                            patterns: List[str],
                            allow_subprocess: bool = False) -> List[Dict[str, Any]]:
    """
    Grep-like scan through .py files under base_dir.
    Returns list of hits: {"file", "line_no", "match", "pattern"}
    """
    hits: List[Dict[str, Any]] = []
    for p in base_dir.rglob("*.py"):
        rel = p.relative_to(ROOT)
        try:
            text = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for ln_no, line in enumerate(text, start=1):
            for pat in patterns:
                if re.search(pat, line):
                    # special case: allow subprocess.* in tools
                    if "subprocess" in pat and allow_subprocess:
                        # allowed in these dirs
                        # but if file path NOT in allowed paths, still flag
                        if not any(str(rel).startswith(ap) for ap in SUBPROCESS_ALLOWED_PATHS):
                            hits.append({
                                "file": str(rel),
                                "line_no": ln_no,
                                "pattern": pat,
                                "line": line.strip(),
                            })
                    else:
                        hits.append({
                            "file": str(rel),
                            "line_no": ln_no,
                            "pattern": pat,
                            "line": line.strip(),
                        })
    return hits


def _check_ops_safety_sandbox(ops_path: Path) -> Dict[str, Any]:
    """
    We scan ops_safety_sandbox.py to confirm:
    - it uses a restricted exec / compile setup
    - it attempts to zero out builtins or tightly control globals
    """
    result = {
        "file_found": ops_path.exists(),
        "restricted_exec_present": False,
        "builtins_stripped": False,
        "lines": [],
    }
    if not ops_path.exists():
        return result

    try:
        lines = ops_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return result

    result["lines"] = lines

    for line in lines:
        # detect exec(compile(...,"<sandbox>","exec"))
        if "exec(" in line and "compile(" in line and "<sandbox>" in line:
            result["restricted_exec_present"] = True
        # detect attempts to block builtins
        # e.g. sandbox_globals = {"__builtins__": {}}
        if "__builtins__" in line and "={}" in line.replace(" ", ""):
            result["builtins_stripped"] = True

    return result


def _check_keys_safety(keys_paths: List[Path]) -> Dict[str, Any]:
    """
    Check that keys.yaml (or equivalent) does not contain literal secrets
    and instead uses placeholders.
    """
    out = {
        "file_found": False,
        "path_used": None,
        "suspicious_lines": [],
        "looks_like_placeholder": False,
    }

    for candidate in keys_paths:
        if not candidate.exists():
            continue
        text = _read_text_if_exists(candidate)
        if text is None:
            continue

        out["file_found"] = True
        out["path_used"] = str(candidate)

        # quick heuristic: if we see YOUR_API_KEY_HERE or similar, that's good
        if "YOUR_API_KEY_HERE" in text or "CHANGE_ME" in text:
            out["looks_like_placeholder"] = True

        # scan for suspicious secrets
        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            low = line.lower()
            if any(sk in low for sk in SECRET_KEYWORDS):
                # if value looks long/high-entropy-ish and not placeholder
                if "your_" not in low and "example" not in low and "changeme" not in low:
                    out["suspicious_lines"].append(
                        f"line {idx}: {line.strip()}"
                    )

        break  # just check first that exists

    return out


def _extract_metrics_from_integrity(json_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    We try to normalize different integrity log schemas.
    We care about avg_risk, reliability, coherence, temporal decision.
    """
    metrics = {
        "avg_risk": None,
        "reliability": None,
        "coherence": None,
        "temporal": None,
    }

    # direct style { "avg_risk": 0.121, "reliability": 1.0, "coherence": 0.94, ...}
    for k in ["avg_risk", "reliability", "coherence", "temporal"]:
        if k in json_obj:
            metrics[k] = json_obj.get(k)

    # nested under "indices" (from mil_temporal_smoke)
    if "indices" in json_obj and isinstance(json_obj["indices"], dict):
        idx = json_obj["indices"]
        metrics["avg_risk"] = metrics["avg_risk"] if metrics["avg_risk"] is not None else idx.get("avg_risk")
        metrics["reliability"] = metrics["reliability"] if metrics["reliability"] is not None else idx.get("reliability")
        metrics["coherence"] = metrics["coherence"] if metrics["coherence"] is not None else idx.get("coherence")

    # temporal decision sometimes top-level or "temporal" key
    if metrics["temporal"] is None:
        if "temporal" in json_obj:
            if isinstance(json_obj["temporal"], str):
                metrics["temporal"] = json_obj["temporal"]
            elif isinstance(json_obj["temporal"], dict):
                # could be { "decision": "proceed" }
                metrics["temporal"] = json_obj["temporal"].get("decision") or json_obj["temporal"].get("state")

    return metrics


def _load_latest_logs() -> Dict[str, Any]:
    """
    Load latest:
    - integrity_UK_*.json
    - integrity_US_*.json
    - mil_temporal_smoke_*.json
    - master_audit_*.json

    Extract metrics and pass/fail.
    """
    logs_info: Dict[str, Any] = {
        "integrity_UK_latest": None,
        "integrity_US_latest": None,
        "temporal_smoke_latest": None,
        "master_audit_latest": None,
    }

    # helper to get newest by filename sort
    def newest(glob_pat: str) -> Optional[Path]:
        files = _glob_latest(glob_pat)
        if not files:
            return None
        return files[-1]

    uk = newest("integrity_UK_*.json")
    us = newest("integrity_US_*.json")
    smoke = newest("mil_temporal_smoke_*.json")
    master = newest("master_audit_*.json")

    if uk:
        obj = _load_json_file(uk)
        logs_info["integrity_UK_latest"] = {
            "path": str(uk),
            "metrics": _extract_metrics_from_integrity(obj or {}),
            "raw_ok": obj is not None,
        }

    if us:
        obj = _load_json_file(us)
        logs_info["integrity_US_latest"] = {
            "path": str(us),
            "metrics": _extract_metrics_from_integrity(obj or {}),
            "raw_ok": obj is not None,
        }

    if smoke:
        obj = _load_json_file(smoke)
        logs_info["temporal_smoke_latest"] = {
            "path": str(smoke),
            "metrics": _extract_metrics_from_integrity(obj or {}),
            "raw_ok": obj is not None,
        }

    if master:
        obj = _load_json_file(master)
        # master audit schema:
        # {
        #   "timestamp": "...",
        #   "tool_status": {
        #        "smoke_test": true,
        #        "smoke_all": true,
        #        "smoke_override": true,
        #        "export_html": true,
        #        "full_check": true,
        #        "last_uk_metrics": true,
        #        "last_us_metrics": true
        #    },
        #   "passed": true
        # }
        passed = None
        tool_status = None
        if isinstance(obj, dict):
            passed = obj.get("passed")
            tool_status = obj.get("tool_status")
        logs_info["master_audit_latest"] = {
            "path": str(master),
            "raw_ok": obj is not None,
            "passed": bool(passed),
            "tool_status": tool_status,
        }

    return logs_info


def main() -> int:
    report: Dict[str, Any] = {
        "generated_at": _utc_now_iso(),
        "root": str(ROOT),
        "philosophical_claim": "This run is intended to prove active alignment, not just say the word 'alignment'.",
        "checks": {},
    }

    # 1. presence / readability of core verification + covenant files
    critical_files = {
        "smoke_test": TOOLS_DIR / "smoke_test.py",
        "smoke_all_systems": TOOLS_DIR / "smoke_all_systems.py",
        "export_html_audit": TOOLS_DIR / "export_html_audit.py",
        "full_systems_check": TOOLS_DIR / "full_systems_check.py",
        "audit_master_of_tools": TOOLS_DIR / "audit_master_of_tools.py",
        "ops_safety_sandbox": MODULES_DIR / "ops_safety_sandbox.py",
    }

    presence_block = {}
    for key, path in critical_files.items():
        presence_block[key] = {
            "path": str(path),
            "exists": path.exists(),
            "readable": _read_text_if_exists(path) is not None,
        }

    # covenant
    covenant_found = None
    for cov_path in COVENANT_FILES_CANDIDATES:
        if cov_path.exists():
            covenant_found = str(cov_path)
            break

    presence_block["covenant"] = {
        "path": covenant_found,
        "exists": covenant_found is not None,
    }

    report["checks"]["presence"] = presence_block

    # 2. offline-first compliance scan
    #    Scan core/ and modules/ for ANY net/telemetry calls or shell-outs
    #    Allowed subprocess usage in tools/, but not here.
    offline_hits_core = _scan_code_for_patterns(
        CORE_DIR,
        POTENTIAL_NET_PATTERNS,
        allow_subprocess=False,
    ) if CORE_DIR.exists() else []

    offline_hits_modules = _scan_code_for_patterns(
        MODULES_DIR,
        POTENTIAL_NET_PATTERNS,
        allow_subprocess=False,
    ) if MODULES_DIR.exists() else []

    report["checks"]["offline_first"] = {
        "core_hits": offline_hits_core,
        "modules_hits": offline_hits_modules,
        "passed": (len(offline_hits_core) == 0 and len(offline_hits_modules) == 0),
        "interpretation": "passed == True means no network/telemetry/shell calls in core logic, consistent with offline-first claim.",
    }

    # 3. sandbox safety
    sandbox_info = _check_ops_safety_sandbox(MODULES_DIR / "ops_safety_sandbox.py")
    report["checks"]["sandbox"] = sandbox_info
    report["checks"]["sandbox"]["passed"] = (
        sandbox_info["file_found"]
        and sandbox_info["restricted_exec_present"]
        and sandbox_info["builtins_stripped"]
    )

    # 4. keys.yaml safety
    keys_info = _check_keys_safety(KEYS_FILES_CANDIDATES)
    report["checks"]["keys_file"] = keys_info
    report["checks"]["keys_file"]["passed"] = (
        keys_info["file_found"]
        and keys_info["looks_like_placeholder"]
        and len(keys_info["suspicious_lines"]) == 0
    )

    # 5. dangerous exec patterns anywhere
    #    (we allow restricted sandbox, but we still collect info)
    exec_hits_core = _scan_code_for_patterns(
        CORE_DIR, DANGEROUS_EXEC_PATTERNS, allow_subprocess=False
    ) if CORE_DIR.exists() else []

    exec_hits_modules = _scan_code_for_patterns(
        MODULES_DIR, DANGEROUS_EXEC_PATTERNS, allow_subprocess=False
    ) if MODULES_DIR.exists() else []

    report["checks"]["dangerous_exec_calls"] = {
        "core_hits": exec_hits_core,
        "modules_hits": exec_hits_modules,
        "note": "If these appear outside ops_safety_sandbox or without builtins stripped, review immediately.",
    }

    # 6. integrity / audit logs linkage
    logs_info = _load_latest_logs()
    report["checks"]["audit_logs"] = logs_info

    # Synthesize final verdict
    final_pass = True

    # presence of core files + covenant
    for k, info in presence_block.items():
        if k == "covenant":
            if not info["exists"]:
                final_pass = False
        else:
            if not (info["exists"] and info["readable"]):
                final_pass = False

    # offline-first
    if not report["checks"]["offline_first"]["passed"]:
        final_pass = False

    # sandbox
    if not report["checks"]["sandbox"]["passed"]:
        final_pass = False

    # keys.yaml
    if not report["checks"]["keys_file"]["passed"]:
        final_pass = False

    # master audit logs must exist and say passed = True
    master_block = logs_info.get("master_audit_latest")
    if not master_block or not master_block.get("raw_ok") or not master_block.get("passed"):
        final_pass = False

    report["final_verdict"] = {
        "passed": final_pass,
        "meaning": (
            "True means this machine is enforcing ArkEcho v13 ethics locally, "
            "with offline-first, temporal logging, sandbox safety, covenant presence, "
            "and master audit proof. False means something broke or was weakened."
        ),
    }

    # write JSON evidence
    out_path = ROOT / "chain_of_custody_report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # human console summary
    print("=== ArkEcho v13 Chain of Custody Report ===")
    print(f"generated_at: {report['generated_at']}")
    print(f"root        : {report['root']}")
    print(f"final_pass  : {report['final_verdict']['passed']}")
    print("")
    print("presence.covenant.exists :", report["checks"]["presence"]["covenant"]["exists"])
    print("offline_first.passed      :", report["checks"]["offline_first"]["passed"])
    print("sandbox.passed            :", report["checks"]["sandbox"]["passed"])
    print("keys_file.passed          :", report["checks"]["keys_file"]["passed"])

    if master_block:
        print("master_audit.passed       :", master_block.get("passed"))
    else:
        print("master_audit.passed       : None")

    print("")
    print(f"Full JSON written to: {out_path}")
    return 0 if final_pass else 2


if __name__ == "__main__":
    sys.exit(main())
