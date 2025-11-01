#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.."; pwd)"
cd "$ROOT"

DIST="$ROOT/dist"
RELEASE="$ROOT/release"

# Clean previous artifacts (both old naming and new naming)
mkdir -p "$DIST"
rm -f "$DIST"/ArkEcho_v13_*.zip || true
rm -f "$DIST"/ARKECHO_v13_*.zip "$DIST"/*Premium.zip || true

# Map editions -> release subfolders
declare -A MAP=(
  ["Educational"]="ArkEcho_v13_Educational"
  ["Indie"]="ArkEcho_v13_Indie"
  ["Startup"]="ArkEcho_v13_Startup"
  ["Corporate"]="ArkEcho_v13_Corporate"
  ["Corporate Premium"]="ArkEcho_v13_Corporate_Premium"
)

# Build each zip deterministically (no extra file attrs via -X)
for name in "Educational" "Indie" "Startup" "Corporate" "Corporate Premium"; do
  src="$RELEASE/${MAP[$name]}"
  out="$DIST/ArkEcho_v13_${name// /_}.zip"
  if [[ -d "$src" ]]; then
    echo "Packing: $src -> $out"
    # Zip from inside release/ so archives contain edition folder at top level (good layout)
    ( cd "$RELEASE" && zip -r -q -X "$out" "${MAP[$name]}" )
  else
    echo "ERROR: missing source folder: $src" >&2
    exit 2
  fi
done

echo
echo "New artifacts (newest first):"
ls -lht "$DIST"/ArkEcho_v13_*.zip

echo
echo "Writing SHA256 checksums..."
( cd "$DIST" && sha256sum ArkEcho_v13_*.zip > ArkEcho_v13_sha256.txt )
echo "Done: $DIST/ArkEcho_v13_sha256.txt"
