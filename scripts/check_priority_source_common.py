"""Shared contract checks for P1 source dry-runs."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from check_source_sanitization import opportunity_sanitization_errors


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PATH = ROOT / "public" / "data" / "opportunities.json"
ALLOWED_STATUS = {"open_confirmed", "closed", "manual_review"}
ALLOWED_SCOPES = {"municipal", "slep", "public_institution", "external_private", "unknown"}
FIELDS = {
    "id", "title", "institution", "source", "source_url", "listing_url", "region", "commune",
    "status", "status_reason", "closing_date", "published_date", "offer_scope",
    "implementation_status", "manual_review", "manual_review_reason", "confidence",
    "document_urls", "evidence",
}


def check_source(key: str, source_name: str) -> tuple[list[str], dict[str, Any] | None]:
    output_dir = ROOT / "output" / "sources" / key
    errors: list[str] = []
    try:
        opportunities = json.loads((output_dir / "opportunities.json").read_text(encoding="utf-8"))
        diagnostics = json.loads((output_dir / "diagnostics.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{source_name}: no fue posible leer output local: {error}"], None
    if not isinstance(opportunities, list):
        return [f"{source_name}: opportunities.json debe contener una lista."], diagnostics
    ids = []
    for index, item in enumerate(opportunities):
        label = f"{source_name}.opportunities[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} debe ser objeto.")
            continue
        missing = FIELDS - item.keys()
        if missing:
            errors.append(f"{label} sin campos: {', '.join(sorted(missing))}")
        ids.append(item.get("id"))
        status = item.get("status")
        scope = item.get("offer_scope")
        if status not in ALLOWED_STATUS:
            errors.append(f"{label}.status no permitido.")
        if scope not in ALLOWED_SCOPES:
            errors.append(f"{label}.offer_scope no permitido.")
        if item.get("implementation_status") != "dry_run":
            errors.append(f"{label} debe conservar implementation_status dry_run.")
        for field in ("source_url", "listing_url"):
            if not _valid_url(item.get(field)):
                errors.append(f"{label}.{field} debe ser URL trazable.")
        if status == "open_confirmed":
            try:
                closing = date.fromisoformat(str(item.get("closing_date")))
            except ValueError:
                errors.append(f"{label}: open_confirmed requiere closing_date ISO.")
            else:
                if closing < date.today():
                    errors.append(f"{label}: open_confirmed no puede tener cierre pasado.")
            if scope == "external_private":
                errors.append(f"{label}: external_private no puede quedar open_confirmed.")
        if status == "manual_review" and (item.get("manual_review") is not True or not item.get("manual_review_reason")):
            errors.append(f"{label}: manual_review requiere marca y motivo.")
        documents = item.get("document_urls")
        if not isinstance(documents, list):
            errors.append(f"{label}.document_urls debe ser lista.")
        else:
            for document in documents:
                if not isinstance(document, dict) or not document.get("name") or not _valid_url(document.get("url")):
                    errors.append(f"{label}.document_urls contiene referencia inválida.")
        if not isinstance(item.get("evidence"), list) or not item.get("evidence"):
            errors.append(f"{label}.evidence debe conservar trazabilidad.")
        errors.extend(opportunity_sanitization_errors(item, label))
    if len(ids) != len(set(ids)):
        errors.append(f"{source_name}: IDs duplicados.")
    if not (output_dir / "report.md").exists():
        errors.append(f"{source_name}: falta report.md local.")
    try:
        public_items = json.loads(PUBLIC_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"{source_name}: no fue posible revisar public/data: {error}")
    else:
        if any(isinstance(item, dict) and item.get("source") == source_name for item in public_items):
            errors.append(f"{source_name}: el dry-run no puede aparecer publicado en public/data.")
    return errors, diagnostics


def _valid_url(value: Any) -> bool:
    return isinstance(value, str) and urlparse(value).scheme in {"http", "https"} and bool(urlparse(value).netloc)
