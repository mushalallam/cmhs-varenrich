# Platform installation and trust

## Recommended download

| Computer | Release file |
|---|---|
| Apple Silicon Mac (M1/M2/M3/M4/M5) | `CMHS-VarEnrich-0.1.0-macOS-Apple-Silicon.zip` |
| Intel Mac | `CMHS-VarEnrich-0.1.0-macOS-Intel.zip` |
| 64-bit Windows | `CMHS-VarEnrich-0.1.0-Windows-x86_64.zip` |
| 64-bit glibc Linux | `CMHS-VarEnrich-0.1.0-Linux-x86_64.tar.gz` |

Each platform archive contains the application, a double-click or shell launcher, and `QUICKSTART.md`. No Python or Conda installation is required.

## Verify a download

Download the archive and its adjacent `.sha256` file into the same directory. Run:

```bash
# macOS
shasum -a 256 -c CMHS-VarEnrich-0.1.0-macOS-Intel.zip.sha256

# Linux
sha256sum -c CMHS-VarEnrich-0.1.0-Linux-x86_64.tar.gz.sha256

# Windows PowerShell (compare with the value inside the .sha256 file)
Get-FileHash .\CMHS-VarEnrich-0.1.0-Windows-x86_64.zip -Algorithm SHA256
```

The SHA-256 shown by GitHub beside a `.sha256` asset is the digest of the small sidecar itself. The digest inside the sidecar is the one for the application archive.

## macOS

Version 0.1.0 preview archives are not Developer ID notarized. Gatekeeper may delay or block the first launch. After verifying the checksum, right-click the launcher and choose **Open**. If an Intel/Apple Silicon build stalls while macOS scans it, a user may remove quarantine from that one verified extracted folder:

```bash
xattr -dr com.apple.quarantine "/exact/path/to/CMHS-VarEnrich-0.1.0-macOS-Intel"
```

Do not run that command on broad directories or unverified downloads. Proper Developer ID signing, hardened runtime, notarization, and stapling are required for a warning-free release.

## Windows

Unsigned preview executables may trigger Microsoft Defender SmartScreen. Verify the SHA-256, then use **More info → Run anyway** only if the publisher/repository is the expected one. Trusted Authenticode signing is planned; a new signature may still require reputation before all SmartScreen prompts disappear.

## Linux

The release targets x86-64 systems using glibc comparable to Ubuntu 22.04 or newer. It does not currently support ARM64 or musl/Alpine. If execution permission was lost during extraction:

```bash
chmod +x varenrich Start-CMHS-VarEnrich.sh
```

## Source installation

Python 3.10+ users on any supported architecture can install the wheel or source distribution in a virtual environment. Docker is also supported for command-line analyses.
