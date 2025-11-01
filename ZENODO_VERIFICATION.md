# Zenodo Verification Block (paste-in)

**DOI:** `10.5281/zenodo.XXXXXXX`
**Version:** ArkEcho v15 — Verification & Implementation Edition (Oct 2025)
**Attestation Timestamp (UTC):** `20251030T221756Z` (`attest/20251030T221756Z/`)
**Final Verdict:** `final_pass_v2: true` (see `chain_of_custody_report_v2.json`)

## Evidence bundle & checksums
Archive to attach:
- **File:** `ArkEcho_v15_attest_20251030T221756Z.tgz`
  **SHA-256:** `ed5a49b425111f4e4908214b2fbaac258515cd78e96f8a2dc8e2a57b61203dc5`

Included digest manifest inside the bundle:
- `attest/20251030T221756Z/SHA256SUMS.txt` (authoritative list of file hashes within this attestation snapshot)

Anyone can verify integrity by:
1. Extracting `ArkEcho_v15_attest_20251030T221756Z.tgz`
2. Running: `cd 20251030T221756Z && sha256sum -c SHA256SUMS.txt`
3. Confirming all entries report `OK`

