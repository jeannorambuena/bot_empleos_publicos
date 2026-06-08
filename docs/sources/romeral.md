# Municipalidad de Romeral - Concursos Publicos

Fuente local prioritaria para el Radar Laboral Publico Chile.

- URL monitoreada: https://muniromeral.cl/romeral/?page_id=3217
- Tipo: municipalidad / concursos publicos.
- Region/comuna: Maule / Romeral.
- Modo inicial: `dry_run` con revision manual controlada.

## Objetivo

Detectar cualquier cambio en la pagina oficial de concursos publicos mediante un
hash normalizado del listado. Si el cambio corresponde a una publicacion que parece
concurso laboral, se genera una oportunidad local para revision. No se publica ni se
envia Telegram real desde el dry-run.

El adaptador revisa la pagina principal y variantes paginadas:

- `page=2`
- `page=3`

## Extraccion

`src/radar/sources/romeral.py` lee el bloque de contenido de WordPress y agrupa
publicaciones por:

- fecha visible;
- titulo del llamado;
- estado textual como `Finalizado` o `Desierto`;
- enlaces a bases;
- enlaces de modificacion de fechas;
- URL oficial del listado.

La salida local queda en:

- `output/sources/romeral/opportunities.json`
- `output/sources/romeral/diagnostics.json`
- `output/sources/romeral/monitor_state.json`
- `output/sources/romeral/report.md`

`monitor_state.json` contiene solo hash, URLs revisadas, fecha de revision e IDs
publicos derivados. No guarda secretos ni datos personales.

## Politica conservadora

Romeral no se publica automaticamente si:

- aparece `Finalizado`, `Desierto`, resultados, actas, nominas o seleccion;
- hay indicios de RUN/RUT o datos personales;
- no existe fecha de cierre confiable;
- no es claramente un llamado a concurso publico laboral.

Si parece concurso pero falta cierre confiable, queda como `manual_review` con
`review_label = Revisar bases`.

## Telegram

El preview local puede mostrar:

`Cambio detectado en concursos Romeral: revisar publicacion.`

Ese aviso se alimenta desde el diagnostico dry-run y no envia mensajes reales. El
estado por hash evita repetir el mismo cambio cuando se ejecuta nuevamente el fetch.

## Estado observado

En la primera implementacion se detectaron publicaciones 2025 con enlaces a bases y
algunas modificaciones de fechas. Por fecha actual y/o marcas visibles, quedan como
cerradas o revision manual; no pasan a recomendacion fuerte ni publicacion automatica.
