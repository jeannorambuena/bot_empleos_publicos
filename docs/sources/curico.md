# Dry-run Municipalidad de Curicó

Municipalidad de Curicó es la primera fuente adicional evaluada con un adaptador
aislado. Este lote no publica resultados ni conecta Curicó al dashboard.

## URL usada

El script lee la ficha `municipalidad-curico` desde `data/source_candidates.json` y
consulta exclusivamente:

```text
https://www.curico.cl/home/category/concursos/
```

No sigue paginación, PDFs ni enlaces de detalle.

## Qué extrae

La página oficial mezcla publicaciones de concursos municipales, salud, programas,
PDFs y resultados de selección. El adaptador lee los artículos de categoría
`concursos`, conserva el enlace oficial de cada publicación y excluye resultados
evidentes con marcas como `SELECCIONADO` o `NÓMINA SELECCIONADOS`.

Cada registro restante se trata como publicación candidata, no como convocatoria
vigente confirmada.

En la revisión del `2026-06-02`, el listado entregó 9 artículos: 2 resultados de
selección fueron excluidos y 7 publicaciones quedaron como candidatas. El dry-run no
confirma concursos vigentes porque el listado no expone cierre ni vigencia inequívocos.

## Campos confiables

- `source`, `institution`, `region` y `commune`.
- `source_url` oficial de la publicación.
- `listing_url` oficial configurada.
- título y descripción visible en el listado.
- `detected_at` de la consulta local.

## Campos sujetos a revisión manual

- `closing_date`: queda como `null`; no se inventan fechas.
- `status`: queda como `manual_review`; el listado no confirma vigencia inequívoca.
- clasificación laboral final: algunos artículos corresponden a salud, programas o
  publicaciones históricas.

## Ejecutar

```powershell
python scripts/fetch_curico.py
python scripts/check_curico_source.py
```

Archivos locales generados:

```text
output/sources/curico/opportunities.json
output/sources/curico/diagnostics.json
output/sources/curico/report.md
```

`output/` está ignorado por Git. El adaptador no modifica `public/data/`, scoring,
feedback, workflows ni Telegram.
