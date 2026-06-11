# Caso de estudio: Radar Laboral Publico Chile

## Problema abordado

Las oportunidades laborales del sector publico chileno se publican en portales y
sitios institucionales dispersos. Revisarlas manualmente consume tiempo, dificulta
comparar requisitos y aumenta el riesgo de perder fechas de cierre relevantes.

El problema no era postular automaticamente, sino construir un radar que ayudara a
detectar, ordenar y revisar convocatorias publicas con trazabilidad y controles de
privacidad.

## Contexto

El proyecto nace como una automatizacion personal y profesional para monitorear
convocatorias publicas asociadas a perfiles TI, soporte, redes, sistemas,
transformacion digital y gestion tecnologica.

El alcance se mantuvo deliberadamente acotado: usar fuentes publicas, publicar solo
datos sanitizados, conservar fuentes locales en dry-run cuando requieren revision y
documentar claramente que el sistema es un MVP funcional validado, no una plataforma
comercial completa.

## Objetivo del proyecto

Construir un MVP capaz de:

- capturar oportunidades desde fuentes publicas;
- normalizarlas a un contrato comun;
- priorizarlas mediante scoring;
- publicarlas en un dashboard estatico;
- mantener historial y trazabilidad;
- validar seguridad, privacidad y calidad antes de presentar el resultado;
- preparar alertas en modo preview/controlado.

## Solucion construida

Radar Laboral Publico Chile implementa un flujo local y auditable:

```text
fuente publica -> captura -> normalizacion -> sanitizacion -> scoring
-> public/data -> dashboard estatico -> previews y QA
```

El dashboard muestra oportunidades publicas, filtros, etiquetas operativas,
coincidencia, urgencia de cierre y enlace a la fuente oficial. El sistema tambien
incluye panel de revision humana, historial, documentacion tecnica, checklist de
release y QA integral.

## Rol del autor

El autor cumplio un rol integral de producto y desarrollo:

- definicion del problema y alcance MVP;
- diseno del flujo de datos;
- implementacion de scripts de captura y validacion;
- construccion del dashboard estatico;
- definicion de criterios de seguridad y privacidad;
- documentacion tecnica y de operacion;
- preparacion del proyecto como caso profesional de portafolio.

## Tecnologias utilizadas

- Python para captura, normalizacion, scoring, sanitizacion y validaciones.
- HTML, CSS y JavaScript para dashboard estatico.
- JSON como contrato de intercambio de datos publicos.
- GitHub Actions para automatizacion controlada de refresco.
- GitHub Pages como destino natural del dashboard estatico.
- Telegram Bot API en modo controlado, con preview y envio real desactivado por
  defecto.

## Arquitectura resumida

Componentes principales:

- `scripts/`: captura, generacion, checks, previews y QA.
- `src/radar/`: logica reutilizable de fuentes, scoring y sanitizacion.
- `public/`: dashboard estatico y datos publicables.
- `public/data/`: JSON versionables consumidos por el dashboard.
- `docs/`: documentacion tecnica, operativa y de seguridad.
- `portfolio/`: materiales para explicar el proyecto externamente.
- `output/`: artefactos locales no publicables.

La arquitectura separa datos publicables de datos locales y mantiene dry-runs
fuera del dashboard hasta que una fuente cumpla criterios de promocion controlada.

## Flujo de datos

Flujo principal:

```powershell
python scripts/fetch_empleos_publicos.py
python scripts/check_real_data.py
python scripts/build_public_data_from_real.py
python scripts/check_release_ready.py
```

El flujo toma datos publicos, valida la captura, genera JSON publicables y ejecuta
checks de release.

Las fuentes municipales y territoriales se prueban en dry-run. Sus salidas quedan
en `output/sources/` y no entran a `public/data` salvo promocion controlada y
documentada.

## Criterios de seguridad y privacidad

El proyecto se diseno con restricciones explicitas:

- no automatiza postulaciones;
- no usa credenciales personales para capturar oportunidades;
- no accede a portales privados;
- no hace scraping autenticado;
- no publica RUN/RUT ni datos sensibles;
- no versiona `.env`, secrets, logs privados ni artefactos locales;
- no reemplaza la revision humana cuando una fuente tiene riesgo de privacidad.

Telegram real queda controlado por secrets, variables de activacion y ejecucion
explicita. El modo validado por defecto es preview/simulacion.

## Validaciones implementadas

El proyecto incluye checks individuales y QA integral.

Comando principal:

```powershell
python scripts/check_all.py
```

Este QA ejecuta validaciones de datos reales, datos publicos, historial, dashboard,
fuentes, sanitizacion, panel de revision, Telegram y release final.

Comando de release:

```powershell
python scripts/check_release_ready.py
```

Resultado esperado:

```text
OK: release MVP listo
```

## Resultado actual

Estado validado:

- MVP funcional validado localmente.
- 101 oportunidades publicas en el dashboard.
- 53 fuentes candidatas catalogadas.
- 7 fuentes configuradas.
- Dashboard estatico refinado para portafolio.
- QA integral reproducible.
- Telegram en preview/controlado.
- Fuentes locales en dry-run o revision manual, salvo promocion controlada ya
  documentada.

## Limitaciones conocidas

- No es SaaS multiusuario.
- No garantiza cobertura total de todas las oportunidades publicas de Chile.
- La captura puede fallar si una fuente publica cambia su estructura.
- Las fuentes nuevas requieren revision y promocion separada.
- Los checks automaticos reducen riesgo, pero no sustituyen revision humana.
- El dashboard no postula ni completa formularios.
- Toda convocatoria debe verificarse en la fuente oficial antes de actuar.

## Aprendizajes

- La frontera entre dato publico y dato publicable necesita reglas claras.
- Un dashboard estatico puede ser suficiente para entregar valor si el contrato de
  datos es estable.
- Las fuentes municipales requieren una politica conservadora por riesgo de nominas,
  resultados historicos o anexos sensibles.
- Documentar validaciones y limitaciones mejora la confianza tanto como agregar
  nuevas funciones.
- Automatizar alertas sin controles puede generar ruido o riesgo; el preview es una
  etapa necesaria.

## Proximos pasos

- Mejorar observabilidad de capturas y fallos.
- Ampliar pruebas automatizadas sobre parsers.
- Incorporar nuevas fuentes una por una, empezando por dry-run.
- Mejorar UX del panel de revision humana.
- Formalizar politica de retencion de datos.
- Evaluar infraestructura productiva solo si el MVP evoluciona a servicio continuo.
