"""Isolated dry-run adapter for Municipalidad de Curico contest publications."""

from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = "RadarLaboralPublicoChile/0.2 (+https://github.com/jeannorambuena/bot_empleos_publicos; dry-run source audit)"
TIMEOUT_SECONDS = 20
SOURCE_NAME = "Municipalidad de Curicó"
INSTITUTION = "Ilustre Municipalidad de Curicó"
SOURCE_ID = "municipalidad-curico"
ALLOWED_STATUS = {"open_confirmed", "closed", "manual_review"}
RESULT_MARKERS = ("seleccionado", "seleccionados", "nomina seleccionados")
DATE_PATTERN = r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})"
PUBLISHED_LABELS = ("fecha de publicacion", "fecha publicacion", "publicado el")
CLOSING_LABELS = (
    "fecha de cierre",
    "cierre de postulacion",
    "cierre postulacion",
    "plazo de postulacion hasta",
    "postulaciones hasta",
)
DOCUMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")


def fetch_curico_candidates(discovery_url: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch one configured listing page and its direct official detail pages."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    response = _get(session, discovery_url)

    soup = BeautifulSoup(response.text, "html.parser")
    detected_at = datetime.now().astimezone()
    opportunities: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    detail_errors: list[dict[str, str]] = []
    total_documents = 0

    articles = soup.select("article.category-concursos")
    for article in articles:
        link = article.select_one("h4.post-title a[href]")
        if link is None:
            continue
        source_url = str(link.get("href") or "").strip()
        title = _clean_text(link.get_text(" ", strip=True))
        listing_description = _clean_text(article.get_text(" ", strip=True))
        if not source_url or not title or source_url in seen_urls:
            continue
        seen_urls.add(source_url)

        detail_checked_at = datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            detail_response = _get(session, source_url)
            detail_soup = BeautifulSoup(detail_response.text, "html.parser")
            detail_text = _detail_text(detail_soup) or listing_description
            documents = _document_urls(detail_soup, source_url)
            total_documents += len(documents)
            published_date = _extract_labeled_date(detail_text, PUBLISHED_LABELS)
            closing_date = _extract_labeled_date(detail_text, CLOSING_LABELS)
            status, status_reason, confidence = _classify(title, detail_text, closing_date, detected_at.date())
            detail_url_status = "ok"
        except RuntimeError as error:
            detail_text = listing_description
            documents = []
            published_date = None
            closing_date = None
            status = "manual_review"
            status_reason = "No fue posible revisar la página de detalle oficial."
            confidence = "low"
            detail_url_status = "error"
            detail_errors.append({"title": title, "source_url": source_url, "error": str(error)})

        source_id = _source_id(article, source_url)
        manual_review = status == "manual_review"
        opportunities.append(
            {
                "id": f"municipalidad-curico-{source_id}",
                "source_id": source_id,
                "title": title,
                "institution": INSTITUTION,
                "source": SOURCE_NAME,
                "source_url": source_url,
                "listing_url": discovery_url,
                "region": "Maule",
                "commune": "Curicó",
                "closing_date": closing_date,
                "published_date": published_date,
                "detected_at": detected_at.isoformat(timespec="seconds"),
                "detail_checked_at": detail_checked_at,
                "detail_url_status": detail_url_status,
                "status": status,
                "status_reason": status_reason,
                "confidence": confidence,
                "description": detail_text[:1000],
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

    status_counts = {status: 0 for status in sorted(ALLOWED_STATUS)}
    for item in opportunities:
        status_counts[item["status"]] += 1
    diagnostics = {
        "source_id": SOURCE_ID,
        "source": SOURCE_NAME,
        "listing_url": discovery_url,
        "http_status": response.status_code,
        "articles_reviewed": len(articles),
        "details_checked": len(opportunities),
        "documents_detected": total_documents,
        "status_counts": status_counts,
        "detail_errors": detail_errors,
        "notes": "Dry-run R2 aislado: revisa solo listado y páginas de detalle oficiales directas; no sigue paginación ni descarga documentos.",
    }
    return opportunities, diagnostics


def _get(session: requests.Session, url: str) -> requests.Response:
    if not _is_official_curico_url(url):
        raise RuntimeError(f"URL fuera del dominio oficial Curicó: {url}")
    try:
        response = session.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response
    except requests.RequestException as error:
        raise RuntimeError(f"No fue posible consultar {url}: {error}") from error


def _detail_text(soup: BeautifulSoup) -> str:
    node = soup.select_one("article") or soup.select_one(".entry-content") or soup.select_one("main")
    return _clean_text(node.get_text(" ", strip=True)) if node else ""


def _document_urls(soup: BeautifulSoup, source_url: str) -> list[dict[str, str]]:
    documents = []
    seen_urls = set()
    for link in soup.select("a[href]"):
        url = str(link.get("href") or "").strip()
        name = _clean_text(link.get_text(" ", strip=True)) or url.rsplit("/", 1)[-1]
        if not url or url in seen_urls or not _is_official_curico_url(url):
            continue
        path = urlparse(url).path.lower()
        if not path.endswith(DOCUMENT_EXTENSIONS):
            continue
        seen_urls.add(url)
        documents.append({"name": name, "url": url})
    return documents


def _extract_labeled_date(text: str, labels: tuple[str, ...]) -> str | None:
    folded = _fold_text(text)
    for label in labels:
        match = re.search(rf"{re.escape(label)}[^0-9]{{0,50}}{DATE_PATTERN}", folded)
        if not match:
            continue
        try:
            return date(int(match.group(3)), int(match.group(2)), int(match.group(1))).isoformat()
        except ValueError:
            continue
    return None


def _classify(title: str, detail_text: str, closing_date: str | None, today: date) -> tuple[str, str, str]:
    if _is_result_publication(title, detail_text):
        return "closed", "La publicación contiene evidencia textual de resultado de selección.", "high"
    if closing_date:
        parsed_closing_date = date.fromisoformat(closing_date)
        if parsed_closing_date >= today:
            return "open_confirmed", "La página de detalle publica una fecha de cierre vigente.", "high"
        return "closed", "La página de detalle publica una fecha de cierre ya vencida.", "high"
    return "manual_review", "La página de detalle no publica una fecha de cierre ni vigencia inequívoca.", "low"


def _evidence(
    published_date: str | None,
    closing_date: str | None,
    documents: list[dict[str, str]],
    status_reason: str,
) -> list[str]:
    evidence = [status_reason]
    if published_date:
        evidence.append(f"Fecha de publicación explícita: {published_date}")
    if closing_date:
        evidence.append(f"Fecha de cierre explícita: {closing_date}")
    if documents:
        evidence.append(f"Documentos oficiales enlazados: {len(documents)}")
    return evidence


def _source_id(article: Any, source_url: str) -> str:
    for class_name in article.get("class", []):
        match = re.fullmatch(r"post-(\d+)", str(class_name))
        if match:
            return match.group(1)
    slug = source_url.rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"[^a-z0-9-]+", "-", _fold_text(slug)).strip("-") or "sin-id"


def _is_result_publication(title: str, description: str) -> bool:
    folded = _fold_text(f"{title} {description}")
    return any(marker in folded for marker in RESULT_MARKERS)


def _is_official_curico_url(url: str) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return hostname == "curico.cl" or hostname.endswith(".curico.cl")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))
