"""Simulate the controlled Telegram policy without sending messages."""

from __future__ import annotations

import json
import sys

from build_telegram_preview import is_profile_relevant, is_relevant_closing_soon, load_public_data
from send_telegram_alerts import DEFAULT_STATE, _load_state, evaluate_automatic_policy, is_automatic_candidate


def _regression_errors() -> list[str]:
    base = {
        "id": "regression-ti",
        "match_level": "Alta",
        "is_new_since_last_run": True,
        "urgency": "normal",
        "manual_review": False,
        "offer_scope": "public_institution",
        "tags": ["ti"],
    }
    errors = []
    if evaluate_automatic_policy([base], {"sent_opportunity_ids": []})[0] is not True:
        errors.append("una oportunidad Alta nueva y segura debe habilitar alerta.")
    if evaluate_automatic_policy([], {"sent_opportunity_ids": []})[1] != "No hay oportunidades nuevas relevantes para el perfil.":
        errors.append("la ausencia de novedades debe entregar un motivo claro.")
    if evaluate_automatic_policy([base], {"sent_opportunity_ids": ["regression-ti"]})[1] != "No hay oportunidades relevantes no notificadas.":
        errors.append("un ID ya notificado no debe reenviarse.")
    blocked = (
        {**base, "id": "discarded", "match_level": "Descartada"},
        {**base, "id": "manual", "manual_review": True},
        {**base, "id": "private", "offer_scope": "external_private"},
        {**base, "id": "omil", "tags": ["omil"]},
    )
    if any(is_automatic_candidate(item, set()) for item in blocked):
        errors.append("descartadas, manual_review, external_private y OMIL deben bloquearse.")
    return errors


def main() -> int:
    regression_errors = _regression_errors()
    if regression_errors:
        for error in regression_errors:
            print(f"ERROR: regresion Telegram: {error}", file=sys.stderr)
        return 1
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
        and is_profile_relevant(item, levels={"Alta"})
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
    print("OK: regresiones Telegram verificadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
