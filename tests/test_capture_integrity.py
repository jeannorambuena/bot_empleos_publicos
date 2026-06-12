from __future__ import annotations

from datetime import datetime, timezone

import pytest
import requests

from radar.capture_integrity import CaptureIntegrityPolicy, validate_capture_integrity
from radar.normalize_opportunity import normalize_real_opportunities
from radar.sources import empleos_publicos


URLS = [
    "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?i=15&region=rm",
    "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?i=7&region=ohiggins",
    "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?i=8&region=maule",
]
REGIONS = ["Metropolitana", "O’Higgins", "Maule"]


def _html(source_id: int) -> str:
    return f"""
    <html><body>
      <div class="caja">
        <div id="bx_titulos">Analista TI {source_id}</div>
        <div id="bx_resumen">
          <strong>Servicio Publico</strong>
          Desarrollo y soporte.
          <em>Plazo de Postulacion 01/07/2026 - 10/07/2026</em>
        </div>
        <a href="/pub/convocatorias/convpostularavisoTrabajo.aspx?i={source_id}&c=0">Ver bases</a>
      </div>
    </body></html>
    """


def _normalized(counts: list[int]) -> list[dict]:
    items = []
    for url, region, count in zip(URLS, REGIONS, counts):
        for index in range(count):
            source_id = f"{region}-{index}"
            items.append(
                {
                    "id": f"empleos-publicos-{source_id}",
                    "source_id": source_id,
                    "title": f"Analista {source_id}",
                    "institution": "Servicio Publico",
                    "source": "Empleos Publicos",
                    "source_url": f"https://www.empleospublicos.cl/postular?i={source_id}",
                    "region": region,
                    "commune": None,
                    "closing_date": "2026-07-10",
                    "detected_at": "2026-06-12T10:00:00-04:00",
                    "description": "Cargo publico.",
                    "listing_url": url,
                }
            )
    return normalize_real_opportunities(items)


def _diagnostics(counts: list[int], *, errors: dict[int, str] | None = None) -> list[dict]:
    errors = errors or {}
    return [
        {
            "source": "Empleos Publicos",
            "url": url,
            "region": region,
            "detected": count,
            "added_unique": count,
            "error": errors.get(index),
        }
        for index, (url, region, count) in enumerate(zip(URLS, REGIONS, counts))
    ]


def _errors(counts: list[int], *, diagnostics: list[dict] | None = None, previous: list[dict] | None = None) -> list[str]:
    return validate_capture_integrity(
        required_urls=URLS,
        diagnostics=diagnostics or _diagnostics(counts),
        normalized=_normalized(counts),
        previous_normalized=previous or _normalized(counts),
        policy=CaptureIntegrityPolicy(max_volume_drop_ratio=0.35),
    )


def test_all_regions_respond_correctly() -> None:
    assert _errors([3, 2, 2]) == []


def test_region_http_error_blocks_capture() -> None:
    errors = _errors([3, 2, 2], diagnostics=_diagnostics([3, 2, 2], errors={1: "HTTPError: 500"}))
    assert any("captura con error" in error for error in errors)


def test_region_timeout_blocks_capture() -> None:
    errors = _errors([3, 2, 2], diagnostics=_diagnostics([3, 2, 2], errors={0: "Timeout: timed out"}))
    assert any("Timeout" in error for error in errors)


def test_region_parsing_error_blocks_capture() -> None:
    errors = _errors([3, 2, 2], diagnostics=_diagnostics([3, 2, 2], errors={2: "ParsingError: boom"}))
    assert any("ParsingError" in error for error in errors)


def test_missing_region_diagnostic_blocks_capture() -> None:
    diagnostics = _diagnostics([3, 2, 2])[:2]
    errors = _errors([3, 2, 2], diagnostics=diagnostics)
    assert any("falta diagnostico" in error for error in errors)


def test_duplicate_diagnostic_blocks_capture() -> None:
    diagnostic = _diagnostics([3, 2, 2])
    errors = _errors([3, 2, 2], diagnostics=diagnostic + [diagnostic[0]])
    assert any("duplicado" in error for error in errors)


def test_unexpected_region_blocks_capture() -> None:
    diagnostic = _diagnostics([3, 2, 2])
    diagnostic[0]["region"] = "No especificada"
    errors = _errors([3, 2, 2], diagnostics=diagnostic)
    assert any("region diagnostica invalida" in error for error in errors)


def test_zero_results_blocks_capture() -> None:
    errors = _errors([3, 0, 2])
    assert any("detected=0" in error for error in errors)


def test_valid_capture_inside_volume_threshold() -> None:
    assert _errors([2, 2, 2], previous=_normalized([3, 3, 3])) == []


def test_abrupt_volume_drop_blocks_capture() -> None:
    errors = _errors([1, 1, 1], previous=_normalized([4, 4, 4]))
    assert any("caida abrupta" in error for error in errors)


class _Response:
    def __init__(self, text: str, error: Exception | None = None) -> None:
        self.text = text
        self._error = error

    def raise_for_status(self) -> None:
        if self._error:
            raise self._error


class _Session:
    def __init__(self, responses: list[object]) -> None:
        self.responses = responses
        self.calls = 0

    def get(self, url: str, **_: object) -> object:
        response = self.responses[self.calls]
        self.calls += 1
        if isinstance(response, Exception):
            raise response
        return response


def test_fetch_empleos_publicos_success_records_all_diagnostics() -> None:
    session = _Session([_Response(_html(101)), _Response(_html(102)), _Response(_html(103))])
    opportunities, diagnostics = empleos_publicos.fetch_empleos_publicos(
        URLS,
        session=session,  # type: ignore[arg-type]
        detected_at=datetime(2026, 6, 12, tzinfo=timezone.utc),
    )
    assert len(opportunities) == 3
    assert [item["region"] for item in diagnostics] == REGIONS
    assert not any(item["error"] for item in diagnostics)


def test_fetch_empleos_publicos_http_error_is_diagnostic() -> None:
    session = _Session([_Response(_html(101)), _Response("", requests.HTTPError("500")), _Response(_html(103))])
    opportunities, diagnostics = empleos_publicos.fetch_empleos_publicos(URLS, session=session)  # type: ignore[arg-type]
    assert len(opportunities) == 2
    assert "HTTPError" in diagnostics[1]["error"]


def test_fetch_empleos_publicos_timeout_is_diagnostic() -> None:
    session = _Session([_Response(_html(101)), requests.Timeout("slow"), _Response(_html(103))])
    opportunities, diagnostics = empleos_publicos.fetch_empleos_publicos(URLS, session=session)  # type: ignore[arg-type]
    assert len(opportunities) == 2
    assert "Timeout" in diagnostics[1]["error"]


def test_fetch_empleos_publicos_parsing_error_is_diagnostic(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_: object, **__: object) -> list[dict]:
        raise ValueError("changed html")

    monkeypatch.setattr(empleos_publicos, "parse_listing_html", boom)
    session = _Session([_Response(_html(101))])
    opportunities, diagnostics = empleos_publicos.fetch_empleos_publicos([URLS[0]], session=session)  # type: ignore[arg-type]
    assert opportunities == []
    assert "ParsingError" in diagnostics[0]["error"]
