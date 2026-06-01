"""Public data contracts shared by future normalizers and exporters."""

from __future__ import annotations

from typing import Any


NORMALIZED_OPPORTUNITY_FIELDS = (
    "id",
    "title",
    "institution",
    "source",
    "source_url",
    "region",
    "commune",
    "closing_date",
    "detected_at",
    "status",
    "match_score",
    "match_level",
    "tags",
    "alert_reasons",
    "description",
    "is_demo",
    "url_status",
)


def missing_opportunity_fields(opportunity: dict[str, Any]) -> list[str]:
    """Return required normalized fields that are absent from an opportunity."""
    return [field for field in NORMALIZED_OPPORTUNITY_FIELDS if field not in opportunity]


def has_normalized_opportunity_contract(opportunity: dict[str, Any]) -> bool:
    """Check whether an opportunity exposes every required public field."""
    return not missing_opportunity_fields(opportunity)
