import math
from itertools import pairwise

import pytest

from varenrich.statistics import benjamini_hochberg, hypergeom_survival


def test_hypergeom_known_probability():
    # P(X >= 2) when drawing 3 from a population of 10 containing 4 successes.
    expected = (math.comb(4, 2) * math.comb(6, 1) + math.comb(4, 3)) / math.comb(10, 3)
    assert hypergeom_survival(2, 3, 4, 10) == pytest.approx(expected)


def test_hypergeom_boundaries_and_invalid_values():
    assert hypergeom_survival(0, 3, 4, 10) == 1.0
    assert hypergeom_survival(4, 3, 4, 10) == 0.0
    with pytest.raises(ValueError):
        hypergeom_survival(1, 11, 4, 10)


def test_bh_is_monotonic_by_p_value():
    p_values = [0.01, 0.04, 0.03, 0.002]
    adjusted = benjamini_hochberg(p_values)
    ranked = sorted(zip(p_values, adjusted))
    assert all(first[1] <= second[1] for first, second in pairwise(ranked))
    assert adjusted == pytest.approx([0.02, 0.04, 0.04, 0.008])
