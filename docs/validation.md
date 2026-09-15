# Validation record

## Statistical implementation

The dependency-free log-space hypergeometric survival function is checked against `scipy.stats.hypergeom.sf` in 1,000 deterministic random valid 2×2 configurations with universe sizes up to 5,000.

On 15 September 2026, the reproducible comparison completed with a maximum absolute difference of approximately `1.82 × 10⁻¹¹`, below the acceptance threshold of `1 × 10⁻¹⁰`. GitHub Actions repeats this check on each push and pull request.

Unit tests separately cover known combinatorial probabilities, boundary values, invalid tables, BH-FDR monotonicity, zero-overlap terms in the multiple-testing denominator, odds-ratio calculation, query-universe enforcement, and report generation.

## Workflow checks

Tests cover gene-list, delimited variant-table, annotated VCF, genotype exclusion, filters, GO ancestor propagation, HPO/ClinVar/Reactome adapters, checksum manifests, the token-protected loopback GUI, full GUI submission, CLI outputs, and SVG export.

Standalone smoke testing runs version, installation diagnosis, GUI-locality, and an actual VCF-to-HTML analysis against the compiled executable.

## Remaining validation boundary

This validation establishes software consistency for the documented enrichment calculation. It does not constitute clinical validation and does not independently validate upstream disease or functional annotations.
