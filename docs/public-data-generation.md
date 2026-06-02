# Generación de datos públicos

Los generadores conectan entradas normalizadas con los archivos JSON consumidos por
el dashboard estático. El repositorio conserva un flujo demo y un flujo real local
para Empleos Públicos. Ambos mantienen separada la captura, la normalización, el
scoring y la publicación.

## Ejecutar

Para regenerar datos demo desde la raíz del repositorio:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\venv\Scripts\python.exe scripts\build_public_data.py
```

El script:

1. Carga `config/profile.example.json`.
2. Lee `examples/sample_opportunities.json`.
3. Completa campos seguros cuando faltan.
4. Calcula scoring y motivos de alerta.
5. Ordena por puntaje, cierre próximo y fecha de detección.
6. Regenera los JSON públicos.

Para generar datos reales locales desde una captura normalizada de Empleos Públicos:

```powershell
.\venv\Scripts\python.exe scripts\fetch_empleos_publicos.py
.\venv\Scripts\python.exe scripts\check_real_data.py
.\venv\Scripts\python.exe scripts\build_public_data_from_real.py
```

## Archivos producidos

- `public/data/opportunities.json`: oportunidades normalizadas y puntuadas.
- `public/data/summary.json`: métricas resumidas para las tarjetas superiores.
- `public/data/last_run.json`: estado y hora de la última generación.
- `public/data/history.json`: historial público versionable para distinguir nuevas
  oportunidades y registros previamente vistos.

## Conexión con el dashboard

`public/index.html` carga estos JSON mediante JavaScript. No es necesario modificar el
HTML ni sus assets para regenerar los datos.

Mientras la entrada provenga de `examples/`, el generador fuerza:

- `"is_demo": true`
- `"url_status": "demo"`
- `"source_url": null`

Así el dashboard mantiene deshabilitados los enlaces y evita presentar convocatorias
ficticias como si fueran reales.

## Validar

```powershell
.\venv\Scripts\python.exe scripts\check_public_data.py
```

El validador comprueba archivos requeridos, contrato mínimo, rangos de scoring,
coherencia de niveles y ausencia de URLs en registros demo.

## Fuentes futuras

Una fuente futura debe producir primero oportunidades normalizadas compatibles con
`docs/source-contract.md`. Después se validan identificadores estables, URLs oficiales,
vigencia, trazabilidad y duplicados antes de combinar su salida con el generador
público.

Cada nueva fuente real debe incorporarse mediante un PR independiente. Este enfoque
protege la captura vigente de Empleos Públicos y permite auditar o revertir un parser
sin afectar a los demás.
