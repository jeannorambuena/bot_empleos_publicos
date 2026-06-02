"""Conservative dry-run adapter for Municipalidad de Talca."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


SOURCE_ID = "municipalidad-talca"
SOURCE_NAME = "Municipalidad de Talca"
INSTITUTION = "Ilustre Municipalidad de Talca"
TIMEOUT_SECONDS = 20
USER_AGENT = "RadarLaboralPublicoChile/0.2 (dry-run source audit)"


def fetch_candidates(discovery_url: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Inspect the official landing page without turning generic links into jobs."""
    response = requests.get(discovery_url, timeout=TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    relevant_links: list[str] = []
    excluded_links: list[str] = []
    for link in soup.select("a[href]"):
        url = urljoin(response.url, str(link.get("href") or "").strip())
        text = _clean_text(link.get_text(" ", strip=True))
        folded = f"{text} {url}".lower()
        if not re.search(r"concurso|convocatoria|empleo|laboral|omil|daem|selecci", folded):
            continue
        if not _official_url(url):
            excluded_links.append(url)
            continue
        if re.search(r"omil|daem|literario|cultura|noticia", folded):
            excluded_links.append(url)
            continue
        relevant_links.append(url)
    diagnostics = _diagnostics(
        discovery_url=response.url,
        http_status=response.status_code,
        source_links_detected=len(set(relevant_links)),
        excluded_links=len(set(excluded_links)),
        notes=(
            "La portada oficial no expone convocatorias laborales municipales trazables. "
            "Se excluyen enlaces DAEM, OMIL, privados y noticias generales."
        ),
    )
    return [], diagnostics


def _diagnostics(**values: Any) -> dict[str, Any]:
    return {
        "source_id": SOURCE_ID,
        "source": SOURCE_NAME,
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "access_status": "ok",
        "publications_detected": 0,
        "status_counts": {"open_confirmed": 0, "closed": 0, "manual_review": 0},
        "external_private": 0,
        "documents_detected": 0,
        "reliable_closing_dates": 0,
        "privacy_risk": "medium",
        "recommendation": "keep_monitoring",
        **values,
    }


def _official_url(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return hostname == "talca.cl" or hostname.endswith(".talca.cl")


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
