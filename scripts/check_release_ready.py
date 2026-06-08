"""Run the final local release checks for the Radar Laboral Publico Chile MVP."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.sources.sanitization import sensitive_personal_data_reasons


CHECKS = (
    "check_public_data.py",
    "check_pages_ready.py",
    "check_source_candidates.py",
    "check_sources_config.py",
    "check_source_sanitization.py",
    "check_priority_sources.py",
    "simulate_telegram_policy.py",
)
NEW_SOURCE_NAMES = {
    "Municipalidad de Curico",
    "Municipalidad de Curicó",
    "Municipalidad de Molina",
    "Municipalidad de Rauco",
    "Gobierno Regional del Maule",
    "Municipalidad de Talca",
    "SLEP Colchagua",
    "SLEP Los Cerezos",
}
PUBLICABLE_FIELDS = ("title", "description", "evidence", "status_reason", "manual_review_reason")
RANCAGUA_SOURCE = "Municipalidad de Rancagua"


def _run(script: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        cwd=ROOT,
    )
    return [] if result.returncode == 0 else [f"{script} falló con código {result.returncode}."]


def _load_public_opportunities() -> list[dict[str, Any]]:
    path = ROOT / "public" / "data" / "opportunities.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("public/data/opportunities.json debe contener una lista.")
    return payload


def _public_release_errors(opportunities: list[dict[str, Any]]) -> list[str]:
    errors = []
    for index, item in enumerate(opportunities):
        label = f"public.opportunities[{index}]"
        if item.get("offer_scope") == "external_private":
            errors.append(f"{label}: no se puede publicar external_private.")
        if item.get("source") in NEW_SOURCE_NAMES and item.get("manual_review") is True:
            errors.append(f"{label}: no se puede publicar manual_review de una fuente nueva.")
        if item.get("source") == RANCAGUA_SOURCE:
            if item.get("status") != "open_confirmed":
                errors.append(f"{label}: Rancagua publicada debe ser open_confirmed.")
            if item.get("offer_scope") != "municipal":
                errors.append(f"{label}: Rancagua publicada debe ser municipal.")
            if item.get("implementation_status") != "published_controlled":
                errors.append(f"{label}: Rancagua publicada debe ser published_controlled.")
        for field in PUBLICABLE_FIELDS:
            value = item.get(field)
            values = value if isinstance(value, list) else [value]
            for candidate in values:
                if isinstance(candidate, str) and sensitive_personal_data_reasons(candidate):
                    errors.append(f"{label}.{field}: contiene datos personales visibles.")
        for document in item.get("document_urls") or []:
            if isinstance(document, dict) and sensitive_personal_data_reasons(document.get("name")):
                errors.append(f"{label}.document_urls[].name: contiene datos personales visibles.")
    return errors


def main() -> int:
    errors = []
    for script in CHECKS:
        if (ROOT / "scripts" / script).exists():
            errors.extend(_run(script))
    errors.extend(_run("build_telegram_preview.py"))
    if (ROOT / "scripts" / "check_telegram_preview.py").exists():
        errors.extend(_run("check_telegram_preview.py"))
    try:
        errors.extend(_public_release_errors(_load_public_opportunities()))
    except (OSError, json.JSONDecodeError, ValueError) as error:
        errors.append(f"No fue posible validar oportunidades públicas: {error}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: release MVP listo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
