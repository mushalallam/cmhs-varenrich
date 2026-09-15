"""Regenerate README SVGs from the current analysis implementation."""

from __future__ import annotations

import html
import shutil
import tempfile
from pathlib import Path

from varenrich.analysis import enrich
from varenrich.io import read_gene_list, read_gene_sets, read_variant_table
from varenrich.report import write_svg_figures

ROOT = Path(__file__).parents[1]
IMAGES = ROOT / "docs" / "images"


def workflow_svg() -> str:
    stages = [
        ("Input", "Gene list · variant table · annotated VCF"),
        ("Validate & filter", "Gene IDs · QUAL · AF · classification · genotype"),
        ("Connect evidence", "Variant → gene → phenotype · disease · pathway · GO"),
        ("Enrichment", "Explicit universe · Fisher/hypergeometric · BH-FDR"),
        ("Explore & export", "Interactive HTML · TSV · editable SVG · provenance"),
    ]
    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 320" role="img" aria-label="CMHS VarEnrich workflow">',
        '<rect width="1200" height="320" rx="24" fill="#eef6f5"/>',
        (
            "<style>.h{font:700 18px system-ui;fill:white}"
            ".s{font:13px system-ui;fill:#d8f3f1}"
            ".a{fill:none;stroke:#d97706;stroke-width:5;"
            "stroke-linecap:round;stroke-linejoin:round}</style>"
        ),
    ]
    for index, (title, subtitle) in enumerate(stages):
        x = 28 + index * 235
        color = "#073b4c" if index % 2 == 0 else "#087f8c"
        safe_title = html.escape(title)
        safe_subtitle = html.escape(subtitle)
        elements.extend(
            [
                f'<rect x="{x}" y="72" width="205" height="172" rx="18" fill="{color}"/>',
                f'<text class="h" x="{x + 18}" y="112">{safe_title}</text>',
                f'<foreignObject x="{x + 18}" y="128" width="169" height="90"><div xmlns="http://www.w3.org/1999/xhtml" style="font:13px/1.45 system-ui;color:#d8f3f1">{safe_subtitle}</div></foreignObject>',
            ]
        )
        if index < len(stages) - 1:
            elements.append(
                f'<path class="a" d="M{x + 208} 158 H{x + 227} M{x + 220} 150 L{x + 229} 158 L{x + 220} 166"/>'
            )
    elements.append("</svg>")
    return "".join(elements)


def main() -> None:
    IMAGES.mkdir(parents=True, exist_ok=True)
    (IMAGES / "workflow.svg").write_text(workflow_svg(), encoding="utf-8")
    variants = read_variant_table(ROOT / "examples" / "demo-variants.tsv")
    query = {record.gene for record in variants}
    universe = read_gene_list(ROOT / "examples" / "demo-universe.txt")
    sets = read_gene_sets(ROOT / "examples" / "demo-gene-sets.gmt")
    with tempfile.TemporaryDirectory() as directory:
        outputs = write_svg_figures(enrich(query, universe, sets), directory)
        shutil.copy2(outputs[0], IMAGES / "example-enrichment.svg")


if __name__ == "__main__":
    main()
