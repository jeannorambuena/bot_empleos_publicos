# Dry-run GORE Maule

Gobierno Regional del Maule es la tercera fuente adicional evaluada mediante un
adaptador aislado. Este lote no publica resultados ni conecta GORE Maule al
dashboard.

## URL usada

El script lee la ficha `gore-maule` desde `data/source_candidates.json` y consulta
exclusivamente la URL configurada:

```text
https://www.goremaule.cl/goremauleVII/concursos-publicos/
```

Además revisa únicamente las páginas de detalle oficiales enlazadas directamente
desde ese listado. No sigue paginación ni descarga documentos.

## Qué extrae

El listado oficial contiene ocho concursos con detalles propios. Las fichas mezclan
bases, anexos, documentos de etapas posteriores y resultados históricos. El índice
visible fue actualizado por última vez en marzo de 2021.

El adaptador registra:

- título y URL oficial directa de cada concurso;
- `listing_url` oficial configurada;
- región Maule;
- documentos oficiales detectados dentro del contenido del concurso, sin descarga;
- `detected_at`, `detail_checked_at` y estado de consulta;
- clasificación conservadora con motivo, confianza y evidencia.

## Reglas de vigencia

- `open_confirmed`: solo si el HTML publica fecha de cierre explícita y vigente.
- `closed`: si el detalle muestra cierre pasado, resultado, nómina o nombramiento.
- `manual_review`: si falta evidencia inequívoca de vigencia.

No se interpretan fechas sueltas ni nombres de archivo como fechas de cierre.

## Campos confiables

- `source`, `institution`, `region`, `source_url` y `listing_url`;
- título visible de la publicación;
- documentos oficiales detectados dentro del detalle;
- `detected_at`, `detail_checked_at`, `status_reason`, `confidence` y `evidence`.

## Campos sujetos a revisión manual

- `commune`: queda `null` porque los concursos corresponden al organismo regional;
- `closing_date`: queda `null` sin etiqueta explícita parseable;
- `published_date`: queda `null` si el HTML no muestra publicación explícita;
- comparación de duplicados con Empleos Públicos antes de cualquier integración.

## Resultado observado

En la revisión del `2026-06-02`, el adaptador consultó 8 detalles oficiales:

- 42 documentos oficiales detectados sin descarga;
- 0 publicaciones `open_confirmed`;
- 8 publicaciones `closed` por evidencia textual de cierre, resultado o
  nombramiento;
- 0 publicaciones `manual_review`;
- 0 errores HTTP de detalle.

No se detectaron fechas de cierre confiables en HTML. Aunque las fichas tienen
trazabilidad útil, corresponden a procesos históricos y no deben publicarse como
oportunidades vigentes.

## Ejecutar

```powershell
python scripts/fetch_gore_maule.py
python scripts/check_gore_maule_source.py
```

Archivos locales generados:

```text
output/sources/gore_maule/opportunities.json
output/sources/gore_maule/diagnostics.json
output/sources/gore_maule/report.md
```

`output/` está ignorado por Git. El adaptador no modifica `public/data/`, scoring,
feedback, workflows ni Telegram. GORE Maule todavía no se publica porque este lote
solo audita la fuente y sus fichas históricas de forma aislada.
