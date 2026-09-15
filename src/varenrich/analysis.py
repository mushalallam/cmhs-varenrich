"""Over-representation analysis with an explicit, defensible gene universe."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .models import GeneSet
from .statistics import benjamini_hochberg, hypergeom_survival


@dataclass(frozen=True)
class EnrichmentResult:
    term_id: str
    term_name: str
    source: str
    overlap: int
    query_size: int
    term_size: int
    universe_size: int
    expected: float
    fold_enrichment: float
    p_value: float
    fdr: float
    genes: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def enrich(
    query_genes: set[str],
    universe_genes: set[str],
    gene_sets: list[GeneSet],
    *,
    min_overlap: int = 1,
) -> list[EnrichmentResult]:
    """Run one-sided hypergeometric over-representation analysis."""
    if not universe_genes:
        raise ValueError("The background universe cannot be empty")
    outside = query_genes - universe_genes
    if outside:
        preview = ", ".join(sorted(outside)[:5])
        raise ValueError(f"Query genes absent from the background universe: {preview}")
    query_size = len(query_genes)
    raw: list[dict[str, object]] = []
    for gene_set in gene_sets:
        members = gene_set.genes & universe_genes
        hits = tuple(sorted(query_genes & members))
        if len(hits) < min_overlap or not members:
            continue
        expected = query_size * len(members) / len(universe_genes)
        raw.append(
            {
                "term_id": gene_set.identifier,
                "term_name": gene_set.name,
                "source": gene_set.source,
                "overlap": len(hits),
                "query_size": query_size,
                "term_size": len(members),
                "universe_size": len(universe_genes),
                "expected": expected,
                "fold_enrichment": len(hits) / expected if expected else 0.0,
                "p_value": hypergeom_survival(
                    len(hits), query_size, len(members), len(universe_genes)
                ),
                "genes": hits,
            }
        )
    adjusted = benjamini_hochberg(float(row["p_value"]) for row in raw)
    results = [EnrichmentResult(**row, fdr=fdr) for row, fdr in zip(raw, adjusted, strict=True)]
    return sorted(results, key=lambda result: (result.fdr, result.p_value, -result.overlap))
