import stat
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_mac_archive_preserves_executable_metadata(tmp_path):
    binary = tmp_path / "varenrich"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "packaging" / "package_standalone.py"),
            "--binary",
            str(binary),
            "--platform-label",
            "macOS-Intel",
            "--version",
            "0.1.0",
            "--format",
            "zip",
            "--output",
            str(tmp_path),
        ],
        check=True,
    )
    archive = tmp_path / "CMHS-VarEnrich-0.1.0-macOS-Intel.zip"
    with zipfile.ZipFile(archive) as bundle:
        modes = {Path(info.filename).name: info.external_attr >> 16 for info in bundle.infolist()}
    assert stat.S_ISREG(modes["varenrich"])
    assert modes["varenrich"] & 0o111
    assert modes["Start CMHS VarEnrich.command"] & 0o111
    assert archive.with_name(f"{archive.name}.sha256").is_file()
