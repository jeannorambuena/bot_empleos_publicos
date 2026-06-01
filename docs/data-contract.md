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
campos auxiliares de presentación y filtrado.

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

```json
{
  "sources_reviewed": 3,
  "active_opportunities": 12,
  "new_opportunities": 5,
  "high_match": 6,
  "closing_soon": 4
}
```

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
