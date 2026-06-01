"""Generate local iCalendar previews for job application reminders."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable


PRODUCT_ID = "-//Radar Laboral Publico Chile//Calendar Preview//ES"
DEFAULT_ALARM_TRIGGER = "-PT9H"


def select_calendar_opportunities(
    opportunities: Iterable[dict[str, Any]],
    *,
    reference_date: date,
    closing_soon_days: int = 7,
) -> list[dict[str, Any]]:
    """Select active, non-discarded opportunities that deserve reminders."""
    selected = []
    for opportunity in opportunities:
        if opportunity.get("status") != "vigente":
            continue
        if opportunity.get("match_level") == "Descartada":
            continue

        closing_date = _parse_date(opportunity.get("closing_date"))
        is_high_match = opportunity.get("match_level") == "Alta"
        is_closing_soon = bool(
            closing_date
            and reference_date <= closing_date <= reference_date + timedelta(days=closing_soon_days)
        )
        if is_high_match or is_closing_soon:
            selected.append(dict(opportunity))

    selected.sort(
        key=lambda item: (
            item.get("closing_date") is None,
            item.get("closing_date") or "9999-12-31",
            -int(item.get("match_score", 0)),
        )
    )
    return selected


def generate_calendar(
    opportunities: Iterable[dict[str, Any]],
    *,
    generated_at: datetime,
) -> tuple[str, dict[str, int]]:
    """Build a complete RFC 5545-style calendar preview and summary counts."""
    events = []
    decision_events = 0
    closing_events = 0

    for opportunity in opportunities:
        closing_date = _parse_date(opportunity.get("closing_date"))
        if closing_date is None:
            continue

        decision_date = _decision_date(closing_date, generated_at.date())
        events.append(
            generate_event(
                opportunity,
                event_kind="decision",
                event_date=decision_date,
                generated_at=generated_at,
                alarm_trigger=DEFAULT_ALARM_TRIGGER,
            )
        )
        decision_events += 1

        events.append(
            generate_event(
                opportunity,
                event_kind="closing",
                event_date=closing_date,
                generated_at=generated_at,
                alarm_trigger=DEFAULT_ALARM_TRIGGER,
            )
        )
        closing_events += 1

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODUCT_ID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Radar Laboral Público Chile - Preview",
        *events,
        "END:VCALENDAR",
    ]
    summary = {
        "total_events": len(events),
        "decision_events": decision_events,
        "closing_events": closing_events,
    }
    return _join_ics_lines(lines), summary


def generate_event(
    opportunity: dict[str, Any],
    *,
    event_kind: str,
    event_date: date,
    generated_at: datetime,
    alarm_trigger: str | None = None,
) -> str:
    """Build one all-day VEVENT with an optional local display alarm."""
    if event_kind not in {"decision", "closing"}:
        raise ValueError(f"Tipo de evento no soportado: {event_kind}")

    prefix = "Decidir postulación" if event_kind == "decision" else "Cierre de convocatoria"
    uid = stable_event_uid(opportunity, event_kind)
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{_utc_stamp(generated_at)}",
        f"DTSTART;VALUE=DATE:{event_date.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{(event_date + timedelta(days=1)).strftime('%Y%m%d')}",
        f"SUMMARY:{_escape_ics(f'{prefix}: {opportunity.get("title", "Oportunidad sin título")}')}",
        f"DESCRIPTION:{_escape_ics(_description(opportunity))}",
    ]

    source_url = opportunity.get("source_url")
    if source_url and opportunity.get("is_demo") is not True:
        lines.append(f"URL:{_escape_ics(str(source_url))}")

    if alarm_trigger:
        lines.extend(
            [
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                f"TRIGGER:{alarm_trigger}",
                f"DESCRIPTION:{_escape_ics(prefix)}",
                "END:VALARM",
            ]
        )

    lines.append("END:VEVENT")
    return _join_ics_lines(lines).rstrip("\r\n")


def stable_event_uid(opportunity: dict[str, Any], event_kind: str) -> str:
    """Return a deterministic UID for repeatable imports."""
    raw_id = str(opportunity.get("id") or opportunity.get("title") or "opportunity")
    digest = hashlib.sha256(f"{raw_id}|{event_kind}".encode("utf-8")).hexdigest()[:20]
    return f"{event_kind}-{digest}@radar-laboral-publico-chile"


def _description(opportunity: dict[str, Any]) -> str:
    reasons = ", ".join(str(reason) for reason in opportunity.get("alert_reasons", [])) or "Sin motivos informados"
    fields = [
        f"Cargo: {opportunity.get('title', 'No especificado')}",
        f"Institución: {opportunity.get('institution', 'No especificada')}",
        f"Fuente: {opportunity.get('source', 'No especificada')}",
        f"Región: {opportunity.get('region', 'No especificada')}",
        f"Comuna: {opportunity.get('commune', 'No especificada')}",
        f"Coincidencia: {opportunity.get('match_score', 0)}%",
        f"Motivos: {reasons}",
    ]
    source_url = opportunity.get("source_url")
    if source_url and opportunity.get("is_demo") is not True:
        fields.append(f"URL: {source_url}")
    return "\n".join(fields)


def _decision_date(closing_date: date, reference_date: date) -> date:
    """Place the decision reminder three days before closing when possible."""
    return max(reference_date, closing_date - timedelta(days=3))


def _parse_date(value: object) -> date | None:
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _utc_stamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _escape_ics(value: object) -> str:
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
        .replace("\n", "\\n")
        .replace(";", "\\;")
        .replace(",", "\\,")
    )


def _join_ics_lines(lines: Iterable[str]) -> str:
    logical_lines = []
    for line in lines:
        logical_lines.extend(str(line).splitlines())
    return "\r\n".join(
        folded_line
        for logical_line in logical_lines
        for folded_line in _fold_ics_line(logical_line)
    ) + "\r\n"


def _fold_ics_line(line: str, limit: int = 75) -> list[str]:
    """Fold content lines by UTF-8 octets for broad calendar compatibility."""
    if len(line.encode("utf-8")) <= limit:
        return [line]

    folded = []
    remaining = line
    first_line = True
    while remaining:
        prefix = "" if first_line else " "
        available = limit - len(prefix.encode("utf-8"))
        end = 0
        used = 0
        for char in remaining:
            char_size = len(char.encode("utf-8"))
            if used + char_size > available:
                break
            used += char_size
            end += 1
        if end == 0:
            end = 1
        folded.append(prefix + remaining[:end])
        remaining = remaining[end:]
        first_line = False
    return folded
