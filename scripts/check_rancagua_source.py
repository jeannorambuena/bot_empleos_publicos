"""Validate the isolated Municipalidad de Rancagua dry-run capture."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from check_source_sanitization import opportunity_sanitization_errors


ROOT = Path(__file__).resolve().parents[1]
OPPORTUNITIES_PATH = ROOT / "output" / "sources" / "rancagua" / "opportunities.json"
REPORT_PATH = ROOT / "output" / "sources" / "rancagua" / "report.md"
PUBLIC_OPPORTUNITIES_PATH = ROOT / "public" / "data" / "opportunities.json"
ALLOWED_STATUS = {"open_confirmed", "closed", "manual_review"}
ALLOWED_SCOPES = {"municipal", "external_private", "unknown"}
FIELDS = {
    "id",
    "source_id",
    "title",
    "institution",
    "source",
    "source_url",
    "listing_url",
    "feed_url",
    "region",
    "commune",
    "closing_date",
    "published_date",
    "detected_at",
    "status",
    "status_reason",
    "confidence",
    "description",
    "tags",
    "categories",
    "offer_scope",
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


def _source_url(value: Any) -> bool:
    if not _valid_url(value):
        return False
    hostname = (urlparse(value).hostname or "").lower()
    return hostname == "rgua.cl" or hostname.endswith(".rgua.cl") or _institutional_url(value)


def _institutional_url(value: Any) -> bool:
    if not _valid_url(value):
        return False
    hostname = (urlparse(value).hostname or "").lower()
    return (
        hostname == "munirancagua.gob.cl"
        or hostname.endswith(".munirancagua.gob.cl")
        or hostname == "rancagua.cl"
        or hostname.endswith(".rancagua.cl")
    )


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
        if not _source_url(item.get("source_url")):
            errors.append(f"{label}.source_url debe provenir del RSS oficial Rancagua.")
        if not _institutional_url(item.get("listing_url")) or not _institutional_url(item.get("feed_url")):
            errors.append(f"{label}.listing_url y feed_url deben ser institucionales Rancagua.")
        if item.get("region") != "O'Higgins" or item.get("commune") != "Rancagua":
            errors.append(f"{label} debe pertenecer a O'Higgins / Rancagua.")
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
        status = item.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{label}.status no permitido.")
        if item.get("offer_scope") not in ALLOWED_SCOPES:
            errors.append(f"{label}.offer_scope no permitido.")
        if status == "open_confirmed":
            try:
                closing_date = date.fromisoformat(str(item.get("closing_date")))
            except ValueError:
                errors.append(f"{label}: open_confirmed requiere closing_date ISO.")
            else:
                if closing_date < date.today():
                    errors.append(f"{label}: open_confirmed no puede tener cierre pasado.")
            if item.get("offer_scope") != "municipal":
                errors.append(f"{label}: open_confirmed solo puede corresponder a oferta municipal.")
        if item.get("offer_scope") == "external_private" and status != "manual_review":
            errors.append(f"{label}: oferta OMIL externa debe permanecer manual_review.")
        if status == "manual_review" and (item.get("manual_review") is not True or not item.get("manual_review_reason")):
            errors.append(f"{label}: manual_review requiere marca y motivo explícitos.")
        if item.get("implementation_status") != "dry_run":
            errors.append(f"{label} debe conservar implementation_status dry_run.")
        documents = item.get("document_urls")
        if not isinstance(documents, list):
            errors.append(f"{label}.document_urls debe ser lista.")
        else:
            for document in documents:
                if not isinstance(document, dict) or not document.get("name") or not _institutional_url(document.get("url")):
                    errors.append(f"{label}.document_urls contiene URL no institucional Rancagua.")
        if not isinstance(item.get("evidence"), list) or not item.get("evidence"):
            errors.append(f"{label}.evidence debe contener trazabilidad.")
        if item.get("is_demo") is not False or item.get("url_status") != "ok":
            errors.append(f"{label} debe conservar URL real sin presentarse como demo.")
        errors.extend(opportunity_sanitization_errors(item, label))
    if len(ids) != len(set(ids)):
        errors.append("Los IDs Rancagua deben ser únicos.")
    if not REPORT_PATH.exists():
        errors.append(f"No existe reporte local: {REPORT_PATH}")
    try:
        public_opportunities = json.loads(PUBLIC_OPPORTUNITIES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"No fue posible revisar {PUBLIC_OPPORTUNITIES_PATH}: {error}")
    else:
        published_rancagua = [
            item
            for item in public_opportunities
            if isinstance(item, dict)
            and (
                str(item.get("id") or "").startswith("municipalidad-rancagua-")
                or item.get("source") == "Municipalidad de Rancagua"
            )
        ]
        if published_rancagua:
            errors.append("Rancagua debe permanecer aislado: se detectaron registros en public/data.")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    counts = {status: 0 for status in sorted(ALLOWED_STATUS)}
    for item in opportunities:
        if isinstance(item, dict) and item.get("status") in counts:
            counts[item["status"]] += 1
    print(
        "OK: dry-run Rancagua válido "
        f"({len(opportunities)} publicaciones: "
        f"{counts['open_confirmed']} abiertas, {counts['closed']} cerradas, "
        f"{counts['manual_review']} manual_review)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
