# Caja Link — Neiber Araque y Santiago Alarcón

## Descripción

Antes de otorgar un subsidio o una tarifa subsidiada, una caja de compensación familiar debe confirmar que la persona no tenga afiliación vigente en otra caja. Hoy eso se hace con archivos mensuales o con integraciones una a una.

Caja Link resuelve esa pregunta en segundos: consulta a todas las cajas a la vez, sin compartir bases de datos, sin mostrar datos personales y sin responder «no afiliado» cuando alguna caja no contesta. También cruza archivos completos de documentos para detectar dobles afiliaciones. Lo usan las cajas de compensación conectadas: Norte, Oriente, Centro y Sur.

## Integrantes

- Neiber Danilo Araque Pacheco
- Santiago Alarcón Gutiérrez

## Requisitos

Todo el proyecto corre dentro de contenedores. En la máquina solo se instalan las herramientas de esta tabla; las librerías de Python del servicio se instalan solas al construir la imagen.

| Herramienta | Para qué se usa | Versión probada | Mínima recomendada |
|---|---|---|---|
| Docker Engine | Construir y ejecutar los contenedores | 29.8.1 | 24 o superior |
| Docker Compose (plugin) | Levantar todos los servicios con un solo comando | 5.5.1 | 2.24 o superior |
| Git | Descargar el repositorio | 2.55.0 | 2.30 o superior |
| Python 3 | Ejecutar `./validator`, que solo usa la biblioteca estándar | 3.14.7 | 3.8 o superior |
| curl | Hacer peticiones de prueba desde la terminal (opcional) | 8.22.0 | Cualquiera |

La columna «Versión probada» es la de la máquina donde se desarrolló (Linux, x86_64). La columna «Mínima recomendada» es una recomendación: no se probó con versiones anteriores.

A tener en cuenta:

- **Compose debe ser el plugin moderno**, el que se invoca como `docker compose` (con espacio). El antiguo `docker-compose` (con guion, versión 1) no sirve.
- **No hay que instalar Python 3.12, FastAPI ni ninguna librería en la máquina.** Van dentro de la imagen del servicio.
- **Sistema operativo:** probado en Linux, que es también el sistema del servidor que califica. En Windows o macOS haría falta Docker Desktop; no se probó.
- **Internet en la primera construcción:** se descarga la imagen `python:3.12-slim` (unos 180 MB) y las librerías.
- **Recursos:** las imágenes ocupan menos de 500 MB de disco y los tres contenedores usan cerca de 80 MB de memoria en reposo.
- **Puertos libres:** 8083 (el servicio), 9001 (Caja Norte), 9002 (Caja Oriente) y 9004 (Caja Sur, solo si se activa).

### Lo que va dentro del contenedor

Se instala automáticamente al construir. Las versiones están fijas en [src/requirements.txt](src/requirements.txt), donde se explica cada librería.

| Componente | Versión | Para qué se usa |
|---|---|---|
| Python | 3.12 (imagen `python:3.12-slim`) | Lenguaje del servicio |
| FastAPI | 0.115.6 | Framework web: define las rutas y responde en JSON |
| Uvicorn | 0.34.0 | Servidor que escucha en el puerto 8083 |
| HTTPX | 0.28.1 | Cliente HTTP para consultar las cajas en paralelo y con tiempo máximo |
| PyYAML | 6.0.2 | Lee el catálogo `config/cajas.yaml` |
| defusedxml | 0.7.1 | Lee de forma segura la respuesta XML de Caja Oriente |
| python-multipart | 0.0.20 | Recibe el CSV del lote cuando llega como formulario |

### Preparar una máquina limpia (Ubuntu o Debian)

```bash
# Git, Python 3 y curl
sudo apt-get update
sudo apt-get install -y git python3 curl ca-certificates

# Docker Engine con el plugin de Compose (instalador oficial de Docker)
curl -fsSL https://get.docker.com | sudo sh

# Usar Docker sin sudo (hay que cerrar la sesión y volver a entrar)
sudo usermod -aG docker "$USER"
```

Para comprobar que todo quedó instalado:

```bash
docker --version
docker compose version
git --version
python3 --version
```

En otros sistemas, seguir la guía oficial: <https://docs.docker.com/engine/install/>

## Instalación y ejecución

1. Descargar el repositorio y entrar en la carpeta:

   ```bash
   git clone https://github.com/neiber170205-rgb/caja_link.git
   cd caja_link
   ```

2. Crear el archivo de configuración a partir del ejemplo:

   ```bash
   cp .env.example .env
   ```

3. Levantar todo y esperar a que el servicio esté listo:

   ```bash
   docker compose up -d --build --wait
   ```

4. Comprobar que responde: `curl http://localhost:8083/health` debe devolver `{"status": "UP"}`. Para una revisión completa, `./validator check`.

5. Para sumar la cuarta caja (Caja Sur), poner `CAJA_SUR_ENABLED=true` en `.env` y reiniciar con:

   ```bash
   docker compose --profile caja-sur up -d --force-recreate
   ```

6. Para apagar todo: `docker compose --profile "*" down`.

## Configuración

Todo se configura en `.env`, que nunca se sube al repositorio; `.env.example` trae valores de prueba. Las cajas y la forma de consultarlas se declaran aparte, en [config/cajas.yaml](config/cajas.yaml).

**Tokens con los que cada caja se identifica ante Caja Link** (cada caja usa el suyo):

| Variable | Para qué sirve | Ejemplo |
|---|---|---|
| `NORTE_TOKEN` | Token de Caja Norte cuando consulta | `token-norte-123` |
| `ORIENTE_TOKEN` | Token de Caja Oriente cuando consulta | `token-oriente-123` |
| `CENTRO_TOKEN` | Token de Caja Centro cuando consulta | `token-centro-123` |
| `SUR_TOKEN` | Token de Caja Sur cuando consulta | `token-sur-123` |
| `ADMIN_TOKEN` | Token del administrador; solo sirve para leer la auditoría | `token-admin-123` |

**Cómo entra Caja Link a cada caja:**

| Variable | Para qué sirve | Ejemplo |
|---|---|---|
| `CAJA_NORTE_URL` | Dirección del servicio de Caja Norte | `http://caja-norte:9001` |
| `CAJA_NORTE_API_KEY` | Clave para consultar a Caja Norte | La que entregue Caja Norte |
| `CAJA_ORIENTE_URL` | Dirección del servicio SOAP de Caja Oriente | `http://caja-oriente:9002/ws/AfiliacionService` |
| `CAJA_ORIENTE_USER` | Usuario para consultar a Caja Oriente | El que entregue Caja Oriente |
| `CAJA_ORIENTE_PASSWORD` | Clave para consultar a Caja Oriente | La que entregue Caja Oriente |
| `CAJA_CENTRO_DIR` | Carpeta, dentro del contenedor, donde está el archivo diario de Caja Centro | `/data/caja-centro` |
| `CAJA_SUR_URL` | Dirección del servicio de Caja Sur | `http://caja-sur:9004` |
| `CAJA_SUR_TOKEN` | Token para consultar a Caja Sur | El que entregue Caja Sur |
| `CAJA_SUR_ENABLED` | Activa Caja Sur como cuarta caja | `false` |

**Puertos en la máquina** (cambiar solo si están ocupados):

| Variable | Para qué sirve | Ejemplo |
|---|---|---|
| `CAJA_NORTE_PORT` | Puerto publicado de Caja Norte | `9001` |
| `CAJA_ORIENTE_PORT` | Puerto publicado de Caja Oriente | `9002` |
| `CAJA_SUR_PORT` | Puerto publicado de Caja Sur | `9004` |

## Arquitectura

Caja Link funciona como un punto central: cada caja se conecta una sola vez con él, y él se encarga de preguntarles a las demás. Cuando llega una consulta, revisa el token y la finalidad, pregunta en paralelo a las otras cajas (máximo 2,5 segundos por caja), junta las respuestas en un formato común, decide el resultado y deja el registro en la auditoría.

Los servicios de `docker-compose.yml`:

| Servicio | Qué es |
|---|---|
| `caja-link` | Nuestro servicio, en el puerto 8083 |
| `caja-norte` | Caja simulada del kit, con servicio REST |
| `caja-oriente` | Caja simulada del kit, con servicio SOAP |
| `caja-sur` | Cuarta caja simulada, REST v2; solo se enciende con el perfil `caja-sur` |
| `tests` | Nuestras pruebas automatizadas; solo corren con el perfil `test` |

Caja Centro no tiene servicio: publica un archivo diario en la carpeta `caja-centro/`, que Caja Link lee en modo de solo lectura. Las cajas no se comunican entre sí ni comparten bases de datos.

```text
caja que consulta ──► caja-link ──┬──► caja-norte   (REST)
                                  ├──► caja-oriente (SOAP)
                                  ├──► caja-sur     (REST v2, si está activa)
                                  └──► archivo de Caja Centro
```

El detalle está en [docs/architecture.md](docs/architecture.md) y en las decisiones de [docs/adr/](docs/adr/).

## Uso

Todas las rutas piden el encabezado `Authorization: Bearer <token>` con el token de la caja que consulta. La consulta en línea exige además la finalidad (`purpose`): `TARIFA_SUBSIDIADA`, `SUBSIDIO_MONETARIO` o `VALIDACION_AFILIACION`.

El resultado de una consulta es uno de tres:

| Resultado | Significa |
|---|---|
| `AFILIADO_OTRA_CAJA` | La persona tiene afiliación vigente en otra caja |
| `NO_AFILIADO` | Todas las cajas respondieron y ninguna la tiene |
| `INDETERMINADO` | Alguna caja no respondió y las demás no la tienen; esa caja aparece en `unavailable` |

**1. Consultar un documento — `GET /api/v1/affiliations/{document}`**

```bash
curl -H "Authorization: Bearer token-oriente-123" \
  "http://localhost:8083/api/v1/affiliations/8873901472?purpose=VALIDACION_AFILIACION"
```

```json
{
  "requestId": "01M4V1X7SK0RED410XSDJDZYPX",
  "result": "AFILIADO_OTRA_CAJA",
  "matches": [
    { "caja": "NORTE", "validFrom": "2024-06-27", "validTo": null, "source": "ONLINE", "asOf": "2026-10-13" }
  ],
  "unavailable": []
}
```

El documento se puede escribir con puntos, espacios o ceros a la izquierda. La caja que consulta nunca aparece en `matches`.

**2. Consultar con el tipo de afiliado — `GET /api/v2/affiliations/{document}`**

Igual a la anterior; cada coincidencia agrega `affiliateType` (`DEPENDIENTE`, `INDEPENDIENTE` o `PENSIONADO`).

```bash
curl -H "Authorization: Bearer token-oriente-123" \
  "http://localhost:8083/api/v2/affiliations/8873901472?purpose=VALIDACION_AFILIACION"
```

**3. Enviar un lote — `POST /api/v1/batch-checks`**

Recibe un CSV con la columna `document` y responde de inmediato con un `jobId`. Repetir el envío con la misma `Idempotency-Key` devuelve el mismo `jobId`.

```bash
curl -X POST -H "Authorization: Bearer token-norte-123" \
  -H "Idempotency-Key: nomina-octubre" -H "Content-Type: text/csv" \
  --data-binary @data/lote_10000.csv http://localhost:8083/api/v1/batch-checks
```

```json
{ "jobId": "01M4VTMRE8N86WHEVWBMDJVB08", "status": "PENDING" }
```

**4. Ver el estado de un lote — `GET /api/v1/batch-checks/{jobId}`**

`status` pasa por `PENDING`, `RUNNING` y `DONE`. Al terminar, `results` trae un resultado por documento, en el orden del archivo. Solo la caja que envió el lote puede verlo.

```bash
curl -H "Authorization: Bearer token-norte-123" \
  http://localhost:8083/api/v1/batch-checks/01M4VTMRE8N86WHEVWBMDJVB08
```

**5. Leer la auditoría — `GET /api/v1/audit`**

Solo con el token de administrador. Muestra quién consultó, para qué y con qué resultado; el documento aparece enmascarado.

```bash
curl -H "Authorization: Bearer token-admin-123" "http://localhost:8083/api/v1/audit?limit=100"
```

```json
[
  { "timestamp": "2026-10-13T16:35:38.994Z", "requestingCaja": "NORTE", "purpose": "SUBSIDIO_MONETARIO",
    "result": "AFILIADO_OTRA_CAJA", "documentMasked": "******6777", "channel": "ONLINE" }
]
```

Los tokens de estos ejemplos son ilustrativos: se usan los que haya en `.env`. El contrato completo, con un ejemplo de cada situación, está en [openapi.yaml](openapi.yaml).

**Probar desde el navegador.** Con el servicio arriba, `http://localhost:8083/docs` muestra ese mismo contrato y permite usarlo:

1. Pulsar **Authorize** y pegar el token de una caja tal como está en `.env`, sin la palabra `Bearer`.
2. Abrir una ruta y pulsar **Try it out**.
3. Llenar los parámetros y pulsar **Execute**. Debajo aparece la respuesta real del servicio, y en **Examples** los ejemplos de cada situación (afiliado, no afiliado, indeterminado, errores).

El servicio lee `openapi.yaml` una sola vez: si se modifica, hay que reiniciarlo con `docker compose restart caja-link`.

## Pruebas

Tenemos 29 pruebas automáticas que llaman al servicio en marcha, como lo haría una caja. Revisan la autenticación, la finalidad obligatoria, que el documento se normalice, que la caja que consulta no aparezca, que no salgan datos personales, que ningún secreto esté escrito en el código, el comportamiento con una caja caída o lenta, las dos versiones de la consulta, la auditoría y el lote.

Se ejecutan con:

```bash
docker compose --profile test run --rm tests
```

Dejan el reporte en `test-results/junit.xml`. Si se modificaron las pruebas, hay que agregar `--build` para que se use la versión nueva.

Otras dos verificaciones:

- `./validator check --lote`: el validador del kit, que revisa el contrato e incluye el lote de 10.000 documentos.
- `python3 scripts/prueba_carga.py`: la prueba de carga del lote (resultados en [docs/load-test.md](docs/load-test.md)).

## Documentación

- [docs/architecture.md](docs/architecture.md): cómo está hecho el servicio.
- [docs/adr/](docs/adr/): las decisiones de arquitectura y sus alternativas.
- [docs/threat-model.md](docs/threat-model.md): amenazas, cómo se mitigan y qué prueba lo demuestra.
- [docs/load-test.md](docs/load-test.md): la prueba de carga del lote.
- [openapi.yaml](openapi.yaml): el contrato de la API.
- [config/cajas.yaml](config/cajas.yaml): el catálogo de cajas.
- [AI_USAGE.md](AI_USAGE.md): cómo usamos la inteligencia artificial.

## Qué resolvimos

- **Cajas que no se parecen:** cada una usa una tecnología distinta (REST, SOAP, un archivo diario). Caja Link las traduce todas a un mismo formato, así quien consulta no tiene que conocerlas.
- **Cajas lentas o caídas:** cada caja tiene un tiempo máximo de respuesta. Si una no contesta, el resultado es `INDETERMINADO`, nunca un falso «no afiliado». La respuesta llega en menos de 5 segundos aunque una caja esté lenta.
- **Privacidad:** las cajas envían nombre, salario, teléfono y otros datos, pero Caja Link solo toma las fechas y la caja; lo demás se descarta. La auditoría guarda el documento enmascarado.
- **Una cuarta caja sin rehacer nada:** Caja Sur se suma cambiando una variable en `.env` y reiniciando.
- **Lotes grandes:** 10.000 documentos se cruzan en 19 segundos cuando se consulta una caja en línea y en 38 cuando son dos, sin errores.

Quedó funcionando: las 13 pruebas públicas del validador que se pueden revisar localmente (460 de 500 puntos; la de la cuarta caja solo la evalúa el oficial y la ensayamos a mano) y las 29 pruebas propias.

## Limitaciones y pendientes

- Los lotes y la auditoría se guardan en memoria: si el servicio se reinicia, se pierden.
- El servicio corre como un solo proceso; para tener varias copias habría que mover ese estado a un almacenamiento compartido.
- Si una caja está lenta (no caída) durante todo un lote, el lote puede pasar de los 5 minutos. La mejora prevista es dejar de consultar a esa caja cuando acumule varias fallas seguidas.
- Caja Link es un punto central: si se cae, nadie puede consultar. Se mitiga con el reinicio automático del contenedor.
- Solo se probó en Linux.
