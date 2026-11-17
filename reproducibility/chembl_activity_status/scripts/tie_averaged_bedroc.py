"""Tie-order-independent, finite-sample-normalized BEDROC for S13.

Each active in a tied score block receives the mean exponential rank discount
over that block, matching the final OR2 S13A–S13D convention. This is the
expectation over all permutations of observations inside score ties.
"""

from __future__ import annotations

import math

import numpy as np


def tie_averaged_bedroc(y_true, scores, alpha: float = 20.0) -> float:
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    if y.shape != s.shape:
        raise ValueError("Labels and scores must have identical shapes")
    if alpha <= 0:
        raise ValueError("alpha must be positive")
    ok = np.isfinite(s)
    y, s = y[ok], s[ok]
    if len(y) == 0 or len(np.unique(y)) < 2:
        return float("nan")
    if not set(np.unique(y)).issubset({0, 1}):
        raise ValueError("Labels must be binary")

    order = np.argsort(-s, kind="mergesort")
    y, s = y[order], s[order]
    n = len(y)
    positive_count = int(y.sum())
    discounts = np.exp(-alpha * np.arange(1, n + 1, dtype=float) / n)
    numerator = 0.0
    start = 0
    while start < n:
        end = start + 1
        while end < n and s[end] == s[start]:
            end += 1
        block_positives = int(y[start:end].sum())
        numerator += block_positives * (float(discounts[start:end].sum()) / (end - start))
        start = end

    prevalence = positive_count / n
    rie = numerator / (prevalence * float(discounts.sum()))
    rie_max = (1.0 - math.exp(-alpha * prevalence)) / (prevalence * (1.0 - math.exp(-alpha)))
    rie_min = (1.0 - math.exp(alpha * prevalence)) / (prevalence * (1.0 - math.exp(alpha)))
    return float((rie - rie_min) / (rie_max - rie_min))
