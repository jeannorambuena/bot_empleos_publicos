# Matriz final de fuentes

## Resumen del catalogo

El catalogo contiene 53 candidatas clasificadas:

| Prioridad | Cantidad |
| --- | ---: |
| P0 | 2 |
| P1 | 3 |
| P2 | 12 |
| P3 | 9 |
| P4 | 27 |

| Publicabilidad | Cantidad |
| --- | ---: |
| `active_published` | 1 |
| `tested_publishable_controlled` | 1 |
| `dry_run_only` | 3 |
| `manual_review_only` | 6 |
| `candidate_only` | 41 |
| `blocked` | 1 |

## Fuentes operativas y auditadas

| Fuente | Estado | Prioridad | Siguiente accion | Riesgo privacidad |
| --- | --- | --- | --- | --- |
| Empleos Publicos | `active_published` | P0 | `keep_active` | low |
| Municipalidad de Rancagua | `tested_publishable_controlled` | P0 | `keep_monitoring` | low |
| Municipalidad de Curico | `dry_run_only` | P2 | `keep_monitoring` | medium |
| Municipalidad de Molina | `manual_review_only` | P2 | `keep_monitoring` | medium |
| GORE Maule | `dry_run_only` | P3 | `keep_monitoring` | high |
| Municipalidad de Talca | `dry_run_only` | P1 | `keep_monitoring` | medium |
| SLEP Colchagua | `manual_review_only` | P1 | `manual_review_only` | low |
| SLEP Los Cerezos | `manual_review_only` | P1 | `manual_review_only` | medium |

Rancagua tambien conserva dry-run auditable aunque tenga promocion municipal
controlada.

## Revision manual y bloqueo

Ademas de Molina, Colchagua y Los Cerezos, el catalogo conserva como
`manual_review_only` el Portal de Transparencia de organismos, la Direccion de
Educacion Publica SLEP y Directores para Chile. Mercado Publico / Compra Agil Nexus
permanece `blocked`: es un radar comercial separado y no una oportunidad laboral.

Las 41 fuentes `candidate_only` no estan implementadas ni publicadas. Sus tiers y
acciones futuras se consultan en `data/source_candidates.json`.
