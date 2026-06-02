"""Validate the isolated Municipalidad de Curico dry-run capture."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
OPPORTUNITIES_PATH = ROOT / "output" / "sources" / "curico" / "opportunities.json"
REPORT_PATH = ROOT / "output" / "sources" / "curico" / "report.md"
FIELDS = {
    "id",
    "source_id",
    "title",
    "institution",
    "source",
    "source_url",
    "listing_url",
    "region",
    "commune",
    "closing_date",
    "detected_at",
    "status",
    "description",
    "tags",
    "is_demo",
    "url_status",
    "implementation_status",
    "manual_review",
    "manual_review_reason",
}


def _valid_url(value: Any) -> bool:
    return isinstance(value, str) and urlparse(value).scheme in {"http", "https"} and bool(urlparse(value).netloc)


def main() -> int:
    try:
        opportunities = json.loads(OPPORTUNITIES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: no fue posible leer {OPPORTUNITIES_PATH}: {error}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if not isinstance(opportunities, list):
        errors.append("opportunities.json debe contener una lista.")
        opportunities = []
    ids = []
    for index, item in enumerate(opportunities):
        label = f"opportunities[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} debe ser objeto.")
            continue
        missing = FIELDS - item.keys()
        if missing:
            errors.append(f"{label} sin campos: {', '.join(sorted(missing))}")
        ids.append(item.get("id"))
        if not item.get("id"):
            errors.append(f"{label}.id no puede estar vacío.")
        if not _valid_url(item.get("source_url")):
            errors.append(f"{label}.source_url debe ser oficial HTTP(S).")
        if not _valid_url(item.get("listing_url")):
            errors.append(f"{label}.listing_url debe ser oficial HTTP(S).")
        if item.get("region") != "Maule" or item.get("commune") != "Curicó":
            errors.append(f"{label} debe pertenecer a Maule / Curicó.")
        if item.get("closing_date") is not None:
            try:
                date.fromisoformat(str(item["closing_date"]))
            except ValueError:
                errors.append(f"{label}.closing_date debe ser null o YYYY-MM-DD verificable.")
        if item.get("status") != "manual_review":
            errors.append(f"{label}.status debe ser manual_review mientras no exista vigencia inequívoca.")
        if item.get("implementation_status") != "dry_run" or item.get("manual_review") is not True:
            errors.append(f"{label} debe conservar marcas explícitas de dry-run y revisión manual.")
        if item.get("is_demo") is not False or item.get("url_status") != "ok":
            errors.append(f"{label} debe conservar URL real sin presentarse como demo.")
    if len(ids) != len(set(ids)):
        errors.append("Los IDs Curicó deben ser únicos.")
    if not REPORT_PATH.exists():
        errors.append(f"No existe reporte local: {REPORT_PATH}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: dry-run Curicó válido ({len(opportunities)} publicaciones candidatas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
