"""Validate safe, versioned human feedback configuration."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.feedback import normalize_feedback_entries


def _check(path: Path, *, required: bool) -> int:
    if not path.exists():
        if required:
            print(f"ERROR: No existe {path}.", file=sys.stderr)
            return 1
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        entries = normalize_feedback_entries(payload)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {path}: {error}", file=sys.stderr)
        return 1
    print(f"OK: {path.name} válido ({len(entries)} entradas).")
    return 0


def main() -> int:
    status = _check(ROOT / "config" / "feedback.example.json", required=True)
    status |= _check(ROOT / "config" / "feedback.json", required=False)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
