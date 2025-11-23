@echo off
cd /d C:\dev\bot_empleos_publicos

REM Activar el entorno virtual
call venv\Scripts\activate.bat

REM Crear carpeta de logs si no existe
if not exist logs mkdir logs

REM Ejecutar el bot y guardar salida en log
python main.py >> logs\bot_empleos.log 2>&1
