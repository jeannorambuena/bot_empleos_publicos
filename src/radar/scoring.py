"""Initial configurable matching engine for public job opportunities."""

from __future__ import annotations

from typing import Any, Iterable

from .normalizer import prepare_search_text


POSITIVE_KEYWORD_POINTS = 12
PRIORITY_REGION_POINTS = 18
PROFILE_AREA_POINTS = 14
PROFILE_ZONE_POINTS = 8
KNOWN_SOURCE_POINTS = 4
MAX_SCORE = 100


def match_level_for_score(score: int) -> str:
    """Map a score to the public match levels documented by the project."""
    if score >= 85:
        return "Alta"
    if score >= 70:
        return "Media"
    if score >= 50:
        return "Baja"
    return "Descartada"


def _normalized_values(values: Iterable[object]) -> set[str]:
    return {prepare_search_text(value) for value in values if prepare_search_text(value)}


def _opportunity_search_text(opportunity: dict[str, Any]) -> str:
    values = [
        opportunity.get("title"),
        opportunity.get("institution"),
        opportunity.get("source"),
        opportunity.get("region"),
        opportunity.get("commune"),
        opportunity.get("area"),
        opportunity.get("description"),
        " ".join(str(tag) for tag in opportunity.get("tags", [])),
    ]
    return prepare_search_text(" ".join(str(value) for value in values if value))


def _matching_keywords(search_text: str, keywords: Iterable[object]) -> list[str]:
    matches = []
    for keyword in keywords:
        normalized_keyword = prepare_search_text(keyword)
        if normalized_keyword and normalized_keyword in search_text:
            matches.append(str(keyword))
    return matches


def calculate_match(opportunity: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """Calculate an initial score and explain the resulting match.

    Negative keywords discard an opportunity immediately. Positive keywords and
    profile context then add points up to the public maximum of 100.
    """
    search_text = _opportunity_search_text(opportunity)
    matched_keywords = _matching_keywords(search_text, profile.get("positive_keywords", []))
    excluded_keywords = _matching_keywords(search_text, profile.get("negative_keywords", []))

    if excluded_keywords:
        return {
            "match_score": 0,
            "match_level": "Descartada",
            "alert_reasons": ["Descartada por palabra negativa"],
            "matched_keywords": matched_keywords,
            "excluded_keywords": excluded_keywords,
        }

    score = len(matched_keywords) * POSITIVE_KEYWORD_POINTS
    reasons = []

    region = prepare_search_text(opportunity.get("region"))
    priority_regions = _normalized_values(profile.get("priority_regions", []))
    if region and region in priority_regions:
        score += PRIORITY_REGION_POINTS
        reasons.append("Región priorizada")

    area = prepare_search_text(opportunity.get("area"))
    profile_areas = _normalized_values(profile.get("areas", []))
    if area and area in profile_areas:
        score += PROFILE_AREA_POINTS
        reasons.append("Área de interés")

    commune = prepare_search_text(opportunity.get("commune"))
    profile_zones = _normalized_values(profile.get("areas_of_interest", []))
    if commune and commune in profile_zones:
        score += PROFILE_ZONE_POINTS
        reasons.append("Zona de interés")

    if opportunity.get("source"):
        score += KNOWN_SOURCE_POINTS
        reasons.append("Fuente disponible")

    score = min(score, MAX_SCORE)
    level = match_level_for_score(score)

    if matched_keywords:
        reasons.insert(0, "Palabras clave positivas")
    if level == "Alta":
        reasons.insert(0, "Alta coincidencia")
    if score >= profile.get("minimum_alert_score", MAX_SCORE + 1):
        reasons.append("Supera puntaje mínimo de alerta")

    return {
        "match_score": score,
        "match_level": level,
        "alert_reasons": reasons,
        "matched_keywords": matched_keywords,
        "excluded_keywords": excluded_keywords,
    }
