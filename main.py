import os
import json
import csv
from datetime import datetime

import feedparser

from config import (
    FEED_URL,
    STATE_FILE,
    INCLUDE_KEYWORDS,
    EXCLUDE_KEYWORDS,
)


def load_state() -> set:
    """
    Carga el conjunto de IDs de concursos ya vistos desde STATE_FILE.
    Si el archivo no existe o hay error, devuelve un conjunto vacío.
    """
    if not os.path.exists(STATE_FILE):
        return set()

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data)
    except Exception:
        # Si hay algún problema leyendo el JSON, empezamos desde cero.
        return set()


def save_state(ids: set) -> None:
    """Guarda el conjunto de IDs de concursos ya vistos en STATE_FILE."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, ensure_ascii=False, indent=2)


def es_relevante(texto: str) -> bool:
    """
    Determina si un concurso es relevante según el texto (título + resumen).

    Reglas:
    - Si contiene alguna palabra de EXCLUDE_KEYWORDS (profesiones de salud) -> False.
    - Si INCLUDE_KEYWORDS está vacío -> True (acepta todo lo que no sea salud).
    - Si INCLUDE_KEYWORDS tiene elementos -> True sólo si aparece al menos
      una palabra de inclusión.
    """
    t = texto.lower()

    # 1) Excluir profesionales de salud
    if any(pal.lower() in t for pal in EXCLUDE_KEYWORDS):
        return False

    # 2) Si no hay palabras de inclusión, aceptamos todo lo no-salud
    if not INCLUDE_KEYWORDS:
        return True

    # 3) Requiere al menos una palabra de inclusión
    return any(pal.lower() in t for pal in INCLUDE_KEYWORDS)


def save_csv(entries: list, filename: str) -> None:
    """
    Guarda los concursos relevantes en un archivo CSV.
    Columnas: titulo, link, fecha_publicacion, es_nuevo
    """
    fieldnames = ["titulo", "link", "fecha_publicacion", "es_nuevo"]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for e in entries:
            writer.writerow(
                {
                    "titulo": e["title"],
                    "link": e["link"],
                    "fecha_publicacion": e["published"],
                    "es_nuevo": "sí" if e["nuevo"] else "no",
                }
            )


def save_html(entries: list, filename: str) -> None:
    """
    Genera un archivo HTML responsivo con la tabla de concursos relevantes.
    Cada fila muestra: título (con enlace), etiqueta 'Nuevo' cuando corresponda,
    fecha de publicación.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = []
    for e in entries:
        title = e["title"]
        link = e["link"]
        published = e["published"]
        badge = (
            "<span class='badge badge-new'>Nuevo</span>"
            if e["nuevo"]
            else ""
        )

        rows.append(
            f"""
            <tr>
                <td>
                    <a href="{link}" target="_blank">{title}</a>
                    {badge}
                </td>
                <td>{published}</td>
            </tr>
            """
        )

    rows_html = "\n".join(rows)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>Concursos públicos relevantes (TI)</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 0;
            padding: 1rem;
            background: #f5f7fa;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
            background: #ffffff;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.08);
        }}
        h1 {{
            font-size: 1.4rem;
            margin-bottom: 0.25rem;
        }}
        .subtitle {{
            font-size: 0.9rem;
            color: #555;
            margin-bottom: 1rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            vertical-align: top;
        }}
        th {{
            border-bottom: 2px solid #e0e4ec;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #666;
        }}
        tr:nth-child(even) td {{
            background: #fafbff;
        }}
        a {{
            color: #1a73e8;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .badge {{
            display: inline-block;
            margin-left: 0.5rem;
            padding: 0.15rem 0.45rem;
            border-radius: 999px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}
        .badge-new {{
            background: #0f9d58;
            color: #fff;
        }}
        @media (max-width: 600px) {{
            th:nth-child(2), td:nth-child(2) {{
                font-size: 0.8rem;
                white-space: nowrap;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Concursos públicos relevantes (TI)</h1>
        <p class="subtitle">Última actualización: {now_str}</p>
        <table>
            <thead>
                <tr>
                    <th>Concurso</th>
                    <th>Publicación</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)


def main() -> None:
    """
    Flujo principal del bot (modo archivos):
    - Carga estado previo (ep_state.json).
    - Lee el feed RSS de Empleos Públicos.
    - Detecta concursos nuevos.
    - Filtra según lógica TI / no-salud.
    - Genera:
        - concursos_relevantes.csv
        - reporte_concursos.html
    - Actualiza el estado.
    """
    vistos = load_state()
    nuevos_ids = set(vistos)
    relevantes = []

    feed = feedparser.parse(FEED_URL)

    print("Cantidad de entradas en el feed:", len(feed.entries))

    for e in feed.entries:
        guid = e.get("id") or e.get("link")
        if not guid:
            continue

        es_nuevo = guid not in vistos
        nuevos_ids.add(guid)

        title_raw = e.get("title", "(Sin título)")
        link = e.get("link", "#")
        summary = e.get("summary", "") or ""
        published = e.get("published", "")

        texto = f"{title_raw} {summary}"
        relevante = es_relevante(texto)

        if relevante:
            title = title_raw + (" (nuevo)" if es_nuevo else "")
            relevantes.append(
                {
                    "id": guid,
                    "title": title,
                    "link": link,
                    "published": published,
                    "nuevo": es_nuevo,
                }
            )

    print(f"Total concursos relevantes (TI / no salud): {len(relevantes)}")

    # Generar archivos sólo con los relevantes
    save_csv(relevantes, "concursos_relevantes.csv")
    save_html(relevantes, "reporte_concursos.html")
    print("Archivos generados:")
    print(" - concursos_relevantes.csv")
    print(" - reporte_concursos.html")

    # Actualizar estado
    save_state(nuevos_ids)
    print("Estado guardado en", STATE_FILE)


if __name__ == "__main__":
    main()
