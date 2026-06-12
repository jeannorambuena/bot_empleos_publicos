"""Generate dashboard JSON files from locally normalized real opportunities."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.config_loader import ConfigurationError, load_json, load_profile
from radar.feedback import (
    apply_feedback_to_opportunity,
    build_feedback_index,
    build_feedback_summary,
    load_feedback_config,
)
from radar.history import (
    apply_history_to_opportunities,
    build_history_summary,
    load_history,
    update_history,
)
from radar.normalize_opportunity import score_real_opportunity
from radar.public_data import summarize_opportunities
from radar.atomic_publication import build_public_bundle, publish_public_bundle
from radar.sources.rancagua import SOURCE_ID as RANCAGUA_SOURCE_ID
from radar.sources.rancagua import fetch_rancagua_candidates
from radar.sources.sanitization import has_sensitive_personal_data, sanitize_opportunity


NORMALIZED_PATH = ROOT / "data" / "normalized" / "empleos_publicos_normalized.json"
SOURCE_CATALOG_PATH = ROOT / "data" / "source_candidates.json"
PUBLIC_DATA = ROOT / "public" / "data"
HISTORY_PATH = PUBLIC_DATA / "history.json"
FEEDBACK_PATH = ROOT / "config" / "feedback.json"
RANCAGUA_SOURCE = "Municipalidad de Rancagua"
PUBLICABLE_RANCAGUA_FIELDS = ("title", "description", "status_reason", "manual_review_reason")


def _load_rancagua_discovery_url() -> str:
    try:
        payload = json.loads(SOURCE_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"No fue posible leer {SOURCE_CATALOG_PATH}: {error}") from error
    sources = payload.get("sources") if isinstance(payload, dict) else None
    matches = [item for item in sources or [] if isinstance(item, dict) and item.get("id") == RANCAGUA_SOURCE_ID]
    if len(matches) != 1:
        raise ValueError(f"El catalogo debe contener exactamente una ficha {RANCAGUA_SOURCE_ID}.")
    discovery_url = matches[0].get("discovery_url")
    if not isinstance(discovery_url, str) or not discovery_url.strip():
        raise ValueError(f"La ficha {RANCAGUA_SOURCE_ID} no tiene discovery_url valida.")
    return discovery_url


def _is_traceable_rancagua_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        hostname = (urlparse(value).hostname or "").lower()
    except ValueError:
        return False
    return hostname == "rgua.cl" or hostname.endswith(".rgua.cl") or hostname == "munirancagua.gob.cl"


def _contains_sensitive_data(item: dict[str, Any]) -> bool:
    values = [item.get(field) for field in PUBLICABLE_RANCAGUA_FIELDS]
    values.extend(item.get("evidence") or [])
    values.extend(
        document.get("name")
        for document in item.get("document_urls") or []
        if isinstance(document, dict)
    )
    return any(has_sensitive_personal_data(value) for value in values if isinstance(value, str))


def _load_publishable_rancagua(today: date) -> tuple[list[dict[str, Any]], int]:
    opportunities, _ = fetch_rancagua_candidates(_load_rancagua_discovery_url())
    publishable = []
    for captured in opportunities:
        item = sanitize_opportunity(captured)
        try:
            closing_date = date.fromisoformat(str(item.get("closing_date")))
        except ValueError:
            continue
        if (
            item.get("source") != RANCAGUA_SOURCE
            or item.get("implementation_status") != "dry_run"
            or item.get("status") != "open_confirmed"
            or item.get("offer_scope") != "municipal"
            or item.get("manual_review") is not False
            or closing_date < today
            or not _is_traceable_rancagua_url(item.get("source_url"))
            or _contains_sensitive_data(item)
        ):
            continue
        item["implementation_status"] = "published_controlled"
        item["tags"] = [tag for tag in item.get("tags", []) if tag != "dry_run"]
        item["tags"].append("municipal_controlled")
        publishable.append(item)
    return publishable, len(opportunities)


def main() -> int:
    try:
        profile = load_profile(ROOT / "config" / "profile.example.json")
        opportunities = load_json(NORMALIZED_PATH)
        rancagua, rancagua_detected = _load_publishable_rancagua(datetime.now().astimezone().date())
    except (ConfigurationError, RuntimeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not isinstance(opportunities, list) or not opportunities:
        print("ERROR: No hay datos reales normalizados. Ejecuta scripts/fetch_empleos_publicos.py.", file=sys.stderr)
        return 1

    opportunities.extend(rancagua)
    generated_at = datetime.now().astimezone()
    scored = [score_real_opportunity(item, profile) for item in opportunities]
    try:
        feedback_entries = load_feedback_config(FEEDBACK_PATH)
    except (OSError, ValueError) as error:
        print(f"ERROR: No fue posible cargar config/feedback.json: {error}", file=sys.stderr)
        return 1
    feedback_index = build_feedback_index(feedback_entries)
    scored = [apply_feedback_to_opportunity(item, feedback_index) for item in scored]
    scored.sort(key=lambda item: (-item["match_score"], item.get("closing_date") or "9999-12-31"))
    try:
        previous_history = load_history(HISTORY_PATH)
    except (OSError, ValueError) as error:
        print(f"ERROR: No fue posible cargar history.json: {error}", file=sys.stderr)
        return 1
    previous_ids = {str(item.get("id")) for item in previous_history if item.get("id")}
    history = update_history(scored, previous_history, generated_at.isoformat(timespec="seconds"))
    scored = apply_history_to_opportunities(scored, history, previous_ids=previous_ids)
    summary = summarize_opportunities(scored, generated_at=generated_at)
    history_summary = build_history_summary(scored, history)
    summary.update(history_summary)
    summary["active_opportunities"] = history_summary["total_opportunities"]
    summary["high_relevance"] = summary["high_match"]
    summary.update(build_feedback_summary(scored))
    last_run = {
        "finished_at": generated_at.isoformat(timespec="seconds"),
        "status": "real-local",
        "message": "Datos reales locales generados correctamente",
    }
    bundle = build_public_bundle(
        scored,
        summary,
        last_run,
        history,
        generated_at=generated_at,
    )
    publish_public_bundle(PUBLIC_DATA, bundle)

    levels = {"Alta": 0, "Media": 0, "Baja": 0, "Descartada": 0}
    for item in scored:
        levels[item["match_level"]] += 1
    with_url = sum(bool(item.get("source_url")) for item in scored)
    print(f"total: {len(scored)}")
    for level in ("Alta", "Media", "Baja", "Descartada"):
        print(f"{level}: {levels[level]}")
    print(f"con source_url real: {with_url}")
    print(f"sin source_url: {len(scored) - with_url}")
    print(f"Rancagua detectadas: {rancagua_detected}")
    print(f"Rancagua publicadas: {len(rancagua)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
