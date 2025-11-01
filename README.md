# ArkEcho v15 — Quick Entry Points  
*“Because these go to 11.”* 🎸  

ArkEcho gives **solo users and large teams** the same clear entry flow for setup and verification.  
Everything begins with six simple actions:

1. **deps** — install dependencies  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   python -m pip install -r requirements.txt
run — start the Guardian service

bash
Copy code
python -m uvicorn service:app --host 127.0.0.1 --port 8080
check — pre-execution ethics gate

bash
Copy code
curl -s -X POST http://127.0.0.1:8080/check \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain cyberbullying to a 10-year-old kindly, no scary detail."}'
answer — end-to-end verified output

bash
Copy code
curl -s -X POST http://127.0.0.1:8080/answer \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain cyberbullying to a 10-year-old kindly, no scary detail."}'
proof — generate attestation & chain of custody

bash
Copy code
python3 verify_chain_of_custody_v2.py
service-* — run permanently as a Linux system service

bash
Copy code
sudo systemctl enable --now arkecho-guardian
systemctl status arkecho-guardian
These six commands cover the entire operational lifecycle:
local install → safe execution → verification → attestation → long-term service mode.

They are identical across Windows, macOS, and Linux, ensuring every ArkEcho instance is reproducible, auditable, and ready for independent verification.



# ArkEcho v15 — Universal User Guide (All Editions)

ArkEcho is a **moral safety sidecar** for AI systems: offline-first, deterministic, reversible, and fully auditable. It runs as a lightweight HTTP service on your machine and can wrap any LLM backend (Ollama, vLLM, cloud, etc.).

**What you get**
- ✅ Guardian pre-check (`/check`) and post-verification (`/verify`)
- ✅ Optional convenience generation (`/answer`) that calls your LLM
- ✅ Human-readable rationale + **MHI** (Moral Health Index)
- ✅ Immutable logs (Moral Integrity Ledger) stored locally
- ✅ Works entirely offline after first install

## Quick Start (works on laptops)

> Two-terminal model:
> - **Terminal A** runs ArkEcho (the sidecar API).
> - **Terminal B** runs commands/tests or your LLM server.

### 1) Create a virtual environment and install deps
**Linux / macOS**
```bash
cd ~/Desktop/ARKECHO_v15   # or your folder
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Windows (PowerShell)

powershell
Copy code
cd $HOME\Desktop\ARKECHO_v15
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
2) Start the ArkEcho service (Terminal A)
bash
Copy code
python -m uvicorn service:app --host 127.0.0.1 --port 8080
Expected: Uvicorn running on http://127.0.0.1:8080

3) (Optional) Run a local LLM with Ollama (Terminal B)
Linux/macOS

bash
Copy code
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral
# CPU-only (works even on low/zero VRAM):
curl -X POST http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"mistral","options":{"num_gpu_layers":0},"prompt":"Say hello nicely."}'
Windows users can install Ollama from their website and keep the same HTTP calls.

4) Ask ArkEcho to guard + answer
bash
Copy code
# Pre-check (Guardian)
curl -X POST http://127.0.0.1:8080/check \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain cyberbullying to a 10-year-old kindly, no scary detail.","context":{}}'

# Generate + post-verify (sidecar calls Ollama → Mistral)
curl -X POST http://127.0.0.1:8080/answer \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain cyberbullying to a 10-year-old kindly, no scary detail.","context":{}}'
Expected JSON (shape):

json
Copy code
{"status":"pass","risk":0.0,"rationale":"Request cleared by Guardian precheck.","protection_index":0.01}
{"blocked":false,"safe_output":"...","rationale":"Output is reversible and suitable for delivery.","mhi":0.95}
5) Where are the logs?
All decisions are written to ./logs/ as JSON (and, in some editions, HTML summaries). Nothing is sent to the cloud.

6) Troubleshooting
Empty reply from server → ensure Terminal A is running on 127.0.0.1:8080.

Ollama timeout / 11434 error → sudo systemctl restart ollama (Linux) or relaunch Ollama; test with {"num_gpu_layers":0}.

Address already in use → change port: --port 8090.

Windows activation issues → run PowerShell as Administrator the first time.

7) Programmatic integration (any stack)
python
Copy code
# pre-check
pre = requests.post("http://127.0.0.1:8080/check",
                    json={"prompt": user_input, "context": ctx}).json()
if pre["status"] == "halt":
    return f"I can't proceed: {pre['rationale']}"

# your generation step (local server, cloud, etc.)
response = llm.generate(user_input, ctx)

# post-verify
post = requests.post("http://127.0.0.1:8080/verify",
                     json={"output": response}).json()
if not post.get("reversible", False):
    return "Output withheld pending human review."
return response
Optional: run as a Linux service (systemd)
bash
Copy code
sudo tee /etc/systemd/system/arkecho-guardian.service >/dev/null <<'EOF'
[Unit]
Description=ArkEcho Guardian Sidecar
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=arc
Group=arc
WorkingDirectory=/home/arc/Desktop/ARKECHO_v15
Environment="PATH=/home/arc/Desktop/ARKECHO_v15/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="OLLAMA_HOST=127.0.0.1"
ExecStart=/home/arc/Desktop/ARKECHO_v15/venv/bin/python -m uvicorn service:app --host 127.0.0.1 --port 8080
Restart=on-failure
RestartSec=2
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now arkecho-guardian
systemctl status arkecho-guardian --no-pager
What’s in this folder (typical)
service.py — FastAPI sidecar (HTTP endpoints)

guardian_wrapper.py — tiny example client (pre→gen→verify)

requirements.txt — pinned, reproducible deps

logs/ — local immutable decision/audit logs

Design ethos: transparency, reversibility, accountability, empathy. No telemetry. Offline-first.