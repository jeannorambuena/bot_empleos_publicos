# feed_html.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs


FEED_URL = "https://www.empleospublicos.cl/pub/feed/feed.aspx?i=334"


class Entry(dict):
    """
    Objeto compatible con el estilo de feedparser:
    permite acceso como entry["title"] y como entry.title
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


def _find_parent_li(tag):
    while tag is not None and tag.name != "li":
        tag = tag.parent
    return tag


def get_entries():
    """
    Descarga el HTML del 'feed' y devuelve una lista de Entry:
    - entry.id
    - entry.title
    - entry.link
    - entry.summary
    - entry.published (por ahora None)
    """
    resp = requests.get(FEED_URL, timeout=30)
    resp.raise_for_status()
    html = resp.text

    soup = BeautifulSoup(html, "html.parser")
    entries = []
    seen_ids = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        title = a.get_text(strip=True)

        # Solo links de convocatorias reales
        if "convocatorias/convpostularavisoTrabajo.aspx" not in href:
            continue

        # Saltar el texto genérico
        if title.lower().startswith("llamado a concurso"):
            continue

        # ID de la convocatoria (?i=123456)
        parsed = urlparse(href)
        job_id = parse_qs(parsed.query).get("i", [None])[0]

        # Evitar duplicados
        if job_id and job_id in seen_ids:
            continue
        if job_id:
            seen_ids.add(job_id)

        li = _find_parent_li(a)
        if li:
            summary = " ".join(li.stripped_strings)
        else:
            summary = title

        link = urljoin(FEED_URL, href)

        entry = Entry(
            id=job_id,
            title=title,
            link=link,
            summary=summary,
            published=None,
        )
        entries.append(entry)

    return entries
