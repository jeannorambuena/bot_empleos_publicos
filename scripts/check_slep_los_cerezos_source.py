from check_priority_source_common import check_source

errors, diagnostics = check_source("slep_los_cerezos", "SLEP Los Cerezos")
for error in errors:
    print(f"ERROR: {error}")
if not errors:
    print("OK: dry-run SLEP Los Cerezos válido; referencias detectadas permanecen manual_review.")
raise SystemExit(1 if errors else 0)
