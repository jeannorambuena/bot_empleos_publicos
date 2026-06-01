"""Validate locally captured and normalized real opportunities."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.contracts import missing_opportunity_fields
from radar.scoring import match_level_for_score


RAW_PATH = ROOT / "data" / "raw" / "empleos_publicos_raw.json"
NORMALIZED_PATH = ROOT / "data" / "normalized" / "empleos_publicos_normalized.json"
PUBLIC_PATH = ROOT / "public" / "data" / "opportunities.json"


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as error:
        raise ValueError(f"No existe: {path}") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON inválido en {path}: {error}") from error


def main() -> int:
    errors = []
    if RAW_PATH.exists():
        try:
            raw = _load_json(RAW_PATH)
            if not isinstance(raw, dict) or not isinstance(raw.get("opportunities"), list):
                errors.append("El archivo raw debe contener una lista 'opportunities'.")
        except ValueError as error:
            errors.append(str(error))

    try:
        normalized = _load_json(NORMALIZED_PATH)
    except ValueError as error:
        return _fail([str(error)])

    if not isinstance(normalized, list):
        errors.append("El archivo normalized debe contener una lista.")
    else:
        for index, item in enumerate(normalized):
            label = f"normalized[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label}: debe ser objeto JSON.")
                continue
            missing = missing_opportunity_fields(item)
            if missing:
                errors.append(f"{label}: faltan campos: {', '.join(missing)}")
            if item.get("is_demo") is not False:
                errors.append(f"{label}: is_demo debe ser false.")
            if item.get("source_url") and "example" in item["source_url"].lower():
                errors.append(f"{label}: source_url parece demo.")

    if PUBLIC_PATH.exists():
        try:
            public_items = _load_json(PUBLIC_PATH)
            for index, item in enumerate(public_items if isinstance(public_items, list) else []):
                if item.get("is_demo") is True:
                    continue
                score = item.get("match_score")
                if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
                    errors.append(f"public[{index}]: match_score inválido.")
                elif item.get("match_level") != match_level_for_score(score):
                    errors.append(f"public[{index}]: match_level no corresponde al puntaje.")
        except ValueError as error:
            errors.append(str(error))

    if errors:
        return _fail(errors)
    print(f"OK: datos reales locales válidos ({len(normalized)} oportunidades normalizadas).")
    return 0


def _fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
