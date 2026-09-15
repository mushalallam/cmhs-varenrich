# Public annotation sources

`varenrich download-resources` retrieves only these public annotation files:

| Collection | File used | Purpose |
|---|---|---|
| Gene Ontology | `go-basic.obo` and human UniProt GAF | GO hierarchy, names, and human gene annotations |
| Human Phenotype Ontology | `genes_to_phenotype.txt` | Human gene–phenotype relationships |
| ClinVar | `gene_condition_source_id` | Human gene–condition relationships and MONDO/other source identifiers |
| Reactome | `UniProt2Reactome_All_Levels.txt` | Curated human pathway membership |

Source URLs are defined in `src/varenrich/download.py` and written into every downloaded-bundle manifest. The manifest also records retrieval time, byte size, and SHA-256 digest for every source and the combined GMT. Resources never change during an analysis and are never updated implicitly.

The downloader uses:

- [Gene Ontology downloads](https://geneontology.org/docs/download-go-annotations/)
- [Human Phenotype Ontology](https://hpo.jax.org/data/ontology)
- [ClinVar downloads](https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/)
- [Reactome downloads](https://reactome.org/download-data)

Users must cite the upstream resources and review their current licenses and attribution instructions when publishing or redistributing a bundle. ClinVar explicitly states that its information is not intended for direct diagnostic use without genetics-professional review; CMHS VarEnrich preserves that boundary.
