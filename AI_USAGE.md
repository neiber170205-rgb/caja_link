# Uso de inteligencia artificial

Usamos Claude Code durante todo el reto. En cada uso se indica qué produjo la herramienta y qué decidió, revisó o corrigió el equipo.

## Uso 1
- Herramienta: Claude Code
- Para qué se usó: entender el reto y planear la arquitectura comparando alternativas
- Prompt principal (resumido): "Lee RETO.md y RUBRICA.md y propón la estructura del proyecto: backend, frontend y despliegue. Para cada decisión dame dos o tres alternativas con su costo y su riesgo, y recomienda una justificándola."
- Qué produjo: un resumen de lo que se califica, la aclaración de que el reto no pide frontend ni despliegue en la nube, y comparaciones de alternativas: hub central, federado o con copia local; estado en memoria, SQLite o Redis; pruebas con pytest o con Postman y Newman
- Qué modificó o corrigió el equipo: le exigimos comparar varias opciones en lugar de aceptar la primera propuesta, elegimos el hub central con Python, FastAPI y pytest, y decidimos no construir un frontend porque no suma puntos

## Uso 2
- Herramienta: Claude Code
- Para qué se usó: organizar el trabajo y asignar las tareas entre los dos integrantes
- Prompt principal (resumido): "Crea en Notion un tablero para repartir las tareas entre Neiber y Santiago, ordenadas según se ejecutan y con lo que hay que hacer en cada una. Escribe también una guía en Markdown para Santiago con las reglas del equipo: commits claros de máximo 300 líneas, código documentado y endpoints documentados."
- Qué produjo: un tablero en Notion con 19 tareas ordenadas, cada una con sus pasos, cómo comprobarla y commits sugeridos, y una guía de trabajo para el compañero
- Qué modificó o corrigió el equipo: asignamos cada tarea a uno de los dos integrantes, definimos las reglas de la guía (commits claros de máximo 300 líneas, código y endpoints documentados) y pedimos ordenar las tareas según el orden real en que se ejecutan

## Uso 3
- Herramienta: Claude Code
- Para qué se usó: generar la base del servicio de consulta en línea y revisar el diseño de su autenticación
- Prompt principal (resumido): "Usaremos Python. Documenta cada librería que uses y para qué sirve, y escribe antes de cada función qué hace, qué recibe y qué devuelve." Y luego: "En auth.py la constante ADMIN está escrita en el código. Explícame qué representa y por qué está así, y dame alternativas para que el rol de administrador no dependa de un valor fijo."
- Qué produjo: el código de la consulta en línea (catálogo de cajas, conectores REST, SOAP y de archivo plano, autenticación, auditoría y rutas v1 y v2), que pasó 11 de las 14 pruebas del validador en el primer intento. La autenticación traía el rol de administrador como etiqueta fija y, al cuestionarla, propuso tres alternativas comparadas
- Qué modificó o corrigió el equipo: revisamos cada archivo con preguntas de control antes de aceptarlo como base; detectamos que una caja llamada ADMIN podría hacerse pasar por administrador, elegimos separar el rol en una clase aparte y la implementamos nosotros con su guía, corrigiendo cuatro detalles en la revisión

## Uso 4
- Herramienta: Claude Code
- Para qué se usó: construir y medir el cruce por lote de 10.000 documentos
- Prompt principal (resumido): "Para el cruce por lote, analiza el contrato y dame opciones de diseño con sus ventajas y riesgos. Implementa la opción elegida y verifícala con el validador antes de entregarla; nosotros revisamos y hacemos los commits, de máximo 300 líneas cada uno."
- Qué produjo: cuatro decisiones de diseño con sus alternativas, el código del lote y una medición que mostró que su propia recomendación inicial, 50 documentos a la vez, era más lenta: 46 segundos frente a 19 con un tope de 24 consultas
- Qué modificó o corrigió el equipo: aceptamos las opciones después de compararlas, partimos el trabajo en commits de menos de 300 líneas y lo medimos con el script de carga del equipo (19 y 38 segundos, sin errores); la limitación con una caja lenta la dejamos documentada en lugar de agregar más código

## Uso 5
- Herramienta: Claude Code
- Para qué se usó: redactar la documentación del proyecto (ADR y README)
- Prompt principal (resumido): "Redacta los ADR 001 a 004 con las decisiones que tomamos (hub central, cajas por configuración, INDETERMINADO ante fallas y lote en segundo plano), cada uno con al menos dos alternativas. Después, el README: puntual, poco técnico, y con las dependencias para instalarlo en una máquina limpia."
- Qué produjo: los borradores de cuatro ADR y del README, con datos reales de las pruebas y las mediciones
- Qué modificó o corrigió el equipo: revisamos los borradores, cuestionamos el motivo para descartar una base de datos en el ADR 004, que se reescribió con el argumento de privacidad, y pedimos un README menos técnico con las dependencias para instalarlo en una máquina limpia
