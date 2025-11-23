"""
Bot de Empleos Públicos (versión HTML + MySQL)

- Lee la página "feed" HTML de Empleos Públicos (no es RSS real) usando feed_html.get_entries().
- Aplica filtros INCLUDE / EXCLUDE (config.py).
- Guarda / actualiza concursos en MySQL.
- Genera:
    - concursos_relevantes.csv
    - reporte_concursos.html
- Envía un correo con el resumen (si hay resultados Y hay concursos nuevos).
"""

import csv
import os
import shutil
import webbrowser
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

from config import (
    INCLUDE_KEYWORDS,
    EXCLUDE_KEYWORDS,
    EMAIL_SUBJECT,
)
from db_utils import upsert_concurso
from feed_html import get_entries


# -------------------------------
# Utilidades de scraping del "feed"
# -------------------------------


def fetch_html_entries():
    """
    Usa feed_html.get_entries() para leer la página HTML "feed" de Empleos Públicos
    y adaptarla al formato esperado por el resto del script:

    Cada dict devuelto tiene:
    - title
    - link
    - published (por ahora None o lo que rellene feed_html)
    - raw_text (texto completo o resumen de la "tarjeta")
    """
    print("Descargando feed HTML (según configuración de feed_html)...")
    raw_entries = get_entries()
    entries = []

    for e in raw_entries:
        entries.append(
            {
                "title": e["title"],
                "link": e["link"],
                "published": e.get("published"),
                "raw_text": e.get("summary", ""),
            }
        )

    print(f"Entradas detectadas en el HTML: {len(entries)}")
    return entries


# -------------------------------
# Filtros de relevancia
# -------------------------------

# (Por ahora dejamos definidas regiones por si luego queremos usarlas con datos
# de la ficha detallada, pero NO se usan en es_relevante.)

REGION_KEYWORDS = [
    # Región Metropolitana
    "región metropolitana de santiago",
    "region metropolitana de santiago",
    "región metropolitana",
    "region metropolitana",

    # Región de O'Higgins
    "región de o'higgins",
    "region de o'higgins",
    "región del libertador general bernardo o'higgins",
    "region del libertador general bernardo o'higgins",

    # Región del Maule
    "región del maule",
    "region del maule",
]


def esta_en_region_permitida(entry) -> bool:
    """
    Devuelve True solo si el concurso menciona alguna de las regiones permitidas
    o si es explícitamente para 'todas las regiones' / 'todo el país'.

    OJO: con el feed HTML estándar, normalmente NO viene la región,
    así que esta función solo será útil cuando tengamos más texto.
    """
    texto = entry["raw_text"].lower()

    # Concursos nacionales
    if "todas las regiones" in texto or "todo el país" in texto or "todo el pais" in texto:
        return True

    for region in REGION_KEYWORDS:
        if region in texto:
            return True

    return False


def es_relevante(entry) -> bool:
    """
    Aplica la lógica INCLUDE / EXCLUDE usando título + texto completo.
    - Si alguna palabra EXCLUDE aparece, se descarta.
    - Si INCLUDE_KEYWORDS está vacío -> se acepta todo (menos EXCLUDE).
    - Si INCLUDE_KEYWORDS tiene cosas -> se acepta solo si alguna aparece
      o si el texto contiene 'TI' como sigla en mayúsculas.

    Por ahora NO filtramos por región, porque el feed no trae esa información
    de forma confiable. Más adelante podremos hacerlo usando los detalles
    guardados en la base de datos.
    """
    texto = entry["title"] + " " + entry["raw_text"]
    texto_lower = texto.lower()

    # 1) Excluir profesiones de salud u otros términos no deseados
    for bad in EXCLUDE_KEYWORDS:
        if bad.lower() in texto_lower:
            return False

    # 2) Palabras clave positivas (TI, compras, educación parvularia, etc.)
    if not INCLUDE_KEYWORDS:
        tiene_match = True
    else:
        tiene_match = any(
            good.lower() in texto_lower for good in INCLUDE_KEYWORDS
        )

        # Caso especial: 'TI' como sigla en mayúsculas (Tecnologías de la Información)
        if not tiene_match:
            patrones_ti = [" TI ", " TI,", " TI.", "(TI)", "[TI]", "TI "]
            for p in patrones_ti:
                if p in texto:
                    tiene_match = True
                    break

    if not tiene_match:
        return False

    # 3) (Desactivado por ahora) Filtrar por región
    # if not esta_en_region_permitida(entry):
    #     return False

    return True


# -------------------------------
# Email
# -------------------------------


def send_email(subject: str, html_body: str, plain_body: str):
    """
    Envía un correo usando los datos SMTP del .env.
    Si falta algo crítico, muestra un mensaje y no envía.
    """
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "465"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    to_addr = os.getenv("MAIL_TO") or user

    if not (host and user and password and to_addr):
        print("SMTP no configurado completamente. No se envía correo.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr

    part1 = MIMEText(plain_body, "plain", "utf-8")
    part2 = MIMEText(html_body, "html", "utf-8")

    msg.attach(part1)
    msg.attach(part2)

    print(f"Enviando correo a {to_addr}...")
    with smtplib.SMTP_SSL(host, port) as server:
        server.login(user, password)
        server.sendmail(user, [to_addr], msg.as_string())
    print("Correo enviado.")


# -------------------------------
# Reportes (CSV + HTML)
# -------------------------------


def generar_csv(concursos_relevantes, filename="concursos_relevantes.csv"):
    """
    Genera un CSV con los concursos relevantes.
    """
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Titulo", "Link", "Fecha_Publicacion", "Es_Nuevo"])
        for c in concursos_relevantes:
            pub = c["published"]
            pub_str = pub.strftime(
                "%Y-%m-%d"
            ) if isinstance(pub, datetime) else ""
            writer.writerow(
                [
                    c["title"],
                    c["link"],
                    pub_str,
                    "SI" if c["es_nuevo"] else "NO",
                ]
            )

    print(f"CSV generado: {filename}")


def generar_html(concursos_relevantes, filename="reporte_concursos.html"):
    """
    Genera un HTML responsivo y más agradable visualmente.
    - Muestra título (link), badge NUEVO y un resumen.
    - La tabla es desplazable horizontalmente en pantallas pequeñas.
    """
    filas_html = []
    for c in concursos_relevantes:
        pub = c["published"]
        pub_str = pub.strftime("%Y-%m-%d") if isinstance(pub, datetime) else ""
        es_nuevo = c["es_nuevo"]
        clase = "nuevo" if es_nuevo else ""
        badge_nuevo = (
            '<span class="badge badge-new">Nuevo</span>' if es_nuevo else ""
        )
        resumen = (c.get("raw_text") or "").replace("\n", " ")

        filas_html.append(
            f"""
            <tr class="{clase}">
                <td class="title-cell">
                    <a href="{c['link']}" target="_blank" rel="noopener noreferrer">
                        {c['title']}
                    </a>
                    {badge_nuevo}
                    <div class="summary">{resumen}</div>
                </td>
                <td class="date-cell">{pub_str}</td>
            </tr>
            """
        )

    if not filas_html:
        cuerpo_tabla = """
            <tr>
                <td colspan="2" class="empty">
                    No hay concursos relevantes para mostrar.
                </td>
            </tr>
        """
    else:
        cuerpo_tabla = "\n".join(filas_html)

    html = f"""<!doctype html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Reporte de Concursos Relevantes</title>
    <style>
        :root {{
            --bg-body: #f4f6fb;
            --bg-card: #ffffff;
            --bg-header: #1f2937;
            --bg-header-light: #374151;
            --border-soft: #e5e7eb;
            --text-main: #111827;
            --text-muted: #6b7280;
            --accent: #2563eb;
            --accent-soft: #dbeafe;
            --badge-new-bg: #dc2626;
            --badge-new-text: #ffffff;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            padding: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: radial-gradient(circle at top left, #e0f2fe, #f9fafb 40%, #e5e7eb 100%);
            color: var(--text-main);
        }}

        .page-wrapper {{
            min-height: 100vh;
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding: 24px 12px;
        }}

        .card {{
            width: 100%;
            max-width: 1200px;
            background: var(--bg-card);
            border-radius: 16px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.35);
        }}

        .card-header {{
            background: linear-gradient(135deg, #1d4ed8, #0f766e);
            color: #f9fafb;
            padding: 18px 20px;
        }}

        .title-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: baseline;
            justify-content: space-between;
        }}

        .title-row h1 {{
            margin: 0;
            font-size: 1.4rem;
            letter-spacing: 0.02em;
        }}

        .subtitle {{
            font-size: 0.85rem;
            opacity: 0.9;
        }}

        .generated-at {{
            font-size: 0.8rem;
            padding: 4px 10px;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.35);
            border: 1px solid rgba(229, 231, 235, 0.5);
        }}

        .card-body {{
            padding: 16px 18px 18px;
        }}

        .table-wrapper {{
            width: 100%;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 600px;
        }}

        thead tr {{
            background-color: var(--bg-header);
            color: #f9fafb;
        }}

        th, td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border-soft);
            vertical-align: top;
            font-size: 0.9rem;
        }}

        th {{
            text-align: left;
            font-weight: 600;
            font-size: 0.85rem;
            white-space: nowrap;
        }}

        tbody tr:nth-child(even) {{
            background-color: #f9fafb;
        }}

        tbody tr:hover {{
            background-color: #eff6ff;
        }}

        .title-cell a {{
            color: var(--accent);
            font-weight: 600;
            text-decoration: none;
        }}

        .title-cell a:hover {{
            text-decoration: underline;
        }}

        .summary {{
            margin-top: 4px;
            font-size: 0.8rem;
            color: var(--text-muted);
            max-height: 3.6em;
            overflow: hidden;
            line-height: 1.2;
        }}

        .date-cell {{
            white-space: nowrap;
            text-align: right;
            font-variant-numeric: tabular-nums;
            color: var(--text-muted);
        }}

        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 600;
            margin-left: 6px;
        }}

        .badge-new {{
            background-color: var(--badge-new-bg);
            color: var(--badge-new-text);
        }}

        .empty {{
            text-align: center;
            padding: 32px 12px;
            color: var(--text-muted);
            font-size: 0.95rem;
        }}

        @media (max-width: 768px) {{
            .card {{
                border-radius: 0;
                box-shadow: none;
                border-left: none;
                border-right: none;
                max-width: 100%;
            }}

            .card-body {{
                padding: 12px;
            }}

            .title-row h1 {{
                font-size: 1.1rem;
            }}

            table {{
                min-width: 100%;
            }}

            th, td {{
                padding: 8px;
            }}

            .summary {{
                max-height: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="page-wrapper">
        <div class="card">
            <div class="card-header">
                <div class="title-row">
                    <div>
                        <h1>Concursos Públicos Relevantes</h1>
                        <div class="subtitle">
                            Filtro: TI / compras / educación parvularia, sin salud (según palabras clave configuradas).
                        </div>
                    </div>
                    <div class="generated-at">
                        Generado el {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    </div>
                </div>
            </div>
            <div class="card-body">
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Título y resumen</th>
                                <th>Fecha publicación</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cuerpo_tabla}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML generado: {filename}")
    # Si lo ejecutas manualmente y quieres abrir el reporte automáticamente,
    # puedes descomentar la siguiente línea:
    # webbrowser.open(os.path.abspath(filename))


# -------------------------------
# MAIN
# -------------------------------


def main():
    load_dotenv()

    # 1) Leer "feed" HTML (vía feed_html.get_entries)
    entries = fetch_html_entries()
    print(f"Cantidad total de entradas encontradas: {len(entries)}")

    # 2) Filtrar por relevancia
    relevantes = [e for e in entries if es_relevante(e)]
    print(f"Total concursos relevantes (según filtros): {len(relevantes)}")

    concursos_relevantes = []

    # 3) Guardar / actualizar en MySQL
    for e in relevantes:
        guid = e["link"]  # usamos el link como identificador único
        titulo = e["title"]
        link = e["link"]
        fecha_publicacion = e["published"]

        es_nuevo = upsert_concurso(
            guid=guid,
            titulo=titulo,
            link=link,
            fecha_publicacion=fecha_publicacion,
        )

        concursos_relevantes.append(
            {
                "title": titulo,
                "link": link,
                "published": fecha_publicacion,
                "es_nuevo": es_nuevo,
                "raw_text": e.get("raw_text", ""),
            }
        )

    # 4) Si no hay concursos relevantes, no hacemos nada más
    if not concursos_relevantes:
        print("No hay concursos relevantes, no se generan reportes ni correo.")
        return

    # 5) Revisar si hay concursos NUEVOS
    nuevos = [c for c in concursos_relevantes if c["es_nuevo"]]
    total = len(concursos_relevantes)
    total_nuevos = len(nuevos)

    if total_nuevos == 0:
        print(
            f"No hay concursos nuevos ({total} relevantes, 0 nuevos). "
            "Se genera reporte, sin copias históricas ni correo."
        )
    else:
        print(
            f"Hay {total_nuevos} concursos nuevos (de {total} relevantes). "
            "Se actualizan reportes, se crean copias con fecha y se puede enviar correo."
        )

    # 6) Generar reportes (siempre que haya relevantes)
    generar_csv(concursos_relevantes)
    generar_html(concursos_relevantes)

    # 7) Solo si hay concursos nuevos: copiar a reportes/ y enviar correo
    if total_nuevos > 0:
        import os
        import shutil

        os.makedirs("reportes", exist_ok=True)
        hoy = datetime.now().strftime("%Y-%m-%d")

        # Copia del HTML
        shutil.copy(
            "reporte_concursos.html",
            os.path.join("reportes", f"reporte_concursos_{hoy}.html"),
        )

        # Copia del CSV
        shutil.copy(
            "concursos_relevantes.csv",
            os.path.join("reportes", f"concursos_relevantes_{hoy}.csv"),
        )

        # Preparar cuerpo del correo
        plain = [
            f"Concursos relevantes encontrados: {total}",
            f"Nuevos en esta ejecución: {total_nuevos}",
            "",
            "Listado:",
        ]
        for c in concursos_relevantes:
            pub = c["published"]
            pub_str = pub.strftime(
                "%Y-%m-%d") if isinstance(pub, datetime) else ""
            marca = " (NUEVO)" if c["es_nuevo"] else ""
            plain.append(f"- {c['title']} [{pub_str}]{marca} -> {c['link']}")

        plain_body = "\n".join(plain)

        try:
            with open("reporte_concursos.html", "r", encoding="utf-8") as f:
                html_body = f.read()
        except FileNotFoundError:
            html_body = plain_body  # fallback

        send_email(EMAIL_SUBJECT, html_body, plain_body)
    else:
        print(
            "Como no hay concursos nuevos, no se envía correo ni se crean copias fechadas."
        )


if __name__ == "__main__":
    main()
