"""Validate the scoped catalog of future public source candidates."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "source_candidates.json"
FIELDS = {
    "id",
    "name",
    "category",
    "official_url",
    "discovery_url",
    "source_type",
    "opportunity_type",
    "region_scope",
    "target_regions",
    "passes_through_empleos_publicos",
    "requires_login",
    "structured_data",
    "technical_difficulty",
    "priority",
    "implementation_status",
    "notes",
}
TARGET_REGIONS = {"metropolitana", "ohiggins", "maule", "nacional_filtrable"}
CATEGORIES = {
    "slep",
    "municipalidad",
    "gobierno_regional",
    "servicio_regional",
    "universidad_estatal",
    "poder_judicial",
    "alta_direccion_publica",
    "transparencia_activa",
    "chilecompra_mercado_publico",
    "empleos_publicos_complementario",
}
REGION_SCOPES = {"local", "regional", "national_filterable"}
PRIORITIES = {"high", "medium", "low"}
DIFFICULTIES = {"low", "medium", "high"}
STATUSES = {"candidate", "not_implemented"}
TRISTATE = {True, False, "unknown"}
SECRET_MARKERS = ("token", "secret", "password", "api_key", "chat_id")


def _valid_url(value: Any) -> bool:
    return isinstance(value, str) and urlparse(value).scheme in {"http", "https"} and bool(urlparse(value).netloc)


def main() -> int:
    try:
        payload = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    sources = payload.get("sources") if isinstance(payload, dict) else None
    errors: list[str] = []
    if not isinstance(sources, list) or not sources:
        errors.append("source_candidates.json debe contener una lista sources no vacía.")
    else:
        ids: list[Any] = []
        for index, source in enumerate(sources):
            label = f"sources[{index}]"
            if not isinstance(source, dict):
                errors.append(f"{label} debe ser objeto.")
                continue
            missing = FIELDS - source.keys()
            if missing:
                errors.append(f"{label} sin campos: {', '.join(sorted(missing))}")
            ids.append(source.get("id"))
            if not _valid_url(source.get("official_url")):
                errors.append(f"{label}.official_url debe ser HTTP(S) no vacía.")
            if not _valid_url(source.get("discovery_url")):
                errors.append(f"{label}.discovery_url debe ser HTTP(S) no vacía.")
            if source.get("category") not in CATEGORIES:
                errors.append(f"{label}.category no permitida.")
            if source.get("region_scope") not in REGION_SCOPES:
                errors.append(f"{label}.region_scope no permitido.")
            regions = source.get("target_regions")
            if not isinstance(regions, list) or not regions:
                errors.append(f"{label}.target_regions debe ser lista no vacía.")
            elif set(regions) - TARGET_REGIONS:
                errors.append(f"{label}.target_regions contiene regiones fuera del alcance.")
            if source.get("priority") not in PRIORITIES:
                errors.append(f"{label}.priority no permitida.")
            if source.get("technical_difficulty") not in DIFFICULTIES:
                errors.append(f"{label}.technical_difficulty no permitida.")
            if source.get("implementation_status") not in STATUSES:
                errors.append(f"{label}.implementation_status no permitido.")
            for field in ("passes_through_empleos_publicos", "requires_login", "structured_data"):
                if source.get(field) not in TRISTATE:
                    errors.append(f"{label}.{field} debe ser booleano o unknown.")
        if len(ids) != len(set(ids)):
            errors.append("Los ids de fuentes candidatas deben ser únicos.")

    serialized = json.dumps(payload, ensure_ascii=False).lower()
    if any(marker in serialized for marker in SECRET_MARKERS):
        errors.append("El catálogo contiene un marcador asociado a secretos.")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: catálogo territorial válido ({len(sources)} fuentes candidatas).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
