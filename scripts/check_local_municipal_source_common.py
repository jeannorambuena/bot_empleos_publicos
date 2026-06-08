"""Common validator for local municipal dry-run source captures."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from check_source_sanitization import opportunity_sanitization_errors


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_OPPORTUNITIES_PATH = ROOT / "public" / "data" / "opportunities.json"
ALLOWED_STATUS = {"open_confirmed", "closed", "manual_review"}
DETAIL_URL_STATUS = {"listing_only"}
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
    "visible_date",
    "detected_at",
    "detail_checked_at",
    "detail_url_status",
    "status",
    "status_reason",
    "confidence",
    "description",
    "tags",
    "categories",
    "document_urls",
    "documents",
    "base_links",
    "application_links",
    "evidence",
    "is_demo",
    "url_status",
    "implementation_status",
    "offer_scope",
    "local_priority",
    "manual_review",
    "manual_review_reason",
    "review_label",
    "source_change_detected",
    "listing_hash",
    "item_hash",
}


def run_check(*, key: str, source_id: str, source_name: str, commune: str, allowed_hosts: tuple[str, ...]) -> int:
    output_dir = ROOT / "output" / "sources" / key
    opportunities_path = output_dir / "opportunities.json"
    diagnostics_path = output_dir / "diagnostics.json"
    state_path = output_dir / "monitor_state.json"
    report_path = output_dir / "report.md"
    try:
        opportunities = _load_json(opportunities_path)
        diagnostics = _load_json(diagnostics_path)
        state = _load_json(state_path)
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: no fue posible leer salida {source_name}: {error}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if not isinstance(opportunities, list):
        errors.append("opportunities.json debe contener una lista.")
        opportunities = []
    if not isinstance(diagnostics, dict):
        errors.append("diagnostics.json debe contener un objeto.")
        diagnostics = {}
    if not isinstance(state, dict):
        errors.append("monitor_state.json debe contener un objeto.")
        state = {}

    if diagnostics.get("source_id") != source_id or diagnostics.get("source") != source_name:
        errors.append("diagnostics debe identificar la fuente municipal esperada.")
    if diagnostics.get("implementation_status") != "dry_run" or diagnostics.get("publishability") != "manual_review_only":
        errors.append("diagnostics debe conservar dry_run/manual_review_only.")
    if diagnostics.get("local_priority") is not True:
        errors.append("diagnostics debe marcar local_priority=true.")
    if not _valid_hash(diagnostics.get("listing_hash")):
        errors.append("diagnostics.listing_hash debe ser SHA-256 normalizado.")
    if state.get("listing_hash") != diagnostics.get("listing_hash"):
        errors.append("monitor_state debe conservar el mismo listing_hash que diagnostics.")
    pages_checked = diagnostics.get("pages_checked")
    if not isinstance(pages_checked, list) or not pages_checked:
        errors.append("diagnostics.pages_checked debe incluir al menos una pagina oficial revisada.")
    else:
        for page in pages_checked:
            if not isinstance(page, dict) or not _official_source_url(page.get("url"), allowed_hosts):
                errors.append("diagnostics.pages_checked contiene URL no oficial.")
            if not _valid_hash(page.get("hash")):
                errors.append("diagnostics.pages_checked debe incluir hash SHA-256 por pagina.")
    page_errors = diagnostics.get("page_errors")
    if page_errors is not None and not isinstance(page_errors, list):
        errors.append("diagnostics.page_errors debe ser lista.")

    ids = []
    for index, item in enumerate(opportunities):
        label = f"{key}.opportunities[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} debe ser objeto.")
            continue
        missing = FIELDS - item.keys()
        if missing:
            errors.append(f"{label} sin campos: {', '.join(sorted(missing))}")
        ids.append(item.get("id"))
        if item.get("source") != source_name or item.get("region") != "Maule" or item.get("commune") != commune:
            errors.append(f"{label} debe pertenecer a Maule / {commune}.")
        if item.get("offer_scope") != "municipal" or item.get("local_priority") is not True:
            errors.append(f"{label} debe ser municipal local_priority.")
        if item.get("implementation_status") != "dry_run" or item.get("review_label") != "Revisar bases":
            errors.append(f"{label} debe conservar dry_run y etiqueta Revisar bases.")
        if not _official_source_url(item.get("source_url"), allowed_hosts):
            errors.append(f"{label}.source_url debe ser URL oficial permitida.")
        if not _official_source_url(item.get("listing_url"), allowed_hosts):
            errors.append(f"{label}.listing_url debe ser URL oficial municipal.")
        if item.get("detail_url_status") not in DETAIL_URL_STATUS:
            errors.append(f"{label}.detail_url_status no permitido.")
        if item.get("status") not in ALLOWED_STATUS:
            errors.append(f"{label}.status no permitido.")
        if item.get("confidence") not in CONFIDENCE or not item.get("status_reason"):
            errors.append(f"{label} requiere confidence/status_reason validos.")
        if not _valid_hash(item.get("listing_hash")) or not _valid_hash(item.get("item_hash")):
            errors.append(f"{label} requiere listing_hash e item_hash SHA-256.")
        _validate_date(item.get("published_date"), f"{label}.published_date", errors)
        _validate_date(item.get("closing_date"), f"{label}.closing_date", errors)
        if item.get("status") == "open_confirmed":
            if item.get("manual_review") is not False:
                errors.append(f"{label}: open_confirmed no debe requerir revision manual.")
            try:
                closing_date = date.fromisoformat(str(item.get("closing_date")))
            except ValueError:
                errors.append(f"{label}: open_confirmed requiere closing_date ISO.")
            else:
                if closing_date < date.today():
                    errors.append(f"{label}: open_confirmed no puede tener cierre pasado.")
        else:
            if item.get("manual_review") is not True or not item.get("manual_review_reason"):
                errors.append(f"{label}: closed/manual_review requiere motivo de revision.")
        for list_field in ("document_urls", "documents", "base_links", "application_links", "evidence"):
            if not isinstance(item.get(list_field), list):
                errors.append(f"{label}.{list_field} debe ser lista.")
        for document in item.get("document_urls") or []:
            if not isinstance(document, dict) or not document.get("name") or not _official_source_url(document.get("url"), allowed_hosts):
                errors.append(f"{label}.document_urls contiene URL no oficial permitida.")
        if item.get("is_demo") is not False or item.get("url_status") != "ok":
            errors.append(f"{label} debe conservar URL real sin presentarse como demo.")
        errors.extend(opportunity_sanitization_errors(item, label))
    if len(ids) != len(set(ids)):
        errors.append(f"Los IDs {source_name} deben ser unicos.")
    if not report_path.exists():
        errors.append(f"No existe reporte local: {report_path}")
    errors.extend(_public_data_errors(source_id, source_name))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    counts = {status: 0 for status in sorted(ALLOWED_STATUS)}
    for item in opportunities:
        if isinstance(item, dict) and item.get("status") in counts:
            counts[item["status"]] += 1
    print(
        f"OK: dry-run {source_name} valido "
        f"({len(opportunities)} publicaciones: {counts['open_confirmed']} abiertas, "
        f"{counts['closed']} cerradas, {counts['manual_review']} manual_review; "
        f"bases={diagnostics.get('base_links_detected', 0)}, "
        f"postulacion={diagnostics.get('application_links_detected', 0)}, "
        f"cambio={'si' if diagnostics.get('source_change_detected') else 'no'})."
    )
    return 0


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _official_source_url(value: Any, allowed_hosts: tuple[str, ...]) -> bool:
    if not _valid_url(value):
        return False
    hostname = (urlparse(str(value)).hostname or "").lower()
    if any(hostname == host or hostname.endswith(f".{host}") for host in allowed_hosts):
        return True
    return hostname == "empleospublicos.cl" or hostname.endswith(".empleospublicos.cl")


def _valid_url(value: Any) -> bool:
    return isinstance(value, str) and urlparse(value).scheme in {"http", "https"} and bool(urlparse(value).netloc)


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _validate_date(value: Any, label: str, errors: list[str]) -> None:
    if value is None:
        return
    try:
        date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{label} debe ser null o YYYY-MM-DD.")


def _public_data_errors(source_id: str, source_name: str) -> list[str]:
    try:
        public_opportunities = _load_json(PUBLIC_OPPORTUNITIES_PATH)
    except (OSError, json.JSONDecodeError) as error:
        return [f"No fue posible revisar {PUBLIC_OPPORTUNITIES_PATH}: {error}"]
    if not isinstance(public_opportunities, list):
        return ["public/data/opportunities.json debe contener una lista."]
    published = [
        item
        for item in public_opportunities
        if isinstance(item, dict)
        and (str(item.get("id") or "").startswith(f"{source_id}-") or item.get("source") == source_name)
    ]
    if published:
        return [f"{source_name} debe permanecer aislado: se detectaron registros en public/data."]
    return []
