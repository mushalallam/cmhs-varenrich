import json
from pathlib import Path

from varenrich.resources import (
    build_clinvar_disease_sets,
    build_go_gene_sets,
    build_hpo_gene_sets,
    build_mapping_gene_sets,
    build_reactome_gene_sets,
    write_gmt,
    write_resource_manifest,
)

EXAMPLES = Path(__file__).parents[1] / "examples"


def test_go_build_propagates_to_parent():
    sets = build_go_gene_sets(EXAMPLES / "mini-human.gaf", EXAMPLES / "mini-go.obo")
    by_id = {item.identifier: item for item in sets}
    assert by_id["GO:0006575"].genes == {"PAH"}
    assert by_id["GO:0008150"].genes == {"PAH"}


def test_mapping_and_manifest(tmp_path):
    sets = build_mapping_gene_sets(EXAMPLES / "demo-mapping.tsv")
    assert {item.source for item in sets} == {"Disease", "Pathway"}
    output = write_gmt(sets, tmp_path / "annotations.gmt")
    manifest = write_resource_manifest(
        [EXAMPLES / "demo-mapping.tsv"], output, tmp_path / "manifest.json"
    )
    data = json.loads(manifest.read_text())
    assert len(data["inputs"][0]["sha256"]) == 64


def test_official_hpo_and_clinvar_adapters():
    hpo = build_hpo_gene_sets(EXAMPLES / "mini-hpo.tsv")
    assert hpo[0].genes == {"PAH", "GCH1"}
    diseases = build_clinvar_disease_sets(EXAMPLES / "mini-clinvar-gene-conditions.tsv")
    by_id = {item.identifier: item for item in diseases}
    assert by_id["MONDO:0018481"].genes == {"PAH"}
    assert by_id["MONDO:0019180"].genes == {"GCH1", "QDPR"}


def test_reactome_adapter_maps_uniprot_and_filters_human():
    sets = build_reactome_gene_sets(EXAMPLES / "mini-reactome.tsv", EXAMPLES / "mini-human.gaf")
    assert len(sets) == 1
    assert sets[0].identifier == "R-HSA-1474151"
    assert sets[0].genes == {"PAH"}
