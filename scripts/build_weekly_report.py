"""Build a local Markdown weekly operational report from public dashboard data."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATA = ROOT / "public" / "data"
OUTPUT_PATH = ROOT / "output" / "reports" / "weekly-report.md"
RELEVANT_LEVELS = {"Alta", "Media", "Baja"}
TOP_LIMIT = 8


def _load_json(name: str) -> Any:
    path = PUBLIC_DATA / name
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"No fue posible leer {path}: {error}") from error


def _is_relevant(item: dict[str, Any]) -> bool:
    return item.get("match_level") in RELEVANT_LEVELS


def _is_new_relevant(item: dict[str, Any]) -> bool:
    return item.get("is_new_since_last_run") is True and _is_relevant(item)


def _is_relevant_closing_soon(item: dict[str, Any]) -> bool:
    return item.get("urgency") == "proximo" and _is_relevant(item)


def _is_pending_review(item: dict[str, Any]) -> bool:
    explicit_review = item.get("manual_review") is True or item.get("human_feedback_action") == "review"
    priority_unreviewed = (
        item.get("human_reviewed") is not True
        and _is_relevant(item)
        and (item.get("match_level") == "Alta" or item.get("urgency") == "proximo")
    )
    return explicit_review or priority_unreviewed


def _sort_key(item: dict[str, Any]) -> tuple[bool, bool, int, str, str]:
    return (
        item.get("is_new_since_last_run") is not True,
        item.get("urgency") != "proximo",
        -int(item.get("match_score", 0)),
        str(item.get("closing_date") or "9999-12-31"),
        str(item.get("title") or ""),
    )


def _format_item(item: dict[str, Any]) -> str:
    markers = []
    if item.get("is_new_since_last_run") is True:
        markers.append("NUEVA")
    if item.get("urgency") == "proximo":
        markers.append("CIERRE PROXIMO")
    marker_text = f" | {', '.join(markers)}" if markers else ""
    return (
        f"- `{item.get('id', '-')}` | {item.get('match_score', 0)}% "
        f"{item.get('match_level', 'Sin nivel')}{marker_text} | "
        f"{item.get('title', 'Sin titulo')} | "
        f"{item.get('institution', 'Institucion no especificada')} | "
        f"cierre: {item.get('closing_date') or 'No especificado'}"
    )


def _append_items(lines: list[str], items: list[dict[str, Any]], *, empty_message: str) -> None:
    if items:
        lines.extend(_format_item(item) for item in items)
    else:
        lines.append(f"- {empty_message}")
    lines.append("")


def _operational_comment(
    new_relevant: list[dict[str, Any]],
    closing_soon: list[dict[str, Any]],
    pending_review: list[dict[str, Any]],
) -> str:
    if new_relevant:
        return "Revisar primero las oportunidades nuevas relevantes y confirmar sus fechas de cierre."
    if closing_soon:
        return "Revisar primero los cierres proximos relevantes para evitar perder plazos de postulacion."
    if pending_review:
        return "Priorizar las oportunidades pendientes de revision humana para mejorar el siguiente ciclo."
    return "No hay urgencias operativas en este corte; mantener seguimiento de las recomendaciones vigentes."


def main() -> int:
    try:
        opportunities = _load_json("opportunities.json")
        summary = _load_json("summary.json")
        history = _load_json("history.json")
        last_run = _load_json("last_run.json")
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not isinstance(opportunities, list) or not isinstance(history, list):
        print("ERROR: opportunities.json e history.json deben contener listas.", file=sys.stderr)
        return 1
    if not isinstance(summary, dict) or not isinstance(last_run, dict):
        print("ERROR: summary.json y last_run.json deben contener objetos.", file=sys.stderr)
        return 1

    relevant = sorted((item for item in opportunities if _is_relevant(item)), key=_sort_key)
    new_relevant = sorted((item for item in opportunities if _is_new_relevant(item)), key=_sort_key)
    high = sorted((item for item in opportunities if item.get("match_level") == "Alta"), key=_sort_key)
    closing_soon = sorted((item for item in opportunities if _is_relevant_closing_soon(item)), key=_sort_key)
    pending_review = sorted((item for item in opportunities if _is_pending_review(item)), key=_sort_key)
    false_positives = sorted(
        (item for item in opportunities if item.get("human_feedback_action") == "false_positive"),
        key=_sort_key,
    )
    top_recommended = relevant[:TOP_LIMIT]
    cutoff = last_run.get("finished_at") or "No especificada"
    hidden_history = sum(item.get("currently_visible") is False for item in history)

    lines = [
        "# Reporte semanal - Radar Laboral Publico Chile",
        "",
        f"- Fecha/hora del corte: `{cutoff}`",
        f"- Total de oportunidades capturadas: {summary.get('total_opportunities', len(opportunities))}",
        f"- Nuevas relevantes: {len(new_relevant)}",
        f"- Oportunidades Alta: {len(high)}",
        f"- Cierres proximos relevantes: {len(closing_soon)}",
        f"- Pendientes de revision humana: {len(pending_review)}",
        f"- Falsos positivos evitados por feedback humano: {len(false_positives)}",
        f"- Registros historicos no visibles en el ultimo corte: {hidden_history}",
        "",
        "## Comentario operativo",
        "",
        _operational_comment(new_relevant, closing_soon, pending_review),
        "",
        "## Top oportunidades recomendadas",
        "",
    ]
    _append_items(lines, top_recommended, empty_message="No hay oportunidades relevantes en este corte.")
    lines.extend(["## Nuevas relevantes", ""])
    _append_items(lines, new_relevant, empty_message="No hay oportunidades nuevas relevantes.")
    lines.extend(["## Cierres proximos relevantes", ""])
    _append_items(lines, closing_soon, empty_message="No hay cierres proximos relevantes.")
    lines.extend(["## Pendientes de revision humana", ""])
    _append_items(lines, pending_review, empty_message="No hay pendientes prioritarios de revision humana.")
    lines.extend(["## Falsos positivos evitados por feedback humano", ""])
    _append_items(lines, false_positives, empty_message="No hay falsos positivos registrados por feedback humano.")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print("Reporte semanal generado")
    print("-----------------------")
    print(f"Total capturado: {summary.get('total_opportunities', len(opportunities))}")
    print(f"Altas: {len(high)}")
    print(f"Nuevas relevantes: {len(new_relevant)}")
    print(f"Cierres proximos: {len(closing_soon)}")
    print(f"Pendientes de revision: {len(pending_review)}")
    print(f"Ruta: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
