# Generación de datos públicos

El generador conecta el motor inicial de scoring con los archivos JSON consumidos por
el dashboard estático. Por ahora trabaja exclusivamente con ejemplos demo y no llama
al scraper histórico, internet ni servicios externos.

## Ejecutar

Desde la raíz del repositorio:

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

## Archivos producidos

- `public/data/opportunities.json`: oportunidades normalizadas y puntuadas.
- `public/data/summary.json`: métricas resumidas para las tarjetas superiores.
- `public/data/last_run.json`: estado y hora de la última generación.

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

## Siguiente fase

La siguiente integración reemplazará el archivo de ejemplos por datos reales
normalizados desde el scraper. Antes de habilitarla deberán revisarse deduplicación,
URLs oficiales y publicación segura.
