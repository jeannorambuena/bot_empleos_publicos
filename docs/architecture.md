# Arquitectura tecnica

Radar Laboral Publico Chile es un MVP funcional validado localmente. Su
arquitectura prioriza trazabilidad, separacion entre datos publicables y artefactos
locales, y controles antes de automatizar fuentes o alertas.

No es una plataforma comercial completa ni un SaaS multiusuario. Es un radar
estatico y auditable que usa fuentes publicas, genera datos normalizados y permite
revision humana antes de ampliar automatizaciones sensibles.

## Componentes principales

| Componente | Ruta | Responsabilidad |
| --- | --- | --- |
| Scripts de captura | `scripts/fetch_*.py` | Consultar fuentes publicas o generar dry-runs locales. |
| Logica reutilizable | `src/radar/` | Adaptadores, sanitizacion, scoring y utilidades compartidas. |
| Datos de trabajo | `data/` | Capturas reales locales, datos normalizados y catalogos. |
| Datos publicos | `public/data/` | JSON versionables consumidos por el dashboard. |
| Dashboard estatico | `public/` | Interfaz publicable por GitHub Pages o servidor local. |
| Documentacion | `docs/` | Arquitectura, operacion, seguridad, fuentes y checklist. |
| Artefactos locales | `output/` | Reportes, previews y dry-runs no versionables. |
| Workflows | `.github/workflows/` | Automatizacion controlada de refresco y publicacion. |

## Scripts de captura

La fuente activa principal es Empleos Publicos:

```powershell
python scripts/fetch_empleos_publicos.py
```

Ese script captura oportunidades publicas, las normaliza y deja salidas locales
que luego pueden validarse y convertirse a `public/data`.

Las fuentes municipales y territoriales se manejan como adaptadores aislados. Por
ejemplo:

```powershell
python scripts/fetch_curico.py
python scripts/fetch_molina.py
python scripts/fetch_romeral.py
python scripts/fetch_rauco.py
python scripts/fetch_rancagua.py
python scripts/fetch_priority_sources.py
```

Esos flujos escriben en `output/sources/` y no publican automaticamente en el
dashboard. Rancagua conserva un dry-run auditable, pero puede aportar registros
municipales controlados cuando pasan las reglas documentadas de promocion.

## Normalizacion

Cada adaptador transforma la fuente original a un contrato comun antes de cualquier
publicacion. La normalizacion busca que oportunidades de portales distintos tengan
campos comparables: identificador, titulo, institucion, region, comuna, fechas,
URL oficial, evidencia, estado y metadatos de revision.

Referencias:

- `docs/source-contract.md`
- `docs/data-contract.md`

## Validacion

El proyecto usa validadores especificos y un check compuesto de release.

Validaciones principales:

```powershell
python scripts/check_real_data.py
python scripts/check_public_data.py
python scripts/check_pages_ready.py
python scripts/check_source_candidates.py
python scripts/check_sources_config.py
python scripts/check_source_sanitization.py
python scripts/check_priority_sources.py
python scripts/check_telegram_preview.py
python scripts/check_release_ready.py
```

El comando final obligatorio es:

```powershell
python scripts/check_release_ready.py
```

Resultado esperado:

```text
OK: release MVP listo
```

## Sanitizacion

La sanitizacion comun reduce el riesgo de publicar datos personales. Los checks
buscan RUN/RUT visibles, variantes parcialmente enmascaradas, nombres de documentos
riesgosos y tablas extensas de resultados.

La regla operativa es conservadora: si una fuente contiene nominas, resultados,
RUN/RUT, anexos sensibles o evidencia insuficiente de vigencia, queda local como
dry-run o `manual_review`.

## Scoring

El scoring asigna prioridad a las oportunidades publicables segun coincidencia con
criterios del perfil, territorio, palabras clave, fuente, vigencia y proximidad de
cierre. El dashboard muestra niveles operativos para facilitar revision, no para
garantizar postulaciones ni decisiones automaticas.

Referencias:

- `docs/scoring.md`
- `docs/scoring-calibration.md`

## public/data

`public/data/` es la frontera publica del sistema. Los archivos principales son:

- `opportunities.json`
- `summary.json`
- `last_run.json`
- `history.json`
- `manifest.json`
- `telegram_alert_state.json`

Solo deben entrar oportunidades publicas normalizadas, sanitizadas y trazables. Los
dry-runs, reportes locales, logs, datos crudos y secretos permanecen fuera de esta
carpeta.

La publicacion de `opportunities`, `summary`, `last_run` e `history` se trata como
un bundle transaccional logico: se prepara en staging, se valida, se respalda el
bundle anterior, se promueve con reemplazos individuales y se usa rollback si falla
un reemplazo intermedio. `manifest.json` se promueve al final e incluye
`generation_id`, `generated_at`, conteos y checksums SHA-256. Esto no promete
atomicidad multiarchivo absoluta del sistema operativo; ofrece consistencia practica
con staging, manifest, backup y rollback.

## Dashboard estatico

`public/index.html` y sus assets consumen los JSON publicos mediante JavaScript. El
dashboard puede levantarse localmente con:

```powershell
python -m http.server 8000 --directory public
```

Tambien puede publicarse como sitio estatico mediante GitHub Pages cuando el release
check pasa y los datos fueron revisados.

## GitHub Actions

La automatizacion de GitHub Actions refresca datos reales bajo controles definidos:

- instala dependencias desde `requirements.txt`;
- ejecuta captura y validaciones;
- regenera JSON publicos solo cuando corresponde;
- no versiona `output/`, `.env`, logs ni secretos;
- mantiene Telegram real desactivado salvo activacion explicita.

Referencia: `docs/github-actions-refresh.md`.

## Telegram preview y envio controlado

Telegram funciona en tres capas:

1. Preview local de mensajes candidatos.
2. Simulacion de politica automatica sin envio real.
3. Envio real solo con secrets, variables y ejecucion explicita.

Comandos de control:

```powershell
python scripts/build_telegram_preview.py
python scripts/check_telegram_preview.py
python scripts/simulate_telegram_policy.py
```

Por defecto no hay envio automatico. Telegram real requiere `TELEGRAM_BOT_TOKEN`,
`TELEGRAM_CHAT_ID` y una decision operacional deliberada.

`telegram_alert_state.json` tiene escritura atomica individual. Telegram es un
efecto externo: si Telegram confirma envio y luego falla commit o push, no existe
transaccion distribuida. El sistema registra `last_alert_batch_id` para trazabilidad
y mantiene una garantia best-effort idempotent con anti-duplicados y limite diario.

## Fuentes locales dry-run

Las fuentes locales o territoriales no promovidas permanecen en `output/sources/`.
Su objetivo es diagnosticar estructura, trazabilidad, vigencia y riesgo de
privacidad sin contaminar `public/data`.

Una fuente solo puede pasar a publicacion controlada si:

- usa fuente institucional publica;
- tiene URL oficial y evidencia trazable;
- entrega estado y fecha de cierre confiables;
- no contiene datos personales visibles;
- pasa validaciones de contrato y sanitizacion;
- no duplica indebidamente Empleos Publicos;
- queda documentada con decision explicita de promocion.

Estado detallado: `docs/local-sources-status.md`.
