"""Simulate a future Telegram policy without sending messages."""

from __future__ import annotations

import json
import sys

from build_telegram_preview import (
    ROOT,
    is_high_closing_soon,
    is_new_relevant,
    is_relevant_closing_soon,
    load_public_data,
    select_recommended,
)


def main() -> int:
    try:
        opportunities, summary, _ = load_public_data()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    new_relevant = [item for item in opportunities if is_new_relevant(item)]
    high = [item for item in opportunities if item.get("match_level") == "Alta"]
    closing_soon = [item for item in opportunities if is_relevant_closing_soon(item)]
    high_closing_soon = [item for item in opportunities if is_high_closing_soon(item)]
    would_send = bool(new_relevant or high_closing_soon)
    if new_relevant:
        reason = "Hay oportunidades nuevas relevantes."
    elif high_closing_soon:
        reason = "Hay oportunidades de coincidencia Alta con cierre próximo."
    else:
        reason = "No hay nuevas relevantes ni oportunidades Alta con cierre próximo."

    included = select_recommended(opportunities) if would_send else []
    print("Simulación de política Telegram")
    print("------------------------------")
    print(f"Habría enviado Telegram: {'Sí' if would_send else 'No'}")
    print(f"Motivo: {reason}")
    print(f"Nuevas relevantes: {len(new_relevant)}")
    print(f"Altas: {len(high)}")
    print(f"Cierres próximos relevantes: {len(closing_soon)}")
    print(f"Total capturado: {summary.get('total_opportunities', len(opportunities))}")
    print("Oportunidades que habría incluido:")
    if included:
        for item in included:
            print(f"- {item.get('match_score', 0)}% | {item.get('match_level')} | {item.get('title')} | {item.get('source_url') or 'Sin enlace directo'}")
    else:
        print("- Ninguna")
    print("\nSIMULACIÓN SOLAMENTE: no se envió Telegram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
