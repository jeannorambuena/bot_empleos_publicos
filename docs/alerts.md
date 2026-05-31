# Alertas por correo en modo preview

El modo preview prepara el contenido de futuras alertas sin enviar correos reales.
Permite revisar reglas, asunto, texto y HTML antes de conectar SMTP.

## Por qué no se envían correos todavía

El proyecto aún usa datos demo y está calibrando sus reglas de alertas. En esta fase
no se leen credenciales, no se usa `.env` y no existe integración SMTP en el código.

## Generar preview

Desde la raíz del repositorio:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\venv\Scripts\python.exe scripts\build_alert_preview.py
```

El script lee los JSON públicos y `config/alerts.example.json`, selecciona
oportunidades alertables y genera:

- `output/alerts/email-preview.txt`
- `output/alerts/email-preview.html`
- `output/alerts/alert-summary.json`

`output/` está ignorado por Git porque los previews futuros podrían contener datos de
operación local.

## Reglas iniciales

El preview considera:

- Nueva oportunidad.
- Alta coincidencia.
- Cierre en 7 días.
- Cierre en 3 días.
- Cierre en 1 día.
- Actualización de convocatoria.

Las oportunidades descartadas no generan alertas.

## Dashboard público

Si la variable de entorno `PUBLIC_SITE_URL` existe, el preview incluye ese enlace.
En caso contrario muestra `dashboard local/no configurado`. El script no carga
archivos `.env`.

## Validar

```powershell
.\venv\Scripts\python.exe scripts\check_alert_preview.py
```

Antes de activar SMTP real se deberán revisar manualmente los previews, probar reglas
con casos reales y confirmar que no se publiquen datos privados.

## SMTP futuro y seguridad

Una fase posterior podrá utilizar desde `.env` local:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASS`
- `MAIL_TO`
- `MAIL_FROM`

Nunca subir `.env`, credenciales SMTP, claves ni previews con datos privados.
