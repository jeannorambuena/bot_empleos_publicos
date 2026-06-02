"""Validate that local dry-run source outputs contain no visible personal data."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.sources.sanitization import sensitive_personal_data_reasons


SOURCE_OUTPUTS = {
    "curico": ROOT / "output" / "sources" / "curico" / "opportunities.json",
    "molina": ROOT / "output" / "sources" / "molina" / "opportunities.json",
    "gore_maule": ROOT / "output" / "sources" / "gore_maule" / "opportunities.json",
    "rancagua": ROOT / "output" / "sources" / "rancagua" / "opportunities.json",
}
PUBLICABLE_FIELDS = ("title", "description", "evidence", "status_reason", "manual_review_reason")


def opportunity_sanitization_errors(item: Any, label: str) -> list[str]:
    """Return residual sensitive-data errors for one normalized opportunity."""
    if not isinstance(item, dict):
        return [f"{label} debe ser objeto."]
    errors = []
    for field in PUBLICABLE_FIELDS:
        errors.extend(_value_errors(item.get(field), f"{label}.{field}"))
    documents = item.get("document_urls")
    if isinstance(documents, list):
        for index, document in enumerate(documents):
            if isinstance(document, dict):
                errors.extend(_value_errors(document.get("name"), f"{label}.document_urls[{index}].name"))
    return errors


def _value_errors(value: Any, label: str) -> list[str]:
    values = value if isinstance(value, list) else [value]
    errors = []
    for index, candidate in enumerate(values):
        if not isinstance(candidate, str):
            continue
        location = f"{label}[{index}]" if isinstance(value, list) else label
        reasons = sensitive_personal_data_reasons(candidate)
        if reasons:
            errors.append(f"{location}: {', '.join(reasons)}.")
    return errors


def main() -> int:
    errors = []
    checked_items = 0
    for source, path in SOURCE_OUTPUTS.items():
        try:
            opportunities = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{source}: no fue posible leer {path}: {error}")
            continue
        if not isinstance(opportunities, list):
            errors.append(f"{source}: opportunities.json debe contener una lista.")
            continue
        for index, item in enumerate(opportunities):
            checked_items += 1
            errors.extend(opportunity_sanitization_errors(item, f"{source}.opportunities[{index}]"))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "OK: sanitizacion de fuentes valida "
        f"({len(SOURCE_OUTPUTS)} fuentes, {checked_items} oportunidades locales revisadas, "
        "sin RUN/RUT visibles ni tablas extensas de resultados)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
