# CMHS VarEnrich 0.1.0

The first research release connects human variants and gene lists to GO functions, HPO phenotypes, Reactome pathways, and ClinVar disease associations through statistically auditable over-representation analysis.

## Highlights

- Gene list, CSV/TSV variant table, annotated VCF, and VCF.GZ input
- VEP `CSQ`, SnpEff `ANN`, and common gene INFO-field support
- QUAL, PASS, allele-frequency, classification, and genotype filtering
- Explicit tested-gene background universe
- Exact one-sided Fisher/hypergeometric p-values with BH-FDR
- Odds ratios, confidence intervals, and contributing genes
- One-click local build of current GO, HPO, Reactome, and ClinVar annotations
- Searchable self-contained HTML reports
- Editable SVG bar, bubble, and term–gene network figures
- Private token-protected localhost GUI
- Standalone macOS, Windows, and Linux applications plus Python wheel/source packages

## Important boundaries

CMHS VarEnrich 0.1.0 is research software and is not validated for diagnosis or clinical decision-making. It does not infer variant pathogenicity. Results must be reviewed with the underlying variant evidence, assay design, background universe, resource versions, and qualified genetics expertise.

Preview standalone applications are unsigned and can trigger macOS Gatekeeper or Windows SmartScreen. Verify the adjacent SHA-256 sidecar before following the documented platform-specific opening procedure.

## Quick start

Standalone users extract the archive for their operating system and launch **Start CMHS VarEnrich**. In the graphical interface, click **Install/update public human annotations**, choose a query and background universe, then run the analysis.

Python users can install the wheel and run `varenrich gui` or use `varenrich analyse --help`.
