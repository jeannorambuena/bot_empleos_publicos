# test_feed.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

FEED_URL = "https://www.empleospublicos.cl/pub/feed/feed.aspx?i=334"


def fetch_html():
    resp = requests.get(FEED_URL, timeout=30)
    resp.raise_for_status()
    return resp.text


def find_parent_li(tag):
    """Sube en el árbol HTML hasta encontrar el <li> que contiene la convocatoria."""
    while tag is not None and tag.name != "li":
        tag = tag.parent
    return tag


def parse_entries(html: str):
    """
    Extrae las convocatorias desde el HTML "feed" de Empleos Públicos.
    Devuelve una lista de diccionarios con title, link, summary.
    Evita duplicados y omite los enlaces genéricos 'LLamado a Concurso'.
    """
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen_ids = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)

        # Solo los links de convocatorias reales
        if "convocatorias/convpostularavisoTrabajo.aspx" not in href:
            continue

        # Saltar el texto genérico
        if title.lower().startswith("llamado a concurso"):
            continue

        # Extraer el ID de la convocatoria (?i=123456)
        parsed = urlparse(href)
        job_id = parse_qs(parsed.query).get("i", [None])[0]

        # Evitar duplicados por ID
        if job_id and job_id in seen_ids:
            continue
        if job_id:
            seen_ids.add(job_id)

        li = find_parent_li(a)
        if li:
            summary = " ".join(li.stripped_strings)
        else:
            summary = title

        link = urljoin(FEED_URL, href)

        entries.append(
            {
                "id": job_id,
                "title": title,
                "link": link,
                "summary": summary,
            }
        )

    return entries


def main():
    html = fetch_html()
    print(f"Largo del HTML descargado: {len(html)}")

    entries = parse_entries(html)
    print(f"Total de convocatorias detectadas (únicas): {len(entries)}\n")

    # Muestra algunas para verificar
    for e in entries[:10]:
        print("- ID    :", e["id"])
        print("  Título:", e["title"])
        print("  Link  :", e["link"])
        print("  Resumen:", e["summary"][:200], "...\n")


if __name__ == "__main__":
    main()
