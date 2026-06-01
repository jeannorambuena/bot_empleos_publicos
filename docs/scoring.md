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

El resultado final se limita a un máximo de 100 puntos. Además del puntaje, el motor
devuelve palabras clave encontradas y motivos legibles para futuras alertas.

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
