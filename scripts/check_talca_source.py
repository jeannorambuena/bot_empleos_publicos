from check_priority_source_common import check_source

errors, diagnostics = check_source("talca", "Municipalidad de Talca")
for error in errors:
    print(f"ERROR: {error}")
if not errors:
    print("OK: dry-run Talca válido, incluso con cero oportunidades trazables.")
raise SystemExit(1 if errors else 0)
