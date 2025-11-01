# core/runner.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
# Core runner (delegates to bus runner) + end-of-cycle integrity summary
# v1.4.0 — jurisdiction auto-default + alignment eval + PSI line + audit snapshot with jurisdiction tag

from __future__ import annotations
from typing import Any, Dict
import os, sys, inspect, json
from datetime import datetime, UTC

# ---------------------------------------------------------------------
# Path bootstrap: ensure project root and /modules are importable
# ---------------------------------------------------------------------
_THIS_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
_MODULES_DIR = os.path.join(_PROJECT_ROOT, "modules")
for _p in (_PROJECT_ROOT, _MODULES_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------------
# Try the canonical runner; fall back to a no-op if missing
# ---------------------------------------------------------------------
try:
    from bus.runner import run_pipeline  # type: ignore
except Exception:
    def run_pipeline(*_a, **_kw) -> Any:  # type: ignore
        # Safe no-op runner so the summary still executes offline
        return None

def main() -> Any:
    """
    Execute the ArkEcho pipeline (or a safe no-op if unavailable).
    Handles both signatures: run_pipeline() and run_pipeline(cfg, ctx).
    Adds jurisdiction context to ctx (from env, default UK).
    """
    # Jurisdiction auto-default (env override)
    jurisdiction = os.getenv("ARKECHO_JURISDICTION", "UK").upper().strip()
    print(f"[ArkEcho] Jurisdiction context: {jurisdiction}")

    # Try to respect either signature
    try:
        sig = inspect.signature(run_pipeline)  # type: ignore
        if len(sig.parameters) >= 2:
            cfg: Dict[str, Any] = {"mode": "test", "version": "v11r1"}
            ctx: Dict[str, Any] = {"jurisdiction": jurisdiction}
            return run_pipeline(cfg, ctx)  # type: ignore
        else:
            return run_pipeline()  # type: ignore
    except Exception:
        # Last resort attempts
        try:
            return run_pipeline({"mode": "test"}, {"jurisdiction": jurisdiction})  # type: ignore
        except Exception:
            try:
                return run_pipeline()  # type: ignore
            except Exception:
                return None

if __name__ == "__main__":
    _result = main()

    # ===============================================================
    # 🧭 ArkEcho_v11r1 — End-of-Cycle Integrity Summary and Telemetry
    # ===============================================================
    try:
        # Prefer packaged layout, then flat fallback
        try:
            from core import report_core as _report_core  # type: ignore
        except Exception:
            import report_core as _report_core            # type: ignore

        # Telemetry module
        try:
            from modules import telemetry_feedback_core as _telemetry  # type: ignore
        except Exception:
            import telemetry_feedback_core as _telemetry               # type: ignore

        # Alignment profile (safe import)
        try:
            from core import alignment_profile as _align  # type: ignore
        except Exception:
            _align = None  # type: ignore

        # 1) Generate integrity summary
        summary: Dict[str, Any] = _report_core.summarize()

        print("\n" + "=" * 65)
        print(f" ArkEcho_v11r1 Integrity Summary — {summary['time']}")
        print("=" * 65)
        print(f"  Modules OK   : {summary['ok']}/{summary['modules']}")
        print(f"  Avg Risk     : {summary['avg_risk']:.3f}")
        print(f"  Reliability  : {summary['reliability']:.3f}")
        print(f"  Stability    : {summary['stability']:.3f}")
        print(f"  Coherence    : {summary['coherence']:.3f}\n")

        # 2) Emit telemetry feedback (optional, offline-safe)
        telemetry_state = _telemetry.init()
        telemetry_ctx = {
            "cpu_load": 0.3,
            "mem_load": 0.4,
            "feedback_signal": summary.get("stability", 0.0),
        }
        telemetry_output, telemetry_state = _telemetry.run(telemetry_ctx, telemetry_state)

        try:
            health = telemetry_output["data"]["health"]
            moral_fb = telemetry_output["data"]["moral_feedback"]
        except Exception:
            health, moral_fb = None, None

        print(
            f"  Telemetry Feedback → Health={health if health is not None else 'n/a'}, "
            f"Moral Feedback={moral_fb if moral_fb is not None else 'n/a'}"
        )

        # 3) Optional: PSI status from ethics module (if present)
        try:
            psi_hits = 0
            for r in summary.get("results", []):
                if r.get("module") == "law_ethics_and_explainability":
                    psi = r.get("data", {}).get("psychological_integrity")
                    if psi:
                        psi_hits = len(psi.get("hits", []) or [])
                    break
            print(f"  PSI status → {'clean' if psi_hits == 0 else f'flagged: {psi_hits} pattern(s)'}")
        except Exception:
            pass

        # 4) Alignment evaluation (non-blocking)
        alignment = None
        if _align and hasattr(_align, "evaluate"):
            try:
                alignment = _align.evaluate(summary)
                print(f"  Alignment → {alignment.get('status','n/a')}")
            except Exception:
                alignment = None

        # 5) Emit event to a bus/emitter if available (safe no-op otherwise)
        emitted = False
        try:
            from bus import emitter as bus_emitter  # type: ignore
            if hasattr(bus_emitter, "emit"):
                bus_emitter.emit("integrity_summary", summary)
                if alignment is not None:
                    bus_emitter.emit("alignment", alignment)
                bus_emitter.emit("telemetry_feedback", telemetry_output)
                emitted = True
        except Exception:
            pass

        if not emitted:
            try:
                import emitter  # type: ignore
                if hasattr(emitter, "emit"):
                    emitter.emit("integrity_summary", summary)
                    if alignment is not None:
                        emitter.emit("alignment", alignment)
                    emitter.emit("telemetry_feedback", telemetry_output)
            except Exception:
                pass  # Safe offline fallback

        # 6) Write a timestamped audit snapshot (offline-safe) with jurisdiction tag
        try:
            logs_dir = os.path.join(_PROJECT_ROOT, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            ts = datetime.now(UTC).isoformat(timespec="seconds").replace(":", "")
            jur = os.getenv("ARKECHO_JURISDICTION", "UK").upper().strip() or "UNK"
            out_path = os.path.join(logs_dir, f"integrity_{jur}_{ts}.json")

            # Embed alignment (if available) before saving
            to_save = dict(summary)
            if alignment is not None:
                to_save["alignment"] = alignment
            to_save["jurisdiction"] = jur

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(to_save, ensure_ascii=False, indent=2))

            print(f"  Audit snapshot saved → {out_path}")
        except Exception as _e:
            print(f"  [audit export skipped] {_e}")

        print("=" * 65 + "\n")

    except Exception as e:
        print(f"[ArkEcho_v11r1 Integrity Summary Failed] {e}")
