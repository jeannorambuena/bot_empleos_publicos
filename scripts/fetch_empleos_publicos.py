"""Capture, validate and promote current Empleos Publicos listings locally."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config import FEED_URLS_REGIONES
from radar.capture_integrity import (
    CaptureIntegrityPolicy,
    load_previous_normalized,
    validate_capture_integrity,
)
from radar.normalize_opportunity import normalize_real_opportunities
from radar.sources.empleos_publicos import fetch_empleos_publicos


RAW_PATH = ROOT / "data" / "raw" / "empleos_publicos_raw.json"
NORMALIZED_PATH = ROOT / "data" / "normalized" / "empleos_publicos_normalized.json"
STAGING_DIR = ROOT / "data" / "staging" / "empleos_publicos"
STAGING_RAW_PATH = STAGING_DIR / "empleos_publicos_raw.staging.json"
STAGING_NORMALIZED_PATH = STAGING_DIR / "empleos_publicos_normalized.staging.json"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> int:
    required_urls = list(FEED_URLS_REGIONES)
    raw_opportunities, diagnostics = fetch_empleos_publicos(required_urls)
    normalized = normalize_real_opportunities(raw_opportunities)
    staged_raw = {
        "source": "Empleos Publicos",
        "required_urls": required_urls,
        "diagnostics": diagnostics,
        "opportunities": raw_opportunities,
    }
    _write_json(STAGING_RAW_PATH, staged_raw)
    _write_json(STAGING_NORMALIZED_PATH, normalized)

    try:
        policy = CaptureIntegrityPolicy.from_env()
        integrity_errors = validate_capture_integrity(
            required_urls=required_urls,
            diagnostics=diagnostics,
            normalized=normalized,
            previous_normalized=load_previous_normalized(NORMALIZED_PATH),
            policy=policy,
        )
    except ValueError as error:
        integrity_errors = [str(error)]

    if integrity_errors:
        print("ERROR: captura principal incompleta; no se promueve el dataset normalizado.", file=sys.stderr)
        print(f"staging raw: {STAGING_RAW_PATH}")
        print(f"staging normalized: {STAGING_NORMALIZED_PATH}")
        for error in integrity_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    _write_json(RAW_PATH, staged_raw)
    _write_json(NORMALIZED_PATH, normalized)

    with_url = sum(bool(item.get("source_url")) for item in normalized)
    errors = sum(bool(item.get("error")) for item in diagnostics)
    print("gate integridad captura: OK")
    print(f"umbral maximo caida volumen: {policy.max_volume_drop_ratio:.0%}")
    print(f"total URLs revisadas: {len(diagnostics)}")
    print(f"total oportunidades crudas: {len(raw_opportunities)}")
    print(f"total normalizadas: {len(normalized)}")
    print(f"total con URL: {with_url}")
    print(f"total sin URL: {len(normalized) - with_url}")
    print(f"total errores: {errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
