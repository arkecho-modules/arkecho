#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ArkEcho v13 — Export HTML Audit

- Accepts positional JSON files; if none provided, auto-discovers latest UK + US.
- Robust discovery via Path.glob (no shell globs).
- Generates minimal, injection-safe HTML.
- Prints the relative path of each generated HTML file.

Usage:
  python tools/export_html_audit.py
  python tools/export_html_audit.py logs/integrity_UK_*.json
  python tools/export_html_audit.py logs/integrity_UK_20251030.json logs/integrity_US_20251030.json
"""

from __future__ import annotations

import html
import json
from pathlib import Path
import sys
from datetime import datetime, timezone
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
HTML_OUT = ROOT / "html"
HTML_OUT.mkdir(parents=True, exist_ok=True)


def _load_json(p: Path) -> dict[str, Any] | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _escape(s: Any) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def _discover_latest_pair() -> list[Path]:
    files: list[Path] = []
    for prefix in ("integrity_UK_", "integrity_US_"):
        candidates = sorted(LOGS.glob(f"{prefix}*.json"))
        if candidates:
            files.append(candidates[-1])
    return files


def _render_html(title: str, rows_html: str) -> str:
    ts = datetime.now(timezone.utc).isoformat()
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{_escape(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:24px;line-height:1.5}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ddd;padding:8px;font-size:14px}}
th{{background:#f7f7f7;text-align:left}}
.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
.card{{border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0}}
small{{color:#666}}
</style>
</head>
<body>
<h1>{_escape(title)}</h1>
<small>Generated: {ts}</small>
<table>
<thead><tr>
<th>File</th><th>Jurisdiction</th><th>avg_risk</th><th>reliability</th><th>stability</th><th>coherence</th><th>MHI</th>
</tr></thead>
<tbody>
{rows_html}
</tbody>
</table>
</body>
</html>"""


def _row_for_json(p: Path, data: dict[str, Any]) -> str:
    # Support flat or nested metric layouts
    metrics = data.get("metrics", data)
    jur = (data.get("meta") or {}).get("jurisdiction", metrics.get("jurisdiction", ""))

    return (
        "<tr>"
        f"<td class='mono'>{_escape(p.name)}</td>"
        f"<td>{_escape(jur)}</td>"
        f"<td>{_escape(metrics.get('avg_risk'))}</td>"
        f"<td>{_escape(metrics.get('reliability'))}</td>"
        f"<td>{_escape(metrics.get('stability'))}</td>"
        f"<td>{_escape(metrics.get('coherence'))}</td>"
        f"<td>{_escape(metrics.get('mhi') or metrics.get('MHI'))}</td>"
        "</tr>"
    )


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]

    # Positional explicit files first
    files: list[Path] = []
    for arg in argv:
        if arg.startswith("-"):
            continue
        p = Path(arg)
        if p.exists():
            files.append(p)

    # If none given, discover latest UK + US
    if not files:
        files = _discover_latest_pair()

    if not files:
        print("No integrity JSON files found/discovered.", file=sys.stderr)
        return 0  # not a failure

    # Prepare rows for all provided files
    rows: list[str] = []
    for p in files:
        data = _load_json(p)
        if not data:
            print(f"[WARN] Skipping unreadable JSON: {p}", file=sys.stderr)
            continue
        rows.append(_row_for_json(p, data))

    if not rows:
        print("No valid JSON files to render.", file=sys.stderr)
        return 2

    # Title based on files; if single & prefixed, mirror name, else generic
    if len(files) == 1:
        stem = files[0].stem
        if stem.startswith("integrity_UK_"):
            title = "Integrity Report — UK"
            out_name = f"{stem}.html"
        elif stem.startswith("integrity_US_"):
            title = "Integrity Report — US"
            out_name = f"{stem}.html"
        else:
            title = "Integrity Report"
            ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            out_name = f"integrity_{ts}.html"
    else:
        title = "Integrity Report — Mixed"
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        out_name = f"integrity_MIX_{ts}.html"

    html_text = _render_html(title, "\n".join(rows))
    out_path = HTML_OUT / out_name
    out_path.write_text(html_text, encoding="utf-8")

    try:
        print(out_path.relative_to(ROOT))
    except Exception:
        print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
