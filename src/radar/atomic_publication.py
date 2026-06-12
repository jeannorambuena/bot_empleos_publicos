"""Transactional publication for the public dashboard JSON bundle."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from radar.atomic_io import atomic_write_json


BUNDLE_FILES = ("opportunities.json", "summary.json", "last_run.json", "history.json")
MANIFEST_FILE = "manifest.json"
SCHEMA_VERSION = 1
ReplaceFunc = Callable[[Path, Path], None]


@dataclass(frozen=True)
class PublicBundle:
    opportunities: list[dict[str, Any]]
    summary: dict[str, Any]
    last_run: dict[str, Any]
    history: list[dict[str, Any]]
    generation_id: str
    generated_at: str


def make_generation_id(generated_at: datetime | str) -> str:
    value = generated_at if isinstance(generated_at, str) else generated_at.isoformat(timespec="seconds")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def publish_public_bundle(
    output_directory: str | Path,
    bundle: PublicBundle,
    *,
    staging_root: str | Path | None = None,
    replace_func: ReplaceFunc | None = None,
) -> dict[str, Any]:
    """Promote a complete public bundle with staging, manifest, backup and rollback."""
    output = Path(output_directory)
    staging_base = Path(staging_root) if staging_root else output.parent.parent / "data" / "staging" / "publication"
    staging = staging_base / bundle.generation_id
    backup = staging_base / f"{bundle.generation_id}.backup"
    payloads = _payloads(bundle)

    if staging.exists():
        shutil.rmtree(staging)
    if backup.exists():
        shutil.rmtree(backup)
    staging.mkdir(parents=True, exist_ok=True)

    try:
        for filename, payload in payloads.items():
            atomic_write_json(staging / filename, payload)
        manifest = _build_manifest(staging, bundle)
        atomic_write_json(staging / MANIFEST_FILE, manifest)
        validate_public_bundle(staging)
        _snapshot_existing(output, backup)
        output.mkdir(parents=True, exist_ok=True)
        for filename in (*BUNDLE_FILES, MANIFEST_FILE):
            (replace_func or os.replace)(staging / filename, output / filename)
        validate_public_bundle(output)
        shutil.rmtree(staging, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)
        return manifest
    except Exception:
        _rollback(output, backup)
        raise


def validate_public_bundle(directory: str | Path, *, require_manifest: bool = True) -> list[str]:
    directory = Path(directory)
    errors: list[str] = []
    manifest_path = directory / MANIFEST_FILE
    if not manifest_path.exists():
        return [f"falta {MANIFEST_FILE}"] if require_manifest else _validate_legacy_bundle(directory)
    try:
        manifest = _load_json(manifest_path)
    except ValueError as error:
        return [str(error)]
    if not isinstance(manifest, dict):
        return ["manifest debe ser objeto JSON."]
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version invalido.")
    generation_id = manifest.get("generation_id")
    generated_at = manifest.get("generated_at")
    if not isinstance(generation_id, str) or not generation_id:
        errors.append("generation_id invalido.")
    if not isinstance(generated_at, str) or not generated_at:
        errors.append("generated_at invalido.")
    files = manifest.get("files")
    if not isinstance(files, dict):
        errors.append("manifest.files debe ser objeto.")
        files = {}
    payloads = {}
    for filename in BUNDLE_FILES:
        path = directory / filename
        if not path.exists():
            errors.append(f"falta {filename}")
            continue
        if path.stat().st_size == 0:
            errors.append(f"{filename} esta vacio.")
            continue
        try:
            payloads[filename] = _load_json(path)
        except ValueError as error:
            errors.append(str(error))
            continue
        entry = files.get(filename)
        if not isinstance(entry, dict):
            errors.append(f"manifest no contiene entrada valida para {filename}.")
            continue
        if entry.get("sha256") != _sha256_file(path):
            errors.append(f"checksum invalido para {filename}.")
        if entry.get("generation_id") != generation_id:
            errors.append(f"{filename} tiene generation_id distinto en manifest.")
    errors.extend(_payload_consistency_errors(payloads))
    return errors


def build_public_bundle(
    opportunities: list[dict[str, Any]],
    summary: dict[str, Any],
    last_run: dict[str, Any],
    history: list[dict[str, Any]],
    *,
    generated_at: datetime,
) -> PublicBundle:
    generated_at_text = generated_at.isoformat(timespec="seconds")
    generation_id = make_generation_id(generated_at_text)
    last_run = dict(last_run)
    last_run["generation_id"] = generation_id
    last_run["generated_at"] = generated_at_text
    return PublicBundle(
        opportunities=opportunities,
        summary=summary,
        last_run=last_run,
        history=history,
        generation_id=generation_id,
        generated_at=generated_at_text,
    )


def _payloads(bundle: PublicBundle) -> dict[str, Any]:
    return {
        "opportunities.json": bundle.opportunities,
        "summary.json": bundle.summary,
        "last_run.json": bundle.last_run,
        "history.json": bundle.history,
    }


def _build_manifest(staging: Path, bundle: PublicBundle) -> dict[str, Any]:
    files = {}
    for filename in BUNDLE_FILES:
        files[filename] = {
            "sha256": _sha256_file(staging / filename),
            "generation_id": bundle.generation_id,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "generation_id": bundle.generation_id,
        "generated_at": bundle.generated_at,
        "files": files,
        "opportunity_count": len(bundle.opportunities),
        "history_count": len(bundle.history),
        "status": "published",
    }


def _snapshot_existing(output: Path, backup: Path) -> None:
    backup.mkdir(parents=True, exist_ok=True)
    for filename in (*BUNDLE_FILES, MANIFEST_FILE):
        source = output / filename
        if source.exists():
            shutil.copy2(source, backup / filename)


def _rollback(output: Path, backup: Path) -> None:
    if not backup.exists():
        return
    output.mkdir(parents=True, exist_ok=True)
    for filename in (*BUNDLE_FILES, MANIFEST_FILE):
        target = output / filename
        backup_file = backup / filename
        if backup_file.exists():
            os.replace(backup_file, target)
        elif target.exists():
            target.unlink()


def _payload_consistency_errors(payloads: dict[str, Any]) -> list[str]:
    errors = []
    opportunities = payloads.get("opportunities.json")
    summary = payloads.get("summary.json")
    history = payloads.get("history.json")
    last_run = payloads.get("last_run.json")
    if opportunities is not None and not isinstance(opportunities, list):
        errors.append("opportunities.json debe ser lista.")
    if summary is not None and not isinstance(summary, dict):
        errors.append("summary.json debe ser objeto.")
    if history is not None and not isinstance(history, list):
        errors.append("history.json debe ser lista.")
    if last_run is not None and not isinstance(last_run, dict):
        errors.append("last_run.json debe ser objeto.")
    if isinstance(opportunities, list):
        ids = [str(item.get("id")) for item in opportunities if isinstance(item, dict) and item.get("id")]
        if len(ids) != len(set(ids)):
            errors.append("opportunities.json contiene IDs duplicados.")
        if isinstance(summary, dict):
            total = summary.get("total_opportunities", summary.get("active_opportunities"))
            if isinstance(total, int) and total != len(opportunities):
                errors.append("summary no coincide con cantidad de opportunities.")
        if isinstance(history, list):
            visible = sum(item.get("currently_visible") is True for item in history if isinstance(item, dict))
            if visible and visible < len(opportunities):
                errors.append("history tiene menos visibles que opportunities.")
    return errors


def _validate_legacy_bundle(directory: Path) -> list[str]:
    payloads = {}
    errors = []
    for filename in BUNDLE_FILES:
        path = directory / filename
        if not path.exists():
            errors.append(f"falta {filename}")
        elif path.stat().st_size == 0:
            errors.append(f"{filename} esta vacio.")
        else:
            try:
                payloads[filename] = _load_json(path)
            except ValueError as error:
                errors.append(str(error))
    errors.extend(_payload_consistency_errors(payloads))
    return errors


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"JSON invalido en {path}: {error}") from error


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
