"""Validate the isolated Municipalidad de Romeral dry-run capture."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from check_source_sanitization import opportunity_sanitization_errors


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "sources" / "romeral"
OPPORTUNITIES_PATH = OUTPUT_DIR / "opportunities.json"
DIAGNOSTICS_PATH = OUTPUT_DIR / "diagnostics.json"
STATE_PATH = OUTPUT_DIR / "monitor_state.json"
REPORT_PATH = OUTPUT_DIR / "report.md"
PUBLIC_OPPORTUNITIES_PATH = ROOT / "public" / "data" / "opportunities.json"
ALLOWED_STATUS = {"open_confirmed", "closed", "manual_review"}
DETAIL_URL_STATUS = {"listing_only"}
CONFIDENCE = {"high", "medium", "low"}
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
    "document_urls",
    "base_links",
    "date_change_links",
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
}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_url(value: Any) -> bool:
    return isinstance(value, str) and urlparse(value).scheme in {"http", "https"} and bool(urlparse(value).netloc)


def _official_romeral_url(value: Any) -> bool:
    if not _valid_url(value):
        return False
    hostname = (urlparse(value).hostname or "").lower()
    return hostname == "muniromeral.cl" or hostname.endswith(".muniromeral.cl")


def _valid_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def main() -> int:
    try:
        opportunities = _load_json(OPPORTUNITIES_PATH)
        diagnostics = _load_json(DIAGNOSTICS_PATH)
        state = _load_json(STATE_PATH)
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: no fue posible leer salida Romeral: {error}", file=sys.stderr)
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

    if diagnostics.get("source") != "Municipalidad de Romeral":
        errors.append("diagnostics.source debe ser Municipalidad de Romeral.")
    if diagnostics.get("implementation_status") != "dry_run":
        errors.append("diagnostics debe conservar implementation_status dry_run.")
    if diagnostics.get("local_priority") is not True:
        errors.append("diagnostics debe marcar local_priority=true.")
    if not _valid_hash(diagnostics.get("listing_hash")):
        errors.append("diagnostics.listing_hash debe ser SHA-256 normalizado.")
    if state.get("listing_hash") != diagnostics.get("listing_hash"):
        errors.append("monitor_state debe conservar el mismo listing_hash que diagnostics.")
    pages_checked = diagnostics.get("pages_checked")
    if not isinstance(pages_checked, list) or len(pages_checked) < 3:
        errors.append("diagnostics.pages_checked debe incluir pagina principal y paginadas.")
    else:
        page_urls = " ".join(str(item.get("url") or "") for item in pages_checked if isinstance(item, dict))
        for expected in ("page=2", "page=3"):
            if expected not in page_urls:
                errors.append(f"diagnostics.pages_checked no incluye {expected}.")

    ids = []
    for index, item in enumerate(opportunities):
        label = f"romeral.opportunities[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} debe ser objeto.")
            continue
        missing = FIELDS - item.keys()
        if missing:
            errors.append(f"{label} sin campos: {', '.join(sorted(missing))}")
        ids.append(item.get("id"))
        if item.get("source") != "Municipalidad de Romeral":
            errors.append(f"{label}.source invalido.")
        if item.get("region") != "Maule" or item.get("commune") != "Romeral":
            errors.append(f"{label} debe pertenecer a Maule / Romeral.")
        if item.get("offer_scope") != "municipal" or item.get("local_priority") is not True:
            errors.append(f"{label} debe ser municipal local_priority.")
        if item.get("implementation_status") != "dry_run":
            errors.append(f"{label} debe conservar implementation_status dry_run.")
        if item.get("review_label") != "Revisar bases":
            errors.append(f"{label}.review_label debe ser Revisar bases.")
        for field in ("source_url", "listing_url"):
            if not _official_romeral_url(item.get(field)):
                errors.append(f"{label}.{field} debe ser URL oficial Romeral.")
        if item.get("detail_url_status") not in DETAIL_URL_STATUS:
            errors.append(f"{label}.detail_url_status no permitido.")
        status = item.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{label}.status no permitido.")
        if item.get("confidence") not in CONFIDENCE or not item.get("status_reason"):
            errors.append(f"{label} requiere confidence/status_reason validos.")
        if item.get("closing_date") is not None:
            try:
                date.fromisoformat(str(item["closing_date"]))
            except ValueError:
                errors.append(f"{label}.closing_date debe ser null o YYYY-MM-DD.")
        if item.get("published_date") is not None:
            try:
                date.fromisoformat(str(item["published_date"]))
            except ValueError:
                errors.append(f"{label}.published_date debe ser null o YYYY-MM-DD.")
        if status == "open_confirmed":
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
        documents = item.get("document_urls")
        if not isinstance(documents, list):
            errors.append(f"{label}.document_urls debe ser lista.")
        else:
            for document in documents:
                if not isinstance(document, dict) or not document.get("name") or not _official_romeral_url(document.get("url")):
                    errors.append(f"{label}.document_urls contiene URL no oficial Romeral.")
        if not isinstance(item.get("base_links"), list) or not isinstance(item.get("date_change_links"), list):
            errors.append(f"{label} debe separar base_links y date_change_links.")
        if not isinstance(item.get("evidence"), list) or not item.get("evidence"):
            errors.append(f"{label}.evidence debe contener trazabilidad.")
        if item.get("is_demo") is not False or item.get("url_status") != "ok":
            errors.append(f"{label} debe conservar URL real sin presentarse como demo.")
        errors.extend(opportunity_sanitization_errors(item, label))

    if len(ids) != len(set(ids)):
        errors.append("Los IDs Romeral deben ser unicos.")
    if not REPORT_PATH.exists():
        errors.append(f"No existe reporte local: {REPORT_PATH}")
    try:
        public_opportunities = _load_json(PUBLIC_OPPORTUNITIES_PATH)
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"No fue posible revisar {PUBLIC_OPPORTUNITIES_PATH}: {error}")
    else:
        published_romeral = [
            item
            for item in public_opportunities
            if isinstance(item, dict)
            and (
                str(item.get("id") or "").startswith("municipalidad-romeral-")
                or item.get("source") == "Municipalidad de Romeral"
            )
        ]
        if published_romeral:
            errors.append("Romeral debe permanecer aislado: se detectaron registros en public/data.")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    counts = {status: 0 for status in sorted(ALLOWED_STATUS)}
    for item in opportunities:
        if isinstance(item, dict) and item.get("status") in counts:
            counts[item["status"]] += 1
    print(
        "OK: dry-run Romeral valido "
        f"({len(opportunities)} publicaciones: "
        f"{counts['open_confirmed']} abiertas, {counts['closed']} cerradas, "
        f"{counts['manual_review']} manual_review; "
        f"bases={diagnostics.get('base_links_detected', 0)}, "
        f"cambio={'si' if diagnostics.get('source_change_detected') else 'no'})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
