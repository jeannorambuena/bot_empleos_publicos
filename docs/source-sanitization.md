# Sanitizacion de fuentes nuevas

Las fuentes nuevas permanecen en `dry_run` hasta demostrar que sus textos publicables
no exponen datos personales. Esta regla es necesaria porque una pagina oficial puede
mezclar convocatorias con resultados historicos, nominas o nombramientos.

## Campos publicables revisados

La sanitizacion se aplica antes de escribir cada salida local a:

- `title`
- `description`
- `evidence`
- `status_reason`
- `manual_review_reason`
- `document_urls[].name`

No modifica URLs oficiales, fuente, institucion, region, comuna, fechas ni `status`.

## Datos redactados

`src/radar/sources/sanitization.py` redacta RUN/RUT completos, variantes con puntos,
digito verificador `K`, secuencias parcialmente visibles con `X` y nombres asociados
de forma conservadora a frases de seleccion o nombramiento. Usa los marcadores
`[RUT_REDACTADO]`, `[NOMBRE_REDACTADO]` y `[DATO_PERSONAL_REDACTADO]`.

Cuando un texto de resultados contiene varias identificaciones, el bloque completo
se reemplaza por `[DATO_PERSONAL_REDACTADO]` para evitar conservar una tabla
historica innecesaria.

## Validacion local

Despues de regenerar los cuatro dry-runs:

```powershell
python scripts/fetch_curico.py
python scripts/fetch_molina.py
python scripts/fetch_gore_maule.py
python scripts/fetch_rancagua.py
python scripts/check_source_sanitization.py
```

El check falla si detecta RUN/RUT completos, RUN/RUT parcialmente visibles,
etiquetas `RUN` o `RUT` residuales o tablas extensas de resultados. Los checks
especificos de cada fuente ejecutan las mismas reglas.

## Motivo y estado de las fuentes

GORE Maule es una fuente legible, historica o cerrada y util para monitoreo futuro.
Sus descripciones historicas mostraron que una fuente oficial puede incluir datos
personales; por eso motivo esta capa comun.

Rancagua es la primera candidata a integracion futura porque detecto una oferta
municipal `open_confirmed` con fecha de cierre confiable. Todavia no se publica:
debe completar sanitizacion, normalizacion, revision humana y una integracion
posterior separada.

## Paso de dry-run a publicable

Una fuente nueva solo puede pasar de `dry_run` a publicable si:

- no contiene datos personales visibles;
- tiene `source_url` oficial;
- tiene `status` confiable;
- si `status=open_confirmed`, tiene `closing_date` futura;
- no mezcla oferta OMIL externa privada como empleo publico automatico;
- pasa el check de sanitizacion;
- pasa el check de contrato;
- mantiene trazabilidad de evidencia.

