from datetime import datetime

from dotenv import load_dotenv

from db_utils import get_concursos_sin_detalle, actualizar_detalle_concurso
from scraping import parsear_detalle_concurso


def main():
    load_dotenv()

    pendientes = get_concursos_sin_detalle(limit=5)
    if not pendientes:
        print("No hay concursos pendientes de detalle.")
        return

    print(f"Encontrados {len(pendientes)} concursos sin detalle. Procesando...")

    for c in pendientes:
        cid = c["id"]
        titulo = c["titulo"]
        link = c["link"]

        print(f"\n[ID {cid}] {titulo}")
        print(f"URL: {link}")

        try:
            detalle = parsear_detalle_concurso(link)
        except Exception as e:
            print("  Error al obtener detalle:", e)
            continue

        ministerio = detalle["ministerio"]
        comuna = detalle["comuna"]
        fecha_cierre = detalle["fecha_cierre"]

        print(f"  Ministerio: {ministerio}")
        print(f"  Comuna/Ciudad: {comuna}")
        print(f"  Fecha cierre: {fecha_cierre}")

        actualizar_detalle_concurso(cid, ministerio, comuna, fecha_cierre)
        print("  >> Detalle actualizado en la BD.")

    print("\nProceso completado.")


if __name__ == "__main__":
    main()
