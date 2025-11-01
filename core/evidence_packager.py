# core/evidence_packager.py
# ArkEcho Systems © 2025 — deterministic, offline evidence-bundle stub.

from __future__ import annotations
from typing import Dict, Any
import json, hashlib, os
from datetime import datetime, UTC

def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def package(event: Dict[str, Any], out_dir: str = "evidence") -> Dict[str, Any]:
    """
    Deterministically packages an evidence event with timestamps and checksums.
    Offline-only; no network calls. Returns manifest including file paths.
    """
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now(UTC).isoformat(timespec="seconds").replace(":", "")
    body = {
        "timestamp": ts,
        "event": event,
        "chain": {"created_by": "ArkEcho_v11r1", "version": "1.0"},
    }
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = _sha256_bytes(raw)

    fname = f"evidence_{ts}_{digest[:8]}.json"
    path = os.path.join(out_dir, fname)
    with open(path, "wb") as f:
        f.write(raw)

    manifest = {
        "path": path,
        "sha256": digest,
        "size": os.path.getsize(path),
        "timestamp": ts,
    }
    with open(path + ".manifest.json", "w", encoding="utf-8") as mf:
        mf.write(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest
