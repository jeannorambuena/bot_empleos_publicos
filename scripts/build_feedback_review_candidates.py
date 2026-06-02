"""Build grouped candidates for the next human feedback review cycle."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PATH = ROOT / "public" / "data" / "opportunities.json"
OUTPUT_PATH = ROOT / "output" / "feedback-review-candidates.md"
RELEVANT_LEVELS = {"Alta", "Media", "Baja"}
TECH_TERMS = (
    "informática",
    "informatica",
    "tecnología",
    "tecnologia",
    "soporte",
    "redes",
    "sistemas",
    "plataforma",
    "servidor",
    "ciberseguridad",
    "desarrollador",
    "digital",
    "cctv",
    "bms",
)


def _load_opportunities() -> list[dict[str, Any]]:
    try:
        payload = json.loads(PUBLIC_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"No fue posible leer {PUBLIC_PATH}: {error}") from error
    if not isinstance(payload, list):
        raise ValueError("opportunities.json debe contener una lista.")
    return payload


def _contains_ambiguous_reason(item: dict[str, Any]) -> bool:
    return any("términos ambiguos" in str(reason).lower() for reason in item.get("alert_reasons", []))


def _contains_tech_term(item: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(item.get("title") or ""),
            str(item.get("description") or ""),
            " ".join(str(keyword) for keyword in item.get("matched_keywords", [])),
        ]
    ).lower()
    return any(term in text for term in TECH_TERMS)


def _groups() -> tuple[tuple[str, str, Callable[[dict[str, Any]], bool]], ...]:
    return (
        ("Nuevas altas", "new_high", lambda item: item.get("is_new_since_last_run") is True and item.get("match_level") == "Alta"),
        ("Oportunidades Alta no revisadas", "high_unreviewed", lambda item: item.get("match_level") == "Alta" and item.get("human_reviewed") is not True),
        ("Cierres próximos relevantes no revisados", "closing_unreviewed", lambda item: item.get("urgency") == "proximo" and item.get("match_level") in RELEVANT_LEVELS and item.get("human_reviewed") is not True),
        ("Oportunidades ambiguas con score medio/alto", "ambiguous_medium_high", lambda item: item.get("match_score", 0) >= 60 and _contains_ambiguous_reason(item)),
        ("Oportunidades marcadas como review", "manual_review", lambda item: item.get("manual_review") is True or item.get("human_feedback_action") == "review"),
        ("Descartadas con palabras TI o tecnología", "discarded_tech", lambda item: item.get("match_level") == "Descartada" and _contains_tech_term(item)),
    )


def _format_item(item: dict[str, Any]) -> str:
    return (
        f"- `{item.get('id', '-')}` | {item.get('match_score', 0)}% {item.get('match_level', '-')} | "
        f"{item.get('title', 'Sin título')} | {item.get('institution', 'No especificada')} | "
        f"cierre: {item.get('closing_date') or 'No especificado'}"
    )


def main() -> int:
    try:
        opportunities = _load_opportunities()
    except ValueError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    lines = ["# Candidatos para revisión humana", ""]
    print("Candidatos para el próximo ciclo de feedback")
    print("------------------------------------------")
    for title, key, predicate in _groups():
        candidates = sorted(
            (item for item in opportunities if predicate(item)),
            key=lambda item: (-int(item.get("match_score", 0)), str(item.get("title", ""))),
        )
        print(f"{key}: {len(candidates)}")
        lines.extend([f"## {title}", "", f"Total: {len(candidates)}", ""])
        lines.extend(_format_item(item) for item in candidates)
        if not candidates:
            lines.append("- Sin candidatos.")
        lines.append("")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nArchivo local generado: {OUTPUT_PATH}")
    print("No modifica scoring ni feedback aplicado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
