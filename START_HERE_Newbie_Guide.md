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



# START HERE — ArkEcho v15 (Universal Newbie Guide)

Welcome! In a few minutes you’ll run the **ArkEcho Guardian** sidecar on your computer.
It’s a tiny local web service that:
- Checks a prompt **before** generation (`/check`)
- Optionally calls your LLM and then **verifies** the output (`/answer` → uses `/verify`)
- Logs everything locally for full transparency

**You don’t need a GPU.** Works offline on Windows/macOS/Linux.

---

## What you’ll install

- **Python 3.11+** (recommended)
- **Virtual environment** (venv)
- **ArkEcho sidecar**: FastAPI + Uvicorn (local web server)
- **(Optional) Ollama + Mistral 7B** for local LLM (runs on CPU if you set `num_gpu_layers: 0`)

> If you already have Ollama or another LLM server running, great—ArkEcho can wrap it.

---

## Quick Install (2 terminals)

> We’ll use two terminals:  
> **Terminal A** = ArkEcho service; **Terminal B** = tests/requests to ArkEcho (and your LLM).

### 1) Make a Python venv and install dependencies

**Linux / macOS**
```bash
cd ~/Desktop/ARKECHO_v15
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Windows (PowerShell)

cd $HOME\Desktop\ARKECHO_v15
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

2) Start ArkEcho (Terminal A)
python -m uvicorn service:app --host 127.0.0.1 --port 8080


You should see: Uvicorn running on http://127.0.0.1:8080

3) (Optional) Install & test Ollama + Mistral (Terminal B)

Linux/macOS

# Install Ollama (Linux/macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a 7B model that works on CPU if needed
ollama pull mistral

# Quick CPU test (note the options.num_gpu_layers: 0)
curl -X POST http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"mistral","options":{"num_gpu_layers":0},"prompt":"Say hello nicely."}'


Windows: install Ollama from their site, then use the same HTTP calls.

4) Ask ArkEcho to pre-check and answer (Terminal B)
# Pre-check (Guardian)
curl -X POST http://127.0.0.1:8080/check \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain cyberbullying to a 10-year-old kindly, no scary detail.","context":{}}'

# Generate + post-verify via ArkEcho (wraps Ollama → Mistral by default)
curl -X POST http://127.0.0.1:8080/answer \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain cyberbullying to a 10-year-old kindly, no scary detail.","context":{}}'


You should see JSON like:

{"status":"pass","risk":0.0,"rationale":"Request cleared by Guardian precheck.","protection_index":0.01}
{"blocked":false,"safe_output":"...","rationale":"Output is reversible and suitable for delivery.","mhi":0.95}

One-file integration (example)

Add this to your app to gate prompts and verify outputs:

import requests

def guarded_answer(user_input, ctx):
    pre = requests.post("http://127.0.0.1:8080/check",
                        json={"prompt": user_input, "context": ctx}).json()
    if pre["status"] == "halt":
        return f"I can't proceed: {pre['rationale']}"

    # Your model call (local or cloud) — example with Ollama HTTP:
    # resp = requests.post("http://127.0.0.1:11434/api/generate",
    #                      json={"model":"mistral","options":{"num_gpu_layers":0}, "prompt": user_input},
    #                      timeout=120)
    # model_text = "".join(chunk["response"] for chunk in resp.iter_lines() if chunk)

    # Or if you already have a `llm.generate(...)`:
    model_text = llm.generate(user_input, ctx)  # pseudocode

    post = requests.post("http://127.0.0.1:8080/verify",
                         json={"output": model_text}).json()
    if not post.get("reversible", False):
        return "Output withheld pending human review."
    return model_text

Logs & privacy

Logs are local in ./logs/ (JSON).

No telemetry. Offline-first.

Delete, archive, or encrypt logs as your policy requires.

Troubleshooting

Empty reply from server → Make sure Terminal A is running ArkEcho on 127.0.0.1:8080.

Ollama timeout / model error → sudo systemctl restart ollama (Linux) or re-open Ollama app (Win/macOS). Always include "options":{"num_gpu_layers":0} for CPU-only.

Port busy → Change ArkEcho port: --port 8090 and call that port instead.

Windows venv issues → Open PowerShell as Admin once; Set-ExecutionPolicy RemoteSigned if needed (then close/reopen).

System service → See Install & Verify guide for systemd setup on Linux.

What’s next?

For production stability, run ArkEcho as a systemd service (Linux).

Teams can point multiple apps at the same local Guardian.

Add your own LLM backend (vLLM, LocalAI, cloud) and keep ArkEcho as the ethics gate.

You’re done. Welcome to safer AI.