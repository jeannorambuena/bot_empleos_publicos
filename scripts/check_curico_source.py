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
ALLOWED_STATUS = {"open_confirmed", "closed", "manual_review"}
DETAIL_URL_STATUS = {"ok", "error"}
CONFIDENCE = {"high", "low"}
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
    "published_date",
    "detected_at",
    "detail_checked_at",
    "detail_url_status",
    "status",
    "status_reason",
    "confidence",
    "description",
    "tags",
    "document_urls",
    "evidence",
    "is_demo",
    "url_status",
    "implementation_status",
    "manual_review",
    "manual_review_reason",
}


def _valid_url(value: Any) -> bool:
    return isinstance(value, str) and urlparse(value).scheme in {"http", "https"} and bool(urlparse(value).netloc)


def _official_curico_url(value: Any) -> bool:
    if not _valid_url(value):
        return False
    hostname = (urlparse(value).hostname or "").lower()
    return hostname == "curico.cl" or hostname.endswith(".curico.cl")


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
        if not _official_curico_url(item.get("source_url")):
            errors.append(f"{label}.source_url debe ser oficial HTTP(S).")
        if not _official_curico_url(item.get("listing_url")):
            errors.append(f"{label}.listing_url debe ser oficial HTTP(S).")
        if item.get("region") != "Maule" or item.get("commune") != "Curicó":
            errors.append(f"{label} debe pertenecer a Maule / Curicó.")
        if item.get("closing_date") is not None:
            try:
                date.fromisoformat(str(item["closing_date"]))
            except ValueError:
                errors.append(f"{label}.closing_date debe ser null o YYYY-MM-DD verificable.")
        if item.get("published_date") is not None:
            try:
                date.fromisoformat(str(item["published_date"]))
            except ValueError:
                errors.append(f"{label}.published_date debe ser null o YYYY-MM-DD verificable.")
        if item.get("detail_url_status") not in DETAIL_URL_STATUS:
            errors.append(f"{label}.detail_url_status no permitido.")
        status = item.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{label}.status no permitido.")
        if not item.get("status_reason") or item.get("confidence") not in CONFIDENCE:
            errors.append(f"{label} requiere status_reason y confidence válidos.")
        if status == "open_confirmed":
            try:
                closing_date = date.fromisoformat(str(item.get("closing_date")))
            except ValueError:
                errors.append(f"{label}: open_confirmed requiere closing_date ISO.")
            else:
                if closing_date < date.today():
                    errors.append(f"{label}: open_confirmed no puede tener cierre pasado.")
        if status == "manual_review":
            if item.get("manual_review") is not True or not item.get("manual_review_reason"):
                errors.append(f"{label}: manual_review requiere marca y motivo explícitos.")
        if item.get("implementation_status") != "dry_run":
            errors.append(f"{label} debe conservar implementation_status dry_run.")
        documents = item.get("document_urls")
        if not isinstance(documents, list):
            errors.append(f"{label}.document_urls debe ser lista.")
        else:
            for document in documents:
                if (
                    not isinstance(document, dict)
                    or not document.get("name")
                    or not _official_curico_url(document.get("url"))
                ):
                    errors.append(f"{label}.document_urls contiene URL no oficial.")
        if not isinstance(item.get("evidence"), list) or not item.get("evidence"):
            errors.append(f"{label}.evidence debe contener trazabilidad.")
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
    counts = {status: 0 for status in sorted(ALLOWED_STATUS)}
    for item in opportunities:
        if isinstance(item, dict) and item.get("status") in counts:
            counts[item["status"]] += 1
    print(
        "OK: dry-run Curicó R2 válido "
        f"({len(opportunities)} publicaciones: "
        f"{counts['open_confirmed']} abiertas, {counts['closed']} cerradas, "
        f"{counts['manual_review']} manual_review)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
