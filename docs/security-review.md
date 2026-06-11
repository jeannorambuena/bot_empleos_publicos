# Revision de seguridad y privacidad

Checklist de seguridad para el MVP Radar Laboral Publico Chile.

## Estado validado

| Control | Estado |
| --- | --- |
| Usa fuentes publicas | Confirmado |
| No automatiza postulaciones | Confirmado |
| No usa credenciales personales para capturar oportunidades | Confirmado |
| No accede a portales privados | Confirmado |
| No realiza scraping autenticado | Confirmado |
| No publica RUN/RUT ni datos sensibles | Controlado por sanitizacion y checks |
| No versiona `.env` | Confirmado como regla del proyecto |
| No versiona secrets | Confirmado como regla del proyecto |
| Telegram real queda controlado | Confirmado por secrets, variables y ejecucion explicita |

## Datos personales

El dashboard publico no debe publicar:

- RUN/RUT completos o parciales;
- nominas de seleccion;
- resultados historicos con identificadores personales;
- anexos con datos personales innecesarios;
- tablas extensas de postulantes;
- credenciales, tokens, claves o configuracion privada.

Los validadores de sanitizacion buscan marcadores sensibles en textos visibles,
evidencias y nombres de documentos. Si una fuente contiene informacion dudosa,
permanece en `manual_review` o dry-run local.

## Secrets y entorno local

Reglas:

- `.env` no se versiona.
- `.env.example` solo contiene placeholders.
- Los secrets de GitHub deben vivir en GitHub Secrets.
- Los scripts y workflows no deben imprimir tokens ni claves.
- `output/`, logs y reportes locales no deben publicarse.

Comandos de revision utiles:

```powershell
git status --short
python scripts/check_source_sanitization.py
python scripts/check_release_ready.py
```

## Credenciales y acceso

El MVP no requiere credenciales personales para capturar oportunidades. La captura
usa paginas publicas y no ingresa a sesiones privadas.

No se permite:

- automatizar postulaciones;
- completar formularios de postulacion;
- entrar a portales con cuentas personales;
- evadir controles de acceso;
- descargar o publicar anexos sensibles sin revision.

## Telegram

Telegram real esta separado del preview. Para enviar mensajes reales se requieren:

- `TELEGRAM_BOT_TOKEN`;
- `TELEGRAM_CHAT_ID`;
- ejecucion manual o workflow con parametro explicito;
- variable de repositorio habilitada en el caso automatico;
- validacion previa del preview.

Por defecto:

- `build_telegram_preview.py` no envia mensajes;
- `check_telegram_preview.py` solo valida;
- `simulate_telegram_policy.py` simula sin enviar ni modificar estado;
- la politica automatica no envia si `TELEGRAM_AUTO_ENABLED` no vale exactamente
  `true`.

## Fuentes locales y privacidad

Las fuentes municipales y SLEP pueden contener documentos con datos personales,
nominas o resultados. Por eso se operan primero como dry-run en `output/sources/` y
no entran al dashboard hasta pasar contrato, sanitizacion, trazabilidad y revision
humana.

Rancagua es una promocion controlada: solo se publican ofertas municipales seguras
con cierre futuro, mientras las ofertas externas OMIL permanecen fuera de
`public/data`.

## Checklist antes de publicar

- Ejecutar `python scripts/check_release_ready.py`.
- Confirmar que no hay `.env` ni secrets en `git status --short`.
- Confirmar que `public/data` solo cambio si el lote autoriza refresco de datos.
- Revisar que Telegram este en preview/controlado.
- Revisar fuentes nuevas o dry-run antes de cualquier promocion.
- No publicar si hay RUN/RUT, nominas, resultados o anexos sensibles.
