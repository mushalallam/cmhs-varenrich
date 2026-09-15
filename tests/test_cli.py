from pathlib import Path

from varenrich.analysis import enrich
from varenrich.cli import main
from varenrich.models import GeneSet
from varenrich.report import write_svg_figures


def test_demo_analysis_creates_self_contained_report(tmp_path):
    examples = Path(__file__).parents[1] / "examples"
    assert (
        main(
            [
                "analyse",
                "--variants",
                str(examples / "demo-variants.tsv"),
                "--universe",
                str(examples / "demo-universe.txt"),
                "--gene-sets",
                str(examples / "demo-gene-sets.gmt"),
                "--output",
                str(tmp_path),
            ]
        )
        == 0
    )
    report = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert "Hyperphenylalaninemia" in report
    assert "<svg" in report
    assert (tmp_path / "enrichment-results.tsv").exists()
    assert (tmp_path / "analysis-metadata.json").exists()
    assert (tmp_path / "figures" / "enrichment-bars.svg").exists()
    assert (tmp_path / "figures" / "enrichment-bubbles.svg").exists()
    assert (tmp_path / "figures" / "term-gene-network.svg").exists()


def test_svg_export_when_all_adjusted_p_values_are_one(tmp_path):
    universe = {f"G{index}" for index in range(1, 21)}
    query = {"G1", "G2", "G3"}
    sets = [GeneSet("HIT", "Hit", "demo", frozenset({"G1"}))]
    sets.extend(
        GeneSet(f"Z{index}", "Zero", "demo", frozenset({f"G{index}"})) for index in range(4, 21)
    )
    results = enrich(query, universe, sets)
    assert results[0].fdr == 1.0
    outputs = write_svg_figures(results, tmp_path)
    assert all(path.stat().st_size > 100 for path in outputs)
