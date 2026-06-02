"""Validate the local Telegram digest preview."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "output" / "telegram" / "telegram-preview.txt"
FORBIDDEN = ("telegram_bot_token", "bot token", "chat_id", "api.telegram.org/bot")


def main() -> int:
    errors: list[str] = []
    if not PREVIEW.exists():
        errors.append("No existe output/telegram/telegram-preview.txt.")
        text = ""
    else:
        text = PREVIEW.read_text(encoding="utf-8")
    lowered = text.lower()
    if any(marker in lowered for marker in FORBIDDEN):
        errors.append("El preview contiene un marcador sensible de Telegram.")
    for expected in ("Radar Laboral Público Chile", "Total oportunidades:", "Nuevas relevantes:", "Cierres próximos relevantes:", "Reporte generado desde GitHub Actions"):
        if expected not in text:
            errors.append(f"El preview no contiene: {expected}")
    if len(text) > 4096:
        errors.append("El preview supera el límite de 4096 caracteres de Telegram.")

    try:
        opportunities = json.loads((ROOT / "public" / "data" / "opportunities.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"No fue posible leer opportunities.json: {error}")
        opportunities = []
    if any(item.get("match_level") in {"Alta", "Media"} for item in opportunities):
        for expected in ("Recomendadas:", "Organismo:", "Ubicación:", "Cierre:", "Link:"):
            if expected not in text:
                errors.append(f"El preview accionable no contiene: {expected}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: preview Telegram válido y sin marcadores sensibles.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
