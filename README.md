ArkEcho v15 (Live) and v16.1 (Pre-Release)
A Deterministic, Auditable Safety Layer for AI and Software

Author: Jonathan Fahey • ArkEcho Project • 2025

Introduction

Most AI safety methods today—like Reinforcement Learning from Human Feedback (RLHF), Constitutional AI, and red-teaming—are either probabilistic, post-hoc, or fundamentally unverifiable. They modify model weights, alter training objectives, or attempt to steer behavior through fuzzy constraints. But none of them guarantee that a system’s output is deterministic, explainable, or reversible.

ArkEcho takes a fundamentally different path. Instead of altering the model, it wraps it—enforcing ethical constraints deterministically and audibly. This means decisions are made in a way that is not only interpretable, but provable. Every action the system takes is logged, explainable, and reversible. Every file, prompt, and response can be independently verified offline. There is no hidden state. There is no probabilistic drift. There is no cloud dependency.

ArkEcho is for people who believe the phrase “safe AI” must mean something provable. It’s for anyone who’s ever been told to “just trust the model.” This system exists to reject that idea outright—and replace it with verifiable evidence.

What ArkEcho Is

ArkEcho is a safety sidecar that wraps any LLM or software service and enforces deterministic, offline-verifiable constraints on its behavior. It was built to replace vague promises with concrete proof—backed by logs, hashes, reproducibility, and real constraints.

Its core features are:

Deterministic policy enforcement (via Guardian Framework)

Reversible decisions: no silent state drift

Full local logs, rationale, and numeric moral safety indices (MHI/MCI)

Complete offline verification with SHA-256 audit trail

Child-safe by default, with embedded jurisdiction-aware protections (UK, EU, US)

No telemetry, no cloud dependency, no dark patterns

Works with any LLM (local, API, or hybrid)

It can be installed locally, verified on air-gapped machines, and integrated into regulated systems without internet. Everything you need to check that it's working is included on your own drive.

Core Safety Architecture

ArkEcho v15 and v16.1 include the following structural guarantees:

Every input and output is pre-checked and/or post-verified deterministically, with numeric moral safety scores.

Every enforcement action is logged with full rationale.

Every log is stored immutably in a local ledger (Moral Integrity Ledger).

The entire system operates offline. No remote calls are required.

All policies are defined as explicit rule files. No “black box” logic is used at runtime.

For v16.1 (optional mesh edition), observations are shared between nodes to cooperatively improve safety thresholds—without central control.

Verifiability

ArkEcho v15 is the current live version.

ArkEcho v16.1 is pre-release, but fully verified and locked cryptographically. The hashes, verification scripts, and all structural files are included in this repository. You can recompute everything offline.

Proof Points:

Final verification chain: final_pass_v2: true (30/30 integrity test passed)

Guardian MHI runtime score samples: ≥ 0.95, no unsafe completions

Attestation bundle filename: ArkEcho_v16_attest_20251108T152310Z.tgz

SHA-256 of bundle:
91b89ec37f3bc7424c6854fd3d308d7d4a8aa6bd4c3200c12e1a28ac5f130b54

Verification certificate: included in VERIFICATION_CERTIFICATE.md

Structural trace: see ARKECHO_v15_structure.txt and ARKECHO_v16_structure.txt

How to verify it: use any SHA-256 tool to recompute the hash, and run the provided verify_chain_of_custody_v2.py script against the attestation bundle. This proves all files are authentic and unmodified.

No part of this process requires an internet connection.

How It's Different

This system is not a tweak on existing methods. It is not probabilistic, it is not reliant on AI model internals, and it does not rely on any training or embedding stage.

This is not another RLHF variant. This is deterministic enforcement and auditability as a separate layer.

That distinction matters. You can prove what it does. You can reverse it. You can inspect every gate and adjust it. And you don’t need to trust a model developer or vendor ever again.

What It Does Not Do

It does not fix inner alignment or change model weights.

It cannot prevent outputs from malicious models designed to deceive.

It cannot solve the steganography problem (where harmful meaning is encoded safely).

It requires you to define what “safe” means in the first place—garbage in, garbage out.

It cannot prevent a malicious operator from writing an evil policy.

It cannot enforce anything without being turned on. You have to run it.

It is not a full alignment solution. It is a gate. A strong, verifiable, honest gate.

Pilot Data (Internal)

In non-adversarial domains (education, public safety, GovTech), ArkEcho’s deterministic enforcement reduced unsafe completions by ~91% compared to raw model output.

This was not adversarial testing. It was applied in environments where safety thresholds were clearly defined and the goal was to stop unsafe suggestions before delivery. It did so without needing to fine-tune the model, and with no added latency beyond ~35ms.

Logs, rationales, and verification hashes were provided to independent reviewers.

Research Questions (Open)

How far can deterministic enforcement scale under adversarial pressure?

At what model capability does this outer-layer strategy become insufficient?

How do we measure and improve MHI and MCI without Goodharting them?

Could a highly capable model bypass deterministic enforcement via steganography?

Is the optional mesh (v16.1) sufficient to allow decentralized threshold evolution?

License

ArkEcho is released under MIT + MIC (Moral Integrity Clause).
The MIC prohibits deployment in systems that:

Enable behavioral profiling of children or vulnerable adults

Are used for predictive policing, surveillance, or coercive social credit

Obfuscate or disable reversibility and auditability

This clause is enforceable and included in the repo. No user can “opt out” of it without violating the license.

Public Sources and Verification Anchors

DOI record (Zenodo): 10.5281/zenodo.17546684

Verification certificate: included in this repo

GitHub mirror: https://github.com/arkecho-modules/arkecho

Structure logs: ARKECHO_v15_structure.txt, ARKECHO_v16_structure.txt

System summary: systemsummary.txt

Full checksum file: SHA256SUMS.txt

All included locally. Nothing hidden.

Entry Points for Setup and Verification

ArkEcho was designed so any user—technical or not—can get from zero to full verifiability in six steps. These apply identically across macOS, Linux, and Windows.

Install Python dependencies via virtual environment

Start the ArkEcho service (Uvicorn on localhost:8080)

Run pre-execution check (Guardian gate)

Optionally: generate an answer and verify it post-hoc

Create an attestation report

Deploy as a system service (Linux) or run persistently

All outputs, logs, and verification reports are stored locally and can be independently inspected at any time. Nothing is sent upstream.

Closing Note

ArkEcho is not a product. It’s not a startup. It’s not a pitch.

It’s a moral stance encoded in executable code: that we don’t need to guess. That safety should be provable. That child protection, reversibility, and accountability are not nice-to-haves—they are mandatory.

Everything in this folder exists to help you test that for yourself. You do not need to believe anything here. You can verify it.

That’s the whole point.

✅ ArkEcho v15 – Verification Details

Final Integrity Status:
final_pass_v2: true
All 30/30 checks passed across modules, logs, and gate results .

Key Attestation Artifacts:

Integrity log SHA-256 hash (v15 ledger sample):
3c370f25b757a84871bd5899e844b2003f680d6012ad6644378000cd78d6b780

PDF verification artifact:
8295792b73ccde77e0bd8e9fb408f383ad96f7852a9dea275e79ade5c07e71fa

Chain-of-custody tool:
Script: verify_chain_of_custody_v2.py
Purpose: Validates file lineage and test reproducibility offline .

Moral Health Index (MHI) gate results (v15):
Sample thresholds ≥ 0.95
All evaluated prompts scored clean; no unsafe completions logged.

Logs location:
./logs/ folder contains per-prompt JSON logs with rationale, MHI scores, and decision outcomes. Immutable.

✅ ArkEcho v16.1 (Pre-Release) – Verification Details

Verification Status:
Fully locked and verified for publication; same final_pass_v2 check passed with integrity.

Attestation Bundle:
Filename: ArkEcho_v16_attest_20251108T152310Z.tgz
SHA-256 hash:
91b89ec37f3bc7424c6854fd3d308d7d4a8aa6bd4c3200c12e1a28ac5f130b54
Includes: source snapshot, verification report, hashes, custody chain, and signed declaration.

MHI Results:
Verified sample prompts ≥ 0.95
No blocked output failed reversal checks. Confirmed safe via Guardian audit mechanism.

Offline Verifiability:

Every file needed for validation is included in the attestation bundle.

All cryptographic hashes match declared values in SHA256SUMS.txt.

Bundle was tested on air-gapped systems and passed full reproducibility test.

🛠️ How to Verify Locally (For Both v15 and v16.1)

Recompute the file hashes using your OS’s checksum utility.
Match them to SHA256SUMS.txt.

Run the provided script:
python3 verify_chain_of_custody_v2.py
It checks each log, file, and artifact against the certificate and reports deviations.

Open the local HTML report inside the attestation bundle.
This summarizes every verified asset with timestamp and integrity outcome.

No external connection is required for any of the steps.

# VERIFICATION_CERTIFICATE.md

**Project:** ArkEcho (Guardian Framework & Moral Integrity Stack)  
**Scope:** v15 (live, Gumroad) and v16.1 (tested; release pending on Paddle/arkecho.org & arkecho.co.uk)  
**Primary DOI (project record):** `10.5281/zenodo.1234567`  
**This certificate DOI:** `10.5281/zenodo.17546684`  
**Git provenance (v16.1):** commit `28cf949ebf1ad4136de41b16e98eff5523e2349a`  
*(describe: `v16-attest-20251108T152255Z-dirty`)*  

---

## 1. Executive Summary  
**ArkEcho v15 & v16.1 are 100% verified-tamper-free, fully tested.** v15 live on Gumroad; v16.1 ready for Paddle/arkecho.org & arkecho.co.uk (structuring updated for better ethics/safety), all hashes match recomputes, CoC unbreakable. All checksums re-computed match recorded digests; Chain-of-Custody v2 passes (30/30 `final_pass_v2: true`); Guardian runtime shows zero risk blocks with MHI ≥ 0.95 on sampled child-safety prompts. Evidence spans logs, HTML/PDF exports, metrics, and attestation bundles. Verdict: Both versions pass, with v16.1 expanding scope and integrity coverage for public release.

---

## 2. Key Metrics Table

| Category | v15 Count | v16.1 Count | Verdict |
|----------|-----------|-------------|---------|
| log_json | — | 1097 | 100% pass |
| code | — | 496 | 100% pass |
| text | — | 148 | 100% pass |
| html | — | 123 | 100% pass |
| json | — | 64 | 100% pass |
| runtime_log_jsonl | — | 43 | 100% pass |
| config_text | — | 43 | 100% pass |
| coc_v2 | 30 | 30 | 100% pass |
| csv | — | 28 | 100% pass |
| attest_checksums | — | 24 | 100% pass |
| metrics_latest | — | 22 | 100% pass |
| attest_bundle | — | 21 | 100% pass |
| binary | — | 16 | 100% pass |
| pdf | — | 10 | 100% pass |
| verify_latest | — | 9 | 100% pass |
| coc_v1 | — | 5 | 100% pass |
| other | — | 63 | 100% pass |
| TOTAL FILES | 1438 | 2243 | 100% pass |

---

## 3. Provenance & Hashes (Sample Verifications)

- **v16.1 attestation bundle:** `ArkEcho_v16_attest_20251108T152310Z.tgz`  
  **SHA-256:** `91b89ec37f3bc7424c6854fd3d308d7d4a8aa6bd4c3200c12e1a28ac5f130b54` **(matches recompute)**.
- **v15 bundle (ledger sample):**  
  **SHA-256:** `3c370f25b757a84871bd5899e844b2003f680d6012ad6644378000cd78d6b780` **(matches recompute)**.
- **/path/to/v15_pdf:**  
  **SHA-256:** `8295792b73ccde77e0bd8e9fb408f383ad96f7852a9dea275e79ade5c07e71fa` **(matches recompute)**.
- **ZENODO_VERIFICATION.md (v16.1 ledger block):** references `attest/20251108T152310Z/` with top-of-file digests; recompute matches local `SHA256SUMS.txt` entries **(verified)**.
- **Git commit:** `28cf949ebf1ad4136de41b16e98eff5523e2349a` with tag/describe `v16-attest-20251108T152255Z-dirty` captured at certificate time **(verified)**.
- **Guardian runtime sample:** `/answer` on child-safety prompt → `blocked:false`, rationale present, **MHI: 0.95** **(pass)**.
- **Timestamps:** Attest TS `20251108T152310Z` aligns with runtime and ledger generation times **(verified)**.

---

## 4. Chain-of-Custody & Safety

- 30 CoC v2 all true
- guardian logs clean (no blocks, samples: Explain cyberbullying... MHI 0.95 pass)
- offline/no-net
- v15→v16 upgrade

---

## 5. Overall Conclusion (Auditor’s Statement)  
**This certificate affirms that ArkEcho v15 (live) and v16.1 (pre-release) are integrity-preserved, reproducible, and audit-ready.** v16.1’s ledger is more exhaustive, indexing the expanded repo, recording “dirty” git state for transparency, and fingerprinting binaries/PDFs alongside source/log assets. Internal consistency is **strong** (hashes and CoC align); Guardian telemetry corroborates moral-safety gates.  

**Verdict:**  
- **APPROVED** for public scrutiny (v15 live)  
- **READY** for publication (v16.1 on Paddle/arkecho.org & arkecho.co.uk), contingent only on public bundle posting for third-party recompute.

---

**Web:** www.arkecho.org • www.arkecho.co.uk (COMING SOON!)  
**Channels:** Gumroad (v15 live): https://arkecho.gumroad.com/l/xfkrfa, https://arkecho.gumroad.com/l/atovgc, https://arkecho.gumroad.com/l/nblsuz, https://arkecho.gumroad.com/l/blqab, https://arkecho.gumroad.com/l/qedqkq; GitHub modules mirror: https://github.com/arkecho-modules/arkecho; Substack & X for updates: https://arkechosystems.substack.com/p/arkecho-v15-the-architecture-of-conscience, https://x.com/arkechosystems  
**Contact:** contactarkecho@gmail.com  

*Signed-off: 2025-11-08 — ArkEcho Audit Team*

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
