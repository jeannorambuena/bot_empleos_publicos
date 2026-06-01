"""Generate dashboard JSON files from locally normalized real opportunities."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


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
    write_history,
)
from radar.normalize_opportunity import score_real_opportunity
from radar.public_data import summarize_opportunities, write_public_data


NORMALIZED_PATH = ROOT / "data" / "normalized" / "empleos_publicos_normalized.json"
PUBLIC_DATA = ROOT / "public" / "data"
HISTORY_PATH = PUBLIC_DATA / "history.json"
FEEDBACK_PATH = ROOT / "config" / "feedback.json"


def main() -> int:
    try:
        profile = load_profile(ROOT / "config" / "profile.example.json")
        opportunities = load_json(NORMALIZED_PATH)
    except ConfigurationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not isinstance(opportunities, list) or not opportunities:
        print("ERROR: No hay datos reales normalizados. Ejecuta scripts/fetch_empleos_publicos.py.", file=sys.stderr)
        return 1

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
    write_public_data(PUBLIC_DATA, scored, summary, last_run)
    write_history(HISTORY_PATH, history)

    levels = {"Alta": 0, "Media": 0, "Baja": 0, "Descartada": 0}
    for item in scored:
        levels[item["match_level"]] += 1
    with_url = sum(bool(item.get("source_url")) for item in scored)
    print(f"total: {len(scored)}")
    for level in ("Alta", "Media", "Baja", "Descartada"):
        print(f"{level}: {levels[level]}")
    print(f"con source_url real: {with_url}")
    print(f"sin source_url: {len(scored) - with_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
