"""Generate an isolated local dry-run capture for Gobierno Regional del Maule."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.sources.gore_maule import SOURCE_ID, fetch_gore_maule_candidates


CATALOG_PATH = ROOT / "data" / "source_candidates.json"
OUTPUT_DIR = ROOT / "output" / "sources" / "gore_maule"
OPPORTUNITIES_PATH = OUTPUT_DIR / "opportunities.json"
REPORT_PATH = OUTPUT_DIR / "report.md"


def _load_candidate() -> dict[str, Any]:
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"No fue posible leer {CATALOG_PATH}: {error}") from error
    sources = payload.get("sources") if isinstance(payload, dict) else None
    matches = [item for item in sources or [] if isinstance(item, dict) and item.get("id") == SOURCE_ID]
    if len(matches) != 1:
        raise ValueError(f"El catálogo debe contener exactamente una ficha {SOURCE_ID}.")
    discovery_url = matches[0].get("discovery_url")
    if not isinstance(discovery_url, str) or not discovery_url.strip():
        raise ValueError(f"La ficha {SOURCE_ID} no tiene discovery_url válida.")
    return matches[0]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _write_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)


def _write_report(candidate: dict[str, Any], diagnostics: dict[str, Any]) -> None:
    lines = [
        "# Dry-run GORE Maule",
        "",
        f"- URL configurada: {candidate['discovery_url']}",
        f"- Publicaciones detectadas: {diagnostics['publications_detected']}",
        f"- Detalles consultados: {diagnostics['details_checked']}",
        f"- Documentos detectados: {diagnostics['documents_detected']}",
        f"- Abiertos confirmados: {diagnostics['status_counts']['open_confirmed']}",
        f"- Cerrados confirmados: {diagnostics['status_counts']['closed']}",
        f"- Pendientes de revisión manual: {diagnostics['status_counts']['manual_review']}",
        f"- Errores HTTP de detalle: {len(diagnostics['detail_errors'])}",
        "",
        "## Alcance",
        "",
        "La captura consulta una sola página oficial configurada y únicamente sus",
        "detalles oficiales directos. No sigue paginación ni descarga documentos. Los",
        "estados se asignan con reglas conservadoras y la salida no se publica.",
    ]
    _write_text(REPORT_PATH, "\n".join(lines) + "\n")


def main() -> int:
    try:
        candidate = _load_candidate()
        opportunities, diagnostics = fetch_gore_maule_candidates(candidate["discovery_url"])
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        _write_json(OPPORTUNITIES_PATH, opportunities)
        _write_json(OUTPUT_DIR / "diagnostics.json", diagnostics)
        _write_report(candidate, diagnostics)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Dry-run GORE Maule")
    print("------------------")
    print(f"URL configurada: {candidate['discovery_url']}")
    print(f"Publicaciones detectadas: {diagnostics['publications_detected']}")
    print(f"Detalles consultados: {diagnostics['details_checked']}")
    print(f"Documentos detectados: {diagnostics['documents_detected']}")
    print(f"Abiertos confirmados: {diagnostics['status_counts']['open_confirmed']}")
    print(f"Cerrados confirmados: {diagnostics['status_counts']['closed']}")
    print(f"Pendientes de revisión manual: {diagnostics['status_counts']['manual_review']}")
    print(f"Errores HTTP de detalle: {len(diagnostics['detail_errors'])}")
    print(f"Salida local: {OPPORTUNITIES_PATH}")
    print("No se modificó public/data ni se enviaron alertas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
