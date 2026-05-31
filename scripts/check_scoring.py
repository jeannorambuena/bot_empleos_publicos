"""Run a local scoring smoke test with standard-library Python only."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.config_loader import ConfigurationError, load_json, load_profile
from radar.scoring import calculate_match, match_level_for_score


def main() -> int:
    try:
        profile = load_profile(ROOT / "config" / "profile.example.json")
        opportunities = load_json(ROOT / "examples" / "sample_opportunities.json")
    except ConfigurationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not isinstance(opportunities, list) or not opportunities:
        print("ERROR: No hay oportunidades para evaluar.", file=sys.stderr)
        return 1

    print("id | title | score | level | reasons")
    print("-" * 112)

    for opportunity in opportunities:
        result = calculate_match(opportunity, profile)
        score = result["match_score"]
        level = result["match_level"]

        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
            print(f"ERROR: Score inválido para {opportunity.get('id', '<sin id>')}", file=sys.stderr)
            return 1
        if level != match_level_for_score(score):
            print(f"ERROR: Level inválido para {opportunity.get('id', '<sin id>')}", file=sys.stderr)
            return 1

        reasons = ", ".join(result["alert_reasons"]) or "-"
        print(f"{opportunity.get('id', '-')} | {opportunity.get('title', '-')} | {score} | {level} | {reasons}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
