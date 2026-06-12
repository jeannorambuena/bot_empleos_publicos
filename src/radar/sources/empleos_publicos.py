"""Local connector for the public Empleos Publicos listing pages."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Iterable
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag


DEFAULT_TIMEOUT_SECONDS = 20
USER_AGENT = "RadarLaboralPublicoChile/0.1 (+proyecto comunitario local)"
SOURCE_NAME = "Empleos Públicos"

REGIONS_BY_QUERY_ID = {
    "15": "Metropolitana",
    "7": "O’Higgins",
    "8": "Maule",
}
POSTULATION_DATES = re.compile(
    r"Plazos?\s+de\s+Postulaci[oó]n\s+(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE,
)


@dataclass
class SourceDiagnostic:
    source: str
    url: str
    region: str
    detected: int = 0
    added_unique: int = 0
    error: str | None = None


def fetch_empleos_publicos(
    urls: Iterable[str],
    *,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    session: requests.Session | None = None,
    detected_at: datetime | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Fetch regional listing pages and return semi-normalized opportunities.

    Network errors are recorded per URL. The caller decides whether a partial
    capture can be promoted.
    """
    http = session or requests.Session()
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    capture_time = detected_at or datetime.now().astimezone()
    opportunities = []
    diagnostics = []
    seen = set()

    for url in urls:
        region = _region_from_url(url)
        diagnostic = SourceDiagnostic(source=SOURCE_NAME, url=url, region=region)
        try:
            response = http.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            parsed = parse_listing_html(
                response.text,
                listing_url=url,
                region=region,
                detected_at=capture_time,
            )
            diagnostic.detected = len(parsed)
            for opportunity in parsed:
                dedupe_key = opportunity.get("id") or opportunity.get("source_url")
                if not dedupe_key or dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                opportunities.append(opportunity)
                diagnostic.added_unique += 1
        except requests.RequestException as error:
            diagnostic.error = f"{type(error).__name__}: {error}"
        except Exception as error:  # Preserve diagnostics if a source changes HTML.
            diagnostic.error = f"ParsingError: {type(error).__name__}: {error}"
        diagnostics.append(asdict(diagnostic))

    return opportunities, diagnostics


def parse_listing_html(
    html: str,
    *,
    listing_url: str,
    region: str,
    detected_at: datetime,
) -> list[dict[str, Any]]:
    """Extract job cards from one listing page without inventing unavailable data."""
    soup = BeautifulSoup(html, "html.parser")
    opportunities = []

    for link in soup.find_all("a", href=True):
        if "ver bases" not in link.get_text(" ", strip=True).lower():
            continue
        card = link.find_parent("div", class_="caja")
        if card is None:
            card = link.parent.parent.parent if link.parent and link.parent.parent else None
        if not isinstance(card, Tag):
            continue

        source_url = urljoin(listing_url, link["href"])
        opportunity_id = _id_from_url(source_url)
        if not opportunity_id:
            continue

        title_node = card.select_one("#bx_titulos")
        summary_node = card.select_one("#bx_resumen")
        institution_node = summary_node.find("strong") if summary_node else None
        deadline_node = summary_node.find("em") if summary_node else None

        title = _clean_text(title_node) or None
        institution = _clean_text(institution_node) or None
        deadline_text = _clean_text(deadline_node)
        description = _description_without_metadata(summary_node)
        closing_date = _closing_date(deadline_text)

        opportunities.append(
            {
                "id": f"empleos-publicos-{opportunity_id}",
                "source_id": opportunity_id,
                "title": title,
                "institution": institution,
                "source": SOURCE_NAME,
                "source_url": source_url,
                "region": region,
                "commune": None,
                "closing_date": closing_date,
                "detected_at": detected_at.isoformat(timespec="seconds"),
                "description": description,
                "listing_url": listing_url,
            }
        )

    return opportunities


def _description_without_metadata(summary_node: Tag | None) -> str | None:
    if summary_node is None:
        return None
    clone = BeautifulSoup(str(summary_node), "html.parser")
    for node in clone.find_all(["strong", "em"]):
        node.decompose()
    text = _clean_text(clone)
    return text or None


def _id_from_url(url: str) -> str | None:
    values = parse_qs(urlparse(url).query).get("i")
    return values[0] if values else None


def _region_from_url(url: str) -> str:
    query_id = parse_qs(urlparse(url).query).get("i", [None])[0]
    return REGIONS_BY_QUERY_ID.get(query_id, "No especificada")


def _closing_date(value: str) -> str | None:
    match = POSTULATION_DATES.search(value)
    if not match:
        return None
    return datetime.strptime(match.group(2), "%d/%m/%Y").date().isoformat()


def _clean_text(node: Any) -> str:
    if node is None:
        return ""
    text = node.get_text(" ", strip=True) if hasattr(node, "get_text") else str(node)
    return re.sub(r"\s+", " ", text).strip()
