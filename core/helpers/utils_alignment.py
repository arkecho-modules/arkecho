# core/helpers/utils_alignment.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
"""
Utilities for alignment calculations: cosine drift and weighted softmax.
"""
import math

def cosine_drift(vec_a, vec_b, epsilon: float = 1e-8) -> float:
    """
    Compute 1 - cosine similarity between two equal-length vectors.
    Returns drift in [0,2] (0 = no drift).
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 1.0
    dot = 0.0
    norm_a = norm_b = 0.0
    for x, y in zip(vec_a, vec_b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    norm_a = math.sqrt(norm_a)
    norm_b = math.sqrt(norm_b)
    if norm_a < epsilon or norm_b < epsilon:
        return 0.0
    cosine_sim = dot / (norm_a * norm_b)
    cosine_sim = max(min(cosine_sim, 1.0), -1.0)
    return 1.0 - cosine_sim

def weighted_softmax(values: list, base_weights: list = None) -> list:
    """
    Compute softmax over values, optionally biasing by base_weights added element-wise.
    Returns normalized weights summing to 1.
    """
    if base_weights and len(base_weights) == len(values):
        vals = [v + w for v, w in zip(values, base_weights)]
    else:
        vals = list(values)
    if not vals:
        return []
    max_val = max(vals)
    exps = [math.exp(v - max_val) for v in vals]
    sum_exps = sum(exps)
    if sum_exps == 0:
        return [1.0/len(vals)] * len(vals)
    return [e / sum_exps for e in exps]
