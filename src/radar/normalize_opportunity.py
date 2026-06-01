"""Normalize captured source opportunities to the public contract."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from datetime import date, datetime, timedelta
from typing import Any, Iterable

from .scoring import calculate_match


def normalize_real_opportunity(
    opportunity: dict[str, Any],
    *,
    detected_at: datetime | None = None,
) -> dict[str, Any]:
    """Complete a real source capture without inventing unavailable information."""
    normalized = deepcopy(opportunity)
    capture_time = detected_at or datetime.now().astimezone()
    source_url = _optional_text(normalized.get("source_url"))

    normalized["id"] = _stable_id(normalized)
    normalized["title"] = _optional_text(normalized.get("title")) or "Título no disponible"
    normalized["institution"] = _optional_text(normalized.get("institution")) or "Institución no especificada"
    normalized["source"] = _optional_text(normalized.get("source")) or "Fuente no especificada"
    normalized["source_url"] = source_url
    normalized["region"] = _optional_text(normalized.get("region")) or "No especificada"
    normalized["commune"] = _optional_text(normalized.get("commune")) or "No especificada"
    normalized["closing_date"] = _optional_text(normalized.get("closing_date"))
    normalized["detected_at"] = _optional_text(normalized.get("detected_at")) or capture_time.isoformat(timespec="seconds")
    normalized["status"] = "abierta" if normalized.get("closing_date") else "desconocido"
    normalized["tags"] = list(normalized.get("tags") or [])
    normalized["alert_reasons"] = list(normalized.get("alert_reasons") or [])
    normalized["description"] = _optional_text(normalized.get("description")) or "Descripción no disponible"
    normalized["is_demo"] = False
    normalized["url_status"] = "ok" if source_url else "missing"
    normalized["area"] = _optional_text(normalized.get("area")) or "No especificada"
    normalized["institution_type"] = _optional_text(normalized.get("institution_type")) or "Institución pública"
    normalized["urgency"] = _urgency_for_closing_date(normalized.get("closing_date"), capture_time.date())
    normalized.setdefault("match_score", 0)
    normalized.setdefault("match_level", "Descartada")
    return normalized


def normalize_real_opportunities(
    opportunities: Iterable[dict[str, Any]],
    *,
    detected_at: datetime | None = None,
) -> list[dict[str, Any]]:
    """Normalize and deduplicate real opportunities by id or source URL."""
    normalized = []
    seen = set()
    for opportunity in opportunities:
        item = normalize_real_opportunity(opportunity, detected_at=detected_at)
        dedupe_key = item.get("source_url") or item["id"]
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        normalized.append(item)
    return normalized


def score_real_opportunity(opportunity: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Apply the configured scoring engine while preserving the real-data contract."""
    normalized = normalize_real_opportunity(opportunity)
    scoring = calculate_match(normalized, profile)
    normalized["match_score"] = scoring["match_score"]
    normalized["match_level"] = scoring["match_level"]
    normalized["alert_reasons"] = scoring["alert_reasons"]
    normalized["matched_keywords"] = scoring["matched_keywords"]
    normalized["excluded_keywords"] = scoring["excluded_keywords"]
    return normalized


def _stable_id(opportunity: dict[str, Any]) -> str:
    existing = _optional_text(opportunity.get("id"))
    if existing:
        return existing
    source_url = _optional_text(opportunity.get("source_url"))
    raw = source_url or "|".join(
        str(opportunity.get(key) or "")
        for key in ("source", "title", "institution", "closing_date")
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]
    return f"real-{digest}"


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _urgency_for_closing_date(value: Any, today: date) -> str:
    try:
        closing_date = date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        closing_date = None
    return "proximo" if closing_date and today <= closing_date <= today + timedelta(days=7) else "normal"
