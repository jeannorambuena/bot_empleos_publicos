"""Import a reviewed browser export into versioned feedback configuration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.feedback import normalize_feedback_entries


def _public_entry(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item[key]
        for key in ("opportunity_id", "action", "reason", "created_at", "title", "source_url")
        if item.get(key)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        items = normalize_feedback_entries(payload)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    output = {"version": 1, "items": [_public_entry(item) for item in items]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"OK: propuesta de feedback escrita en {args.output} ({len(items)} entradas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
