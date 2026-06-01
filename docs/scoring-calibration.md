# Calibración inicial del scoring real

La primera captura local desde Empleos Públicos mostró que el scoring demo era
demasiado estricto: las 110 oportunidades quedaban como `Descartada`, incluso cuando
el título incluía señales claras como redes, desarrollo, plataformas digitales,
CCTV o compras públicas.

## Criterios aplicados

- Las coincidencias del título pesan más que las de la descripción.
- Los términos fuertes del título reciben una bonificación adicional.
- Región, comuna, área y fuente siguen aportando contexto, pero no dominan el score.
- Hospitales y servicios de salud no se descartan automáticamente.
- Los cargos clínicos evidentes se descartan si no contienen una señal tecnológica
  fuerte en el título.
- Las palabras negativas generales, como práctica profesional o voluntariado,
  mantienen descarte directo.

## Rangos

- `Alta`: 80 a 100.
- `Media`: 60 a 79.
- `Baja`: 35 a 59.
- `Descartada`: 0 a 34 o descarte fuerte.

## Analizar una captura

Después de regenerar el dashboard con datos reales:

```powershell
.\venv\Scripts\python.exe scripts\build_public_data_from_real.py
.\venv\Scripts\python.exe scripts\analyze_real_scoring.py
```

El analizador muestra distribución, mejores puntajes, descartadas con coincidencias
positivas, términos relevantes pendientes de revisión y frecuencia de keywords.

## Pendientes

Esta calibración sigue siendo inicial. Hará falta revisar capturas sucesivas, añadir
casos de prueba guardados y ajustar sinónimos para evitar falsos positivos en cargos
administrativos o clínicos.
