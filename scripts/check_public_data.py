"""Validate the JSON files consumed by the static dashboard."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.contracts import missing_opportunity_fields
from radar.scoring import match_level_for_score


PUBLIC_DATA = ROOT / "public" / "data"
MATCH_LEVELS = {"Alta", "Media", "Baja", "Descartada"}
FEEDBACK_ACTIONS = {"useful", "false_positive", "review", "boost_priority", "lower_priority"}


def _load_json(path: Path) -> Any:
    if not path.exists():
        raise ValueError(f"No existe: {path}")
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON inválido en {path}: {error}") from error


def _validate_opportunity(opportunity: Any, index: int) -> list[str]:
    label = f"opportunities[{index}]"
    if not isinstance(opportunity, dict):
        return [f"{label}: debe ser un objeto JSON."]

    errors = []
    missing = missing_opportunity_fields(opportunity)
    if missing:
        errors.append(f"{label}: faltan campos: {', '.join(missing)}")

    score = opportunity.get("match_score")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        errors.append(f"{label}: match_score debe ser entero entre 0 y 100.")
    elif opportunity.get("match_level") != match_level_for_score(score):
        errors.append(f"{label}: match_level no corresponde al puntaje {score}.")
    elif opportunity.get("match_level") not in MATCH_LEVELS:
        errors.append(f"{label}: match_level no pertenece a los niveles permitidos.")

    if opportunity.get("is_demo") is True and opportunity.get("source_url") is not None:
        errors.append(f"{label}: source_url debe ser null cuando is_demo es true.")

    if "human_reviewed" in opportunity and not isinstance(opportunity.get("human_reviewed"), bool):
        errors.append(f"{label}: human_reviewed debe ser booleano.")
    action = opportunity.get("human_feedback_action")
    if action is not None and action not in FEEDBACK_ACTIONS:
        errors.append(f"{label}: human_feedback_action no permitida.")
    if action == "false_positive" and opportunity.get("match_level") != "Descartada":
        errors.append(f"{label}: false_positive debe quedar como Descartada.")
    if "manual_review" in opportunity and not isinstance(opportunity.get("manual_review"), bool):
        errors.append(f"{label}: manual_review debe ser booleano.")
    return errors


def main() -> int:
    try:
        opportunities = _load_json(PUBLIC_DATA / "opportunities.json")
        summary = _load_json(PUBLIC_DATA / "summary.json")
        last_run = _load_json(PUBLIC_DATA / "last_run.json")
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    errors = []
    if not isinstance(opportunities, list):
        errors.append("opportunities.json debe contener una lista.")
    else:
        for index, opportunity in enumerate(opportunities):
            errors.extend(_validate_opportunity(opportunity, index))
    if not isinstance(summary, dict):
        errors.append("summary.json debe contener un objeto.")
    if not isinstance(last_run, dict):
        errors.append("last_run.json debe contener un objeto.")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: datos públicos válidos ({len(opportunities)} oportunidades).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
