import gzip
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


def test_vep_csq_vcfgz_and_multisample_genotypes(tmp_path):
    text = """##fileformat=VCFv4.2
##INFO=<ID=CSQ,Number=.,Type=String,Description="VEP annotations. Format: Allele|Consequence|IMPACT|SYMBOL|Gene|HGVSc|HGVSp">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tREF-SAMPLE\tCASE-SAMPLE
12\t1\t.\tG\tA\t80\tPASS\tCSQ=A|missense_variant|MODERATE|PAH|5053|NM_000277.3:c.1G>A|NP_000268.1:p.X\tGT\t0/0\t0/1
"""
    path = tmp_path / "vep.vcf.gz"
    with gzip.open(path, "wt") as handle:
        handle.write(text)
    records = read_vcf(path)
    assert len(records) == 1
    assert records[0].gene == "PAH"
    assert records[0].sample == "CASE-SAMPLE"
    assert records[0].variant == "NM_000277.3:c.1G>A"


def test_snpeff_ann_gene_parsing(tmp_path):
    text = """##fileformat=VCFv4.2
##INFO=<ID=ANN,Number=.,Type=String,Description="Functional annotations: 'Allele | Annotation | Annotation_Impact | Gene_Name | Gene_ID | Feature_Type | Feature_ID | Transcript_BioType | Rank | HGVS.c | HGVS.p'">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
14\t2\t.\tT\tC\t60\tPASS\tANN=C|missense_variant|MODERATE|GCH1|2643|transcript|NM_000161|protein_coding|1/6|c.2T>C|p.X
"""
    path = tmp_path / "snpeff.vcf"
    path.write_text(text)
    record = read_vcf(path)[0]
    assert record.gene == "GCH1"
    assert record.consequence == "missense_variant"
    assert record.variant == "c.2T>C"
