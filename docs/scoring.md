# Scoring y coincidencia

El motor inicial de scoring compara cada oportunidad con
`config/profile.example.json`. Su objetivo es entregar una primera señal explicable
para ordenar oportunidades. Todavía no está conectado al scraper histórico ni al
dashboard público.

## Normalización

Antes de comparar textos, el motor:

- Convierte el contenido a minúsculas.
- Quita tildes y otras marcas diacríticas.
- Limpia espacios repetidos.

Esto permite encontrar, por ejemplo, `informática` e `informatica` como el mismo
concepto.

## Qué suma puntos

- Cada palabra clave positiva encontrada en el título: 22 puntos.
- Cada palabra clave adicional encontrada en descripción o tags: 6 puntos.
- Presencia de una palabra fuerte en el título: 30 puntos.
- Región priorizada: 8 puntos.
- Área incluida en el perfil: 10 puntos.
- Comuna o zona de interés: 4 puntos.
- Fuente informada: 3 puntos.

Los términos ambiguos `sistemas`, `plataforma` y `abastecimiento` suman menos por
sí solos. Solo recuperan peso parcial cuando aparecen con contexto tecnológico o
de compras públicas según corresponda.

El resultado final se limita a un máximo de 100 puntos. Además del puntaje, el motor
devuelve palabras clave encontradas y motivos legibles para futuras alertas.

## Viabilidad economica Santiago/RM

Despues del scoring profesional se aplica una regla economica solo para oportunidades
ubicadas en Santiago o Region Metropolitana. La deteccion usa `region`, `commune`,
`title`, `listing_url` y `source_url`, normalizados sin tildes, buscando senales como
`Metropolitana` o `Santiago`.

La renta se lee desde campos estructurados si existen (`salary`, `renta`,
`renta_bruta`, `renta_liquida`, `sueldo`, etc.) y, como respaldo, desde montos en
texto libre con signo `$`. Los montos menores a `$500.000` se ignoran para evitar
confundir valores por hora o viaticos con renta mensual. Si el texto indica renta
liquida se compara contra pisos liquidos; si indica bruta o no lo aclara se compara
contra equivalencias brutas configurables en `santiago_economic_viability`:

- `cumple_bueno`: desde `$2.500.000` bruto o `$2.000.000` liquido.
- `cumple_recomendable`: desde `$2.250.000` bruto o `$1.800.000` liquido.
- `viable_justo`: desde `$2.000.000` bruto o `$1.600.000` liquido.
- `bajo_piso`: bajo esos montos; baja prioridad.
- `renta_no_informada`: queda visible y marcada para revisar renta antes de postular.

Esta regla no se aplica a Maule, O'Higgins ni oportunidades cercanas al domicilio.

## Qué descarta

Si aparece una palabra negativa general configurada, la oportunidad se descarta con
puntaje `0`. Los cargos clínicos evidentes también se descartan cuando no existe una
señal tecnológica fuerte en el título. Una institución de salud no provoca descarte
por sí sola: infraestructura, redes, soporte o CCTV pueden seguir siendo relevantes.

## Rangos

- `Alta`: 80 a 100.
- `Media`: 60 a 79.
- `Baja`: 35 a 59.
- `Descartada`: 0 a 34 o descarte fuerte.

Una oportunidad también puede marcarse como descartada directamente por una palabra
negativa.

## Validación local

Desde la raíz del repositorio:

```powershell
.\venv\Scripts\python.exe scripts\check_scoring.py
```

El script usa seis oportunidades de ejemplo, imprime una tabla simple y falla si la
configuración mínima es inválida o si un puntaje no respeta los rangos acordados.

## Calibración futura

Esta es una primera versión. Los pesos y reglas deberán calibrarse con convocatorias
reales revisadas por la comunidad antes de usarse para priorización operativa.
