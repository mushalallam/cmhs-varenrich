# Development roadmap

## 0.1 — release MVP

- Gene-list and delimited variant-table input
- Explicit tested-gene universe
- Hypergeometric over-representation analysis and BH-FDR
- Custom GMT annotations
- Searchable HTML, SVG, TSV, and analysis metadata
- Synthetic rare-disease demonstration and automated tests
- Reproducible, version-pinned GO human annotations
- Reactome pathway mappings
- HPO and ClinVar/MONDO gene-condition mappings
- Resource manifests with source URL and SHA-256 checksums
- VCF/VCF.GZ input for GRCh37 and GRCh38
- Allele-frequency, consequence, classification, quality, zygosity, and inheritance filters
- Variant-to-gene-to-term evidence table
- Offline-first operation with an explicit, auditable database update command
- Local browser interface with drag-and-drop inputs
- Bar and bubble plots, searchable results, and evidence tables
- SVG, TSV, and self-contained HTML export
- Standalone cross-platform build automation

## 0.2 — identifier and visualization expansion

- HGNC identifier normalization and retired-symbol warnings
- Orphanet and ClinGen/GenCC mappings where licensing permits
- Automated extraction of upstream release versions and license metadata into manifests
- Multi-allelic normalization and transcript-aware annotation import
- WEGO-like interactive GO hierarchy and multi-cohort comparison
- UpSet, heatmap, disease–gene–variant network, and pathway plots
- PDF, PNG, and Excel export
- One-click signed applications for macOS and Windows plus Linux packages

## 1.0 — validation and reproducibility

- Independent numerical validation against established implementations
- Golden datasets and cross-platform acceptance tests
- Full provenance, parameter manifests, and deterministic reports
- Documented clinical boundaries and security/privacy review
- Separate coverage- and ancestry-aware rare-variant burden workflow for cohorts
