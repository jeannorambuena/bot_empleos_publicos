# SLEP Colchagua: dry-run

## Alcance

El adaptador consulta la sede oficial con validación TLS normal. Nunca desactiva la
verificación de certificado para obtener datos.

## Resultado inicial

La sede oficial presenta un error de validación TLS desde el entorno de captura. El
dry-run genera cero oportunidades y registra el bloqueo en
`output/sources/slep_colchagua/`.

## Regla de promoción

La fuente queda en revisión manual hasta que la consulta HTTPS sea verificable y se
pueda medir si sus llamados complementan o duplican Empleos Públicos.
