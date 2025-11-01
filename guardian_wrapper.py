import requests
import subprocess
import json
import sys
import os
import glob
import time
import hmac
import hashlib

# ArkEcho Guardian local endpoints
GUARDIAN_URL_CHECK = "http://localhost:8080/check"
GUARDIAN_URL_VERIFY = "http://localhost:8080/verify"

# Local model name (we know mistral via ollama works on your machine)
MODEL_NAME = "mistral"


# =========================
# CORE GUARDED GENERATION
# =========================

def ask_guarded(prompt: str) -> str:
    """
    1. Pre-check with ArkEcho Guardian (Guardian decides if we are even allowed to ask).
    2. Generate with local model (offline / ollama mistral).
    3. Post-check with ArkEcho Guardian (Guardian verifies output is lawful, humane, reversible).
    """

    # 1. PRE-CHECK
    try:
        pre_resp = requests.post(
            GUARDIAN_URL_CHECK,
            json={"prompt": prompt, "context": {}},
            timeout=5,
        )
        pre = pre_resp.json()
    except Exception as e:
        return f"[GUARDIAN PRECHECK ERROR] {e}"

    if pre.get("status") == "halt":
        return f"[BLOCKED BEFORE GENERATION] {pre.get('rationale', 'risk too high')}"

    # 2. GENERATION (local mistral via ollama)
    try:
        proc = subprocess.run(
            ["ollama", "run", MODEL_NAME],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        model_answer = proc.stdout.decode("utf-8", errors="replace").strip()
    except Exception as e:
        return f"[MODEL ERROR] {e}"

    # 3. POST-CHECK
    try:
        post_resp = requests.post(
            GUARDIAN_URL_VERIFY,
            json={"output": model_answer},
            timeout=5,
        )
        post = post_resp.json()
    except Exception as e:
        return f"[GUARDIAN POSTCHECK ERROR] {e}"

    if not post.get("reversible", True):
        return "[WITHHELD AFTER GENERATION] output requires human review"

    return model_answer


# =====================================================================
# MESH SUPPORT (ArkEcho v16 pre-wire: Collective Memory Protocol)
#
# GOAL:
# - Export privacy-clean 'ghosts' describing what Guardian halted
#   (numeric / categorical only, never raw text, never IDs)
# - Bundle & sign them into a .arkmesh file for manual sharing
#
# - Import another node's .arkmesh file
# - Verify signature using shared mesh_hmac_key
# - Turn those ghosts into "pending safety improvements"
#   in mesh_pending_safety.json (for human approval)
#
# We NEVER auto-change Guardian policy. We only queue suggestions.
# =====================================================================

# ---- internal constants / paths ----
RUNTIME_LOG_DIR = "logs/runtime"
MESH_OUTBOX_DIR = "mesh_outbox"
MESH_PENDING_FILE = "mesh_pending_safety.json"
MESH_POLICY_FILE = "configs/mesh_policy.yaml"
KEYS_FILE = "configs/keys.yaml"


NON_EXPORT_KEYS = {
    "raw_context",
    "full_text",
    "transcript",
    "session_id",
    "user_id",
    "actor_id",
    "conversation_id",
    "ip",
    "age_hint",
    "demographic_hint",
    "geo_hint",
    "timestamp",  # do not forward timestamps: re-ident risk
    "user_role",  # e.g. "minor" etc. -- never export
}

ALLOWED_FIELDS = {
    "pattern",              # e.g. "grooming_escalation"
    "manipulation_score",   # e.g. 0.14
    "empathy_drop",         # e.g. 0.04
    "halt_latency_ms",      # e.g. 52
    "guardian_action",      # e.g. "halt"
    "jurisdiction",         # e.g. "UK"
}


def _load_mesh_secret(keys_path: str = KEYS_FILE) -> bytes:
    """
    Load mesh_hmac_key from configs/keys.yaml.

    Expected line in keys.yaml:
        mesh_hmac_key: "SOME_LONG_RANDOM_SECRET"

    We keep parsing dead simple: first line that starts with mesh_hmac_key:
    """

    if not os.path.exists(keys_path):
        raise RuntimeError("keys.yaml not found. Cannot sign/verify mesh packets.")

    key_str = None
    with open(keys_path, "r", encoding="utf-8") as f:
        for line in f:
            line_stripped = line.strip()
            if line_stripped.lower().startswith("mesh_hmac_key:"):
                parts = line_stripped.split(":", 1)
                if len(parts) == 2:
                    candidate = parts[1].strip().strip('"').strip("'")
                    if candidate:
                        key_str = candidate
                        break

    if not key_str:
        raise RuntimeError("mesh_hmac_key not found in keys.yaml")

    return key_str.encode("utf-8")


def _make_ghost(guardian_event: dict) -> dict:
    """
    Produce a privacy-clean ghost dict from a Guardian event.
    Reject anything that risks leaking raw content, identity, or replayable specifics.
    """

    if not isinstance(guardian_event, dict):
        return {}

    # If any non-export key is present, hard reject.
    for bad_key in NON_EXPORT_KEYS:
        if bad_key in guardian_event:
            return {}

    ghost: dict = {}
    for key in ALLOWED_FIELDS:
        if key in guardian_event:
            val = guardian_event[key]

            # Only accept ints/floats or short safe strings
            if isinstance(val, (int, float)):
                ghost[key] = val
            elif isinstance(val, str):
                if len(val) <= 64:
                    ghost[key] = val
                else:
                    return {}
            else:
                return {}

    # Require minimum shape
    for required_key in ("pattern", "guardian_action", "jurisdiction"):
        if required_key not in ghost:
            return {}

    if ghost.get("guardian_action") not in ("halt", "allow", "escalate"):
        return {}

    # sanity check halt_latency_ms if present
    ms = ghost.get("halt_latency_ms")
    if ms is not None:
        if (not isinstance(ms, (int, float))) or ms < 0 or ms > 10000:
            return {}

    return ghost


def _collect_recent_guardian_events(runtime_dir: str = RUNTIME_LOG_DIR) -> list[dict]:
    """
    Read recent Guardian runtime logs (we assume *.jsonl with one JSON object per line).
    We only sample the last ~5 files to keep it light.
    """

    ghosts: list[dict] = []
    paths = sorted(glob.glob(os.path.join(runtime_dir, "*.jsonl")))

    for p in paths[-5:]:
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        evt = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    g = _make_ghost(evt)
                    if g:
                        ghosts.append(g)
        except FileNotFoundError:
            continue
        except PermissionError:
            continue

    return ghosts


def export_mesh_packet(out_dir: str = MESH_OUTBOX_DIR) -> str:
    """
    Build a mesh packet from local ghosts, sign it, and save as .arkmesh.
    This does NOT auto-send anywhere. You (human) move it however you want.
    """

    os.makedirs(out_dir, exist_ok=True)

    ghosts = _collect_recent_guardian_events()
    clean_ghosts = [g for g in ghosts if g]

    packet_body = {
        "version": "arkmesh_v16_draft1",
        "created_unix": int(time.time()),
        "ghosts": clean_ghosts,
    }

    # sign/HMAC
    secret = _load_mesh_secret()
    body_bytes = json.dumps(packet_body, sort_keys=True).encode("utf-8")
    sig = hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()
    packet_body["hmac_sha256"] = sig

    out_path = os.path.join(out_dir, f"packet_{packet_body['created_unix']}.arkmesh")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(packet_body, f, indent=2, sort_keys=True)

    return out_path


def _load_mesh_policy(policy_path: str = MESH_POLICY_FILE) -> dict:
    """
    Tiny, dependency-free parser for configs/mesh_policy.yaml.
    We only care about:
      allowed_patterns:
        - some_pattern
      manipulation_margin: 0.02
    """

    cfg = {
        "allowed_patterns": [],
        "manipulation_margin": 0.02,
    }

    if not os.path.exists(policy_path):
        return cfg

    with open(policy_path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.readlines()]

    current_key = None
    for ln in lines:
        if not ln or ln.startswith("#"):
            continue

        if ":" in ln and not ln.startswith("-"):
            k, v = ln.split(":", 1)
            k = k.strip()
            v = v.strip()
            current_key = k

            if k == "manipulation_margin":
                try:
                    cfg[k] = float(v)
                except ValueError:
                    pass
            elif k == "allowed_patterns":
                cfg[k] = []
            else:
                cfg[k] = v
        else:
            # list item if we're inside allowed_patterns
            if current_key == "allowed_patterns" and ln.startswith("-"):
                pat = ln.lstrip("-").strip()
                if pat:
                    cfg["allowed_patterns"].append(pat)

    return cfg


def _verify_packet_sig(packet: dict) -> bool:
    """
    Confirm HMAC matches packet body.
    """

    if "hmac_sha256" not in packet:
        return False
    sig = packet["hmac_sha256"]

    body_copy = dict(packet)
    body_copy.pop("hmac_sha256", None)

    secret = _load_mesh_secret()
    body_bytes = json.dumps(body_copy, sort_keys=True).encode("utf-8")
    calc = hmac.new(secret, body_bytes, hashlib.sha256).hexdigest()

    return hmac.compare_digest(sig, calc)


def _ghost_is_legally_safe(ghost: dict, mesh_cfg: dict) -> bool:
    """
    Gate check on imported ghosts.
    Must be short categorical + numeric. No PII, no transcripts.
    Pattern must be on our whitelist.
    """

    if not isinstance(ghost, dict):
        return False

    # required fields
    for r in ("pattern", "guardian_action", "jurisdiction"):
        if r not in ghost:
            return False

    if ghost["guardian_action"] not in ("halt", "allow", "escalate"):
        return False

    # whitelist pattern
    allowed_pats = mesh_cfg.get("allowed_patterns", [])
    if allowed_pats and ghost["pattern"] not in allowed_pats:
        return False

    # block long strings / suspicious keys
    banned_keys = ["raw_context", "session_id", "user_id", "full_text"]
    for b in banned_keys:
        if b in ghost:
            return False

    for k, v in ghost.items():
        if isinstance(v, str) and len(v) > 64:
            return False

    return True


def _derive_suggestion_from_ghost(ghost: dict, mesh_cfg: dict) -> dict:
    """
    Convert an imported ghost into a pending safety-tightening suggestion.
    We ONLY suggest stricter behaviour.
    """

    suggestion = {
        "pattern": ghost.get("pattern", ""),
        "proposed_at_unix": int(time.time()),
        "source": "mesh_import",
        "notes": [],
        "actions": []
    }

    # 1. tighten manipulation_score cutoff
    ms = ghost.get("manipulation_score")
    if isinstance(ms, (int, float)):
        margin = mesh_cfg.get("manipulation_margin", 0.02)
        proposed_thresh = max(0.0, ms - margin)
        suggestion["actions"].append({
            "type": "tighten_threshold",
            "field": "manipulation_score_cutoff",
            "new_value": proposed_thresh,
            "direction": "safer_only"
        })
        suggestion["notes"].append(
            f"Observed halt at manip_score≈{ms:.3f}; propose cutoff {proposed_thresh:.3f}."
        )

    # 2. tighten halt latency
    lt = ghost.get("halt_latency_ms")
    if isinstance(lt, (int, float)):
        suggestion["actions"].append({
            "type": "tighten_latency",
            "field": "max_halt_latency_ms",
            "new_value": int(lt),
            "direction": "safer_only"
        })
        suggestion["notes"].append(
            f"Peer halted in {int(lt)}ms; propose matching or faster."
        )

    # 3. explicitly mark high-risk patterns Guardian halted
    if ghost.get("guardian_action") == "halt":
        suggestion["actions"].append({
            "type": "set_high_risk_pattern",
            "pattern": ghost.get("pattern", ""),
            "risk_level": "high",
            "direction": "safer_only"
        })
        suggestion["notes"].append(
            "Pattern was hard-stopped by peer Guardian; mark as high-risk by default."
        )

    return suggestion


def _load_json(path: str):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _queue_safety_suggestion(suggestion: dict,
                             pending_path: str = MESH_PENDING_FILE) -> None:
    """
    Append a new tightening suggestion to mesh_pending_safety.json.

    We REFUSE any action that isn't explicitly 'safer_only'.
    We DO NOT actually mutate Guardian config here.
    """

    data = _load_json(pending_path)
    if not isinstance(data, list):
        data = []

    safe_actions = []
    for act in suggestion.get("actions", []):
        if act.get("direction") == "safer_only":
            safe_actions.append(act)

    if not safe_actions:
        return

    clean = {
        "pattern": suggestion.get("pattern", ""),
        "proposed_at_unix": suggestion.get("proposed_at_unix", int(time.time())),
        "source": suggestion.get("source", "mesh_import"),
        "notes": suggestion.get("notes", []),
        "actions": safe_actions,
        "status": "pending_human_review",
    }

    data.append(clean)
    _save_json(pending_path, data)


def ingest_mesh_packet(packet_path: str,
                       pending_path: str = MESH_PENDING_FILE,
                       policy_path: str = MESH_POLICY_FILE) -> dict:
    """
    Import a .arkmesh packet from another ArkEcho node (manually transferred).
    Verify HMAC, sanity-check ghosts, produce only stricter-safety suggestions.

    We do NOT auto-apply. Suggestions wait in mesh_pending_safety.json
    for a human to merge into configs/settings.yaml + custody logs.
    """

    if not os.path.exists(packet_path):
        raise FileNotFoundError(packet_path)

    with open(packet_path, "r", encoding="utf-8") as f:
        packet = json.load(f)

    # verify signature
    if not _verify_packet_sig(packet):
        return {
            "status": "reject",
            "reason": "signature_failed",
            "accepted": 0,
            "rejected": 0,
        }

    mesh_cfg = _load_mesh_policy()
    ghosts = packet.get("ghosts", [])

    accepted = 0
    rejected = 0

    for g in ghosts:
        if not _ghost_is_legally_safe(g, mesh_cfg):
            rejected += 1
            continue

        suggestion = _derive_suggestion_from_ghost(g, mesh_cfg)
        _queue_safety_suggestion(suggestion, pending_path=pending_path)
        accepted += 1

    return {
        "status": "ok",
        "accepted": accepted,
        "rejected": rejected,
        "pending_file": pending_path,
    }


def list_pending_safety(pending_path: str = MESH_PENDING_FILE) -> list[dict]:
    """
    View pending tightening suggestions that came from Mesh.
    These are waiting for a human to apply them.
    """
    data = _load_json(pending_path)
    if not isinstance(data, list):
        return []
    return data


def apply_safety_suggestion(index: int,
                            pending_path: str = MESH_PENDING_FILE,
                            audit_log_path: str = "mesh_applied_log.json") -> dict:
    """
    Mark a suggestion as approved.
    We DO NOT silently mutate Guardian runtime config here.
    Instead we log an instruction set for ops (humans) to tighten thresholds
    in configs/settings.yaml and then capture that change in custody.

    That preserves:
    - human approval,
    - reversibility,
    - full audit trail.
    """

    data = _load_json(pending_path)
    if not isinstance(data, list):
        raise IndexError("Pending safety list empty.")
    if index < 0 or index >= len(data):
        raise IndexError("No such pending suggestion index.")

    suggestion = data[index]
    suggestion["status"] = "applied_pending_manual_merge"
    suggestion["applied_unix"] = int(time.time())

    data[index] = suggestion
    _save_json(pending_path, data)

    applied_log = _load_json(audit_log_path)
    if not isinstance(applied_log, list):
        applied_log = []

    applied_log.append({
        "applied_unix": suggestion["applied_unix"],
        "pattern": suggestion.get("pattern", ""),
        "actions": suggestion.get("actions", []),
        "note": "Operator approved stricter safety. Manually tighten thresholds in configs/settings.yaml, then record custody.",
    })
    _save_json(audit_log_path, applied_log)

    return {
        "status": "ok",
        "actions_to_merge": suggestion.get("actions", []),
        "message": "Tighten indicated thresholds in configs/settings.yaml, then custody-log the change.",
    }


# =========================
# CLI ENTRY
# =========================

if __name__ == "__main__":
    # modes:
    # 1) text generation via guardian:
    #    python3 guardian_wrapper.py "some prompt for mistral"
    #
    # 2) export mesh packet:
    #    python3 guardian_wrapper.py --export-mesh
    #
    # 3) ingest mesh packet:
    #    python3 guardian_wrapper.py --ingest-mesh path/to/packet_xxx.arkmesh
    #
    # 4) list pending safety suggestions:
    #    python3 guardian_wrapper.py --list-pending
    #
    # 5) approve/apply a suggestion (record it, generate ops instructions):
    #    python3 guardian_wrapper.py --apply 0

    if len(sys.argv) == 1:
        # default demo prompt if nothing passed
        user_prompt = "Explain internet safety to a 10 year old in kind language."
        safe_output = ask_guarded(user_prompt)
        print("\n=== FINAL OUTPUT ===")
        print(safe_output)
        sys.exit(0)

    # if flags:
    if sys.argv[1] == "--export-mesh":
        path = export_mesh_packet()
        print(f"[MESH EXPORT COMPLETE] wrote packet: {path}")
        sys.exit(0)

    if sys.argv[1] == "--ingest-mesh":
        if len(sys.argv) < 3:
            print("usage: --ingest-mesh path/to/file.arkmesh")
            sys.exit(1)
        result = ingest_mesh_packet(sys.argv[2])
        print(json.dumps(result, indent=2))
        sys.exit(0)

    if sys.argv[1] == "--list-pending":
        pending = list_pending_safety()
        print(json.dumps(pending, indent=2))
        sys.exit(0)

    if sys.argv[1] == "--apply":
        if len(sys.argv) < 3:
            print("usage: --apply <index>")
            sys.exit(1)
        try:
            idx = int(sys.argv[2])
        except ValueError:
            print("index must be int")
            sys.exit(1)
        result = apply_safety_suggestion(idx)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # otherwise treat as user prompt
    user_prompt = " ".join(sys.argv[1:])
    safe_output = ask_guarded(user_prompt)
    print("\n=== FINAL OUTPUT ===")
    print(safe_output)
