# CMHS VarEnrich

**Human rare-variant enrichment and interactive visualization**

CMHS VarEnrich connects variants to genes and tests whether the affected genes are over-represented in rare diseases, phenotypes, pathways, or Gene Ontology categories. It produces a searchable, self-contained HTML report and publication-ready SVG graphics without uploading patient data.

> **Development status:** early preview. Not validated for diagnosis or clinical decision-making.

## Why it is different

- Keeps the path from variant → gene → enriched term → statistical evidence traceable.
- Requires an explicit background universe, such as all genes on the panel or all genes that passed analysis QC.
- Reports one-sided hypergeometric p-values, Benjamini–Hochberg FDR, fold enrichment, and contributing genes.
- Accepts simple gene lists and CSV/TSV variant tables.
- Generates a local interactive report with no external JavaScript or patient-data upload.
- Designed to grow into WEGO-style ontology views and cohort rare-variant burden analysis.

## Try the synthetic demonstration

Python 3.10 or newer is required during early development.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e .

varenrich analyse \
  --variants examples/demo-variants.tsv \
  --universe examples/demo-universe.txt \
  --gene-sets examples/demo-gene-sets.gmt \
  --output demo-results
```

Open `demo-results/report.html`. The bundled demonstration is entirely synthetic and contains no patient information.

## Inputs

### Gene list

One HGNC gene symbol per line. A header named `gene`, `gene_symbol`, `symbol`, or `hgnc_symbol` is allowed.

### Variant table

A comma-, tab-, or semicolon-delimited table containing a gene column. Optional columns currently retained for traceability include `variant`, `consequence`, `classification`, `disease`, and `sample`.

### Background universe

One gene per line representing **every gene that could have entered the query list**. For a clinical panel analysis, this is normally the adequately tested panel genes. Using every human gene for a small targeted panel creates biased p-values.

### Annotation collection

GMT format: term identifier, `Source|Term name`, then gene symbols, separated by tabs.

```text
HP:0001250	HPO|Seizure	SCN1A	SCN2A	STXBP1
```

## Outputs

- `report.html`: self-contained interactive report and embedded SVG chart
- `enrichment-results.tsv`: complete machine-readable results
- `analysis-metadata.json`: method, version, input type, universe size, and resource paths

## Statistical scope

The current method is over-representation analysis for an unranked gene list. It is not a replacement for ancestry-aware, coverage-aware case-control rare-variant burden testing. Those models are planned as a distinct workflow so their assumptions cannot be confused with a hypergeometric test.

## Privacy and clinical use

Analysis runs locally. The program does not make network requests. Inputs may still contain identifiable sample labels, so outputs must be handled under the same institutional controls as the source data.

CMHS VarEnrich is research software. ClinVar and other public resources contain submitted interpretations that require expert review; enrichment significance does not establish pathogenicity, causality, or diagnosis.

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for planned versioned annotations, phenotype-aware analysis, interactive ontology trees, VCF support, and cross-platform applications.

## License

MIT © Human Genomics Solutions. External annotation databases retain their own licenses and attribution requirements.

