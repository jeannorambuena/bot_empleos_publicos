\# Bot Empleos Públicos (Chile)



Script en Python que consulta diariamente el feed RSS de \[https://www.empleospublicos.cl](https://www.empleospublicos.cl), filtra los concursos relacionados con informática / TI, guarda un histórico en MySQL (WAMP) y genera:



\- Un archivo `concursos\_relevantes.csv` con los concursos relevantes.

\- Un reporte HTML responsivo `reporte\_concursos.html` con todos los concursos relevantes.

\- Opcionalmente, un correo con \*\*los nuevos concursos\*\* detectados desde la última ejecución.



La idea es que cualquier persona pueda adaptar los filtros y reutilizar la base de datos para sus propias postulaciones o análisis.



---



\## Requisitos



\- Windows con:

&nbsp; - \[WAMP](https://www.wampserver.com/) (incluye MySQL)

&nbsp; - Python 3.10+ instalado

\- Cuenta de correo (por ejemplo Gmail) para enviar notificaciones (opcional)



---



\## Estructura del proyecto



```text

bot\_empleos\_publicos/

├─ venv/                     # Entorno virtual de Python (no se versiona)

├─ config.py                 # Filtros TI / salud + URL del feed

├─ main.py                   # Script principal (lee RSS, guarda en MySQL, genera reportes)

├─ db\_utils.py               # Conexión y funciones de acceso a MySQL

├─ .env                      # Configuración local (SMTP + MySQL) - NO subir a GitHub

├─ concursos\_relevantes.csv  # Salida CSV (generado por el script)

├─ reporte\_concursos.html    # Reporte HTML responsivo (generado por el script)

├─ .gitignore

└─ README.md



