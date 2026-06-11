# Radar Laboral Publico Chile

Radar Laboral Publico Chile es un MVP funcional validado localmente para
monitorear oportunidades laborales publicas en Chile, normalizarlas, priorizarlas
y publicarlas en un dashboard estatico revisable.

El proyecto esta construido como un caso profesional de automatizacion responsable
con datos publicos: no automatiza postulaciones, no accede a portales privados, no
usa credenciales personales para capturar oportunidades y no reemplaza la revision
humana. Su objetivo es reducir trabajo manual de seguimiento y mejorar la
trazabilidad de convocatorias publicas.

## Resumen ejecutivo

El MVP toma oportunidades desde fuentes publicas, las transforma a un contrato de
datos comun, aplica reglas de scoring y sanitizacion, y genera una vista publica
en `public/`. Tambien incluye historial, panel de revision, reporte semanal local,
preview de alertas y controles para Telegram sin envio automatico por defecto.

Estado validado del cierre profesional:

- 101 oportunidades publicas validas.
- 53 fuentes candidatas catalogadas.
- 7 fuentes configuradas.
- Telegram en modo preview/controlado.
- Fuentes locales municipales en dry-run o revision manual, salvo integraciones
  ya documentadas explicitamente.
- Validacion final reproducible con `python scripts/check_release_ready.py`.

Mas detalle: [docs/project-status.md](docs/project-status.md).

## Problema que resuelve

Las oportunidades laborales del sector publico chileno se publican en portales y
sitios institucionales dispersos. Eso obliga a revisar manualmente muchas paginas,
comparar requisitos, detectar fechas de cierre y decidir que convocatorias son
relevantes.

Radar Laboral Publico Chile organiza esas senales en una estructura comun para:

- Reducir revision manual repetitiva.
- Priorizar oportunidades segun criterios configurables.
- Mantener trazabilidad hacia la fuente original.
- Separar oportunidades publicables de fuentes que requieren revision humana.
- Preparar alertas sin enviar mensajes automaticos no revisados.

## Demo publica / dashboard

El dashboard estatico vive en `public/` y puede publicarse mediante GitHub Pages o
ejecutarse localmente.

Para verlo en local:

```powershell
python -m http.server 8000 --directory public
```

Luego abrir:

```text
http://localhost:8000
```

El dashboard consume los JSON versionados en `public/data/`. En este cierre no se
modifican esos datos: ya fueron validados como parte del MVP funcional.

## Funcionalidades implementadas

- Captura local de oportunidades publicas desde Empleos Publicos.
- Normalizacion a JSON publicos usados por el dashboard.
- Dashboard estatico responsivo en `public/`.
- Historial de oportunidades y deteccion de novedades.
- Scoring y etiquetas operativas para priorizacion.
- Panel de revision humana exportable sin backend.
- Sanitizacion comun para reducir exposicion de datos personales.
- Catalogo territorial de fuentes candidatas.
- Fuentes locales municipales aisladas como dry-run o revision manual.
- Reporte semanal local en `output/`.
- Preview de alertas de correo, calendario y Telegram.
- Politica Telegram simulable y desactivada por defecto para envios reales.
- Checks de release para validar datos, dashboard, fuentes, privacidad y alertas.

## Arquitectura resumida

El proyecto usa una arquitectura simple y auditable:

```text
Fuentes publicas
  -> scripts de captura
  -> datos reales locales
  -> normalizacion y sanitizacion
  -> public/data/*.json
  -> dashboard estatico en public/
  -> previews y checks de validacion
```

Componentes principales:

- `scripts/`: captura, normalizacion, previews y validaciones.
- `src/`: logica reutilizable del radar.
- `public/`: dashboard estatico y datos publicables.
- `data/`: catalogos y datos de trabajo.
- `docs/`: arquitectura, seguridad, fuentes, operacion y checklist de release.
- `output/`: artefactos locales no publicables, ignorados por Git.

Documentacion tecnica relacionada:

- [docs/architecture.md](docs/architecture.md)
- [docs/data-contract.md](docs/data-contract.md)
- [docs/source-contract.md](docs/source-contract.md)

## Flujo de datos

El flujo operativo con datos reales es:

```powershell
python scripts/fetch_empleos_publicos.py
python scripts/check_real_data.py
python scripts/build_public_data_from_real.py
python scripts/check_release_ready.py
```

Ese flujo captura oportunidades publicas, valida la salida real, reconstruye los
JSON publicos y ejecuta el control final de release.

Las fuentes candidatas o municipales en dry-run no alimentan automaticamente el
dashboard. Para publicar una fuente nueva debe existir evidencia de trazabilidad,
vigencia, sanitizacion y decision explicita de promocion.

## Instalacion local en Windows

Requisitos recomendados:

- Windows 10 u 11.
- Python 3.10 o superior.
- Git.

Instalacion:

```powershell
git clone <URL-DEL-REPOSITORIO>
cd bot_empleos_publicos
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

El archivo `.env.example` es solo una plantilla. No escribas secretos reales en
archivos versionados.

## Ejecucion local del dashboard

Desde la raiz del repositorio:

```powershell
python -m http.server 8000 --directory public
```

Abrir:

```text
http://localhost:8000
```

Para detener el servidor local, usar `Ctrl+C` en la terminal.

## Pruebas y validacion

El control principal antes de publicar o presentar es:

```powershell
python scripts/check_release_ready.py
```

Resultado esperado:

```text
OK: release MVP listo
```

Ese check valida datos publicos, dashboard, catalogo de fuentes, configuracion,
sanitizacion, fuentes prioritarias, politica Telegram y preview Telegram.

Checklist completa: [docs/release-checklist.md](docs/release-checklist.md).

## Automatizacion con GitHub Actions

El workflow de refresco de datos reales puede capturar desde fuentes publicas,
validar los resultados, regenerar `public/data/` y preparar la publicacion del
dashboard cuando corresponde.

La automatizacion esta disenada con controles:

- Instala dependencias desde `requirements.txt`.
- Ejecuta scripts de captura, validacion y previews.
- Versiona solo archivos publicos autorizados cuando hay cambios.
- No publica `output/`, logs locales, `.env` ni secretos.
- Telegram programado permanece en modo seguro salvo activacion deliberada.

Detalle operativo: [docs/github-actions-refresh.md](docs/github-actions-refresh.md).

## Seguridad y privacidad

El proyecto trabaja con fuentes publicas y evita publicar informacion sensible.
Reglas centrales:

- No automatiza postulaciones.
- No usa credenciales personales para entrar a portales.
- No accede a portales privados.
- No publica RUN/RUT ni datos personales sensibles.
- No publica nominas, resultados historicos sensibles ni anexos riesgosos.
- No reemplaza la revision humana en fuentes con riesgo de privacidad.
- No versiona `.env`, tokens, claves, logs privados ni artefactos locales.

Telegram real requiere secretos y activacion explicita. Por defecto el proyecto
usa preview, validacion y simulacion de politica.

Referencias:

- [docs/security.md](docs/security.md)
- [docs/telegram-alerts.md](docs/telegram-alerts.md)

## Estado actual del proyecto

Radar Laboral Publico Chile esta en estado MVP funcional validado localmente. No
debe presentarse como una plataforma comercial completa ni como un servicio SaaS
multiusuario.

Estado resumido:

- Fuente principal activa: Empleos Publicos.
- Publicacion municipal controlada: solo lo ya documentado y validado.
- Fuentes locales adicionales: dry-run o revision manual.
- Catalogo de fuentes: priorizado, pero no completamente implementado.
- Dashboard: estatico, publicable y verificable.
- Alertas: previews y controles; envio real no automatico por defecto.

Detalle actualizado: [docs/project-status.md](docs/project-status.md).

## Limitaciones conocidas

- No tiene cuentas de usuario, permisos ni perfiles aislados.
- No garantiza exhaustividad de todas las oportunidades publicas de Chile.
- La captura puede fallar si una fuente publica cambia su estructura.
- Las fuentes nuevas requieren PR, revision y validaciones separadas.
- Los checks automaticos no sustituyen la revision humana de privacidad.
- El dashboard publica datos ya normalizados; no es un motor transaccional.
- Telegram real requiere configuracion deliberada y controles previos.

## Roadmap hacia v1.0

Prioridades sugeridas:

1. Consolidar observabilidad de capturas y fallos de fuente.
2. Ampliar pruebas automatizadas sobre parsers y contratos de datos.
3. Incorporar nuevas fuentes una por una, con dry-run y revision humana.
4. Mejorar UX del panel de revision y feedback.
5. Formalizar politicas de retencion de datos y auditoria.
6. Evaluar perfiles de usuario solo si el proyecto evoluciona fuera del MVP.
7. Definir infraestructura productiva antes de operar como servicio continuo.

Referencias:

- [docs/roadmap.md](docs/roadmap.md)
- [docs/sources-roadmap.md](docs/sources-roadmap.md)
- [docs/service-model.md](docs/service-model.md)

## Valor profesional / portafolio

Este repositorio demuestra una implementacion concreta de automatizacion con
criterio profesional:

- Extraccion y normalizacion de datos publicos.
- Separacion entre datos publicables, artefactos locales y fuentes en revision.
- Dashboard estatico facil de desplegar.
- Validaciones reproducibles para release.
- Seguridad y privacidad documentadas desde el diseno.
- Automatizacion responsable con GitHub Actions.
- Alcance honesto: MVP validado, no producto comercial terminado.

Como pieza de portafolio, muestra capacidad para convertir un problema operativo
real en un sistema auditable, documentado y mantenible, con controles antes de
automatizar decisiones sensibles.
