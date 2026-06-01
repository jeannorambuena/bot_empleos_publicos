"""Maintain a small public history for dashboard opportunities."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable


HISTORY_FIELDS = (
    "id",
    "first_seen_at",
    "last_seen_at",
    "seen_count",
    "last_title",
    "last_institution",
    "last_level",
    "last_score",
    "currently_visible",
)


def load_history(path: str | Path) -> list[dict[str, Any]]:
    """Load public history when it exists, otherwise start with an empty list."""
    history_path = Path(path)
    if not history_path.exists():
        return []
    with history_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError("history.json debe contener una lista.")
    return payload


def update_history(
    opportunities: Iterable[dict[str, Any]],
    previous_history: Iterable[dict[str, Any]],
    run_timestamp: str,
) -> list[dict[str, Any]]:
    """Update public history and preserve entries missing from the latest capture."""
    history_by_id = {
        str(item.get("id")): deepcopy(item)
        for item in previous_history
        if isinstance(item, dict) and item.get("id")
    }
    visible_ids: set[str] = set()

    for opportunity in opportunities:
        opportunity_id = str(opportunity.get("id", ""))
        if not opportunity_id:
            continue
        visible_ids.add(opportunity_id)
        previous = history_by_id.get(opportunity_id)
        first_seen_at = previous.get("first_seen_at") if previous else run_timestamp
        seen_count = int(previous.get("seen_count", 0)) + 1 if previous else 1
        history_by_id[opportunity_id] = {
            "id": opportunity_id,
            "first_seen_at": first_seen_at,
            "last_seen_at": run_timestamp,
            "seen_count": seen_count,
            "last_title": opportunity.get("title", ""),
            "last_institution": opportunity.get("institution", ""),
            "last_level": opportunity.get("match_level", "Descartada"),
            "last_score": int(opportunity.get("match_score", 0)),
            "currently_visible": True,
        }

    for opportunity_id, item in history_by_id.items():
        if opportunity_id not in visible_ids:
            item["currently_visible"] = False

    return sorted(history_by_id.values(), key=lambda item: str(item["id"]))


def apply_history_to_opportunities(
    opportunities: Iterable[dict[str, Any]],
    history: Iterable[dict[str, Any]],
    *,
    previous_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Attach history metadata to currently visible opportunities."""
    history_by_id = {str(item.get("id")): item for item in history if item.get("id")}
    known_before_run = previous_ids or set()
    enriched = []
    for opportunity in opportunities:
        item = deepcopy(opportunity)
        opportunity_id = str(item.get("id", ""))
        record = history_by_id.get(opportunity_id, {})
        item["is_new_since_last_run"] = opportunity_id not in known_before_run
        item["first_seen_at"] = record.get("first_seen_at")
        item["last_seen_at"] = record.get("last_seen_at")
        item["seen_count"] = int(record.get("seen_count", 0))
        enriched.append(item)
    return enriched


def build_history_summary(
    opportunities: Iterable[dict[str, Any]],
    history: Iterable[dict[str, Any]],
) -> dict[str, int]:
    """Return public metrics derived from the latest capture and full history."""
    items = list(opportunities)
    records = list(history)
    new_items = [item for item in items if item.get("is_new_since_last_run") is True]
    return {
        "total_opportunities": len(items),
        "new_opportunities": len(new_items),
        "previously_seen": len(items) - len(new_items),
        "first_seen_this_run": len(new_items),
        "not_seen_in_latest_capture": sum(
            item.get("currently_visible") is False for item in records
        ),
    }


def write_history(path: str | Path, history: list[dict[str, Any]]) -> None:
    """Write versionable public history using stable UTF-8 formatting."""
    history_path = Path(path)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(history, file, ensure_ascii=False, indent=2)
        file.write("\n")
