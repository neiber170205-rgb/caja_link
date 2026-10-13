# Caja Link — interoperabilidad entre cajas (nivel Profesional)

Antes de otorgar una tarifa subsidiada o un subsidio, una caja debe verificar que la persona no tenga
afiliación vigente en otra caja. Ustedes construyen el servicio que lo hace posible.

> Esta es la guía del kit. La documentación de **su** software va en `README.md`, que trae la plantilla con el formato obligatorio (entregable «README: documentación del software»).

## Arranque

```bash
cp .env.example .env
docker compose up -d --build        # Caja Norte (9001) y Caja Oriente (9002)
./validator check                   # revisión rápida del contrato
./validator check --lote            # incluye el lote de 10.000 documentos
```

Caja Sur se enciende con `docker compose --profile caja-sur up -d` (puerto 9004).
`./reset.sh` borra todo y vuelve a levantar el entorno desde cero.

## Qué contiene

| Ruta | Contenido |
|---|---|
| `mocks/` | Cajas simuladas (Norte REST, Oriente SOAP, Sur REST v2) y sus datos |
| `caja-centro/` | Archivo plano diario de Caja Centro |
| `data/lote_10000.csv` | Documentos para el cruce por lote |
| `docs/cajas/` | Cómo consultar cada caja |
| `docs/proteccion-datos.md` | Resumen de finalidad y dato mínimo (Ley 1581) |

Cada caja simulada acepta `POST /__chaos` con `{"mode": "ok" | "down" | "slow"}`; el validador lo usa
para provocar caídas y lentitud. Déjenla en `ok` cuando terminen sus pruebas.

## Contrato (puerto 8083)

Cada caja consumidora se autentica con `Authorization: Bearer <token>` (`NORTE_TOKEN`, `ORIENTE_TOKEN`,
`CENTRO_TOKEN`, `SUR_TOKEN`, `ADMIN_TOKEN` del `.env`). La caja que consulta es la dueña del token.

- `GET /api/v1/affiliations/{document}?purpose=<finalidad>` → `requestId`, `result`
  (`AFILIADO_OTRA_CAJA`, `NO_AFILIADO`, `INDETERMINADO`), `matches` (`caja`, `validFrom`, `validTo`,
  `source` `ONLINE|FILE`, `asOf`) y `unavailable`.
- `GET /api/v2/affiliations/{document}?purpose=...` → igual, con `affiliateType` en cada match.
- `POST /api/v1/batch-checks` con encabezado `Idempotency-Key` y el CSV (columna `document`) como cuerpo
  `text/csv` (también se acepta multipart con el campo `file`) → `202 {"jobId"}`.
- `GET /api/v1/batch-checks/{jobId}` → `{"status": "PENDING|RUNNING|DONE", "results": [{"document", "result", ...}]}`.
- `GET /api/v1/audit?limit=100` (solo `ADMIN_TOKEN`) → entradas con `timestamp`, `requestingCaja`,
  `purpose`, `result`, `documentMasked`.

Una afiliación es **vigente** si no tiene fecha de fin o su fecha de fin es igual o posterior a la fecha
de corte de la consulta. Agreguen su servicio al `docker-compose.yml` (hay una plantilla comentada).

La cuarta caja debe sumarse por configuración: el validador oficial pone `CAJA_SUR_ENABLED=true` en el
`.env` y ejecuta `docker compose --profile caja-sur up -d --force-recreate` (ver `docs/cajas/sur.md`).
Las cuatro cajas se declaran en `config/cajas.yaml` y ningún archivo de `src/` puede tener escritas sus
direcciones (`caja-norte`, `:9001`…).

**Límite de acceso:** su servicio habla con las cajas solo por sus interfaces (REST, SOAP y el archivo de
Caja Centro). Montar `mocks/` o leer `mocks/data` desde `src/` es una penalización automática.

**Pruebas del equipo:** servicio `tests` en `docker-compose.yml` con `profiles: ["test"]` que prueba el
servicio en funcionamiento y deja un reporte JUnit XML en `./test-results/`.

## Entregables

`src/`, `tests/`, `config/cajas.yaml`, `docker-compose.yml`, `openapi.yaml` (v1, v2, lote y auditoría),
`README.md` (documentación de su software), `AI_USAGE.md` y `docs/` con `architecture.md`, `adr/` (3 a 5), `threat-model.md` y
`load-test.md`. Los documentos ya vienen como plantillas con el formato obligatorio (vacías no suman;
copien `docs/adr/000-plantilla.md` para cada ADR).

`./validator entregables` los revisa con las mismas reglas y puntos del calificador oficial. Las filas de
`threat-model.md` se comprueban contra el último reporte de `test-results/`; generen uno con
`docker compose --profile test run --rm tests`.
