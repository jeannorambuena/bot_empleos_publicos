"""Generate an isolated local dry-run capture for Municipalidad de Romeral."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.sources.romeral import DEFAULT_DISCOVERY_URL, SOURCE_ID, fetch_romeral_candidates


CATALOG_PATH = ROOT / "data" / "source_candidates.json"
OUTPUT_DIR = ROOT / "output" / "sources" / "romeral"
OPPORTUNITIES_PATH = OUTPUT_DIR / "opportunities.json"
DIAGNOSTICS_PATH = OUTPUT_DIR / "diagnostics.json"
STATE_PATH = OUTPUT_DIR / "monitor_state.json"
REPORT_PATH = OUTPUT_DIR / "report.md"


def _load_candidate() -> dict[str, Any]:
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"No fue posible leer {CATALOG_PATH}: {error}") from error
    sources = payload.get("sources") if isinstance(payload, dict) else None
    matches = [item for item in sources or [] if isinstance(item, dict) and item.get("id") == SOURCE_ID]
    if len(matches) != 1:
        raise ValueError(f"El catalogo debe contener exactamente una ficha {SOURCE_ID}.")
    return matches[0]


def _load_previous_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"No fue posible leer estado Romeral {path}: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("El estado Romeral debe ser un objeto JSON.")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_report(candidate: dict[str, Any], diagnostics: dict[str, Any]) -> None:
    counts = diagnostics["status_counts"]
    lines = [
        "# Dry-run Municipalidad de Romeral",
        "",
        f"- URL configurada: {candidate.get('discovery_url') or DEFAULT_DISCOVERY_URL}",
        f"- Paginas revisadas: {len(diagnostics['pages_checked'])}",
        f"- Hash normalizado: `{diagnostics['listing_hash']}`",
        f"- Cambio detectado: {'si' if diagnostics['source_change_detected'] else 'no'}",
        f"- Publicaciones detectadas: {diagnostics['publications_detected']}",
        f"- Documentos detectados: {diagnostics['documents_detected']}",
        f"- Enlaces a bases detectados: {diagnostics['base_links_detected']}",
        f"- Enlaces a modificaciones de fechas: {diagnostics['date_change_links_detected']}",
        f"- Abiertos confirmados: {counts['open_confirmed']}",
        f"- Cerrados/finalizados/desiertos: {counts['closed']}",
        f"- Pendientes de revision manual: {counts['manual_review']}",
        "",
        "## Alcance",
        "",
        "La captura consulta la pagina oficial de concursos publicos y variantes paginadas",
        "`page=2` y `page=3`. No descarga documentos.",
        "El estado queda en `output/sources/romeral/monitor_state.json` y se usa solo para",
        "detectar cambios posteriores por hash normalizado.",
        "",
        "## Seguridad",
        "",
        "La salida se sanitiza con la capa comun y no se publica automaticamente en",
        "`public/data`. Cualquier publicacion sin cierre confiable queda como `manual_review`",
        "con etiqueta `Revisar bases`.",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Modo explicito sin publicar ni enviar alertas.")
    parser.add_argument("--url", default=None, help="URL oficial de concursos Romeral.")
    args = parser.parse_args()

    try:
        candidate = _load_candidate()
        discovery_url = args.url or candidate.get("discovery_url") or DEFAULT_DISCOVERY_URL
        previous_state = _load_previous_state(STATE_PATH)
        opportunities, diagnostics, state = fetch_romeral_candidates(discovery_url, previous_state=previous_state)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        _write_json(OPPORTUNITIES_PATH, opportunities)
        _write_json(DIAGNOSTICS_PATH, diagnostics)
        _write_json(STATE_PATH, state)
        _write_report(candidate, diagnostics)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    counts = diagnostics["status_counts"]
    print("Dry-run Municipalidad de Romeral")
    print("--------------------------------")
    print(f"URL configurada: {discovery_url}")
    print(f"Paginas revisadas: {len(diagnostics['pages_checked'])}")
    print(f"Cambio detectado: {'Si' if diagnostics['source_change_detected'] else 'No'}")
    print(f"Publicaciones detectadas: {diagnostics['publications_detected']}")
    print(f"Documentos detectados: {diagnostics['documents_detected']}")
    print(f"Enlaces a bases detectados: {diagnostics['base_links_detected']}")
    print(f"Enlaces a modificaciones de fechas: {diagnostics['date_change_links_detected']}")
    print(f"Abiertos confirmados: {counts['open_confirmed']}")
    print(f"Cerrados/finalizados/desiertos: {counts['closed']}")
    print(f"Pendientes de revision manual: {counts['manual_review']}")
    if diagnostics.get("telegram_notice"):
        print(f"Aviso controlado local: {diagnostics['telegram_notice']}")
    print(f"Salida local: {OPPORTUNITIES_PATH}")
    print("No se modifico public/data ni se envio Telegram real.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
