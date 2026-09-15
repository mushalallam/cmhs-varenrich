"""Independent numerical comparison of VarEnrich probabilities with SciPy."""

from __future__ import annotations

import random

from scipy.stats import hypergeom

from varenrich.statistics import hypergeom_survival


def main() -> None:
    random.seed(20260915)
    maximum_error = 0.0
    for _ in range(1_000):
        universe = random.randint(2, 5_000)
        term = random.randint(0, universe)
        query = random.randint(0, universe)
        lower = max(0, query - (universe - term))
        upper = min(query, term)
        overlap = random.randint(lower, upper)
        observed = hypergeom_survival(overlap, query, term, universe)
        reference = float(hypergeom.sf(overlap - 1, universe, term, query))
        maximum_error = max(maximum_error, abs(observed - reference))
    print(f"1,000-case SciPy comparison maximum absolute error: {maximum_error:.3g}")
    if maximum_error >= 1e-10:
        raise SystemExit("Numerical validation threshold exceeded")


if __name__ == "__main__":
    main()
