"""Strict, friendly readers for gene, variant, universe, and annotation files."""

from __future__ import annotations

import csv
import gzip
import re
from collections.abc import Iterator
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
            raise ValueError(
                f"Variant table requires one of these columns: {', '.join(GENE_COLUMNS)}"
            )

        def value(row: dict[str, str], *names: str) -> str:
            key = next((headings[name] for name in names if name in headings), None)
            return (row.get(key, "") if key else "").strip()

        records = [
            VariantRecord(
                gene=normalize_gene(row.get(gene_key, "")),
                variant=value(row, "variant", "hgvs", "hgvsc", "hgvsp"),
                chromosome=value(row, "chromosome", "chrom", "chr"),
                position=_optional_int(value(row, "position", "pos")),
                reference=value(row, "reference", "ref"),
                alternate=value(row, "alternate", "alt"),
                consequence=value(row, "consequence", "effect"),
                classification=value(row, "classification", "clinical_significance"),
                disease=value(row, "disease", "condition", "phenotype"),
                sample=value(row, "sample", "sample_id"),
                quality=_optional_float(value(row, "quality", "qual")),
                filter_status=value(row, "filter", "filter_status"),
                allele_frequency=_optional_float(value(row, "allele_frequency", "af", "gnomad_af")),
                zygosity=value(row, "zygosity", "genotype", "gt"),
            )
            for row in reader
            if normalize_gene(row.get(gene_key, ""))
        ]
    if not records:
        raise ValueError(f"No variant records found in {path}")
    return records


def _optional_float(value: str) -> float | None:
    if not value or value in {".", "NA", "N/A"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _optional_int(value: str) -> int | None:
    parsed = _optional_float(value)
    return int(parsed) if parsed is not None else None


def _open_text(path: Path):
    return (
        gzip.open(path, "rt", encoding="utf-8")
        if path.suffix == ".gz"
        else path.open(encoding="utf-8")
    )


def _info_map(field: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in field.split(";"):
        key, separator, value = item.partition("=")
        values[key] = value if separator else "true"
    return values


def _annotation_fields(header: str) -> list[str]:
    patterns = (
        r"Format:\s*([^\">]+)",
        r"Functional annotations:\s*'([^']+)'",
    )
    for pattern in patterns:
        match = re.search(pattern, header)
        if match:
            return [field.strip() for field in match.group(1).split("|")]
    return []


def _sample_zygosity(format_field: str, sample_field: str) -> str:
    keys = format_field.split(":")
    values = sample_field.split(":")
    genotype = values[keys.index("GT")] if "GT" in keys and keys.index("GT") < len(values) else ""
    alleles = re.split(r"[/|]", genotype)
    called = [allele for allele in alleles if allele not in {"", "."}]
    if not called:
        return "unknown"
    if all(allele == "0" for allele in called):
        return "reference"
    if len(set(called)) == 1:
        return "hemizygous" if len(called) == 1 else "homozygous"
    return "heterozygous"


def _annotated_genes(
    info: dict[str, str], annotation_formats: dict[str, list[str]]
) -> Iterator[tuple[str, str, str]]:
    """Yield gene, consequence, and HGVS from common VEP/SnpEff annotations."""
    for key in ("CSQ", "ANN"):
        if key not in info:
            continue
        fields = annotation_formats.get(key, [])
        for entry in info[key].split(","):
            values = entry.split("|")
            annotation = dict(zip(fields, values))
            gene = (
                annotation.get("SYMBOL")
                or annotation.get("Gene_Name")
                or annotation.get("Gene")
                or ""
            )
            consequence = annotation.get("Consequence") or annotation.get("Annotation") or ""
            hgvs = (
                annotation.get("HGVSc") or annotation.get("HGVS.c") or annotation.get("HGVSp") or ""
            )
            if gene:
                yield normalize_gene(gene), consequence, hgvs
        return
    genes = info.get("GENE") or info.get("SYMBOL") or info.get("Gene.refGene") or ""
    consequence = info.get("CONSEQUENCE") or info.get("ExonicFunc.refGene") or ""
    for gene in re.split(r"[,;]", genes):
        if gene.strip():
            yield normalize_gene(gene), consequence, ""


def read_vcf(path: str | Path) -> list[VariantRecord]:
    """Read a locally annotated VCF/VCF.GZ without transmitting data.

    Gene symbols are obtained from VEP ``CSQ``, SnpEff ``ANN``, or INFO fields
    named ``GENE``, ``SYMBOL``, or ``Gene.refGene``.
    """
    file_path = Path(path)
    annotation_formats: dict[str, list[str]] = {}
    records: list[VariantRecord] = []
    sample_names: list[str] = []
    with _open_text(file_path) as handle:
        for line_number, line in enumerate(handle, 1):
            if line.startswith("##INFO=<ID=CSQ"):
                annotation_formats["CSQ"] = _annotation_fields(line)
            elif line.startswith("##INFO=<ID=ANN"):
                annotation_formats["ANN"] = _annotation_fields(line)
            elif line.startswith("#CHROM"):
                sample_names = line.rstrip("\n").split("\t")[9:]
            elif line.startswith("#") or not line.strip():
                continue
            else:
                columns = line.rstrip("\n").split("\t")
                if len(columns) < 8:
                    raise ValueError(f"Invalid VCF row {line_number}: expected at least 8 columns")
                chrom, position, identifier, reference, alternates, quality, status, raw_info = (
                    columns[:8]
                )
                info = _info_map(raw_info)
                annotations = list(_annotated_genes(info, annotation_formats))
                if not annotations:
                    continue
                allele_frequency = _optional_float(
                    (info.get("gnomAD_AF") or info.get("AF") or info.get("MAX_AF") or "").split(
                        ","
                    )[0]
                )
                samples = list(zip(sample_names, columns[9:], strict=False)) or [("", "")]
                format_field = columns[8] if len(columns) > 8 else ""
                for gene, consequence, hgvs in annotations:
                    for sample_name, sample_value in samples:
                        zygosity = (
                            _sample_zygosity(format_field, sample_value) if sample_value else ""
                        )
                        if sample_value and zygosity in {"reference", "unknown"}:
                            continue
                        records.append(
                            VariantRecord(
                                gene=gene,
                                variant=(
                                    hgvs
                                    or (identifier if identifier != "." else "")
                                    or f"{chrom}:{position}:{reference}>{alternates}"
                                ),
                                chromosome=chrom,
                                position=int(position),
                                reference=reference,
                                alternate=alternates,
                                consequence=consequence,
                                classification=info.get("CLNSIG", "").replace("_", " "),
                                disease=info.get("CLNDN", "").replace("_", " "),
                                sample=sample_name,
                                quality=_optional_float(quality),
                                filter_status=status,
                                allele_frequency=allele_frequency,
                                zygosity=zygosity,
                            )
                        )
    if not records:
        raise ValueError(
            f"No gene-annotated variants found in {path}; annotate with VEP/SnpEff or add a GENE INFO field"
        )
    return records


def filter_variants(
    records: list[VariantRecord],
    *,
    min_quality: float | None = None,
    max_allele_frequency: float | None = None,
    pass_only: bool = False,
    classifications: set[str] | None = None,
) -> list[VariantRecord]:
    wanted = {value.casefold() for value in classifications or set()}
    kept = []
    for record in records:
        if min_quality is not None and (record.quality is None or record.quality < min_quality):
            continue
        if max_allele_frequency is not None and (
            record.allele_frequency is not None and record.allele_frequency > max_allele_frequency
        ):
            continue
        if pass_only and record.filter_status not in {"", ".", "PASS"}:
            continue
        if wanted and not any(value in record.classification.casefold() for value in wanted):
            continue
        kept.append(record)
    return kept


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
