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

El catastro territorial detallado está en `docs/source-discovery.md` y
`data/source_candidates.json`.

La Región Metropolitana ya no se interpreta solo como comuna de Santiago o SLEP
Santiago Centro. El catastro incorpora una selección metropolitana de SLEP,
municipios, servicios regionales y universidades estatales, siempre como candidatas
documentales sin scraper implementado.

## Hipótesis de integración

- **H1:** Municipalidad de Curicó. Su sección oficial de concursos tiene
  publicaciones y bases descargables; permite probar un adaptador municipal acotado.
- **H2:** SLEP Los Cerezos. Tiene alta utilidad territorial para Curicó, Molina,
  Rauco, Romeral y Teno, pero primero debe identificarse una sección estable de
  convocatorias y medirse duplicación con Empleos Públicos.
- **H3:** Mercado Público y Compra Ágil como radar comercial Nexus separado. No debe
  mezclarse con recomendaciones laborales personales.
- **H4:** ampliar a otras regiones únicamente después de validar H1 y H2, y solo con
  aprobación explícita del usuario.

La ampliación RM no altera H1 ni H2: siguen siendo pruebas acotadas antes de abrir
nuevas integraciones reales.

## Criterios para agregar una fuente

Antes de crear un parser se debe confirmar que la página sea institucional,
pública, estable y útil para el perfil comunitario. También conviene revisar
frecuencia de cambios, paginación, fechas de cierre y condiciones de acceso.

Cada sitio puede necesitar un parser propio. Cambios de HTML, medidas anti-bot o
publicaciones no estructuradas pueden romper una captura automática. Por eso las
fuentes nuevas comienzan como `planned` o `manual_review`; este lote no implementa
scrapers frágiles adicionales.

## Incorporación gradual

Cada fuente real futura debe entrar por separado:

1. Revisar manualmente el sitio institucional, sus URLs y condiciones de acceso.
2. Documentar el mapeo al contrato de `docs/source-contract.md`.
3. Crear un adaptador aislado que produzca oportunidades normalizadas.
4. Validar vigencia, fechas, URLs oficiales y duplicados.
5. Comparar una muestra contra la fuente original.
6. Abrir un PR exclusivo para esa fuente.
7. Publicar solo después de revisión humana.

No se deben mezclar SLEP, municipalidades o portales adicionales en un único PR. Un
cambio por fuente facilita detectar fallas, revertir una integración específica y
auditar qué portal originó cada oportunidad.

## Reglas de trazabilidad

- Conservar un `id` estable prefijado por fuente.
- Mantener `source`, `source_id`, `source_url` y `listing_url`.
- Publicar únicamente URLs oficiales verificables.
- Evitar duplicados dentro de una fuente y revisar coincidencias entre fuentes.
- Verificar vigencia usando estado, fecha de cierre y capturas sucesivas.
- Mantener datos crudos y normalizados locales fuera de `public/`.

Este macro-lote solo prepara arquitectura y documentación. No agrega scrapers reales
de SLEP, municipalidades ni ChileCompra.

El catastro inicial se limita a Región Metropolitana, O'Higgins y Maule. Los portales
nacionales solo se incluyen cuando son filtrables o útiles para investigar estas
tres regiones.
