# Caja Oriente — SOAP 1.1 (`http://localhost:9002/ws/AfiliacionService`)

WSDL: `GET /ws/AfiliacionService?wsdl`. Operación `ConsultarAfiliacion` (`SOAPAction: ConsultarAfiliacion`).

Caja Oriente maneja documentos de **12 dígitos con ceros a la izquierda**; los muestra con puntos
(`001.098.765.432`). Los puntos son opcionales en la petición; los ceros no.

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ori="http://cajaoriente.example/afiliacion">
  <soapenv:Header>
    <ori:Credenciales><ori:Usuario>caja-link</ori:Usuario><ori:Clave>oriente-pass</ori:Clave></ori:Credenciales>
  </soapenv:Header>
  <soapenv:Body>
    <ori:ConsultarAfiliacionRequest><ori:NumeroDocumento>001.098.765.432</ori:NumeroDocumento></ori:ConsultarAfiliacionRequest>
  </soapenv:Body>
</soapenv:Envelope>
```

Respuesta (resumida): `ori:Encontrado` (`true`/`false`) y, si existe, `ori:Persona` con `NombreCompleto`,
`Telefono`, `Direccion` y `ori:Afiliaciones/ori:Afiliacion` (`FechaIngreso` y `FechaRetiro` en `DD/MM/YYYY`,
`FechaRetiro` vacía si sigue vigente; `TipoAfiliado`: `D` dependiente, `I` independiente, `P` pensionado).

Errores: SOAP Fault con HTTP 500 (credenciales, formato de documento). `503` si el servicio no está disponible.
