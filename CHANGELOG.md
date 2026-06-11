# Changelog

Todos los cambios relevantes del proyecto se documentan aqui.

## [v1.0.0] - Release de portafolio

Version final de portafolio de Radar Laboral Publico Chile. Este release documenta
un MVP funcional validado localmente con datos publicos, dashboard estatico,
controles de privacidad, QA integral y materiales de presentacion profesional.

No debe interpretarse como una plataforma comercial completa ni como servicio SaaS
multiusuario. Es una version demostrable, auditable y preparada para presentacion.

### Dashboard publico

- Dashboard estatico en `public/` listo para ejecucion local o publicacion por
  GitHub Pages.
- Vista refinada para portafolio con estado MVP, ultima actualizacion, cantidad de
  oportunidades, fuente principal activa y notas de verificacion.
- Filtros por texto, relevancia, fuente, region, comuna, area, urgencia, piso
  economico y ordenamiento.
- Tarjetas de oportunidades con coincidencia, urgencia, fuente oficial y etiquetas
  operativas.

### Captura y validacion de datos publicos

- Flujo local de captura desde Empleos Publicos.
- Generacion de JSON publicos bajo `public/data/`.
- Validacion de datos reales y datos publicos antes de publicar o presentar.
- Datos publicos vigentes: 101 oportunidades.

### Historial de oportunidades

- Historial publico para distinguir registros nuevos, previamente vistos y no
  vistos en la ultima captura.
- Validacion automatica de consistencia con `scripts/check_history.py`.

### Scoring y relevancia

- Priorizacion de oportunidades segun coincidencia con perfil, area, territorio,
  palabras clave y urgencia.
- Niveles operativos: `Alta`, `Media`, `Baja` y `Descartada`.
- Explicaciones visibles en dashboard para apoyar revision humana.

### Sanitizacion

- Capa comun de sanitizacion para reducir riesgo de publicar RUN/RUT, datos
  personales, nominas o tablas extensas de resultados.
- Checks dedicados sobre fuentes locales y datos publicables.
- Politica conservadora para mantener fuentes riesgosas en dry-run o revision
  manual.

### Telegram preview/controlado

- Generacion de preview Telegram sin envio automatico.
- Validacion del preview antes de cualquier envio real.
- Simulacion de politica automatica sin modificar estado ni enviar mensajes.
- Envio real controlado por secrets, variables y ejecucion explicita.

### GitHub Actions

- Documentacion de workflow de refresco de datos reales.
- Automatizacion controlada para captura, validaciones, previews y publicacion de
  JSON autorizados.
- Reglas para no versionar `output/`, `.env`, logs privados ni secrets.

### QA integral

- `scripts/check_all.py` como suite local integral.
- Ejecucion secuencial de validaciones principales: datos reales, datos publicos,
  historial, dashboard, fuentes, sanitizacion, panel de revision, Telegram y release.
- Resultado esperado: `OK: todas las pruebas integrales pasaron`.

### Documentacion tecnica

- README profesional externo.
- Estado del proyecto y checklist reproducible de release.
- Arquitectura, flujo de datos, operacion, testing, seguridad y estado de fuentes.
- Checklist final de release v1.0.0.

### Materiales de portafolio

- Caso de estudio en `portfolio/case-study.md`.
- Resumen ejecutivo en `portfolio/executive-summary.md`.
- Resumen tecnico en `portfolio/technical-summary.md`.
- Descripciones para CV, LinkedIn y portafolio en `portfolio/cv-description.md`.

### Limitaciones conocidas

- No automatiza postulaciones.
- No accede a portales privados.
- No usa credenciales personales para capturar oportunidades.
- No garantiza cobertura total de todas las oportunidades publicas de Chile.
- No reemplaza revision humana ni verificacion en fuente oficial.
- Las fuentes locales municipales permanecen en dry-run o revision manual salvo
  promocion controlada ya documentada.
