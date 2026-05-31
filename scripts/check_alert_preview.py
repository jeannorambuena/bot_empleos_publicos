"""Validate locally generated alert preview files."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "alerts"
TEXT_PREVIEW = OUTPUT / "email-preview.txt"
HTML_PREVIEW = OUTPUT / "email-preview.html"
SUMMARY = OUTPUT / "alert-summary.json"


def main() -> int:
    errors = []
    for path in (TEXT_PREVIEW, HTML_PREVIEW, SUMMARY):
        if not path.exists():
            errors.append(f"No existe: {path}")

    if errors:
        return _fail(errors)

    text = TEXT_PREVIEW.read_text(encoding="utf-8")
    html = HTML_PREVIEW.read_text(encoding="utf-8")
    try:
        summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return _fail([f"JSON inválido en {SUMMARY}: {error}"])

    if not text.strip():
        errors.append("El preview de texto plano está vacío.")
    if "<title>Radar Laboral Público Chile - Preview de alertas</title>" not in html:
        errors.append("El preview HTML no contiene el título esperado.")
    if summary.get("total_alertable", 0) > 0 and "<article>" not in html:
        errors.append("El preview HTML no contiene oportunidades alertables.")
    if summary.get("email_sent") is not False:
        errors.append("alert-summary.json debe confirmar que no se envió correo.")

    if errors:
        return _fail(errors)

    print(f"OK: preview de alertas válido ({summary.get('total_alertable', 0)} alertables).")
    return 0


def _fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
