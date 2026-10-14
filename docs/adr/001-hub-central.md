# ADR 001: Hub central de interoperabilidad

- Estado: aceptada
- Fecha: 2026-10-13

## Contexto

Antes de otorgar un subsidio, una caja debe verificar que la persona no tenga afiliación vigente en otra caja. Hoy eso se hace con archivos mensuales o con servicios punto a punto. Las cajas no se parecen entre sí: Caja Norte expone REST con JSON, Caja Oriente SOAP con XML, Caja Centro solo publica un archivo plano diario y Caja Sur llega con un REST v2 nuevo. Con integraciones punto a punto, cinco cajas serían diez integraciones distintas, cada una con su formato, sus credenciales y sus fallas.

Además, toda consulta debe cumplir las mismas reglas: autenticación de la caja que pregunta, finalidad declarada, dato mínimo, auditoría, nunca un falso «no afiliado» cuando una caja no responde, y respuesta en menos de 5 segundos.

## Decisión

Construimos un servicio central, `caja-link`, que escucha en el puerto 8083. Cada caja se integra una sola vez con él. El hub autentica a la caja que consulta, valida la finalidad, pregunta en paralelo a todas las demás cajas por sus propias interfaces, traduce sus respuestas a un modelo común, decide el resultado y deja el registro de auditoría. Las cajas nunca hablan directamente entre sí.

## Alternativas

- **Federado (cada caja consulta directamente a las demás):** no tiene un punto único de falla, pero exige N×(N−1)/2 integraciones, repite en cada caja las reglas de finalidad, dato mínimo y auditoría, y deja la trazabilidad repartida entre todas.
- **Hub con copia local de los datos de todas las cajas:** respondería aunque una caja esté caída y sería más rápido, pero guardaría datos personales que no necesita (contra el principio de dato mínimo de la Ley 1581), respondería con información desactualizada, y el reto prohíbe leer los datos internos de las cajas.
- **Bus de mensajes entre cajas:** desacopla a las cajas, pero agrega infraestructura nueva y la consulta en línea necesita una respuesta inmediata, no un mensaje que llegue después.

## Consecuencias

- **Se gana:** una sola integración por caja; las reglas de seguridad y privacidad viven en un único lugar; sumar una caja nueva es un cambio de configuración (ver ADR 002).
- **Se acepta:** el hub es un punto único de falla: si se cae, nadie puede consultar. Se mitiga con el `healthcheck` y el reinicio automático del contenedor (`restart: unless-stopped`).
- **Se acepta:** el tiempo de respuesta es el de la caja más lenta, con un tope por caja (ver ADR 003).
- **Pendiente:** hoy el servicio corre como un solo proceso, porque la auditoría y los lotes viven en memoria (ver ADR 004). Para correr varias copias habría que moverlos a un almacenamiento compartido.
