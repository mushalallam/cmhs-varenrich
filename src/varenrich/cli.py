"""Command-line entry point for reproducible local analyses."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .analysis import enrich
from .io import read_gene_list, read_gene_sets, read_variant_table
from .report import write_html_report, write_results_tsv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="varenrich", description="Human rare-variant enrichment")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyse = subparsers.add_parser("analyse", aliases=["analyze"], help="run enrichment")
    inputs = analyse.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--genes", help="one gene symbol per line")
    inputs.add_argument("--variants", help="CSV/TSV with a gene or gene_symbol column")
    analyse.add_argument("--universe", required=True, help="all genes that could have been selected")
    analyse.add_argument("--gene-sets", required=True, help="GMT annotation collection")
    analyse.add_argument("--output", default="varenrich-results", help="output directory")
    analyse.add_argument("--min-overlap", type=int, default=1)
    analyse.add_argument("--title", default="CMHS VarEnrich Report")
    return parser


def run_analysis(args: argparse.Namespace) -> int:
    records = read_variant_table(args.variants) if args.variants else []
    query = {record.gene for record in records} if records else read_gene_list(args.genes)
    universe = read_gene_list(args.universe)
    gene_sets = read_gene_sets(args.gene_sets)
    results = enrich(query, universe, gene_sets, min_overlap=args.min_overlap)
    destination = Path(args.output)
    destination.mkdir(parents=True, exist_ok=True)
    metadata = {
        "software": "CMHS VarEnrich",
        "version": __version__,
        "query_size": len(query),
        "universe_size": len(universe),
        "gene_sets_tested": len(gene_sets),
        "input_type": "variant table" if records else "gene list",
        "method": "one-sided hypergeometric survival test; Benjamini-Hochberg FDR",
        "gene_sets_file": str(Path(args.gene_sets).resolve()),
        "universe_file": str(Path(args.universe).resolve()),
    }
    write_results_tsv(results, destination / "enrichment-results.tsv")
    write_html_report(results, destination / "report.html", title=args.title, metadata=metadata)
    (destination / "analysis-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Analysed {len(query)} genes against {len(gene_sets)} gene sets.")
    print(f"Report: {(destination / 'report.html').resolve()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command in {"analyse", "analyze"}:
            return run_analysis(args)
    except (OSError, ValueError) as error:
        parser.exit(2, f"error: {error}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())

