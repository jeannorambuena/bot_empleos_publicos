"""Validate and summarize the P1 source dry-run batch."""

from check_priority_source_common import check_source


SOURCES = {
    "talca": "Municipalidad de Talca",
    "slep_colchagua": "SLEP Colchagua",
    "slep_los_cerezos": "SLEP Los Cerezos",
}


def main() -> int:
    errors = []
    rows = []
    for key, source_name in SOURCES.items():
        source_errors, diagnostics = check_source(key, source_name)
        errors.extend(source_errors)
        if diagnostics:
            rows.append(diagnostics)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Resumen batch dry-run P1")
    print("------------------------")
    for item in rows:
        counts = item["status_counts"]
        print(
            f"{item['source']}: detectadas={item['publications_detected']}, "
            f"open_confirmed={counts['open_confirmed']}, closed={counts['closed']}, "
            f"manual_review={counts['manual_review']}, external_private={item['external_private']}, "
            f"documentos={item['documents_detected']}, fechas_confiables={item['reliable_closing_dates']}, "
            f"privacidad={item['privacy_risk']}, siguiente={item['recommendation']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
