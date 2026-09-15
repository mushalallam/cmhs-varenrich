# Statistical methods

## Over-representation test

For each annotation term, CMHS VarEnrich constructs this 2×2 table after intersecting the term with the user-provided gene universe:

| | In term | Not in term |
|---|---:|---:|
| Query genes | a | b |
| Other universe genes | c | d |

The reported p-value is the one-sided Fisher/hypergeometric probability of observing at least `a` term genes in a query of the same size:

`P(X ≥ a)`, where `X ~ Hypergeometric(N, K, n)`.

Here `N` is the universe size, `K` the term size inside that universe, and `n` the query size. Probabilities are evaluated in log space using `lgamma` to remain stable for human-genome-sized counts.

All annotation terms containing at least one universe gene are included in the Benjamini–Hochberg multiple-testing correction, including terms with zero query overlap. `--min-overlap` controls display only; it does not reduce the FDR denominator.

The report includes expected overlap, fold enrichment, the sample odds ratio, and an approximate 95% odds-ratio confidence interval. A 0.5 Haldane–Anscombe correction is used for the interval when any table cell is zero. This interval is descriptive; the exact one-sided p-value is the inferential test.

## Background-universe requirement

The universe must contain every gene that had a genuine opportunity to enter the query after assay and analysis QC. Examples include adequately covered genes on a diagnostic panel or genes passing exome-wide coverage criteria. Using all human genes for a small panel changes the null hypothesis and generally inflates apparent enrichment.

Query genes outside the universe cause analysis to stop rather than being silently discarded.

## Annotation processing

- GO annotations marked with the `NOT` qualifier are excluded.
- GO terms can be propagated through `is_a` and `part_of` ancestors using a matching OBO file.
- Obsolete GO terms are excluded.
- HPO uses `genes_to_phenotype.txt` gene–phenotype relationships.
- Reactome human pathways are mapped from UniProt identifiers using the accompanying human GO GAF.
- ClinVar gene-condition relationships are grouped by source identifier or MedGen concept identifier.
- Every generated annotation collection has a SHA-256 resource manifest.

## Boundaries

This method tests over-representation in an unranked gene list. It does not correct case-control rare-variant analyses for ancestry, coverage, relatedness, gene length, or variant mutability. A cohort burden workflow must use a separate model with those covariates.

Enrichment does not prove that a variant is pathogenic, that a gene causes the phenotype, or that a patient has a disease.
