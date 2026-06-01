"""Generate dashboard JSON files from locally normalized real opportunities."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.config_loader import ConfigurationError, load_json, load_profile
from radar.normalize_opportunity import score_real_opportunity
from radar.public_data import summarize_opportunities, write_public_data


NORMALIZED_PATH = ROOT / "data" / "normalized" / "empleos_publicos_normalized.json"


def main() -> int:
    try:
        profile = load_profile(ROOT / "config" / "profile.example.json")
        opportunities = load_json(NORMALIZED_PATH)
    except ConfigurationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not isinstance(opportunities, list) or not opportunities:
        print("ERROR: No hay datos reales normalizados. Ejecuta scripts/fetch_empleos_publicos.py.", file=sys.stderr)
        return 1

    generated_at = datetime.now().astimezone()
    scored = [score_real_opportunity(item, profile) for item in opportunities]
    scored.sort(key=lambda item: (-item["match_score"], item.get("closing_date") or "9999-12-31"))
    summary = summarize_opportunities(scored, generated_at=generated_at)
    last_run = {
        "finished_at": generated_at.isoformat(timespec="seconds"),
        "status": "real-local",
        "message": "Datos reales locales generados correctamente",
    }
    write_public_data(ROOT / "public" / "data", scored, summary, last_run)

    levels = {"Alta": 0, "Media": 0, "Baja": 0, "Descartada": 0}
    for item in scored:
        levels[item["match_level"]] += 1
    with_url = sum(bool(item.get("source_url")) for item in scored)
    print(f"total: {len(scored)}")
    for level in ("Alta", "Media", "Baja", "Descartada"):
        print(f"{level}: {levels[level]}")
    print(f"con source_url real: {with_url}")
    print(f"sin source_url: {len(scored) - with_url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
