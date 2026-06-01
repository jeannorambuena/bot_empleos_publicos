"""Build safe email previews for alertable public opportunities.

This module formats previews only. It deliberately contains no SMTP integration.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from html import escape
from typing import Any, Iterable


LOCAL_DASHBOARD_LABEL = "dashboard local/no configurado"


def select_alertable_opportunities(
    opportunities: Iterable[dict[str, Any]],
    alerts_config: dict[str, Any],
    *,
    reference_time: datetime,
) -> list[dict[str, Any]]:
    """Return active, non-discarded opportunities that match enabled alert rules."""
    selected = []
    for opportunity in opportunities:
        if opportunity.get("status") not in {"vigente", "abierta"}:
            continue
        if opportunity.get("match_level") == "Descartada":
            continue

        reasons = _alert_reasons(opportunity, alerts_config, reference_time)
        if reasons:
            item = dict(opportunity)
            item["preview_alert_reasons"] = reasons
            selected.append(item)

    selected.sort(key=lambda item: (-int(item.get("match_score", 0)), item.get("closing_date") or "9999-12-31"))
    return selected


def generate_email_subject(
    alertable_opportunities: Iterable[dict[str, Any]],
    *,
    is_demo: bool = True,
) -> str:
    """Create a concise subject for one digest-style preview email."""
    count = len(list(alertable_opportunities))
    mode = "PREVIEW DEMO" if is_demo else "PREVIEW"
    return f"[Radar Laboral Público Chile] {mode}: {count} oportunidades alertables"


def generate_text_body(
    alertable_opportunities: Iterable[dict[str, Any]],
    *,
    public_site_url: str | None = None,
    generated_at: datetime,
) -> str:
    """Create a readable plain-text digest without sending it."""
    items = list(alertable_opportunities)
    dashboard = public_site_url or LOCAL_DASHBOARD_LABEL
    lines = [
        "Radar Laboral Público Chile",
        "Vista previa de alertas por correo",
        "",
        "Este archivo es un preview local. No se envió ningún correo.",
        f"Generado: {generated_at.isoformat(timespec='seconds')}",
        f"Dashboard: {dashboard}",
        f"Oportunidades alertables: {len(items)}",
        "",
    ]

    if not items:
        lines.append("No hay oportunidades alertables para este corte.")
    else:
        for item in items:
            lines.extend(_text_opportunity(item))

    lines.extend(
        [
            "",
            "Modo seguro: SMTP no está habilitado.",
            "Los registros actuales pueden corresponder a datos demo/prototipo.",
        ]
    )
    return "\n".join(lines) + "\n"


def generate_html_body(
    alertable_opportunities: Iterable[dict[str, Any]],
    *,
    public_site_url: str | None = None,
    generated_at: datetime,
) -> str:
    """Create a simple professional HTML digest without sending it."""
    items = list(alertable_opportunities)
    dashboard_html = (
        f'<a href="{escape(public_site_url, quote=True)}">{escape(public_site_url)}</a>'
        if public_site_url
        else escape(LOCAL_DASHBOARD_LABEL)
    )
    cards = "".join(_html_opportunity(item) for item in items)
    if not cards:
        cards = '<p class="empty">No hay oportunidades alertables para este corte.</p>'

    return f"""<!DOCTYPE html>
<html lang="es">
  <head>
    <meta charset="UTF-8">
    <title>Radar Laboral Público Chile - Preview de alertas</title>
    <style>
      body {{ margin: 0; background: #f3f7f8; color: #163034; font-family: Arial, sans-serif; }}
      main {{ max-width: 760px; margin: 0 auto; padding: 28px 18px 44px; }}
      header {{ padding: 22px; border-radius: 14px; color: #fff; background: #05645d; }}
      h1 {{ margin: 0 0 8px; font-size: 24px; }}
      header p, .meta {{ margin: 5px 0; color: #d5f1ee; font-size: 13px; }}
      .notice {{ margin: 18px 0; padding: 12px; border-left: 4px solid #e7a72f; background: #fff8e8; }}
      article {{ margin: 14px 0; padding: 17px; border: 1px solid #d9e4e5; border-radius: 12px; background: #fff; }}
      h2 {{ margin: 0 0 7px; font-size: 17px; }}
      article p {{ margin: 6px 0; color: #60777a; font-size: 14px; line-height: 1.45; }}
      .score {{ color: #057a55; font-weight: bold; }}
      .reasons {{ color: #765415; }}
      footer {{ margin-top: 20px; color: #60777a; font-size: 12px; }}
    </style>
  </head>
  <body>
    <main>
      <header>
        <h1>Radar Laboral Público Chile</h1>
        <p>Vista previa de alertas por correo</p>
        <p class="meta">Generado: {escape(generated_at.isoformat(timespec="seconds"))}</p>
      </header>
      <p class="notice">Este archivo es un preview local. No se envió ningún correo.</p>
      <p>Dashboard: {dashboard_html}</p>
      <p>Oportunidades alertables: <strong>{len(items)}</strong></p>
      {cards}
      <footer>
        Modo seguro: SMTP no está habilitado. Los registros actuales pueden corresponder a datos demo/prototipo.
      </footer>
    </main>
  </body>
</html>
"""


def _alert_reasons(
    opportunity: dict[str, Any],
    alerts_config: dict[str, Any],
    reference_time: datetime,
) -> list[str]:
    reasons = []
    for rule in alerts_config.get("rules", []):
        if not rule.get("enabled", False):
            continue

        event = rule.get("event")
        if event == "new_opportunity" and _is_new(opportunity, reference_time):
            reasons.append("Nueva oportunidad")
        elif event == "high_match" and opportunity.get("match_score", 0) >= rule.get("minimum_match_score", 85):
            reasons.append("Alta coincidencia")
        elif event == "closing_soon":
            days = rule.get("days_before_closing")
            if isinstance(days, int) and _days_until_closing(opportunity, reference_time.date()) == days:
                reasons.append(f"Cierre en {days} día{'s' if days != 1 else ''}")
        elif event == "opportunity_updated" and _is_updated(opportunity):
            reasons.append("Convocatoria actualizada")
    return reasons


def _is_new(opportunity: dict[str, Any], reference_time: datetime) -> bool:
    detected_at = _parse_datetime(opportunity.get("detected_at"))
    if detected_at is None:
        return False
    if detected_at.tzinfo is None and reference_time.tzinfo is not None:
        detected_at = detected_at.replace(tzinfo=reference_time.tzinfo)
    return reference_time - timedelta(days=1) <= detected_at <= reference_time


def _is_updated(opportunity: dict[str, Any]) -> bool:
    if opportunity.get("is_updated") is True:
        return True
    updated_at = _parse_datetime(opportunity.get("updated_at"))
    detected_at = _parse_datetime(opportunity.get("detected_at"))
    return bool(updated_at and detected_at and updated_at > detected_at)


def _days_until_closing(opportunity: dict[str, Any], today: date) -> int | None:
    closing_date = _parse_date(opportunity.get("closing_date"))
    return (closing_date - today).days if closing_date else None


def _parse_date(value: object) -> date | None:
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _parse_datetime(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _text_opportunity(item: dict[str, Any]) -> list[str]:
    reasons = ", ".join(item.get("preview_alert_reasons", [])) or "-"
    return [
        f"- {item.get('title', 'Oportunidad sin título')}",
        f"  Institución: {item.get('institution', 'No especificada')}",
        f"  Ubicación: {item.get('region', 'No especificada')} / {item.get('commune', 'No especificada')}",
        f"  Cierre: {item.get('closing_date') or 'No especificado'}",
        f"  Coincidencia: {item.get('match_score', 0)}% ({item.get('match_level', 'Sin nivel')})",
        f"  Motivos: {reasons}",
        "",
    ]


def _html_opportunity(item: dict[str, Any]) -> str:
    reasons = ", ".join(item.get("preview_alert_reasons", [])) or "-"
    return f"""<article>
        <h2>{escape(str(item.get("title", "Oportunidad sin título")))}</h2>
        <p><strong>{escape(str(item.get("institution", "No especificada")))}</strong></p>
        <p>{escape(str(item.get("region", "No especificada")))} / {escape(str(item.get("commune", "No especificada")))}</p>
        <p>Cierre: {escape(str(item.get("closing_date") or "No especificado"))}</p>
        <p class="score">Coincidencia: {escape(str(item.get("match_score", 0)))}% ({escape(str(item.get("match_level", "Sin nivel")))})</p>
        <p class="reasons">Motivos: {escape(reasons)}</p>
      </article>
"""
