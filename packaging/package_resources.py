"""Package a versioned human annotation GMT and provenance manifest."""

from __future__ import annotations

import argparse
import hashlib
import zipfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, default=Path("release-assets"))
    args = parser.parse_args()
    for path in (args.annotations, args.manifest):
        if not path.is_file():
            raise SystemExit(f"Resource file not found: {path}")
    args.output.mkdir(parents=True, exist_ok=True)
    archive = args.output / f"CMHS-VarEnrich-{args.version}-Human-Annotations.zip"
    folder = f"CMHS-VarEnrich-{args.version}-Human-Annotations"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(args.annotations, f"{folder}/human-annotations.gmt")
        bundle.write(args.manifest, f"{folder}/human-annotations.manifest.json")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_name(f"{archive.name}.sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
