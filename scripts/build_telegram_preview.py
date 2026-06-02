"""Generate a local Telegram digest preview without sending messages."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "telegram"
DASHBOARD_URL = os.environ.get("PUBLIC_SITE_URL") or "https://jeannorambuena.github.io/bot_empleos_publicos/"


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def main() -> int:
    try:
        opportunities = _load(ROOT / "public" / "data" / "opportunities.json")
        summary = _load(ROOT / "public" / "data" / "summary.json")
        last_run = _load(ROOT / "public" / "data" / "last_run.json")
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not isinstance(opportunities, list) or not isinstance(summary, dict):
        print("ERROR: JSON público inválido para preview Telegram.", file=sys.stderr)
        return 1

    recommended = [
        item for item in opportunities
        if item.get("match_level") in {"Alta", "Media"}
    ][:5]
    generated_at = last_run.get("finished_at") or datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "Radar Laboral Público Chile",
        "Reporte generado desde GitHub Actions",
        f"Fecha/hora: {generated_at}",
        "",
        f"Total oportunidades: {summary.get('total_opportunities', len(opportunities))}",
        f"Nuevas reales: {summary.get('new_opportunities', 0)}",
        f"Altas: {sum(item.get('match_level') == 'Alta' for item in opportunities)}",
        f"Medias: {sum(item.get('match_level') == 'Media' for item in opportunities)}",
        f"Cierre próximo: {summary.get('closing_soon', 0)}",
        "",
        "Recomendadas:",
    ]
    if recommended:
        for item in recommended:
            lines.append(f"- {item.get('match_score', 0)}% | {item.get('title', 'Sin título')}")
    else:
        lines.append("- No hay oportunidades recomendadas en este corte.")
    lines.extend(["", f"Dashboard: {DASHBOARD_URL}", "", "Envío manual seguro del radar laboral."])

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "telegram-preview.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK: preview Telegram generado ({len(recommended)} recomendadas). No se envió ningún mensaje.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
