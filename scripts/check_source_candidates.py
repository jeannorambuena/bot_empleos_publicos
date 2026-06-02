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
    "region",
    "commune",
    "geo_priority",
    "mobility_rule",
    "rm_policy",
    "profile_fit",
    "source_quality",
    "privacy_risk",
    "publishability",
    "priority_tier",
    "next_action",
    "rationale",
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
    "directores_para_chile",
}
REGION_SCOPES = {"local", "regional", "national_filterable"}
PRIORITIES = {"high", "medium", "low"}
DIFFICULTIES = {"low", "medium", "high"}
STATUSES = {"candidate", "not_implemented"}
TRISTATE = {True, False, "unknown"}
SECRET_MARKERS = ("token", "secret", "password", "api_key", "chat_id")
GEO_PRIORITIES = {"local_or_near", "regional_possible", "rm_high_salary_or_strong_ti_only", "out_of_scope"}
MOBILITY_RULES = {
    "local_preferred",
    "relocation_for_strong_fit",
    "rm_strong_ti_salary_or_hybrid_only",
    "territorial_filter_only",
    "out_of_scope",
}
RM_POLICIES = {"not_applicable", "strong_ti_salary_or_hybrid_only"}
PROFILE_FITS = {"ti_direct", "ti_adjacent", "administrative_public", "generic_low_fit", "unknown"}
SOURCE_QUALITIES = {"proven", "readable", "unknown", "weak"}
PRIVACY_RISKS = {"low", "medium", "high"}
PUBLISHABILITY = {
    "active_published",
    "tested_publishable_controlled",
    "dry_run_only",
    "manual_review_only",
    "candidate_only",
    "blocked",
}
PRIORITY_TIERS = {"P0", "P1", "P2", "P3", "P4"}
NEXT_ACTIONS = {
    "keep_active",
    "keep_monitoring",
    "evaluate_next",
    "dry_run_candidate",
    "manual_review_only",
    "defer",
    "block",
}
CONSERVATIVE_STATES = {
    "municipalidad-curico": {"dry_run_only"},
    "municipalidad-molina": {"dry_run_only", "manual_review_only"},
    "gore-maule": {"dry_run_only", "manual_review_only"},
}


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
            if source.get("geo_priority") not in GEO_PRIORITIES:
                errors.append(f"{label}.geo_priority no permitido.")
            if source.get("mobility_rule") not in MOBILITY_RULES:
                errors.append(f"{label}.mobility_rule no permitido.")
            if source.get("rm_policy") not in RM_POLICIES:
                errors.append(f"{label}.rm_policy no permitido.")
            if source.get("profile_fit") not in PROFILE_FITS:
                errors.append(f"{label}.profile_fit no permitido.")
            if source.get("source_quality") not in SOURCE_QUALITIES:
                errors.append(f"{label}.source_quality no permitido.")
            if source.get("privacy_risk") not in PRIVACY_RISKS:
                errors.append(f"{label}.privacy_risk no permitido.")
            if source.get("publishability") not in PUBLISHABILITY:
                errors.append(f"{label}.publishability no permitido.")
            if source.get("priority_tier") not in PRIORITY_TIERS:
                errors.append(f"{label}.priority_tier no permitido.")
            if source.get("next_action") not in NEXT_ACTIONS:
                errors.append(f"{label}.next_action no permitido.")
            if not isinstance(source.get("region"), str) or not str(source.get("region") or "").strip():
                errors.append(f"{label}.region debe ser texto no vacío.")
            if not isinstance(source.get("commune"), str) or not str(source.get("commune") or "").strip():
                errors.append(f"{label}.commune debe ser texto no vacío.")
            if not isinstance(source.get("rationale"), str) or not str(source.get("rationale") or "").strip():
                errors.append(f"{label}.rationale debe explicar la prioridad.")

            is_rm = "metropolitana" in (regions or [])
            if is_rm and source.get("rm_policy") != "strong_ti_salary_or_hybrid_only":
                errors.append(f"{label}: RM requiere política explícita de TI fuerte, sueldo o modalidad conveniente.")
            if is_rm and source.get("priority_tier") == "P0":
                rationale = str(source.get("rationale") or "").lower()
                if not any(marker in rationale for marker in ("ti fuerte", "sueldo", "hibrida", "remota")):
                    errors.append(f"{label}: RM no puede quedar P0 sin justificación TI, sueldo o modalidad.")
            if source.get("privacy_risk") == "high" and source.get("next_action") == "keep_active":
                errors.append(f"{label}: privacy_risk high no permite keep_active.")
            if source.get("publishability") == "manual_review_only" and source.get("next_action") == "keep_active":
                errors.append(f"{label}: manual_review_only no puede marcarse como fuente activa.")
            if source.get("priority_tier") == "P0" and source.get("publishability") not in {
                "active_published",
                "tested_publishable_controlled",
            }:
                errors.append(f"{label}: P0 se reserva para fuentes activas o publicadas controladamente.")

            source_id = source.get("id")
            if source_id == "municipalidad-rancagua":
                if source.get("publishability") != "tested_publishable_controlled" or source.get("next_action") != "keep_monitoring":
                    errors.append(f"{label}: Rancagua debe conservar publicación controlada y monitoreo.")
            if source_id in CONSERVATIVE_STATES and source.get("publishability") not in CONSERVATIVE_STATES[source_id]:
                errors.append(f"{label}: {source_id} debe conservar estado dry-run o revisión manual.")
            if source_id == "gore-maule" and source.get("privacy_risk") != "high":
                errors.append(f"{label}: GORE Maule debe conservar advertencia de privacidad histórica.")
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
