"""Generate local .ics reminders without connecting to calendar services."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.calendar_preview import generate_calendar, select_calendar_opportunities
from radar.config_loader import ConfigurationError, load_json


OUTPUT = ROOT / "output" / "calendar"
ICS_PATH = OUTPUT / "radar-laboral-reminders.ics"
SUMMARY_PATH = OUTPUT / "calendar-summary.json"


def _reference_time(last_run: Any) -> datetime:
    if isinstance(last_run, dict) and isinstance(last_run.get("finished_at"), str):
        try:
            return datetime.fromisoformat(last_run["finished_at"])
        except ValueError:
            pass
    return datetime.now().astimezone()


def main() -> int:
    try:
        opportunities = load_json(ROOT / "public" / "data" / "opportunities.json")
        last_run = load_json(ROOT / "public" / "data" / "last_run.json")
    except ConfigurationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not isinstance(opportunities, list):
        print("ERROR: opportunities.json debe contener una lista.", file=sys.stderr)
        return 1

    generated_at = _reference_time(last_run)
    alertable = select_calendar_opportunities(
        opportunities,
        reference_date=generated_at.date(),
    )
    calendar_text, event_summary = generate_calendar(alertable, generated_at=generated_at)
    summary = {
        "mode": "preview",
        "calendar_connected": False,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "total_opportunities_read": len(opportunities),
        "total_alertable_opportunities": len(alertable),
        **event_summary,
    }

    OUTPUT.mkdir(parents=True, exist_ok=True)
    ICS_PATH.write_text(calendar_text, encoding="utf-8", newline="")
    with SUMMARY_PATH.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(summary, file, ensure_ascii=False, indent=2)
        file.write("\n")

    print("Preview de calendario generado. No se conectó Google Calendar.")
    print(f"total oportunidades leídas: {summary['total_opportunities_read']}")
    print(f"total eventos generados: {summary['total_events']}")
    print(f"eventos de decisión: {summary['decision_events']}")
    print(f"eventos de cierre: {summary['closing_events']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
