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

## Etiquetas del dashboard

El dashboard público muestra etiquetas operativas calculadas solo desde los datos
ya publicados:

- `NUEVA`: oportunidad detectada por primera vez en el último corte.
- `ALTA`: coincidencia alta según el score publicado.
- `CIERRE PRÓXIMO`: fecha de cierre cercana.
- `REVISADA`: existe feedback humano aplicado.
- `FALSO POSITIVO`: una revisión humana descartó la oportunidad.
- `REVISAR`: existe una marca de revisión manual pendiente.

Cada tarjeta agrega una explicación breve y determinista, por ejemplo si el puntaje
es alto, si subió por feedback útil o si conviene revisar pronto por cierre cercano.
No se usa IA ni se inventan motivos fuera del JSON público.

## Preparar el próximo ciclo

Para generar una lista local de candidatos agrupados:

```powershell
python scripts/build_feedback_review_candidates.py
```

El script imprime conteos y genera
`output/feedback-review-candidates.md`. Incluye nuevas altas, altas no revisadas,
cierres próximos relevantes no revisados, coincidencias ambiguas, marcas `review`
y descartadas con términos TI o tecnología.

El archivo de `output/` sirve como apoyo para la revisión humana y no debe
versionarse. Este flujo no modifica scoring ni feedback aplicado.
