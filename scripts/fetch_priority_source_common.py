"""Shared local writer for the P1 dry-run batch."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.sources.slep_colchagua import fetch_candidates as fetch_colchagua
from radar.sources.slep_los_cerezos import fetch_candidates as fetch_los_cerezos
from radar.sources.talca import fetch_candidates as fetch_talca


CATALOG_PATH = ROOT / "data" / "source_candidates.json"
SOURCES: dict[str, tuple[str, str, Callable[[str], tuple[list[dict[str, Any]], dict[str, Any]]]]] = {
    "talca": ("municipalidad-talca", "Municipalidad de Talca", fetch_talca),
    "slep_colchagua": ("slep-colchagua", "SLEP Colchagua", fetch_colchagua),
    "slep_los_cerezos": ("slep-los-cerezos", "SLEP Los Cerezos", fetch_los_cerezos),
}


def fetch_source(key: str) -> int:
    source_id, label, fetcher = SOURCES[key]
    try:
        candidate = _load_candidate(source_id)
        opportunities, diagnostics = fetcher(candidate["discovery_url"])
        output_dir = ROOT / "output" / "sources" / key
        _write_json(output_dir / "opportunities.json", opportunities)
        _write_json(output_dir / "diagnostics.json", diagnostics)
        _write_report(output_dir / "report.md", label, candidate, diagnostics)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {label}: {error}", file=sys.stderr)
        return 1
    print(f"Dry-run {label}: {len(opportunities)} publicaciones locales.")
    print(f"Salida local: {output_dir / 'opportunities.json'}")
    print("No se modificó public/data ni se enviaron alertas.")
    return 0


def _load_candidate(source_id: str) -> dict[str, Any]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    matches = [item for item in payload.get("sources", []) if item.get("id") == source_id]
    if len(matches) != 1 or not matches[0].get("discovery_url"):
        raise ValueError(f"El catálogo debe contener una ficha utilizable {source_id}.")
    return matches[0]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_report(path: Path, label: str, candidate: dict[str, Any], diagnostics: dict[str, Any]) -> None:
    counts = diagnostics["status_counts"]
    lines = [
        f"# Dry-run {label}",
        "",
        f"- URL configurada: {candidate['discovery_url']}",
        f"- Estado de acceso: {diagnostics['access_status']}",
        f"- Publicaciones detectadas: {diagnostics['publications_detected']}",
        f"- open_confirmed: {counts['open_confirmed']}",
        f"- closed: {counts['closed']}",
        f"- manual_review: {counts['manual_review']}",
        f"- Enlaces externos privados: {diagnostics['external_private']}",
        f"- Documentos detectados: {diagnostics['documents_detected']}",
        f"- Fechas de cierre confiables: {diagnostics['reliable_closing_dates']}",
        f"- Riesgo de privacidad: {diagnostics['privacy_risk']}",
        f"- Recomendación siguiente: {diagnostics['recommendation']}",
        "",
        "## Diagnóstico",
        "",
        diagnostics["notes"],
    ]
    if diagnostics.get("error"):
        lines.extend(["", f"- Error conservado: {diagnostics['error']}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
