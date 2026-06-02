# Contrato para fuentes futuras

Cada nueva fuente debe transformar sus registros a una oportunidad normalizada antes
de entrar al scoring o al dashboard. El adaptador de una fuente es responsable de
capturar datos verificables, conservar trazabilidad y no alterar el conector estable
de Empleos Públicos.

## Campos mínimos de entrada normalizada

| Campo | Tipo | Regla |
| --- | --- | --- |
| `id` | string | Identificador estable y prefijado por fuente. |
| `source_id` | string | Identificador original de la fuente, si existe. |
| `title` | string | Título público de la oportunidad. |
| `institution` | string | Organismo responsable. |
| `source` | string | Nombre legible de la fuente. |
| `source_url` | string | URL oficial directa de la convocatoria. |
| `listing_url` | string o null | Página oficial de listado o categoría. |
| `region` | string | Región normalizada o `Nacional`. |
| `commune` | string | Comuna normalizada o `No especificada`. |
| `closing_date` | string | Fecha `YYYY-MM-DD`, cuando la fuente la publique. |
| `detected_at` | string | Fecha de captura ISO 8601. |
| `status` | string | Estado verificable, por ejemplo `abierta`. |
| `description` | string | Resumen público disponible. |
| `tags` | array de string | Etiquetas verificables o lista vacía. |
| `is_demo` | boolean | `false` para capturas reales. |
| `url_status` | string | Estado de validación de URL, por ejemplo `ok`. |

El scoring, las marcas de historial y el feedback humano se aplican después de esta
normalización. Una fuente nueva no debe calcular esos campos por su cuenta.

## Identidad y duplicados

El `id` debe ser reproducible entre ejecuciones. Se recomienda combinar un prefijo de
fuente con el identificador oficial, por ejemplo `slep-los-cerezos-12345`. Cuando una
fuente no entregue identificador, el adaptador puede derivar uno estable desde URL
oficial y campos normalizados. La deduplicación entre fuentes debe revisarse
explícitamente antes de publicar: dos portales pueden difundir la misma convocatoria.

## URL, vigencia y trazabilidad

- `source_url` debe apuntar a la convocatoria oficial real, no a un enlace inventado.
- `listing_url` permite rastrear la página donde apareció el registro.
- La vigencia se valida con estado publicado, fecha de cierre y presencia en capturas
  sucesivas.
- Los datos crudos y normalizados locales permanecen fuera de `public/` y respetan
  las reglas de seguridad del repositorio.

Consulta `examples/source-normalized-opportunity.json` para ver un ejemplo seguro.
El ejemplo usa el dominio reservado `.example`: ilustra el contrato, no representa
una convocatoria real ni debe publicarse como dato capturado.

## Catastro previo a una integración

Antes de implementar un adaptador, registrar la fuente en
`data/source_candidates.json` y validar:

```powershell
python scripts/check_source_candidates.py
```

El catastro no es un feed operativo: documenta hipótesis, URLs oficiales y riesgos
para decidir qué fuente merece un PR independiente.

## Regla de fuente publicable

Una fuente nueva solo puede pasar de `dry_run` a publicable si no contiene datos
personales visibles, tiene `source_url` oficial, conserva trazabilidad de evidencia
y pasa sus checks de contrato y sanitizacion. El `status` debe ser confiable; todo
`open_confirmed` requiere `closing_date` futura. Una oferta OMIL externa privada no
puede tratarse automaticamente como empleo publico.

Los campos publicables deben sanearse antes de escribir la salida local. Consulta
`docs/source-sanitization.md` y ejecuta:

```powershell
python scripts/check_source_sanitization.py
```
