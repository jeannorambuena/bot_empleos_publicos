# Panel de revisión humana

`public/review.html` permite revisar oportunidades de nivel Alta, Media y casos
descartados con términos ambiguos. Desde el navegador se puede marcar cada caso
como útil, falso positivo, revisar, subir prioridad o bajar prioridad.

Las marcas se guardan únicamente en `localStorage`. El panel no tiene backend y no
envía información automáticamente. Los botones **Copiar JSON** y **Descargar JSON**
permiten exportar el feedback para revisarlo y usarlo en futuras calibraciones del
scoring.

Por ahora el feedback exportado no modifica puntajes ni reglas. Cualquier ajuste
debe revisarse humanamente y entrar por una rama de trabajo.
