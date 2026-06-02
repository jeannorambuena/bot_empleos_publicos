# Catastro acotado de fuentes candidatas

Fecha de revisión inicial: `2026-06-02`.

Este catastro prepara futuras integraciones para Radar Laboral Público Chile sin
implementar scrapers nuevos. El archivo versionado `data/source_candidates.json`
registra URLs oficiales, alcance territorial, dificultad estimada y prioridad.

## Alcance territorial

La revisión está limitada a:

- Región Metropolitana y Santiago.
- Región de O'Higgins.
- Región del Maule.

También se incluyen portales nacionales cuando permiten investigar o filtrar
oportunidades para esas tres regiones. No se incorporaron fuentes regionales del
resto del país porque ampliar el territorio antes de probar adaptadores locales
haría más difícil auditar duplicados, vigencia y calidad.

## Fuentes prometedoras

### Maule

- [Municipalidad de Curicó - Concursos](https://www.curico.cl/home/category/concursos/):
  sección oficial con publicaciones y bases descargables. Es la primera fuente
  municipal recomendada.
- [Municipalidad de Molina - Concursos Públicos](https://web.molina.cl/?page_id=71592):
  página oficial con listados y fechas. Es una segunda candidata municipal clara.
- [Gobierno Regional del Maule - Concursos Públicos](https://www.goremaule.cl/goremauleVII/concursos-publicos/):
  sección oficial estructurada; debe revisarse contra Empleos Públicos para evitar
  duplicados.
- [SLEP Los Cerezos](https://sleploscerezos.gob.cl/): prioridad educativa por su
  cobertura de Curicó, Molina, Rauco, Romeral y Teno, entre otras comunas.
- [SLEP Maule Costa](https://slepmc.cl/): prioridad educativa complementaria.

También quedan catastradas las municipalidades de Rauco, Romeral, Teno y Talca, y la
Universidad de Talca. Requieren revisión manual adicional para identificar páginas
estables de concursos y distinguir convocatorias laborales de noticias u ofertas
OMIL.

### O'Higgins

- [SLEP Colchagua](https://www.slepcolchagua.gob.cl/): el sitio oficial incluye un
  acceso `Trabaja con Nosotros`; debe comprobarse si complementa o duplica Empleos
  Públicos.
- [Municipalidad de Rancagua - Ofertas Laborales](https://munirancagua.gob.cl/ofertas-laborales):
  página oficial con buscador, filtros, conteo y RSS. Antes de integrar se debe
  separar empleo municipal propio de intermediación OMIL.
- [Municipalidad de San Fernando](https://municipalidadsanfernando.cl/): el sitio
  oficial enlaza `Trabaja con Nosotros` y publica fichas de cargos.

También quedan registrados el Gobierno Regional de O'Higgins, el Servicio de Salud
O'Higgins y la Universidad de O'Higgins. Son candidatos de revisión manual, no
integraciones aprobadas.

### Región Metropolitana

- [SLEP Santiago Centro](https://www.slepsantiagocentro.gob.cl/): candidato educativo
  de Santiago para revisar convocatorias institucionales.
- [Municipalidad de Santiago](https://www.municipalidaddesantiago.cl/): el sitio
  oficial enlaza `Concursos Públicos`.

También quedan registrados el Gobierno Regional Metropolitano y la Universidad de
Chile. Sus estructuras requieren revisión manual antes de diseñar un adaptador.

## Portales nacionales filtrables

- [Empleos Públicos](https://www.empleospublicos.cl/): fuente real activa. Las
  integraciones futuras deben medir duplicados contra este portal.
- [Alta Dirección Pública](https://adp.serviciocivil.cl/): portal del Servicio Civil
  con búsqueda por cargo, comuna o institución. Puede contener publicaciones
  relacionadas con SLEP y otros organismos.
- [Poder Judicial - Trabaje con nosotros](https://www.pjud.cl/transparencia/trabaje-con-nosotros):
  portal propio de concursos y postulaciones. Requiere validar filtros territoriales.
- [Dirección de Educación Pública - directorio SLEP](https://educacionpublica.gob.cl/servicios-locales-de-educacion-publica/):
  directorio institucional útil para investigación, no feed laboral.
- [Portal de Transparencia - organismos regulados](https://www.consejotransparencia.cl/transparencia_activa/paginacontingenciaportal/listaorganismos.html):
  directorio para descubrir organismos y revisar transparencia activa. No debe
  tratarse como feed laboral automático.

## Línea comercial Nexus

[Mercado Público y Compra Ágil](https://www.mercadopublico.cl/Portal/Modules/Menu/CompraAgil)
publica oportunidades de negocio y permite explorar regiones, incluidos RM,
O'Higgins y Maule. Esta fuente es prioritaria para un radar comercial Nexus separado.
No debe mezclarse con recomendaciones laborales personales.

## Posibles duplicados de Empleos Públicos

Los candidatos institucionales pueden republicar concursos visibles en Empleos
Públicos. El riesgo es especialmente relevante para gobiernos regionales, SLEP y
Alta Dirección Pública. Antes de publicar una fuente nueva se debe comparar:

- identificador oficial;
- institución;
- título normalizado;
- fecha de cierre;
- URL directa;
- coincidencias ya visibles en Empleos Públicos.

## Fuentes que requieren revisión manual

Una URL oficial no implica que exista un feed estable. Deben revisarse manualmente:

- sitios con noticias mezcladas con concursos;
- páginas que publican PDFs sin estado explícito;
- portales con postulaciones externas;
- transparencia activa;
- ofertas OMIL que pueden incluir empleo privado;
- páginas institucionales sin archivo o paginación verificable.

## Incorporar una fuente real después

1. Elegir una única fuente priorizada.
2. Verificar manualmente una muestra vigente.
3. Documentar mapeo al contrato de `docs/source-contract.md`.
4. Implementar un adaptador aislado.
5. Validar URLs oficiales, vigencia y duplicados con Empleos Públicos.
6. Abrir un PR exclusivo para esa fuente.
7. Comparar salida normalizada contra la muestra original antes de publicar.

Este lote no implementa scraping real de SLEP, municipalidades, gobiernos
regionales, universidades, Poder Judicial, ADP, Transparencia ni Mercado Público.
