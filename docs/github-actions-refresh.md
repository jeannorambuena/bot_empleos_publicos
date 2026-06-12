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
check_source_candidates.py
check_sources_config.py
check_source_sanitization.py
build_alert_preview.py
check_alert_preview.py
build_calendar_preview.py
check_calendar_preview.py
build_telegram_preview.py
check_telegram_preview.py
check_review_panel.py
build_weekly_report.py
```

`fetch_empleos_publicos.py` contiene el gate P0 de integridad. Escribe primero en
`data/staging/empleos_publicos/` y solo promueve
`data/normalized/empleos_publicos_normalized.json` si todas las URLs regionales
obligatorias tienen diagnostico valido, no hay errores, no hay regiones sin
resultados y la caida de volumen queda dentro del umbral configurado. El valor
predeterminado bloquea caidas superiores a 35% contra el ultimo normalizado valido.

Si ese gate falla, el job se detiene antes de `build_public_data_from_real.py`. Por
lo tanto no se modifica `public/data`, no se evalua Telegram real, no se actualiza
`telegram_alert_state.json`, no se crea commit automatico y no se despacha Pages.

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
- `public/data/telegram_alert_state.json`

El workflow no debe versionar:

- `data/raw/`
- `data/normalized/`
- `output/`
- `.env`
- credenciales, logs privados ni archivos locales adicionales

Los previews de correo, calendario y Telegram se generan solo como validación local
dentro del runner. No se envían correos reales ni se conecta Google Calendar.

Telegram manual permanece disponible con `send_telegram=true`, secretos configurados
y llamada explícita a `scripts/send_telegram_alerts.py --send`.

La programación horaria evalúa además una política automática controlada. Por defecto
ejecuta solo `--automatic --dry-run`. El envío real programado se habilita únicamente
si la variable de repositorio `TELEGRAM_AUTO_ENABLED` vale exactamente `true`; incluso
entonces el script exige oportunidades `Alta` nuevas o con cierre próximo, excluye
falsos positivos, evita IDs repetidos y limita el envío automático a una vez al día.

Para probar manualmente la política sin enviar, ejecuta el workflow con
`run_telegram_auto_policy=true` y deja `send_telegram_auto=false`. Para volver al modo
manual seguro, elimina `TELEGRAM_AUTO_ENABLED` o configúrala como `false`.

La revisión programada puede correr de lunes a viernes sin enviar un resumen diario.
El paso automático real recibe `TELEGRAM_AUTO_ENABLED` desde las variables del
repositorio y el script vuelve a exigir que valga exactamente `true`. Si no hay
oportunidades `Alta` seguras y no notificadas, Telegram no envía ningún mensaje.

El estado anti-duplicados se versiona en `public/data/telegram_alert_state.json`
porque los runners son efímeros. Solo contiene timestamp, IDs públicos, modo y motivo.
El límite diario se calcula en UTC para mantener comportamiento reproducible en
GitHub Actions y equipos Windows sin dependencias adicionales.

El reporte semanal se genera dentro del runner como preview local en `output/`. No se
versiona, publica ni envía automáticamente.

## Limitaciones

La captura depende de la estructura pública de Empleos Públicos. Puede fallar si
el sitio cambia su HTML, altera sus endpoints o bloquea solicitudes automatizadas.
Ante un fallo, el workflow se detiene antes de crear un commit.
