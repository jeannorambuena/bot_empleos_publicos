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

- Cada palabra clave positiva encontrada: 12 puntos.
- Región priorizada: 18 puntos.
- Área incluida en el perfil: 14 puntos.
- Comuna o zona de interés: 8 puntos.
- Fuente informada: 4 puntos.

El resultado final se limita a un máximo de 100 puntos. Además del puntaje, el motor
devuelve palabras clave encontradas y motivos legibles para futuras alertas.

## Qué descarta

Si aparece cualquier palabra clave negativa configurada, la oportunidad se descarta
de inmediato con puntaje `0`. El resultado incluye las palabras que causaron el
descarte para facilitar la revisión.

## Rangos

- `Alta`: 85 a 100.
- `Media`: 70 a 84.
- `Baja`: 50 a 69.
- `Descartada`: menos de 50.

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
