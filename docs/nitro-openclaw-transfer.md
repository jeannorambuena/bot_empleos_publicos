# Traspaso controlado a Nitro/OpenClaw

GitHub sigue siendo la fuente oficial del proyecto. Nitro/OpenClaw será un entorno
de ejecución futuro y no debe mezclar este repositorio con otros proyectos.

## Preparación en Nitro

Ejecutar en Linux cuando corresponda:

```bash
mkdir -p ~/.openclaw/workspace/repos
cd ~/.openclaw/workspace/repos
git clone <URL-DEL-REPOSITORIO> bot_empleos_publicos
cd bot_empleos_publicos
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python scripts/check_public_data.py
python scripts/check_pages_ready.py
python scripts/build_alert_preview.py
python scripts/check_alert_preview.py
python scripts/build_calendar_preview.py
python scripts/check_calendar_preview.py
python scripts/build_telegram_preview.py
python scripts/check_telegram_preview.py
```

## Controles operativos

1. Mantener `main` limpia y sincronizada con GitHub.
2. Usar ramas de trabajo y PRs para cambios.
3. Probar scripts localmente antes de automatizar.
4. No conectar Telegram real hasta validar previews y secretos.
5. No almacenar `.env`, tokens ni credenciales en Git.
6. No mezclar carpetas, estados ni artefactos con otros proyectos.
