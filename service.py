import time
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from fastapi import FastAPI
from pydantic import BaseModel

# -----------------------------------------------------------------------------
# basic config
# -----------------------------------------------------------------------------

LOG_DIR = Path("./logs/runtime")
LOG_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "mistral"  # you already pulled this
CPU_OPTIONS = {
    "num_gpu_layers": 0  # force pure CPU so it doesn't try GPU VRAM
}

app = FastAPI(title="ArkEcho Guardian Sidecar", version="0.1")


# -----------------------------------------------------------------------------
# request / response schemas
# -----------------------------------------------------------------------------

class GuardianRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = None


class VerifyRequest(BaseModel):
    output: str
    meta: Optional[Dict[str, Any]] = None


# -----------------------------------------------------------------------------
# helper: minimal moral hash / ledger write
# -----------------------------------------------------------------------------

def _now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _write_ledger(kind: str, data: Dict[str, Any]) -> None:
    """
    Append a JSON line to logs/runtime/YYYYMMDD_guardian.jsonl
    That gives you local, offline audit trail.
    """
    day = time.strftime("%Y%m%d", time.gmtime())
    fpath = LOG_DIR / f"{day}_guardian.jsonl"
    entry = {
        "ts": _now_ts(),
        "kind": kind,
        **data,
    }
    with fpath.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# -----------------------------------------------------------------------------
# Guardian pre-check
# This is where ArkEcho decides if we should even allow the request.
# For now: we simulate your Guardian Framework behaviour:
# - block obvious self-harm / exploitation / illegal stuff
# - otherwise pass
# -----------------------------------------------------------------------------

BLOCK_PATTERNS = [
    "suicide",
    "how do i kill",
    "how to hurt",
    "child sexual",
    "csam",
    "exploit a child",
    "bomb",
    "make a weapon",
    "how to hack",
]

def guardian_precheck(prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
    lowered = prompt.lower()

    # crude safety block (you can wire your actual guardian here)
    for bad in BLOCK_PATTERNS:
        if bad in lowered:
            rationale = f"Guardian halt: sensitive / harmful intent detected ('{bad}')"
            decision = {
                "status": "halt",
                "risk": 1.0,
                "protection_index": 1.0,
                "rationale": rationale,
            }
            _write_ledger("precheck_block", {
                "prompt": prompt,
                "context": context,
                "decision": decision,
            })
            return decision

    # otherwise allow
    decision = {
        "status": "pass",
        "risk": 0.0,
        "protection_index": 0.01,
        "rationale": "Request cleared by Guardian precheck.",
    }
    _write_ledger("precheck_pass", {
        "prompt": prompt,
        "context": context,
        "decision": decision,
    })
    return decision


# -----------------------------------------------------------------------------
# Guardian post-check
# This is the "after model speaks" gate.
# Here we can:
# - assert output is reversible (always yes in our flow, because we haven't
#   actually pushed it anywhere permanent)
# - sanity check tone / grooming / manipulation
# -----------------------------------------------------------------------------

BAD_TONE_SNIPPETS = [
    "don't tell your parents",
    "keep this secret",
    "i can meet you alone",
]

def guardian_postcheck(output_text: str,
                       context: Dict[str, Any]) -> Dict[str, Any]:

    lowered = output_text.lower()

    # grooming / secrecy red flag
    for phrase in BAD_TONE_SNIPPETS:
        if phrase in lowered:
            rationale = f"Guardian flagged grooming language ('{phrase}')"
            decision = {
                "blocked": True,
                "reversible": True,
                "mhi": 0.4,  # Moral Health Index dropped
                "rationale": rationale,
            }
            _write_ledger("postcheck_block", {
                "output": output_text,
                "context": context,
                "decision": decision,
            })
            return decision

    # normal safe result
    decision = {
        "blocked": False,
        "reversible": True,  # ArkEcho principle: always undoable
        "mhi": 0.95,
        "rationale": "Output is reversible and suitable for delivery.",
    }
    _write_ledger("postcheck_pass", {
        "output": output_text,
        "context": context,
        "decision": decision,
    })
    return decision


# -----------------------------------------------------------------------------
# internal helper: call local mistral via Ollama
# streaming mode, but we stitch chunks into one string for you
# -----------------------------------------------------------------------------

def call_local_llm(prompt: str, timeout_s: int = 120) -> str:
    """
    Ask Ollama for completion. Forces CPU mode via num_gpu_layers=0.
    We ALSO cap num_predict so it can't ramble forever on CPU.
    Returns the full stitched text or raises.
    """
    ollama_req = {
        "model": MODEL_NAME,
        "options": {
            "num_gpu_layers": 0,  # run fully on CPU
            "num_predict": 40     # cap length so we don't sit here forever
        },
        "prompt": prompt,
    }

    r = requests.post(
        OLLAMA_URL,
        json=ollama_req,
        timeout=timeout_s,
        stream=True,
    )
    r.raise_for_status()

    chunks = []
    for line in r.iter_lines():
        if not line:
            continue
        try:
            piece = json.loads(line.decode("utf-8"))
        except Exception:
            continue
        if "response" in piece:
            chunks.append(piece["response"])

    return "".join(chunks).strip()


# -----------------------------------------------------------------------------
# /ping   (sanity check; lets you see service is alive)
# -----------------------------------------------------------------------------

@app.get("/ping")
def ping():
    status = {
        "ok": True,
        "ts": _now_ts(),
        "message": "ArkEcho Guardian sidecar live",
    }
    _write_ledger("ping", status)
    return status


# -----------------------------------------------------------------------------
# /check  (pre-check only, no model run)
# -----------------------------------------------------------------------------

@app.post("/check")
def check(req: GuardianRequest):
    ctx = req.context or {}
    decision = guardian_precheck(req.prompt, ctx)
    # we already logged in guardian_precheck
    return {
        "status": decision["status"],
        "risk": decision["risk"],
        "rationale": decision["rationale"],
        "protection_index": decision["protection_index"],
    }


# -----------------------------------------------------------------------------
# /answer (full guarded answer)
# Flow:
#   1. Guardian precheck
#   2. Call local Mistral through Ollama (CPU mode)
#   3. Guardian postcheck
#   4. Return final text if allowed
# -----------------------------------------------------------------------------

@app.post("/answer")
def guarded_answer(req: GuardianRequest):
    ctx = req.context or {}
    user_prompt = req.prompt

    # 1. PRECHECK
    pre = guardian_precheck(user_prompt, ctx)
    if pre["status"] == "halt":
        resp = {
            "blocked": True,
            "safe_output": None,
            "rationale": f"Request paused by Guardian: {pre['rationale']}",
            "mhi": 0.95,
        }
        _write_ledger("answer_preblocked", {
            "prompt": user_prompt,
            "context": ctx,
            "resp": resp,
        })
        return resp

    # 2. GENERATE WITH OLLAMA
    try:
        model_output = call_local_llm(user_prompt, timeout_s=120)
    except requests.exceptions.ReadTimeout:
        model_output = "[LLM_ERROR: Timeout waiting for local model (increase timeout)]"
    except Exception as e:
        model_output = f"[LLM_ERROR: {e}]"

    # 3. POSTCHECK
    post = guardian_postcheck(model_output, ctx)

    resp = {
        "blocked": post["blocked"],
        "safe_output": None if post["blocked"] else model_output,
        "rationale": post["rationale"],
        "mhi": post["mhi"],
    }

    # 4. LOG EVERYTHING FOR AUDIT
    _write_ledger("answer_complete", {
        "prompt": user_prompt,
        "context": ctx,
        "model_output": model_output,
        "final_response": resp,
    })

    return resp


# -----------------------------------------------------------------------------
# /verify  (just a post-check on some text you pass in)
# This is like "is this safe to show / store / ship?"
# -----------------------------------------------------------------------------

@app.post("/verify")
def verify(req: VerifyRequest):
    ctx = req.meta or {}
    text = req.output

    decision = guardian_postcheck(text, ctx)

    resp = {
        "reversible": decision["reversible"],
        "blocked": decision["blocked"],
        "rationale": decision["rationale"],
        "mhi": decision["mhi"],
        "hash": _hash_str(text),
    }

    _write_ledger("verify", {
        "text": text,
        "meta": ctx,
        "decision": resp,
    })

    return resp
