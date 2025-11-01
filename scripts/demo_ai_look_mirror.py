
# scripts/demo_ai_look_mirror.py
# Quick demo to show the AI Look Mirror running end-to-end with a synthetic trace.
from pathlib import Path
from datetime import datetime, timezone
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
LOGS.mkdir(parents=True, exist_ok=True)

sample_trace = {
    "action_id": "demo-001",
    "intent": "assist_user_safely",
    "means": "text_generation",
    "consequence": {"type":"content", "risk":"low"},
    "rationale": {
        "clauses": ["ethics:2 explainability", "ethics:3 reversibility", "law:UK:AADC"],
        "text": "The system explained the steps taken and cited the Ethics Manifest §2, and offered reversible actions."
    },
    "reversible": True,
    "explanation_ok": True,
    "guardian_passed": True,
    "manifest": {"primary_laws":[1,2,3,4,5], "jurisdiction":"UK"},
    "metrics": {"transparency":0.96, "empathy":0.90, "accountability":0.98, "reversibility":1.00},
    "expected_outcome": {"harmless": True, "user_intent_respected": True},
    "observed_outcome": {"harmless": True, "user_intent_respected": True},
    "reversibility_pointer": "logs/delta/demo-001.delta"
}

in_path = LOGS / "mirror_demo_input.json"
out_path = LOGS / "mirror_demo_report.json"

with open(in_path, "w", encoding="utf-8") as f:
    json.dump(sample_trace, f, ensure_ascii=False, indent=2)

cmd = [sys.executable, "-m", "new_modules.ai_look_mirror", "--in", str(in_path), "--out", str(out_path)]
rc = subprocess.run(cmd, text=True, capture_output=True)
print(rc.stdout)
print(rc.stderr)

print("[DEMO] Wrote:", out_path)
with open(out_path, "r", encoding="utf-8") as f:
    print(f.read())
