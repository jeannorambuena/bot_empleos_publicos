"""Validate public/data as a coherent dashboard bundle."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.atomic_publication import MANIFEST_FILE, validate_public_bundle


PUBLIC_DATA = ROOT / "public" / "data"


def main() -> int:
    require_manifest = (PUBLIC_DATA / MANIFEST_FILE).exists()
    errors = validate_public_bundle(PUBLIC_DATA, require_manifest=require_manifest)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    mode = "manifest" if require_manifest else "legacy sin manifest"
    print(f"OK: bundle publico valido ({mode}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
