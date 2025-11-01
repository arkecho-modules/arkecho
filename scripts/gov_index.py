# scripts/gov_index.py
# ArkEcho Systems © 2025 — Generate a static HTML index for governance bundles

from __future__ import annotations
import os, json, glob, html
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
GOV = os.path.join(ROOT, "governance")
OUT = os.path.join(GOV, "index.html")

HTML = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ArkEcho Governance Index</title>
<style>
 body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu; margin:24px}}
 h1{{margin:0 0 10px}} .muted{{color:#666}}
 .wk{{margin-top:18px}}
 table{{border-collapse:collapse; width:100%; margin-top:8px}}
 th,td{{border-bottom:1px solid #eee; text-align:left; padding:8px}}
 .pill{{display:inline-block; padding:2px 10px; border-radius:999px; font-size:12px; background:#f3f4f6}}
 code{{background:#f3f4f6; padding:2px 6px; border-radius:6px}}
</style></head><body>
<h1>ArkEcho Governance Index</h1>
<div class="muted">Generated: {generated}</div>
{weeks}
</body></html>"""

def human_size(n: int) -> str:
    u = ["B","KB","MB","GB","TB"]; s=float(n)
    for x in u:
        if s<1024 or x=="TB": return f"{s:.1f}{x}"
        s/=1024.0

def list_weeks():
    if not os.path.isdir(GOV): return []
    weeks = [w for w in os.listdir(GOV) if os.path.isdir(os.path.join(GOV,w))]
    def key(w):
        try:
            y, wn = w.split("-W")
            return (int(y), int(wn))
        except: return (0,0)
    return sorted(weeks, key=key, reverse=True)

def rows_for_week(week_dir: str) -> str:
    wdir = os.path.join(GOV, week_dir)
    zips = sorted(glob.glob(os.path.join(wdir, "arke_custody_*_*.zip")))
    lines = []
    lines.append("<table><thead><tr><th>Jurisdiction</th><th>Bundle</th><th>Size</th><th>Entries</th><th>Created</th></tr></thead><tbody>")
    for z in zips:
        base = os.path.basename(z)  # arke_custody_JUR_WEEK.zip
        stem = base[:-4]
        parts = stem.split("_")
        jur = parts[2] if len(parts)>=3 else "UNK"
        man_path = os.path.join(wdir, stem + ".manifest.json")
        size = human_size(os.path.getsize(z)) if os.path.exists(z) else "?"
        created = "—"; entries = "—"
        if os.path.isfile(man_path):
            try:
                man = json.load(open(man_path,"r",encoding="utf-8"))
                created = man.get("created_at","—").replace("+0000","+00:00")
                try:
                    created = datetime.fromisoformat(created).strftime("%Y-%m-%d %H:%M:%S%z")
                except: pass
                entries = str(len(man.get("entries",[])))
            except: pass
        lines.append(
            "<tr>"
            f"<td><span class='pill'>{html.escape(jur)}</span></td>"
            f"<td><a href='{html.escape(week_dir+'/'+base)}'>{html.escape(base)}</a> &nbsp; "
            f"<a href='{html.escape(week_dir+'/'+stem+'.manifest.json')}'>(manifest)</a></td>"
            f"<td>{html.escape(size)}</td>"
            f"<td>{html.escape(entries)}</td>"
            f"<td>{html.escape(created)}</td>"
            "</tr>"
        )
    lines.append("</tbody></table>")
    return "\n".join(lines)

def build():
    sections = []
    for wk in list_weeks():
        sections.append(f"<div class='wk'><h2>{html.escape(wk)}</h2>{rows_for_week(wk)}</div>")
    html_out = HTML.format(generated=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                           weeks="\n".join(sections) if sections else "<p>No bundles yet.</p>")
    os.makedirs(GOV, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"Governance index written → {OUT}")

if __name__ == "__main__":
    build()
