"""Economic viability rules for Santiago/RM opportunities."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from .normalizer import prepare_search_text
from .scoring import match_level_for_score


DEFAULT_SANTIAGO_THRESHOLDS = {
    "minimum_net": 1_600_000,
    "recommended_net": 1_800_000,
    "good_net": 2_000_000,
    "minimum_gross": 2_000_000,
    "recommended_gross": 2_250_000,
    "good_gross": 2_500_000,
}
SANTIAGO_LOW_SALARY_PENALTY = 18
SANTIAGO_ECONOMIC_NOTE = (
    "Para Santiago/RM se considera un piso economico por arriendo, pension, "
    "transporte y viajes de fin de semana."
)
SANTIAGO_REVIEW_MESSAGE = "Revisar renta antes de postular"

AMOUNT_PATTERN = re.compile(r"\$\s*([0-9][0-9.\s]{4,}(?:,[0-9]+)?)")
SALARY_FIELDS = (
    "salary",
    "salary_text",
    "salary_gross",
    "salary_net",
    "gross_salary",
    "net_salary",
    "renta",
    "renta_text",
    "renta_bruta",
    "renta_liquida",
    "sueldo",
    "sueldo_bruto",
    "sueldo_liquido",
    "remuneracion",
    "remuneration",
)


def apply_santiago_economic_viability(
    opportunity: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Apply Santiago/RM economic labels and priority adjustment."""
    item = deepcopy(opportunity)
    if not is_santiago_rm_opportunity(item):
        item["economic_viability"] = None
        item["economic_label"] = None
        item["economic_alert"] = None
        item["economic_review_required"] = False
        item["economic_priority_adjustment"] = 0
        return item

    thresholds = _thresholds_from_profile(profile)
    salary = detect_salary(item)
    status, label = _classify_salary(salary, thresholds)
    item["economic_viability"] = status
    item["economic_label"] = label
    item["economic_note"] = SANTIAGO_ECONOMIC_NOTE
    item["economic_review_required"] = status == "renta_no_informada"
    item["economic_priority_adjustment"] = 0
    item["santiago_salary_floor"] = {
        "minimum_net": thresholds["minimum_net"],
        "recommended_net": thresholds["recommended_net"],
        "good_net": thresholds["good_net"],
        "minimum_gross": thresholds["minimum_gross"],
        "recommended_gross": thresholds["recommended_gross"],
        "good_gross": thresholds["good_gross"],
    }
    if salary:
        item["salary_estimate"] = salary

    reasons = list(item.get("alert_reasons") or [])
    if label not in reasons:
        reasons.append(label)

    if status == "renta_no_informada":
        item["economic_alert"] = "Revisar renta Santiago"
        if SANTIAGO_REVIEW_MESSAGE not in reasons:
            reasons.append(SANTIAGO_REVIEW_MESSAGE)
    elif status == "bajo_piso":
        item["economic_alert"] = "Bajo piso economico Santiago"
        current_score = int(item.get("match_score", 0))
        item["pre_economic_match_score"] = current_score
        item["economic_priority_adjustment"] = -SANTIAGO_LOW_SALARY_PENALTY
        adjusted = max(0, current_score - SANTIAGO_LOW_SALARY_PENALTY)
        item["match_score"] = adjusted
        item["match_level"] = match_level_for_score(adjusted)
    else:
        item["economic_alert"] = "Cumple piso Santiago"

    item["alert_reasons"] = reasons
    return item


def is_santiago_rm_opportunity(opportunity: dict[str, Any]) -> bool:
    """Detect Santiago/RM from region, commune, title, listing URL and source URL."""
    values = [
        opportunity.get("region"),
        opportunity.get("commune"),
        opportunity.get("title"),
        opportunity.get("listing_url"),
        opportunity.get("source_url"),
    ]
    text = prepare_search_text(" ".join(str(value) for value in values if value))
    if not text:
        return False
    return any(
        marker in text
        for marker in (
            "metropolitana",
            "region metropolitana",
            "metropolitana de santiago",
            "santiago",
        )
    )


def detect_salary(opportunity: dict[str, Any]) -> dict[str, Any] | None:
    """Detect an approximate monthly gross/net salary when present."""
    candidates: list[dict[str, Any]] = []
    for field in SALARY_FIELDS:
        if field in opportunity:
            candidates.extend(_salary_candidates(opportunity.get(field), field=field))

    text_fields = [
        opportunity.get("title"),
        opportunity.get("description"),
        " ".join(str(tag) for tag in opportunity.get("tags", [])),
    ]
    candidates.extend(_salary_candidates(" ".join(str(value) for value in text_fields if value), field="text"))
    monthly_candidates = [candidate for candidate in candidates if candidate["amount"] >= 500_000]
    if not monthly_candidates:
        return None

    preferred = sorted(
        monthly_candidates,
        key=lambda candidate: (
            candidate["kind"] not in {"gross", "net"},
            candidate["source_field"] == "text",
            -candidate["amount"],
        ),
    )[0]
    return preferred


def _thresholds_from_profile(profile: dict[str, Any]) -> dict[str, int]:
    raw = profile.get("santiago_economic_viability")
    thresholds = dict(DEFAULT_SANTIAGO_THRESHOLDS)
    if isinstance(raw, dict):
        for key in thresholds:
            value = raw.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                thresholds[key] = value
    return thresholds


def _classify_salary(salary: dict[str, Any] | None, thresholds: dict[str, int]) -> tuple[str, str]:
    if not salary:
        return "renta_no_informada", "Santiago: revisar renta"
    amount = int(salary["amount"])
    kind = salary["kind"]
    if _meets(amount, kind, thresholds["good_gross"], thresholds["good_net"]):
        return "cumple_bueno", "Santiago: sueldo bueno"
    if _meets(amount, kind, thresholds["recommended_gross"], thresholds["recommended_net"]):
        return "cumple_recomendable", "Santiago: sueldo recomendable"
    if _meets(amount, kind, thresholds["minimum_gross"], thresholds["minimum_net"]):
        return "viable_justo", "Santiago: viable justo"
    return "bajo_piso", "Santiago: bajo piso economico"


def _meets(amount: int, kind: str, gross_threshold: int, net_threshold: int) -> bool:
    threshold = net_threshold if kind == "net" else gross_threshold
    return amount >= threshold


def _salary_candidates(value: Any, *, field: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, int) and not isinstance(value, bool):
        return [_candidate(value, field=field, text=field)]
    if isinstance(value, float):
        return [_candidate(int(value), field=field, text=field)]
    if isinstance(value, dict):
        candidates = []
        for key, child in value.items():
            candidates.extend(_salary_candidates(child, field=f"{field}.{key}"))
        return candidates
    if isinstance(value, list):
        candidates = []
        for index, child in enumerate(value):
            candidates.extend(_salary_candidates(child, field=f"{field}[{index}]"))
        return candidates

    text = str(value)
    return [
        _candidate(_parse_amount(match.group(1)), field=field, text=text)
        for match in AMOUNT_PATTERN.finditer(text)
    ]


def _candidate(amount: int, *, field: str, text: str) -> dict[str, Any]:
    lowered = prepare_search_text(f"{field} {text}")
    kind = "unknown"
    if "liquid" in lowered or "liquido" in lowered or "net" in lowered:
        kind = "net"
    elif "brut" in lowered or "gross" in lowered:
        kind = "gross"
    return {
        "amount": amount,
        "kind": kind,
        "source_field": field,
    }


def _parse_amount(raw: str) -> int:
    normalized = raw.replace(".", "").replace(" ", "")
    if "," in normalized:
        normalized = normalized.split(",", maxsplit=1)[0]
    return int(normalized)
