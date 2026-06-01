# Seguridad

Este proyecto está pensado para ser reutilizable y público. La seguridad depende de
separar cuidadosamente ejemplos publicables, configuración local y datos reales.

## Secretos locales

No subir al repositorio:

- Archivos `.env`.
- Credenciales SMTP.
- Contraseñas, tokens o claves API.
- Variables locales que contengan información sensible.

`.env.example` es solo una plantilla pública y debe mantener valores ficticios.

## Bases y logs

No subir bases de datos reales, respaldos ni logs privados. Estos archivos pueden
incluir datos personales, rutas locales, errores internos o detalles de operación.

Antes de publicar reportes o JSON generados, revisar que contengan únicamente
información pública necesaria para consultar una convocatoria.

## GitHub Secrets

Cuando existan workflows de GitHub Actions, las credenciales deberán guardarse en
GitHub Secrets. Los workflows no deben imprimir secretos ni volcarlos a archivos que
se publiquen como artefactos.

## Datos personales

Evitar almacenar o publicar información personal innecesaria. Si una fuente incluye
datos de contacto, evaluar si son estrictamente necesarios antes de incorporarlos al
contrato público.

## Datos demo y datos reales

Los datos demo sirven para desarrollar y probar el dashboard. Deben incluir
`"is_demo": true`, `"url_status": "demo"` y `"source_url": null`.

Los datos reales solo podrán publicarse cuando provengan de una fuente verificable.
Deberán incluir `"is_demo": false` y una `source_url` válida hacia la convocatoria o
su página institucional oficial.
