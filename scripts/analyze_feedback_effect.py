"""Report the visible effect of versioned human feedback."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        opportunities = json.loads((ROOT / "public" / "data" / "opportunities.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    affected = [item for item in opportunities if item.get("human_reviewed") is True]
    counts = Counter(item.get("human_feedback_action") for item in affected)
    print(f"oportunidades con feedback: {len(affected)}")
    for action in ("false_positive", "useful", "boost_priority", "lower_priority", "review"):
        print(f"{action}: {counts[action]}")
    if not affected:
        print("Sin feedback humano versionado aplicado.")
        return 0
    print("\nOportunidades afectadas")
    print("----------------------")
    for item in affected:
        print(
            f"{item.get('id')} | "
            f"{item.get('base_match_score')}->{item.get('match_score')} | "
            f"{item.get('base_match_level')}->{item.get('match_level')} | "
            f"{item.get('human_feedback_action')} | {item.get('title')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
