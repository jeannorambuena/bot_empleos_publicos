# Dry-run Municipalidad de Rancagua

Municipalidad de Rancagua es la cuarta fuente adicional evaluada mediante un
adaptador aislado. Este lote no publica resultados ni conecta Rancagua al dashboard.

## URL usada

El script lee la ficha `municipalidad-rancagua` desde
`data/source_candidates.json` y consulta exclusivamente:

```text
https://munirancagua.gob.cl/ofertas-laborales
```

La página oficial anuncia un RSS específico de ofertas laborales:

```text
https://munirancagua.gob.cl/rss/ofertas-laborales.xml
```

El adaptador descubre esa URL desde el HTML. No sigue fichas ni descarga documentos.

## Qué extrae

El RSS corresponde a intermediación OMIL y mezcla ofertas municipales con ofertas
externas privadas. Incluye título, enlace corto oficial publicado por Rancagua,
fecha de publicación, categorías, descripción, fecha de postulación y, cuando
existen, documentos institucionales.

Las ofertas externas se conservan únicamente como auditoría local con
`offer_scope = "external_private"` y `status = "manual_review"`. No deben tratarse
como empleo público recomendado.

## Reglas de vigencia

- `open_confirmed`: solo para oferta municipal con categoría abierta y fecha de
  cierre futura explícita.
- `closed`: si existe cierre pasado o evidencia textual de resultado o cierre.
- `manual_review`: para ofertas externas OMIL o cuando falta evidencia suficiente.

## Campos confiables

- `source`, `institution`, `region`, `commune`, `listing_url` y `feed_url`;
- título, categorías y enlace publicados por el RSS oficial;
- `published_date` y `closing_date` explícitas;
- documentos institucionales enlazados sin descarga;
- `offer_scope`, `status_reason`, `confidence` y `evidence`.

## Campos sujetos a revisión manual

- naturaleza pública o privada de cada oferta externa;
- relevancia laboral para el radar comunitario;
- política futura para separar intermediación OMIL de convocatorias públicas.

## Resultado observado

En la revisión del `2026-06-02`, el adaptador detectó 5 ofertas:

- 1 oferta municipal `open_confirmed` con cierre futuro explícito;
- 4 ofertas externas privadas en `manual_review`;
- 0 publicaciones `closed`;
- 5 enlaces de oferta publicados por el RSS oficial;
- 5 fechas de publicación RSS;
- 5 fechas de cierre explícitas;
- 1 documento institucional detectado sin descarga.

La fuente es técnicamente legible, pero no debe publicarse completa en el radar de
empleo público porque el RSS mezcla contratación municipal e intermediación OMIL
privada.

## Ejecutar

```powershell
python scripts/fetch_rancagua.py
python scripts/check_rancagua_source.py
```

Archivos locales generados:

```text
output/sources/rancagua/opportunities.json
output/sources/rancagua/diagnostics.json
output/sources/rancagua/report.md
```

`output/` está ignorado por Git. El adaptador no modifica `public/data/`, scoring,
feedback, workflows ni Telegram. Rancagua todavía no se publica porque primero se
debe definir una separación explícita entre convocatorias municipales y ofertas
externas intermediadas por OMIL.
