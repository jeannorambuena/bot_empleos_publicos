# Resumen tecnico

Radar Laboral Publico Chile es un MVP de automatizacion responsable con datos
publicos. Captura oportunidades laborales, las normaliza, aplica scoring,
sanitizacion y validaciones, y publica un dashboard estatico.

## Stack

- Python.
- HTML.
- CSS.
- JavaScript.
- JSON.
- GitHub Actions.
- GitHub Pages.
- Telegram Bot API en modo controlado.

## Componentes principales

- `scripts/fetch_empleos_publicos.py`: captura y normaliza datos reales locales.
- `scripts/check_real_data.py`: valida captura real.
- `scripts/build_public_data_from_real.py`: genera datos publicos desde datos reales.
- `scripts/check_public_data.py`: valida contrato de `public/data`.
- `scripts/check_pages_ready.py`: valida dashboard estatico.
- `scripts/check_source_candidates.py`: valida catalogo territorial.
- `scripts/check_sources_config.py`: valida configuracion de fuentes.
- `scripts/check_source_sanitization.py`: valida privacidad y sanitizacion.
- `scripts/check_priority_sources.py`: valida batch dry-run P1.
- `scripts/build_telegram_preview.py`: genera preview Telegram sin envio.
- `scripts/check_telegram_preview.py`: valida preview Telegram.
- `scripts/simulate_telegram_policy.py`: simula politica de envio.
- `scripts/check_release_ready.py`: check final de release.
- `scripts/check_all.py`: QA integral local.

## Arquitectura

```text
fuentes publicas
  -> scripts de captura
  -> datos reales locales
  -> normalizacion
  -> sanitizacion
  -> scoring
  -> public/data/*.json
  -> dashboard estatico
  -> previews y QA
```

`public/data` actua como frontera publica. Los dry-runs, capturas locales, previews,
logs y reportes operativos quedan fuera del dashboard.

## Validaciones

QA integral:

```powershell
python scripts/check_all.py
```

Release check:

```powershell
python scripts/check_release_ready.py
```

Las validaciones cubren:

- datos reales;
- datos publicos;
- historial;
- dashboard;
- configuracion de fuentes;
- catalogo de fuentes candidatas;
- sanitizacion;
- fuentes prioritarias;
- panel de revision humana;
- preview Telegram;
- politica Telegram simulada;
- reglas finales de release.

## Seguridad

El proyecto mantiene controles explicitos:

- no publica RUN/RUT;
- no versiona `.env`;
- no versiona secrets;
- no usa credenciales personales;
- no accede a portales privados;
- no realiza scraping autenticado;
- no automatiza postulaciones;
- no publica artefactos locales de `output/`.

Telegram real requiere secrets y activacion explicita. El modo por defecto validado
es preview/controlado.

## Operacion

Instalacion local:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Dashboard local:

```powershell
python -m http.server 8000 --directory public
```

Refresco de datos reales:

```powershell
python scripts/fetch_empleos_publicos.py
python scripts/check_real_data.py
python scripts/build_public_data_from_real.py
python scripts/check_release_ready.py
```

## QA integral

`scripts/check_all.py` orquesta las validaciones principales en orden controlado y
detiene la ejecucion si una falla. El resultado exitoso esperado es:

```text
OK: todas las pruebas integrales pasaron
```

## Estado actual

El proyecto esta validado como MVP funcional local, con 101 oportunidades publicas,
53 fuentes candidatas, 7 fuentes configuradas, dashboard estatico y documentacion
tecnica. No debe presentarse como plataforma comercial completa.
