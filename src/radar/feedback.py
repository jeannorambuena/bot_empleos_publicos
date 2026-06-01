"""Apply versioned human feedback as an auditable post-scoring layer."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable

from .scoring import match_level_for_score


ALLOWED_ACTIONS = {"useful", "false_positive", "review", "boost_priority", "lower_priority"}
ACTION_ALIASES = {"raise_priority": "boost_priority"}
USEFUL_BOOST = 8
PRIORITY_BOOST = 12
PRIORITY_PENALTY = 12
ACTION_REASONS = {
    "useful": "Marcada como útil por revisión humana",
    "false_positive": "Marcada como falso positivo por revisión humana",
    "review": "Marcada para revisión humana",
    "boost_priority": "Prioridad aumentada por revisión humana",
    "lower_priority": "Prioridad reducida por revisión humana",
}
SENSITIVE_KEYS = ("token", "secret", "password", "email", "telegram", "chat_id", "smtp")
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
TELEGRAM_TOKEN_PATTERN = re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b")
SENSITIVE_VALUE_MARKERS = ("telegram_bot_token", "telegram_chat_id", "smtp_pass", "api_key")


def load_feedback_config(path: str | Path) -> list[dict[str, Any]]:
    """Load optional versioned feedback configuration."""
    feedback_path = Path(path)
    if not feedback_path.exists():
        return []
    with feedback_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    return normalize_feedback_entries(payload)


def normalize_feedback_entries(raw_feedback: Any) -> list[dict[str, Any]]:
    """Normalize config files and browser exports into stable feedback entries."""
    if not isinstance(raw_feedback, dict):
        raise ValueError("El feedback debe ser un objeto JSON.")
    _validate_no_sensitive_payload(raw_feedback)

    raw_items = raw_feedback.get("items")
    if raw_items is None and isinstance(raw_feedback.get("feedback"), dict):
        raw_items = [
            {
                "opportunity_id": opportunity_id,
                "action": details.get("action") or details.get("label"),
                "reason": details.get("reason"),
                "created_at": details.get("created_at") or details.get("updated_at"),
                "title": details.get("title"),
                "source_url": details.get("source_url"),
            }
            for opportunity_id, details in raw_feedback["feedback"].items()
            if isinstance(details, dict)
        ]
    if not isinstance(raw_items, list):
        raise ValueError("El feedback debe contener una lista items.")

    normalized = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise ValueError("Cada entrada de feedback debe ser un objeto JSON.")
        item = {
            "opportunity_id": str(raw_item.get("opportunity_id") or "").strip(),
            "action": ACTION_ALIASES.get(str(raw_item.get("action") or "").strip(), str(raw_item.get("action") or "").strip()),
        }
        for field in ("reason", "created_at", "title", "source_url"):
            value = raw_item.get(field)
            if value is not None and str(value).strip():
                item[field] = str(value).strip()
        normalized.append(item)
    validate_feedback_entries(normalized)
    return sorted(normalized, key=lambda item: (item["opportunity_id"], item["action"]))


def validate_feedback_entries(entries: Iterable[dict[str, Any]]) -> None:
    """Reject malformed, sensitive or contradictory feedback."""
    seen: dict[str, str] = {}
    for index, item in enumerate(entries):
        opportunity_id = item.get("opportunity_id")
        action = item.get("action")
        if not isinstance(opportunity_id, str) or not opportunity_id.strip():
            raise ValueError(f"items[{index}].opportunity_id no puede estar vacío.")
        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"items[{index}].action no permitida: {action}")
        previous_action = seen.get(opportunity_id)
        if previous_action and previous_action != action:
            raise ValueError(f"Feedback contradictorio para opportunity_id: {opportunity_id}")
        if previous_action:
            raise ValueError(f"Feedback duplicado para opportunity_id: {opportunity_id}")
        seen[opportunity_id] = str(action)

        for key, value in item.items():
            if any(marker in str(key).lower() for marker in SENSITIVE_KEYS):
                raise ValueError(f"items[{index}] contiene campo sensible: {key}")
            if EMAIL_PATTERN.search(str(value)):
                raise ValueError(f"items[{index}] contiene un email no permitido.")
            if TELEGRAM_TOKEN_PATTERN.search(str(value)) or any(
                marker in str(value).lower() for marker in SENSITIVE_VALUE_MARKERS
            ):
                raise ValueError(f"items[{index}] contiene un valor sensible.")


def build_feedback_index(entries: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index feedback by stable id, with optional source URL and title fallbacks."""
    index: dict[str, dict[str, Any]] = {}
    for entry in entries:
        index[f"id:{entry['opportunity_id']}"] = entry
        if entry.get("source_url"):
            index[f"url:{entry['source_url']}"] = entry
        if entry.get("title"):
            index[f"title:{entry['title']}"] = entry
    return index


def apply_feedback_to_opportunity(
    opportunity: dict[str, Any],
    feedback_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Apply human feedback after base scoring without deleting the opportunity."""
    item = deepcopy(opportunity)
    entry = _find_feedback(item, feedback_index)
    item["base_match_score"] = int(item.get("match_score", 0))
    item["base_match_level"] = item.get("match_level", "Descartada")
    item["human_reviewed"] = entry is not None
    item["human_feedback_action"] = entry.get("action") if entry else None
    item["human_feedback_reason"] = entry.get("reason") if entry else None
    item["manual_review"] = entry.get("action") == "review" if entry else False
    if not entry:
        return item

    action = entry["action"]
    score = int(item.get("match_score", 0))
    if action == "false_positive":
        score = 0
        level = "Descartada"
    else:
        if action == "useful":
            score += USEFUL_BOOST
        elif action == "boost_priority":
            score += PRIORITY_BOOST
        elif action == "lower_priority":
            score -= PRIORITY_PENALTY
        score = max(0, min(100, score))
        level = match_level_for_score(score)

    item["match_score"] = score
    item["match_level"] = level
    reasons = list(item.get("alert_reasons") or [])
    visible_reason = ACTION_REASONS[action]
    if visible_reason not in reasons:
        reasons.append(visible_reason)
    if entry.get("reason"):
        reasons.append(f"Motivo de revisión humana: {entry['reason']}")
    item["alert_reasons"] = reasons
    return item


def build_feedback_summary(opportunities: Iterable[dict[str, Any]]) -> dict[str, int]:
    """Summarize applied human feedback for public diagnostics."""
    items = list(opportunities)
    return {
        "human_feedback_applied": sum(item.get("human_reviewed") is True for item in items),
        "human_false_positives": sum(item.get("human_feedback_action") == "false_positive" for item in items),
        "human_boosted": sum(item.get("human_feedback_action") in {"useful", "boost_priority"} for item in items),
        "human_lowered": sum(item.get("human_feedback_action") == "lower_priority" for item in items),
        "manual_review_count": sum(item.get("manual_review") is True for item in items),
    }


def _find_feedback(
    opportunity: dict[str, Any],
    feedback_index: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    for key in (
        f"id:{opportunity.get('id')}",
        f"url:{opportunity.get('source_url')}",
        f"title:{opportunity.get('title')}",
    ):
        if key in feedback_index:
            return feedback_index[key]
    return None


def _validate_no_sensitive_payload(value: Any, *, path: str = "feedback") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if any(marker in str(key).lower() for marker in SENSITIVE_KEYS):
                raise ValueError(f"{path} contiene campo sensible: {key}")
            _validate_no_sensitive_payload(child, path=f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_sensitive_payload(child, path=f"{path}[{index}]")
        return
    text = str(value)
    if EMAIL_PATTERN.search(text):
        raise ValueError(f"{path} contiene un email no permitido.")
    if TELEGRAM_TOKEN_PATTERN.search(text) or any(
        marker in text.lower() for marker in SENSITIVE_VALUE_MARKERS
    ):
        raise ValueError(f"{path} contiene un valor sensible.")
