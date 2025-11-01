# ArkEcho Systems © 2025 — Minimal loop/time guard

from __future__ import annotations
import time

class LoopGuard:
    def __init__(self, max_seconds: float = 30.0, max_calls: int = 1000):
        self.max_seconds = max_seconds
        self.max_calls = max_calls
        self.start = None
        self.calls = 0

    def __enter__(self):
        self.start = time.time()
        self.calls = 0
        return self

    def tick(self):
        self.calls += 1
        if (time.time() - self.start) > self.max_seconds:
            raise TimeoutError(f"LoopGuard: exceeded {self.max_seconds}s")
        if self.calls > self.max_calls:
            raise RuntimeError(f"LoopGuard: exceeded {self.max_calls} calls")

    def __exit__(self, exc_type, exc, tb):
        return False
