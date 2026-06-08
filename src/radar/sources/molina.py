"""Dry-run monitor for Municipalidad de Molina contest publications."""

from __future__ import annotations

from typing import Any

from radar.sources.local_municipal_watch import MunicipalSourceConfig, fetch_municipal_candidates


SOURCE_NAME = "Municipalidad de Molina"
INSTITUTION = "Ilustre Municipalidad de Molina"
SOURCE_ID = "municipalidad-molina"
DEFAULT_DISCOVERY_URLS = (
    "https://web2.molina.cl/concursos-publicos/",
    "https://web.molina.cl/?page_id=71592",
)
CONFIG = MunicipalSourceConfig(
    key="molina",
    source_id=SOURCE_ID,
    source_name=SOURCE_NAME,
    institution=INSTITUTION,
    commune="Molina",
    urls=DEFAULT_DISCOVERY_URLS,
    allowed_hosts=("molina.cl",),
)


def fetch_molina_candidates(
    discovery_urls: tuple[str, ...] | list[str] | None = None,
    *,
    previous_state: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    config = CONFIG
    if discovery_urls:
        config = MunicipalSourceConfig(
            key=CONFIG.key,
            source_id=CONFIG.source_id,
            source_name=CONFIG.source_name,
            institution=CONFIG.institution,
            commune=CONFIG.commune,
            urls=tuple(discovery_urls),
            allowed_hosts=CONFIG.allowed_hosts,
            non_labor_markers=CONFIG.non_labor_markers,
        )
    return fetch_municipal_candidates(config, previous_state=previous_state)
