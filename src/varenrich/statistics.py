"""Dependency-free enrichment statistics with auditable implementations."""

from __future__ import annotations

import math
from collections.abc import Iterable


def _log_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def hypergeom_survival(overlap: int, query_size: int, set_size: int, universe_size: int) -> float:
    """Return P[X >= overlap] for X ~ Hypergeometric(N, K, n).

    ``universe_size`` is N, ``set_size`` is K, and ``query_size`` is n.
    Log-space probabilities avoid overflowing on human-genome-sized universes.
    """
    values = (overlap, query_size, set_size, universe_size)
    if any(not isinstance(value, int) for value in values):
        raise TypeError("hypergeometric counts must be integers")
    if universe_size < 1:
        raise ValueError("universe_size must be positive")
    if not 0 <= query_size <= universe_size:
        raise ValueError("query_size must be between 0 and universe_size")
    if not 0 <= set_size <= universe_size:
        raise ValueError("set_size must be between 0 and universe_size")
    maximum = min(query_size, set_size)
    minimum = max(0, query_size - (universe_size - set_size))
    if overlap <= minimum:
        return 1.0
    if overlap > maximum:
        return 0.0

    denominator = _log_choose(universe_size, query_size)
    terms = [
        _log_choose(set_size, k)
        + _log_choose(universe_size - set_size, query_size - k)
        - denominator
        for k in range(overlap, maximum + 1)
    ]
    peak = max(terms)
    probability = math.exp(peak) * sum(math.exp(term - peak) for term in terms)
    return min(1.0, max(0.0, probability))


def benjamini_hochberg(p_values: Iterable[float]) -> list[float]:
    """Adjust p-values using the Benjamini-Hochberg step-up procedure."""
    values = list(p_values)
    if any(not 0 <= value <= 1 for value in values):
        raise ValueError("p-values must be between 0 and 1")
    count = len(values)
    adjusted = [1.0] * count
    running = 1.0
    for rank, index in reversed(list(enumerate(sorted(range(count), key=values.__getitem__), 1))):
        running = min(running, values[index] * count / rank)
        adjusted[index] = min(1.0, running)
    return adjusted

