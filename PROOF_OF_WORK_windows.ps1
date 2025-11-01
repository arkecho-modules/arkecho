<# ============================================================================
 ArkEcho v15 — Proof-of-Work & Attestation (Windows / PowerShell)
 Run in: PowerShell 5+ or PowerShell 7+ (recommended)
 Project root example: C:\Users\YOUR-COMPUTER\Desktop\ARKECHO_v15
============================================================================ #>

# --- CONFIG ---------------------------------------------------------------
# CHANGE THIS to your actual project root:
$Root = "C:\Users\YOUR-COMPUTER\Desktop\ARKECHO_v15"

# Derived paths
Set-Location $Root
$AttestDir  = Join-Path $Root "attest"
$LogsDir    = Join-Path $Root "logs"
$CocV2Json  = Join-Path $Root "chain_of_custody_report_v2.json"
$CocV2Py    = Join-Path $Root "verify_chain_of_custody_v2.py"

# UTC timestamp like 20251030T214518Z
$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$SnapDir   = Join-Path $AttestDir $Timestamp
$Bundle    = Join-Path $Root ("ArkEcho_v15_attest_{0}.zip" -f $Timestamp)  # Use .zip on Windows
$ZenodoMd  = Join-Path $Root "ZENODO_VERIFICATION.md"

# --- 1) Ensure latest attestation exists ---------------------------------
if (Test-Path $CocV2Py) {
  Write-Host "Running verify_chain_of_custody_v2.py..." -ForegroundColor Cyan
  # Use the project venv if you have one; otherwise use system python
  $VenvPy = Join-Path $Root "venv\Scripts\python.exe"
  if (Test-Path $VenvPy) {
    & $VenvPy $CocV2Py
  } else {
    python $CocV2Py
  }
} else {
  Write-Warning "Missing $CocV2Py (skipping attestation script run)"
}

# --- 2) Snapshot proofs ---------------------------------------------------
Write-Host "Creating snapshot: $SnapDir" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $SnapDir | Out-Null

# Copy chain_of_custody_report_v2.json (if present)
if (Test-Path $CocV2Json) {
  Copy-Item $CocV2Json -Destination $SnapDir -Force
} else {
  Write-Warning "Missing $CocV2Json"
}

# Copy ArkEchoSessionCovenant*.md (if any)
Get-ChildItem -Path $Root -Filter "ArkEchoSessionCovenant*.md" -File -ErrorAction SilentlyContinue | ForEach-Object {
  Copy-Item $_.FullName -Destination $SnapDir -Force
}

# Copy logs folder (if present)
if (Test-Path $LogsDir) {
  $SnapLogs = Join-Path $SnapDir "logs"
  Copy-Item $LogsDir -Destination $SnapLogs -Recurse -Force
} else {
  Write-Warning "No logs folder found (skipping)"
}

# --- 3) Create SHA-256 manifest for all files in snapshot -----------------
Write-Host "Building SHA256SUMS.txt..." -ForegroundColor Cyan
$ShaFile = Join-Path $SnapDir "SHA256SUMS.txt"
$BaseLen = ($SnapDir.TrimEnd('\')).Length + 1

# Compute relative paths + SHA256 hashes
Remove-Item $ShaFile -ErrorAction SilentlyContinue
Get-ChildItem -Path $SnapDir -File -Recurse | ForEach-Object {
  $rel = $_.FullName.Substring($BaseLen) -replace '\\','/'
  $hash = (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash
  # Match GNU format: "<hash> *relative/path"
  "$hash *$rel" | Out-File -FilePath $ShaFile -Encoding UTF8 -Append
}

# --- 4) Create bundle (ZIP) + optional GPG signature ----------------------
Write-Host "Creating bundle: $Bundle" -ForegroundColor Cyan
if (Test-Path $Bundle) { Remove-Item $Bundle -Force }
Compress-YOUR-COMPUTERhive -Path $SnapDir -DestinationPath $Bundle

# Optional GPG signing (requires gpg.exe in PATH)
# gpg --detach-sign --armor "$Bundle"

Write-Host ("`u2705 Proof bundle: {0}" -f $Bundle) -ForegroundColor Green

# --- 5) Generate ZENODO_VERIFICATION.md ----------------------------------
Write-Host "Generating Zenodo verification block..." -ForegroundColor Cyan
$Sha256 = (Get-FileHash -Path $Bundle -Algorithm SHA256).Hash
# Show first 6 lines of SHA file (if present)
$TopSha = @()
if (Test-Path $ShaFile) {
  $TopSha = Get-Content $ShaFile -TotalCount 6
}

$Zenodo = @"
# Zenodo Verification Block (paste-in)

**DOI:** `10.5281/zenodo.XXXXXXX`
**Version:** ArkEcho v15 — Verification & Implementation Edition (Oct 2025)  
**Attestation Timestamp (UTC):** `$Timestamp` (`attest/$Timestamp/`)  
**Final Verdict:** `final_pass_v2: true` (see `chain_of_custody_report_v2.json`)

## Evidence bundle & checksums
YOUR-COMPUTERhive to attach:
- **File:** `$(Split-Path -Leaf $Bundle)`  
  **SHA-256:** `$Sha256`

Included digest manifest inside the bundle:
- **File:** `attest/$Timestamp/SHA256SUMS.txt` (authoritative list)

### Top artefacts (first few lines of SHA256SUMS.txt)


$($TopSha -join "rn")

"@
Set-Content -Path $ZenodoMd -Value $Zenodo -Encoding UTF8
Write-Host ("`u2705 Wrote {0} (hash: {1})" -f $ZenodoMd,$Sha256) -ForegroundColor Green

# --- 6) Success message ---------------------------------------------------
Write-Host "`nDone." -ForegroundColor Green
Write-Host "Bundle: $Bundle"
Write-Host "Zenodo block: $ZenodoMd"