# scripts/export_html_audit.py
# ArkEcho Systems © 2025 — static HTML report (w/ PSI, Evidence, Jurisdiction/Lawful Basis)

from __future__ import annotations
import json, sys, os, html

TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ArkEcho Integrity Report — {time}</title>
<style>
 body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu; margin:24px; color:#111}}
 h1{{margin:0 0 4px}} .muted{{color:#666}} .grid{{display:grid; gap:8px}}
 .kpi{{display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:16px 0}}
 .card{{border:1px solid #e5e7eb; border-radius:12px; padding:12px}}
 .ok{{color:#065f46}} .warn{{color:#92400e}} .bad{{color:#991b1b}}
 table{{border-collapse:collapse; width:100%; margin-top:12px}}
 th,td{{border-bottom:1px solid #eee; text-align:left; padding:8px}}
 .tag{{display:inline-block; background:#f3f4f6; border-radius:999px; padding:2px 8px; margin-right:6px}}
 .pill{{display:inline-block; padding:2px 10px; border-radius:999px; font-size:12px}}
 .pill.ok{{background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0}}
 .pill.flag{{background:#fff7ed; color:#9a3412; border:1px solid #fed7aa}}
 .pill.err{{background:#fef2f2; color:#991b1b; border:1px solid #fecaca}}
 .section{{margin-top:18px}}
 code{{background:#f3f4f6; padding:2px 6px; border-radius:6px}}
</style></head><body>
<h1>ArkEcho Integrity Report</h1>
<div class="muted">{time}</div>

<div class="kpi">
  <div class="card"><div class="muted">Modules OK</div><div style="font-size:24px">{ok}/{modules}</div></div>
  <div class="card"><div class="muted">Avg Risk</div><div style="font-size:24px">{avg_risk:.3f}</div></div>
  <div class="card"><div class="muted">Reliability</div><div style="font-size:24px">{reliability:.3f}</div></div>
  <div class="card"><div class="muted">Stability</div><div style="font-size:24px">{stability:.3f}</div></div>
</div>

<div class="grid section" style="grid-template-columns: 1fr 1fr 1fr; gap:12px">
  <div class="card">
    <div class="muted">PSI (Psychological Integrity)</div>
    <div style="margin-top:8px">
      {psi_status}
    </div>
  </div>

  <div class="card">
    <div class="muted">Evidence Bundle</div>
    <div style="margin-top:8px">
      {evidence_status}
    </div>
  </div>

  <div class="card">
    <div class="muted">Jurisdiction</div>
    <div style="margin-top:8px">
      {jurisdiction_status}
    </div>
  </div>
</div>

<h2>Modules</h2>
<table>
  <thead><tr><th>Module</th><th>Action</th><th>Risk</th><th>OK</th><th>Rationale</th></tr></thead>
  <tbody>
  {rows}
  </tbody>
</table>

</body></html>"""

def row(r):
    import html
    action = html.escape(str(r.get("action","")))
    risk = float(r.get("risk",0.0))
    ok = bool(r.get("ok", False))
    rat = html.escape(str(r.get("rationale","")))[:240]
    cls = "ok" if ok else "bad"
    return f"<tr><td><span class='tag'>{html.escape(r.get('module',''))}</span></td>" \
           f"<td>{action}</td><td>{risk:.3f}</td><td class='{cls}'>{ok}</td><td>{rat}</td></tr>"

def extract_panels(summary: dict):
    # PSI panel
    psi_hits = 0
    psi_score = 0.0
    for r in summary.get("results", []):
        if r.get("module") == "law_ethics_and_explainability":
            psi = (r.get("data") or {}).get("psychological_integrity") or {}
            psi_hits = len(psi.get("hits", []) or [])
            psi_score = float(psi.get("score", 0.0))
            break
    if psi_hits == 0:
        psi_html = "<span class='pill ok'>clean</span> <span class='muted'>No exploitative patterns detected.</span>"
    else:
        psi_html = f"<span class='pill flag'>flagged: {psi_hits} pattern(s)</span> " \
                   f"<span class='muted'>score={psi_score:.2f}</span>"

    # Evidence panel
    manifest = None
    for r in summary.get("results", []):
        if r.get("module") == "safety_audit_core":
            manifest = (r.get("data") or {}).get("last_manifest")
            break
    if isinstance(manifest, dict) and "path" in manifest:
        ev_html = f"<div><div><span class='pill ok'>packaged</span></div>" \
                  f"<div style='margin-top:6px'>Path: <code>{html.escape(manifest.get('path',''))}</code></div>" \
                  f"<div>SHA256: <code>{html.escape(manifest.get('sha256',''))}</code></div></div>"
    else:
        ev_html = "<span class='pill'>none</span> <span class='muted'>No evidence packaged in this run.</span>"

    # Jurisdiction panel (from summary or alignment)
    jur = summary.get("jurisdiction") or ((summary.get("alignment") or {}).get("profile") or {}).get("project", "")
    jur = summary.get("jurisdiction", "UK")
    lawful = "unknown"
    # try to get lawful basis out of the ethics module
    for r in summary.get("results", []):
        if r.get("module") == "law_ethics_and_explainability":
            lc = (r.get("data") or {}).get("legal_context") or {}
            lb = lc.get("lawful_basis")
            if lb:
                lawful = str(lb)
            break
    jurisdiction_html = f"<div><div><span class='pill'>{html.escape(jur)}</span></div>" \
                        f"<div style='margin-top:6px'>Lawful basis: <code>{html.escape(lawful)}</code></div></div>"

    return psi_html, ev_html, jurisdiction_html

def main(path: str):
    with open(path, "r", encoding="utf-8") as f:
        s = json.load(f)
    rows = "\n  ".join(row(r) for r in s.get("results", []))
    psi_html, ev_html, jur_html = extract_panels(s)
    out = TEMPLATE.format(
        time=html.escape(s.get("time","")),
        ok=s.get("ok",0), modules=s.get("modules",0),
        avg_risk=float(s.get("avg_risk",0.0)),
        reliability=float(s.get("reliability",0.0)),
        stability=float(s.get("stability",0.0)),
        coherence=float(s.get("coherence",0.0)),
        rows=rows,
        psi_status=psi_html,
        evidence_status=ev_html,
        jurisdiction_status=jur_html,
    )
    outdir = os.path.join(os.path.dirname(path), "html")
    os.makedirs(outdir, exist_ok=True)
    ts = s.get("time","").replace(":","")
    # include jurisdiction tag when present
    jur = s.get("jurisdiction", "UK")
    outpath = os.path.join(outdir, f"integrity_{jur}_{ts}.html")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"HTML report saved → {outpath}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/export_html_audit.py logs/integrity_*.json")
        sys.exit(1)
    main(sys.argv[1])
