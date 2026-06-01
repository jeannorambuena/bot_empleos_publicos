"""Inspect scoring distribution and suspicious discarded real opportunities."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PATH = ROOT / "public" / "data" / "opportunities.json"
RELEVANT_TERMS = (
    "redes",
    "informática",
    "tecnologías de la información",
    "plataforma",
    "servicios digitales",
    "desarrollador",
    "full stack",
    "soporte ti",
    "soporte informático",
    "infraestructura tecnológica",
    "gestión tecnológica",
    "sistemas",
    "servidores",
    "ciberseguridad",
    "cctv",
    "corrientes débiles",
    "bms",
    "compras públicas",
    "chilecompra",
    "mercado público",
    "organismos compradores",
    "contratación pública",
    "abastecimiento",
    "transparencia",
    "acceso a la información",
    "probidad",
    "gestión documental",
)


def _load_items() -> list[dict[str, Any]]:
    try:
        with PUBLIC_PATH.open("r", encoding="utf-8") as file:
            items = json.load(file)
    except FileNotFoundError:
        print(f"ERROR: No existe {PUBLIC_PATH}", file=sys.stderr)
        raise SystemExit(1)
    except json.JSONDecodeError as error:
        print(f"ERROR: JSON inválido en {PUBLIC_PATH}: {error}", file=sys.stderr)
        raise SystemExit(1)
    if not isinstance(items, list):
        print("ERROR: opportunities.json debe contener una lista.", file=sys.stderr)
        raise SystemExit(1)
    return items


def _print_items(title: str, items: list[dict[str, Any]]) -> None:
    print(f"\n{title}")
    print("-" * len(title))
    if not items:
        print("(sin resultados)")
        return
    for item in items:
        matched = ", ".join(item.get("matched_keywords", [])) or "-"
        print(f"{item.get('match_score', 0):>3} | {item.get('match_level', '-'):>10} | {item.get('title', '-')}")
        print(f"    keywords: {matched}")


def main() -> int:
    items = _load_items()
    levels = Counter(item.get("match_level", "Sin nivel") for item in items)
    keywords = Counter(
        keyword
        for item in items
        for keyword in item.get("matched_keywords", [])
    )
    discarded_with_matches = [
        item
        for item in items
        if item.get("match_level") == "Descartada" and item.get("matched_keywords")
    ]
    suspicious_discarded = [
        item
        for item in items
        if item.get("match_level") == "Descartada"
        and any(term in f"{item.get('title', '')} {item.get('description', '')}".lower() for term in RELEVANT_TERMS)
    ]

    print("Distribución por nivel")
    print("----------------------")
    for level in ("Alta", "Media", "Baja", "Descartada"):
        print(f"{level}: {levels[level]}")

    _print_items("Top 20 por score", sorted(items, key=lambda item: item.get("match_score", 0), reverse=True)[:20])
    _print_items(
        "Top 20 descartadas con palabras positivas",
        sorted(discarded_with_matches, key=lambda item: item.get("match_score", 0), reverse=True)[:20],
    )
    _print_items("Descartadas con términos relevantes para revisar", suspicious_discarded[:20])

    print("\nConteo de matched_keywords")
    print("--------------------------")
    for keyword, count in keywords.most_common():
        print(f"{keyword}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
