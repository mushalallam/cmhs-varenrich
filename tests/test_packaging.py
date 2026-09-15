import stat
import subprocess
import sys
import tarfile
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


def test_windows_archive_contains_batch_launcher(tmp_path):
    binary = tmp_path / "varenrich.exe"
    binary.write_bytes(b"synthetic executable")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "packaging" / "package_standalone.py"),
            "--binary",
            str(binary),
            "--platform-label",
            "Windows-x86_64",
            "--version",
            "0.1.0",
            "--format",
            "zip",
            "--output",
            str(tmp_path),
        ],
        check=True,
    )
    archive = tmp_path / "CMHS-VarEnrich-0.1.0-Windows-x86_64.zip"
    with zipfile.ZipFile(archive) as bundle:
        names = {Path(name).name for name in bundle.namelist()}
        launcher = bundle.read("CMHS-VarEnrich-0.1.0-Windows-x86_64/Start CMHS VarEnrich.bat")
    assert {"varenrich.exe", "Start CMHS VarEnrich.bat", "QUICKSTART.md"} <= names
    assert b"varenrich.exe gui" in launcher


def test_linux_tar_preserves_shell_launcher_mode(tmp_path):
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
            "Linux-x86_64",
            "--version",
            "0.1.0",
            "--format",
            "tar.gz",
            "--output",
            str(tmp_path),
        ],
        check=True,
    )
    archive = tmp_path / "CMHS-VarEnrich-0.1.0-Linux-x86_64.tar.gz"
    with tarfile.open(archive, "r:gz") as bundle:
        members = {Path(member.name).name: member for member in bundle.getmembers()}
        launcher = bundle.extractfile("CMHS-VarEnrich-0.1.0-Linux-x86_64/Start-CMHS-VarEnrich.sh")
        assert launcher is not None
        launcher_content = launcher.read()
    assert members["varenrich"].mode & 0o111
    assert members["Start-CMHS-VarEnrich.sh"].mode & 0o111
    assert b'"$SCRIPT_DIR/varenrich" gui' in launcher_content
