#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Package weekly custody bundles of integrity logs and temporal MIL records.

This script:
  - Scans ./logs for integrity_*.json and mil_temporal_*.json
  - Groups by ISO week and jurisdiction (if present in integrity file name or contents)
  - Zips each group per jurisdiction into governance/<WEEK>/arke_custody_<JUR>_<WEEK>.zip
  - Computes SHA-256 for the zip and each entry
  - Writes governance/<WEEK>/arke_custody_<JUR>_<WEEK>.manifest.json

Usage:
  python scripts/pack_governance_week.py           # auto-detect latest week with data
  python scripts/pack_governance_week.py --week 2025-W44
"""

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
GOV  = ROOT / "governance"

INTEGRITY_RE = re.compile(r"integrity_(?P<jur>[A-Z]{2})?_*([0-9T\-\+]+)?\.json")
TEMPORAL_RE  = re.compile(r"mil_temporal_([0-9T\-\+\.]+)\.json")

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _iso_week_of(path: Path) -> str:
    # Try to parse timestamp embedded, fallback to file mtime
    m = INTEGRITY_RE.match(path.name) or TEMPORAL_RE.match(path.name)
    if m and "202" in path.name:
        # naive parse: grab digits
        digits = re.findall(r"\d{8}", path.name.replace("-","").replace(":",""))
        if digits:
            s = digits[0]
            try:
                d = dt.datetime.strptime(s, "%Y%m%d").date()
                iso = d.isocalendar()
                return f"{iso[0]}-W{iso[1]:02d}"
            except Exception:
                pass
    d = dt.date.fromtimestamp(path.stat().st_mtime)
    iso = d.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"

def _jurisdiction_from_file(path: Path) -> str | None:
    # Prefer filename marker integrity_<JUR>_*.json
    m = INTEGRITY_RE.match(path.name)
    if m:
        jur = m.group("jur")
        if jur:
            return jur
    # Fallback: try to read json and look for 'jurisdiction'
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        jur = data.get("jurisdiction")
        if isinstance(jur, str) and jur:
            return jur.upper()
    except Exception:
        pass
    return None

def _list_files():
    integrities = sorted(LOGS.glob("integrity_*.json"))
    temporals   = sorted(LOGS.glob("mil_temporal_*.json"))
    return integrities, temporals

def _group_by_week_and_jur(integrities, temporals, target_week: str | None):
    # Build map: week -> jur -> [files]
    groups: dict[str, dict[str, list[Path]]] = {}

    def add(p: Path, jur: str):
        w = _iso_week_of(p)
        if target_week and w != target_week:
            return
        groups.setdefault(w, {}).setdefault(jur, []).append(p)

    for p in integrities:
        jur = _jurisdiction_from_file(p) or "NA"
        add(p, jur)

    # Temporal records have no jurisdiction embedded; attach to all jurs present for the week, or NA
    tmp_by_week = {}
    for t in temporals:
        w = _iso_week_of(t)
        tmp_by_week.setdefault(w, []).append(t)

    # merge temporals into all week/jur buckets
    for w, week_map in groups.items():
        tlist = tmp_by_week.get(w, [])
        if not tlist:
            continue
        for jur in week_map.keys():
            week_map[jur].extend(tlist)

    # if a week has only temporal records (no integrity), put under NA
    for w, tlist in tmp_by_week.items():
        if w not in groups and (not target_week or w == target_week):
            groups[w] = {"NA": list(tlist)}

    return groups

def _ensure_dir(p: Path): p.mkdir(parents=True, exist_ok=True)

def _pack_week_jur(week: str, jur: str, files: list[Path]) -> tuple[Path, dict]:
    week_dir = GOV / week
    _ensure_dir(week_dir)

    zip_name = f"arke_custody_{jur}_{week}.zip"
    zip_path = week_dir / zip_name

    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        entries = []
        for p in files:
            arc = f"{p.name}"
            zf.write(p, arcname=arc)
            entries.append({
                "file": arc,
                "sha256": _sha256(p),
                "size": p.stat().st_size
            })

    manifest = {
        "week": week,
        "jurisdiction": jur,
        "created": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "bundle": zip_name,
        "bundle_sha256": _sha256(zip_path),
        "entries": entries,
        "counts": { "files": len(entries) }
    }
    man_path = week_dir / f"arke_custody_{jur}_{week}.manifest.json"
    with man_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return zip_path, manifest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", help="ISO week like 2025-W44 (optional)")
    args = ap.parse_args()

    integrities, temporals = _list_files()
    if not integrities and not temporals:
        print("[INFO] No integrity logs or temporal MIL logs found in ./logs", file=sys.stderr)
        sys.exit(0)

    groups = _group_by_week_and_jur(integrities, temporals, args.week)

    total_bundles = 0
    for week in sorted(groups.keys()):
        jmap = groups[week]
        for jur, files in sorted(jmap.items()):
            files = sorted(set(files))
            zip_path, manifest = _pack_week_jur(week, jur, files)
            print(f"[OK] Packed {len(files)} files -> {zip_path} ({manifest['bundle_sha256'][:12]}...)")
            total_bundles += 1

    if total_bundles == 0:
        print("[INFO] Nothing to pack for the selected week.", file=sys.stderr)
    else:
        print(f"[DONE] {total_bundles} bundle(s) created under ./governance")

if __name__ == "__main__":
    main()
