# Publicación futura en GitHub Pages

GitHub Pages permitirá publicar el dashboard como un sitio estático comunitario. La
preparación ya existe, pero el despliegue no se activa automáticamente hasta que el
workflow sea revisado, fusionado a `main` y Pages se configure en GitHub.

## Carpeta publicada

La única carpeta publicada será:

```text
public/
```

Contiene:

- `index.html`
- `assets/`
- `data/`

El sitio actual mantiene datos demo/prototipo. Todavía no representa convocatorias
reales obtenidas automáticamente desde el scraper.

## Workflow preparado

`.github/workflows/pages.yml` usa acciones oficiales de GitHub Pages y permisos
mínimos:

- `contents: read`
- `pages: write`
- `id-token: write`

El workflow sube `public/` como artefacto y despliega ese contenido cuando:

- Se ejecuta manualmente con `workflow_dispatch`.
- Hay un push a `main` que modifica `public/**` o el propio workflow.

El workflow no contiene credenciales, SMTP ni integración con calendarios.

## Activación manual futura

Después de revisar y fusionar los cambios:

1. Abre el repositorio en GitHub.
2. Ve a **Settings**.
3. Abre **Pages**.
4. En **Build and deployment**, selecciona **GitHub Actions** como fuente.
5. Ejecuta manualmente el workflow o publica un cambio revisado en `public/`.
6. Revisa la URL entregada por GitHub Pages.

No ejecutar estos pasos mientras la rama siga en revisión.

## Validación local

Antes de fusionar:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\venv\Scripts\python.exe scripts\check_pages_ready.py
```

El validador comprueba estructura estática, JSON válidos, título esperado, ausencia
de `.env` en la raíz y ausencia de `output/` dentro de `public/`.

## Seguridad

Nunca subir:

- `.env`
- Credenciales
- Logs privados
- Bases reales
- `output/`

Los archivos publicados deben revisarse antes de cada despliegue, especialmente
cuando el proyecto comience a incorporar datos reales.
