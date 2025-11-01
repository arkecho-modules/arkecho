# core/psi_compliance.py
# ArkEcho Systems © 2025 — Psychological Integrity compliance helper (hardened)

from __future__ import annotations
from typing import Dict, Any, List, Tuple
import re

def _normalize_text(x: Any) -> str:
    """Flatten nested structures to a single, lowercase text block (keys + values)."""
    if x is None:
        return ""
    if isinstance(x, dict):
        parts = []
        for k, v in x.items():
            parts.append(_normalize_text(k))
            parts.append(_normalize_text(v))
        return " ".join(parts)
    if isinstance(x, (list, tuple, set)):
        return " ".join(_normalize_text(i) for i in x)
    s = str(x).lower()
    # Light normalization: collapse punctuation to spaces for resilient matching
    s = re.sub(r"[_\-+:/\\|]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# Default textual patterns for exploitative reward/engagement mechanics
# Keep these broad yet specific; normalized text collapses punctuation/hyphens.
_DEFAULT_PATTERNS = [
    r"\bloot\s*box(es)?\b",
    r"\bgacha\b",
    r"\bpay\s*to\s*win\b",
    r"\bartificial\s*scarcity\b",
    r"\blimited\s*time\s*offer\b",
    r"\bstreak\s*loss\b",
    r"\baddictive\s*loop\b",
    r"\bvariable\s*reward\b",
    r"\bcompulsive\s*(play|spend|engage)\b",
]

def check_psychological_integrity(
    design: Dict[str, Any] | None = None,
    telemetry: Dict[str, Any] | None = None,
    extra_patterns: List[str] | None = None
) -> Tuple[List[str], float]:
    """
    Scan provided design/telemetry for exploitative reward patterns.
    Returns (violations, score) where score ∈ [0,1].
    Non-punitive: caller decides response (e.g., flag for redesign).
    """
    design = design or {}
    telemetry = telemetry or {}

    haystack = " ".join([
        _normalize_text(design),
        _normalize_text(telemetry),
    ])

    patterns = _DEFAULT_PATTERNS + (extra_patterns or [])
    hits: List[str] = []
    for pat in patterns:
        try:
            if re.search(pat, haystack):
                hits.append(pat)
        except re.error:
            # ignore bad custom patterns, keep scanning
            continue

    # Score caps at 1.0; unique hits to avoid over-counting similar patterns
    score = min(1.0, len(set(hits)) / 5.0)
    return hits, round(score, 3)
