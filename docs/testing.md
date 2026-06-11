# Pruebas y validacion

Este documento resume las pruebas principales del MVP, que comando ejecutar, que
validan y que riesgo cubren.

## Check compuesto de release

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/check_release_ready.py` |
| Valida | Datos publicos, dashboard, catalogo, fuentes, sanitizacion, fuentes prioritarias, politica Telegram y preview. |
| Resultado esperado | `OK: release MVP listo` |
| Riesgos cubiertos | Publicar datos invalidos, romper dashboard, promover fuentes inseguras o dejar Telegram sin control. |

## QA integral local

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/check_all.py` |
| Valida | Ejecuta en orden las validaciones principales, incluyendo datos reales, datos publicos, historial, dashboard, fuentes, sanitizacion, panel de revision, Telegram y release final. |
| Resultado esperado | `OK: todas las pruebas integrales pasaron` |
| Riesgos cubiertos | Cerrar un lote con una validacion parcial, omitir checks importantes o depender de una secuencia manual incompleta. |

## Datos publicos

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/check_public_data.py` |
| Valida | Contrato minimo de `public/data`, coherencia de oportunidades, reglas especiales de Rancagua y ausencia de registros manuales inseguros. |
| Resultado esperado | Mensaje `OK` del validador. |
| Riesgos cubiertos | JSON incompletos, oportunidades no publicables, fechas invalidas o datos sensibles visibles. |

## Dashboard estatico

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/check_pages_ready.py` |
| Valida | Archivos necesarios para servir `public/` y consistencia basica del dashboard. |
| Resultado esperado | Mensaje `OK` del validador. |
| Riesgos cubiertos | Publicar una pagina incompleta o con dependencias publicas faltantes. |

## Datos reales de Empleos Publicos

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/check_real_data.py` |
| Valida | Captura real local, estructura normalizada y campos necesarios antes de regenerar `public/data`. |
| Resultado esperado | Mensaje `OK` del validador. |
| Riesgos cubiertos | Capturas rotas por cambios HTML, datos incompletos o fuente no trazable. |

## Catalogo de fuentes

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/check_source_candidates.py` |
| Valida | `data/source_candidates.json`, prioridades, estados, acciones futuras y restricciones de publicabilidad. |
| Resultado esperado | Mensaje `OK` del validador. |
| Riesgos cubiertos | Catalogo inconsistente, fuentes bloqueadas mal clasificadas o promociones no documentadas. |

## Configuracion de fuentes

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/check_sources_config.py` |
| Valida | `config/sources.example.json`, fuentes configuradas, parsers esperados y estados declarados. |
| Resultado esperado | Mensaje `OK` del validador. |
| Riesgos cubiertos | Configuracion publica rota, fuente habilitada por error o parser inexistente. |

## Sanitizacion

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/check_source_sanitization.py` |
| Valida | Salidas locales de fuentes y textos publicables contra RUN/RUT visibles, datos personales residuales y tablas sensibles. |
| Resultado esperado | Mensaje `OK` del validador. |
| Riesgos cubiertos | Exposicion de datos personales o documentos sensibles. |

## Fuentes prioritarias dry-run

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/check_priority_sources.py` |
| Valida | Diagnostico de Talca, SLEP Colchagua y SLEP Los Cerezos. |
| Resultado esperado | Resumen sin errores bloqueantes. |
| Riesgos cubiertos | Promover fuentes P1 sin fecha confiable, con TLS dudoso, documentos sensibles o revision humana pendiente. |

## Fuentes locales especificas

| Fuente | Comando de captura | Comando de validacion | Resultado esperado |
| --- | --- | --- | --- |
| Romeral | `python scripts/fetch_romeral.py` | `python scripts/check_romeral_source.py` | Dry-run valido o diagnostico conservador. |
| Curico | `python scripts/fetch_curico.py` | `python scripts/check_curico_source.py` | Dry-run valido. |
| Molina | `python scripts/fetch_molina.py` | `python scripts/check_molina_source.py` | Dry-run/manual_review valido. |
| Rauco | `python scripts/fetch_rauco.py` | `python scripts/check_rauco_source.py` | Dry-run/manual_review valido. |
| Rancagua | `python scripts/fetch_rancagua.py` | `python scripts/check_rancagua_source.py` | Dry-run auditable valido; publicacion solo controlada. |

## Telegram

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/build_telegram_preview.py` |
| Valida | Generacion del preview de mensajes desde datos publicos. |
| Resultado esperado | Preview generado sin envio. |
| Riesgos cubiertos | Mensajes incompletos o candidatos inseguros. |

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/check_telegram_preview.py` |
| Valida | Preview sin marcadores sensibles ni errores de contrato. |
| Resultado esperado | Mensaje `OK` del validador. |
| Riesgos cubiertos | Enviar datos sensibles o texto mal formado. |

| Item | Detalle |
| --- | --- |
| Comando | `python scripts/simulate_telegram_policy.py` |
| Valida | Politica automatica sin envio real. |
| Resultado esperado | Simulacion solamente, sin modificar estado ni enviar mensajes. |
| Riesgos cubiertos | Envios automaticos no deliberados, duplicados o fuera de politica. |

## Criterio de cierre

Un cambio puede considerarse listo para presentacion local cuando:

- `python scripts/check_release_ready.py` pasa;
- `python scripts/check_all.py` pasa cuando se requiere QA integral;
- el dashboard local carga;
- no hay cambios no autorizados en `public/data`, workflows, scripts o secrets;
- las fuentes no promovidas siguen fuera del dashboard;
- cualquier limitacion queda documentada.
