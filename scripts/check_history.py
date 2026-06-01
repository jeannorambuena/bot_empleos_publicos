"""Validate versionable public opportunity history."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATA = ROOT / "public" / "data"
SECRET_MARKERS = ("token", "secret", "password", "smtp", "chat_id", "telegram_bot")
HISTORY_FIELDS = {
    "id",
    "first_seen_at",
    "last_seen_at",
    "seen_count",
    "last_title",
    "last_institution",
    "last_level",
    "last_score",
    "currently_visible",
}
OPPORTUNITY_HISTORY_FIELDS = {
    "is_new_since_last_run",
    "first_seen_at",
    "last_seen_at",
    "seen_count",
}


def _load(path: Path) -> Any:
    if not path.exists():
        raise ValueError(f"No existe: {path}")
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    try:
        history = _load(PUBLIC_DATA / "history.json")
        opportunities = _load(PUBLIC_DATA / "opportunities.json")
        summary = _load(PUBLIC_DATA / "summary.json")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if not isinstance(history, list) or not isinstance(opportunities, list) or not isinstance(summary, dict):
        errors.append("history y opportunities deben ser listas; summary debe ser objeto.")
    else:
        ids: list[str] = []
        for index, item in enumerate(history):
            if not isinstance(item, dict):
                errors.append(f"history[{index}] debe ser objeto.")
                continue
            missing = HISTORY_FIELDS - item.keys()
            if missing:
                errors.append(f"history[{index}] sin campos: {', '.join(sorted(missing))}")
            ids.append(str(item.get("id", "")))
        if len(ids) != len(set(ids)):
            errors.append("history.json contiene ids duplicados.")

        for index, item in enumerate(opportunities):
            missing = OPPORTUNITY_HISTORY_FIELDS - item.keys()
            if missing:
                errors.append(f"opportunities[{index}] sin historial: {', '.join(sorted(missing))}")

        expected_new = sum(item.get("is_new_since_last_run") is True for item in opportunities)
        expected_hidden = sum(item.get("currently_visible") is False for item in history)
        if summary.get("new_opportunities") != expected_new:
            errors.append("summary.new_opportunities no coincide con oportunidades nuevas.")
        if summary.get("first_seen_this_run") != expected_new:
            errors.append("summary.first_seen_this_run no coincide con oportunidades nuevas.")
        if summary.get("previously_seen") != len(opportunities) - expected_new:
            errors.append("summary.previously_seen no coincide con oportunidades ya vistas.")
        if summary.get("not_seen_in_latest_capture") != expected_hidden:
            errors.append("summary.not_seen_in_latest_capture no coincide con historial.")

    for item in history if isinstance(history, list) else []:
        for key in item if isinstance(item, dict) else {}:
            if any(marker in str(key).lower() for marker in SECRET_MARKERS):
                errors.append("history.json contiene un campo asociado a secretos.")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: historial público válido ({len(history)} registros).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
