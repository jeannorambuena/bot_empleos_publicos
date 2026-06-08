"""Shared dry-run monitor for local municipal contest pages."""

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
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from radar.sources.sanitization import has_sensitive_personal_data, sanitize_opportunity


USER_AGENT = "RadarLaboralPublicoChile/0.2 (+https://github.com/jeannorambuena/bot_empleos_publicos; dry-run source audit)"
TIMEOUT_SECONDS = 7
ALLOWED_STATUS = {"open_confirmed", "closed", "manual_review"}
DOCUMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")
BASE_LINK_MARKERS = ("base", "bases", "perfil", "ficha")
APPLICATION_LINK_MARKERS = ("postula", "postular", "empleospublicos", "formulario")
CONTEST_MARKERS = (
    "concurso publico",
    "concursos publicos",
    "concurso",
    "llamado a concurso",
    "convocatoria",
    "cargo",
    "vacante",
    "seleccion",
    "bases",
    "postulacion",
    "oferta laboral",
)
CLOSED_MARKERS = (
    "finalizado",
    "desierto",
    "cerrado",
    "resultado",
    "resultados",
    "acta",
    "nomina",
    "seleccionado",
    "seleccionados",
    "admisibilidad",
    "evaluacion",
)
DEFAULT_NON_LABOR_MARKERS = (
    "reina",
    "pintura",
    "literario",
    "cultura",
    "subvencion",
    "premio",
    "beca",
    "remate",
    "licitacion",
)
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
VISIBLE_DATE_PATTERN = re.compile(r"\b(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+(\d{4})\b", re.IGNORECASE)
NUMERIC_DATE_PATTERN = re.compile(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b")
CLOSING_LABELS = (
    "fecha de cierre",
    "cierre de postulacion",
    "cierre postulacion",
    "plazo de postulacion",
    "postulaciones hasta",
    "recepcion de antecedentes hasta",
)


@dataclass(frozen=True)
class MunicipalSourceConfig:
    key: str
    source_id: str
    source_name: str
    institution: str
    commune: str
    urls: tuple[str, ...]
    allowed_hosts: tuple[str, ...]
    non_labor_markers: tuple[str, ...] = DEFAULT_NON_LABOR_MARKERS


@dataclass
class _FetchedPage:
    text: str
    status_code: int


class _BlockHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict[str, Any]] = []
        self._stack: list[dict[str, Any]] = []
        self._active_href: str | None = None
        self._active_link_text: list[str] = []
        self._all_text: list[str] = []
        self._all_links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in {"article", "li", "tr", "p", "h1", "h2", "h3", "h4", "h5"}:
            self._stack.append({"tag": lowered, "text": [], "links": []})
        if lowered == "a":
            href = dict(attrs).get("href")
            self._active_href = str(href or "").strip() or None
            self._active_link_text = []

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "a" and self._active_href:
            name = _clean_text(" ".join(self._active_link_text))
            link = {"name": name, "url": self._active_href}
            self._all_links.append(link)
            if self._stack:
                self._stack[-1]["links"].append(link)
            self._active_href = None
            self._active_link_text = []
            return
        if self._stack and lowered == self._stack[-1]["tag"]:
            node = self._stack.pop()
            text = _clean_text(" ".join(node["text"]))
            links = list(node["links"])
            if text or links:
                self.blocks.append({"text": text, "links": links})
            if self._stack:
                self._stack[-1]["text"].append(text)
                self._stack[-1]["links"].extend(links)

    def handle_data(self, data: str) -> None:
        self._all_text.append(data)
        if self._stack:
            self._stack[-1]["text"].append(data)
        if self._active_href:
            self._active_link_text.append(data)

    def normalized_fallback_block(self) -> dict[str, Any]:
        return {"text": _clean_text(" ".join(self._all_text)), "links": self._all_links}


def fetch_municipal_candidates(
    config: MunicipalSourceConfig,
    *,
    previous_state: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    detected_at = datetime.now().astimezone()
    pages: list[dict[str, Any]] = []
    page_errors: list[dict[str, str]] = []
    for url in config.urls:
        try:
            response = _get_with_deadline(url, config)
        except RuntimeError as error:
            page_errors.append({"url": url, "error": str(error)})
            continue
        blocks = _parse_blocks(response.text)
        normalized_text = _normalized_listing_text(blocks)
        pages.append(
            {
                "url": url,
                "status_code": response.status_code,
                "hash": _hash(normalized_text),
                "normalized_text": normalized_text,
                "blocks": blocks,
            }
        )
    if not pages:
        raise RuntimeError(f"No fue posible consultar paginas oficiales para {config.source_name}.")

    combined_text = "\n\n".join(page["normalized_text"] for page in pages)
    listing_hash = _hash(combined_text)
    previous_hash = str((previous_state or {}).get("listing_hash") or "")
    source_change_detected = not previous_hash or previous_hash != listing_hash

    opportunities_by_id: dict[str, dict[str, Any]] = {}
    for page in pages:
        for item in _extract_items(config, page["blocks"], page["url"], detected_at):
            item["source_change_detected"] = source_change_detected
            item["listing_hash"] = listing_hash
            existing = opportunities_by_id.get(item["source_id"])
            if existing is None:
                opportunities_by_id[item["source_id"]] = item
                continue
            _merge_item_links(existing, item)

    opportunities = [sanitize_opportunity(item) for item in opportunities_by_id.values()]
    opportunities.sort(key=lambda item: (item.get("published_date") or "", item.get("title") or ""), reverse=True)
    status_counts = {status: 0 for status in sorted(ALLOWED_STATUS)}
    for item in opportunities:
        status_counts[item["status"]] += 1

    state = {
        "source_id": config.source_id,
        "source": config.source_name,
        "listing_urls": list(config.urls),
        "listing_hash": listing_hash,
        "page_hashes": [{"url": page["url"], "hash": page["hash"]} for page in pages],
        "last_checked_at": detected_at.isoformat(timespec="seconds"),
        "last_publication_ids": [item["source_id"] for item in opportunities],
    }
    diagnostics = {
        "source_id": config.source_id,
        "source": config.source_name,
        "listing_urls": list(config.urls),
        "pages_checked": [{"url": page["url"], "status_code": page["status_code"], "hash": page["hash"]} for page in pages],
        "page_errors": page_errors,
        "listing_hash": listing_hash,
        "previous_listing_hash": previous_hash or None,
        "source_change_detected": source_change_detected,
        "publications_detected": len(opportunities),
        "documents_detected": sum(len(item["document_urls"]) for item in opportunities),
        "base_links_detected": sum(1 for item in opportunities if item.get("base_links")),
        "application_links_detected": sum(1 for item in opportunities if item.get("application_links")),
        "status_counts": status_counts,
        "open_confirmed": status_counts["open_confirmed"],
        "closed_or_finished": status_counts["closed"],
        "manual_review": status_counts["manual_review"],
        "local_priority": True,
        "implementation_status": "dry_run",
        "publishability": "manual_review_only",
        "telegram_notice": None,
        "notes": "Dry-run municipal local prioritario: detecta cambios por hash normalizado; no descarga documentos ni publica automaticamente.",
    }
    return opportunities, diagnostics, state


def _extract_items(
    config: MunicipalSourceConfig,
    blocks: list[dict[str, Any]],
    listing_url: str,
    detected_at: datetime,
) -> list[dict[str, Any]]:
    items = []
    seen = set()
    for block in blocks:
        text = _clean_text(str(block.get("text") or ""))
        links = block.get("links") or []
        if not text and not links:
            continue
        block_text = _clean_text(" ".join([text] + [str(link.get("name") or "") for link in links]))
        if not _looks_like_labor_contest(block_text, config.non_labor_markers):
            continue
        source_url = _best_source_url(links, listing_url, config)
        source_id = _stable_source_id(source_url, block_text)
        if source_id in seen:
            continue
        seen.add(source_id)
        documents = _document_urls(links, listing_url, config)
        base_links = [document for document in documents if _has_marker(document, BASE_LINK_MARKERS)]
        application_links = [document for document in _official_links(links, listing_url, config) if _has_marker(document, APPLICATION_LINK_MARKERS)]
        published_date = _extract_first_date(block_text)
        closing_date = _extract_labeled_date(block_text)
        status, status_reason, confidence = _classify(block_text, closing_date, detected_at.date())
        manual_review = status != "open_confirmed"
        manual_reason = status_reason if manual_review else None
        if has_sensitive_personal_data(block_text):
            status = "manual_review"
            status_reason = "La publicacion contiene posible dato personal o resultado; requiere revision manual."
            confidence = "low"
            manual_review = True
            manual_reason = status_reason
        item = {
            "id": f"{config.source_id}-{source_id}",
            "source_id": source_id,
            "title": _title_from_block(block_text),
            "institution": config.institution,
            "source": config.source_name,
            "source_url": source_url,
            "listing_url": listing_url,
            "region": "Maule",
            "commune": config.commune,
            "closing_date": closing_date,
            "published_date": published_date,
            "visible_date": published_date,
            "detected_at": detected_at.isoformat(timespec="seconds"),
            "detail_checked_at": None,
            "detail_url_status": "listing_only",
            "status": status,
            "status_reason": status_reason,
            "confidence": confidence,
            "description": block_text[:1000],
            "tags": ["municipalidad", _fold_text(config.commune).replace(" ", "_"), "concurso", "local_priority", "dry_run", "revisar_bases"],
            "categories": ["municipal", "local_priority"],
            "document_urls": documents,
            "documents": documents,
            "base_links": base_links,
            "application_links": application_links,
            "evidence": _evidence(published_date, closing_date, documents, base_links, application_links, status_reason),
            "is_demo": False,
            "url_status": "ok",
            "implementation_status": "dry_run",
            "offer_scope": "municipal",
            "local_priority": True,
            "manual_review": manual_review,
            "manual_review_reason": manual_reason,
            "review_label": "Revisar bases",
            "item_hash": _hash(block_text),
        }
        items.append(item)
    return items


def _merge_item_links(existing: dict[str, Any], item: dict[str, Any]) -> None:
    for field in ("document_urls", "documents", "base_links", "application_links", "evidence"):
        merged = list(existing.get(field) or [])
        for value in item.get(field) or []:
            if value not in merged:
                merged.append(value)
        existing[field] = merged


def _get(url: str, config: MunicipalSourceConfig) -> _FetchedPage:
    if not _is_allowed_url(url, config.allowed_hosts):
        raise RuntimeError(f"URL fuera del dominio oficial {config.commune}: {url}")
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


def _get_with_deadline(url: str, config: MunicipalSourceConfig) -> _FetchedPage:
    results: queue.Queue[tuple[str, _FetchedPage | Exception]] = queue.Queue(maxsize=1)

    def worker() -> None:
        try:
            results.put(("ok", _get(url, config)))
        except Exception as error:  # noqa: BLE001 - source errors are reported as diagnostics.
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


def _parse_blocks(html: str) -> list[dict[str, Any]]:
    parser = _BlockHTMLParser()
    parser.feed(html)
    blocks = parser.blocks
    if not blocks:
        blocks = [parser.normalized_fallback_block()]
    return blocks


def _normalized_listing_text(blocks: list[dict[str, Any]]) -> str:
    lines = []
    for block in blocks:
        text = _clean_text(str(block.get("text") or ""))
        links = " ".join(str(link.get("url") or "") for link in block.get("links") or [])
        if text or links:
            lines.append(f"{text} {links}".strip())
    return _fold_text("\n".join(lines))


def _looks_like_labor_contest(text: str, non_labor_markers: tuple[str, ...]) -> bool:
    folded = _fold_text(text)
    if not any(marker in folded for marker in CONTEST_MARKERS):
        return False
    return not any(marker in folded for marker in non_labor_markers)


def _official_links(links: list[dict[str, str]], listing_url: str, config: MunicipalSourceConfig) -> list[dict[str, str]]:
    documents = []
    seen = set()
    for link in links:
        raw_url = str(link.get("url") or "").strip()
        if not raw_url:
            continue
        url = urljoin(listing_url, raw_url)
        if not (_is_allowed_url(url, config.allowed_hosts) or _is_empleos_publicos_url(url)):
            continue
        if url in seen:
            continue
        seen.add(url)
        documents.append({"name": _clean_text(str(link.get("name") or "")) or url.rsplit("/", 1)[-1], "url": url})
    return documents


def _document_urls(links: list[dict[str, str]], listing_url: str, config: MunicipalSourceConfig) -> list[dict[str, str]]:
    return [link for link in _official_links(links, listing_url, config) if urlparse(link["url"]).path.lower().endswith(DOCUMENT_EXTENSIONS)]


def _best_source_url(links: list[dict[str, str]], listing_url: str, config: MunicipalSourceConfig) -> str:
    official = _official_links(links, listing_url, config)
    return official[0]["url"] if official else listing_url


def _classify(text: str, closing_date: str | None, today: date) -> tuple[str, str, str]:
    folded = _fold_text(text)
    if any(marker in folded for marker in CLOSED_MARKERS):
        return "closed", "La publicacion contiene evidencia de cierre, resultado, finalizado o desierto.", "high"
    if closing_date:
        parsed = date.fromisoformat(closing_date)
        if parsed >= today:
            return "open_confirmed", "La publicacion informa una fecha de cierre vigente.", "high"
        return "closed", "La publicacion informa una fecha de cierre ya vencida.", "high"
    return "manual_review", "Publicacion con senales de concurso, pero sin fecha de cierre confiable; revisar bases.", "low"


def _extract_labeled_date(text: str) -> str | None:
    folded = _fold_text(text)
    for label in CLOSING_LABELS:
        match = re.search(rf"{re.escape(label)}[^0-9]{{0,80}}{NUMERIC_DATE_PATTERN.pattern}", folded)
        if match:
            return _iso_date(match.group(1), match.group(2), match.group(3))
    return None


def _extract_first_date(text: str) -> str | None:
    match = VISIBLE_DATE_PATTERN.search(text)
    if match:
        month = MONTHS.get(_fold_text(match.group(2)))
        if month:
            return _iso_date(match.group(1), str(month), match.group(3))
    match = NUMERIC_DATE_PATTERN.search(text)
    if match:
        return _iso_date(match.group(1), match.group(2), match.group(3))
    return None


def _iso_date(day: str, month: str, year: str) -> str | None:
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def _title_from_block(text: str) -> str:
    parts = re.split(r"\s{2,}|\s+-\s+|\s+\|\s+", text)
    candidate = parts[0] if parts else text
    if len(candidate) > 180:
        candidate = candidate[:177].rstrip() + "..."
    return candidate or "Concurso publico municipal"


def _evidence(
    published_date: str | None,
    closing_date: str | None,
    documents: list[dict[str, str]],
    base_links: list[dict[str, str]],
    application_links: list[dict[str, str]],
    status_reason: str,
) -> list[str]:
    evidence = [status_reason]
    if published_date:
        evidence.append(f"Fecha visible detectada: {published_date}")
    if closing_date:
        evidence.append(f"Fecha de cierre explicita: {closing_date}")
    if documents:
        evidence.append(f"Documentos oficiales enlazados sin descarga: {len(documents)}")
    if base_links:
        evidence.append(f"Enlaces a bases/fichas detectados: {len(base_links)}")
    if application_links:
        evidence.append(f"Enlaces de postulacion detectados: {len(application_links)}")
    return evidence


def _has_marker(document: dict[str, str], markers: tuple[str, ...]) -> bool:
    folded = _fold_text(f"{document.get('name') or ''} {document.get('url') or ''}")
    return any(marker in folded for marker in markers)


def _stable_source_id(source_url: str, text: str) -> str:
    return _hash(f"{source_url}\n{_fold_text(text)}")[:16]


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_allowed_url(url: str, allowed_hosts: tuple[str, ...]) -> bool:
    try:
        hostname = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return any(hostname == host or hostname.endswith(f".{host}") for host in allowed_hosts)


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
    return normalized.encode("ascii", "ignore").decode("ascii")
