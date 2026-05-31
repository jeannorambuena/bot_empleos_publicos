"""Load and validate community configuration files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROFILE_REQUIRED_KEYS = {
    "profile_name",
    "priority_regions",
    "areas",
    "positive_keywords",
    "negative_keywords",
    "minimum_alert_score",
    "areas_of_interest",
}


class ConfigurationError(ValueError):
    """Raised when a JSON configuration file is missing required information."""


def load_json(path: str | Path) -> Any:
    """Load a UTF-8 JSON file and provide a clear error when it is invalid."""
    config_path = Path(path)
    try:
        with config_path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError as error:
        raise ConfigurationError(f"No existe el archivo de configuración: {config_path}") from error
    except json.JSONDecodeError as error:
        raise ConfigurationError(f"JSON inválido en {config_path}: {error}") from error


def validate_required_keys(data: dict[str, Any], required_keys: set[str], label: str) -> None:
    """Ensure a configuration object contains every required key."""
    missing = sorted(required_keys - data.keys())
    if missing:
        raise ConfigurationError(f"Faltan claves mínimas en {label}: {', '.join(missing)}")


def validate_profile(profile: Any) -> dict[str, Any]:
    """Validate the minimum profile contract used by the scoring engine."""
    if not isinstance(profile, dict):
        raise ConfigurationError("El perfil debe ser un objeto JSON.")

    validate_required_keys(profile, PROFILE_REQUIRED_KEYS, "el perfil")

    list_keys = (
        "priority_regions",
        "areas",
        "positive_keywords",
        "negative_keywords",
        "areas_of_interest",
    )
    for key in list_keys:
        if not isinstance(profile[key], list):
            raise ConfigurationError(f"La clave '{key}' debe ser una lista.")

    minimum_score = profile["minimum_alert_score"]
    if not isinstance(minimum_score, int) or isinstance(minimum_score, bool):
        raise ConfigurationError("La clave 'minimum_alert_score' debe ser un número entero.")
    if not 0 <= minimum_score <= 100:
        raise ConfigurationError("La clave 'minimum_alert_score' debe estar entre 0 y 100.")

    return profile


def load_profile(path: str | Path = "config/profile.example.json") -> dict[str, Any]:
    """Load the default example profile or another compatible profile."""
    return validate_profile(load_json(path))
