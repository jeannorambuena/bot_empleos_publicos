# Checklist de release

Esta checklist permite validar Radar Laboral Publico Chile antes de publicarlo,
presentarlo o fusionar cambios hacia una rama de entrega. Esta pensada para un
analista externo que necesita confirmar el estado del MVP sin depender de
contexto verbal.

## 1. Confirmar rama y commit

Desde la raiz del repositorio:

```powershell
git status --short --branch
git rev-parse --short HEAD
```

Criterios:

- La rama esperada para el cierre actual es `main`.
- El commit validado para este estado es `333b5a6`.
- No debe haber cambios no explicados en zonas sensibles antes de publicar.

## 2. Revisar zonas que no deben cambiar

Antes de generar o publicar, confirmar que no se hayan modificado sin decision
explicita:

```powershell
git status --short
```

No modificar durante este cierre:

- `public/data/`
- `.github/workflows/`
- `.env` o archivos de secrets
- Configuracion de fuentes para agregar fuentes nuevas
- Scrapers o fuentes adicionales fuera del alcance aprobado

## 3. Validar datos reales de origen

Si se necesita regenerar el dataset desde la fuente principal:

```powershell
python scripts/fetch_empleos_publicos.py
python scripts/check_real_data.py
```

Criterios:

- El comando de chequeo de datos reales debe terminar sin errores.
- Los datos deben corresponder a oportunidades laborales publicas vigentes o
  trazables.
- Cualquier alerta de privacidad o trazabilidad debe revisarse antes de
  reconstruir datos publicos.

## 4. Reconstruir datos publicos solo cuando corresponda

Si hubo una captura real nueva y aprobada:

```powershell
python scripts/build_public_data_from_real.py
```

Criterios:

- Los archivos bajo `public/data/` solo deben cambiar si la tarea autoriza
  explicitamente regenerar datos.
- El cierre documentado del Lote A no requiere modificar `public/data/`.
- Los datos publicados no deben contener campos sensibles visibles.

## 5. Ejecutar el check unico de release

Comando obligatorio:

```powershell
python scripts/check_release_ready.py
```

Criterio de exito:

```text
OK: release MVP listo
```

Este comando cubre:

- Datos publicos.
- Preparacion de GitHub Pages.
- Catalogo de fuentes candidatas.
- Configuracion de fuentes.
- Sanitizacion.
- Fuentes prioritarias.
- Politica Telegram.
- Preview Telegram.
- Reglas de publicacion para fuentes nuevas o controladas.

## 6. Revisar dashboard local

Levantar servidor local:

```powershell
python -m http.server 8000 --directory public
```

Abrir:

```text
http://localhost:8000
```

Criterios:

- La pagina principal carga sin errores visibles.
- El listado muestra oportunidades publicas.
- Los filtros y datos resumidos son coherentes con `public/data/summary.json`.
- No aparecen RUN/RUT, nominas sensibles ni informacion personal residual.

## 7. Revisar fuentes y estados

Documentos de apoyo:

- `docs/source-status-matrix.md`
- `docs/sources-roadmap.md`
- `data/source_candidates.json`

Criterios:

- Las fuentes activas y promovidas deben coincidir con los estados
  documentados.
- Las fuentes locales municipales no publicadas deben seguir como dry-run o
  revision manual.
- Las fuentes `candidate_only` no deben aparecer como publicadas.
- No promover una fuente sin evidencia, sanitizacion y decision documentada.

## 8. Revisar Telegram

Comandos de control:

```powershell
python scripts/build_telegram_preview.py
python scripts/check_telegram_preview.py
python scripts/simulate_telegram_policy.py
```

Criterios:

- Telegram real permanece desactivado por defecto.
- El preview debe generarse y validarse sin enviar mensajes.
- No activar `TELEGRAM_AUTO_ENABLED=true` sin aprobacion explicita, revision de
  preview, logs y plan de rollback.

## 9. Revisar privacidad y publicacion

Antes de presentar o publicar:

- Confirmar que no se incluyen `output/`, logs, `.env`, secrets ni artefactos
  locales.
- Revisar nombres de documentos, evidencias, descripciones y razones de estado.
- Mantener resultados historicos, nominas y anexos sensibles fuera del dashboard
  publico.
- Usar revision humana para fuentes con riesgo medio o alto de privacidad.

## 10. Resultado esperado de cierre

El release puede considerarse listo para presentacion local cuando:

- `python scripts/check_release_ready.py` termina con
  `OK: release MVP listo`.
- El dashboard local carga correctamente.
- No hay cambios no autorizados en datos publicos, workflows, secrets o fuentes.
- La documentacion de estado y esta checklist estan actualizadas.
- Las limitaciones del MVP estan comunicadas: no es SaaS multiusuario, Telegram
  no envia automaticamente y las fuentes no promovidas siguen bajo control
  manual o dry-run.
