# Dry-run Municipalidad de Curicó R2

Municipalidad de Curicó es la primera fuente adicional evaluada con un adaptador
aislado. Este lote no publica resultados ni conecta Curicó al dashboard.

## URL usada

El script lee la ficha `municipalidad-curico` desde `data/source_candidates.json` y
consulta exclusivamente:

```text
https://www.curico.cl/home/category/concursos/
```

No sigue paginación ni descarga archivos. R2 consulta únicamente las páginas de
detalle oficiales enlazadas directamente desde ese listado.

## Qué extrae

La página oficial mezcla publicaciones de concursos municipales, salud, programas,
documentos y resultados de selección. El adaptador lee los artículos de categoría
`concursos`, conserva el enlace oficial de cada publicación, consulta el detalle y
registra enlaces a bases o anexos oficiales sin descargarlos.

R2 clasifica cada publicación con reglas conservadoras:

- `open_confirmed`: solo si existe fecha de cierre explícita y vigente.
- `closed`: si existe cierre pasado o evidencia textual de resultado de selección.
- `manual_review`: si falta fecha o la vigencia no es inequívoca.

## Campos confiables

- `source`, `institution`, `region` y `commune`.
- `source_url` oficial de la publicación.
- `listing_url` oficial configurada.
- título y descripción visible en el listado.
- `detected_at` de la consulta local.
- `detail_checked_at` y `detail_url_status`.
- `document_urls` oficiales detectadas en el detalle.
- `published_date` o `closing_date` únicamente cuando existe etiqueta textual
  explícita y parseable.

## Campos sujetos a revisión manual

- `closing_date`: queda `null` si no existe evidencia clara; no se inventan fechas.
- `status`: queda `manual_review` cuando el detalle no confirma vigencia.
- clasificación laboral final: algunos artículos corresponden a salud, programas o
  publicaciones históricas.

Los campos adicionales `evidence`, `status_reason` y `confidence` explican por qué se
asignó cada estado.

## Resultado observado de R2

En la revisión del `2026-06-02`, R2 consultó 9 detalles oficiales directos:

- 13 documentos oficiales detectados sin descarga.
- 0 publicaciones `open_confirmed`.
- 2 publicaciones `closed` por evidencia textual de resultado.
- 7 publicaciones `manual_review`.

Se detectó una fecha explícita de publicación en un resultado cerrado. No se
detectaron fechas de cierre confiables en HTML, por lo que ningún registro se marcó
como abierto.

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
