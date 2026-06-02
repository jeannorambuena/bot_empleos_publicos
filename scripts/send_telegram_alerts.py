"""Send Telegram alerts in explicit manual mode or controlled automatic mode."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from build_telegram_preview import (
    DASHBOARD_URL,
    MAX_RECOMMENDATIONS,
    ROOT,
    _format_recommendation,
    load_public_data,
)


PREVIEW = ROOT / "output" / "telegram" / "telegram-preview.txt"
DEFAULT_STATE = ROOT / "public" / "data" / "telegram_alert_state.json"
AUTOMATION_TIMEZONE = timezone.utc


def _masked_chat_id(chat_id: str) -> str:
    return f"{chat_id[:2]}***{chat_id[-2:]}" if len(chat_id) > 4 else "****"


def _load_state(path: Path) -> dict[str, Any]:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"No fue posible leer estado Telegram {path}: {error}") from error
    if not isinstance(state, dict):
        raise ValueError("El estado Telegram debe ser un objeto JSON.")
    if not isinstance(state.get("sent_opportunity_ids"), list):
        raise ValueError("El estado Telegram requiere sent_opportunity_ids como lista.")
    return state


def _write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _same_day(timestamp: Any, now: datetime) -> bool:
    if not timestamp:
        return False
    try:
        return datetime.fromisoformat(str(timestamp)).astimezone(AUTOMATION_TIMEZONE).date() == now.astimezone(AUTOMATION_TIMEZONE).date()
    except ValueError:
        return False


def is_automatic_candidate(item: dict[str, Any], sent_ids: set[str]) -> bool:
    """Return whether an opportunity may trigger a controlled automatic alert."""
    item_id = str(item.get("id") or "")
    is_trigger = item.get("is_new_since_last_run") is True or item.get("urgency") == "proximo"
    return (
        bool(item_id)
        and item_id not in sent_ids
        and item.get("match_level") == "Alta"
        and item.get("human_feedback_action") != "false_positive"
        and is_trigger
    )


def evaluate_automatic_policy(
    opportunities: list[dict[str, Any]],
    state: dict[str, Any],
    *,
    now: datetime | None = None,
) -> tuple[bool, str, list[dict[str, Any]]]:
    """Evaluate rate limit, duplicates and relevance without sending anything."""
    current_time = now or datetime.now(AUTOMATION_TIMEZONE)
    if _same_day(state.get("last_auto_sent_at"), current_time):
        return False, "Ya existe un envío automático registrado para el día de hoy.", []

    sent_ids = {str(item_id) for item_id in state.get("sent_opportunity_ids", [])}
    candidates = [item for item in opportunities if is_automatic_candidate(item, sent_ids)]
    candidates.sort(
        key=lambda item: (
            item.get("is_new_since_last_run") is not True,
            item.get("urgency") != "proximo",
            -int(item.get("match_score", 0)),
            item.get("closing_date") or "9999-12-31",
        )
    )
    included = candidates[:MAX_RECOMMENDATIONS]
    if not included:
        return False, "No hay oportunidades Alta nuevas o con cierre próximo pendientes de envío.", []
    if any(item.get("is_new_since_last_run") is True for item in included):
        return True, "Hay oportunidades Alta nuevas pendientes de envío.", included
    return True, "Hay oportunidades Alta con cierre próximo pendientes de envío.", included


def _automatic_message(opportunities: list[dict[str, Any]], reason: str, generated_at: str) -> str:
    lines = [
        "Radar Laboral Público Chile",
        "Alerta automática controlada",
        f"Fecha/hora: {generated_at}",
        f"Motivo: {reason}",
        "",
        "Recomendadas:",
    ]
    for index, item in enumerate(opportunities, start=1):
        lines.extend(_format_recommendation(index, item))
    lines.extend(["", f"Dashboard: {DASHBOARD_URL}", "", "Envío automático limitado: máximo una alerta diaria."])
    return "\n".join(lines) + "\n"


def _send_message(message: str, token: str, chat_id: str) -> int:
    data = urlencode({"chat_id": chat_id, "text": message, "disable_web_page_preview": "true"}).encode("utf-8")
    request = Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"ERROR: Telegram no confirmó el envío para chat {_masked_chat_id(chat_id)}: {error}", file=sys.stderr)
        return 1
    if payload.get("ok") is not True:
        print(f"ERROR: Telegram rechazó el envío para chat {_masked_chat_id(chat_id)}.", file=sys.stderr)
        return 1
    print(f"Telegram enviado correctamente al chat {_masked_chat_id(chat_id)}.")
    return 0


def _run_automatic(*, send: bool, state_path: Path) -> int:
    try:
        opportunities, _, last_run = load_public_data()
        state = _load_state(state_path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: política automática bloqueada: {error}", file=sys.stderr)
        return 1

    now = datetime.now(AUTOMATION_TIMEZONE)
    would_send, reason, included = evaluate_automatic_policy(opportunities, state, now=now)
    print("Política automática Telegram")
    print("---------------------------")
    print(f"Modo: {'REAL' if send else 'DRY-RUN'}")
    print(f"Corresponde enviar: {'Sí' if would_send else 'No'}")
    print(f"Motivo: {reason}")
    print(f"Oportunidades incluidas: {len(included)}")
    for item in included:
        print(f"- {item.get('id')} | {item.get('match_score', 0)}% | {item.get('title')}")

    if not would_send:
        print("Sin envío: la política no habilitó una alerta.")
        return 0
    if not send:
        print("DRY-RUN SOLAMENTE: no se llamó a Telegram y no se modificó el estado.")
        return 0

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("ERROR: envío automático bloqueado: faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID.", file=sys.stderr)
        return 1

    generated_at = last_run.get("finished_at") or now.isoformat(timespec="seconds")
    result = _send_message(_automatic_message(included, reason, str(generated_at)), token, chat_id)
    if result:
        return result

    state.update(
        {
            "last_auto_sent_at": now.isoformat(timespec="seconds"),
            "sent_opportunity_ids": sorted(
                {str(item_id) for item_id in state.get("sent_opportunity_ids", [])}
                | {str(item.get("id")) for item in included}
            ),
            "last_mode": "automatic",
            "last_reason": reason,
        }
    )
    _write_state(state_path, state)
    print(f"Estado anti-duplicados actualizado: {state_path}")
    return 0


def _run_manual(*, send: bool) -> int:
    if not send:
        print("Envío bloqueado: falta confirmación explícita --send.")
        return 0
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Envío bloqueado: configura TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID.")
        return 0
    if not PREVIEW.exists():
        print("ERROR: primero genera output/telegram/telegram-preview.txt.", file=sys.stderr)
        return 1
    return _send_message(PREVIEW.read_text(encoding="utf-8"), token, chat_id)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--send", action="store_true", help="Confirmar envío real por Telegram.")
    parser.add_argument("--automatic", action="store_true", help="Evaluar política automática controlada.")
    parser.add_argument("--dry-run", action="store_true", help="Forzar simulación sin llamar a Telegram.")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE, help="Ruta del estado anti-duplicados.")
    args = parser.parse_args()

    if args.send and args.dry_run:
        parser.error("--send y --dry-run no pueden usarse juntos.")
    if args.automatic:
        return _run_automatic(send=args.send and not args.dry_run, state_path=args.state)
    if args.dry_run:
        print("DRY-RUN manual: no se llamó a Telegram.")
        return 0
    return _run_manual(send=args.send)


if __name__ == "__main__":
    raise SystemExit(main())
