import re
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup


def _extraer_texto_siguiente(soup: BeautifulSoup, encabezado: str) -> Optional[str]:
    """
    Busca un <h3> cuyo texto contenga `encabezado` y devuelve el texto
    del primer hermano siguiente (normalmente un <p>).
    """
    h3 = soup.find("h3", string=lambda t: t and encabezado.lower() in t.lower())
    if not h3:
        return None

    sib = h3.find_next_sibling()
    if not sib:
        return None

    texto = sib.get_text(strip=True)
    return texto or None


def _extraer_fecha_cierre(soup: BeautifulSoup) -> Optional[datetime]:
    """
    Busca la sección 'Calendarización del Proceso' y dentro de ella la fila
    'Difusión y Plazo de Postulación', luego toma la fecha final del rango.

    Ejemplo de texto esperado: '05/02/2025-11/02/2025' -> usamos 11/02/2025.
    """
    # 1) Buscar el título de calendarización
    h3 = soup.find("h3", string=lambda t: t and "Calendarización del Proceso" in t)
    if not h3:
        # fallback: buscar cualquier texto similar
        h3 = soup.find(string=lambda t: t and "Calendarización del Proceso" in t)
        if not h3:
            return None
        h3 = h3.parent

    # 2) Buscar la tabla que viene después
    tabla = h3.find_next("table")
    if not tabla:
        return None

    # 3) Buscar una fila que mencione "Difusión y Plazo de Postulación"
    for tr in tabla.find_all("tr"):
        texto_fila = tr.get_text(" ", strip=True)
        if "Difusión y Plazo de Postulación" in texto_fila:
            # Buscamos algo tipo 05/02/2025-11/02/2025
            match = re.search(r"(\d{{2}}/\d{{2}}/\d{{4}})\s*-\s*(\d{{2}}/\d{{2}}/\d{{4}})", texto_fila)
            if match:
                fecha_final_str = match.group(2)
                try:
                    return datetime.strptime(fecha_final_str, "%d/%m/%Y")
                except ValueError:
                    return None
            # Si no encontramos rango, probamos al menos una fecha suelta dd/mm/yyyy
            match2 = re.search(r"(\d{{2}}/\d{{2}}/\d{{4}})", texto_fila)
            if match2:
                try:
                    return datetime.strptime(match2.group(1), "%d/%m/%Y")
                except ValueError:
                    return None

    return None


def parsear_detalle_concurso(url: str) -> dict:
    """
    Descarga la página de un concurso en empleospublicos.cl y extrae:
    - ministerio
    - comuna (usamos el campo 'Ciudad')
    - fecha_cierre (desde Calendarización del Proceso)

    Devuelve un dict con esas claves, pudiendo contener valores None.
    """
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    ministerio = _extraer_texto_siguiente(soup, "Ministerio")
    ciudad = _extraer_texto_siguiente(soup, "Ciudad")
    fecha_cierre = _extraer_fecha_cierre(soup)

    return {
        "ministerio": ministerio,
        "comuna": ciudad,      # por ahora usamos 'Ciudad' como comuna
        "fecha_cierre": fecha_cierre,
    }
