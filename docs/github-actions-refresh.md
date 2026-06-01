# Actualización de datos reales con GitHub Actions

El workflow `Refresh real data` prepara una actualización segura de los datos
públicos del dashboard. Captura convocatorias desde Empleos Públicos, valida la
salida, regenera los JSON públicos y ejecuta los previews locales antes de publicar
cambios.

## Ejecución manual

El workflow admite ejecución manual:

1. Abre la pestaña **Actions** del repositorio en GitHub.
2. Selecciona **Refresh real data**.
3. Presiona **Run workflow**.
4. Revisa los logs de captura, validación y diagnóstico Git.

También se ejecuta de lunes a viernes a las `12:00 UTC`. Eso corresponde
aproximadamente a la mañana de Chile y puede variar según el horario de verano.

## Flujo ejecutado

El workflow instala las dependencias de `requirements.txt` con Python 3.11 y
ejecuta:

```text
fetch_empleos_publicos.py
check_real_data.py
check_feedback_config.py
build_public_data_from_real.py
check_public_data.py
check_history.py
analyze_real_scoring.py
check_pages_ready.py
build_alert_preview.py
check_alert_preview.py
build_calendar_preview.py
check_calendar_preview.py
build_telegram_preview.py
check_telegram_preview.py
check_sources_config.py
check_review_panel.py
```

Si los datos públicos cambian, el workflow crea un commit automático en `main`.
Ese commit modifica `public/**`. Como GitHub no inicia otros workflows a partir de
un `push` realizado con `GITHUB_TOKEN`, el mismo flujo solicita después una
ejecución manual automatizada (`workflow_dispatch`) del workflow existente de
GitHub Pages. No requiere PAT ni secretos adicionales.

## Archivos versionados

El commit automático puede incluir exclusivamente:

- `public/data/opportunities.json`
- `public/data/summary.json`
- `public/data/last_run.json`
- `public/data/history.json`

El workflow no debe versionar:

- `data/raw/`
- `data/normalized/`
- `output/`
- `.env`
- credenciales, logs privados ni archivos locales adicionales

Los previews de correo, calendario y Telegram se generan solo como validación local
dentro del runner. No se envían correos reales ni se conecta Google Calendar.

Telegram real permanece desactivado por defecto. Solo se intenta desde una
ejecución manual con `send_telegram=true`, secretos configurados y llamada
explícita a `scripts/send_telegram_alerts.py --send`. La programación horaria nunca
activa ese paso.

## Limitaciones

La captura depende de la estructura pública de Empleos Públicos. Puede fallar si
el sitio cambia su HTML, altera sus endpoints o bloquea solicitudes automatizadas.
Ante un fallo, el workflow se detiene antes de crear un commit.
