# Bot Empleos Públicos (Chile) – versión HTML + MySQL

Script en Python que consulta las **convocatorias públicas** de  
[https://www.empleospublicos.cl](https://www.empleospublicos.cl), extrae las ofertas desde el **HTML**, aplica filtros (TI / compras públicas / educación parvularia, excluyendo salud), guarda un histórico en **MySQL** y genera:

- Un archivo `concursos_relevantes.csv` con los concursos relevantes del momento.
- Un reporte HTML responsivo `reporte_concursos.html` con todos los concursos relevantes.
- Opcionalmente, un correo con **solo los concursos nuevos** detectados desde la última ejecución.
- Copias históricas fechadas en la carpeta `reportes/` (solo cuando hay novedades).

La idea es que **cualquier persona** pueda:

- Ajustar fácilmente los filtros de búsqueda (`config.py`).
- Reutilizar la base de datos para sus propias postulaciones o análisis.
- Automatizar la ejecución diaria en Windows (Programador de tareas).

---

## ¿Cómo funciona?

1. `main.py` llama a `feed_html.get_entries()` para leer las convocatorias desde la página HTML de Empleos Públicos.
2. Cada convocatoria se transforma en un diccionario con:
   - `title`, `link`, `published`, `raw_text`.
3. Se aplican los filtros definidos en `config.py`:
   - `INCLUDE_KEYWORDS`: TI, compras públicas, educación parvularia, etc.
   - `EXCLUDE_KEYWORDS`: profesiones de salud (médico, enfermera, kinesiólogo, etc.).
4. Por cada concurso relevante se llama a `upsert_concurso(...)` (definido en `db_utils.py`), que trabaja sobre la base de datos MySQL creada por `concursos.sql`:
   - Si el concurso es nuevo → se inserta.
   - Si ya existe → se actualiza lo necesario.
   - La función devuelve un flag `es_nuevo` (True/False).
5. Dependiendo del resultado:
   - **Si no hay concursos relevantes** → no se genera nada.
   - **Si hay relevantes pero ninguno nuevo** → se mantiene el reporte anterior.
   - **Si hay al menos un concurso nuevo**:
     - Se genera/actualiza:
       - `concursos_relevantes.csv`
       - `reporte_concursos.html`
     - Se guardan copias con fecha en `reportes/`.
     - Opcionalmente se envía un correo con el resumen (si SMTP está configurado).

---

## Requisitos

- **Sistema operativo:** Windows
- **Software base:**
  - [WAMP](https://www.wampserver.com/) (incluye MySQL)
  - Python **3.10+**
- **Correo (opcional):**
  - Cuenta SMTP (por ejemplo, Gmail) para enviar notificaciones de nuevos concursos.

---

## Configuración

### 1. Base de datos (MySQL)

La estructura de la base de datos está definida en el archivo:

- `concursos.sql`

Pasos típicos:

1. Iniciar MySQL (por ejemplo desde WAMP).
2. Crear la base de datos (si no existe), por ejemplo:

   ```sql
   CREATE DATABASE bot_empleos
     CHARACTER SET utf8mb4
     COLLATE utf8mb4_unicode_ci;
