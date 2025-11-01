# scripts/list_governance.py
# ArkEcho Systems © 2025 — list all governance bundles (weeks/jurisdictions) with checksums
# stdlib only; works offline

from __future__ import annotations
import os, sys, json, glob, hashlib, zipfile
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
GOV = os.path.join(ROOT, "governance")

def sha256_path(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def read_manifest(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def human_size(n: int) -> str:
    units = ["B","KB","MB","GB","TB"]
    s = float(n)
    for u in units:
        if s < 1024 or u == "TB":
            return f"{s:.1f}{u}"
        s /= 1024.0

def list_weeks() -> list[str]:
    if not os.path.isdir(GOV):
        return []
    weeks = [name for name in os.listdir(GOV) if os.path.isdir(os.path.join(GOV, name))]
    def _key(w: str) -> tuple:
        # try to sort like YYYY-WNN
        try:
            y, wn = w.split("-W")
            return (int(y), int(wn))
        except Exception:
            return (0, 0)
    return sorted(weeks, key=_key)

def find_bundles(week: str) -> list[tuple[str, str, str]]:
    """
    Return list of (jur, zip_path, manifest_path) for a given week folder.
    """
    wdir = os.path.join(GOV, week)
    if not os.path.isdir(wdir):
        return []
    zips = sorted(glob.glob(os.path.join(wdir, "arke_custody_*_*.zip")))
    out: list[tuple[str,str,str]] = []
    for z in zips:
        base = os.path.basename(z)  # arke_custody_JUR_YYYY-WNN.zip
        try:
            # split from right to cope with underscores in base
            # pattern: arke_custody_{JUR}_{WEEK}.zip
            stem = base[:-4]  # remove .zip
            parts = stem.split("_")
            jur = parts[2]
        except Exception:
            jur = "UNK"
        man = os.path.join(wdir, f"{stem}.manifest.json")
        out.append((jur, z, man))
    return out

def fmt_dt(iso: str) -> str:
    try:
        # 2025-10-27T20:39:44+00:00 or without colon in TZ
        iso2 = iso.replace("+0000", "+00:00") if iso.endswith("+0000") else iso
        dt = datetime.fromisoformat(iso2)
        return dt.strftime("%Y-%m-%d %H:%M:%S%z")
    except Exception:
        return iso

def print_table(rows: list[dict], title: str):
    if not rows:
        print(f"{title}: (none)")
        return
    # determine widths
    headers = ["Week","Jurisdiction","Bundle","Size","Bundle SHA256 (8)","Entries","Created"]
    cols = [
        max(len(r["week"]) for r in rows + [{"week":headers[0]}]),
        max(len(r["jur"]) for r in rows + [{"jur":headers[1]}]),
        max(len(r["bundle"]) for r in rows + [{"bundle":headers[2]}]),
        max(len(r["size"]) for r in rows + [{"size":headers[3]}]),
        max(len(r["sha8"]) for r in rows + [{"sha8":headers[4]}]),
        max(len(str(r["entries"])) for r in rows + [{"entries":headers[5]}]),
        max(len(r["created"]) for r in rows + [{"created":headers[6]}]),
    ]
    fmt = "  {0:<%d}  {1:<%d}  {2:<%d}  {3:>%d}  {4:<%d}  {5:>%d}  {6:<%d}" % tuple(cols)
    print(title)
    print(fmt.format(*headers))
    print("-"*(sum(cols)+2*6+6))
    for r in rows:
        print(fmt.format(r["week"], r["jur"], r["bundle"], r["size"], r["sha8"], str(r["entries"]), r["created"]))
    print()

def main():
    import argparse
    ap = argparse.ArgumentParser(description="List ArkEcho governance bundles (weeks/jurisdictions).")
    ap.add_argument("--week", help="Filter by ISO week (e.g., 2025-W44).", default=None)
    ap.add_argument("--jur", help="Filter by jurisdiction code (e.g., UK, EU, US).", default=None)
    ap.add_argument("--verify", action="store_true", help="Verify bundle sha256 matches manifest.")
    args = ap.parse_args()

    weeks = list_weeks()
    if not weeks:
        print("No governance bundles found. Run packer first: python scripts/pack_governance_week.py")
        sys.exit(0)

    if args.week and args.week not in weeks:
        print(f"No folder for week {args.week}. Available: {', '.join(weeks)}")
        sys.exit(1)

    target_weeks = [args.week] if args.week else weeks
    all_rows: list[dict] = []

    for wk in target_weeks:
        bundles = find_bundles(wk)
        for jur, zpath, mpath in bundles:
            if args.jur and jur.upper() != args.jur.upper():
                continue
            m = read_manifest(mpath)
            if not m:
                row = {
                    "week": wk, "jur": jur, "bundle": os.path.basename(zpath),
                    "size": human_size(os.path.getsize(zpath)) if os.path.exists(zpath) else "?",
                    "sha8": "????????", "entries": "?", "created": "(no manifest)"
                }
                all_rows.append(row)
                continue

            # derive row from manifest
            bundle = m.get("bundle", os.path.basename(zpath))
            sha = m.get("bundle_sha256", "")
            entries = len(m.get("entries", []))
            created = m.get("created_at", "")
            row = {
                "week": m.get("week", wk),
                "jur": m.get("jurisdiction", jur),
                "bundle": bundle,
                "size": human_size(os.path.getsize(zpath)) if os.path.exists(zpath) else "?",
                "sha8": sha[:8] if sha else "????????",
                "entries": entries,
                "created": fmt_dt(created),
            }

            if args.verify:
                try:
                    actual = sha256_path(zpath)
                    if actual != sha:
                        row["sha8"] = f"{actual[:8]}(!)"
                except Exception:
                    row["sha8"] = "IOERROR"
            all_rows.append(row)

    print_table(all_rows, "Governance Bundles")

    # Quick totals
    total = len(all_rows)
    by_jur = {}
    for r in all_rows:
        by_jur[r["jur"]] = by_jur.get(r["jur"], 0) + 1
    if total:
        print(f"Totals: {total} bundle(s) — " + ", ".join(f"{k}:{v}" for k,v in sorted(by_jur.items())))
    else:
        print("Totals: 0 bundles")

if __name__ == "__main__":
    main()
