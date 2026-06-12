"""Run the full local QA suite for Radar Laboral Publico Chile."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"

CHECKS = (
    "check_real_data.py",
    "check_public_data.py",
    "check_history.py",
    "check_public_bundle.py",
    "check_pages_ready.py",
    "check_sources_config.py",
    "check_source_candidates.py",
    "check_source_sanitization.py",
    "check_priority_sources.py",
    "check_review_panel.py",
    "build_telegram_preview.py",
    "check_telegram_preview.py",
    "simulate_telegram_policy.py",
    "check_release_ready.py",
)


def _run_check(index: int, total: int, script: str) -> int:
    path = SCRIPTS_DIR / script
    print(f"\n[{index}/{total}] {script}", flush=True)
    print("-" * (len(script) + len(f"[{index}/{total}] ")), flush=True)
    if not path.exists():
        print(f"ERROR: no existe {path}", file=sys.stderr)
        return 1
    result = subprocess.run([sys.executable, str(path)], cwd=ROOT)
    if result.returncode != 0:
        print(
            f"ERROR: {script} fallo con codigo {result.returncode}.",
            file=sys.stderr,
        )
        return result.returncode
    return 0


def main() -> int:
    total = len(CHECKS)
    for index, script in enumerate(CHECKS, start=1):
        returncode = _run_check(index, total, script)
        if returncode != 0:
            return returncode
    print("\nOK: todas las pruebas integrales pasaron")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
