"""Conservative dry-run adapter for SLEP Colchagua."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests


SOURCE_ID = "slep-colchagua"
SOURCE_NAME = "SLEP Colchagua"
TIMEOUT_SECONDS = 20
USER_AGENT = "RadarLaboralPublicoChile/0.2 (dry-run source audit)"


def fetch_candidates(discovery_url: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Report TLS access failures instead of bypassing certificate validation."""
    diagnostics = {
        "source_id": SOURCE_ID,
        "source": SOURCE_NAME,
        "listing_url": discovery_url,
        "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "publications_detected": 0,
        "source_links_detected": 0,
        "status_counts": {"open_confirmed": 0, "closed": 0, "manual_review": 0},
        "external_private": 0,
        "documents_detected": 0,
        "reliable_closing_dates": 0,
        "privacy_risk": "low",
        "recommendation": "manual_review_only",
        "notes": "No se omite validación TLS. El dry-run no inventa registros si la sede no es consultable de forma segura.",
    }
    try:
        response = requests.get(discovery_url, timeout=TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
    except requests.exceptions.SSLError as error:
        diagnostics["access_status"] = "tls_error"
        diagnostics["error"] = f"Validación TLS fallida: {error}"
        return [], diagnostics
    except requests.RequestException as error:
        diagnostics["access_status"] = "request_error"
        diagnostics["error"] = f"Consulta oficial fallida: {error}"
        return [], diagnostics
    diagnostics["access_status"] = "ok"
    diagnostics["http_status"] = response.status_code
    diagnostics["notes"] = "La sede oficial respondió; este lote conserva diagnóstico sin promover publicaciones."
    return [], diagnostics
