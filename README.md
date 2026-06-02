# Radar Laboral Público Chile

Herramienta comunitaria en evolución para detectar, ordenar y publicar oportunidades
laborales del sector público chileno. El objetivo es facilitar el seguimiento de
convocatorias relevantes mediante filtros configurables, alertas y una vista pública
simple de consultar.

> Estado actual: prototipo en desarrollo. El dashboard de `public/` puede regenerarse
> con datos demo o con una captura real local explícita. Todavía no existe publicación
> automática ni operación productiva.

## Qué problema resuelve

Las oportunidades públicas suelen estar distribuidas entre portales generales,
ministerios, municipalidades, SLEP y otras instituciones. Radar Laboral Público Chile
busca reunir señales útiles en una estructura común para reducir la revisión manual,
priorizar convocatorias afines y recordar fechas de cierre.

## Estado del proyecto

El repositorio conserva una implementación histórica local y suma gradualmente una
arquitectura reutilizable. En esta etapa:

- Existe un dashboard estático responsivo en `public/`.
- Los JSON públicos pueden regenerarse con oportunidades demo o datos reales locales.
- Hay archivos de configuración de referencia en `config/`.
- Están documentados el contrato de datos, la arquitectura, la seguridad y el roadmap.
- El scraper antiguo no se conecta al dashboard público; existe un flujo local nuevo y controlado.
- GitHub Pages y GitHub Actions están preparados; correo, calendario y Telegram real
  permanecen desactivados por defecto.

## Estado actual del bot

- El dashboard público puede publicarse mediante GitHub Pages.
- La captura real puede ejecutarse manualmente o una vez al día hábil desde GitHub Actions.
- `public/data/history.json` distingue oportunidades nuevas reales de registros ya vistos.
- Telegram dispone de preview local y envío real bloqueado por defecto.
- `public/review.html` permite exportar feedback humano sin backend.
- El dashboard muestra etiquetas operativas y explicaciones breves basadas en datos públicos.
- Existe un reporte semanal local para priorizar revisión operativa sin publicar artefactos adicionales.
- SLEP y municipalidades cercanas están declaradas como fuentes futuras.
- Nitro/OpenClaw queda documentado como entorno de despliegue futuro controlado.

## Instalación en Windows

Requisitos recomendados:

- Windows 10 u 11.
- Python 3.10 o superior.
- Git.

Crear un entorno virtual local:

```powershell
git clone <URL-DEL-REPOSITORIO>
cd bot_empleos_publicos
py -m venv venv
.\venv\Scripts\Activate.ps1
```

Esta fase documental no requiere instalar paquetes adicionales. La lógica histórica
puede tener requisitos propios que deberán revisarse antes de reutilizarla.

## Ejecutar la página local

Desde la raíz del repositorio:

```powershell
.\venv\Scripts\python.exe -m http.server 8000 --directory public
```

Luego abre `http://localhost:8000`. La página muestra los JSON públicos disponibles;
pueden ser datos demo o una captura real local previamente validada.

## Publicación en GitHub Pages

El repositorio está preparado para publicar `public/` mediante GitHub Pages después
de revisión y merge a `main`. La publicación puede no estar activa todavía. Consulta
`docs/github-pages.md` para validar el sitio y conocer los pasos manuales futuros.

## Flujo local con datos reales

El primer conector local puede capturar convocatorias públicas desde Empleos Públicos
y regenerar el dashboard sin modificar el scraper histórico:

```powershell
python scripts/fetch_empleos_publicos.py
python scripts/check_real_data.py
python scripts/build_public_data_from_real.py
python -m http.server 8000 --directory public
```

Este flujo todavía no se ejecuta automáticamente y no envía alertas ni recordatorios
reales. Consulta `docs/real-data.md` antes de publicar resultados.

## Actualización manual desde GitHub Actions

El workflow **Refresh real data** permite ejecutar manualmente la captura real,
validar el resultado y actualizar solo los JSON públicos del dashboard. Si hay
cambios, el commit automático en `main` solicita el despliegue existente de GitHub
Pages mediante `workflow_dispatch`. Consulta `docs/github-actions-refresh.md` para
conocer el alcance y las limitaciones.

También existe una ejecución horaria segura de lunes a viernes a las `12:00 UTC`.
Telegram real permanece desactivado en esa programación.

## Fase W: Telegram manual seguro

La Fase W está cerrada. El envío real de Telegram fue probado correctamente mediante
el workflow **Refresh real data** usando `workflow_dispatch` con
`send_telegram=true`. El mensaje llegó al bot `@RADARLABORALJPBOT`.

El envío manual requiere los secrets `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.
El bot no responde mensajes porque no tiene polling ni webhook. Consulta
`docs/telegram-alerts.md` para conocer los controles, el dry-run automático y el
rollback recomendado.

Existe una política automática controlada con dry-run, deduplicación y límite diario.
Permanece desactivada por defecto y solo se habilita deliberadamente con la variable
de repositorio `TELEGRAM_AUTO_ENABLED=true`. Consulta `docs/telegram-alerts.md` antes
de activarla.

## Reporte semanal local

El reporte operativo semanal se genera desde los JSON públicos ya validados:

```powershell
python scripts/build_weekly_report.py
```

El archivo resultante queda en `output/reports/weekly-report.md`, ignorado por Git.
Resume recomendaciones, cierres próximos y pendientes de revisión humana. Consulta
`docs/reports.md`.

## Agregar fuentes futuras

Empleos Públicos sigue siendo la única fuente real activa. Las fuentes futuras deben
incorporarse una por una mediante PRs separados, usando el contrato normalizado de
`docs/source-contract.md` y la guía de `docs/sources-roadmap.md`.

## Configuración futura

Los archivos de `config/` son ejemplos públicos y no contienen secretos:

- `config/profile.example.json`: regiones, áreas, palabras clave, zonas y puntaje
  mínimo de alerta.
- `config/sources.example.json`: fuentes configurables y URLs base o placeholders.
- `config/alerts.example.json`: reglas de alerta por correo y preparación para
  recordatorios de calendario.

Para una instalación local futura, estos ejemplos podrán copiarse a archivos locales
ignorados o transformarse en una configuración administrada por el bot. Todavía no
están conectados a la lógica histórica.

## Alertas y variables locales

`.env.example` enumera variables esperadas para SMTP, destinatarios, zona horaria y
URL pública. Es solo una plantilla. Nunca escribas secretos reales en ese archivo.

Las credenciales locales deberán almacenarse en `.env`, que está excluido por Git.
Cuando exista automatización con GitHub Actions, los secretos deberán configurarse
mediante GitHub Secrets.

## Archivos que no deben subirse

No publiques:

- `.env` ni variantes con credenciales.
- Contraseñas SMTP, tokens o claves.
- Bases de datos reales.
- Logs privados.
- Reportes locales con datos sensibles.
- Información personal innecesaria de postulantes o contactos.

Consulta `docs/security.md` para más detalles.

## Documentación

- `docs/architecture.md`: flujo técnico propuesto.
- `docs/data-contract.md`: contrato de los JSON públicos.
- `docs/security.md`: prácticas mínimas de seguridad.
- `docs/roadmap.md`: evolución por fases.
- `docs/parametros-iniciales.md`: alcance funcional inicial.

## Roadmap resumido

1. Dashboard demo.
2. Documentación y configuración comunitaria.
3. Motor de filtros y scoring.
4. Datos reales locales.
5. Alertas por correo.
6. Recordatorios de calendario `.ics`.
7. Publicación con GitHub Pages.
8. Automatización con GitHub Actions.
9. Incorporación gradual de múltiples fuentes.

El detalle y los criterios de avance están en `docs/roadmap.md`.

## Contribuir

Las contribuciones pueden mejorar documentación, contratos, parsers, pruebas y
fuentes compatibles. Antes de publicar cambios, verifica que no incluyan secretos,
logs privados ni datos personales innecesarios. El proyecto debe seguir siendo
comprensible y reutilizable por la comunidad.
