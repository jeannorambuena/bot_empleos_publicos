"""Print a focused sample for human review of scoring relevance."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PATH = ROOT / "public" / "data" / "opportunities.json"
AMBIGUOUS_TERMS = ("sistemas", "plataforma", "abastecimiento")


def _load_items() -> list[dict[str, Any]]:
    try:
        with PUBLIC_PATH.open("r", encoding="utf-8") as file:
            items = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: No se pudo leer {PUBLIC_PATH}: {error}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(items, list):
        print("ERROR: opportunities.json debe contener una lista.", file=sys.stderr)
        raise SystemExit(1)
    return items


def _possible_issue(item: dict[str, Any]) -> str:
    matched = " ".join(item.get("matched_keywords", [])).lower()
    ambiguous = [term for term in AMBIGUOUS_TERMS if term in matched]
    if ambiguous:
        return f"Revisar término ambiguo: {', '.join(ambiguous)}"
    if item.get("match_level") == "Descartada" and item.get("matched_keywords"):
        return "Descartada con keywords positivas"
    return "-"


def _should_show(item: dict[str, Any]) -> bool:
    return (
        item.get("match_level") in {"Alta", "Media"}
        or bool(item.get("matched_keywords")) and item.get("match_level") == "Descartada"
        or _possible_issue(item) != "-"
    )


def main() -> int:
    items = [item for item in _load_items() if _should_show(item)]
    items.sort(key=lambda item: (-int(item.get("match_score", 0)), item.get("title", "")))

    print("id | score | level | title | institution | matched_keywords | alert_reasons | posible problema")
    print("-" * 180)
    for item in items:
        print(
            " | ".join(
                [
                    str(item.get("id", "-")),
                    str(item.get("match_score", 0)),
                    str(item.get("match_level", "-")),
                    str(item.get("title", "-")),
                    str(item.get("institution", "-")),
                    ", ".join(item.get("matched_keywords", [])) or "-",
                    ", ".join(item.get("alert_reasons", [])) or "-",
                    _possible_issue(item),
                ]
            )
        )
    print(f"\nTotal para revisión manual: {len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
