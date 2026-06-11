# Estado del proyecto

## Resumen ejecutivo

Radar Laboral Publico Chile queda documentado como un MVP funcional validado
localmente. El sistema captura, normaliza y publica oportunidades laborales
publicas en una vista estatica, con priorizacion, historial, sanitizacion,
revision humana y preview controlado de Telegram.

El proyecto queda preparado como release de portafolio `v1.0.0`, sujeto al commit
final, revision de GitHub Pages y creacion deliberada del tag correspondiente.

Este estado corresponde al Lote A del cierre profesional del proyecto: deja
constancia del alcance validado, los comandos de control y las limitaciones que
debe conocer un analista externo antes de presentar, publicar o extender el MVP.

## Validacion registrada

| Item | Valor |
| --- | --- |
| Fecha de validacion local | 2026-06-10, America/Santiago |
| Rama validada | `main` |
| Commit validado | `333b5a6` |
| Datos publicos validos | 101 oportunidades |
| Fuentes candidatas catalogadas | 53 |
| Fuentes configuradas | 7 |
| Estado Telegram | Preview/controlado, sin envio automatico |
| Estado fuentes locales municipales | Dry-run o revision manual, salvo promocion controlada documentada |

## Alcance funcional validado

El MVP validado cubre:

- Generacion de datos publicos bajo `public/data/`.
- Dashboard estatico bajo `public/`.
- Catalogo de fuentes candidatas y configuracion de fuentes operativas.
- Sanitizacion comun para reducir exposicion de datos personales.
- Matriz de estados de fuentes con separacion entre publicacion, dry-run y
  revision manual.
- Preview de alertas Telegram y simulacion de politica de envio.
- Checks reproducibles de preparacion de release mediante
  `scripts/check_release_ready.py`.

## Estado de datos y fuentes

Los datos publicos vigentes contienen 101 oportunidades validas. El catalogo de
fuentes conserva 53 candidatas clasificadas por prioridad y publicabilidad. La
configuracion operativa mantiene 7 fuentes.

Estados principales:

- `active_published`: fuente estable publicada en el flujo publico.
- `tested_publishable_controlled`: fuente promovida con reglas limitadas y
  controles adicionales.
- `dry_run_only`: fuente con captura local auditable, no publicada.
- `manual_review_only`: fuente que requiere revision humana antes de cualquier
  promocion.
- `candidate_only`: fuente solo catalogada, sin scraper ni publicacion.
- `blocked`: fuente fuera del alcance del radar laboral o separada por criterio
  de producto.

Detalle de referencia: `docs/source-status-matrix.md`.

## Comandos ejecutados o usados como control

Durante la validacion local del cierre se consideran estos comandos:

```powershell
git rev-parse --short HEAD
python scripts/check_release_ready.py
```

El check de release ejecuta controles compuestos sobre datos publicos,
preparacion de GitHub Pages, catalogo de fuentes, configuracion de fuentes,
sanitizacion, fuentes prioritarias, politica Telegram, generacion de preview
Telegram y verificacion del preview.

Comandos operativos documentados para regenerar y revisar el MVP localmente:

```powershell
python scripts/fetch_empleos_publicos.py
python scripts/check_real_data.py
python scripts/build_public_data_from_real.py
python scripts/check_release_ready.py
python -m http.server 8000 --directory public
```

## Resultado validado

Resultado esperado del cierre local:

```text
OK: release MVP listo
```

Ese resultado indica que el MVP pasa las validaciones automaticas disponibles
para publicacion/presentacion local: datos publicos, dashboard estatico,
catalogo, configuracion, sanitizacion, fuentes priorizadas y Telegram en modo
controlado.

## Limitaciones conocidas

- El MVP no es un SaaS multiusuario. No incluye cuentas, permisos por usuario,
  perfiles aislados ni administracion de clientes.
- Telegram real no debe activarse por defecto. El estado validado es preview y
  simulacion de politica, sin envio automatico.
- Las fuentes locales municipales no promovidas permanecen como dry-run o
  revision manual. No deben publicarse automaticamente.
- Las fuentes `candidate_only` estan catalogadas, pero no implementadas.
- Los artefactos locales de captura, logs, `.env`, secrets y salidas de
  desarrollo no forman parte de la publicacion.
- La sanitizacion reduce riesgo, pero no reemplaza revision humana cuando una
  fuente contiene nominas, resultados historicos, RUN/RUT, anexos sensibles o
  documentos extensos.
- Publicar nuevas fuentes requiere evidencia de vigencia, trazabilidad,
  privacidad y decision explicita de promocion.

## Condiciones de cierre del Lote A

- Documentacion de estado creada para lectura externa.
- Checklist reproducible creada para validacion previa a publicacion o
  presentacion.
- Sin cambios requeridos en `public/data/`.
- Sin cambios requeridos en workflows.
- Sin fuentes nuevas.
- Sin cambios en secrets ni `.env`.
- `python scripts/check_release_ready.py` debe seguir pasando despues de crear
  esta documentacion.
