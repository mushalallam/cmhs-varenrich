"""Self-contained, privacy-preserving HTML reports with publication-ready SVG."""

from __future__ import annotations

import csv
import html
import json
import math
from pathlib import Path

from .analysis import EnrichmentResult


def write_results_tsv(results: list[EnrichmentResult], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "term_id", "term_name", "source", "overlap", "query_size", "term_size",
        "universe_size", "expected", "fold_enrichment", "p_value", "fdr", "genes",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for result in results:
            row = result.as_dict()
            row["genes"] = ";".join(result.genes)
            writer.writerow(row)
    return output


def _bar_chart(results: list[EnrichmentResult], limit: int = 15) -> str:
    selected = results[:limit]
    if not selected:
        return '<p class="empty">No gene sets met the requested overlap threshold.</p>'
    width, left, right, row_height = 940, 290, 55, 38
    height = 60 + row_height * len(selected)
    scores = [-math.log10(max(result.fdr, 1e-300)) for result in selected]
    scale = (width - left - right) / max(scores)
    elements = [
        (
            f'<svg viewBox="0 0 {width} {height}" role="img" '
            'aria-label="Top enrichment results by negative log ten FDR">'
        ),
        (
            '<style>.label{font:13px system-ui;fill:#152536}'
            '.value{font:12px system-ui;fill:#375169}'
            '.bar{fill:#087f8c}.bar:hover{fill:#d97706}</style>'
        ),
    ]
    for index, (result, score) in enumerate(zip(selected, scores, strict=True)):
        y = 30 + index * row_height
        label = html.escape(result.term_name[:39])
        elements.extend(
            [
                f'<text class="label" x="{left - 12}" y="{y + 17}" text-anchor="end">{label}</text>',
                (
                    f'<rect class="bar" x="{left}" y="{y}" '
                    f'width="{max(2, score * scale):.1f}" height="24" rx="5">'
                    f'<title>{html.escape(result.term_id)}; FDR={result.fdr:.3g}; '
                    f'genes={html.escape(", ".join(result.genes))}</title></rect>'
                ),
                (
                    f'<text class="value" x="{left + score * scale + 8:.1f}" y="{y + 17}">'
                    f'{score:.2f}</text>'
                ),
            ]
        )
    elements.extend(
        [
            f'<text class="value" x="{left}" y="{height - 8}">−log₁₀(FDR)</text>',
            "</svg>",
        ]
    )
    return "".join(elements)


def write_html_report(
    results: list[EnrichmentResult],
    path: str | Path,
    *,
    title: str = "CMHS VarEnrich Report",
    metadata: dict[str, object] | None = None,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    meta = metadata or {}
    significant = sum(result.fdr <= 0.05 for result in results)
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(result.source)}</td><td>{html.escape(result.term_id)}</td>"
        f"<td>{html.escape(result.term_name)}</td><td>{result.overlap}/{result.term_size}</td>"
        f"<td>{result.fold_enrichment:.2f}</td><td>{result.p_value:.3g}</td>"
        f"<td>{result.fdr:.3g}</td><td>{html.escape(', '.join(result.genes))}</td>"
        "</tr>"
        for result in results
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{html.escape(title)}</title>
<style>
:root{{--ink:#152536;--muted:#64748b;--teal:#087f8c;--gold:#d97706;--paper:#fff;--wash:#f2f7f7}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--wash);color:var(--ink);font:15px/1.5 system-ui}}
header{{padding:48px max(5vw,24px);background:linear-gradient(120deg,#073b4c,#087f8c);color:white}}
header p{{max-width:780px;color:#d8f3f1}} main{{max-width:1200px;margin:auto;padding:26px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-top:-48px}}
.card,.panel{{background:var(--paper);border-radius:14px;padding:20px;box-shadow:0 6px 22px #16324f17}}
.metric{{font-size:30px;font-weight:750;color:var(--teal)}} .panel{{margin-top:22px;overflow:auto}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{padding:10px;border-bottom:1px solid #dbe5e7;text-align:left}}
th{{position:sticky;top:0;background:#e8f3f3}} input{{padding:11px;width:100%;border:1px solid #a9bdc2;border-radius:8px}}
.note{{border-left:4px solid var(--gold);padding-left:13px;color:#5b4a24}} .empty{{color:var(--muted)}}
@media print{{body{{background:white}} .card,.panel{{box-shadow:none;border:1px solid #ccd}}}}
</style></head><body>
<header><h1>{html.escape(title)}</h1><p>Human rare-variant gene-set enrichment with an explicit background universe. This report is self-contained and does not transmit patient data.</p></header>
<main><section class="cards"><div class="card"><div class="metric">{len(results)}</div>tested terms</div>
<div class="card"><div class="metric">{significant}</div>FDR ≤ 0.05</div>
<div class="card"><div class="metric">{html.escape(str(meta.get('query_size', '—')))}</div>query genes</div>
<div class="card"><div class="metric">{html.escape(str(meta.get('universe_size', '—')))}</div>background genes</div></section>
<section class="panel"><h2>Enrichment overview</h2>{_bar_chart(results)}</section>
<section class="panel"><h2>Complete results</h2><input id="filter" aria-label="Filter results" placeholder="Filter terms, sources, or genes…">
<table id="results"><thead><tr><th>Source</th><th>ID</th><th>Term</th><th>Hits</th><th>Fold</th><th>P</th><th>FDR</th><th>Genes</th></tr></thead><tbody>{rows}</tbody></table></section>
<section class="panel"><h2>Interpretation safeguards</h2><p class="note">Enrichment is exploratory evidence, not a diagnosis. Results depend on the selected gene universe, annotations, filtering, and multiple-testing correction. Review variants and disease associations with a qualified genetics professional.</p>
<details><summary>Analysis metadata</summary><pre>{html.escape(json.dumps(meta, indent=2, sort_keys=True))}</pre></details></section></main>
<script>document.getElementById('filter').addEventListener('input',e=>{{let q=e.target.value.toLowerCase();document.querySelectorAll('#results tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))}})</script>
</body></html>"""
    output.write_text(document, encoding="utf-8")
    return output
