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

