"""Conservative sanitization for local dry-run source opportunities."""

from __future__ import annotations

import copy
import re
from typing import Any


RUT_REDACTED = "[RUT_REDACTADO]"
NAME_REDACTED = "[NOMBRE_REDACTADO]"
PERSONAL_DATA_REDACTED = "[DATO_PERSONAL_REDACTADO]"
PUBLICABLE_TEXT_FIELDS = (
    "title",
    "description",
    "status_reason",
    "manual_review_reason",
)

_RUT_VALUE = r"(?:\d{1,2}(?:\.\d{3}){2}|[0-9Xx]{7,9})\s*-\s*[0-9KkXx]"
_PARTIAL_RUT_VALUE = r"(?:\d{1,2}(?:\.\d{3})?\.[0-9]?[Xx]{2,3}|[0-9]{5,8}[Xx]{1,3})\s*(?:-\s*[0-9KkXx])?"
_RUT_LABEL = r"(?:RUN|RUT)\s*(?:N\s*[°ºo.]?\s*)?"
_LABELED_RUT_PATTERN = re.compile(rf"\b{_RUT_LABEL}:?\s*(?:{_RUT_VALUE}|{_PARTIAL_RUT_VALUE})", re.IGNORECASE)
_RUT_PATTERN = re.compile(rf"(?<![0-9A-Za-z]){_RUT_VALUE}(?![0-9A-Za-z])", re.IGNORECASE)
_PARTIAL_RUT_PATTERN = re.compile(rf"(?<![0-9A-Za-z]){_PARTIAL_RUT_VALUE}(?![0-9A-Za-z])", re.IGNORECASE)
_BARE_IDENTIFIER_PATTERN = re.compile(r"(?<!\d)\d{7,9}(?!\d)")
_RESIDUAL_RUT_LABEL_PATTERN = re.compile(r"\b(?:RUN|RUT)\b(?!_REDACTADO)", re.IGNORECASE)
_RESULT_NAME_PATTERN = re.compile(
    r"\b(?:nombramiento\s+de|persona\s+seleccionada|seleccionad[oa])\s*:?\s+"
    r"(?P<name>(?!\[)[A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ.' -]{4,80})"
    r"(?=\s+(?:RUN|RUT)\b|[,;.]|$)",
    re.IGNORECASE,
)
_HONORIFIC_NAME_PATTERN = re.compile(
    r"\b(?:SRA|SRTA|SR)\.?\s+(?P<name>(?!\[)[A-ZÁÉÍÓÚÜÑ][A-Za-zÁÉÍÓÚÜÑáéíóúüñ.' -]{4,80})"
    r"(?=\s+(?:RUN|RUT)\b)",
    re.IGNORECASE,
)
_RESULT_MARKER_PATTERN = re.compile(
    r"\b(?:resultado|n[oó]mina|seleccionad[oa]s?|nombramiento|adjudicad[oa]s?)\b",
    re.IGNORECASE,
)


def sanitize_text(text: str) -> str:
    """Redact personal data from a publicable text without changing its metadata."""
    if not isinstance(text, str) or not text:
        return text
    sensitive_identifiers = _count_sensitive_identifiers(text)
    sanitized = _HONORIFIC_NAME_PATTERN.sub(_replace_name, text)
    sanitized = _RESULT_NAME_PATTERN.sub(_replace_name, sanitized)
    sanitized = _LABELED_RUT_PATTERN.sub(RUT_REDACTED, sanitized)
    sanitized = _RUT_PATTERN.sub(RUT_REDACTED, sanitized)
    sanitized = _PARTIAL_RUT_PATTERN.sub(RUT_REDACTED, sanitized)
    sanitized = _RESIDUAL_RUT_LABEL_PATTERN.sub(PERSONAL_DATA_REDACTED, sanitized)
    if (sensitive_identifiers >= 3 and _RESULT_MARKER_PATTERN.search(text)) or _looks_like_results_table(text):
        return PERSONAL_DATA_REDACTED
    return sanitized


def sanitize_document_name(text: str) -> str:
    """Sanitize a visible document label while preserving its official URL elsewhere."""
    return sanitize_text(text)


def sanitize_opportunity(item: dict[str, Any]) -> dict[str, Any]:
    """Return a sanitized copy of one normalized source opportunity."""
    sanitized = copy.deepcopy(item)
    for field in PUBLICABLE_TEXT_FIELDS:
        value = sanitized.get(field)
        if isinstance(value, str):
            sanitized[field] = sanitize_text(value)
    evidence = sanitized.get("evidence")
    if isinstance(evidence, list):
        sanitized["evidence"] = [sanitize_text(value) if isinstance(value, str) else value for value in evidence]
    documents = sanitized.get("document_urls")
    if isinstance(documents, list):
        for document in documents:
            if isinstance(document, dict) and isinstance(document.get("name"), str):
                document["name"] = sanitize_document_name(document["name"])
    return sanitized


def has_sensitive_personal_data(text: str) -> bool:
    """Return whether publicable text still contains a dangerous personal-data pattern."""
    if not isinstance(text, str) or not text:
        return False
    return bool(
        _LABELED_RUT_PATTERN.search(text)
        or _RUT_PATTERN.search(text)
        or _PARTIAL_RUT_PATTERN.search(text)
        or _RESIDUAL_RUT_LABEL_PATTERN.search(text)
        or _looks_like_results_table(text)
    )


def sensitive_personal_data_reasons(text: str) -> list[str]:
    """Describe residual sensitive patterns for clear validation errors."""
    if not isinstance(text, str) or not text:
        return []
    reasons = []
    if _LABELED_RUT_PATTERN.search(text) or _RESIDUAL_RUT_LABEL_PATTERN.search(text):
        reasons.append("etiqueta RUN/RUT visible")
    if _RUT_PATTERN.search(text):
        reasons.append("RUN/RUT visible")
    if _PARTIAL_RUT_PATTERN.search(text):
        reasons.append("RUN/RUT parcialmente visible")
    if _looks_like_results_table(text):
        reasons.append("tabla extensa de resultados")
    return reasons


def _replace_name(match: re.Match[str]) -> str:
    return match.group(0).replace(match.group("name"), NAME_REDACTED)


def _count_sensitive_identifiers(text: str) -> int:
    return len(_RUT_PATTERN.findall(text)) + len(_PARTIAL_RUT_PATTERN.findall(text))


def _looks_like_results_table(text: str) -> bool:
    identifiers = _count_sensitive_identifiers(text) + len(_BARE_IDENTIFIER_PATTERN.findall(text))
    return bool(_RESULT_MARKER_PATTERN.search(text) and identifiers >= 3)
