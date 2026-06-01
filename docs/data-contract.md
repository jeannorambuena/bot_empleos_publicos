# Contrato de datos públicos

Los JSON de `public/data/` son la interfaz entre el futuro proceso de actualización y
el dashboard estático. Deben ser válidos, legibles y no contener secretos.

## `opportunities.json`

Arreglo de oportunidades normalizadas.

| Campo | Tipo | Obligatorio | Descripción |
| --- | --- | --- | --- |
| `id` | string | Sí | Identificador estable de la oportunidad. |
| `title` | string | Sí | Nombre del cargo o convocatoria. |
| `institution` | string | Sí | Institución responsable. |
| `source` | string | Sí | Nombre legible de la fuente. |
| `source_url` | string o null | Sí | URL oficial real; `null` para demos. |
| `region` | string | Sí | Región o `Nacional`. |
| `commune` | string | Sí | Comuna o `No especificada`. |
| `closing_date` | string | Sí | Fecha de cierre en formato `YYYY-MM-DD`. |
| `detected_at` | string | Sí | Fecha ISO 8601 de detección. |
| `status` | string | Sí | Estado normalizado, por ejemplo `vigente`. |
| `match_score` | integer | Sí | Puntaje entre 0 y 100. |
| `match_level` | string | Sí | `Alta`, `Media`, `Baja` o `Descartada`. |
| `tags` | array de string | Sí | Etiquetas útiles para búsqueda y visualización. |
| `alert_reasons` | array de string | Sí | Motivos para destacar o alertar. |
| `description` | string | Sí | Resumen breve de la oportunidad. |
| `is_demo` | boolean | Sí | Indica si el registro es de ejemplo. |
| `url_status` | string | Sí | `demo`, `available` o estado equivalente acordado. |

El dashboard actual también utiliza `institution_type`, `area` y `urgency` como
campos auxiliares de presentación y filtrado. Cuando existe historial público,
también incluye `is_new_since_last_run`, `first_seen_at`, `last_seen_at` y
`seen_count`. Cuando existe una capa de feedback humano también publica:

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `base_match_score` | integer | Puntaje anterior a feedback humano. |
| `base_match_level` | string | Nivel anterior a feedback humano. |
| `human_reviewed` | boolean | Indica si se aplicó feedback versionado. |
| `human_feedback_action` | string o null | `useful`, `false_positive`, `review`, `boost_priority` o `lower_priority`. |
| `human_feedback_reason` | string o null | Motivo humano opcional. |
| `manual_review` | boolean | Indica revisión manual pendiente. |

Rangos de coincidencia:

- `Alta`: 80 a 100.
- `Media`: 60 a 79.
- `Baja`: 35 a 59.
- `Descartada`: 0 a 34 o descarte fuerte.

Ejemplo:

```json
{
  "id": "demo-001",
  "title": "Profesional de Infraestructura y Servidores",
  "institution": "Ministerio de Ejemplo",
  "source": "Empleos Públicos",
  "source_url": null,
  "region": "Metropolitana",
  "commune": "Santiago",
  "closing_date": "2026-06-03",
  "detected_at": "2026-05-31T15:30:00-04:00",
  "status": "vigente",
  "match_score": 96,
  "match_level": "Alta",
  "tags": ["Linux", "Windows Server"],
  "alert_reasons": ["Alta coincidencia", "Cierre próximo"],
  "description": "Registro demostrativo.",
  "is_demo": true,
  "url_status": "demo"
}
```

## `summary.json`

Objeto con métricas del dashboard.

| Campo | Tipo | Obligatorio | Descripción |
| --- | --- | --- | --- |
| `sources_reviewed` | integer | Sí | Cantidad de fuentes revisadas. |
| `active_opportunities` | integer | Sí | Oportunidades vigentes. |
| `new_opportunities` | integer | Sí | Oportunidades nuevas. |
| `high_match` | integer | Sí | Oportunidades con coincidencia alta. |
| `closing_soon` | integer | Sí | Oportunidades con cierre próximo. |
| `total_opportunities` | integer | Sí con historial | Total visible en la captura más reciente. |
| `high_relevance` | integer | Sí con historial | Alias legible de coincidencias altas. |
| `previously_seen` | integer | Sí con historial | Oportunidades visibles que ya aparecieron antes. |
| `first_seen_this_run` | integer | Sí con historial | Oportunidades detectadas por primera vez en esta ejecución. |
| `not_seen_in_latest_capture` | integer | Sí con historial | Registros históricos ausentes de la captura más reciente. |
| `human_feedback_applied` | integer | Sí con capa de feedback | Oportunidades con feedback versionado aplicado. |
| `human_false_positives` | integer | Sí con capa de feedback | Falsos positivos marcados humanamente. |
| `human_boosted` | integer | Sí con capa de feedback | Oportunidades promovidas humanamente. |
| `human_lowered` | integer | Sí con capa de feedback | Oportunidades con prioridad reducida. |
| `manual_review_count` | integer | Sí con capa de feedback | Oportunidades marcadas para revisión manual. |

```json
{
  "sources_reviewed": 3,
  "active_opportunities": 12,
  "new_opportunities": 5,
  "high_match": 6,
  "closing_soon": 4
}
```

## `history.json`

Arreglo público versionable que permite distinguir oportunidades nuevas reales de
registros ya vistos. No contiene secretos ni datos privados.

| Campo | Tipo | Obligatorio | Descripción |
| --- | --- | --- | --- |
| `id` | string | Sí | Identificador estable de la oportunidad. |
| `first_seen_at` | string | Sí | Primera detección en formato ISO 8601. |
| `last_seen_at` | string | Sí | Última detección en formato ISO 8601. |
| `seen_count` | integer | Sí | Cantidad de capturas en que apareció. |
| `last_title` | string | Sí | Último título público conocido. |
| `last_institution` | string | Sí | Última institución pública conocida. |
| `last_level` | string | Sí | Último nivel de coincidencia. |
| `last_score` | integer | Sí | Último puntaje calculado. |
| `currently_visible` | boolean | Sí | Indica si apareció en la última captura. |

## `last_run.json`

Objeto con el resultado de la última actualización del radar.

| Campo | Tipo | Obligatorio | Descripción |
| --- | --- | --- | --- |
| `finished_at` | string | Sí | Fecha ISO 8601 de término. |
| `status` | string | Sí | Estado de la ejecución, por ejemplo `prototype`. |
| `message` | string | Sí | Mensaje breve para el dashboard. |

```json
{
  "finished_at": "2026-05-31T15:30:00-04:00",
  "status": "prototype",
  "message": "Carga demostrativa completada correctamente"
}
```
