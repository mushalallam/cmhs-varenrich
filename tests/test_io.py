from pathlib import Path

from varenrich.io import read_gene_list, read_gene_sets, read_variant_table

EXAMPLES = Path(__file__).parents[1] / "examples"


def test_example_inputs_are_readable():
    assert "PAH" in read_gene_list(EXAMPLES / "demo-universe.txt")
    records = read_variant_table(EXAMPLES / "demo-variants.tsv")
    assert {record.gene for record in records} == {"PAH", "GCH1", "QDPR"}
    sets = read_gene_sets(EXAMPLES / "demo-gene-sets.gmt")
    assert sets[0].source == "Disease"
