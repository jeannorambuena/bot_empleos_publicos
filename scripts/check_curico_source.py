"""Validate the isolated Municipalidad de Curico dry-run capture."""

from __future__ import annotations

from check_local_municipal_source_common import run_check


if __name__ == "__main__":
    raise SystemExit(
        run_check(
            key="curico",
            source_id="municipalidad-curico",
            source_name="Municipalidad de Curico",
            commune="Curico",
            allowed_hosts=("curico.cl",),
        )
    )
