# =============================================================================
# main.py — Punto de entrada de Caja Link.
#
# Arma la aplicación: lee la configuración, crea los conectores de las cajas,
# registra las rutas y define cómo se responden los errores.
# Uvicorn carga la variable "app" de este archivo (ver src/Dockerfile).
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# logging (estándar): configura los mensajes que se ven con "docker compose logs".
# contextlib.asynccontextmanager (estándar): permite escribir en una sola función
#     lo que pasa al arrancar y al apagar el servicio.
# httpx: cliente HTTP asíncrono; se crea UNO solo y lo comparten todos los conectores
#     para reutilizar conexiones con las cajas.
# fastapi: FastAPI es la aplicación web; Request representa cada petición.
# fastapi.exceptions.RequestValidationError: error de FastAPI cuando un parámetro no
#     tiene el tipo esperado (por ejemplo limit=abc).
# fastapi.responses.JSONResponse: respuesta JSON con el código HTTP que se indique.
# starlette.exceptions.HTTPException: error HTTP genérico (ruta inexistente, método no permitido).
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import affiliations, audit as audit_api, batch as batch_api
from app.audit import AuditLog
from app.auth import Authenticator
from app.batch import BatchManager
from app.config import load_settings
from app.connectors import build_connectors
from app.domain.service import AffiliationService
from app.errors import ApiError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# httpx escribe la URL de cada petición, y esa URL lleva el documento consultado.
# Se sube su nivel a WARNING para que ningún documento quede en los registros.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Conexiones simultáneas que se permiten hacia las cajas (pensado para el cruce por lote).
MAX_CONNECTIONS = 200
MAX_KEEPALIVE_CONNECTIONS = 100

# Espera máxima, al arrancar, a que las cajas activas acepten conexiones.
WARM_UP_SECONDS = 8.0


# Ciclo de vida del servicio: lo que está antes de "yield" corre al arrancar y lo
# que está después corre al apagar.
# Recibe: la aplicación FastAPI.
# Al arrancar deja en app.state lo que usan las rutas: autenticador, servicio de
# consulta, auditoría y gestor de lotes. Al apagar cierra las conexiones con las cajas.
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    http = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=MAX_CONNECTIONS, max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS),
        trust_env=False,          # no usar proxies del entorno para hablar con las cajas
        follow_redirects=False,   # una caja no debe poder redirigirnos a otro destino
    )
    app.state.settings = settings
    app.state.authenticator = Authenticator(settings)
    app.state.service = AffiliationService(build_connectors(settings, http))
    app.state.audit = AuditLog()
    app.state.batch = BatchManager(app.state.service, app.state.audit)
    await app.state.service.warm_up(WARM_UP_SECONDS)
    logger.info("Caja Link listo")
    yield
    await http.aclose()


# Crea y configura la aplicación FastAPI.
# No recibe nada. Devuelve: la aplicación con rutas y manejo de errores registrados.
def create_app() -> FastAPI:
    app = FastAPI(
        title="Caja Link",
        description="Servicio de interoperabilidad entre cajas de compensación.",
        version="2.0.0",
        lifespan=lifespan,
    )
    app.include_router(affiliations.router)
    app.include_router(audit_api.router)
    app.include_router(batch_api.router)

    # Ruta de salud: la usa docker compose para saber si el servicio ya arrancó.
    # No pide token y no entrega información del sistema.
    @app.get("/health", tags=["Salud"], summary="Estado del servicio")
    async def health() -> dict:
        return {"status": "UP"}

    # Agrega a todas las respuestas el encabezado que prohíbe guardarlas en caché:
    # las respuestas hablan de afiliaciones de personas y no deben quedar en intermediarios.
    @app.middleware("http")
    async def no_store(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    # Convierte un ApiError en la respuesta JSON {"error", "message"} con su código HTTP.
    # En los 401 agrega WWW-Authenticate, como pide el estándar HTTP.
    @app.exception_handler(ApiError)
    async def handle_api_error(request: Request, error: ApiError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else None
        return JSONResponse(status_code=error.status, content={"error": error.code, "message": error.message}, headers=headers)

    # Parámetros con tipo equivocado: el contrato pide 400 (FastAPI respondería 422).
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": "PETICION_INVALIDA", "message": "Revise los parámetros de la petición"})

    # Rutas que no existen o métodos no permitidos, con el mismo formato de error.
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(status_code=error.status_code, content={"error": "HTTP_{0}".format(error.status_code), "message": str(error.detail)})

    # Cualquier error no previsto: se registra completo en el servidor y al cliente
    # solo se le dice que hubo un error interno, sin detalles del sistema.
    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        # Se registra la plantilla de la ruta (/api/v1/affiliations/{document}), no la URL
        # real: así el documento consultado tampoco queda escrito cuando hay un error.
        route = request.scope.get("route")
        logger.exception("Error no controlado en %s %s", request.method, getattr(route, "path", "ruta desconocida"))
        return JSONResponse(status_code=500, content={"error": "ERROR_INTERNO", "message": "Error interno del servicio"})

    return app


app = create_app()
