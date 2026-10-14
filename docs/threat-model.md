# Modelo de amenazas

<!--
Plantilla con el formato obligatorio: una fila por categoría.
- Amenaza y Mitigación: al menos 3 palabras cada una.
- Prueba: el nombre de una prueba automatizada del equipo que demuestra la mitigación
  (por ejemplo test_consulta_sin_token_responde_401 o tests.test_auth::test_consulta_sin_token_responde_401).
  El sistema verifica que esa prueba aparezca APROBADA en el reporte JUnit de test-results/.
Revisen con: ./validator entregables
-->

| Categoría | Amenaza | Mitigación | Prueba |
|---|---|---|---|
| Autenticación | Una caja sin token o con un token falso consulta afiliaciones de personas | Cada ruta exige `Authorization: Bearer`; `src/app/auth.py` compara el token con el de cada caja usando `hmac.compare_digest` y responde 401 si falta o no coincide. El token de administrador solo sirve para la auditoría (403 en las consultas) | test_consulta_sin_token_responde_401 |
| Finalidad | Alguien consulta sin declarar para qué usará el dato de afiliación | `validate_purpose` en `src/app/api/affiliations.py` exige `purpose` dentro de TARIFA_SUBSIDIADA, SUBSIDIO_MONETARIO o VALIDACION_AFILIACION y responde 400 si falta o es otra. La finalidad queda registrada en la auditoría | test_consulta_sin_purpose_responde_400 |
| Dato mínimo | La respuesta deja ver nombre, salario, dirección u otros datos personales | Los conectores traducen la respuesta de cada caja al modelo `Affiliation` de `src/app/domain/models.py`, que solo guarda caja, fechas de vigencia, fuente, fecha de corte y tipo de afiliado. Los demás campos se descartan al leerlos y nunca salen del servicio | test_respuesta_no_contiene_datos_personales |
| Secretos | Un token o una clave de las cajas queda escrito en el repositorio | Los tokens y claves viven en `.env`, que git ignora. `config/cajas.yaml` solo guarda el nombre de cada variable (`consumer_token_env`, `value_env`) y `src/app/config.py` lee su valor de `os.environ` al arrancar | test_secretos_no_estan_escritos_en_el_codigo |
| Auditoría | No queda rastro de quién consultó, o el rastro expone el documento completo | `AuditLog.record` en `src/app/audit.py` registra cada consulta en línea y cada documento del lote con hora, caja, finalidad y resultado, y guarda el documento con `mask_document`: solo quedan visibles los últimos 4 dígitos | test_auditoria_enmascara_el_documento |
