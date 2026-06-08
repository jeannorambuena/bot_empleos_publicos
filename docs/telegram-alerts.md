# Alertas Telegram

Telegram opera con preview local, envío manual seguro y una política automática
controlada. El modo automático real permanece desactivado por defecto.

## Estado operativo

La Fase W de Telegram manual seguro fue probada con `workflow_dispatch` y
`send_telegram=true`. El modo manual sigue disponible y exige confirmación explícita.

La política automática agrega `dry-run`, deduplicación y límite diario. Una ejecución
programada solo envía realmente si la variable de repositorio
`TELEGRAM_AUTO_ENABLED` vale exactamente `true`.

## Preview local

```powershell
python scripts/build_telegram_preview.py
python scripts/check_telegram_preview.py
```

`output/telegram/telegram-preview.txt` contiene hasta cinco recomendaciones
accionables. `output/` está ignorado por Git.

Para oportunidades Santiago/RM, cada recomendacion puede incluir una alerta breve:
`Cumple piso Santiago`, `Revisar renta Santiago` o `Bajo piso economico Santiago`.
Las ofertas bajo piso economico solo entran al preview si la coincidencia previa es
muy alta y se marcan como revision manual.

## Envío manual seguro

El modo manual exige simultáneamente:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- argumento explícito `--send`

Prueba bloqueada sin enviar:

```powershell
python scripts/send_telegram_alerts.py
```

Envío manual deliberado después de revisar el preview:

```powershell
python scripts/send_telegram_alerts.py --send
```

## Política automática controlada

La política automática solo permite enviar cuando se cumplen todas estas reglas:

1. La ejecución programada o manual habilita explícitamente el modo automático.
2. Existe al menos una oportunidad `Alta` nueva o `Alta` con cierre próximo.
3. La oportunidad no está marcada como `false_positive`.
4. La oportunidad no esta marcada como `bajo_piso` economico para Santiago/RM.
5. La oportunidad no aparece en los IDs enviados previamente.
6. No existe otro envío automático registrado durante el mismo día.
7. El modo real está habilitado y existen los secrets de Telegram.

El límite diario usa UTC para mantener comportamiento reproducible en GitHub Actions
y equipos Windows sin dependencias adicionales.

Prueba local segura:

```powershell
python scripts/send_telegram_alerts.py --automatic --dry-run
python scripts/simulate_telegram_policy.py
```

Ambos comandos muestran qué ocurriría sin llamar a Telegram ni modificar estado.

## Estado anti-duplicados

`public/data/telegram_alert_state.json` conserva únicamente fecha del último envío
automático, IDs públicos de oportunidades enviadas, modo y motivo. Se versiona porque
los runners de GitHub Actions son efímeros y necesitan recuperar el estado entre
ejecuciones.

El archivo nunca debe contener tokens, chat IDs ni secretos. El ejemplo
`data/telegram_alert_state.example.json` documenta su estructura mínima.

## Activación y rollback

- Modo seguro predeterminado: no definir `TELEGRAM_AUTO_ENABLED` o usar un valor
  distinto de `true`. La ejecución programada hará solamente dry-run.
- Prueba manual sin enviar: ejecutar **Refresh real data** con
  `run_telegram_auto_policy=true` y `send_telegram_auto=false`.
- Envío automático controlado manual: usar además `send_telegram_auto=true`.
- Activación programada deliberada: configurar la variable de repositorio
  `TELEGRAM_AUTO_ENABLED=true` después de revisar logs en dry-run.
- Rollback inmediato: cambiar `TELEGRAM_AUTO_ENABLED` a `false` o eliminarla.

Si Telegram empieza a enviar ruido, desactiva primero `TELEGRAM_AUTO_ENABLED`, revisa
los logs del workflow y audita `public/data/telegram_alert_state.json`. No borres el
historial sin revisión: perderlo puede permitir alertas duplicadas.

## Alcance intencional

El bot no responde mensajes porque no tiene polling ni webhook. Tampoco incorpora
lógica conversacional. El workflow no envía correo ni conecta Google Calendar real.
