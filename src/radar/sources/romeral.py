"""Dry-run monitor for Municipalidad de Romeral public contests."""

from __future__ import annotations

import hashlib
import queue
import re
import threading
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from radar.sources.sanitization import has_sensitive_personal_data, sanitize_opportunity


USER_AGENT = "RadarLaboralPublicoChile/0.2 (+https://github.com/jeannorambuena/bot_empleos_publicos; dry-run source audit)"
TIMEOUT_SECONDS = 5
SOURCE_NAME = "Municipalidad de Romeral"
INSTITUTION = "Ilustre Municipalidad de Romeral"
SOURCE_ID = "municipalidad-romeral"
DEFAULT_DISCOVERY_URL = "https://muniromeral.cl/romeral/?page_id=3217"
ALLOWED_STATUS = {"open_confirmed", "closed", "manual_review"}
DOCUMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")
BASE_LINK_MARKERS = ("base", "bases")
DATE_CHANGE_MARKERS = ("modificacion de fecha", "modificación de fecha", "cambio de fecha", "cambio fechas")
CONTEST_MARKERS = ("concurso publico", "concurso público", "llamado a concurso")
CLOSED_MARKERS = ("finalizado", "desierto", "cerrado", "resultado", "resultados", "acta", "nomina", "nómina", "seleccion")
MONTHS = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}
VISIBLE_DATE_PATTERN = re.compile(
    r"\b(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+(\d{4})\b",
    re.IGNORECASE,
)


@dataclass
class _FetchedPage:
    text: str
    status_code: int


class _RomeralHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[dict[str, Any]] = []
        self._in_paragraph = False
        self._current_text: list[str] = []
        self._current_links: list[dict[str, str]] = []
        self._active_href: str | None = None
        self._active_link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "p":
            self._in_paragraph = True
            self._current_text = []
            self._current_links = []
        if self._in_paragraph and tag.lower() == "a":
            href = dict(attrs).get("href")
            self._active_href = str(href or "").strip() or None
            self._active_link_text = []

    def handle_endtag(self, tag: str) -> None:
        if self._in_paragraph and tag.lower() == "a" and self._active_href:
            name = _clean_text(" ".join(self._active_link_text))
            self._current_links.append({"name": name, "url": self._active_href})
            self._active_href = None
            self._active_link_text = []
        if tag.lower() == "p" and self._in_paragraph:
            text = _clean_text(" ".join(self._current_text))
            if text or self._current_links:
                self.paragraphs.append({"text": text, "links": list(self._current_links)})
            self._in_paragraph = False

    def handle_data(self, data: str) -> None:
        if not self._in_paragraph:
            return
        self._current_text.append(data)
        if self._active_href:
            self._active_link_text.append(data)


def fetch_romeral_candidates(
    discovery_url: str = DEFAULT_DISCOVERY_URL,
    *,
    previous_state: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Fetch listing pages and return dry-run opportunities plus monitor state."""
    detected_at = datetime.now().astimezone()
    pages = []
    errors: list[dict[str, str]] = []
    for url in _candidate_page_urls(discovery_url):
        try:
            response = _get_with_deadline(url)
        except RuntimeError as error:
            errors.append({"url": url, "error": str(error)})
            continue
        paragraphs = _parse_paragraphs(response.text)
        normalized_listing = _normalized_listing_text(paragraphs)
        pages.append(
            {
                "url": url,
                "status_code": response.status_code,
                "normalized_text": normalized_listing,
                "hash": _hash(normalized_listing),
                "paragraphs": paragraphs,
            }
        )

    if not pages:
        raise RuntimeError("No fue posible consultar ninguna pagina oficial de Romeral.")

    combined_text = "\n\n".join(page["normalized_text"] for page in pages if page["normalized_text"])
    listing_hash = _hash(combined_text)
    previous_hash = str((previous_state or {}).get("listing_hash") or "")
    source_change_detected = not previous_hash or previous_hash != listing_hash

    opportunities_by_id: dict[str, dict[str, Any]] = {}
    for page in pages:
        for raw_item in _extract_publications(page["paragraphs"], page["url"], detected_at):
            source_id = raw_item["source_id"]
            existing = opportunities_by_id.get(source_id)
            if existing is None:
                opportunities_by_id[source_id] = raw_item
                continue
            existing["document_urls"].extend(
                document
                for document in raw_item["document_urls"]
                if document not in existing["document_urls"]
            )
            existing["evidence"].extend(
                evidence
                for evidence in raw_item["evidence"]
                if evidence not in existing["evidence"]
            )

    opportunities = []
    for item in opportunities_by_id.values():
        item["source_change_detected"] = source_change_detected
        item["listing_hash"] = listing_hash
        opportunities.append(sanitize_opportunity(item))
    opportunities.sort(key=lambda item: (item.get("published_date") or "", item.get("title") or ""), reverse=True)

    status_counts = {status: 0 for status in sorted(ALLOWED_STATUS)}
    for item in opportunities:
        status_counts[item["status"]] += 1
    state = {
        "source_id": SOURCE_ID,
        "source": SOURCE_NAME,
        "listing_url": discovery_url,
        "listing_hash": listing_hash,
        "page_hashes": [{"url": page["url"], "hash": page["hash"]} for page in pages],
        "last_checked_at": detected_at.isoformat(timespec="seconds"),
        "last_publication_ids": [item["source_id"] for item in opportunities],
    }
    diagnostics = {
        "source_id": SOURCE_ID,
        "source": SOURCE_NAME,
        "listing_url": discovery_url,
        "pages_checked": [{"url": page["url"], "status_code": page["status_code"], "hash": page["hash"]} for page in pages],
        "page_errors": errors,
        "listing_hash": listing_hash,
        "previous_listing_hash": previous_hash or None,
        "source_change_detected": source_change_detected,
        "publications_detected": len(opportunities),
        "documents_detected": sum(len(item["document_urls"]) for item in opportunities),
        "base_links_detected": sum(1 for item in opportunities if item.get("base_links")),
        "date_change_links_detected": sum(1 for item in opportunities if item.get("date_change_links")),
        "status_counts": status_counts,
        "local_priority": True,
        "implementation_status": "dry_run",
        "telegram_notice": (
            "Cambio detectado en concursos Romeral: revisar publicacion."
            if source_change_detected and opportunities
            else None
        ),
        "notes": (
            "Dry-run local prioritario: detecta cambios por hash normalizado del listado y "
            "crea oportunidades solo para publicaciones con senales de concurso laboral. "
            "No descarga documentos ni publica automaticamente."
        ),
    }
    return opportunities, diagnostics, state


def _candidate_page_urls(discovery_url: str) -> list[str]:
    urls = [discovery_url]
    for page_number in (2, 3):
        urls.append(_with_query(discovery_url, "page", str(page_number)))
    seen = set()
    unique = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def _with_query(url: str, key: str, value: str) -> str:
    parsed = urlparse(url)
    pairs = dict(parse_qsl(parsed.query, keep_blank_values=True))
    pairs[key] = value
    return urlunparse(parsed._replace(query=urlencode(pairs)))


def _get(url: str) -> _FetchedPage:
    if not _is_official_romeral_url(url):
        raise RuntimeError(f"URL fuera del dominio oficial Romeral: {url}")
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT, "Connection": "close"})
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            raw = response.read()
            encoding = response.headers.get_content_charset() or "utf-8"
            return _FetchedPage(text=raw.decode(encoding, errors="replace"), status_code=response.status)
    except HTTPError as error:
        raise RuntimeError(f"No fue posible consultar {url}: HTTP {error.code}") from error
    except (URLError, TimeoutError, OSError) as error:
        raise RuntimeError(f"No fue posible consultar {url}: {error}") from error


def _get_with_deadline(url: str) -> _FetchedPage:
    results: queue.Queue[tuple[str, _FetchedPage | Exception]] = queue.Queue(maxsize=1)

    def worker() -> None:
        try:
            results.put(("ok", _get(url)))
        except Exception as error:  # noqa: BLE001 - propagate as controlled source error.
            results.put(("error", error))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    try:
        status, payload = results.get(timeout=TIMEOUT_SECONDS + 2)
    except queue.Empty as error:
        raise RuntimeError("timeout total al consultar pagina oficial") from error
    if status == "error":
        raise RuntimeError(str(payload))
    return payload  # type: ignore[return-value]


def _parse_paragraphs(html: str) -> list[dict[str, Any]]:
    parser = _RomeralHTMLParser()
    parser.feed(html)
    return parser.paragraphs


def _extract_publications(paragraphs: list[dict[str, Any]], listing_url: str, detected_at: datetime) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    index = 0
    while index < len(paragraphs):
        date_text = _clean_text(str(paragraphs[index].get("text") or ""))
        published_date = _extract_visible_date(date_text)
        if not published_date:
            index += 1
            continue

        title_index = _next_text_index(paragraphs, index + 1)
        if title_index is None:
            index += 1
            continue
        title = _clean_text(str(paragraphs[title_index].get("text") or ""))
        if not _looks_like_contest(title):
            index += 1
            continue

        block_nodes = [paragraphs[index], paragraphs[title_index]]
        cursor = title_index + 1
        while cursor < len(paragraphs) and not _extract_visible_date(_clean_text(str(paragraphs[cursor].get("text") or ""))):
            block_nodes.append(paragraphs[cursor])
            cursor += 1

        item = _build_item(
            title=title,
            date_text=date_text,
            published_date=published_date,
            block_nodes=block_nodes,
            listing_url=listing_url,
            detected_at=detected_at,
        )
        if item:
            items.append(item)
        index = cursor
    return items


def _build_item(
    *,
    title: str,
    date_text: str,
    published_date: str,
    block_nodes: list[Any],
    listing_url: str,
    detected_at: datetime,
) -> dict[str, Any] | None:
    block_text = _clean_text(" ".join(str(node.get("text") or "") for node in block_nodes))
    source_id = _stable_source_id(title, published_date, block_text)
    documents = _document_urls(block_nodes, listing_url)
    base_links = [document for document in documents if _is_base_link(document["name"], document["url"])]
    date_change_links = [document for document in documents if _is_date_change_link(document["name"], document["url"])]
    status, status_reason, confidence = _classify(date_text, title, block_text, detected_at.date())
    manual_review = status != "open_confirmed"
    manual_reason = status_reason if manual_review else None
    if has_sensitive_personal_data(block_text):
        status = "manual_review"
        status_reason = "La publicacion contiene posible dato personal o resultado; requiere revision manual."
        confidence = "low"
        manual_review = True
        manual_reason = status_reason

    return {
        "id": f"municipalidad-romeral-{source_id}",
        "source_id": source_id,
        "title": title,
        "institution": INSTITUTION,
        "source": SOURCE_NAME,
        "source_url": listing_url,
        "listing_url": listing_url,
        "region": "Maule",
        "commune": "Romeral",
        "closing_date": None,
        "published_date": published_date,
        "visible_date": date_text,
        "detected_at": detected_at.isoformat(timespec="seconds"),
        "detail_checked_at": None,
        "detail_url_status": "listing_only",
        "status": status,
        "status_reason": status_reason,
        "confidence": confidence,
        "description": block_text[:1000],
        "tags": ["municipalidad", "romeral", "concurso", "local_priority", "dry_run", "revisar_bases"],
        "document_urls": documents,
        "base_links": base_links,
        "date_change_links": date_change_links,
        "evidence": _evidence(published_date, base_links, date_change_links, status_reason),
        "is_demo": False,
        "url_status": "ok",
        "implementation_status": "dry_run",
        "offer_scope": "municipal",
        "local_priority": True,
        "manual_review": manual_review,
        "manual_review_reason": manual_reason,
        "review_label": "Revisar bases",
    }


def _next_text_index(paragraphs: list[dict[str, Any]], start: int) -> int | None:
    for index in range(start, len(paragraphs)):
        if _clean_text(str(paragraphs[index].get("text") or "")):
            return index
    return None


def _document_urls(nodes: list[Any], listing_url: str) -> list[dict[str, str]]:
    documents = []
    seen = set()
    for node in nodes:
        for link in node.get("links") or []:
            url = urljoin(listing_url, str(link.get("url") or "").strip())
            name = _clean_text(str(link.get("name") or "")) or url.rsplit("/", 1)[-1]
            if not _is_official_romeral_url(url) or url in seen:
                continue
            if not urlparse(url).path.lower().endswith(DOCUMENT_EXTENSIONS):
                continue
            seen.add(url)
            documents.append({"name": name, "url": url})
    return documents


def _classify(date_text: str, title: str, block_text: str, today: date) -> tuple[str, str, str]:
    folded = _fold_text(f"{date_text} {title} {block_text}")
    published_date = _extract_visible_date(date_text)
    if any(marker in folded for marker in CLOSED_MARKERS):
        return "closed", "La publicacion contiene evidencia de cierre, resultado, finalizado o desierto.", "high"
    if published_date and date.fromisoformat(published_date) < today:
        return "closed", "La fecha visible de publicacion es anterior al corte actual y no hay cierre vigente confiable.", "medium"
    return "manual_review", "Publicacion con senales de concurso, pero sin fecha de cierre confiable; revisar bases.", "low"


def _evidence(
    published_date: str,
    base_links: list[dict[str, str]],
    date_change_links: list[dict[str, str]],
    status_reason: str,
) -> list[str]:
    evidence = [status_reason, f"Fecha visible en el listado: {published_date}"]
    if base_links:
        evidence.append(f"Enlaces a bases detectados: {len(base_links)}")
    if date_change_links:
        evidence.append(f"Enlaces de modificacion de fechas detectados: {len(date_change_links)}")
    return evidence


def _normalized_listing_text(paragraphs: list[dict[str, Any]]) -> str:
    lines = []
    for paragraph in paragraphs:
        text = _clean_text(str(paragraph.get("text") or ""))
        links = " ".join(str(link.get("url") or "") for link in paragraph.get("links") or [])
        if text or links:
            lines.append(f"{text} {links}".strip())
    return _fold_text("\n".join(lines))


def _extract_visible_date(text: str) -> str | None:
    if len(text) > 120:
        return None
    match = VISIBLE_DATE_PATTERN.search(text)
    if not match:
        return None
    month = MONTHS.get(_fold_text(match.group(2)))
    if not month:
        return None
    try:
        return date(int(match.group(3)), month, int(match.group(1))).isoformat()
    except ValueError:
        return None


def _looks_like_contest(text: str) -> bool:
    folded = _fold_text(text)
    return any(marker in folded for marker in CONTEST_MARKERS)


def _is_base_link(name: str, url: str) -> bool:
    folded = _fold_text(f"{name} {url}")
    return any(marker in folded for marker in BASE_LINK_MARKERS)


def _is_date_change_link(name: str, url: str) -> bool:
    folded = _fold_text(f"{name} {url}")
    return any(marker in folded for marker in DATE_CHANGE_MARKERS)


def _stable_source_id(title: str, published_date: str, block_text: str) -> str:
    return _hash(f"{published_date}\n{_fold_text(title)}\n{_fold_text(block_text)}")[:16]


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_official_romeral_url(url: str) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return hostname == "muniromeral.cl" or hostname.endswith(".muniromeral.cl")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return normalized.encode("ascii", "ignore").decode("ascii")
