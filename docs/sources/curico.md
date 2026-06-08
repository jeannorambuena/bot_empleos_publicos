# Dry-run Municipalidad de Curico

Fuente local prioritaria de Maule norte integrada en modo `dry_run` y
`manual_review_only`.

## URLs revisadas

```text
https://www.curico.cl/home/category/concursos/
https://www.curico.cl/home/concursos-publicos/
```

## Alcance

El monitor revisa paginas oficiales, normaliza texto visible, calcula hash por
pagina y hash agregado del listado. Las publicaciones detectadas se guardan solo
en:

```text
output/sources/curico/
```

No descarga documentos, no modifica `public/data`, no cambia scoring y no envia
Telegram real.

## Clasificacion

- `open_confirmed`: solo con fecha de cierre explicita y vigente.
- `closed`: si hay cierre vencido o evidencia de resultado/finalizado/desierto.
- `manual_review`: cuando falta vigencia confiable o requiere revisar bases.

Los enlaces a documentos oficiales se conservan como trazabilidad local en
`document_urls`, `base_links` y `application_links`.
