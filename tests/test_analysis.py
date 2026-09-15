from varenrich.analysis import enrich
from varenrich.models import GeneSet


def test_enrichment_is_sorted_and_universe_limited():
    universe = {f"G{index}" for index in range(1, 11)}
    query = {"G1", "G2", "G3"}
    sets = [
        GeneSet("A", "Strong", "demo", frozenset({"G1", "G2", "G3", "OUTSIDE"})),
        GeneSet("B", "Weak", "demo", frozenset({"G1", "G4", "G5"})),
    ]
    results = enrich(query, universe, sets)
    assert [result.term_id for result in results] == ["A", "B"]
    assert results[0].term_size == 3
    assert results[0].genes == ("G1", "G2", "G3")


def test_query_must_be_within_universe():
    try:
        enrich({"NOT_TESTED"}, {"G1"}, [])
    except ValueError as error:
        assert "NOT_TESTED" in str(error)
    else:
        raise AssertionError("Expected invalid universe to fail")


def test_zero_overlap_terms_are_in_fdr_denominator():
    universe = {f"G{index}" for index in range(1, 21)}
    query = {"G1", "G2", "G3"}
    sets = [GeneSet("HIT", "Hit", "demo", frozenset(query))]
    sets.extend(
        GeneSet(f"ZERO-{index}", "No overlap", "demo", frozenset({f"G{index}"}))
        for index in range(4, 14)
    )
    result = enrich(query, universe, sets)[0]
    assert result.fdr == min(1.0, result.p_value * len(sets))
    assert len(enrich(query, universe, sets, min_overlap=0)) == len(sets)
