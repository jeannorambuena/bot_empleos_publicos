# Reporte semanal local

El reporte semanal resume el estado operativo del radar sin activar automatizaciones
ni publicar archivos adicionales. Se construye desde los JSON públicos ya validados y
se guarda únicamente como artefacto local ignorado por Git.

## Generar el reporte

Desde la raíz del repositorio:

```powershell
python scripts/build_weekly_report.py
```

El resultado queda en:

```text
output/reports/weekly-report.md
```

## Contenido

El reporte incluye fecha del corte, total capturado, oportunidades nuevas relevantes,
niveles `Alta`, cierres próximos relevantes, recomendaciones principales, pendientes
de revisión humana y falsos positivos evitados por feedback humano.

El comentario operativo se calcula con reglas simples: prioriza nuevas relevantes,
después cierres próximos y finalmente revisiones humanas pendientes. No utiliza IA ni
modifica scoring, feedback aplicado o datos públicos.

El reporte puede revisarse y compartirse manualmente después de verificar su
contenido. Este lote no activa envío semanal automático: esa decisión requiere una
política separada de destinatarios, frecuencia y rollback.

## Seguridad

`output/` está ignorado por Git porque los reportes son artefactos locales de
operación. Antes de compartir un reporte, revisa que no contenga información que no
deba circular fuera del equipo.
