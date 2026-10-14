# ADR 003: Ante una caja que no responde, INDETERMINADO y nunca NO_AFILIADO

- Estado: aceptada
- Fecha: 2026-10-13

## Contexto

Las cajas fallan: Caja Norte es lenta a ratos y a veces no responde, y el validador provoca caídas y lentitud a propósito con `/__chaos` (en modo lento la caja tarda 8 segundos). El contrato exige responder en menos de 5 segundos aunque una caja esté lenta, y prohíbe responder «no afiliado» si alguna caja no contestó. Un falso `NO_AFILIADO` es el peor error posible: llevaría a otorgar un subsidio a alguien que ya está afiliado en otra caja. La Ley 1581 también lo pide: no se informa algo que no se pudo verificar.

## Decisión

- Las cajas se consultan **en paralelo**: el tiempo total es el de la caja más lenta, no la suma.
- Cada intento espera como máximo **2,5 segundos**. Si la caja falla rápido (un error del servidor, como el HTTP 503, o la conexión rechazada) se reintenta hasta **2 veces** con pausas cortas; si no responde a tiempo, no se reintenta. Ninguna caja puede tomar más de **3,5 segundos** en total.
- Una caja que no responde, o que responde algo que no se entiende, queda en `unavailable`.
- Un 404 solo significa «la persona no existe» si trae el código de error propio de la caja; otro 404 (por ejemplo, una ruta mal configurada) cuenta como caja no disponible.
- El resultado se decide así: si hay una afiliación vigente en otra caja, `AFILIADO_OTRA_CAJA`; si no la hay pero alguna caja no respondió, `INDETERMINADO`; solo si todas respondieron y ninguna la tiene, `NO_AFILIADO`.
- Al arrancar, el servicio espera hasta 8 segundos a que las cajas acepten conexiones, para que las primeras consultas tras un reinicio no salgan indeterminadas.

Los tiempos están en `config/cajas.yaml` y se pueden ajustar por caja.

## Alternativas

- **Esperar a que la caja responda, sin tope:** el resultado sería siempre completo, pero con una caja lenta la respuesta tardaría 8 segundos o más, y una sola caja colgada bloquearía todas las consultas.
- **Responder con lo que haya y dar `NO_AFILIADO` si las cajas que contestaron no tienen a la persona:** es rápido, pero produce falsos negativos, incumple el contrato y la regla de veracidad.
- **Guardar respuestas anteriores y usarlas cuando una caja falle:** respondería más casos, pero con datos desactualizados y guardando información personal que no necesitamos.
- **Un «corte» global que deje de consultar a una caja que viene fallando:** ahorra esperas, pero cuando la caja se recupera seguiría respondiendo `INDETERMINADO` por un tiempo. Para la consulta en línea lo descartamos.

## Consecuencias

- **Se gana:** nunca hay un falso `NO_AFILIADO`. Con Caja Norte caída, una persona afiliada solo en Norte sale `INDETERMINADO` con NORTE en `unavailable` (prueba P07 y `test_caja_caida_responde_indeterminado`).
- **Se gana:** con Caja Norte lenta la respuesta llega en unos 2,5 segundos, por debajo de los 5 que exige el contrato (P08 y `test_caja_lenta_responde_en_menos_de_5_segundos`).
- **Se acepta:** un `INDETERMINADO` obliga a la caja consumidora a repetir la consulta más tarde.
- **Se acepta:** una caja que tarde más de 2,5 segundos en un día malo, aunque esté funcionando, se informará como no disponible. Si pasa seguido, se sube su tiempo en el YAML.
