# Protección de datos — resumen para Caja Link (Ley 1581 de 2012)

- **Finalidad:** todo tratamiento debe tener una finalidad legítima, informada y verificable. Cada consulta
  declara `purpose` (`TARIFA_SUBSIDIADA`, `SUBSIDIO_MONETARIO`, `VALIDACION_AFILIACION`); sin finalidad no hay respuesta.
- **Dato mínimo (necesidad):** solo se comparte lo indispensable para la finalidad. Para validar afiliación basta
  saber *si* existe afiliación vigente, en qué caja y desde/hasta cuándo. Nunca: nombre, dirección, teléfono,
  correo, salario ni beneficiarios.
- **Seguridad y acceso restringido:** autenticación de cada caja; secretos fuera del repositorio.
- **Trazabilidad:** quién consultó, con qué finalidad y qué resultado obtuvo; el documento se registra enmascarado.
- **Veracidad:** no se informa "no afiliado" si no se pudo consultar a todas las cajas.
