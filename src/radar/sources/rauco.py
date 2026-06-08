"""Dry-run monitor for Municipalidad de Rauco contest publications."""

from __future__ import annotations

from typing import Any

from radar.sources.local_municipal_watch import MunicipalSourceConfig, fetch_municipal_candidates


SOURCE_NAME = "Municipalidad de Rauco"
INSTITUTION = "Ilustre Municipalidad de Rauco"
SOURCE_ID = "municipalidad-rauco"
DEFAULT_DISCOVERY_URLS = ("https://munirauco.cl/pages/concurso",)
CONFIG = MunicipalSourceConfig(
    key="rauco",
    source_id=SOURCE_ID,
    source_name=SOURCE_NAME,
    institution=INSTITUTION,
    commune="Rauco",
    urls=DEFAULT_DISCOVERY_URLS,
    allowed_hosts=("munirauco.cl",),
)


def fetch_rauco_candidates(
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
