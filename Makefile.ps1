<#
 ArkEcho v15 — Convenience Makefile.ps1 (Windows)
 Usage:
   ./Makefile.ps1 venv
   ./Makefile.ps1 deps
   ./Makefile.ps1 run
   ./Makefile.ps1 check
   ./Makefile.ps1 answer
   ./Makefile.ps1 proof
   ./Makefile.ps1 proof-zenodo
   ./Makefile.ps1 clean
#>

param([Parameter(Position=0)][string]$Task = "help")

$Root = (Get-Location).Path
$VEnv = Join-Path $Root "venv"
$Py   = Join-Path $VEnv "Scripts\python.exe"
$Pip  = Join-Path $VEnv "Scripts\pip.exe"

function venv {
  if (Test-Path $VEnv) { Remove-Item -Recurse -Force $VEnv }
  python -m venv $VEnv
  & $Py -V
}

function deps {
  if (-not (Test-Path $Py)) { venv }
  & $Py -m pip install --upgrade pip
  & $Pip install -r requirements.txt
}

function run {
  if (-not (Test-Path $Py)) { deps }
  & $Py -m uvicorn service:app --host 127.0.0.1 --port 8080
}

function check {
  $body = @{ prompt = "Explain cyberbullying to a 10-year-old, no scary detail."; context = @{} } | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/check" -ContentType "application/json" -Body $body | ConvertTo-Json
}

function answer {
  $body = @{ prompt = "Explain cyberbullying to a 10-year-old, no scary detail."; context = @{} } | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/answer" -ContentType "application/json" -Body $body | ConvertTo-Json
}

function proof {
  if (Test-Path (Join-Path $Root "verify_chain_of_custody_v2.py")) {
    & $Py (Join-Path $Root "verify_chain_of_custody_v2.py")
  } else {
    Write-Host "NOTE: verify_chain_of_custody_v2.py not found (skipping)" -ForegroundColor Yellow
  }

  $Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
  $SnapDir   = Join-Path $Root "attest\$Timestamp"
  New-Item -ItemType Directory -Force -Path $SnapDir | Out-Null

  $coc = Join-Path $Root "chain_of_custody_report_v2.json"
  if (Test-Path $coc) { Copy-Item $coc $SnapDir -Force }

  Get-ChildItem -Path $Root -Filter "ArkEchoSessionCovenant*.md" -File -ErrorAction SilentlyContinue | ForEach-Object {
    Copy-Item $_.FullName -Destination $SnapDir -Force
  }
  if (Test-Path (Join-Path $Root "logs")) {
    Copy-Item (Join-Path $Root "logs") -Destination (Join-Path $SnapDir "logs") -Recurse -Force
  }

  $ShaFile = Join-Path $SnapDir "SHA256SUMS.txt"
  $BaseLen = ($SnapDir.TrimEnd('\')).Length + 1
  if (Test-Path $ShaFile) { Remove-Item $ShaFile -Force }
  Get-ChildItem -Path $SnapDir -File -Recurse | ForEach-Object {
    $rel = $_.FullName.Substring($BaseLen) -replace '\\','/'
    $hash = (Get-FileHash -Path $_.FullName -Algorithm SHA256).Hash
    "$hash *$rel" | Out-File -FilePath $ShaFile -Encoding UTF8 -Append
  }

  $Bundle = Join-Path $Root ("ArkEcho_v15_attest_{0}.zip" -f $Timestamp)
  if (Test-Path $Bundle) { Remove-Item $Bundle -Force }
  Compress-Archive -Path $SnapDir -DestinationPath $Bundle

  $Hash = (Get-FileHash -Path $Bundle -Algorithm SHA256).Hash
  Write-Host "✓ Proof bundle: $Bundle" -ForegroundColor Green
  Write-Host "  SHA256: $Hash"
}

function proof-zenodo {
  $Att = Get-ChildItem -Path (Join-Path $Root "attest") -Directory -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
  if (-not $Att) { Write-Error "No attest/* found. Run: ./Makefile.ps1 proof"; exit 1 }
  $TS = $Att.Name
  $Bundle = Join-Path $Root ("ArkEcho_v15_attest_{0}.zip" -f $TS)
  if (-not (Test-Path $Bundle)) { Write-Error "Missing $Bundle. Run: ./Makefile.ps1 proof"; exit 1 }
  $Hash = (Get-FileHash -Path $Bundle -Algorithm SHA256).Hash

  $ShaFile = Join-Path $Att.FullName "SHA256SUMS.txt"
  $Top = @()
  if (Test-Path $ShaFile) { $Top = Get-Content $ShaFile -TotalCount 6 }

  $Zenodo = @"
# Zenodo Verification Block (paste-in)

**DOI:** `10.5281/zenodo.XXXXXXX`
**Version:** ArkEcho v15 — Verification & Implementation Edition (Oct 2025)
**Attestation Timestamp (UTC):** `$TS` (`attest/$TS/`)
**Final Verdict:** `final_pass_v2: true` (see `chain_of_custody_report_v2.json`)

## Evidence bundle & checksums
- **File:** `$(Split-Path -Leaf $Bundle)`
  **SHA-256:** `$Hash`

Included digest manifest inside the bundle:
- **File:** `attest/$TS/SHA256SUMS.txt` (authoritative list)

### Top artefacts (first few lines of SHA256SUMS.txt)

$($Top -join "rn")

"@
  Set-Content -Path (Join-Path $Root "ZENODO_VERIFICATION.md") -Value $Zenodo -Encoding UTF8
  Write-Host "✓ Wrote ZENODO_VERIFICATION.md" -ForegroundColor Green
}

function clean {
  Get-Process | Where-Object { $_.Path -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
  if (Test-Path $VEnv) { Remove-Item -Recurse -Force $VEnv }
  Get-ChildItem *.tgz, *.zip -ErrorAction SilentlyContinue | Remove-Item -Force
  if (Test-Path (Join-Path $Root "attest")) { Remove-Item -Recurse -Force (Join-Path $Root "attest") }
  if (Test-Path (Join-Path $Root "ZENODO_VERIFICATION.md")) { Remove-Item (Join-Path $Root "ZENODO_VERIFICATION.md") -Force }
  Write-Host "✓ Clean complete" -ForegroundColor Green
}

switch ($Task.ToLower()) {
  "venv"          { venv }
  "deps"          { deps }
  "run"           { run }
  "check"         { check }
  "answer"        { answer }
  "proof"         { proof }
  "proof-zenodo"  { proof-zenodo }
  "clean"         { clean }
  default {
    Write-Host "Tasks: venv | deps | run | check | answer | proof | proof-zenodo | clean"
  }
}


Quick-start (copy/paste)

Linux/macOS:

cd ~/Desktop/ARKECHO_v15
make deps
make run     # starts API on 127.0.0.1:8080
# In another terminal:
make check
make answer
# Build proof bundle + Zenodo block:
make proof
make proof-zenodo


Windows (PowerShell):

cd $HOME\Desktop\ARKECHO_v15
.\Makefile.ps1 deps
.\Makefile.ps1 run         # starts API on 127.0.0.1:8080
# New PowerShell tab:
.\Makefile.ps1 check
.\Makefile.ps1 answer
# Proof bundle + Zenodo block:
.\Makefile.ps1 proof
.\Makefile.ps1 proof-zenodo