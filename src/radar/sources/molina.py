"""Isolated dry-run adapter for Municipalidad de Molina contest publications."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from radar.sources.sanitization import sanitize_opportunity


USER_AGENT = "RadarLaboralPublicoChile/0.2 (+https://github.com/jeannorambuena/bot_empleos_publicos; dry-run source audit)"
TIMEOUT_SECONDS = 20
SOURCE_NAME = "Municipalidad de Molina"
INSTITUTION = "Ilustre Municipalidad de Molina"
SOURCE_ID = "municipalidad-molina"
ALLOWED_STATUS = {"open_confirmed", "closed", "manual_review"}
DATE_PATTERN = r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})"
CLOSING_LABELS = (
    "fecha de cierre",
    "cierre de postulacion",
    "cierre postulacion",
    "postulaciones hasta",
)
DOCUMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")
CLOSED_MARKERS = ("concurso cerrado", "proceso cerrado", "seleccionado", "seleccionados")


def fetch_molina_candidates(discovery_url: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch the configured listing page without downloading linked documents."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    response = _get(session, discovery_url)
    soup = BeautifulSoup(response.text, "html.parser")
    content = soup.select_one(".td-page-content.tagdiv-type")
    if content is None:
        raise RuntimeError("La página oficial de Molina no contiene el bloque esperado de concursos.")

    detected_at = datetime.now().astimezone()
    opportunities: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    listing_items = [_clean_text(item.get_text(" ", strip=True)) for item in content.select("li")]
    for item in content.select("li"):
        title = _clean_text(item.get_text(" ", strip=True))
        if not title:
            continue
        link = item.select_one("a[href]")
        href = str(link.get("href") or "").strip() if link else ""
        source_url = href if _is_official_source_url(href) else discovery_url
        source_id = _stable_source_id(source_url, title)
        if source_id in seen_ids:
            continue
        seen_ids.add(source_id)

        published_date = _extract_prefixed_date(title)
        closing_date = _extract_labeled_date(title, CLOSING_LABELS)
        status, status_reason, confidence = _classify(title, closing_date, detected_at.date())
        documents = _document_urls(href, title)
        manual_review = status == "manual_review"
        opportunities.append(
            sanitize_opportunity(
            {
                "id": f"municipalidad-molina-{source_id}",
                "source_id": source_id,
                "title": title,
                "institution": INSTITUTION,
                "source": SOURCE_NAME,
                "source_url": source_url,
                "listing_url": discovery_url,
                "region": "Maule",
                "commune": "Molina",
                "closing_date": closing_date,
                "published_date": published_date,
                "detected_at": detected_at.isoformat(timespec="seconds"),
                "detail_checked_at": None,
                "detail_url_status": _link_type(href),
                "status": status,
                "status_reason": status_reason,
                "confidence": confidence,
                "description": title,
                "tags": ["municipalidad", "concurso", "dry_run"],
                "document_urls": documents,
                "evidence": _evidence(published_date, closing_date, documents, status_reason),
                "is_demo": False,
                "url_status": "ok",
                "implementation_status": "dry_run",
                "manual_review": manual_review,
                "manual_review_reason": status_reason if manual_review else None,
            }
            )
        )

    status_counts = {status: 0 for status in sorted(ALLOWED_STATUS)}
    for item in opportunities:
        status_counts[item["status"]] += 1
    diagnostics = {
        "source_id": SOURCE_ID,
        "source": SOURCE_NAME,
        "listing_url": discovery_url,
        "http_status": response.status_code,
        "listing_items_reviewed": len([item for item in listing_items if item]),
        "publications_detected": len(opportunities),
        "documents_detected": sum(len(item["document_urls"]) for item in opportunities),
        "external_official_links": sum(item["detail_url_status"] == "external_official" for item in opportunities),
        "status_counts": status_counts,
        "notes": "Dry-run aislado: consulta una sola página oficial; no sigue enlaces ni descarga documentos.",
    }
    return opportunities, diagnostics


def _get(session: requests.Session, url: str) -> requests.Response:
    if not _is_official_molina_url(url):
        raise RuntimeError(f"URL fuera del dominio oficial Molina: {url}")
    try:
        response = session.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response
    except requests.RequestException as error:
        raise RuntimeError(f"No fue posible consultar {url}: {error}") from error


def _document_urls(url: str, title: str) -> list[dict[str, str]]:
    if not _is_official_molina_url(url):
        return []
    if not urlparse(url).path.lower().endswith(DOCUMENT_EXTENSIONS):
        return []
    return [{"name": title, "url": url}]


def _extract_prefixed_date(text: str) -> str | None:
    match = re.match(rf"^\s*\({DATE_PATTERN}\)", text)
    return _iso_date(match) if match else None


def _extract_labeled_date(text: str, labels: tuple[str, ...]) -> str | None:
    folded = _fold_text(text)
    for label in labels:
        match = re.search(rf"{re.escape(label)}[^0-9]{{0,50}}{DATE_PATTERN}", folded)
        if match:
            return _iso_date(match)
    return None


def _iso_date(match: re.Match[str]) -> str | None:
    try:
        return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()
    except ValueError:
        return None


def _classify(title: str, closing_date: str | None, today: date) -> tuple[str, str, str]:
    folded = _fold_text(title)
    if any(marker in folded for marker in CLOSED_MARKERS):
        return "closed", "El listado oficial contiene evidencia textual de cierre o resultado.", "high"
    if closing_date:
        parsed_closing_date = date.fromisoformat(closing_date)
        if parsed_closing_date >= today:
            return "open_confirmed", "El listado oficial publica una fecha de cierre vigente.", "high"
        return "closed", "El listado oficial publica una fecha de cierre ya vencida.", "high"
    return "manual_review", "El listado oficial no publica una fecha de cierre ni vigencia inequívoca.", "low"


def _evidence(
    published_date: str | None,
    closing_date: str | None,
    documents: list[dict[str, str]],
    status_reason: str,
) -> list[str]:
    evidence = [status_reason]
    if published_date:
        evidence.append(f"Fecha visible en el listado, tratada como publicación: {published_date}")
    if closing_date:
        evidence.append(f"Fecha de cierre explícita: {closing_date}")
    if documents:
        evidence.append(f"Documentos oficiales enlazados sin descarga: {len(documents)}")
    return evidence


def _stable_source_id(source_url: str, title: str) -> str:
    digest = hashlib.sha256(f"{source_url}\n{_fold_text(title)}".encode("utf-8")).hexdigest()
    return digest[:16]


def _link_type(url: str) -> str:
    if not url:
        return "listing_only"
    if _is_official_molina_url(url) and urlparse(url).path.lower().endswith(DOCUMENT_EXTENSIONS):
        return "document"
    if _is_official_source_url(url):
        return "external_official"
    return "listing_only"


def _is_official_source_url(url: str) -> bool:
    return _is_official_molina_url(url) or _is_empleos_publicos_url(url)


def _is_official_molina_url(url: str) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return hostname == "molina.cl" or hostname.endswith(".molina.cl")


def _is_empleos_publicos_url(url: str) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return hostname == "empleospublicos.cl" or hostname.endswith(".empleospublicos.cl")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))
