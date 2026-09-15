from pathlib import Path

from varenrich.cli import main


def test_demo_analysis_creates_self_contained_report(tmp_path):
    examples = Path(__file__).parents[1] / "examples"
    assert main([
        "analyse", "--variants", str(examples / "demo-variants.tsv"),
        "--universe", str(examples / "demo-universe.txt"),
        "--gene-sets", str(examples / "demo-gene-sets.gmt"),
        "--output", str(tmp_path),
    ]) == 0
    report = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert "Hyperphenylalaninemia" in report
    assert "<svg" in report
    assert (tmp_path / "enrichment-results.tsv").exists()
    assert (tmp_path / "analysis-metadata.json").exists()

