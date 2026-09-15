"""Exercise a newly built CMHS VarEnrich executable."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary")
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    version = subprocess.run(
        [args.binary, "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()
    if version != f"varenrich {args.version}":
        raise SystemExit(f"Unexpected version output: {version!r}")
    diagnosis = json.loads(
        subprocess.run([args.binary, "doctor"], check=True, capture_output=True, text=True).stdout
    )
    if diagnosis.get("status") != "PASS" or diagnosis.get("distribution") != "standalone":
        raise SystemExit(f"Standalone diagnosis failed: {diagnosis}")
    gui = json.loads(
        subprocess.run(
            [args.binary, "gui", "--check"], check=True, capture_output=True, text=True
        ).stdout
    )
    if gui != {"gui": "PASS", "local_only": True}:
        raise SystemExit(f"Standalone GUI diagnosis failed: {gui}")
    examples = Path(__file__).parents[1] / "examples"
    with tempfile.TemporaryDirectory(prefix="varenrich-standalone-") as directory:
        subprocess.run(
            [
                args.binary,
                "analyse",
                "--vcf",
                str(examples / "demo-annotated.vcf"),
                "--universe",
                str(examples / "demo-universe.txt"),
                "--gene-sets",
                str(examples / "demo-gene-sets.gmt"),
                "--output",
                directory,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        report = Path(directory) / "report.html"
        if (
            not report.is_file()
            or "Hyperphenylalaninemia" not in report.read_text(encoding="utf-8")
        ):
            raise SystemExit("Standalone end-to-end report check failed")
    print(json.dumps({"standalone": "PASS", "version": args.version}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
