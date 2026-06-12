# Operacion

Guia de operacion local y automatizada para Radar Laboral Publico Chile. Los
comandos se ejecutan desde la raiz del repositorio.

## Preparacion local en Windows

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

No copiar secretos a archivos versionados. `.env.example` es solo referencia; `.env`
debe permanecer local e ignorado.

## Levantar dashboard local

```powershell
python -m http.server 8000 --directory public
```

Abrir:

```text
http://localhost:8000
```

Detener con `Ctrl+C`.

## Refrescar datos reales

Flujo manual completo:

```powershell
python scripts/fetch_empleos_publicos.py
python scripts/check_real_data.py
python scripts/build_public_data_from_real.py
python scripts/check_release_ready.py
```

`fetch_empleos_publicos.py` escribe primero una captura staging bajo
`data/staging/empleos_publicos/`. Solo reemplaza el normalizado vigente si aprueba
completitud regional, ausencia de errores, estructura, cantidad minima y control de
caida de volumen.

El umbral predeterminado bloquea una disminucion superior a 35% respecto del ultimo
normalizado valido. Puede ajustarse con `RADAR_CAPTURE_MAX_DROP_RATIO` sin depender
de una cifra rigida de oportunidades actuales.

Este flujo puede modificar `public/data/` porque regenera los datos publicos, pero
solo despues de que la captura principal fue promovida como integra. Debe ejecutarse
cuando el objetivo de trabajo autoriza refrescar datos.

La generacion publica usa publicacion transaccional logica: prepara
`opportunities.json`, `summary.json`, `last_run.json`, `history.json` y
`manifest.json` en staging; valida JSON, conteos, checksums e identidad de
generacion; respalda el bundle vigente; promueve `manifest.json` al final; y hace
rollback del conjunto si falla un reemplazo intermedio.

## Validar release

Comando unico de cierre:

```powershell
python scripts/check_release_ready.py
```

Resultado esperado:

```text
OK: release MVP listo
```

El comando agrupa validaciones de datos publicos, dashboard, fuentes, sanitizacion,
fuentes prioritarias, politica Telegram y preview Telegram.

## Operar fuentes locales dry-run

Estas fuentes no publican automaticamente:

```powershell
python scripts/fetch_romeral.py
python scripts/check_romeral_source.py
python scripts/fetch_curico.py
python scripts/check_curico_source.py
python scripts/fetch_molina.py
python scripts/check_molina_source.py
python scripts/fetch_rauco.py
python scripts/check_rauco_source.py
python scripts/fetch_rancagua.py
python scripts/check_rancagua_source.py
python scripts/fetch_priority_sources.py
python scripts/check_priority_sources.py
```

Las salidas quedan bajo `output/sources/`. No mover esos artefactos a `public/data`
sin promocion documentada y validaciones completas.

## Operar previews

```powershell
python scripts/build_alert_preview.py
python scripts/check_alert_preview.py
python scripts/build_calendar_preview.py
python scripts/check_calendar_preview.py
python scripts/build_telegram_preview.py
python scripts/check_telegram_preview.py
python scripts/simulate_telegram_policy.py
```

Los previews son artefactos locales de control. No implican envio real.

## GitHub Actions

El workflow de refresco de datos reales ejecuta captura, validaciones, generacion
de datos publicos y previews en un runner. Si hay cambios autorizados, puede
versionar solo archivos publicos bajo `public/data/`.

Controles:

- no versiona `output/`;
- no versiona `.env`;
- no imprime secrets;
- Telegram real requiere secrets y activacion explicita;
- si una validacion falla, el workflow se detiene antes de publicar cambios.

Referencia: `docs/github-actions-refresh.md`.

## Si falla una validacion

1. Leer el primer error del script que fallo.
2. No publicar ni presentar el release mientras el error siga activo.
3. Identificar si el problema viene de datos, dashboard, fuente, privacidad o
   Telegram.
4. Si falla una fuente dry-run, mantenerla fuera de `public/data`.
5. Si aparece RUN/RUT o dato sensible, tratarlo como bloqueo de publicacion.
6. Si falla captura por cambio HTML de una fuente, no forzar datos parciales.
7. Corregir de forma acotada y volver a ejecutar el check especifico.
8. Ejecutar nuevamente `python scripts/check_release_ready.py`.

Si falla el gate de integridad de Empleos Publicos:

- revisar `data/staging/empleos_publicos/`;
- no ejecutar `build_public_data_from_real.py`;
- preservar `data/normalized/empleos_publicos_normalized.json`;
- no evaluar Telegram real;
- no modificar `public/data/telegram_alert_state.json`;
- volver a capturar cuando la fuente publica este estable.

## Comandos de diagnostico utiles

```powershell
git status --short --branch
git rev-parse --short HEAD
python scripts/check_public_data.py
python scripts/check_public_bundle.py
python scripts/check_pages_ready.py
python scripts/check_source_sanitization.py
python -m pytest
```

Antes de cerrar un lote documental, confirmar que solo cambiaron archivos de
documentacion y que el release check sigue pasando.
