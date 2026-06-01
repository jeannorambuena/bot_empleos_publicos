"""Build the JSON files consumed by the static public dashboard."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from .scoring import calculate_match


DEFAULT_TIMEZONE = "America/Santiago"
DEFAULT_INSTITUTION_TYPE = "Institución pública"
DEMO_URL_STATUS = "demo"
AVAILABLE_URL_STATUS = "available"


def normalize_opportunity(
    opportunity: dict[str, Any],
    profile: dict[str, Any],
    *,
    detected_at: datetime,
    force_demo: bool = False,
) -> dict[str, Any]:
    """Complete safe defaults and apply scoring to one opportunity."""
    normalized = deepcopy(opportunity)
    score = calculate_match(normalized, profile)
    is_demo = force_demo or bool(normalized.get("is_demo", False))

    normalized.setdefault("id", "")
    normalized.setdefault("title", "Oportunidad sin título")
    normalized.setdefault("institution", "Institución no especificada")
    normalized.setdefault("source", "Fuente no especificada")
    normalized.setdefault("region", "No especificada")
    normalized.setdefault("commune", "No especificada")
    normalized.setdefault("closing_date", None)
    normalized.setdefault("detected_at", detected_at.isoformat(timespec="seconds"))
    normalized.setdefault("status", "vigente")
    normalized.setdefault("tags", [])
    normalized.setdefault("description", "")
    normalized.setdefault("area", "No especificada")
    normalized.setdefault("institution_type", DEFAULT_INSTITUTION_TYPE)
    normalized["match_score"] = score["match_score"]
    normalized["match_level"] = score["match_level"]
    normalized["alert_reasons"] = score["alert_reasons"]
    normalized["is_demo"] = is_demo

    if is_demo:
        normalized["source_url"] = None
        normalized["url_status"] = DEMO_URL_STATUS
    else:
        normalized.setdefault("source_url", None)
        normalized.setdefault(
            "url_status",
            AVAILABLE_URL_STATUS if normalized["source_url"] else "missing",
        )

    normalized["urgency"] = _urgency_for_closing_date(
        normalized.get("closing_date"),
        detected_at.date(),
    )
    return normalized


def build_public_payloads(
    opportunities: Iterable[dict[str, Any]],
    profile: dict[str, Any],
    *,
    generated_at: datetime,
    force_demo: bool = False,
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, str]]:
    """Score opportunities, sort them and create all dashboard payloads."""
    normalized = [
        normalize_opportunity(
            opportunity,
            profile,
            detected_at=generated_at,
            force_demo=force_demo,
        )
        for opportunity in opportunities
    ]
    normalized.sort(key=_opportunity_sort_key)

    summary = summarize_opportunities(normalized, generated_at=generated_at)
    last_run = {
        "finished_at": generated_at.isoformat(timespec="seconds"),
        "status": "prototype" if force_demo else "ok",
        "message": (
            "Carga demostrativa generada correctamente"
            if force_demo
            else "Datos públicos generados correctamente"
        ),
    }
    return normalized, summary, last_run


def summarize_opportunities(
    opportunities: Iterable[dict[str, Any]],
    *,
    generated_at: datetime,
) -> dict[str, int]:
    """Create the metrics currently consumed by the dashboard."""
    items = list(opportunities)
    active = [item for item in items if item.get("status") in {"vigente", "abierta"}]
    sources = {item.get("source") for item in items if item.get("source")}
    return {
        "sources_reviewed": len(sources),
        "active_opportunities": len(active),
        "new_opportunities": sum(_is_new(item, generated_at) for item in active),
        "high_match": sum(item.get("match_level") == "Alta" for item in active),
        "closing_soon": sum(
            _is_closing_soon(item.get("closing_date"), generated_at.date())
            for item in active
        ),
    }


def write_public_data(
    output_directory: str | Path,
    opportunities: list[dict[str, Any]],
    summary: dict[str, int],
    last_run: dict[str, str],
) -> None:
    """Write dashboard JSON files using UTF-8 and stable formatting."""
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    _write_json(directory / "opportunities.json", opportunities)
    _write_json(directory / "summary.json", summary)
    _write_json(directory / "last_run.json", last_run)


def _write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _urgency_for_closing_date(value: object, today: date) -> str:
    return "proximo" if _is_closing_soon(value, today) else "normal"


def _is_closing_soon(value: object, today: date) -> bool:
    closing_date = _parse_date(value)
    return bool(closing_date and today <= closing_date <= today + timedelta(days=7))


def _is_new(opportunity: dict[str, Any], generated_at: datetime) -> bool:
    detected_at = _parse_datetime(opportunity.get("detected_at"))
    if detected_at is None:
        return False
    if detected_at.tzinfo is None and generated_at.tzinfo is not None:
        detected_at = detected_at.replace(tzinfo=generated_at.tzinfo)
    return generated_at - timedelta(days=1) <= detected_at <= generated_at


def _opportunity_sort_key(opportunity: dict[str, Any]) -> tuple[Any, ...]:
    closing_date = _parse_date(opportunity.get("closing_date"))
    detected_at = _parse_datetime(opportunity.get("detected_at"))
    return (
        -int(opportunity.get("match_score", 0)),
        closing_date is None,
        closing_date or date.max,
        detected_at is None,
        -(detected_at.timestamp()) if detected_at else 0,
    )
