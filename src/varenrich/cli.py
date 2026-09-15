"""Command-line entry point for reproducible local analyses."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from . import __version__
from .analysis import enrich
from .io import filter_variants, read_gene_list, read_gene_sets, read_variant_table, read_vcf
from .report import write_html_report, write_results_tsv, write_svg_figures, write_variants_tsv
from .resources import (
    build_clinvar_disease_sets,
    build_go_gene_sets,
    build_hpo_gene_sets,
    build_mapping_gene_sets,
    build_reactome_gene_sets,
    resource_provenance,
    sha256,
    write_gmt,
    write_resource_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="varenrich", description="Human rare-variant enrichment")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyse = subparsers.add_parser("analyse", aliases=["analyze"], help="run enrichment")
    inputs = analyse.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--genes", help="one gene symbol per line")
    inputs.add_argument("--variants", help="CSV/TSV with a gene or gene_symbol column")
    inputs.add_argument("--vcf", help="locally annotated VCF or VCF.GZ")
    analyse.add_argument(
        "--universe", required=True, help="all genes that could have been selected"
    )
    analyse.add_argument("--gene-sets", required=True, help="GMT annotation collection")
    analyse.add_argument("--output", default="varenrich-results", help="output directory")
    analyse.add_argument("--min-overlap", type=int, default=1)
    analyse.add_argument("--min-quality", type=float, help="exclude variants below this QUAL")
    analyse.add_argument(
        "--max-af", type=float, help="exclude variants above this allele frequency"
    )
    analyse.add_argument("--pass-only", action="store_true", help="retain PASS variants only")
    analyse.add_argument(
        "--classification",
        action="append",
        help="retain classifications containing this text; repeat to allow several",
    )
    analyse.add_argument(
        "--consequence",
        action="append",
        help="retain consequences containing this text; repeat to allow several",
    )
    analyse.add_argument(
        "--zygosity",
        action="append",
        choices=("heterozygous", "homozygous", "hemizygous"),
        help="retain this called zygosity; repeat to allow several",
    )
    analyse.add_argument("--title", default="CMHS VarEnrich Report")
    resources = subparsers.add_parser("build-resources", help="build a versioned local GMT bundle")
    resources.add_argument("--go-gaf", help="GO human GAF or GAF.GZ")
    resources.add_argument("--go-obo", help="matching GO OBO ontology")
    resources.add_argument("--hpo", help="HPO genes_to_phenotype.txt or .gz")
    resources.add_argument("--clinvar-diseases", help="ClinVar gene_condition_source_id file")
    resources.add_argument("--reactome", help="Reactome UniProt2Reactome_All_Levels.txt")
    resources.add_argument(
        "--mapping",
        action="append",
        default=[],
        help="CSV/TSV gene-to-term mapping; repeat for several sources",
    )
    resources.add_argument("--output", default="human-annotations.gmt")
    resources.add_argument("--no-go-propagation", action="store_true")
    gui = subparsers.add_parser("gui", help="launch the private local graphical interface")
    gui.add_argument("--no-browser", action="store_true")
    gui.add_argument("--output-root", type=Path)
    gui.add_argument("--check", action="store_true", help=argparse.SUPPRESS)
    subparsers.add_parser("doctor", help="check whether the installation can run analyses")
    download = subparsers.add_parser(
        "download-resources", help="download and checksum current public human annotations"
    )
    download.add_argument("--output", type=Path, default=Path("varenrich-human-resources"))
    return parser


def run_analysis(args: argparse.Namespace) -> int:
    records = (
        read_vcf(args.vcf)
        if args.vcf
        else read_variant_table(args.variants)
        if args.variants
        else []
    )
    records = filter_variants(
        records,
        min_quality=args.min_quality,
        max_allele_frequency=args.max_af,
        pass_only=args.pass_only,
        classifications=set(args.classification or []),
        consequences=set(args.consequence or []),
        zygosities=set(args.zygosity or []),
    )
    if (args.vcf or args.variants) and not records:
        raise ValueError("No variants remain after filtering")
    query = {record.gene for record in records} if records else read_gene_list(args.genes)
    universe = read_gene_list(args.universe)
    gene_sets = read_gene_sets(args.gene_sets)
    testable_gene_sets = sum(bool(gene_set.genes & universe) for gene_set in gene_sets)
    results = enrich(query, universe, gene_sets, min_overlap=args.min_overlap)
    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)
    metadata = {
        "software": "CMHS VarEnrich",
        "version": __version__,
        "query_size": len(query),
        "universe_size": len(universe),
        "gene_sets_loaded": len(gene_sets),
        "gene_sets_tested": testable_gene_sets,
        "results_returned": len(results),
        "input_type": "VCF" if args.vcf else "variant table" if records else "gene list",
        "variant_records": len(records),
        "filters": {
            "min_quality": args.min_quality,
            "max_allele_frequency": args.max_af,
            "pass_only": args.pass_only,
            "classifications": args.classification or [],
            "consequences": args.consequence or [],
            "zygosities": args.zygosity or [],
        },
        "method": "one-sided hypergeometric survival test; Benjamini-Hochberg FDR",
        "annotation_resource": resource_provenance(args.gene_sets),
        "universe_file": Path(args.universe).name,
        "universe_sha256": sha256(args.universe),
    }
    write_results_tsv(results, destination / "enrichment-results.tsv")
    write_svg_figures(results, destination / "figures")
    if records:
        write_variants_tsv(records, destination / "filtered-variants.tsv")
    write_html_report(results, destination / "report.html", title=args.title, metadata=metadata)
    (destination / "analysis-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Analysed {len(query)} genes against {testable_gene_sets} testable gene sets.")
    print(f"Report: {(destination / 'report.html').resolve()}")
    return 0


def run_resource_build(args: argparse.Namespace) -> int:
    if args.go_obo and not args.go_gaf:
        raise ValueError("--go-obo requires --go-gaf")
    if args.go_gaf and not args.go_obo and not args.reactome:
        raise ValueError("--go-gaf requires --go-obo unless used to map --reactome")
    if args.reactome and not args.go_gaf:
        raise ValueError("--reactome requires --go-gaf for UniProt-to-symbol mapping")
    if not any((args.go_obo, args.hpo, args.clinvar_diseases, args.reactome, args.mapping)):
        raise ValueError("Provide GO, HPO, Reactome, ClinVar, or at least one --mapping file")
    gene_sets = []
    inputs: list[str] = []
    if args.go_gaf and args.go_obo:
        gene_sets.extend(
            build_go_gene_sets(args.go_gaf, args.go_obo, propagate=not args.no_go_propagation)
        )
        inputs.extend([args.go_gaf, args.go_obo])
    if args.reactome:
        gene_sets.extend(build_reactome_gene_sets(args.reactome, args.go_gaf))
        inputs.append(args.reactome)
        if args.go_gaf not in inputs:
            inputs.append(args.go_gaf)
    if args.hpo:
        gene_sets.extend(build_hpo_gene_sets(args.hpo))
        inputs.append(args.hpo)
    if args.clinvar_diseases:
        gene_sets.extend(build_clinvar_disease_sets(args.clinvar_diseases))
        inputs.append(args.clinvar_diseases)
    for mapping in args.mapping:
        gene_sets.extend(build_mapping_gene_sets(mapping))
        inputs.append(mapping)
    output = write_gmt(gene_sets, args.output)
    manifest = write_resource_manifest(inputs, output, output.with_suffix(".manifest.json"))
    print(f"Built {len(gene_sets)} gene sets: {output.resolve()}")
    print(f"Manifest: {manifest.resolve()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command in {"analyse", "analyze"}:
            return run_analysis(args)
        if args.command == "build-resources":
            return run_resource_build(args)
        if args.command == "gui":
            if args.check:
                print(json.dumps({"gui": "PASS", "local_only": True}))
                return 0
            from .gui import run_gui

            run_gui(open_browser=not args.no_browser, output_root=args.output_root)
            return 0
        if args.command == "doctor":
            with tempfile.TemporaryDirectory(prefix="varenrich-doctor-") as directory:
                probe = Path(directory) / "write-test"
                probe.write_text("ok", encoding="utf-8")
            print(
                json.dumps(
                    {
                        "status": "PASS",
                        "version": __version__,
                        "python": sys.version.split()[0],
                        "distribution": "standalone" if getattr(sys, "frozen", False) else "python",
                        "local_only_gui": True,
                    },
                    indent=2,
                )
            )
            return 0
        if args.command == "download-resources":
            from .download import download_human_annotations

            print("Downloading public GO, HPO, ClinVar, and Reactome annotations…")
            output, manifest = download_human_annotations(args.output)
            print(f"Annotations: {output.resolve()}")
            print(f"Manifest: {manifest.resolve()}")
            return 0
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
