# Arquitectura del radar

Radar Laboral Público Chile evoluciona en componentes pequeños para que pueda ser
reutilizado y auditado por la comunidad. El dashboard puede publicarse con datos
reales normalizados desde Empleos Públicos. Las nuevas fuentes deben incorporarse de
forma gradual sin acoplarse al scraper histórico ni romper el conector estable.

## Flujo general

```text
fuentes -> adaptadores -> normalización -> scoring -> almacenamiento
        -> JSON público -> dashboard
        -> alertas por correo
        -> recordatorios .ics
```

## Scraper y fuentes

Cada fuente debe contar con un adaptador responsable de obtener convocatorias desde
una URL base institucional. Las primeras categorías previstas son Empleos Públicos,
SLEP, ministerios, municipalidades y otras páginas institucionales.

Los adaptadores no deben inventar URLs de convocatorias ni publicar información que
no haya sido obtenida desde una fuente verificable.

Empleos Públicos es la única fuente real activa. Una fuente futura se agrega mediante
un PR propio: primero contrato y evidencia manual, después adaptador y validaciones,
y finalmente publicación controlada. No se deben mezclar varios portales reales en
un mismo PR porque dificulta rastrear duplicados, errores de parser y regresiones.

## Normalización

Los resultados de distintas fuentes deben transformarse al contrato común descrito
en `docs/source-contract.md` antes de entrar al scoring. La normalización permite
comparar, deduplicar y publicar convocatorias aunque sus sitios de origen tengan
estructuras diferentes. La salida pública final sigue el contrato de
`docs/data-contract.md`.

## Scoring y coincidencia

El motor de scoring comparará cada oportunidad con el perfil configurable:

- Regiones, comunas o zonas priorizadas.
- Áreas laborales.
- Palabras clave positivas y negativas.
- Cercanía de la fecha de cierre.
- Fuentes priorizadas.

El resultado será un puntaje entre 0 y 100 y un nivel: `Alta`, `Media`, `Baja` o
`Descartada`.

## Almacenamiento

El almacenamiento local conservará convocatorias normalizadas, historial de cambios
y marcas de alerta emitida. Antes de publicar una base real se deberán definir
retención, respaldo y tratamiento de datos sensibles.

## Generación JSON

El generador real exporta archivos públicos sin secretos:

- `public/data/opportunities.json`
- `public/data/summary.json`
- `public/data/last_run.json`
- `public/data/history.json`

Estos archivos serán la interfaz entre el proceso de actualización y el dashboard.

## Dashboard público

`public/` contiene una página estática compatible con GitHub Pages. Carga JSON mediante
JavaScript, muestra métricas, filtros y tarjetas, y diferencia explícitamente los
datos demo de futuras convocatorias reales.

## Alertas por correo

Las alertas futuras podrán activarse por nueva oportunidad, alta coincidencia,
actualización y proximidad de cierre. Las credenciales SMTP vivirán solo en variables
locales o GitHub Secrets.

## Calendario

Una fase posterior generará archivos `.ics` con recordatorios de cierre. El calendario
será un artefacto derivado; no deberá contener más información de la necesaria.

## GitHub Pages

GitHub Pages podrá servir exclusivamente el contenido estático de `public/`. La
publicación debe ocurrir solo cuando los JSON estén revisados y no contengan datos
sensibles.

## GitHub Actions

La automatización futura podrá ejecutar validaciones, actualizar JSON públicos y
publicar el sitio. Las credenciales deberán configurarse mediante GitHub Secrets y
los workflows tendrán permisos mínimos.
