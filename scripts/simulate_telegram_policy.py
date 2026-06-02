"""Simulate the controlled Telegram policy without sending messages."""

from __future__ import annotations

import json
import sys

from build_telegram_preview import is_relevant_closing_soon, load_public_data
from send_telegram_alerts import DEFAULT_STATE, _load_state, evaluate_automatic_policy


def main() -> int:
    try:
        opportunities, summary, _ = load_public_data()
        state = _load_state(DEFAULT_STATE)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    new_high = [
        item
        for item in opportunities
        if item.get("is_new_since_last_run") is True
        and item.get("match_level") == "Alta"
        and item.get("human_feedback_action") != "false_positive"
    ]
    high = [item for item in opportunities if item.get("match_level") == "Alta"]
    closing_soon = [item for item in opportunities if is_relevant_closing_soon(item)]
    would_send, reason, included = evaluate_automatic_policy(opportunities, state)

    print("Simulación de política Telegram")
    print("------------------------------")
    print(f"Habría enviado Telegram: {'Sí' if would_send else 'No'}")
    print(f"Motivo: {reason}")
    print(f"Nuevas relevantes Alta: {len(new_high)}")
    print(f"Altas: {len(high)}")
    print(f"Cierres próximos relevantes: {len(closing_soon)}")
    print(f"Total capturado: {summary.get('total_opportunities', len(opportunities))}")
    print("Oportunidades que habría incluido:")
    if included:
        for item in included:
            print(f"- {item.get('match_score', 0)}% | {item.get('match_level')} | {item.get('title')} | {item.get('source_url') or 'Sin enlace directo'}")
    else:
        print("- Ninguna")
    print("\nSIMULACIÓN SOLAMENTE: no se envió Telegram y no se modificó el estado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
