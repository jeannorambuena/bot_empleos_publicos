# Flujo local con datos reales

El flujo real local captura convocatorias públicas desde Empleos Públicos, las
normaliza al contrato comunitario y permite regenerar el dashboard sin depender del
scraper histórico. Todavía no existe automatización ni ejecución en GitHub Actions.
La interfaz visual conserva su aviso de prototipo mientras este flujo permanezca en
revisión local.

## Fuente inicial

La primera fuente es `empleospublicos.cl`. El conector reutiliza las URLs regionales
de `config.py` para Metropolitana, O’Higgins y Maule. Usa un `User-Agent` explícito,
timeout y diagnóstico por URL revisada.

## Ejecutar captura

```powershell
.\venv\Scripts\python.exe scripts\fetch_empleos_publicos.py
```

Genera archivos locales ignorados por Git:

- `data/raw/empleos_publicos_raw.json`
- `data/normalized/empleos_publicos_normalized.json`

Luego valida y publica localmente:

```powershell
.\venv\Scripts\python.exe scripts\check_real_data.py
.\venv\Scripts\python.exe scripts\build_public_data_from_real.py
.\venv\Scripts\python.exe scripts\check_public_data.py
```

## Diferencia entre demo y real

Los ejemplos demo mantienen `is_demo: true`, `url_status: "demo"` y
`source_url: null`.

Las oportunidades reales locales usan `is_demo: false`. Si existe una URL oficial,
se conserva en `source_url` con `url_status: "ok"`. Si no puede extraerse, el campo
queda `null` y el estado pasa a `missing`; el flujo no inventa enlaces.

## Validar enlaces

Antes de publicar resultados reales, revisar una muestra de `source_url` y confirmar:

- Que la URL pertenece al dominio institucional esperado.
- Que abre la convocatoria correcta.
- Que la fecha de cierre coincide con la ficha oficial.
- Que no se publicó información privada innecesaria.

## Limitaciones

- El parser depende de la estructura HTML actual de Empleos Públicos.
- La comuna no siempre está disponible en el listado.
- El flujo aún no deduplica entre múltiples sitios institucionales.
- No se ejecuta automáticamente.
- No envía alertas reales ni conecta calendarios externos.

## Próximos pasos

Antes de automatizar será necesario añadir pruebas con HTML guardado, revisar
deduplicación, revisar periódicamente la calibración descrita en
`docs/scoring-calibration.md`, decidir qué niveles publicar y validar seguridad de
datos reales.
