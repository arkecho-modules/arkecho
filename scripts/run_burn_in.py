# scripts/run_burn_in.py
# ArkEcho Systems © 2025 — burn-in cycles: summarize multiple runs and save CSV

from __future__ import annotations
import os, sys, csv, time
from datetime import datetime, UTC

# path bootstrap
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import report_core  # type: ignore

def run_once():
    return report_core.summarize()

def main(cycles: int = 200, delay_s: float = 0.0):
    rows = []
    for i in range(cycles):
        s = run_once()
        rows.append({
            "i": i + 1,
            "time": s.get("time",""),
            "ok": s.get("ok", 0),
            "modules": s.get("modules", 0),
            "avg_risk": s.get("avg_risk", 0.0),
            "reliability": s.get("reliability", 0.0),
            "stability": s.get("stability", 0.0),
            "coherence": s.get("coherence", 0.0),
        })
        if delay_s > 0:
            time.sleep(delay_s)

    logs_dir = os.path.join(ROOT, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    ts = datetime.now(UTC).isoformat(timespec="seconds").replace(":", "")
    out_csv = os.path.join(logs_dir, f"burn_in_{ts}.csv")

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"Burn-in finished: {len(rows)} cycles → {out_csv}")
    if rows:
        avg = lambda k: sum(float(r[k]) for r in rows) / len(rows)
        print(f" Averages — avg_risk={avg('avg_risk'):.3f} reliability={avg('reliability'):.3f} "
              f"stability={avg('stability'):.3f} coherence={avg('coherence'):.3f}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--cycles", type=int, default=200)
    p.add_argument("--delay", type=float, default=0.0)
    args = p.parse_args()
    main(args.cycles, args.delay)
