"""Write portable SHA-256 sidecars for release files."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.files:
        if not path.is_file():
            raise SystemExit(f"File not found: {path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sidecar = path.with_name(f"{path.name}.sha256")
        sidecar.write_bytes(f"{digest}  {path.name}\n".encode("ascii"))
        print(sidecar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
