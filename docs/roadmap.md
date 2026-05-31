# Roadmap

El avance será incremental para mantener el proyecto comprensible, auditable y útil
para la comunidad. Cada fase debe conservar una separación clara entre datos demo,
configuración local y datos reales.

## Fase 1: dashboard demo

- Crear página estática responsiva.
- Cargar oportunidades desde JSON.
- Diferenciar visualmente oportunidades demo.

Estado: completada como prototipo inicial.

## Fase 2: documentación y configuración comunitaria

- Documentar arquitectura, seguridad y contratos.
- Añadir perfiles, fuentes y alertas configurables de ejemplo.
- Preparar plantilla pública de variables locales.

Estado: completada como base documental inicial.

## Fase 3: motor de filtros y scoring

- Definir reglas configurables.
- Calcular puntajes entre 0 y 100.
- Registrar motivos de coincidencia y descarte.
- Añadir pruebas automatizadas.

## Fase 4: conexión a datos reales locales

- Normalizar resultados del scraper.
- Deduplicar oportunidades.
- Generar JSON públicos revisables.
- Mantener procesamiento local antes de automatizar.

## Fase 5: alertas por correo

- Enviar resúmenes por nuevas oportunidades.
- Alertar coincidencias altas y actualizaciones.
- Usar variables locales seguras para SMTP.

## Fase 6: recordatorios calendario `.ics`

- Generar recordatorios para cierres próximos.
- Incluir solo información necesaria.
- Permitir importación manual en calendarios.

## Fase 7: GitHub Pages

- Publicar el dashboard estático.
- Validar JSON antes del despliegue.
- Revisar que no existan secretos ni datos privados.

## Fase 8: GitHub Actions

- Automatizar validaciones y publicación.
- Usar GitHub Secrets.
- Mantener permisos mínimos y logs revisables.

## Fase 9: múltiples fuentes

- Incorporar adaptadores para SLEP, ministerios y municipalidades.
- Añadir páginas institucionales de forma gradual.
- Registrar cobertura, errores y cambios por fuente.
