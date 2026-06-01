# Panel de revisión humana

`public/review.html` permite revisar oportunidades de nivel Alta, Media y casos
descartados con términos ambiguos. Desde el navegador se puede marcar cada caso
como útil, falso positivo, revisar, subir prioridad o bajar prioridad.

Las marcas se guardan únicamente en `localStorage`. El panel no tiene backend y no
envía información automáticamente. Los botones **Copiar JSON** y **Descargar JSON**
permiten exportar el feedback para revisarlo y usarlo en futuras calibraciones del
scoring.

## Importación controlada

El archivo descargado no afecta el dashboard por sí solo. Para revisar e importar
una propuesta:

```powershell
New-Item -ItemType Directory -Force data/feedback
# Guarda la descarga como data/feedback/review-feedback.json
python scripts/import_review_feedback.py --input data/feedback/review-feedback.json --output config/feedback.json
python scripts/check_feedback_config.py
python scripts/build_public_data_from_real.py
python scripts/analyze_feedback_effect.py
```

`data/feedback/` está ignorado por Git porque contiene exportes locales de trabajo.
`config/feedback.json`, cuando exista, es el archivo controlado y auditable que debe
revisarse por PR. No se crea automáticamente desde el navegador ni desde el
workflow.

## Aplicación

El feedback se aplica como capa posterior al scoring base:

- `false_positive` fuerza nivel `Descartada` sin borrar la oportunidad.
- `useful` aplica un aumento moderado.
- `boost_priority` sube prioridad sin superar 100.
- `lower_priority` baja prioridad sin caer bajo 0.
- `review` conserva score y marca revisión manual.

Los motivos quedan visibles en `alert_reasons`. El scoring base no se modifica de
forma opaca y los efectos pueden auditarse con `scripts/analyze_feedback_effect.py`.
