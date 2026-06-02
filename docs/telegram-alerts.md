# Alertas Telegram

Telegram se prepara en dos modos separados: preview local y envío real controlado.
Por defecto no se envía ningún mensaje.

## Estado de la Fase W

La Fase W — Telegram manual seguro — está cerrada. Se ejecutó manualmente el
workflow **Refresh real data** con `workflow_dispatch` y `send_telegram=true`. El
mensaje real llegó correctamente al bot `@RADARLABORALJPBOT`.

El envío continúa siendo manual. No se activa Telegram real desde la ejecución
horaria o programada.

## Preview local

Ejecuta:

```powershell
python scripts/build_telegram_preview.py
python scripts/check_telegram_preview.py
```

El archivo `output/telegram/telegram-preview.txt` resume total de oportunidades,
nuevas reales, altas, medias, cierres próximos y hasta cinco recomendaciones.
`output/` está ignorado por Git.

## Envío real controlado

El script `scripts/send_telegram_alerts.py` exige simultáneamente:

- variable de entorno `TELEGRAM_BOT_TOKEN`
- variable de entorno `TELEGRAM_CHAT_ID`
- argumento explícito `--send`

En GitHub Actions el envío solo se intenta desde `workflow_dispatch` cuando el
operador activa `send_telegram=true` y existen los secretos
`TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`. La ejecución horaria nunca activa el
envío real.

Prueba segura sin enviar:

```powershell
python scripts/send_telegram_alerts.py
```

Envío manual deliberado, después de revisar el preview:

```powershell
python scripts/send_telegram_alerts.py --send
```

Nunca publiques tokens ni identificadores privados. El script no imprime el token
y enmascara el identificador del chat si necesita informar un resultado.

## Alcance intencional

El bot no responde mensajes porque no tiene polling ni webhook. Tampoco incorpora
lógica conversacional. Esa limitación es intencional: esta fase valida únicamente
el envío saliente manual y controlado.

El próximo paso recomendado es mantener el modo manual o definir por PR una política
futura de envío automático con límites claros de frecuencia, contenido y operación.
