"""Reproducible builders for local human annotation collections."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .io import normalize_gene
from .models import GeneSet


def _open_text(path: Path):
    return (
        gzip.open(path, "rt", encoding="utf-8")
        if path.suffix == ".gz"
        else path.open(encoding="utf-8")
    )


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_obo(path: str | Path) -> dict[str, dict[str, object]]:
    """Read the term fields needed for enrichment and ancestor propagation."""
    terms: dict[str, dict[str, object]] = {}
    current: dict[str, object] | None = None
    with _open_text(Path(path)) as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if line == "[Term]":
                if current and "id" in current and not current.get("obsolete"):
                    terms[str(current["id"])] = current
                current = {"parents": set()}
            elif line.startswith("["):
                if current and "id" in current and not current.get("obsolete"):
                    terms[str(current["id"])] = current
                current = None
            elif current is not None:
                key, separator, value = line.partition(": ")
                if not separator:
                    continue
                if key in {"id", "name", "namespace"}:
                    current[key] = value
                elif key == "is_a":
                    current["parents"].add(value.split()[0])  # type: ignore[union-attr]
                elif key == "relationship" and value.startswith("part_of "):
                    current["parents"].add(value.split()[1])  # type: ignore[union-attr]
                elif key == "is_obsolete" and value == "true":
                    current["obsolete"] = True
    if current and "id" in current and not current.get("obsolete"):
        terms[str(current["id"])] = current
    return terms


def _ancestors(
    term_id: str, terms: dict[str, dict[str, object]], memo: dict[str, set[str]]
) -> set[str]:
    if term_id in memo:
        return memo[term_id]
    parents = set(terms.get(term_id, {}).get("parents", set()))
    result = set(parents)
    memo[term_id] = result
    for parent in parents:
        result.update(_ancestors(parent, terms, memo))
    return result


def build_go_gene_sets(
    gaf_path: str | Path, obo_path: str | Path, *, propagate: bool = True
) -> list[GeneSet]:
    """Build GO sets from an official GAF and matching OBO release."""
    terms = read_obo(obo_path)
    annotations: dict[str, set[str]] = defaultdict(set)
    memo: dict[str, set[str]] = {}
    with _open_text(Path(gaf_path)) as handle:
        for line in handle:
            if line.startswith("!") or not line.strip():
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 5:
                continue
            qualifier = fields[3].split("|")
            if "NOT" in qualifier:
                continue
            gene, term_id = normalize_gene(fields[2]), fields[4]
            if not gene or term_id not in terms:
                continue
            annotations[term_id].add(gene)
            if propagate:
                for ancestor in _ancestors(term_id, terms, memo):
                    annotations[ancestor].add(gene)
    return [
        GeneSet(
            identifier=term_id,
            name=str(terms[term_id].get("name", term_id)),
            source=f"GO:{str(terms[term_id].get('namespace', 'unknown')).replace('_', ' ')}",
            genes=frozenset(genes),
        )
        for term_id, genes in annotations.items()
        if genes
    ]


def build_mapping_gene_sets(path: str | Path) -> list[GeneSet]:
    """Build sets from a CSV/TSV with gene, term_id, term_name, and optional source columns."""
    groups: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        reader = csv.DictReader(handle, dialect=dialect)
        headings = {heading.lower().strip(): heading for heading in reader.fieldnames or []}
        required = {"gene", "term_id", "term_name"}
        if not required <= headings.keys():
            raise ValueError(f"Mapping file requires columns: {', '.join(sorted(required))}")
        for row in reader:
            gene = normalize_gene(row[headings["gene"]])
            term_id = row[headings["term_id"]].strip()
            term_name = row[headings["term_name"]].strip()
            source = row.get(headings.get("source", ""), "custom").strip() or "custom"
            if gene and term_id:
                groups[(source, term_id, term_name)].add(gene)
    return [
        GeneSet(term_id, term_name, source, frozenset(genes))
        for (source, term_id, term_name), genes in groups.items()
    ]


def build_hpo_gene_sets(path: str | Path) -> list[GeneSet]:
    """Build phenotype sets from the HPO ``genes_to_phenotype.txt`` release file."""
    groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    with _open_text(Path(path)) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"gene_symbol", "hpo_id", "hpo_name"}
        if not required <= set(reader.fieldnames or []):
            raise ValueError("HPO file requires gene_symbol, hpo_id, and hpo_name columns")
        for row in reader:
            gene = normalize_gene(row["gene_symbol"])
            if gene and row["hpo_id"]:
                groups[(row["hpo_id"], row["hpo_name"])].add(gene)
    return [
        GeneSet(term_id, name, "HPO", frozenset(genes)) for (term_id, name), genes in groups.items()
    ]


def build_clinvar_disease_sets(path: str | Path) -> list[GeneSet]:
    """Build disease sets from ClinVar's daily ``gene_condition_source_id`` file."""
    groups: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    with _open_text(Path(path)) as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames:
            reader.fieldnames = [name.removeprefix("#") for name in reader.fieldnames]
        required = {"AssociatedGenes", "ConceptID", "DiseaseName", "SourceName", "SourceID"}
        if not required <= set(reader.fieldnames or []):
            raise ValueError("Unrecognized ClinVar gene_condition_source_id columns")
        for row in reader:
            term_id = row["SourceID"] or row["ConceptID"]
            source = f"ClinVar:{row['SourceName'] or 'condition'}"
            genes = re_split_genes(row["AssociatedGenes"] + "," + row.get("RelatedGenes", ""))
            if term_id:
                groups[(source, term_id, row["DiseaseName"])].update(genes)
    return [
        GeneSet(term_id, name, source, frozenset(genes))
        for (source, term_id, name), genes in groups.items()
        if genes
    ]


def build_reactome_gene_sets(path: str | Path, gaf_path: str | Path) -> list[GeneSet]:
    """Build human Reactome sets using UniProt identifiers mapped by a human GO GAF."""
    symbols: dict[str, str] = {}
    with _open_text(Path(gaf_path)) as handle:
        for line in handle:
            if line.startswith("!"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) >= 3:
                symbols[fields[1]] = normalize_gene(fields[2])
    groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    with _open_text(Path(path)) as handle:
        for line in handle:
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 6 or fields[5] != "Homo sapiens":
                continue
            gene = symbols.get(fields[0])
            if gene:
                groups[(fields[1], fields[3])].add(gene)
    return [
        GeneSet(term_id, name, "Reactome", frozenset(genes))
        for (term_id, name), genes in groups.items()
    ]


def re_split_genes(value: str) -> set[str]:
    return {
        normalize_gene(gene)
        for piece in value.replace(";", ",").split(",")
        if (gene := piece.strip())
    }


def write_gmt(gene_sets: list[GeneSet], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        for gene_set in sorted(gene_sets, key=lambda item: (item.source, item.identifier)):
            fields = [
                gene_set.identifier,
                f"{gene_set.source}|{gene_set.name}",
                *sorted(gene_set.genes),
            ]
            handle.write("\t".join(fields) + "\n")
    return output


def write_resource_manifest(
    inputs: list[str | Path],
    output_gmt: Path,
    path: str | Path,
    *,
    source_urls: dict[str, str] | None = None,
    source_metadata: dict[str, object] | None = None,
) -> Path:
    manifest = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "builder": "CMHS VarEnrich",
        "source_urls": source_urls or {},
        "source_metadata": source_metadata or {},
        "inputs": [
            {
                "filename": Path(item).name,
                "sha256": sha256(item),
                "bytes": Path(item).stat().st_size,
            }
            for item in inputs
        ],
        "output": {
            "filename": output_gmt.name,
            "sha256": sha256(output_gmt),
            "bytes": output_gmt.stat().st_size,
        },
    }
    destination = Path(path)
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def resource_provenance(gmt_path: str | Path) -> dict[str, object]:
    """Return annotation provenance and verify an adjacent manifest when present."""
    gmt = Path(gmt_path)
    actual = sha256(gmt)
    provenance: dict[str, object] = {"filename": gmt.name, "sha256": actual}
    manifest_path = gmt.with_suffix(".manifest.json")
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = manifest.get("output", {}).get("sha256")
        if expected and expected != actual:
            raise ValueError(
                f"Annotation checksum does not match {manifest_path.name}; rebuild or restore the resource"
            )
        provenance["manifest"] = manifest
    return provenance
