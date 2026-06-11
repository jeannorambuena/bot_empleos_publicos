# Checklist final de release v1.0.0

Checklist reproducible para cerrar Radar Laboral Publico Chile como release
`v1.0.0` de portafolio.

## 1. Confirmar estado Git

```powershell
git status --short --branch
```

Criterios:

- Rama esperada: `main`.
- Antes de crear el tag, el estado debe estar limpio despues del commit final.
- No deben existir cambios no revisados en `public/data/`, workflows, scripts
  funcionales, `.env` o secrets.

## 2. Ejecutar QA integral

```powershell
python scripts/check_all.py
```

Resultado esperado:

```text
OK: todas las pruebas integrales pasaron
```

Este comando valida datos reales, datos publicos, historial, dashboard, fuentes,
sanitizacion, panel de revision, Telegram y release final.

## 3. Ejecutar release check

```powershell
python scripts/check_release_ready.py
```

Resultado esperado:

```text
OK: release MVP listo
```

Este comando confirma que el MVP sigue listo para presentacion/publicacion local.

## 4. Revisar `public/data`

```powershell
git status --short public/data
```

Criterios:

- No debe haber cambios inesperados.
- Los datos publicos vigentes deben seguir validados por los checks.
- No deben existir registros con RUN/RUT, nominas, resultados sensibles ni datos
  personales innecesarios.

## 5. Revisar secrets y `.env`

```powershell
git status --short .env .env.example
```

Criterios:

- `.env` no debe estar versionado.
- `.env.example` solo debe contener placeholders.
- No deben existir tokens, claves, credenciales SMTP ni credenciales Telegram en
  archivos versionados.

## 6. Confirmar GitHub Pages

Antes de presentar publicamente:

- Confirmar que GitHub Pages apunta a `public/` o al flujo configurado del repo.
- Abrir el dashboard publicado o levantarlo localmente:

```powershell
python -m http.server 8000 --directory public
```

Abrir:

```text
http://localhost:8000
```

Criterios:

- El dashboard carga.
- Muestra 101 oportunidades publicas validadas.
- Muestra estado MVP y notas de privacidad/verificacion.
- Los enlaces a fuente oficial deben revisarse antes de cualquier postulacion.

## 7. Preparar commit final

Despues de revisar el diff:

```powershell
git status --short
git diff --stat
```

Criterios:

- Solo deben incluirse cambios esperados del cierre.
- No incluir `output/`, logs, `.env`, datos locales privados ni artefactos sensibles.

## 8. Crear tag `v1.0.0`

Cuando el commit final ya este creado y subido:

```powershell
git tag -a v1.0.0 -m "Release v1.0.0 - portfolio MVP"
git push origin v1.0.0
```

Este paso no forma parte de los lotes de edicion sin commit/push. Debe ejecutarse
solo cuando el responsable decida publicar oficialmente el release.

## 9. Confirmacion final

El release `v1.0.0` queda listo cuando:

- `git status --short` esta limpio.
- `python scripts/check_all.py` pasa.
- `python scripts/check_release_ready.py` pasa.
- `public/data` no tiene cambios inesperados.
- No hay secrets ni `.env` versionados.
- GitHub Pages fue revisado.
- El tag `v1.0.0` fue creado sobre el commit final correcto.
