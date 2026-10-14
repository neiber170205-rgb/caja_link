# ADR 004: Cruce por lote en segundo plano, en memoria y con tope de consultas

- Estado: aceptada
- Fecha: 2026-10-13

## Contexto

Además de la consulta en línea, una caja debe poder cruzar un archivo completo para detectar dobles afiliaciones. El contrato pide recibir un CSV con la columna `document`, responder de inmediato `202` con un `jobId`, permitir consultar el estado (`PENDING`, `RUNNING`, `DONE`) y devolver el mismo `jobId` si se repite la `Idempotency-Key`. Un lote de 10.000 documentos debe terminar en 5 minutos o menos. Los documentos del archivo vienen sucios (con puntos y espacios) y cada uno debe cumplir las mismas reglas que la consulta en línea, incluida la de no dar un falso `NO_AFILIADO`.

## Decisión

- El lote corre como una **tarea en segundo plano dentro del mismo servicio** y usa el mismo servicio de consulta que la ruta en línea, así que las reglas son idénticas.
- Se permiten **24 consultas simultáneas a las cajas**, repartidas entre las cajas en línea: 24 documentos a la vez si se consulta una caja en línea, 12 si son dos. Caja Centro responde desde memoria y no cuenta.
- Los documentos que quedan `INDETERMINADO` tienen una **ronda de repaso**, 3 segundos después y más despacio (8 consultas a la vez), mientras no se pasen 240 segundos.
- La idempotencia se guarda por caja y llave: la misma caja con la misma `Idempotency-Key` recibe el mismo `jobId`.
- Solo la caja que envió el lote puede consultarlo; para las demás no existe (404).
- Los resultados salen en el orden del archivo, con el documento normalizado en `document` y el original en `documentInput`. Cada documento queda en la auditoría.
- Los lotes viven en memoria; se conservan los últimos 20 terminados.

## Alternativas

- **Procesar todo dentro de la petición POST:** es lo más simple, pero incumple el contrato (`202` y consulta de estado), y con 10.000 documentos la conexión se cortaría por tiempo.
- **Una cola externa con un worker (por ejemplo Redis con Celery o RQ):** sobreviviría a reinicios y escalaría a varios procesos, pero agrega dos servicios al Compose, más riesgo de que el entorno no levante desde cero, y es más de lo que necesitan 10.000 documentos.
- **Consultar muchos documentos a la vez (probamos 50):** parecía lo más rápido, pero al medir el lote tardó 46 segundos frente a 19 con el tope actual. El cuello de botella es el propio servicio: con demasiadas consultas simultáneas se satura y va más lento.
- **Guardar los lotes en una base de datos propia del hub (por ejemplo SQLite):** sobrevivirían a un reinicio, pero quedaría en disco una copia de miles de documentos con su resultado, más de lo que justifica el principio de dato mínimo, y costaba varias horas más. No va contra el reto, que lo que pide evitar es que las cajas compartan una base de datos; simplemente no lo necesitamos para cumplir el contrato.

## Consecuencias

- **Se gana:** 10.000 documentos en 19 segundos con una caja en línea y en 38 con dos, sin errores (ver `docs/load-test.md`). Comparamos los 30.000 resultados de tres corridas contra los datos de las cajas y no hubo diferencias.
- **Se gana:** con Caja Norte caída durante todo el lote, terminó en 241 segundos, dentro del límite, sin ningún falso `NO_AFILIADO`.
- **Se acepta:** si el servicio se reinicia, se pierden los lotes y la auditoría en curso.
- **Se acepta:** el servicio debe correr como un solo proceso, porque el estado está en memoria (ver ADR 001).
- **Pendiente:** si una caja está lenta (no caída) durante todo el lote, cada documento espera 2,5 segundos y el lote pasaría de los 5 minutos. La mejora prevista es dejar de consultar en esa ronda a una caja que acumule varias fallas seguidas.
