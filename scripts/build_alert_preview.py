"""Generate local email preview files without using SMTP or credentials."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.alerts import (
    generate_email_subject,
    generate_html_body,
    generate_text_body,
    select_alertable_opportunities,
)
from radar.config_loader import ConfigurationError, load_json


OUTPUT = ROOT / "output" / "alerts"


def _reference_time(last_run: Any) -> datetime:
    if isinstance(last_run, dict) and isinstance(last_run.get("finished_at"), str):
        try:
            return datetime.fromisoformat(last_run["finished_at"])
        except ValueError:
            pass
    return datetime.now().astimezone()


def _write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> int:
    try:
        opportunities = load_json(ROOT / "public" / "data" / "opportunities.json")
        summary = load_json(ROOT / "public" / "data" / "summary.json")
        last_run = load_json(ROOT / "public" / "data" / "last_run.json")
        alerts_config = load_json(ROOT / "config" / "alerts.example.json")
    except ConfigurationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not isinstance(opportunities, list):
        print("ERROR: opportunities.json debe contener una lista.", file=sys.stderr)
        return 1
    if not isinstance(summary, dict) or not isinstance(alerts_config, dict):
        print("ERROR: summary.json y alerts.example.json deben contener objetos.", file=sys.stderr)
        return 1

    generated_at = _reference_time(last_run)
    alertable = select_alertable_opportunities(
        opportunities,
        alerts_config,
        reference_time=generated_at,
    )
    public_site_url = os.environ.get("PUBLIC_SITE_URL") or None
    subject = generate_email_subject(alertable, is_demo=all(item.get("is_demo") is True for item in opportunities))
    text_body = generate_text_body(alertable, public_site_url=public_site_url, generated_at=generated_at)
    html_body = generate_html_body(alertable, public_site_url=public_site_url, generated_at=generated_at)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "email-preview.txt").write_text(f"Asunto: {subject}\n\n{text_body}", encoding="utf-8")
    (OUTPUT / "email-preview.html").write_text(html_body, encoding="utf-8")

    preview_summary = {
        "mode": "preview",
        "email_sent": False,
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "subject": subject,
        "public_site_url": public_site_url,
        "total_opportunities_read": len(opportunities),
        "total_alertable": len(alertable),
        "high_match": sum(item.get("match_level") == "Alta" for item in alertable),
        "closing_soon": sum(
            any(reason.startswith("Cierre en ") for reason in item["preview_alert_reasons"])
            for item in alertable
        ),
        "new_opportunities": sum("Nueva oportunidad" in item["preview_alert_reasons"] for item in alertable),
        "alertable_ids": [item.get("id") for item in alertable],
    }
    _write_json(OUTPUT / "alert-summary.json", preview_summary)

    print("Preview local generado. No se envió ningún correo.")
    print(f"total oportunidades leídas: {preview_summary['total_opportunities_read']}")
    print(f"total alertables: {preview_summary['total_alertable']}")
    print(f"alta coincidencia: {preview_summary['high_match']}")
    print(f"cierre próximo: {preview_summary['closing_soon']}")
    print(f"nuevas: {preview_summary['new_opportunities']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
