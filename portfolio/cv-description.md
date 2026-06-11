# Descripciones para CV y portafolio

## Descripcion corta para CV

Desarrolle Radar Laboral Publico Chile, un MVP en Python, JavaScript y GitHub
Actions que captura, normaliza, valida y publica oportunidades laborales publicas en
un dashboard estatico con controles de privacidad y QA integral.

## Descripcion mediana para LinkedIn

Construí Radar Laboral Publico Chile, un MVP funcional para monitorear oportunidades
laborales publicas usando fuentes abiertas. El sistema captura datos, los normaliza
a JSON, aplica scoring de relevancia, sanitizacion y validaciones, y publica un
dashboard estatico orientado a revision profesional. Incluye documentacion tecnica,
QA integral, historial, fuentes en dry-run y alertas Telegram en modo
preview/controlado. El foco del proyecto fue automatizar de forma responsable sin
usar credenciales personales, sin acceder a portales privados y sin automatizar
postulaciones.

## Descripcion tecnica para portafolio

Radar Laboral Publico Chile es un caso de automatizacion responsable con datos
publicos. Implementa un pipeline en Python para captura, normalizacion,
sanitizacion, scoring y validacion de oportunidades laborales del sector publico,
con salida a JSON versionables consumidos por un dashboard estatico en HTML, CSS y
JavaScript.

El proyecto incorpora QA integral (`scripts/check_all.py`), release check,
documentacion operativa, matriz de fuentes, flujo de datos, revision de seguridad y
previews de alertas Telegram sin envio automatico por defecto. El MVP validado
contiene 101 oportunidades publicas, 53 fuentes candidatas y 7 fuentes configuradas.
Las fuentes municipales no promovidas permanecen en dry-run o revision manual, y
toda convocatoria debe verificarse en la fuente oficial antes de actuar.
