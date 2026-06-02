# Priorizacion de fuentes candidatas

El catalogo territorial clasifica las fuentes antes de crear nuevos adaptadores.
Este paso evita implementar portales por cantidad y concentra el trabajo en fuentes
con utilidad real para perfiles TI, informatica, redes, soporte, servidores,
telecomunicaciones, ciberseguridad, desarrollo web y transparencia publica.

## Criterios territoriales

- **Maule y comunas cercanas:** prioridad alta para fuentes que puedan publicar
  cargos TI o administrativos tecnologicos con desplazamiento razonable.
- **O'Higgins:** evaluar fuentes regionales cuando un cargo TI fuerte pueda
  justificar traslado.
- **Region Metropolitana:** avanzar solo ante TI fuerte, sueldo conveniente o
  modalidad hibrida o remota. Una fuente RM no se prioriza por publicar cargos
  genericos.
- **Fuentes lejanas o ambiguas:** mantener en baja prioridad o solo revision manual.

`geo_priority`, `mobility_rule` y `rm_policy` dejan estas reglas explicitamente
versionadas en `data/source_candidates.json`.

## Estados

- **Candidata:** existe una URL oficial, pero todavia falta medir estabilidad,
  duplicados y utilidad.
- **Dry-run:** cuenta con adaptador local auditable, sin promocion automatica.
- **Publicable controlada:** demostro contrato, sanitizacion, vigencia y filtros de
  seguridad para una promocion limitada.
- **Activa publicada:** forma parte estable del flujo publico.

`publishability` describe el estado y `next_action` indica el siguiente paso
permitido. `priority_tier` ordena trabajo: `P0` es operacion ya publicada, `P1` son
las siguientes pruebas, y `P2` a `P4` quedan para evaluacion gradual o descarte.

## Proximas tres pruebas

1. `slep-los-cerezos`: primera prioridad territorial por cobertura de Curico,
   Molina, Rauco, Romeral y Teno.
2. `municipalidad-talca`: municipio cercano con fichas y bases; debe separar
   concursos de planta, DAEM y OMIL.
3. `slep-colchagua`: prueba regional de O'Higgins para medir cargos TI fuertes y
   duplicados con Empleos Publicos.

Cada dry-run debe entrar en un PR independiente. Antes de publicar una fuente debe
pasar contrato comun, sanitizacion, verificacion de fechas y revision humana.

## Validacion

```powershell
python scripts/check_source_candidates.py
```

El check exige clasificacion completa, aplica la politica especial de RM, conserva
Rancagua como publicacion controlada y bloquea promociones inseguras para fuentes
con riesgo de privacidad alto o revision manual obligatoria.
