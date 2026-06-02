"""Isolated dry-run adapter for Municipalidad de Curico contest publications."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any

import requests
from bs4 import BeautifulSoup


USER_AGENT = "RadarLaboralPublicoChile/0.1 (+https://github.com/jeannorambuena/bot_empleos_publicos; dry-run source audit)"
TIMEOUT_SECONDS = 20
SOURCE_NAME = "Municipalidad de Curicó"
INSTITUTION = "Ilustre Municipalidad de Curicó"
SOURCE_ID = "municipalidad-curico"
RESULT_MARKERS = ("seleccionado", "seleccionados", "nomina seleccionados", "nómina seleccionados")


def fetch_curico_candidates(discovery_url: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Fetch one configured listing page and return manual-review candidates."""
    try:
        response = requests.get(
            discovery_url,
            timeout=TIMEOUT_SECONDS,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(f"No fue posible consultar {discovery_url}: {error}") from error

    soup = BeautifulSoup(response.text, "html.parser")
    detected_at = datetime.now().astimezone().isoformat(timespec="seconds")
    candidates: list[dict[str, Any]] = []
    skipped_results: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for article in soup.select("article.category-concursos"):
        link = article.select_one("h4.post-title a[href]")
        if link is None:
            continue
        source_url = str(link.get("href") or "").strip()
        title = _clean_text(link.get_text(" ", strip=True))
        description = _clean_text(article.get_text(" ", strip=True))
        if not source_url or not title or source_url in seen_urls:
            continue
        seen_urls.add(source_url)
        if _is_result_publication(title, description):
            skipped_results.append({"title": title, "source_url": source_url})
            continue

        source_id = _source_id(article, source_url)
        candidates.append(
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
                "closing_date": None,
                "detected_at": detected_at,
                "status": "manual_review",
                "description": description[:1000],
                "tags": ["municipalidad", "concurso", "manual_review"],
                "is_demo": False,
                "url_status": "ok",
                "implementation_status": "dry_run",
                "manual_review": True,
                "manual_review_reason": "La página de listado no publica una fecha de cierre ni vigencia inequívoca.",
            }
        )

    diagnostics = {
        "source_id": SOURCE_ID,
        "source": SOURCE_NAME,
        "listing_url": discovery_url,
        "http_status": response.status_code,
        "articles_reviewed": len(soup.select("article.category-concursos")),
        "candidates_detected": len(candidates),
        "selection_results_skipped": len(skipped_results),
        "skipped_results": skipped_results,
        "notes": "Dry-run aislado: no sigue paginación ni enlaces de detalle y no publica datos.",
    }
    return candidates, diagnostics


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


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))
