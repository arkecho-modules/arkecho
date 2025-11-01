#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# ArkEcho v15 bundle builder
# Generates 5 SKU zips in dist/ for Gumroad:
#   - Educational
#   - Indie
#   - Startup
#   - Corporate
#   - Corporate_Premium
#
# All editions include:
#  - Guardian sidecar (service.py -> /check, /answer, /verify)
#  - MHI + Protection Index telemetry
#  - Offline-first, no-calls-out runtime posture
#  - Governance + Covenant
#  - Chain of custody verification scripts
#
# Corporate / Premium additionally include SECURITY_COMMERCE.md, LOGGING.md
###############################################################################

# ------------------------------------------------------------------
# Resolve project root as the parent of this script's directory.
# Example: if script is   /home/arc/Desktop/ARKECHO_v15/scripts/build_all_v15.sh
# ROOT becomes            /home/arc/Desktop/ARKECHO_v15
# ------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$ROOT"

echo "[1/6] Cleaning old build artifacts..."
rm -rf "$ROOT/release" "$ROOT/dist"
mkdir -p "$ROOT/release" "$ROOT/dist"

# ------------------------------------------------------------------
# helper: safe_rsync_dir
# copies a dir from ROOT into TARGET/<that-dir-name>, excluding junk
# ------------------------------------------------------------------
safe_rsync_dir () {
  local SRC_DIR="$1"
  local TARGET_DIR="$2"

  if [ -d "$SRC_DIR" ]; then
    rsync -a \
      --exclude '__pycache__' \
      --exclude '.git' \
      --exclude '.venv' \
      --exclude 'venv' \
      --exclude 'attest' \
      --exclude 'logs' \
      --exclude '*.pyc' \
      --exclude '.DS_Store' \
      "$SRC_DIR"/ "$TARGET_DIR/$(basename "$SRC_DIR")"/
  else
    echo "WARN: dir $SRC_DIR not found, skipping"
  fi
}

# ------------------------------------------------------------------
# helper: copy_named_file
# find a file by basename anywhere under $ROOT and copy it into $TARGET
# ------------------------------------------------------------------
copy_named_file () {
  local NAME="$1"
  local TARGET="$2"

  # search the WHOLE project tree, not just scripts/
  local FOUND
  FOUND="$(find "$ROOT" -maxdepth 2 -type f -name "$NAME" -print -quit 2>/dev/null || true)"

  if [ -n "$FOUND" ]; then
    rsync -a "$FOUND" "$TARGET/"
  else
    echo "WARN: file $NAME not found in project root, skipping"
  fi
}

# ------------------------------------------------------------------
# helper: stage_edition
# creates release/<EditionName>, copies common/enterprise files + dirs,
# creates logs README, drops systemd template
# ------------------------------------------------------------------
stage_edition () {
  local EDITION_NAME="$1"; shift
  local FILE_LIST=("$@")

  local TARGET="$ROOT/release/$EDITION_NAME"
  mkdir -p "$TARGET"

  echo "  -> Staging $EDITION_NAME in $TARGET"

  echo "     -> Copying files"
  for F in "${FILE_LIST[@]}"; do
    local BASENAME
    BASENAME="$(basename "$F")"
    copy_named_file "$BASENAME" "$TARGET"
  done

  echo "     -> Copying core runtime dirs"
  # these dirs are at $ROOT right now in your tree
  for D in core modules new_modules quantum scripts bus configs interface tools governance docs SECURITY_COMMERCE.md; do
    # NOTE: we also want bus/, configs/, interface/, tools/, governance/, docs/
    # SECURITY_COMMERCE.md is a *file*, but this loop sees it's not a dir and will "skip"
    if [ -d "$ROOT/$D" ]; then
      safe_rsync_dir "$ROOT/$D" "$TARGET"
    else
      # quiet skip for dirs not present
      :
    fi
  done

  # logs placeholder
  mkdir -p "$TARGET/logs"
  echo "(Runtime evidence lands here when you run ArkEcho locally. Local only, never phoned home.)" > "$TARGET/logs/README.txt"

  # systemd template
  cat > "$TARGET/arkecho-guardian.service.example" <<'EOF'
[Unit]
Description=ArkEcho Guardian Sidecar
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=YOUR_USERNAME
Group=YOUR_USERNAME
WorkingDirectory=/path/to/ARKECHO_v15
Environment="PATH=/path/to/ARKECHO_v15/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
Environment="OLLAMA_HOST=127.0.0.1"
ExecStart=/path/to/ARKECHO_v15/venv/bin/python -m uvicorn service:app --host 127.0.0.1 --port 8080
Restart=on-failure
RestartSec=2
TimeoutStopSec=15

[Install]
WantedBy=multi-user.target
EOF
}

# ------------------------------------------------------------------
# FILE SETS
# ------------------------------------------------------------------

COMMON_FILES=(
  "README.md"
  "START_HERE_Newbie_Guide.md"
  "INSTALL_AND_VERIFY.md"
  "PROOF_OF_WORK.txt"
  "PROOF_OF_WORK_windows.ps1"
  "VERIFY_windows.md"
  "ZENODO_VERIFICATION.md"
  "LICENSE.txt"
  "COMPLIANCE.md"
  "SECURITY.md"
  "GOVERNANCE.md"
  "ArkEchoSessionCovenant v1.md"
  "service.py"
  "guardian_wrapper.py"
  "requirements.txt"
  "verify_chain_of_custody.py"
  "verify_chain_of_custody_v2.py"
  "chain_of_custody_report.json"
  "chain_of_custody_report_v2.json"
  "audit_report.txt"
  "auditor.py"
  "Makefile"
  "Makefile.ps1"
)

ENTERPRISE_FILES=(
  "SECURITY_COMMERCE.md"
  "LOGGING.md"
)

echo "[2/6] Staging Educational..."
EDU_NAME="ArkEcho_v15_Educational"
stage_edition "$EDU_NAME" "${COMMON_FILES[@]}"
# strip enterprise-only stuff
rm -f "$ROOT/release/$EDU_NAME/SECURITY_COMMERCE.md" "$ROOT/release/$EDU_NAME/LOGGING.md" 2>/dev/null || true

echo "[3/6] Staging Indie..."
INDIE_NAME="ArkEcho_v15_Indie"
stage_edition "$INDIE_NAME" "${COMMON_FILES[@]}"
rm -f "$ROOT/release/$INDIE_NAME/SECURITY_COMMERCE.md" "$ROOT/release/$INDIE_NAME/LOGGING.md" 2>/dev/null || true

echo "[4/6] Staging Startup..."
STARTUP_NAME="ArkEcho_v15_Startup"
stage_edition "$STARTUP_NAME" "${COMMON_FILES[@]}"
rm -f "$ROOT/release/$STARTUP_NAME/SECURITY_COMMERCE.md" "$ROOT/release/$STARTUP_NAME/LOGGING.md" 2>/dev/null || true

echo "[5/6] Staging Corporate..."
CORP_NAME="ArkEcho_v15_Corporate"
stage_edition "$CORP_NAME" "${COMMON_FILES[@]}" "${ENTERPRISE_FILES[@]}"

echo "[5/6b] Staging Corporate_Premium..."
PREMIUM_NAME="ArkEcho_v15_Corporate_Premium"
stage_edition "$PREMIUM_NAME" "${COMMON_FILES[@]}" "${ENTERPRISE_FILES[@]}"
# if you eventually add SBOM / pack_governance_week.py extras, they will naturally get pulled because scripts/ is already included

echo "[6/6] Zipping bundles..."

cd "$ROOT/release"

zip -q -r "$ROOT/dist/${EDU_NAME}.zip"     "$EDU_NAME"
zip -q -r "$ROOT/dist/${INDIE_NAME}.zip"   "$INDIE_NAME"
zip -q -r "$ROOT/dist/${STARTUP_NAME}.zip" "$STARTUP_NAME"
zip -q -r "$ROOT/dist/${CORP_NAME}.zip"    "$CORP_NAME"
zip -q -r "$ROOT/dist/${PREMIUM_NAME}.zip" "$PREMIUM_NAME"

cd "$ROOT"

echo ""
echo "✅ Zips are in $ROOT/dist:"
ls -lh "$ROOT/dist"/*.zip
echo ""

echo "Generating SHA256SUMS.txt for Gumroad listings..."
cd "$ROOT/dist"
sha256sum *.zip > SHA256SUMS.txt
echo ""
cat SHA256SUMS.txt
echo ""
echo "✅ Copy the above hashes + file sizes into each Gumroad product description."
echo ""
echo "Reminder to include in each listing:"
echo " - offline-first, local-only (no telemetry)"
echo " - pre-check (/check) and post-verify (/answer,/verify)"
echo " - Protection Index + Moral Health Index (MHI)"
echo " - Governance.md, Covenant, Compliance docs are INCLUDED"
echo " - 'Because these go to 11.' 🎸"
