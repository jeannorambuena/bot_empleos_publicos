import os
from datetime import datetime

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv


def get_connection():
    """
    Crea y devuelve una conexión a MySQL usando variables de entorno.
    Lee los valores desde el archivo .env.
    """
    load_dotenv()

    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
    )
    return conn


def has_any_concurso():
    """
    Devuelve True si la tabla concursos tiene al menos un registro.
    Esto sirve para saber si es la primera ejecución lógica del bot.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM concursos LIMIT 1")
        row = cursor.fetchone()
        return row is not None
    finally:
        cursor.close()
        conn.close()


def upsert_concurso(guid, titulo, link, fecha_publicacion=None):
    """
    Inserta un concurso nuevo o actualiza uno existente según el GUID.
    Devuelve True si el concurso era NUEVO en esta ejecución (no existía antes),
    False si ya existía y solo se actualizó.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)

        # ¿Existe ya este guid?
        cursor.execute("SELECT id FROM concursos WHERE guid = %s", (guid,))
        row = cursor.fetchone()

        ahora = datetime.now()

        if row is None:
            # INSERT nuevo
            cursor.execute(
                """
                INSERT INTO concursos (guid, titulo, link, fecha_publicacion, creado_en, actualizado_en)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (guid, titulo, link, fecha_publicacion, ahora, ahora),
            )
            conn.commit()
            return True  # es nuevo
        else:
            # UPDATE (por si cambió título o fecha)
            cursor.execute(
                """
                UPDATE concursos
                SET titulo = %s,
                    link = %s,
                    fecha_publicacion = %s,
                    actualizado_en = %s
                WHERE guid = %s
                """,
                (titulo, link, fecha_publicacion, ahora, guid),
            )
            conn.commit()
            return False  # ya existía

    finally:
        cursor.close()
        conn.close()


def get_concursos_sin_detalle(limit=20):
    """
    Devuelve una lista de concursos que aún no tienen detalle completo
    (ministerio, comuna o fecha_cierre en NULL).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, guid, titulo, link
            FROM concursos
            WHERE ministerio IS NULL
               OR comuna IS NULL
               OR fecha_cierre IS NULL
            ORDER BY creado_en DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        return rows
    finally:
        cursor.close()
        conn.close()


def actualizar_detalle_concurso(concurso_id, ministerio, comuna, fecha_cierre):
    """
    Actualiza los campos de detalle de un concurso:
    ministerio, comuna y fecha_cierre.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        ahora = datetime.now()
        cursor.execute(
            """
            UPDATE concursos
            SET ministerio = %s,
                comuna = %s,
                fecha_cierre = %s,
                actualizado_en = %s
            WHERE id = %s
            """,
            (ministerio, comuna, fecha_cierre, ahora, concurso_id),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
