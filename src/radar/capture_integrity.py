"""Integrity gate for promoting Empleos Publicos captures."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from radar.contracts import missing_opportunity_fields
from radar.sources.empleos_publicos import REGIONS_BY_QUERY_ID


DEFAULT_MAX_VOLUME_DROP_RATIO = 0.35
DEFAULT_MIN_NORMALIZED_COUNT = 1
ENV_MAX_VOLUME_DROP_RATIO = "RADAR_CAPTURE_MAX_DROP_RATIO"
ENV_MIN_NORMALIZED_COUNT = "RADAR_CAPTURE_MIN_NORMALIZED"


@dataclass(frozen=True)
class CaptureIntegrityPolicy:
    """Conservative rules for accepting a new principal capture."""

    max_volume_drop_ratio: float = DEFAULT_MAX_VOLUME_DROP_RATIO
    min_normalized_count: int = DEFAULT_MIN_NORMALIZED_COUNT
    zero_results_are_anomalous: bool = True

    @classmethod
    def from_env(cls) -> "CaptureIntegrityPolicy":
        return cls(
            max_volume_drop_ratio=_env_float(
                ENV_MAX_VOLUME_DROP_RATIO,
                DEFAULT_MAX_VOLUME_DROP_RATIO,
            ),
            min_normalized_count=_env_int(
                ENV_MIN_NORMALIZED_COUNT,
                DEFAULT_MIN_NORMALIZED_COUNT,
            ),
        )


def expected_region_for_url(url: str) -> str | None:
    query_id = parse_qs(urlparse(url).query).get("i", [None])[0]
    return REGIONS_BY_QUERY_ID.get(query_id)


def load_previous_normalized(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def validate_capture_integrity(
    *,
    required_urls: list[str],
    diagnostics: list[dict[str, Any]],
    normalized: list[dict[str, Any]],
    previous_normalized: list[dict[str, Any]] | None,
    policy: CaptureIntegrityPolicy,
) -> list[str]:
    """Return blocking errors for an incomplete or anomalous capture."""
    errors: list[str] = []
    if not required_urls:
        errors.append("No hay URLs obligatorias configuradas para Empleos Publicos.")
    errors.extend(_diagnostic_errors(required_urls, diagnostics, policy))
    errors.extend(_normalized_errors(required_urls, normalized, policy))
    errors.extend(_volume_errors(normalized, previous_normalized or [], policy))
    return errors


def _diagnostic_errors(
    required_urls: list[str],
    diagnostics: list[dict[str, Any]],
    policy: CaptureIntegrityPolicy,
) -> list[str]:
    errors: list[str] = []
    required_set = set(required_urls)
    seen: set[str] = set()
    by_url: dict[str, dict[str, Any]] = {}

    for index, diagnostic in enumerate(diagnostics):
        if not isinstance(diagnostic, dict):
            errors.append(f"diagnostics[{index}] debe ser objeto JSON.")
            continue
        url = diagnostic.get("url")
        if not isinstance(url, str) or not url:
            errors.append(f"diagnostics[{index}] no tiene URL valida.")
            continue
        if url in seen:
            errors.append(f"diagnostico duplicado para URL obligatoria: {url}")
        seen.add(url)
        by_url[url] = diagnostic
        if url not in required_set:
            errors.append(f"diagnostico contiene URL no obligatoria: {url}")

    for url in required_urls:
        diagnostic = by_url.get(url)
        expected_region = expected_region_for_url(url)
        if diagnostic is None:
            errors.append(f"falta diagnostico para URL obligatoria: {url}")
            continue
        if not expected_region:
            errors.append(f"URL obligatoria sin region esperada: {url}")
        if diagnostic.get("region") != expected_region:
            errors.append(
                f"{url}: region diagnostica invalida "
                f"({diagnostic.get('region')!r}, esperado {expected_region!r})."
            )
        if diagnostic.get("error"):
            errors.append(f"{url}: captura con error: {diagnostic.get('error')}")
        detected = diagnostic.get("detected")
        added_unique = diagnostic.get("added_unique")
        if not isinstance(detected, int) or isinstance(detected, bool) or detected < 0:
            errors.append(f"{url}: detected invalido.")
        elif policy.zero_results_are_anomalous and detected == 0:
            errors.append(f"{url}: detected=0 se considera captura anomala.")
        if not isinstance(added_unique, int) or isinstance(added_unique, bool) or added_unique < 0:
            errors.append(f"{url}: added_unique invalido.")

    return errors


def _normalized_errors(
    required_urls: list[str],
    normalized: list[dict[str, Any]],
    policy: CaptureIntegrityPolicy,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(normalized, list):
        return ["La captura normalizada debe ser una lista."]
    if len(normalized) < policy.min_normalized_count:
        errors.append(
            f"captura normalizada insuficiente: {len(normalized)} "
            f"< {policy.min_normalized_count}."
        )

    required_regions = {
        region for region in (expected_region_for_url(url) for url in required_urls) if region
    }
    required_url_set = set(required_urls)
    seen_regions = set()
    for index, item in enumerate(normalized):
        if not isinstance(item, dict):
            errors.append(f"normalized[{index}] debe ser objeto JSON.")
            continue
        missing = missing_opportunity_fields(item)
        if missing:
            errors.append(f"normalized[{index}] faltan campos: {', '.join(missing)}")
        region = item.get("region")
        if region in required_regions:
            seen_regions.add(region)
        listing_url = item.get("listing_url")
        if listing_url is not None and listing_url not in required_url_set:
            errors.append(f"normalized[{index}] tiene listing_url no obligatoria.")

    for region in sorted(required_regions - seen_regions):
        errors.append(f"captura normalizada sin oportunidades para region obligatoria: {region}")

    return errors


def _volume_errors(
    normalized: list[dict[str, Any]],
    previous_normalized: list[dict[str, Any]],
    policy: CaptureIntegrityPolicy,
) -> list[str]:
    previous_count = len(previous_normalized)
    current_count = len(normalized)
    if previous_count <= 0:
        return []
    allowed_minimum = previous_count * (1 - policy.max_volume_drop_ratio)
    if current_count < allowed_minimum:
        drop_ratio = 1 - (current_count / previous_count)
        return [
            "caida abrupta de volumen: "
            f"{current_count} actual vs {previous_count} anterior "
            f"({drop_ratio:.1%} > {policy.max_volume_drop_ratio:.1%})."
        ]
    return []


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError(f"{name} debe ser numerico.") from error
    if not 0 <= value < 1:
        raise ValueError(f"{name} debe estar entre 0 y 1.")
    return value


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{name} debe ser entero.") from error
    if value < 1:
        raise ValueError(f"{name} debe ser mayor o igual a 1.")
    return value
