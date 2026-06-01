# Roadmap de fuentes

## Estado actual

Empleos Públicos es la única fuente con captura activa. Las demás fuentes quedan
declaradas en `config/sources.example.json` para revisión e implementación gradual:
SLEP Los Cerezos, SLEP Colchagua y municipalidades de Romeral, Curicó y Rauco.

## Prioridad recomendada

1. Empleos Públicos.
2. SLEP Los Cerezos.
3. SLEP Colchagua.
4. Municipalidades cercanas.

## Criterios para agregar una fuente

Antes de crear un parser se debe confirmar que la página sea institucional,
pública, estable y útil para el perfil comunitario. También conviene revisar
frecuencia de cambios, paginación, fechas de cierre y condiciones de acceso.

Cada sitio puede necesitar un parser propio. Cambios de HTML, medidas anti-bot o
publicaciones no estructuradas pueden romper una captura automática. Por eso las
fuentes nuevas comienzan como `planned` o `manual_review`; este lote no implementa
scrapers frágiles adicionales.
