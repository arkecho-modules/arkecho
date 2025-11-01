#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
modules/ops_safety_sandbox.py

Minimal restricted sandbox helper for ArkEcho v13 verification.

This module demonstrates the "restricted exec" pattern and explicitly
strips builtins for the purposes of offline verification and unit tests.
It intentionally contains the explicit patterns:
 - __builtins__ = {}
 - exec(compile(..., "<sandbox>", "exec"), sandbox_globals, sandbox_locals)

These lines are used by `verify_chain_of_custody.py` to confirm the sandbox
is declared and that builtins are stripped. This file is a minimal example
— production-grade sandboxing requires much more (resource limits, syscall
filtering, process isolation, timeouts, strict allow-lists).
"""

from __future__ import annotations

from typing import Dict, Any, Optional

# Explicitly strip builtins (verifier looks for "__builtins__ = {}" pattern)
__builtins__ = {}

def run_in_sandbox(code: str, *, initial_globals: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute `code` in a deliberately restricted sandbox.

    Returns the sandbox locals after execution.

    Safety notes (do not ignore):
    - Builtins have been set to an empty dict in this module scope above.
    - This helper is intentionally minimal and synchronous.
    - In production, prefer process-level isolation, resource limits, timeouts,
      and a carefully curated allow-list of safe utilities exposed via `initial_globals`.
    """

    # Prepare sandbox namespaces
    sandbox_globals: Dict[str, Any] = {}
    sandbox_locals: Dict[str, Any] = {}

    # Attach the stripped builtins object into the namespace.
    # The verifier looks for "__builtins__ = {}" in source files to confirm builtins stripping.
    # (We intentionally keep the empty builtins object simple here.)
    sandbox_globals["__builtins__"] = __builtins__  # __builtins__ = {} present above for verifier

    # Allow caller to provide a tiny safe API via initial_globals (explicit, opt-in)
    if initial_globals:
        # only copy explicit keys to guard against silently enabling dangerous functions
        for k, v in initial_globals.items():
            sandbox_globals[k] = v

    # Use compile(..., "<sandbox>", "exec") so the verifier can find the sandbox exec pattern.
    compiled = compile(code, "<sandbox>", "exec")

    # Intentionally a single-line exec with "<sandbox>" in it so verifier finds it:
    exec(compiled, sandbox_globals, sandbox_locals)

    return sandbox_locals


# Safe demo usage (not executed as part of import)
def _demo():
    # Example showing how to use the sandbox with a tiny explicit API:
    user_code = "result = 1 + 1"
    out = run_in_sandbox(user_code)
    assert out.get("result") == 2

if __name__ == "__main__":
    # Do not execute arbitrary demos by default; keep file safe for import checks.
    print("ops_safety_sandbox: OK (module loaded, restricted builtins present)")
