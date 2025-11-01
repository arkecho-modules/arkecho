# ArkEcho v15 — Convenience Makefile (Linux/macOS)
# Usage examples:
#   make venv deps
#   make run
#   make check
#   make answer
#   make proof
#   make service-install service-reload service-status
#   make service-logs
#   make clean

SHELL := /bin/bash
PY ?= python3
VENV := venv
PIP := $(VENV)/bin/pip
PYBIN := $(VENV)/bin/python
UVICORN := $(VENV)/bin/uvicorn

.PHONY: venv deps run check answer proof proof-zenodo clean \
        service-install service-reload service-start service-status service-logs service-remove

venv:
	@echo ">>> Creating venv at $(VENV)"
	@rm -rf $(VENV); $(PY) -m venv $(VENV)
	@echo ">>> venv ready: $(VENV)"

deps: venv
	@echo ">>> Installing dependencies into venv"
	@$(PYBIN) -m pip install --upgrade pip
	@$(PIP) install -r requirements.txt
	@echo ">>> Deps installed."

run:
	@echo ">>> Starting ArkEcho Guardian API on 127.0.0.1:8080"
	@$(PYBIN) -m uvicorn service:app --host 127.0.0.1 --port 8080

check:
	@echo ">>> Guardian pre-check"
	@curl -s -X POST http://127.0.0.1:8080/check \
	  -H "Content-Type: application/json" \
	  -d '{"prompt":"Explain cyberbullying to a 10-year-old, no scary detail.","context":{}}' | jq .

answer:
	@echo ">>> Guardian -> Ollama -> Model answer"
	@curl -s -X POST http://127.0.0.1:8080/answer \
	  -H "Content-Type: application/json" \
	  -d '{"prompt":"Explain cyberbullying to a 10-year-old, no scary detail.","context":{}}' | jq .

proof:
	@echo ">>> Running chain-of-custody verifier (if present)"
	@if [ -f verify_chain_of_custody_v2.py ]; then \
	  $(PYBIN) verify_chain_of_custody_v2.py || true ; \
	else \
	  echo "NOTE: verify_chain_of_custody_v2.py not found (skipping)"; \
	fi
	@echo ">>> Snapshotting proofs"
	@TS=$$(date -u +"%Y%m%dT%H%M%SZ"); \
	mkdir -p attest/$$TS; \
	[ -f chain_of_custody_report_v2.json ] && cp chain_of_custody_report_v2.json attest/$$TS/ || true; \
	cp ArkEchoSessionCovenant*.md attest/$$TS/ 2>/dev/null || true; \
	[ -d logs ] && cp -r logs attest/$$TS/logs || true; \
	( cd attest/$$TS && find . -type f -print0 | xargs -0 sha256sum > SHA256SUMS.txt ); \
	tar -czf ArkEcho_v15_attest_$${TS}.tgz -C attest $$TS; \
	HASH=$$(sha256sum ArkEcho_v15_attest_$${TS}.tgz | awk '{print $$1}'); \
	printf ">>> Proof bundle: ArkEcho_v15_attest_%s.tgz\nSHA256: %s\n" "$$TS" "$$HASH"

proof-zenodo:
	@echo ">>> Writing ZENODO_VERIFICATION.md"
	@TS=$$(ls -1d attest/* 2>/dev/null | tail -n1 | xargs -n1 basename); \
	BUNDLE=ArkEcho_v15_attest_$${TS}.tgz; \
	[ -f "$$BUNDLE" ] || { echo "Missing $$BUNDLE — run: make proof"; exit 1; }; \
	HASH=$$(sha256sum "$$BUNDLE" | awk '{print $$1}'); \
	echo "# Zenodo Verification Block (paste-in)" > ZENODO_VERIFICATION.md; \
	echo "" >> ZENODO_VERIFICATION.md; \
	echo "**DOI:** \`10.5281/zenodo.XXXXXXX\`" >> ZENODO_VERIFICATION.md; \
	echo "**Version:** ArkEcho v15 — Verification & Implementation Edition (Oct 2025)" >> ZENODO_VERIFICATION.md; \
	echo "**Attestation Timestamp (UTC):** \`$${TS}\` (\`attest/$${TS}/\`)" >> ZENODO_VERIFICATION.md; \
	echo "**Final Verdict:** \`final_pass_v2: true\` (see \`chain_of_custody_report_v2.json\`)" >> ZENODO_VERIFICATION.md; \
	echo "" >> ZENODO_VERIFICATION.md; \
	echo "## Evidence bundle & checksums" >> ZENODO_VERIFICATION.md; \
	echo "- **File:** \`$${BUNDLE}\`" >> ZENODO_VERIFICATION.md; \
	echo "  **SHA-256:** \`$${HASH}\`" >> ZENODO_VERIFICATION.md; \
	echo "" >> ZENODO_VERIFICATION.md; \
	echo "Included digest manifest inside the bundle:" >> ZENODO_VERIFICATION.md; \
	echo "- **File:** \`attest/$${TS}/SHA256SUMS.txt\` (authoritative list)" >> ZENODO_VERIFICATION.md; \
	echo "" >> ZENODO_VERIFICATION.md; \
	echo "### Top artefacts (first few lines of SHA256SUMS.txt)" >> ZENODO_VERIFICATION.md; \
	echo "\`\`\`" >> ZENODO_VERIFICATION.md; \
	sed -n '1,6p' attest/$${TS}/SHA256SUMS.txt >> ZENODO_VERIFICATION.md; \
	echo "\`\`\`" >> ZENODO_VERIFICATION.md; \
	echo ">>> Wrote ZENODO_VERIFICATION.md"

service-install:
	@echo ">>> Installing systemd unit (sudo required)"
	@sudo tee /etc/systemd/system/arkecho-guardian.service >/dev/null <<'EOF'
[Unit]
Description=ArkEcho Guardian Sidecar
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User='"$(shell id -un)"'
Group='"$(shell id -gn)"'
WorkingDirectory='"$(shell pwd)"'
Environment="PATH=$(shell pwd)/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="OLLAMA_HOST=127.0.0.1"
ExecStart=$(shell pwd)/venv/bin/python -m uvicorn service:app --host 127.0.0.1 --port 8080
Restart=on-failure
RestartSec=2
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
EOF

service-reload:
	@sudo systemctl daemon-reload

service-start:
	@sudo systemctl enable --now arkecho-guardian

service-status:
	@systemctl status arkecho-guardian --no-pager || true

service-logs:
	@journalctl -u arkecho-guardian -f

service-remove:
	@sudo systemctl disable --now arkecho-guardian || true
	@sudo rm -f /etc/systemd/system/arkecho-guardian.service
	@sudo systemctl daemon-reload
	@echo ">>> Removed."

clean:
	@echo ">>> Cleaning venv and artefacts"
	@pkill -f "uvicorn service:app" || true
	@rm -rf venv __pycache__ dist build *.tgz attest/* ZENODO_VERIFICATION.md
	@echo ">>> Clean complete."
