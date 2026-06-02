"""Validate that the static dashboard is ready for a future Pages deployment."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
REQUIRED_FILES = (
    PUBLIC / "index.html",
    PUBLIC / "assets" / "styles.css",
    PUBLIC / "assets" / "app.js",
    PUBLIC / "review.html",
    PUBLIC / "assets" / "review.css",
    PUBLIC / "assets" / "review.js",
    PUBLIC / "data" / "opportunities.json",
    PUBLIC / "data" / "summary.json",
    PUBLIC / "data" / "last_run.json",
    PUBLIC / "data" / "history.json",
)
JSON_FILES = REQUIRED_FILES[6:]
EXPECTED_SCORE_THRESHOLDS = (
    "if (score >= 80)",
    "if (score >= 60)",
    "if (score >= 35)",
    'return "discarded"',
)
EXPECTED_DATA_MODE_LABEL = "Captura local de Empleos Públicos"
EXPECTED_RELEVANCE_FILTER = (
    'id="relevance-filter"',
    '<option value="relevant" selected>Recomendadas para mi perfil</option>',
    '<option value="discarded">Descartadas</option>',
    '<option value="all">Todas las oportunidades públicas</option>',
)
EXPECTED_DEFAULT_RELEVANCE_LOGIC = (
    'const RELEVANT_LEVELS = new Set(["Alta", "Media", "Baja"])',
    'relevance === "relevant"',
    'relevanceFilter.value = "relevant"',
)


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON inválido en {path}: {error}") from error


def main() -> int:
    errors = []

    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"No existe: {path}")

    if not errors:
        for path in JSON_FILES:
            try:
                _load_json(path)
            except ValueError as error:
                errors.append(str(error))

        index_html = (PUBLIC / "index.html").read_text(encoding="utf-8")
        if "Radar Laboral Público Chile" not in index_html:
            errors.append("public/index.html no contiene el título esperado.")
        for expected_filter_text in EXPECTED_RELEVANCE_FILTER:
            if expected_filter_text not in index_html:
                errors.append(f"public/index.html no contiene: {expected_filter_text}")

        app_js = (PUBLIC / "assets" / "app.js").read_text(encoding="utf-8")
        for expected_threshold in EXPECTED_SCORE_THRESHOLDS:
            if expected_threshold not in app_js:
                errors.append(f"public/assets/app.js no contiene: {expected_threshold}")
        if EXPECTED_DATA_MODE_LABEL not in app_js:
            errors.append("public/assets/app.js no contiene la etiqueta para datos reales.")
        for expected_logic in EXPECTED_DEFAULT_RELEVANCE_LOGIC:
            if expected_logic not in app_js:
                errors.append(f"public/assets/app.js no contiene: {expected_logic}")

    if (ROOT / ".env").exists():
        errors.append("Existe .env en la raíz. No debe publicarse ni mantenerse en el repositorio.")

    if (PUBLIC / "output").exists():
        errors.append("public/output existe. Los artefactos locales no deben publicarse con el dashboard.")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("OK: dashboard preparado para una futura publicación en GitHub Pages.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
