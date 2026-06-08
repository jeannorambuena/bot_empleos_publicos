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

RELEVANT_LEVELS = {"Alta", "Media", "Baja"}
RECOMMENDED_LEVELS = {"Alta", "Media"}
MAX_RECOMMENDATIONS = 5
VERY_HIGH_MANUAL_REVIEW_SCORE = 90
LOCAL_SOURCE_DIAGNOSTICS = (
    ROOT / "output" / "sources" / "romeral" / "diagnostics.json",
)


def _load(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_public_data() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Load the public payloads used by Telegram preview and policy simulation."""
    opportunities = _load(ROOT / "public" / "data" / "opportunities.json")
    summary = _load(ROOT / "public" / "data" / "summary.json")
    last_run = _load(ROOT / "public" / "data" / "last_run.json")

    if not isinstance(opportunities, list) or not isinstance(summary, dict) or not isinstance(last_run, dict):
        raise ValueError("JSON público inválido para preview Telegram.")

    return opportunities, summary, last_run


def is_profile_relevant(opportunity: dict[str, Any], *, levels: set[str] = RECOMMENDED_LEVELS) -> bool:
    """Return whether an opportunity is safe and relevant for Jean's profile."""
    markers = " ".join(
        [
            str(opportunity.get("source") or ""),
            *(str(tag) for tag in opportunity.get("tags") or []),
            *(str(category) for category in opportunity.get("categories") or []),
        ]
    ).lower()

    return (
        opportunity.get("match_level") in levels
        and opportunity.get("human_feedback_action") != "false_positive"
        and opportunity.get("manual_review") is not True
        and opportunity.get("offer_scope") != "external_private"
        and "omil" not in markers
    )


def _can_be_telegram_recommendation(item: dict[str, Any]) -> bool:
    """Return whether an item passes the Santiago/RM economic viability rule for Telegram preview."""
    if item.get("economic_viability") != "bajo_piso":
        return True

    comparison_score = int(item.get("pre_economic_match_score") or item.get("match_score") or 0)
    return comparison_score >= VERY_HIGH_MANUAL_REVIEW_SCORE


def select_recommended(opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a short actionable selection for a Telegram digest."""
    recommended = [
        item
        for item in opportunities
        if is_profile_relevant(item) and _can_be_telegram_recommendation(item)
    ]

    recommended.sort(
        key=lambda item: (
            item.get("is_new_since_last_run") is not True,
            item.get("urgency") != "proximo",
            -int(item.get("match_score", 0)),
            item.get("closing_date") or "9999-12-31",
        )
    )

    return recommended[:MAX_RECOMMENDATIONS]


def is_new_relevant(opportunity: dict[str, Any]) -> bool:
    return opportunity.get("is_new_since_last_run") is True and is_profile_relevant(
        opportunity,
        levels=RELEVANT_LEVELS,
    )


def is_high_closing_soon(opportunity: dict[str, Any]) -> bool:
    return opportunity.get("urgency") == "proximo" and is_profile_relevant(
        opportunity,
        levels={"Alta"},
    )


def is_relevant_closing_soon(opportunity: dict[str, Any]) -> bool:
    return opportunity.get("urgency") == "proximo" and is_profile_relevant(
        opportunity,
        levels=RELEVANT_LEVELS,
    )


def _short(value: Any, *, limit: int) -> str:
    text = str(value or "No especificado").strip()
    return text if len(text) <= limit else f"{text[: limit - 1].rstrip()}…"


def _location(opportunity: dict[str, Any]) -> str:
    values = [
        opportunity.get("region"),
        opportunity.get("commune"),
    ]
    visible = [str(value) for value in values if value and value != "No especificada"]
    return " / ".join(visible) or "No especificada"


def _format_recommendation(index: int, opportunity: dict[str, Any]) -> list[str]:
    new_marker = " | NUEVA" if opportunity.get("is_new_since_last_run") is True else ""

    lines = [
        f"{index}. [{opportunity.get('match_level', 'Sin nivel')} | {opportunity.get('match_score', 0)}%{new_marker}] {_short(opportunity.get('title'), limit=120)}",
        f"   Organismo: {_short(opportunity.get('institution'), limit=90)}",
        f"   Ubicación: {_location(opportunity)}",
        f"   Cierre: {opportunity.get('closing_date') or 'No especificado'}",
        f"   Link: {opportunity.get('source_url') or 'Sin enlace directo'}",
    ]

    if opportunity.get("economic_alert"):
        suffix = " | Revisión manual" if opportunity.get("economic_viability") == "bajo_piso" else ""
        lines.insert(3, f"   Alerta económica: {opportunity['economic_alert']}{suffix}")

    return lines


def local_source_notices() -> list[str]:
    """Return controlled local-source notices from optional dry-run diagnostics."""
    notices = []
    for path in LOCAL_SOURCE_DIAGNOSTICS:
        if not path.exists():
            continue
        try:
            diagnostics = _load(path)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(diagnostics, dict):
            continue
        notice = diagnostics.get("telegram_notice")
        if diagnostics.get("source_change_detected") is True and isinstance(notice, str) and notice.strip():
            notices.append(notice.strip())
    return notices


def main() -> int:
    try:
        opportunities, summary, last_run = load_public_data()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    recommended = select_recommended(opportunities)
    new_relevant = sum(is_new_relevant(item) for item in opportunities)
    relevant_closing_soon = sum(is_relevant_closing_soon(item) for item in opportunities)
    generated_at = last_run.get("finished_at") or datetime.now().astimezone().isoformat(timespec="seconds")

    lines = [
        "Radar Laboral Público Chile",
        "Reporte generado desde GitHub Actions",
        f"Fecha/hora: {generated_at}",
        "",
        f"Total oportunidades: {summary.get('total_opportunities', len(opportunities))}",
        f"Nuevas relevantes: {new_relevant}",
        f"Altas: {sum(item.get('match_level') == 'Alta' for item in opportunities)}",
        f"Medias: {sum(item.get('match_level') == 'Media' for item in opportunities)}",
        f"Cierres próximos relevantes: {relevant_closing_soon}",
        "",
        "Recomendadas:",
    ]

    if recommended:
        for index, item in enumerate(recommended, start=1):
            lines.extend(_format_recommendation(index, item))
    else:
        lines.append("- No hay oportunidades recomendadas en este corte.")

    notices = local_source_notices()
    if notices:
        lines.extend(["", "Avisos fuentes locales:"])
        lines.extend(f"- {notice}" for notice in notices)

    lines.extend(
        [
            "",
            f"Dashboard: {DASHBOARD_URL}",
            "",
            "Envío manual seguro del radar laboral.",
        ]
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "telegram-preview.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"OK: preview Telegram generado ({len(recommended)} recomendadas). No se envió ningún mensaje.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
