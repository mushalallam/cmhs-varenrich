"""Create a cross-platform standalone archive and SHA-256 sidecar."""

from __future__ import annotations

import argparse
import hashlib
import io
import tarfile
import zipfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--platform-label", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--format", choices=("zip", "tar.gz"), required=True)
    parser.add_argument("--output", type=Path, default=Path("release-assets"))
    args = parser.parse_args()
    if not args.binary.is_file():
        raise SystemExit(f"Standalone binary not found: {args.binary}")
    args.output.mkdir(parents=True, exist_ok=True)
    stem = f"CMHS-VarEnrich-{args.version}-{args.platform_label}"
    suffix = ".zip" if args.format == "zip" else ".tar.gz"
    archive = args.output / f"{stem}{suffix}"
    quickstart = Path(__file__).with_name("QUICKSTART.md").read_bytes()
    extras: list[tuple[str, bytes, int]] = [("QUICKSTART.md", quickstart, 0o644)]
    if args.platform_label.startswith("Windows"):
        extras.append(
            (
                "Start CMHS VarEnrich.bat",
                b'@echo off\r\ncd /d "%~dp0"\r\nvarenrich.exe gui\r\n',
                0o755,
            )
        )
    else:
        launcher = (
            "Start CMHS VarEnrich.command"
            if args.platform_label.startswith("macOS")
            else "Start-CMHS-VarEnrich.sh"
        )
        extras.append(
            (
                launcher,
                (
                    b'#!/bin/sh\nSCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"\n'
                    b'exec "$SCRIPT_DIR/varenrich" gui\n'
                ),
                0o755,
            )
        )
    if args.format == "zip":
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            binary = zipfile.ZipInfo(f"{stem}/{args.binary.name}")
            binary.external_attr = 0o755 << 16
            bundle.writestr(binary, args.binary.read_bytes())
            for name, data, mode in extras:
                info = zipfile.ZipInfo(f"{stem}/{name}")
                info.external_attr = mode << 16
                bundle.writestr(info, data)
    else:
        with tarfile.open(archive, "w:gz") as bundle:
            info = bundle.gettarinfo(str(args.binary), arcname=f"{stem}/{args.binary.name}")
            info.mode = 0o755
            with args.binary.open("rb") as handle:
                bundle.addfile(info, handle)
            for name, data, mode in extras:
                info = tarfile.TarInfo(f"{stem}/{name}")
                info.size, info.mode = len(data), mode
                bundle.addfile(info, io.BytesIO(data))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum = archive.with_name(f"{archive.name}.sha256")
    checksum.write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
    print(archive)
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
