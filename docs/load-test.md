# Prueba de carga del lote

herramienta: script en Python (scripts/prueba_carga.py)
documentos: 10000
duracion_segundos: 38
errores: 0

## Cómo se midió

- Comando: `python3 scripts/prueba_carga.py [CAJA]`, con el entorno levantado con `docker compose up -d --build`.
- El script envía `data/lote_10000.csv`, pregunta el estado cada segundo hasta que el lote queda en DONE y cuenta los resultados.
- Máquina: Linux (CachyOS), 16 núcleos y 23 GB de RAM. Fecha: 13 de octubre de 2026.

## Resultados

| Caja que consulta | Cajas en línea consultadas | Corridas | Duración | Errores | AFILIADO_OTRA_CAJA | NO_AFILIADO |
|---|---|---|---|---|---|---|
| NORTE | Oriente | 3 | 19 s | 0 | 3559 | 6441 |
| CENTRO | Norte y Oriente | 3 | 38 s | 0 | 3959 | 6041 |

`duracion_segundos` reporta el caso más lento: 38 segundos, el 13 % del límite de 300.
