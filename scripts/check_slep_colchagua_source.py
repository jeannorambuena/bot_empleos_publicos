from check_priority_source_common import check_source

errors, diagnostics = check_source("slep_colchagua", "SLEP Colchagua")
for error in errors:
    print(f"ERROR: {error}")
if not errors:
    print("OK: dry-run SLEP Colchagua válido; los fallos TLS quedan como diagnóstico conservador.")
raise SystemExit(1 if errors else 0)
