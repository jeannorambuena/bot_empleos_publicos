from __future__ import annotations

import json

import scripts.fetch_empleos_publicos as fetch_script

from radar.normalize_opportunity import normalize_real_opportunities


URLS = [
    "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?i=15&region=rm",
    "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?i=7&region=ohiggins",
    "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?i=8&region=maule",
]
REGIONS = ["Metropolitana", "O’Higgins", "Maule"]


def _raw_items(counts: list[int]) -> list[dict]:
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
    return items


def _diagnostics(counts: list[int], *, error_index: int | None = None) -> list[dict]:
    return [
        {
            "source": "Empleos Publicos",
            "url": url,
            "region": region,
            "detected": count,
            "added_unique": count,
            "error": "HTTPError: 500" if index == error_index else None,
        }
        for index, (url, region, count) in enumerate(zip(URLS, REGIONS, counts))
    ]


def _patch_paths(monkeypatch, tmp_path) -> tuple:
    raw_path = tmp_path / "data" / "raw" / "empleos_publicos_raw.json"
    normalized_path = tmp_path / "data" / "normalized" / "empleos_publicos_normalized.json"
    staging_raw = tmp_path / "data" / "staging" / "raw.json"
    staging_normalized = tmp_path / "data" / "staging" / "normalized.json"
    public_data = tmp_path / "public" / "data"
    public_data.mkdir(parents=True)
    telegram_state = public_data / "telegram_alert_state.json"
    telegram_state.write_text('{"sent_opportunity_ids": ["old"], "last_mode": "automatic"}\n', encoding="utf-8")
    (public_data / "opportunities.json").write_text("[]\n", encoding="utf-8")
    monkeypatch.setattr(fetch_script, "FEED_URLS_REGIONES", URLS)
    monkeypatch.setattr(fetch_script, "RAW_PATH", raw_path)
    monkeypatch.setattr(fetch_script, "NORMALIZED_PATH", normalized_path)
    monkeypatch.setattr(fetch_script, "STAGING_RAW_PATH", staging_raw)
    monkeypatch.setattr(fetch_script, "STAGING_NORMALIZED_PATH", staging_normalized)
    return raw_path, normalized_path, staging_raw, staging_normalized, telegram_state


def test_incomplete_capture_returns_nonzero_and_preserves_files(monkeypatch, tmp_path) -> None:
    _, normalized_path, staging_raw, staging_normalized, telegram_state = _patch_paths(monkeypatch, tmp_path)
    previous = normalize_real_opportunities(_raw_items([4, 4, 4]))
    normalized_path.parent.mkdir(parents=True)
    normalized_path.write_text(json.dumps(previous, ensure_ascii=False), encoding="utf-8")
    before_normalized = normalized_path.read_text(encoding="utf-8")
    before_state = telegram_state.read_text(encoding="utf-8")

    monkeypatch.setattr(
        fetch_script,
        "fetch_empleos_publicos",
        lambda urls: (_raw_items([4, 0, 4]), _diagnostics([4, 0, 4], error_index=1)),
    )

    assert fetch_script.main() == 1
    assert normalized_path.read_text(encoding="utf-8") == before_normalized
    assert telegram_state.read_text(encoding="utf-8") == before_state
    assert staging_raw.exists()
    assert staging_normalized.exists()


def test_abrupt_drop_returns_nonzero_and_preserves_normalized(monkeypatch, tmp_path) -> None:
    _, normalized_path, _, _, _ = _patch_paths(monkeypatch, tmp_path)
    previous = normalize_real_opportunities(_raw_items([10, 10, 10]))
    normalized_path.parent.mkdir(parents=True)
    normalized_path.write_text(json.dumps(previous, ensure_ascii=False), encoding="utf-8")
    before_normalized = normalized_path.read_text(encoding="utf-8")
    monkeypatch.setattr(
        fetch_script,
        "fetch_empleos_publicos",
        lambda urls: (_raw_items([3, 3, 3]), _diagnostics([3, 3, 3])),
    )

    assert fetch_script.main() == 1
    assert normalized_path.read_text(encoding="utf-8") == before_normalized


def test_valid_capture_promotes_normalized(monkeypatch, tmp_path) -> None:
    raw_path, normalized_path, _, _, _ = _patch_paths(monkeypatch, tmp_path)
    previous = normalize_real_opportunities(_raw_items([4, 4, 4]))
    normalized_path.parent.mkdir(parents=True)
    normalized_path.write_text(json.dumps(previous, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(
        fetch_script,
        "fetch_empleos_publicos",
        lambda urls: (_raw_items([4, 4, 4]), _diagnostics([4, 4, 4])),
    )

    assert fetch_script.main() == 0
    promoted = json.loads(normalized_path.read_text(encoding="utf-8"))
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    assert len(promoted) == 12
    assert raw["required_urls"] == URLS
