# Caja Sur — REST JSON v2 (`http://localhost:9004`, perfil `caja-sur`)

Se activa con `docker compose --profile caja-sur up -d`. Debe poder incorporarse **por configuración**
(por ejemplo `config/cajas.yaml` + `CAJA_SUR_ENABLED=true`), sin reescribir el servicio.

**Autenticación:** `Authorization: Bearer <CAJA_SUR_TOKEN>`.

`GET /v2/people/{documento}/memberships` — documento solo dígitos.

```json
200
{
  "person": { "id": "1098765432", "fullName": "...", "email": "...", "monthlySalary": 3100000 },
  "memberships": [ { "start": "2021-06-01", "end": null, "category": "DEPENDENT" } ]
}
```

- `category`: `DEPENDENT`, `SELF_EMPLOYED`, `RETIREE` (equivalen a `DEPENDIENTE`, `INDEPENDIENTE`, `PENSIONADO`).
- `404 {"error": "person_not_found"}`; `401` sin token; `503` si no está disponible.

## Cómo la activa el validador oficial (P14)

1. Pone `CAJA_SUR_ENABLED=true` en el `.env` del repositorio.
2. Ejecuta `docker compose --profile caja-sur up -d --force-recreate`.
3. Espera a que el puerto 8083 responda y consulta afiliados que solo existen en Caja Sur.
