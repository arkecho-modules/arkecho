# =========== ArkEcho v15 — Third-Party Verification (Windows) ===========
# 1) Hash check
$bundle = "ArkEcho_v15_attest_20251030T214518Z.zip"   # <- change to your filename
(Get-FileHash $bundle -Algorithm SHA256).Hash
# Compare the output with the SHA-256 printed in ZENODO_VERIFICATION.md

# 2) Inspect archive contents
Expand-Archive -LiteralPath $bundle -DestinationPath "$env:TEMP\arkecho_attest" -Force
Get-ChildItem "$env:TEMP\arkecho_attest" -Recurse | Select-Object -First 20 | Format-Table -AutoSize

# 3) Inspect SHA256SUMS.txt and chain_of_custody JSON
$ts = "20251030T214518Z"  # <- change to match the folder inside the archive
$base = Join-Path $env:TEMP "arkecho_attest\$ts"
Get-Content (Join-Path $base "SHA256SUMS.txt") | Select-Object -First 6

# Pretty-print JSON with built-in PowerShell:
$json = Get-Content (Join-Path $base "chain_of_custody_report_v2.json") -Raw | ConvertFrom-Json
$json | Format-List
# Confirm: final_pass_v2 == true and other expected fields present

# 4) (Optional) Re-run a tiny demo on their machine:
#     - Create a Python venv
#     - pip install -r requirements.txt
#     - start uvicorn service:app
#     - POST /check and /answer (curl or Invoke-RestMethod)
