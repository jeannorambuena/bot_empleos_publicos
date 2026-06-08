"""Validate the isolated Municipalidad de Molina dry-run capture."""

from __future__ import annotations

from check_local_municipal_source_common import run_check


if __name__ == "__main__":
    raise SystemExit(
        run_check(
            key="molina",
            source_id="municipalidad-molina",
            source_name="Municipalidad de Molina",
            commune="Molina",
            allowed_hosts=("molina.cl",),
        )
    )
