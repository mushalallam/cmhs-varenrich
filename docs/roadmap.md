# Development roadmap

## 0.1 — statistically auditable core

- Gene-list and delimited variant-table input
- Explicit tested-gene universe
- Hypergeometric over-representation analysis and BH-FDR
- Custom GMT annotations
- Searchable HTML, SVG, TSV, and analysis metadata
- Synthetic rare-disease demonstration and automated tests

## 0.2 — human annotation bundles

- Reproducible, version-pinned GO human annotations
- Reactome pathway mappings
- HPO, MONDO, Orphanet, ClinGen/GenCC, and ClinVar gene-condition mappings where licensing permits
- HGNC identifier normalization and retired-symbol warnings
- Resource manifests with source URL, release date, license, checksum, and genome assembly

## 0.3 — variant workflow

- VCF/VCF.GZ input for GRCh37 and GRCh38
- Multi-allelic normalization and transcript-aware annotation import
- Allele-frequency, consequence, classification, quality, zygosity, and inheritance filters
- Variant-to-gene-to-term evidence table
- Offline-first operation with an explicit, auditable database update command

## 0.4 — interactive application

- Local browser interface with drag-and-drop inputs
- WEGO-like GO hierarchy and multi-cohort comparison
- Bubble, UpSet, heatmap, disease–gene–variant network, and pathway plots
- SVG, PDF, PNG, Excel, and self-contained HTML export
- One-click signed applications for macOS and Windows plus Linux packages

## 1.0 — validation and reproducibility

- Independent numerical validation against established implementations
- Golden datasets and cross-platform acceptance tests
- Full provenance, parameter manifests, and deterministic reports
- Documented clinical boundaries and security/privacy review
- Separate coverage- and ancestry-aware rare-variant burden workflow for cohorts

