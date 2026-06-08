"""Helpers for isolated local municipal dry-run captures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "source_candidates.json"


def run_fetch(
    *,
    key: str,
    source_id: str,
    default_urls: tuple[str, ...],
    fetcher: Callable[..., tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]],
) -> int:
    parser = argparse.ArgumentParser(description=f"Generate dry-run capture for {source_id}.")
    parser.add_argument("--dry-run", action="store_true", help="Modo explicito sin publicar ni enviar alertas.")
    parser.add_argument("--url", action="append", default=None, help="URL oficial a consultar; se puede repetir.")
    args = parser.parse_args()

    output_dir = ROOT / "output" / "sources" / key
    opportunities_path = output_dir / "opportunities.json"
    diagnostics_path = output_dir / "diagnostics.json"
    state_path = output_dir / "monitor_state.json"
    report_path = output_dir / "report.md"

    try:
        candidate = _load_candidate(source_id)
        urls = tuple(args.url or candidate.get("discovery_urls") or [candidate.get("discovery_url")] or default_urls)
        urls = tuple(str(url).strip() for url in urls if str(url or "").strip()) or default_urls
        previous_state = _load_previous_state(state_path)
        opportunities, diagnostics, state = fetcher(urls, previous_state=previous_state)
        output_dir.mkdir(parents=True, exist_ok=True)
        _write_json(opportunities_path, opportunities)
        _write_json(diagnostics_path, diagnostics)
        _write_json(state_path, state)
        _write_report(report_path, diagnostics, opportunities_path)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"ERROR: {error}")
        return 1

    counts = diagnostics["status_counts"]
    print(f"Dry-run {diagnostics['source']}")
    print("-" * (8 + len(str(diagnostics["source"]))))
    for url in urls:
        print(f"URL revisada: {url}")
    print(f"Paginas revisadas: {len(diagnostics['pages_checked'])}")
    print(f"Cambio detectado: {'Si' if diagnostics['source_change_detected'] else 'No'}")
    print(f"Publicaciones detectadas: {diagnostics['publications_detected']}")
    print(f"Documentos detectados: {diagnostics['documents_detected']}")
    print(f"Enlaces a bases/fichas detectados: {diagnostics['base_links_detected']}")
    print(f"Enlaces de postulacion detectados: {diagnostics['application_links_detected']}")
    print(f"Abiertos confirmados: {counts['open_confirmed']}")
    print(f"Cerrados/finalizados/desiertos: {counts['closed']}")
    print(f"Pendientes de revision manual: {counts['manual_review']}")
    print(f"Salida local: {opportunities_path}")
    print("No se modifico public/data ni se envio Telegram real.")
    return 0


def _load_candidate(source_id: str) -> dict[str, Any]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    sources = payload.get("sources") if isinstance(payload, dict) else None
    matches = [item for item in sources or [] if isinstance(item, dict) and item.get("id") == source_id]
    if len(matches) != 1:
        raise ValueError(f"El catalogo debe contener exactamente una ficha {source_id}.")
    return matches[0]


def _load_previous_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"El estado {path} debe ser un objeto JSON.")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_report(path: Path, diagnostics: dict[str, Any], opportunities_path: Path) -> None:
    counts = diagnostics["status_counts"]
    lines = [
        f"# Dry-run {diagnostics['source']}",
        "",
        f"- URLs revisadas: {len(diagnostics['listing_urls'])}",
        f"- Paginas revisadas: {len(diagnostics['pages_checked'])}",
        f"- Hash normalizado: `{diagnostics['listing_hash']}`",
        f"- Cambio detectado: {'si' if diagnostics['source_change_detected'] else 'no'}",
        f"- Publicaciones detectadas: {diagnostics['publications_detected']}",
        f"- Documentos detectados: {diagnostics['documents_detected']}",
        f"- Enlaces a bases/fichas: {diagnostics['base_links_detected']}",
        f"- Enlaces de postulacion: {diagnostics['application_links_detected']}",
        f"- Abiertos confirmados: {counts['open_confirmed']}",
        f"- Cerrados/finalizados/desiertos: {counts['closed']}",
        f"- Revision manual: {counts['manual_review']}",
        f"- Salida local: `{opportunities_path}`",
        "",
        "## Alcance",
        "",
        "Modo dry-run/manual_review_only. La captura revisa paginas oficiales, calcula hash normalizado",
        "y guarda estado local para detectar cambios. No descarga documentos, no publica en public/data",
        "y no envia Telegram real.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
