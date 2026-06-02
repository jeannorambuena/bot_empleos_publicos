# Dry-run Municipalidad de Molina

Municipalidad de Molina es la segunda fuente municipal evaluada mediante un
adaptador aislado. Este lote no publica resultados ni conecta Molina al dashboard.

## URL usada

El script lee la ficha `municipalidad-molina` desde
`data/source_candidates.json` y consulta exclusivamente la URL configurada:

```text
https://web.molina.cl/?page_id=71592
```

No sigue enlaces ni descarga documentos. Los enlaces oficiales se conservan como
trazabilidad local.

## Qué extrae

La página oficial contiene un bloque de concursos públicos con entradas fechadas.
Algunas enlazan bases en PDF o DOCX bajo el dominio municipal; una enlaza una ficha
oficial de Empleos Públicos y otra publicación cerrada no contiene URL directa.
No se observaron noticias mezcladas dentro del bloque, pero sí documentos y una
publicación marcada explícitamente como cerrada.

El adaptador registra:

- título visible y URL oficial disponible;
- `listing_url` configurada;
- fecha visible inicial como `published_date`;
- documentos oficiales enlazados sin descargarlos;
- región Maule y comuna Molina;
- estado conservador con motivo, confianza y evidencia.

## Reglas de vigencia

- `open_confirmed`: solo si el HTML publica una fecha de cierre explícita y vigente.
- `closed`: si el HTML muestra cierre pasado o evidencia textual inequívoca de
  cierre o resultado.
- `manual_review`: si falta fecha de cierre o la vigencia no es inequívoca.

Las fechas iniciales entre paréntesis se registran como publicación visible. No se
interpretan como fecha de cierre.

## Campos confiables

- `source`, `institution`, `region` y `commune`;
- `listing_url` oficial configurada;
- `source_url` oficial directa cuando existe, o la página oficial del listado
  cuando una entrada no enlaza detalle;
- `published_date` visible al inicio de cada entrada;
- `document_urls` municipales detectadas sin descarga;
- `detected_at`, `status_reason`, `confidence` y `evidence`.

## Campos sujetos a revisión manual

- `closing_date`: permanece `null` si el HTML no publica cierre explícito;
- `status`: permanece `manual_review` sin evidencia inequívoca de vigencia;
- clasificación laboral final: la página reúne perfiles municipales diversos.

## Resultado observado

En la revisión del `2026-06-02`, el adaptador detectó 8 publicaciones:

- 6 documentos municipales oficiales sin descarga;
- 1 enlace oficial externo a Empleos Públicos;
- 0 publicaciones `open_confirmed`;
- 1 publicación `closed` por texto explícito;
- 7 publicaciones `manual_review`.

No se detectaron fechas de cierre confiables en HTML.

## Ejecutar

```powershell
python scripts/fetch_molina.py
python scripts/check_molina_source.py
```

Archivos locales generados:

```text
output/sources/molina/opportunities.json
output/sources/molina/diagnostics.json
output/sources/molina/report.md
```

`output/` está ignorado por Git. El adaptador no modifica `public/data/`, scoring,
feedback, workflows ni Telegram. Molina todavía no se publica porque sus vigencias
requieren revisión humana y este lote valida la fuente de forma aislada.
