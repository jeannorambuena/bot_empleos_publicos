# Entrega final del MVP

## Que hace el sistema

Radar Laboral Publico Chile captura oportunidades publicas, las normaliza, prioriza
para un perfil profesional y publica una vista estatica revisable. Incluye historial,
feedback humano, reporte semanal, sanitizacion comun y preview seguro de Telegram.

El MVP es multi-fuente controlado: no todo adaptador local publica. Cada fuente debe
probar trazabilidad, vigencia y privacidad antes de entrar al dashboard.

## Estado de fuentes

- **Activa publicada:** Empleos Publicos alimenta el flujo principal.
- **Publicada controladamente:** Municipalidad de Rancagua publica solo registros
  municipales `open_confirmed`, sanitizados y con cierre confiable.
- **Dry-run:** Curico, Molina, GORE Maule, Rancagua, Talca, SLEP Colchagua y SLEP
  Los Cerezos conservan artefactos locales auditables bajo `output/sources/`.
- **Solo catalogadas:** las candidatas restantes viven en
  `data/source_candidates.json`; no tienen scraper ni publicacion automatica.

Estados operativos:

- `active_published`: fuente estable del flujo publico.
- `tested_publishable_controlled`: fuente promovida con reglas limitadas.
- `dry_run_only`: captura local que aun no publica.
- `manual_review_only`: requiere revision humana; no se promueve automaticamente.
- `blocked`: se mantiene separada del radar laboral o no debe avanzar.

Consulta `docs/source-status-matrix.md` para la matriz resumida.

## Operacion local

```powershell
python scripts/fetch_empleos_publicos.py
python scripts/check_real_data.py
python scripts/build_public_data_from_real.py
python scripts/check_release_ready.py
python -m http.server 8000 --directory public
```

Revisa `http://localhost:8000`. Antes de merge, el comando unico de cierre es:

```powershell
python scripts/check_release_ready.py
```

El check valida datos publicos, dashboard, catalogo, configuracion, sanitizacion,
dry-runs P1, preview Telegram y reglas de promocion de fuentes nuevas.

## GitHub Pages

La carpeta publicada es `public/`. Para revisar Pages, valida localmente, fusiona
solo un PR aprobado y comprueba la URL configurada en GitHub Pages. No publiques
`output/`, `.env`, logs ni artefactos locales. Consulta `docs/github-pages.md`.

## Privacidad

La sanitizacion comun redacta RUN/RUT completos y parciales, datos personales
residuales y tablas extensas de resultados. Los checks revisan campos visibles,
evidencia y nombres de documentos. Un resultado historico o nomina sensible debe
permanecer local, sanitizado y sujeto a revision humana.

## Telegram

Telegram real permanece desactivado por defecto. El flujo local permitido es:

```powershell
python scripts/build_telegram_preview.py
python scripts/check_telegram_preview.py
python scripts/simulate_telegram_policy.py
```

El envio real requiere credenciales y activacion deliberada. No actives
`TELEGRAM_AUTO_ENABLED=true` sin revisar preview, logs y rollback documentado en
`docs/telegram-alerts.md`.

## Despues del MVP

Una version SaaS o para terceros necesita perfiles aislados por usuario, hosting
propio cuando crezca el volumen, control de acceso, almacenamiento privado,
observabilidad, gestion de consentimiento, soporte operativo y una politica formal
de retencion de datos. El MVP no promete empleos: monitorea y prioriza convocatorias.
