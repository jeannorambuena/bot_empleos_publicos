"""Validate the isolated Municipalidad de Rauco dry-run capture."""

from __future__ import annotations

from check_local_municipal_source_common import run_check


if __name__ == "__main__":
    raise SystemExit(
        run_check(
            key="rauco",
            source_id="municipalidad-rauco",
            source_name="Municipalidad de Rauco",
            commune="Rauco",
            allowed_hosts=("munirauco.cl",),
        )
    )
