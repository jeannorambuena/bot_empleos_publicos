# Resumen ejecutivo

Radar Laboral Publico Chile es un MVP funcional validado localmente que ayuda a
monitorear oportunidades laborales publicas en Chile.

## Que hace el sistema

El sistema revisa fuentes publicas, normaliza oportunidades laborales, las ordena
por relevancia y las muestra en un dashboard estatico. Tambien mantiene historial,
filtros, etiquetas de prioridad, revision humana y previews de alertas.

## Que problema reduce

Reduce el tiempo de revisar manualmente portales y sitios institucionales donde se
publican convocatorias laborales. En vez de buscar en multiples paginas, el usuario
puede consultar una vista ordenada y priorizada.

## Que valor entrega

- Ahorra tiempo de monitoreo.
- Ordena oportunidades por coincidencia con un perfil.
- Mantiene trazabilidad hacia la fuente oficial.
- Ayuda a detectar cierres proximos.
- Separa oportunidades publicables de fuentes que requieren revision.
- Incluye controles de privacidad antes de publicar datos.

## Estado actual

El proyecto esta en estado MVP funcional validado, no como plataforma comercial
completa.

Estado validado:

- 101 oportunidades publicas disponibles en el dashboard.
- Fuente principal activa: Empleos Publicos.
- Fuentes candidatas y locales documentadas.
- Telegram en modo preview/controlado, sin envio automatico por defecto.
- QA integral disponible con `python scripts/check_all.py`.

## Advertencia importante

Toda convocatoria debe verificarse en la fuente oficial antes de postular o tomar
una decision. El radar ayuda a detectar y priorizar oportunidades, pero no reemplaza
la lectura de bases, requisitos, fechas ni instrucciones institucionales.

El sistema no automatiza postulaciones, no accede a portales privados y no usa
credenciales personales para capturar oportunidades.
