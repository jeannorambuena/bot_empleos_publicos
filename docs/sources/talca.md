# Municipalidad de Talca: dry-run

## Alcance

El adaptador consulta únicamente la portada oficial configurada y busca enlaces
relacionados con concursos o llamados laborales. No sigue OMIL, DAEM, noticias
generales ni enlaces privados, y no descarga documentos.

## Resultado inicial

La portada oficial no expone hoy un índice laboral municipal trazable. El dry-run
genera cero oportunidades y conserva un diagnóstico local en
`output/sources/talca/`.

## Regla de promoción

Una integración futura requiere una ficha oficial de convocatoria laboral, fecha de
cierre explícita y vigente, URL trazable y sanitización aprobada.
