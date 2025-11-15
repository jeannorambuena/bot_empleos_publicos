"""
Configuración del bot de empleos públicos:
- URL del feed RSS
- Archivo de estado
- Palabras clave de inclusión (TI)
- Palabras clave de exclusión (profesionales de salud)
"""

# Feed general de concursos
FEED_URL = "https://www.empleospublicos.cl/pub/feed/feed.aspx?i=334"

# Archivo donde guardamos los IDs ya vistos para no repetir notificaciones
STATE_FILE = "ep_state.json"

# Palabras que indican que el cargo está relacionado con informática / TI.
# Si quieres que te lleguen TODOS los cargos (menos los de salud),
# puedes dejar esta lista vacía: INCLUDE_KEYWORDS = []
INCLUDE_KEYWORDS = [
    # Informática general
    "informática", "informatica", "computación", "computacion",
    "tecnologías de la información", "tic", "ti",

    # Cargos típicos TI
    "analista de sistemas", "analista programador",
    "ingeniero en informática", "ingeniero de sistemas",
    "soporte informático", "soporte tecnico", "soporte técnico",
    "administrador de sistemas", "administrador de redes",
    "jefe de informática", "jefe de ti",
    "coordinador de informática", "coordinador ti",

    # Desarrollo de software
    "desarrollador", "programador", "desarrollo de software",
    "aplicaciones web", "full stack", "backend", "frontend",

    # Datos
    "base de datos", "bases de datos", "sql", "mysql",
    "analista de datos", "data analyst",

    # Infraestructura / seguridad
    "redes", "infraestructura ti",
    "seguridad informática", "ciberseguridad", "firewall", "servidores",
    "virtualización", "virtualizacion",

    # Modernización / digitalización
    "transformación digital", "transformacion digital",
    "gobierno digital", "modernización", "modernizacion",
    "automatización", "automatizacion",

    # Nube / DevOps
    "aws", "azure", "cloud", "nube", "devops",
]

# Palabras que indican que es un profesional de salud (no queremos estos cargos).
# OJO: aquí NO incluimos "salud", "hospital", "cesfam", etc.
EXCLUDE_KEYWORDS = [
    "médico", "medico", "médica", "medica",
    "cirujano", "cirujana", "cirugía", "cirugia",
    "enfermero", "enfermera", "enfermería", "enfermeria",
    "kinesiólogo", "kinesiologo", "kinesióloga", "kinesiologa",
    "terapeuta ocupacional", "fisioterapeuta",
    "odontólogo", "odontologo", "odontóloga", "odontologa",
    "nutricionista",
    "psicólogo", "psicologo", "psicóloga", "psicologa",
    "psiquiatra",
    "matrona", "obstetra",
    "tecnólogo médico", "tecnologo medico",
    "bioquímico", "bioquimico",
    "laboratorista clínico", "laboratorista clinico",
    "fonoaudiólogo", "fonoaudiologo", "fonoaudióloga", "fonoaudiologa",
]

EMAIL_SUBJECT = "Nuevos concursos públicos relevantes (TI)"
