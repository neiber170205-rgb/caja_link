# Caja Centro — archivo plano diario (`caja-centro/`)

Caja Centro no expone servicios. Cada noche deja `centro_afiliados_YYYYMMDD.txt` con la información
del día anterior. Usen siempre el archivo más reciente.

```text
FECHA_CORTE|2026-10-03
TIPO_DOC|NUMERO_DOCUMENTO|FECHA_INICIO|FECHA_FIN|TIPO_AFILIADO|NOMBRE|SALARIO
CC|1098765432|20190201||DEP|NOMBRE COMPLETO|2500000
```

- Fechas `YYYYMMDD`; `FECHA_FIN` vacía = vigente.
- `TIPO_AFILIADO`: `DEP`, `IND`, `PEN`.
- Las coincidencias que vengan de este archivo se informan con `"source": "FILE"` y `"asOf"` = `FECHA_CORTE`.
