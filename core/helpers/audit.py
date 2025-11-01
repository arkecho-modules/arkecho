# core/helpers/audit.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
"""
Unified audit logging for ArkEcho events.
Provides a function to log events with timestamp and integrity hash.
"""
import json
import time
from core.utils import ensure_dir, sha256_hex
from pathlib import Path

# Define path for audit log (e.g., ~/.arkecho/logs/arkecho_audit.jsonl)
_log_path = Path.home() / ".arkecho" / "logs" / "arkecho_audit.jsonl"
ensure_dir(_log_path.parent)

def log_event(event: dict) -> None:
    """
    Append an event dict to the audit log with timestamp and hash for integrity.
    """
    event["timestamp"] = time.time()
    # Compute hash excluding 'hash' field
    event_copy = {k: v for k, v in event.items() if k != "hash"}
    event_json = json.dumps(event_copy, sort_keys=True)
    event_hash = sha256_hex(event_json.encode('utf-8'))
    event["hash"] = event_hash
    with open(_log_path, "a") as f:
        json.dump(event, f)
        f.write("\n")
