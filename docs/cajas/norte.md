# Caja Norte — REST JSON (`http://localhost:9001`, en compose `http://caja-norte:9001`)

**Autenticación:** encabezado `X-Api-Key: <CAJA_NORTE_API_KEY>`.

`GET /api/v1/afiliados/{documento}` — documento solo con dígitos, sin puntos ni ceros de relleno.

```json
200
{
  "documento": "1098765432",
  "titular": { "nombre": "...", "direccion": "...", "telefono": "...", "correo": "...", "salario": 2500000, "beneficiarios": ["..."] },
  "afiliaciones": [
    { "fechaInicio": "2019-02-01", "fechaFin": null, "tipoAfiliado": "DEPENDIENTE", "estado": "VIGENTE" },
    { "fechaInicio": "2010-05-03", "fechaFin": "2014-01-31", "tipoAfiliado": "INDEPENDIENTE", "estado": "HISTORICA" }
  ]
}
```

- `404 {"error": "NO_ENCONTRADO"}` si la persona nunca estuvo afiliada.
- `400 {"error": "DOCUMENTO_INVALIDO"}` si el documento tiene caracteres distintos a dígitos.
- `503` cuando el servicio no está disponible. A veces responde lento.
