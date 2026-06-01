# Calendario en modo preview

El modo preview de calendario genera recordatorios locales en formato `.ics`. No
conecta Google Calendar, Outlook ni ningún servicio externo.

## Generar calendario

Desde la raíz del repositorio:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\venv\Scripts\python.exe scripts\build_calendar_preview.py
```

El script lee `public/data/opportunities.json` y genera:

- `output/calendar/radar-laboral-reminders.ics`
- `output/calendar/calendar-summary.json`

`output/` está ignorado por Git porque puede contener información de operación local.

## Oportunidades seleccionadas

El preview considera oportunidades vigentes que:

- Tienen nivel de coincidencia `Alta`.
- O tienen cierre próximo dentro de 7 días.

Las oportunidades descartadas no generan recordatorios.

## Eventos creados

Para cada oportunidad seleccionada con fecha de cierre:

- `Decidir postulación`: recordatorio previo para revisar antecedentes y decidir.
- `Cierre de convocatoria`: evento en la fecha límite.

Los eventos incluyen cargo, institución, fuente, región, comuna, puntaje y motivos de
alerta. Solo incluyen una URL cuando existe una fuente real y el registro no es demo.

## Importación manual

Antes de importar, abre el archivo `.ics` y revisa su contenido.

En Google Calendar:

1. Abre Configuración.
2. Ve a Importar y exportar.
3. Selecciona `radar-laboral-reminders.ics`.
4. Elige un calendario de destino y confirma la importación.

En Outlook:

1. Abre el calendario.
2. Usa la opción para importar o abrir un archivo `.ics`.
3. Revisa los eventos antes de guardarlos.

## Por qué no hay conexión real todavía

Esta fase busca validar contenido, fechas y recordatorios sin credenciales ni efectos
externos. Una integración futura requerirá revisión adicional de permisos, privacidad
y manejo seguro de secretos.

## Privacidad

Los calendarios pueden compartirse accidentalmente. Revisa los datos antes de
importar o compartir archivos `.ics`, especialmente cuando el proyecto comience a
usar oportunidades reales.
