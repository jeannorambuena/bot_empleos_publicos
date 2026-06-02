# Dry-run Municipalidad de Rancagua

Municipalidad de Rancagua es la primera fuente municipal integrada de forma
controlada al dashboard. El adaptador conserva su dry-run completo para auditoria
local, pero la publicacion solo admite ofertas municipales seguras y vigentes.

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
como empleo público recomendado ni entrar a `public/data`.

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

La fuente es técnicamente legible, pero no se publica completa porque el RSS mezcla
contratación municipal e intermediación OMIL privada. El generador público vuelve a
sanear la captura y selecciona únicamente la oferta municipal `open_confirmed` con
cierre futuro. La marca `implementation_status = "published_controlled"` permite
distinguir esa promoción explícita del dry-run local.

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

`output/` está ignorado por Git. El adaptador aislado no modifica `public/data/`,
scoring, feedback, workflows ni Telegram. `scripts/build_public_data_from_real.py`
es el único punto que promueve registros de Rancagua al dashboard y excluye las
ofertas externas intermediadas por OMIL.
