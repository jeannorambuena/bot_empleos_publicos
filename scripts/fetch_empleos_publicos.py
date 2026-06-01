"""Capture and normalize current Empleos Publicos listings locally."""

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
from radar.normalize_opportunity import normalize_real_opportunities
from radar.sources.empleos_publicos import fetch_empleos_publicos


RAW_PATH = ROOT / "data" / "raw" / "empleos_publicos_raw.json"
NORMALIZED_PATH = ROOT / "data" / "normalized" / "empleos_publicos_normalized.json"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> int:
    raw_opportunities, diagnostics = fetch_empleos_publicos(FEED_URLS_REGIONES)
    normalized = normalize_real_opportunities(raw_opportunities)
    _write_json(
        RAW_PATH,
        {
            "source": "Empleos Públicos",
            "diagnostics": diagnostics,
            "opportunities": raw_opportunities,
        },
    )
    _write_json(NORMALIZED_PATH, normalized)

    with_url = sum(bool(item.get("source_url")) for item in normalized)
    errors = sum(bool(item.get("error")) for item in diagnostics)
    print(f"total URLs revisadas: {len(diagnostics)}")
    print(f"total oportunidades crudas: {len(raw_opportunities)}")
    print(f"total normalizadas: {len(normalized)}")
    print(f"total con URL: {with_url}")
    print(f"total sin URL: {len(normalized) - with_url}")
    print(f"total errores: {errors}")
    for diagnostic in diagnostics:
        if diagnostic.get("error"):
            print(f"ERROR {diagnostic['url']}: {diagnostic['error']}", file=sys.stderr)
    return 0 if normalized else 1


if __name__ == "__main__":
    raise SystemExit(main())
