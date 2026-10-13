# Caja Link — <nombre de la pareja>

<!--
Documentación del software de la pareja (entregable «README: documentación del software», 2 puntos).
Llenen cada sección; conserven los títulos ## tal como están. Los comentarios como este no cuentan
y una sección vacía no suma. La guía del kit está en KIT.md.
-->

## Descripción

<!-- Qué problema resuelve su software y para quién (al menos 30 palabras). -->

## Integrantes

<!-- Una viñeta por integrante con su nombre completo. -->

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

<!-- Los comandos, en orden, para levantarlo desde una copia limpia (al menos 15 palabras). Deben aparecer `docker compose` con `up`. -->

## Configuración

<!-- Expliquen cada variable de .env.example: nombre, para qué sirve y un valor de ejemplo. El sistema verifica que estén todas. -->

## Arquitectura

<!-- Componentes y cómo se comunican (al menos 30 palabras). Nombren cada servicio de docker-compose.yml; el sistema verifica que estén todos. -->

## Uso

<!-- Las rutas del servicio con un ejemplo de cada una: /api/v1/affiliations/{document}, /api/v2/affiliations/{document}, /api/v1/batch-checks, /api/v1/batch-checks/{jobId} y /api/v1/audit. El sistema verifica que aparezcan las cinco. -->

## Pruebas

<!-- Qué prueban sus pruebas automatizadas y cómo se ejecutan con docker compose --profile test run --rm tests (al menos 15 palabras). -->

## Documentación

<!-- Enlaces a los demás documentos del repositorio: docs/architecture.md, docs/adr/, docs/threat-model.md, docs/load-test.md, openapi.yaml, config/cajas.yaml y AI_USAGE.md. -->

## Qué resolvimos

<!-- Qué problemas encontraron, cómo los resolvieron y qué quedó funcionando (al menos 30 palabras). -->

## Limitaciones y pendientes

<!-- Qué no alcanzaron a hacer o qué falla todavía (al menos 10 palabras). -->
