"""Validate the JSON files consumed by the static dashboard."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.contracts import missing_opportunity_fields
from radar.scoring import match_level_for_score
from radar.sources.sanitization import sensitive_personal_data_reasons


PUBLIC_DATA = ROOT / "public" / "data"
MATCH_LEVELS = {"Alta", "Media", "Baja", "Descartada"}
FEEDBACK_ACTIONS = {"useful", "false_positive", "review", "boost_priority", "lower_priority"}
RANCAGUA_SOURCE = "Municipalidad de Rancagua"
PUBLICABLE_TEXT_FIELDS = ("title", "description", "evidence", "status_reason", "manual_review_reason")


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
    if opportunity.get("offer_scope") == "external_private":
        errors.append(f"{label}: public/data no puede publicar ofertas OMIL externas privadas.")
    if opportunity.get("source") != "Empleos Públicos" and opportunity.get("manual_review") is True:
        errors.append(f"{label}: public/data no puede publicar manual_review de fuentes nuevas.")
    for field in PUBLICABLE_TEXT_FIELDS:
        value = opportunity.get(field)
        values = value if isinstance(value, list) else [value]
        for candidate in values:
            if isinstance(candidate, str) and sensitive_personal_data_reasons(candidate):
                errors.append(f"{label}.{field}: contiene datos personales visibles.")
    for document in opportunity.get("document_urls") or []:
        if isinstance(document, dict) and sensitive_personal_data_reasons(document.get("name")):
            errors.append(f"{label}.document_urls[].name: contiene datos personales visibles.")
    if opportunity.get("source") == RANCAGUA_SOURCE:
        errors.extend(_validate_rancagua(opportunity, label))
    return errors


def _validate_rancagua(opportunity: dict[str, Any], label: str) -> list[str]:
    errors = []
    if opportunity.get("status") != "open_confirmed":
        errors.append(f"{label}: Rancagua publicada debe conservar status=open_confirmed.")
    if opportunity.get("offer_scope") != "municipal":
        errors.append(f"{label}: Rancagua publicada debe conservar offer_scope=municipal.")
    if opportunity.get("implementation_status") != "published_controlled":
        errors.append(f"{label}: Rancagua publicada debe conservar marca published_controlled.")
    try:
        closing_date = date.fromisoformat(str(opportunity.get("closing_date")))
    except ValueError:
        errors.append(f"{label}: Rancagua publicada requiere closing_date ISO.")
    else:
        if closing_date < date.today():
            errors.append(f"{label}: Rancagua publicada no puede tener cierre pasado.")
    try:
        hostname = (urlparse(str(opportunity.get("source_url"))).hostname or "").lower()
    except ValueError:
        hostname = ""
    if hostname != "rgua.cl" and not hostname.endswith(".rgua.cl") and hostname != "munirancagua.gob.cl":
        errors.append(f"{label}: Rancagua publicada requiere source_url oficial o trazable.")
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
