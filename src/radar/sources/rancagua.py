"""Isolated dry-run adapter for Municipalidad de Rancagua OMIL publications."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup


USER_AGENT = "RadarLaboralPublicoChile/0.2 (+https://github.com/jeannorambuena/bot_empleos_publicos; dry-run source audit)"
TIMEOUT_SECONDS = 20
SOURCE_NAME = "Municipalidad de Rancagua"
INSTITUTION = "Ilustre Municipalidad de Rancagua"
SOURCE_ID = "municipalidad-rancagua"
ALLOWED_STATUS = {"open_confirmed", "closed", "manual_review"}
CONTENT_NAMESPACE = "{http://purl.org/rss/1.0/modules/content/}encoded"
DATE_PATTERN = r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})"
CLOSING_LABELS = ("postulacion hasta", "fecha de cierre", "cierre de postulacion")
CLOSED_MARKERS = ("cerrada", "cerrado", "seleccionado", "adjudicado", "nombramiento")
DOCUMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")


def fetch_rancagua_candidates(discovery_url: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch one configured HTML page and its advertised official OMIL RSS feed."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    response = _get(session, discovery_url)
    feed_url = _discover_feed_url(response.text, discovery_url)
    feed_response = _get(session, feed_url)
    try:
        root = ElementTree.fromstring(feed_response.content)
    except ElementTree.ParseError as error:
        raise RuntimeError(f"El RSS oficial Rancagua no contiene XML válido: {error}") from error

    detected_at = datetime.now().astimezone()
    opportunities: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    total_documents = 0
    for item in root.findall("./channel/item"):
        title = _clean_text(_item_text(item, "title"))
        source_url = _item_text(item, "link") or _item_text(item, "guid")
        if not title or not _is_official_source_url(source_url):
            continue
        source_id = _stable_source_id(source_url)
        if source_id in seen_ids:
            continue
        seen_ids.add(source_id)

        description_html = _item_text(item, "description")
        content_html = _item_text(item, CONTENT_NAMESPACE)
        description = _html_text(description_html)
        content_text = _html_text(content_html)
        categories = [_clean_text(node.text or "") for node in item.findall("category") if _clean_text(node.text or "")]
        offer_scope = _offer_scope(categories)
        published_date = _published_date(_item_text(item, "pubDate"))
        closing_date = _extract_labeled_date(content_text, CLOSING_LABELS)
        documents = _document_urls(content_html)
        total_documents += len(documents)
        status, status_reason, confidence = _classify(
            categories,
            f"{description} {content_text}",
            closing_date,
            detected_at.date(),
            offer_scope,
        )
        manual_review = status == "manual_review"
        opportunities.append(
            {
                "id": f"municipalidad-rancagua-{source_id}",
                "source_id": source_id,
                "title": title,
                "institution": INSTITUTION,
                "source": SOURCE_NAME,
                "source_url": source_url,
                "listing_url": discovery_url,
                "feed_url": feed_url,
                "region": "O'Higgins",
                "commune": "Rancagua",
                "closing_date": closing_date,
                "published_date": published_date,
                "detected_at": detected_at.isoformat(timespec="seconds"),
                "detail_checked_at": None,
                "detail_url_status": "feed_only",
                "status": status,
                "status_reason": status_reason,
                "confidence": confidence,
                "description": description or content_text[:1000],
                "tags": ["municipalidad", "omil", "oferta_laboral", "dry_run"],
                "categories": categories,
                "offer_scope": offer_scope,
                "document_urls": documents,
                "evidence": _evidence(published_date, closing_date, documents, offer_scope, status_reason),
                "is_demo": False,
                "url_status": "ok",
                "implementation_status": "dry_run",
                "manual_review": manual_review,
                "manual_review_reason": status_reason if manual_review else None,
            }
        )

    status_counts = {status: 0 for status in sorted(ALLOWED_STATUS)}
    for opportunity in opportunities:
        status_counts[opportunity["status"]] += 1
    diagnostics = {
        "source_id": SOURCE_ID,
        "source": SOURCE_NAME,
        "listing_url": discovery_url,
        "feed_url": feed_url,
        "http_status": response.status_code,
        "feed_http_status": feed_response.status_code,
        "publications_detected": len(opportunities),
        "source_links_detected": len(opportunities),
        "municipal_offers": sum(item["offer_scope"] == "municipal" for item in opportunities),
        "external_private_offers": sum(item["offer_scope"] == "external_private" for item in opportunities),
        "documents_detected": total_documents,
        "status_counts": status_counts,
        "notes": "Dry-run aislado: consulta página oficial y RSS anunciado; no sigue fichas ni descarga documentos. Ofertas externas OMIL quedan manual_review.",
    }
    return opportunities, diagnostics


def _get(session: requests.Session, url: str) -> requests.Response:
    if not _is_official_rancagua_url(url):
        raise RuntimeError(f"URL fuera del dominio institucional Rancagua: {url}")
    try:
        response = session.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response
    except requests.RequestException as error:
        raise RuntimeError(f"No fue posible consultar {url}: {error}") from error


def _discover_feed_url(html: str, discovery_url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one('link[type="application/rss+xml"][href*="ofertas-laborales"]')
    if link is None:
        raise RuntimeError("La página oficial Rancagua no anuncia el RSS esperado de ofertas laborales.")
    feed_url = urljoin(discovery_url, str(link.get("href") or "").strip())
    if not _is_official_rancagua_url(feed_url):
        raise RuntimeError(f"El RSS anunciado no pertenece al dominio institucional Rancagua: {feed_url}")
    return feed_url


def _item_text(item: Any, field: str) -> str:
    node = item.find(field)
    return (node.text or "").strip() if node is not None else ""


def _published_date(value: str) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError):
        return None


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


def _document_urls(html: str) -> list[dict[str, str]]:
    documents = []
    seen_urls = set()
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.select("a[href]"):
        url = str(link.get("href") or "").strip()
        name = _clean_text(link.get_text(" ", strip=True)) or url.rsplit("/", 1)[-1]
        if not url or url in seen_urls or not _is_institutional_rancagua_url(url):
            continue
        if not urlparse(url).path.lower().endswith(DOCUMENT_EXTENSIONS):
            continue
        seen_urls.add(url)
        documents.append({"name": name, "url": url})
    return documents


def _offer_scope(categories: list[str]) -> str:
    folded = {_fold_text(category) for category in categories}
    if "municipal" in folded:
        return "municipal"
    if "externa" in folded:
        return "external_private"
    return "unknown"


def _classify(
    categories: list[str],
    text: str,
    closing_date: str | None,
    today: date,
    offer_scope: str,
) -> tuple[str, str, str]:
    folded = _fold_text(f"{' '.join(categories)} {text}")
    if any(marker in folded for marker in CLOSED_MARKERS):
        return "closed", "El RSS oficial contiene evidencia textual de cierre o resultado.", "high"
    if closing_date and date.fromisoformat(closing_date) < today:
        return "closed", "El RSS oficial publica una fecha de cierre ya vencida.", "high"
    if offer_scope == "external_private":
        return "manual_review", "Oferta externa OMIL: requiere revisión y no debe tratarse como empleo público.", "low"
    if closing_date and date.fromisoformat(closing_date) >= today and "abierta" in folded and offer_scope == "municipal":
        return "open_confirmed", "Oferta municipal con categoría abierta y fecha de cierre futura explícita.", "high"
    return "manual_review", "El RSS oficial no permite confirmar una convocatoria pública municipal vigente.", "low"


def _evidence(
    published_date: str | None,
    closing_date: str | None,
    documents: list[dict[str, str]],
    offer_scope: str,
    status_reason: str,
) -> list[str]:
    evidence = [status_reason, f"Ámbito publicado en RSS: {offer_scope}"]
    if published_date:
        evidence.append(f"Fecha de publicación RSS: {published_date}")
    if closing_date:
        evidence.append(f"Fecha de cierre explícita: {closing_date}")
    if documents:
        evidence.append(f"Documentos institucionales enlazados sin descarga: {len(documents)}")
    return evidence


def _stable_source_id(source_url: str) -> str:
    slug = urlparse(source_url).path.rstrip("/").rsplit("/", 1)[-1]
    return re.sub(r"[^a-z0-9-]+", "-", _fold_text(slug)).strip("-") or hashlib.sha256(source_url.encode()).hexdigest()[:16]


def _html_text(value: str) -> str:
    return _clean_text(BeautifulSoup(value, "html.parser").get_text(" ", strip=True))


def _is_official_source_url(url: str) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return hostname == "rgua.cl" or hostname.endswith(".rgua.cl") or _is_official_rancagua_url(url)


def _is_official_rancagua_url(url: str) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return hostname == "munirancagua.gob.cl" or hostname.endswith(".munirancagua.gob.cl")


def _is_institutional_rancagua_url(url: str) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return (
        _is_official_rancagua_url(url)
        or hostname == "rancagua.cl"
        or hostname.endswith(".rancagua.cl")
    )


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))
