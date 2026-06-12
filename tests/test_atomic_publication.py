from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from radar.atomic_publication import (
    BUNDLE_FILES,
    MANIFEST_FILE,
    build_public_bundle,
    publish_public_bundle,
    validate_public_bundle,
)


def _payload(index: int = 1) -> tuple[list[dict], dict, dict, list[dict]]:
    opportunities = [
        {
            "id": f"opp-{index}",
            "title": "Analista",
            "institution": "Servicio",
            "status": "abierta",
            "match_score": 80,
            "match_level": "Alta",
        }
    ]
    summary = {"total_opportunities": 1, "active_opportunities": 1}
    last_run = {"finished_at": "2026-06-12T12:00:00+00:00", "status": "real-local"}
    history = [
        {
            "id": f"opp-{index}",
            "first_seen_at": "2026-06-12T12:00:00+00:00",
            "last_seen_at": "2026-06-12T12:00:00+00:00",
            "seen_count": 1,
            "currently_visible": True,
        }
    ]
    return opportunities, summary, last_run, history


def _bundle(index: int = 1):
    return build_public_bundle(*_payload(index), generated_at=datetime(2026, 6, 12, 12, tzinfo=timezone.utc))


def _read_all(directory: Path) -> dict[str, str]:
    return {
        filename: (directory / filename).read_text(encoding="utf-8")
        for filename in (*BUNDLE_FILES, MANIFEST_FILE)
        if (directory / filename).exists()
    }


def test_publication_complete_success(tmp_path: Path) -> None:
    manifest = publish_public_bundle(tmp_path / "public" / "data", _bundle())
    assert manifest["status"] == "published"
    assert validate_public_bundle(tmp_path / "public" / "data") == []


def test_all_files_share_logical_identity(tmp_path: Path) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle())
    manifest = json.loads((output / MANIFEST_FILE).read_text(encoding="utf-8"))
    generation_ids = {entry["generation_id"] for entry in manifest["files"].values()}
    last_run = json.loads((output / "last_run.json").read_text(encoding="utf-8"))
    assert generation_ids == {manifest["generation_id"]}
    assert last_run["generation_id"] == manifest["generation_id"]


def test_manifest_contains_correct_checksums(tmp_path: Path) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle())
    assert validate_public_bundle(output) == []


def test_summary_matches_opportunities(tmp_path: Path) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle())
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    opportunities = json.loads((output / "opportunities.json").read_text(encoding="utf-8"))
    assert summary["total_opportunities"] == len(opportunities)


def test_history_matches_generation(tmp_path: Path) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle())
    history = json.loads((output / "history.json").read_text(encoding="utf-8"))
    opportunities = json.loads((output / "opportunities.json").read_text(encoding="utf-8"))
    assert {item["id"] for item in history if item["currently_visible"]} == {item["id"] for item in opportunities}


@pytest.mark.parametrize("fail_name", ["summary.json", "history.json", "manifest.json"])
def test_staging_write_failure_preserves_public_files(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fail_name: str) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle(1))
    before = _read_all(output)

    import radar.atomic_publication as publication

    real_atomic = publication.atomic_write_json

    def failing_write(path, payload):
        if path.name == fail_name:
            raise OSError("injected staging failure")
        return real_atomic(path, payload)

    monkeypatch.setattr(publication, "atomic_write_json", failing_write)
    with pytest.raises(OSError):
        publish_public_bundle(output, _bundle(2))
    assert _read_all(output) == before


@pytest.mark.parametrize("fail_on", [1, 3])
def test_replace_failure_rolls_back_exactly(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, fail_on: int) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle(1))
    before = _read_all(output)
    calls = {"count": 0}

    def failing_replace(src, dst):
        calls["count"] += 1
        if calls["count"] == fail_on:
            raise OSError("injected replace failure")
        Path(src).replace(dst)

    with pytest.raises(OSError):
        publish_public_bundle(output, _bundle(2), replace_func=failing_replace)
    assert _read_all(output) == before
    assert validate_public_bundle(output) == []


def test_no_public_file_changes_if_staging_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle(1))
    before = _read_all(output)

    import radar.atomic_publication as publication

    monkeypatch.setattr(publication, "atomic_write_json", lambda path, payload: (_ for _ in ()).throw(OSError("boom")))
    with pytest.raises(OSError):
        publish_public_bundle(output, _bundle(2))
    assert _read_all(output) == before


def test_no_public_file_is_truncated_after_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle(1))
    before = _read_all(output)

    def failing_replace(src, dst):
        if Path(dst).name == "summary.json":
            raise OSError("boom")
        Path(src).replace(dst)

    with pytest.raises(OSError):
        publish_public_bundle(output, _bundle(2), replace_func=failing_replace)
    assert all((output / filename).stat().st_size == len(content.encode("utf-8")) for filename, content in before.items())


def test_check_detects_checksum_altered(tmp_path: Path) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle())
    (output / "summary.json").write_text('{"total_opportunities": 2}\n', encoding="utf-8")
    assert any("checksum" in error for error in validate_public_bundle(output))


def test_check_detects_missing_file(tmp_path: Path) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle())
    (output / "history.json").unlink()
    assert any("falta history.json" in error for error in validate_public_bundle(output))


def test_check_detects_mixed_generations(tmp_path: Path) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle())
    manifest = json.loads((output / MANIFEST_FILE).read_text(encoding="utf-8"))
    manifest["files"]["summary.json"]["generation_id"] = "other"
    (output / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    assert any("generation_id distinto" in error for error in validate_public_bundle(output))


def test_check_detects_incomplete_manifest(tmp_path: Path) -> None:
    output = tmp_path / "public" / "data"
    publish_public_bundle(output, _bundle())
    manifest = json.loads((output / MANIFEST_FILE).read_text(encoding="utf-8"))
    del manifest["files"]["last_run.json"]
    (output / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    assert any("last_run.json" in error for error in validate_public_bundle(output))
