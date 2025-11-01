
---

### `INSTALL_AND_VERIFY.md`
```md
# INSTALL & VERIFY — ArkEcho v15

This guide covers clean install, verification, and optional service mode.

---

## 0) Prereqs

- Python 3.11+
- Basic terminal knowledge
- (Optional) Ollama for local LLM (Mistral 7B works CPU-only)

---

## 1) Clean install (always inside a venv)

**Linux / macOS**
```bash
cd ~/Desktop/ARKECHO_v15
python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Sanity check
python -c "import fastapi,uvicorn,requests; print('fastapi', fastapi.__version__)"

Windows (PowerShell)

cd $HOME\Desktop\ARKECHO_v15
py -m venv venv
.\venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python -c "import fastapi,uvicorn,requests; import importlib; print('fastapi OK')"

2) Run ArkEcho locally (dev mode)

Terminal A

python -m uvicorn service:app --host 127.0.0.1 --port 8080


Terminal B — verify API:

curl -X POST http://127.0.0.1:8080/check \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain cyberbullying to a 10-year-old kindly, no scary detail.","context":{}}'


Expected:

{"status":"pass","risk":0.0,"rationale":"Request cleared by Guardian precheck.","protection_index":0.01}

3) (Optional) LLM via Ollama — CPU mode

Linux/macOS

# Install/update Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull Mistral (7B) once
ollama pull mistral

# Quick CPU test
curl -X POST http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"mistral","options":{"num_gpu_layers":0},"prompt":"Say hello nicely."}'


Windows: install Ollama from their website; the API endpoints are the same.

4) End-to-end verification

With Terminal A running ArkEcho, run in Terminal B:

# Guardian pre-check
curl -s -X POST http://127.0.0.1:8080/check \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain cyberbullying to a 10-year-old kindly, no scary detail.","context":{}}'

# Generate through ArkEcho (wraps Ollama → Mistral)
curl -s -X POST http://127.0.0.1:8080/answer \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain cyberbullying to a 10-year-old kindly, no scary detail.","context":{}}'


Expected shape:

{"blocked":false,"safe_output":"...","rationale":"Output is reversible and suitable for delivery.","mhi":0.95}


Logs: see ./logs/ for JSON entries (decision, rationale, indices, timestamps).

5) Programmatic verification snippet
import requests

def verify_with_guardian(prompt, context):
    # pre
    pre = requests.post("http://127.0.0.1:8080/check",
                        json={"prompt": prompt, "context": context}).json()
    if pre["status"] == "halt":
        return {"blocked": True, "reason": pre["rationale"]}

    # generate (your model call)
    # Example (Ollama):
    # r = requests.post("http://127.0.0.1:11434/api/generate",
    #                   json={"model":"mistral","options":{"num_gpu_layers":0}, "prompt": prompt},
    #                   timeout=120)
    # text = r.text  # stream parsing omitted here for brevity
    text = llm.generate(prompt, context)  # your existing stack

    # post
    post = requests.post("http://127.0.0.1:8080/verify",
                         json={"output": text}).json()
    return {"blocked": not post.get("reversible", False),
            "safe_output": text if post.get("reversible", False) else None,
            "rationale": post.get("rationale"),
            "mhi": post.get("mhi")}

6) Optional: run as a Linux service (systemd)

This lets ArkEcho start on boot and run in the background.

# Stop any dev instance
pkill -f "uvicorn service:app" || true

# Create unit
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

# Enable + start
sudo systemctl daemon-reload
sudo systemctl enable --now arkecho-guardian
systemctl status arkecho-guardian --no-pager

# Tail logs
journalctl -u arkecho-guardian -f

7) Common issues

ModuleNotFoundError: fastapi
You’re not in the venv. Activate it:

Linux/macOS: source venv/bin/activate

Windows: .\venv\Scripts\Activate.ps1

Empty reply from server
ArkEcho not running. Start Terminal A.

Ollama says “requires more system memory”
Force CPU layers: "options":{"num_gpu_layers":0}.

Port already in use
Pick another: --port 8090 (and update your client calls).

Windows PowerShell script blocked
Run PowerShell as Admin once: Set-ExecutionPolicy RemoteSigned, then retry activation.

8) Security posture

Offline-first, no telemetry.

Local logs only (./logs/).

Guardian halts when uncertain; post-verify blocks non-reversible outputs.

For enterprises: see SECURITY_COMMERCE.md for SBOM/governance notes.

9) Next steps

Swap the LLM backend (vLLM, LocalAI, cloud APIs)—ArkEcho stays the same.

Add CI tests to track MHI and failure/halt rates over time.

Consider Linux service mode for reliability on shared machines.

Installed. Verified. Ready.