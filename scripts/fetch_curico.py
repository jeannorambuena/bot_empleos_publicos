"""Generate an isolated local dry-run capture for Municipalidad de Curico."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fetch_local_municipal_source_common import run_fetch
from radar.sources.curico import DEFAULT_DISCOVERY_URLS, SOURCE_ID, fetch_curico_candidates


if __name__ == "__main__":
    raise SystemExit(
        run_fetch(
            key="curico",
            source_id=SOURCE_ID,
            default_urls=DEFAULT_DISCOVERY_URLS,
            fetcher=fetch_curico_candidates,
        )
    )
