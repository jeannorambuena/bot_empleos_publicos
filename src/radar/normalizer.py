"""Text normalization helpers used by search and scoring."""

from __future__ import annotations

import re
import unicodedata


def lowercase_text(value: object) -> str:
    """Return a lowercase string, treating None as an empty value."""
    return "" if value is None else str(value).lower()


def remove_accents(value: object) -> str:
    """Remove diacritical marks so searches are accent-insensitive."""
    text = "" if value is None else str(value)
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def clean_spaces(value: object) -> str:
    """Collapse repeated whitespace and trim surrounding spaces."""
    return re.sub(r"\s+", " ", "" if value is None else str(value)).strip()


def prepare_search_text(value: object) -> str:
    """Normalize text for case-insensitive and accent-insensitive matching."""
    return clean_spaces(remove_accents(lowercase_text(value)))
