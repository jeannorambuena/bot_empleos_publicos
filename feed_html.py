# feed_html.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from config import FEED_URLS_REGIONES


FEED_URL = "https://www.empleospublicos.cl/pub/convocatorias/convocatorias.aspx"


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
    Lee las páginas de convocatorias filtradas por región (RM, O'Higgins, Maule)
    y devuelve una lista de Entry con:
    - id       -> parámetro i de la URL (convFicha.aspx?c=0&i=...)
    - title    -> título del cargo (texto principal del aviso)
    - link     -> link absoluto a "Ver Bases"
    - summary  -> bloque completo de texto del aviso (institución, descripción, plazos)
    - published -> None (por ahora)
    """
    entries = []
    seen_ids = set()

    for base_url in FEED_URLS_REGIONES:
        resp = requests.get(base_url, timeout=20)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Cada convocatoria tiene un link "Ver Bases"
        for a in soup.find_all("a", string=lambda s: s and "Ver Bases" in s):
            href = a.get("href")
            if not href:
                continue

            # Link absoluto
            full_link = urljoin(base_url, href)

            # Intentar sacar el id desde el parámetro ?i=...
            parsed = urlparse(full_link)
            qs = parse_qs(parsed.query)
            job_id = qs.get("i", [full_link])[0]

            # Evitar duplicados por id entre regiones
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            # -------- TÍTULO --------
            title_text = None
            for prev in a.find_all_previous(string=True, limit=15):
                txt = (prev or "").strip()
                if not txt:
                    continue

                lower = txt.lower()
                # Saltar textos que claramente no son título
                if "plazos de postulación" in lower or "plazos de postulacion" in lower:
                    continue
                if "ver bases" in lower or "postula en línea" in lower or "postula en linea" in lower:
                    continue

                title_text = txt
                break

            if not title_text:
                title_text = a.get_text(strip=True) or f"Convocatoria {job_id}"

            # -------- SUMMARY: bloque completo --------
            container = a.parent
            for _ in range(4):
                if container is None:
                    break
                text_len = len(container.get_text(strip=True))
                if text_len < len(title_text) + 40:
                    container = container.parent
                else:
                    break

            if container:
                summary = container.get_text(" ", strip=True)
            else:
                summary = title_text

            entry = Entry(
                id=job_id,
                title=title_text,
                link=full_link,
                summary=summary,
                published=None,
            )
            entries.append(entry)

    return entries
