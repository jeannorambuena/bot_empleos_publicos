"""Validate configurable source metadata without connecting to websites."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "config" / "sources.example.json"
PARSERS = {"empleos_publicos", "planned_html", "manual"}
STATUSES = {"active", "planned", "manual_review"}
FIELDS = {"id", "name", "type", "url", "enabled", "priority", "notes", "status", "parser"}
SECRET_MARKERS = ("token", "secret", "password", "api_key", "chat_id")


def main() -> int:
    try:
        payload = json.loads(PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    sources = payload.get("sources") if isinstance(payload, dict) else None
    errors: list[str] = []
    if not isinstance(sources, list) or not sources:
        errors.append("sources.example.json debe contener una lista sources no vacía.")
    else:
        ids = []
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"sources[{index}] debe ser objeto.")
                continue
            missing = FIELDS - source.keys()
            if missing:
                errors.append(f"sources[{index}] sin campos: {', '.join(sorted(missing))}")
            ids.append(source.get("id"))
            url = source.get("url")
            if not isinstance(url, str) or not url.strip() or urlparse(url).scheme not in {"http", "https"}:
                errors.append(f"sources[{index}].url debe ser HTTP(S) no vacía.")
            if source.get("parser") not in PARSERS:
                errors.append(f"sources[{index}].parser no permitido.")
            if source.get("status") not in STATUSES:
                errors.append(f"sources[{index}].status no permitido.")
        if len(ids) != len(set(ids)):
            errors.append("Los ids de fuentes deben ser únicos.")
    serialized = json.dumps(payload, ensure_ascii=False).lower()
    if any(marker in serialized for marker in SECRET_MARKERS):
        errors.append("La configuración contiene un marcador asociado a secretos.")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: configuración de fuentes válida ({len(sources)} fuentes).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
