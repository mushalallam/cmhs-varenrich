"""Explicit downloader for public human annotation sources (never patient data)."""

from __future__ import annotations

import shutil
from pathlib import Path
from urllib.request import Request, urlopen

from .resources import (
    build_clinvar_disease_sets,
    build_go_gene_sets,
    build_hpo_gene_sets,
    build_reactome_gene_sets,
    write_gmt,
    write_resource_manifest,
)

SOURCES = {
    "go_obo": "https://current.geneontology.org/ontology/go-basic.obo",
    "go_gaf": "https://current.geneontology.org/annotations/gaf/HUMAN-uniprot.gaf.gz",
    "hpo": "https://github.com/obophenotype/human-phenotype-ontology/releases/latest/download/genes_to_phenotype.txt",
    "clinvar": "https://ftp.ncbi.nlm.nih.gov/pub/clinvar/gene_condition_source_id",
    "reactome": "https://reactome.org/download/current/UniProt2Reactome_All_Levels.txt",
}


def download_file(url: str, path: Path) -> Path:
    request = Request(url, headers={"User-Agent": "CMHS-VarEnrich/0.1 (+research software)"})
    partial = path.with_suffix(path.suffix + ".partial")
    with urlopen(request, timeout=120) as response, partial.open("wb") as output:
        shutil.copyfileobj(response, output)
    partial.replace(path)
    return path


def download_human_annotations(directory: str | Path) -> tuple[Path, Path]:
    """Download public sources and create a checksummed, local combined GMT."""
    destination = Path(directory)
    raw = destination / "source-files"
    raw.mkdir(parents=True, exist_ok=True)
    filenames = {
        "go_obo": "go-basic.obo",
        "go_gaf": "HUMAN-uniprot.gaf.gz",
        "hpo": "genes_to_phenotype.txt",
        "clinvar": "gene_condition_source_id.tsv",
        "reactome": "UniProt2Reactome_All_Levels.txt",
    }
    paths = {key: download_file(url, raw / filenames[key]) for key, url in SOURCES.items()}
    sets = []
    sets.extend(build_go_gene_sets(paths["go_gaf"], paths["go_obo"]))
    sets.extend(build_hpo_gene_sets(paths["hpo"]))
    sets.extend(build_clinvar_disease_sets(paths["clinvar"]))
    sets.extend(build_reactome_gene_sets(paths["reactome"], paths["go_gaf"]))
    output = write_gmt(sets, destination / "human-annotations.gmt")
    manifest = write_resource_manifest(
        list(paths.values()),
        output,
        destination / "human-annotations.manifest.json",
        source_urls=SOURCES,
    )
    return output, manifest
