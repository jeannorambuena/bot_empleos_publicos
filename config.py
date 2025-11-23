"""
Configuración del bot de empleos públicos:
- URL del feed RSS
- Archivo de estado
- Palabras clave de inclusión (TI)
- Palabras clave de exclusión (profesionales de salud)
"""

# Feed general de concursos
FEED_URL = "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx"

# Listado de convocatorias filtradas por región (RM, O'Higgins, Maule)
FEED_URLS_REGIONES = [
    "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?i=15&region=Regi%C3%B3n-Metropolitana-de-Santiago",
    "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?i=7&region=Libertador-Bernardo-OHiggins",
    "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx?i=8&region=Regi%C3%B3n-del-Maule",
]


# Archivo donde guardamos los IDs ya vistos para no repetir notificaciones
STATE_FILE = "ep_state.json"
# Palabras que indican que el cargo está relacionado con:
# - Informática / TI
# - Compras públicas / abastecimiento / logística
# - Educación parvularia
#
# OJO: se buscan como "subcadenas" dentro del texto.
INCLUDE_KEYWORDS = [
    # --- Informática / TI ---
    "informática", "informatica",
    "informático", "informatico",
    "computación", "computacion",
    "tecnologías de la información", "tecnologias de la informacion",
    "gobierno digital",
    "transformación digital", "transformacion digital",

    # Cargos típicos TI
    "analista de sistemas", "analista programador",
    "ingeniero en informática", "ingeniero en informatica",
    "ingeniero informático", "ingeniero informatico",
    "ingeniero de sistemas",
    "soporte informático", "soporte informatico",
    "soporte tecnico", "soporte técnico",
    "administrador de sistemas", "administrador de redes",
    "jefe de informática", "jefe de informatica",
    "jefe de ti",
    "coordinador de informática", "coordinador de informatica",
    "coordinador ti",

    # Desarrollo de software
    "desarrollador", "programador", "desarrollo de software",
    "aplicaciones web", "full stack", "backend", "frontend",

    # Datos
    "base de datos", "bases de datos", "sql", "mysql",
    "analista de datos", "data analyst",

    # Infraestructura / seguridad
    "redes", "infraestructura ti",
    "seguridad informática", "seguridad informatica",
    "ciberseguridad", "firewall", "servidores",
    "virtualización", "virtualizacion",

    # Nube / DevOps
    "aws", "azure", "cloud", "nube", "devops",

    # --- Compras públicas / abastecimiento / logística ---
    "compras públicas", "compras publicas",
    "encargado de compras", "encargada de compras",
    "encargado de compras públicas", "encargada de compras publicas",
    "encargado de adquisiciones", "encargada de adquisiciones",
    "jefe de abastecimiento", "encargado de abastecimiento",
    "unidad de abastecimiento",
    "logística", "logistica",
    "gestión de abastecimiento", "gestion de abastecimiento",
    "mercado público", "mercado publico",
    "chilecompra",

    # --- Educación parvularia ---
    "educadora de párvulos", "educadora de parvulos",
    "educador de párvulos", "educador de parvulos",
    "educación parvularia", "educacion parvularia",
    "parvulario", "parvularia",
    "párvulo", "parvulo", "párvulos", "parvulos",
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
