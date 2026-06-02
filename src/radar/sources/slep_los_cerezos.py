"""Safe diagnostic dry-run adapter for SLEP Los Cerezos."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from radar.sources.sanitization import sanitize_opportunity


SOURCE_ID = "slep-los-cerezos"
SOURCE_NAME = "SLEP Los Cerezos"
INSTITUTION = "Servicio Local de Educación Pública Los Cerezos"
TIMEOUT_SECONDS = 20
USER_AGENT = "RadarLaboralPublicoChile/0.2 (dry-run source audit)"
REFERENCE_PATTERN = re.compile(r"/concursos-internos-2/.*/slep-los-cerezos/?$", re.I)
DOCUMENT_EXTENSIONS = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".zip")


def fetch_candidates(discovery_url: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Detect official DEP references but keep them in manual review."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    landing = _get(session, discovery_url)
    soup = BeautifulSoup(landing.text, "html.parser")
    references = []
    for link in soup.select("a[href]"):
        url = urljoin(landing.url, str(link.get("href") or "").strip())
        if _institutional_url(url) and REFERENCE_PATTERN.search(urlparse(url).path):
            references.append(url)
    opportunities = []
    total_documents = 0
    for reference_url in sorted(set(references)):
        detail = _get(session, reference_url)
        documents = _documents(detail.text, detail.url)
        total_documents += len(documents)
        reason = (
            "Referencia oficial DEP a concurso interno SLEP sin fecha de cierre confiable en la ficha; "
            "requiere revisión humana y no se publica automáticamente."
        )
        opportunities.append(
            sanitize_opportunity(
                {
                    "id": f"slep-los-cerezos-{hashlib.sha256(detail.url.encode()).hexdigest()[:16]}",
                    "title": "Concurso interno SLEP Los Cerezos",
                    "institution": INSTITUTION,
                    "source": SOURCE_NAME,
                    "source_url": detail.url,
                    "listing_url": landing.url,
                    "region": "Maule",
                    "commune": "regional_or_multiple",
                    "status": "manual_review",
                    "status_reason": reason,
                    "closing_date": None,
                    "published_date": None,
                    "offer_scope": "slep",
                    "implementation_status": "dry_run",
                    "manual_review": True,
                    "manual_review_reason": reason,
                    "confidence": "medium",
                    "description": "Referencia institucional externa detectada desde la sede oficial SLEP.",
                    "document_urls": documents,
                    "evidence": [
                        "Enlace detectado desde la portada oficial SLEP Los Cerezos.",
                        f"Ficha oficial DEP: {detail.url}",
                        f"Documentos institucionales enlazados sin descarga: {len(documents)}",
                    ],
                }
            )
        )
    diagnostics = {
        "source_id": SOURCE_ID,
        "source": SOURCE_NAME,
        "listing_url": landing.url,
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "access_status": "ok",
        "http_status": landing.status_code,
        "publications_detected": len(opportunities),
        "source_links_detected": len(set(references)),
        "status_counts": {"open_confirmed": 0, "closed": 0, "manual_review": len(opportunities)},
        "external_private": 0,
        "documents_detected": total_documents,
        "reliable_closing_dates": 0,
        "privacy_risk": "medium",
        "recommendation": "manual_review_only",
        "notes": "Diagnóstico seguro: referencia DEP conservada como manual_review; no publicar ni alertar automáticamente.",
    }
    return opportunities, diagnostics


def _get(session: requests.Session, url: str) -> requests.Response:
    if not _institutional_url(url):
        raise RuntimeError(f"URL fuera de sedes institucionales permitidas: {url}")
    try:
        response = session.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response
    except requests.RequestException as error:
        raise RuntimeError(f"No fue posible consultar {url}: {error}") from error


def _documents(html: str, base_url: str) -> list[dict[str, str]]:
    documents = []
    seen = set()
    soup = BeautifulSoup(html, "html.parser")
    for link in soup.select("a[href]"):
        url = urljoin(base_url, str(link.get("href") or "").strip())
        name = re.sub(r"\s+", " ", link.get_text(" ", strip=True)).strip() or url.rsplit("/", 1)[-1]
        document_hint = f"{name} {url}".lower()
        if (
            url in seen
            or not _institutional_url(url)
            or not urlparse(url).path.lower().endswith(DOCUMENT_EXTENSIONS)
            or not re.search(r"anexo|base|postul|concurso", document_hint)
        ):
            continue
        seen.add(url)
        documents.append({"name": name, "url": url})
    return documents


def _institutional_url(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return (
        hostname == "sleploscerezos.gob.cl"
        or hostname.endswith(".sleploscerezos.gob.cl")
        or hostname in {"educacionpublica.gob.cl", "www.educacionpublica.gob.cl", "dep.gob.cl", "www.dep.gob.cl"}
    )
