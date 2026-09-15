# Public annotation sources

`varenrich download-resources` retrieves only these public annotation files:

| Collection | File used | Purpose | Upstream terms |
|---|---|---|---|
| Gene Ontology | `go-basic.obo` and human UniProt GAF | GO hierarchy, names, and human gene annotations | CC BY 4.0; attribution and release identification required |
| Human Phenotype Ontology | `genes_to_phenotype.txt` | Human gene–phenotype relationships | Free with HPO acknowledgement, citation, and visible version/date; source files must not be altered |
| ClinVar | `gene_condition_source_id` | Human gene–condition relationships and MONDO/other source identifiers | Freely available; ClinVar requests attribution |
| Reactome | `UniProt2Reactome_All_Levels.txt` | Curated human pathway membership | Database data and derived files are CC0; attribution encouraged |

Source URLs are defined in `src/varenrich/download.py` and written into every downloaded-bundle manifest. The manifest also records retrieval time, byte size, and SHA-256 digest for every source and the combined GMT. Resources never change during an analysis and are never updated implicitly.

The downloader uses:

- [Gene Ontology downloads](https://geneontology.org/docs/download-go-annotations/) and [GO license/citation policy](https://geneontology.org/docs/go-citation-policy/)
- [Human Phenotype Ontology](https://hpo.jax.org/data/ontology) and [HPO license](https://human-phenotype-ontology.github.io/license.html)
- [ClinVar downloads](https://www.ncbi.nlm.nih.gov/clinvar/docs/downloads/) and [data-use policy](https://www.ncbi.nlm.nih.gov/clinvar/docs/maintenance_use/)
- [Reactome downloads](https://reactome.org/download-data) and [Reactome license](https://reactome.org/license)

CMHS VarEnrich does not redistribute a combined copy of these databases. Each user explicitly downloads the original current files from their maintainers and receives a local derived analysis collection plus provenance manifest. Users must cite the upstream resources and review their current terms when publishing results. ClinVar explicitly states that its information is not intended for direct diagnostic use without genetics-professional review; CMHS VarEnrich preserves that boundary.
