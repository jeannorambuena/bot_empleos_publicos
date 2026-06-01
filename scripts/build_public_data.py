"""Generate demo public JSON files for the static dashboard."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.config_loader import ConfigurationError, load_json, load_profile
from radar.public_data import DEFAULT_TIMEZONE, build_public_payloads, write_public_data


def _resolve_timezone(timezone_name: str) -> Any:
    """Use IANA timezone data when available and keep Windows setup dependency-free."""
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        if timezone_name == DEFAULT_TIMEZONE:
            return datetime.now().astimezone().tzinfo
        raise


def main() -> int:
    try:
        profile = load_profile(ROOT / "config" / "profile.example.json")
        opportunities = load_json(ROOT / "examples" / "sample_opportunities.json")
    except ConfigurationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not isinstance(opportunities, list) or not opportunities:
        print("ERROR: No hay oportunidades de entrada.", file=sys.stderr)
        return 1

    timezone_name = profile.get("timezone", DEFAULT_TIMEZONE)
    try:
        timezone = _resolve_timezone(timezone_name)
    except ZoneInfoNotFoundError:
        print(f"ERROR: Zona horaria no disponible: {timezone_name}", file=sys.stderr)
        return 1

    generated_at = datetime.now(timezone)
    public_opportunities, summary, last_run = build_public_payloads(
        opportunities,
        profile,
        generated_at=generated_at,
        force_demo=True,
    )
    write_public_data(ROOT / "public" / "data", public_opportunities, summary, last_run)

    levels = {"Alta": 0, "Media": 0, "Baja": 0, "Descartada": 0}
    for opportunity in public_opportunities:
        levels[opportunity["match_level"]] += 1

    print("Datos públicos demo generados correctamente.")
    print(f"total: {len(public_opportunities)}")
    print(f"alta: {levels['Alta']}")
    print(f"media: {levels['Media']}")
    print(f"baja: {levels['Baja']}")
    print(f"descartada: {levels['Descartada']}")
    print(f"nuevas: {summary['new_opportunities']}")
    print(f"cierre próximo: {summary['closing_soon']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
