"""Validate static human review panel assets."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"
FILES = (PUBLIC / "review.html", PUBLIC / "assets" / "review.js", PUBLIC / "assets" / "review.css")
FORBIDDEN = ("telegram_bot_token", "telegram_chat_id", "api.telegram.org", "http://", "https://")


def main() -> int:
    errors: list[str] = []
    for path in FILES:
        if not path.exists():
            errors.append(f"No existe: {path}")
    if not errors:
        combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in FILES)
        if any(marker in combined for marker in FORBIDDEN):
            errors.append("El panel contiene tokens o endpoints externos sospechosos.")
        review_js = (PUBLIC / "assets" / "review.js").read_text(encoding="utf-8")
        if 'fetch("data/opportunities.json")' not in review_js:
            errors.append("review.js no lee data/opportunities.json localmente.")
        index_html = (PUBLIC / "index.html").read_text(encoding="utf-8")
        if 'href="review.html"' not in index_html:
            errors.append("public/index.html no enlaza el panel de revisión.")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: panel estático de revisión humana válido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
