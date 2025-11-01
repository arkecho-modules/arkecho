# scripts/verify_pack.py
# ArkEcho Systems © 2025 — Verify a governance bundle's SHA256 manifest

from __future__ import annotations
import os, sys, json, zipfile, hashlib, tempfile, shutil

def sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256(); h.update(b); return h.hexdigest()

def sha256_path(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def verify(bundle_path: str, manifest_path: str) -> int:
    # Check bundle hash
    if not os.path.isfile(bundle_path):
        print(f"[ERR] bundle not found: {bundle_path}")
        return 2
    if not os.path.isfile(manifest_path):
        print(f"[ERR] manifest not found: {manifest_path}")
        return 2

    with open(manifest_path, "r", encoding="utf-8") as f:
        man = json.load(f)

    bundle_sha = sha256_path(bundle_path)
    if bundle_sha != man.get("bundle_sha256"):
        print("[FAIL] bundle sha256 mismatch.")
        print(f" expected: {man.get('bundle_sha256')}")
        print(f"   actual: {bundle_sha}")
        return 1
    else:
        print("[OK] bundle sha256 matches.")

    # Extract and verify each entry
    with zipfile.ZipFile(bundle_path, "r") as z, tempfile.TemporaryDirectory() as td:
        z.extractall(td)
        ok = True
        for ent in man.get("entries", []):
            fp = os.path.join(td, ent["file"])
            if not os.path.isfile(fp):
                print(f"[FAIL] missing file in bundle: {ent['file']}")
                ok = False
                continue
            got = sha256_path(fp)
            if got != ent["sha256"]:
                print(f"[FAIL] sha mismatch: {ent['file']}")
                print(f" expected: {ent['sha256']}")
                print(f"   actual: {got}")
                ok = False
            else:
                print(f"[OK] {ent['file']} sha256 match.")
        return 0 if ok else 1

def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/verify_pack.py <bundle.zip> <bundle.manifest.json>")
        sys.exit(2)
    sys.exit(verify(sys.argv[1], sys.argv[2]))

if __name__ == "__main__":
    main()
