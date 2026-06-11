# Flujo de datos

Este documento describe como una oportunidad pasa desde una fuente publica hasta el
dashboard de Radar Laboral Publico Chile, y que informacion queda solo en local.

## Flujo general

```text
Fuente publica
  -> captura o dry-run
  -> normalizacion
  -> validacion y sanitizacion
  -> scoring
  -> public/data
  -> dashboard estatico
  -> previews de alertas
```

No todas las fuentes llegan al dashboard. El MVP separa las fuentes publicables de
las fuentes en diagnostico, revision manual o dry-run.

## Empleos Publicos

Empleos Publicos es la fuente principal activa.

Flujo local:

```powershell
python scripts/fetch_empleos_publicos.py
python scripts/check_real_data.py
python scripts/build_public_data_from_real.py
python scripts/check_release_ready.py
```

Etapas:

1. `fetch_empleos_publicos.py` consulta listados publicos y genera datos reales
   locales.
2. `check_real_data.py` valida estructura, campos minimos y coherencia de la
   captura.
3. `build_public_data_from_real.py` normaliza, puntua, sanitiza y genera JSON
   publicos.
4. `check_release_ready.py` ejecuta controles de cierre antes de presentar o
   publicar.

Salida publicable:

- `public/data/opportunities.json`
- `public/data/summary.json`
- `public/data/last_run.json`
- `public/data/history.json`
- `public/data/telegram_alert_state.json`

## Fuentes municipales dry-run

Las fuentes locales se prueban primero en modo aislado. Ejemplos:

```powershell
python scripts/fetch_romeral.py
python scripts/check_romeral_source.py
python scripts/fetch_curico.py
python scripts/check_curico_source.py
python scripts/fetch_molina.py
python scripts/check_molina_source.py
python scripts/fetch_rauco.py
python scripts/check_rauco_source.py
python scripts/fetch_priority_sources.py
python scripts/check_priority_sources.py
```

Esas capturas escriben en `output/sources/` y quedan fuera de `public/data`.

Motivos para mantener una fuente en local:

- falta fecha de cierre confiable;
- hay documentos o resultados que pueden contener datos personales;
- el sitio mezcla empleo publico con intermediacion privada;
- el contenido parece historico, cerrado o duplicado;
- la fuente requiere revision humana antes de promoverse.

## Rancagua como promocion controlada

Municipalidad de Rancagua conserva dry-run completo en `output/sources/rancagua/`.
El generador publico solo puede promover registros municipales seguros:

- `status = "open_confirmed"`;
- `offer_scope = "municipal"`;
- cierre futuro confiable;
- URL trazable;
- textos sanitizados;
- `implementation_status = "published_controlled"`.

Las ofertas OMIL externas privadas quedan fuera del dashboard.

## Alertas y preview Telegram

El flujo de alertas se alimenta desde los JSON publicos ya validados.

Comandos:

```powershell
python scripts/build_telegram_preview.py
python scripts/check_telegram_preview.py
python scripts/simulate_telegram_policy.py
```

El preview construye mensajes candidatos sin enviar nada. La simulacion indica si
la politica automatica habria enviado una alerta, pero no modifica estado ni llama
a Telegram.

El envio real solo puede ocurrir con secrets configurados, activacion explicita y
comandos o workflow deliberados. Por defecto el MVP queda en preview/controlado.

## Que se publica

Se publica:

- dashboard estatico en `public/`;
- JSON sanitizados y versionables en `public/data/`;
- estado publico de historial y anti-duplicacion Telegram sin secrets;
- documentacion tecnica en `docs/`.

## Que queda solo local

Queda fuera de publicacion:

- `output/`;
- dry-runs de fuentes locales;
- reportes operativos locales;
- previews de correo, calendario o Telegram;
- capturas crudas;
- logs privados;
- `.env`;
- tokens, claves y credenciales;
- anexos o nominas con datos personales.

## Regla de frontera publica

Una oportunidad entra al dashboard solo si es publica, trazable, vigente o
operativamente valida, sanitizada y aprobada por las reglas del generador. Si hay
duda razonable, queda en revision manual o dry-run local.
