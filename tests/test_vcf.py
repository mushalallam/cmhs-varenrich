from pathlib import Path

from varenrich.io import filter_variants, read_vcf

EXAMPLES = Path(__file__).parents[1] / "examples"


def test_read_vcf_and_filter_variants():
    records = read_vcf(EXAMPLES / "demo-annotated.vcf")
    assert {record.gene for record in records} == {"PAH", "GCH1", "QDPR"}
    assert records[0].zygosity == "heterozygous"
    assert records[0].quality == 99
    kept = filter_variants(records, min_quality=30, max_allele_frequency=0.001, pass_only=True)
    assert {record.gene for record in kept} == {"PAH", "GCH1"}


def test_pathogenic_text_filter():
    records = read_vcf(EXAMPLES / "demo-annotated.vcf")
    kept = filter_variants(records, classifications={"pathogenic"})
    assert {record.gene for record in kept} == {"PAH", "QDPR"}


def test_reference_genotype_is_not_returned(tmp_path):
    source = (EXAMPLES / "demo-annotated.vcf").read_text()
    source = source.replace("0/1\n", "0/0\n", 1)
    path = tmp_path / "reference.vcf"
    path.write_text(source)
    assert "PAH" not in {record.gene for record in read_vcf(path)}
