# core/helpers/reviewers.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
"""
Reviewer scoring and selection helper for oversight processes.
Provides functions to score reviewers based on trust, load, etc., and pick top candidates.
"""
import math
from typing import List, Dict, Any

def score_reviewer(reviewer: Dict[str, Any]) -> float:
    """
    Compute a reviewer's score based on trust, workload, and domain match.
    Formula: score = (1 - load) + trust + 0.3 * domain_match
    """
    trust = reviewer.get("trust", 0.0)          # Trust [0,1]
    load = reviewer.get("load", 0.0)            # Load [0,1] (1 means fully busy)
    domain = reviewer.get("domain_match", 0.0)  # Domain match [0,1]
    score = (1.0 - load) + trust + 0.3 * domain
    return score

def pick_top_reviewers(reviewers: List[Dict[str, Any]], top_n: int = 1) -> List[Dict[str, Any]]:
    """
    Select the top N reviewers by score (highest first).
    """
    scored = [(score_reviewer(r), r) for r in reviewers]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for (_score, r) in scored[:top_n]]
