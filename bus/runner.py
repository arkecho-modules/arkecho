# bus/runner.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
# Pipeline execution engine for ArkEcho bus

from core.loader import load_module
from core.contract import coerce_output, ModuleOutput
from core.utils import timer

def run_pipeline(cfg: dict, ctx: dict) -> dict:
    """
    Run a pipeline as defined in cfg (with 'steps': [ {'name':..., 'call':...}, ... ])
    against the context ctx. Returns an aggregated result.
    """
    results = []
    overall_ok = True
    steps = cfg.get("steps", [])
    for idx, step in enumerate(steps, start=1):
        step_name = step.get("name", f"step_{idx}")
        call_path = step.get("call")
        if not call_path:
            continue
        try:
            module_fn = load_module(call_path)
        except Exception as e:
            # If module cannot be loaded, mark as failure
            results.append({
                "i": idx,
                "name": step_name,
                "action": "block",
                "risk": "vhigh",
                "elapsed_s": 0.0
            })
            overall_ok = False
            break
        # Execute module function with timer
        try:
            output, elapsed = timer(module_fn, ctx)
        except Exception:
            elapsed = 0.0
            output = None
        # Normalize output
        mod_output = coerce_output(output)
        results.append({
            "i": idx,
            "name": step_name,
            "action": mod_output.action,
            "risk": mod_output.risk,
            "elapsed_s": round(elapsed, 3)
        })
        if mod_output.action == "block":
            overall_ok = False
            break
    return {"ok": overall_ok, "results": results}
