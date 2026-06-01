"""Validate the locally generated calendar preview."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "calendar"
ICS_PATH = OUTPUT / "radar-laboral-reminders.ics"
SUMMARY_PATH = OUTPUT / "calendar-summary.json"


def main() -> int:
    errors = []
    for path in (ICS_PATH, SUMMARY_PATH):
        if not path.exists():
            errors.append(f"No existe: {path}")

    if errors:
        return _fail(errors)

    calendar_text = ICS_PATH.read_text(encoding="utf-8")
    try:
        summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return _fail([f"JSON inválido en {SUMMARY_PATH}: {error}"])

    if "BEGIN:VCALENDAR" not in calendar_text:
        errors.append("El archivo .ics no contiene BEGIN:VCALENDAR.")
    if "END:VCALENDAR" not in calendar_text:
        errors.append("El archivo .ics no contiene END:VCALENDAR.")
    if summary.get("total_alertable_opportunities", 0) > 0 and "BEGIN:VEVENT" not in calendar_text:
        errors.append("El archivo .ics no contiene VEVENT para oportunidades alertables.")
    if calendar_text.count("BEGIN:VEVENT") != summary.get("total_events"):
        errors.append("La cantidad de VEVENT no coincide con calendar-summary.json.")
    if summary.get("calendar_connected") is not False:
        errors.append("calendar-summary.json debe confirmar que no se conectó un calendario real.")

    if errors:
        return _fail(errors)

    print(f"OK: preview de calendario válido ({summary.get('total_events', 0)} eventos).")
    return 0


def _fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
