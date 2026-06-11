# Estado de fuentes locales

Este documento resume el estado operativo de las fuentes principales y locales del
MVP. La tabla distingue fuentes que publican en `public/data` de aquellas que solo
generan diagnosticos locales o requieren revision humana.

## Tabla de fuentes

| Fuente | Estado operativo | Siguiente accion | Publica en `public/data` | Evidencia local |
| --- | --- | --- | --- | --- |
| Empleos Publicos | `active_published` / `active` | `keep_active` | Si | `scripts/fetch_empleos_publicos.py`, `scripts/check_real_data.py` |
| Municipalidad de Romeral | `dry_run` + `manual_review` | `keep_monitoring` | No | `scripts/fetch_romeral.py`, `scripts/check_romeral_source.py` |
| Municipalidad de Curico | `dry_run_only` | `keep_monitoring` | No | `scripts/fetch_curico.py`, `scripts/check_curico_source.py` |
| Municipalidad de Molina | `manual_review_only` | `keep_monitoring` | No | `scripts/fetch_molina.py`, `scripts/check_molina_source.py` |
| Municipalidad de Rauco | `dry_run` + `manual_review` | `keep_monitoring` | No | `scripts/fetch_rauco.py`, `scripts/check_rauco_source.py` |
| Municipalidad de Talca | `dry_run_only` | `keep_monitoring` | No | `scripts/fetch_priority_sources.py`, `scripts/check_priority_sources.py` |
| SLEP Colchagua | `manual_review_only` | `manual_review_only` | No | `scripts/fetch_priority_sources.py`, `scripts/check_priority_sources.py` |
| SLEP Los Cerezos | `manual_review_only` | `manual_review_only` | No | `scripts/fetch_priority_sources.py`, `scripts/check_priority_sources.py` |
| Municipalidad de Rancagua | `tested_publishable_controlled` / `published_controlled` parcial | `keep_monitoring` | Si, solo registros municipales seguros | `scripts/fetch_rancagua.py`, `scripts/check_rancagua_source.py` |

## Lectura de estados

- `active_published`: fuente estable del flujo publico.
- `active`: fuente habilitada en configuracion publica de ejemplo.
- `dry_run`: adaptador local aislado; genera artefactos en `output/sources/`.
- `dry_run_only`: captura local auditable que no alimenta dashboard ni alertas.
- `manual_review`: requiere interpretacion humana antes de cualquier promocion.
- `manual_review_only`: no debe publicarse automaticamente.
- `tested_publishable_controlled`: fuente promovida con reglas acotadas y checks.
- `published_controlled`: registro publicado solo bajo condiciones explicitas.
- `keep_monitoring`: mantener observacion sin ampliar alcance automaticamente.

## Que publica hoy

Publican o pueden alimentar `public/data` bajo las reglas actuales:

- Empleos Publicos, como fuente activa principal.
- Municipalidad de Rancagua, solo para oportunidades municipales
  `open_confirmed`, sanitizadas, con cierre futuro, URL trazable y marca
  `published_controlled`.

No publican:

- Romeral.
- Curico.
- Molina.
- Rauco.
- Talca.
- SLEP Colchagua.
- SLEP Los Cerezos.

Estas fuentes permanecen como diagnostico local, dry-run o revision manual. Sus
artefactos no deben moverse a `public/data` manualmente.

## Criterio para pasar de dry-run a publicacion controlada

Una fuente puede evaluarse para publicacion controlada solo si cumple todo lo
siguiente:

1. La fuente es publica, institucional y estable.
2. La URL de cada oportunidad es oficial o trazable.
3. El estado de vigencia es confiable.
4. La fecha de cierre es explicita y futura para registros `open_confirmed`.
5. No hay RUN/RUT, nominas, resultados sensibles ni datos personales visibles.
6. Las descripciones, evidencias y documentos pasan sanitizacion.
7. No mezcla empleo publico con ofertas privadas sin separacion clara.
8. No duplica indebidamente Empleos Publicos.
9. Tiene check especifico y pasa `python scripts/check_release_ready.py`.
10. La promocion queda documentada en PR o documento tecnico.

Si falta cualquiera de esos puntos, la fuente debe seguir en dry-run o revision
manual.
