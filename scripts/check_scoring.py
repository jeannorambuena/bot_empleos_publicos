"""Run a local scoring smoke test with standard-library Python only."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from radar.config_loader import ConfigurationError, load_json, load_profile
from radar.normalize_opportunity import score_real_opportunity
from radar.scoring import calculate_match, match_level_for_score


def main() -> int:
    try:
        profile = load_profile(ROOT / "config" / "profile.example.json")
        opportunities = load_json(ROOT / "examples" / "sample_opportunities.json")
    except ConfigurationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not isinstance(opportunities, list) or not opportunities:
        print("ERROR: No hay oportunidades para evaluar.", file=sys.stderr)
        return 1

    print("id | title | score | level | reasons")
    print("-" * 112)

    for opportunity in opportunities:
        result = calculate_match(opportunity, profile)
        score = result["match_score"]
        level = result["match_level"]

        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
            print(f"ERROR: Score inválido para {opportunity.get('id', '<sin id>')}", file=sys.stderr)
            return 1
        if level != match_level_for_score(score):
            print(f"ERROR: Level inválido para {opportunity.get('id', '<sin id>')}", file=sys.stderr)
            return 1

        reasons = ", ".join(result["alert_reasons"]) or "-"
        print(f"{opportunity.get('id', '-')} | {opportunity.get('title', '-')} | {score} | {level} | {reasons}")

    clinical = calculate_match(
        {
            "title": "Técnico en enfermería para hospital",
            "source": "Empleos Públicos",
            "region": "Metropolitana",
        },
        profile,
    )
    hospital_technology = calculate_match(
        {
            "title": "Especialista CCTV y redes para hospital",
            "source": "Empleos Públicos",
            "region": "Metropolitana",
        },
        profile,
    )
    if clinical["match_level"] != "Descartada":
        print("ERROR: Un cargo clínico evidente no fue descartado.", file=sys.stderr)
        return 1
    if hospital_technology["match_level"] == "Descartada":
        print("ERROR: Un cargo tecnológico hospitalario fue descartado.", file=sys.stderr)
        return 1

    rm_no_salary = score_real_opportunity(
        {
            "title": "Profesional de redes",
            "source": "Empleos PÃºblicos",
            "region": "Metropolitana",
            "commune": "Santiago",
            "description": "Administracion de redes y servidores Linux.",
        },
        profile,
    )
    rm_low_salary = score_real_opportunity(
        {
            "title": "Profesional de redes",
            "source": "Empleos PÃºblicos",
            "region": "Metropolitana",
            "commune": "Santiago",
            "description": "Administracion de redes y servidores Linux. Renta bruta $1.500.000.",
        },
        profile,
    )
    maule_low_salary = score_real_opportunity(
        {
            "title": "Profesional de redes",
            "source": "Empleos PÃºblicos",
            "region": "Maule",
            "commune": "Talca",
            "description": "Administracion de redes y servidores Linux. Renta bruta $1.500.000.",
        },
        profile,
    )
    if rm_no_salary["economic_viability"] != "renta_no_informada" or rm_no_salary["match_score"] <= 0:
        print("ERROR: Santiago/RM sin renta debe quedar visible y marcado para revisar renta.", file=sys.stderr)
        return 1
    if rm_low_salary["economic_viability"] != "bajo_piso" or rm_low_salary["economic_priority_adjustment"] >= 0:
        print("ERROR: Santiago/RM bajo piso debe bajar prioridad.", file=sys.stderr)
        return 1
    if maule_low_salary.get("economic_viability") is not None:
        print("ERROR: Maule no debe recibir castigo economico Santiago/RM.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
