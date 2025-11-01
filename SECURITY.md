
---

### `SECURITY.md`
```md
# SECURITY — ArkEcho v15

## Threat model (high level)
- **Data custody:** All inputs/outputs and decisions remain local. No telemetry.
- **Auditability:** Every decision is logged with time, rationale, and integrity fields.
- **Safety gates:** Pre-check halts unsafe prompts; post-verify withholds irreversible outputs.

## Data handling
- **Storage:** `./logs/` (JSON, optional HTML summaries per edition).
- **Retention:** You control retention. Delete or archive as policy requires.
- **Network:** Sidecar binds to `127.0.0.1` by default. Do not expose publicly without a reverse proxy/auth.

## Child & vulnerable-user safety
- The Guardian Framework prioritizes protection and **may halt** or defer when uncertain.
- Outputs delivered only when **reversible**; otherwise withheld for human review.

## Dependencies
- Pinned in `requirements.txt` for deterministic installs.
- Recommended Python: 3.11+.

## Reporting vulnerabilities
Please create a minimal reproduction (sanitized) and contact the maintainer.  
Include: OS, Python version, edition, logs snippet around the issue.  
If this repo is mirrored publicly, open a private security advisory on the host platform.

## Hardening tips (optional)
- Run as a **non-privileged user**.
- Keep `venv` separate per project.
- Consider filesystem encryption on `logs/` at rest if handling sensitive data.
- For multi-user hosts, restrict filesystem ACLs on the project directory.
