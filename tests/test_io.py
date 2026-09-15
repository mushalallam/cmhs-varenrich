from pathlib import Path

from varenrich.io import read_gene_list, read_gene_sets, read_variant_table

EXAMPLES = Path(__file__).parents[1] / "examples"


def test_example_inputs_are_readable():
    assert "PAH" in read_gene_list(EXAMPLES / "demo-universe.txt")
    records = read_variant_table(EXAMPLES / "demo-variants.tsv")
    assert {record.gene for record in records} == {"PAH", "GCH1", "QDPR"}
    sets = read_gene_sets(EXAMPLES / "demo-gene-sets.gmt")
    assert sets[0].source == "Disease"


def test_variant_table_accepts_windows_newlines(tmp_path):
    table = tmp_path / "variants.tsv"
    table.write_bytes(b"gene\tvariant\r\nPAH\tc.1A>G\r\nQDPR\tc.2C>T\r\n")
    assert [record.gene for record in read_variant_table(table)] == ["PAH", "QDPR"]
