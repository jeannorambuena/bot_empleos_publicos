"""Run the three P1 source dry-runs."""

from fetch_priority_source_common import SOURCES, fetch_source

raise SystemExit(max(fetch_source(key) for key in SOURCES))
