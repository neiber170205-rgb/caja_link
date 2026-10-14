# ADR 002: Cajas declaradas por configuración y un conector por protocolo

- Estado: aceptada
- Fecha: 2026-10-13

## Contexto

Cada caja se consulta distinto: cambian el protocolo (REST, SOAP o archivo), la forma de autenticarse (encabezado propio, token Bearer o credenciales dentro del sobre SOAP), los nombres de los campos, el formato de las fechas y la forma de escribir el documento (Caja Oriente exige 12 dígitos con ceros a la izquierda). El reto pide que una cuarta caja, Caja Sur, se pueda sumar sin rehacer el sistema: el validador oficial la activa poniendo `CAJA_SUR_ENABLED=true` en el `.env` y reiniciando el servicio. También exige que ningún archivo de `src/` tenga escritas direcciones de cajas y que ningún secreto quede en el repositorio.

## Decisión

Las cajas se declaran en `config/cajas.yaml`. Cada entrada dice el identificador de la caja, qué tipo de conector usa (`rest-json`, `soap` o `flat-file`), cómo se llaman sus campos, el formato de sus fechas, cómo se traducen sus tipos de afiliado y si está activa. Las direcciones, claves y tokens no se escriben en el YAML: se escribe el **nombre** de la variable de entorno que los contiene (por ejemplo `base_url_env: CAJA_NORTE_URL`), y el servicio lee el valor del `.env` al arrancar.

En el código hay un conector por protocolo, no por caja. Caja Norte y Caja Sur usan el mismo conector REST con mapeos distintos; Caja Oriente usa el conector SOAP y Caja Centro el de archivo plano.

## Alternativas

- **Un módulo de código por cada caja:** es lo más directo al principio, pero cada caja nueva obliga a escribir, probar y desplegar código, y la política de fallas termina repetida en cada módulo.
- **Direcciones y claves escritas en el código o en el YAML:** es lo más rápido de escribir, pero incumple la regla del reto sobre `src/` (0 en PE05) y deja secretos en el repositorio (resta 5 puntos).
- **Un conector totalmente genérico, con las plantillas SOAP y las reglas de cada caja descritas en el YAML:** sería más flexible, pero el archivo se volvería difícil de entender y de probar; con tres protocolos conocidos no compensa.

## Consecuencias

- **Se gana:** Caja Sur entró solo con configuración. Lo ensayamos como lo hace el validador: con `CAJA_SUR_ENABLED=true` y el reinicio, sus afiliaciones aparecen en las respuestas, y con la variable en `false` no se consulta.
- **Se gana:** una quinta caja que use un protocolo ya soportado se suma con una entrada en el YAML y sus variables en `.env`, sin tocar código.
- **Se gana:** ningún secreto ni dirección queda en el repositorio; las pruebas lo verifican (`test_secretos_no_estan_escritos_en_el_codigo`).
- **Se acepta:** un protocolo nuevo (por ejemplo gRPC) sí exige escribir un conector y registrarlo.
- **Se acepta:** el mapeo de campos solo sirve para campos de primer nivel del JSON; una respuesta muy anidada necesitaría código.
- **Se acepta:** un error en el YAML impide que el servicio arranque. Lo preferimos así, con un mensaje claro, a que responda con una configuración incompleta.
