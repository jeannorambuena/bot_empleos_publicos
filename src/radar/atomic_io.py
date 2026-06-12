"""Small cross-platform helpers for durable JSON file replacement."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Callable


ReplaceFunc = Callable[[Path, Path], None]


def stable_json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write_bytes(
    path: Path,
    payload: bytes,
    *,
    replace_func: ReplaceFunc | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temp_path.open("wb") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        (replace_func or os.replace)(temp_path, path)
        _fsync_directory(path.parent)
    except Exception:
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise


def atomic_write_json(
    path: Path,
    payload: Any,
    *,
    replace_func: ReplaceFunc | None = None,
) -> None:
    atomic_write_bytes(path, stable_json_bytes(payload), replace_func=replace_func)


def _fsync_directory(path: Path) -> None:
    if os.name == "nt":
        return
    try:
        directory_fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
