"""Strict, friendly readers for gene, variant, universe, and annotation files."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import GeneSet, VariantRecord

GENE_COLUMNS = ("gene", "gene_symbol", "symbol", "hgnc_symbol")


def normalize_gene(value: str) -> str:
    return value.strip().upper()


def read_gene_list(path: str | Path) -> set[str]:
    genes: set[str] = set()
    with Path(path).open(encoding="utf-8-sig") as handle:
        for line in handle:
            value = line.split("#", 1)[0].strip().split("\t", 1)[0].split(",", 1)[0]
            if value and value.lower() not in GENE_COLUMNS:
                genes.add(normalize_gene(value))
    if not genes:
        raise ValueError(f"No genes found in {path}")
    return genes


def read_variant_table(path: str | Path) -> list[VariantRecord]:
    file_path = Path(path)
    with file_path.open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
        reader = csv.DictReader(handle, dialect=dialect)
        headings = {heading.strip().lower(): heading for heading in (reader.fieldnames or [])}
        gene_key = next((headings[key] for key in GENE_COLUMNS if key in headings), None)
        if gene_key is None:
            raise ValueError(f"Variant table requires one of these columns: {', '.join(GENE_COLUMNS)}")

        def value(row: dict[str, str], *names: str) -> str:
            key = next((headings[name] for name in names if name in headings), None)
            return (row.get(key, "") if key else "").strip()

        records = [
            VariantRecord(
                gene=normalize_gene(row.get(gene_key, "")),
                variant=value(row, "variant", "hgvs", "hgvsc", "hgvsp"),
                consequence=value(row, "consequence", "effect"),
                classification=value(row, "classification", "clinical_significance"),
                disease=value(row, "disease", "condition", "phenotype"),
                sample=value(row, "sample", "sample_id"),
            )
            for row in reader
            if normalize_gene(row.get(gene_key, ""))
        ]
    if not records:
        raise ValueError(f"No variant records found in {path}")
    return records


def read_gene_sets(path: str | Path) -> list[GeneSet]:
    """Read GMT: set ID, description/name, then one or more gene symbols."""
    sets: list[GeneSet] = []
    with Path(path).open(encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip() or line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 3:
                raise ValueError(f"Invalid GMT row {line_number}: expected at least 3 columns")
            identifier = fields[0].strip()
            descriptor = fields[1].strip()
            source, separator, name = descriptor.partition("|")
            genes = frozenset(normalize_gene(gene) for gene in fields[2:] if normalize_gene(gene))
            sets.append(
                GeneSet(
                    identifier=identifier,
                    name=name if separator else descriptor,
                    source=source if separator else "custom",
                    genes=genes,
                )
            )
    if not sets:
        raise ValueError(f"No gene sets found in {path}")
    return sets

