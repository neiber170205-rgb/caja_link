# =============================================================================
# batch.py (API) — Rutas del cruce por lote.
#
#   POST /api/v1/batch-checks            recibe el CSV y responde 202 con el jobId
#   GET  /api/v1/batch-checks/{jobId}    estado y resultados del lote
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# fastapi.APIRouter: agrupa rutas para registrarlas juntas en la aplicación.
# fastapi.Depends: exige el token de una caja antes de entrar a la función.
# fastapi.Request: da acceso al cuerpo de la petición, sus encabezados y el gestor de lotes.
# fastapi.responses.JSONResponse: respuesta JSON con código HTTP propio (202). Además
#     escribe el JSON directo, que es más rápido con respuestas de 10.000 resultados.
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.api.affiliations import validate_purpose
from app.auth import require_caja
from app.batch import DEFAULT_PURPOSE, MAX_BODY_BYTES, parse_documents
from app.errors import ApiError

router = APIRouter(tags=["Cruce por lote"])

# Largo máximo de la llave de idempotencia.
MAX_KEY_LENGTH = 200


# Lee el archivo CSV de la petición.
# Recibe: la petición.
# Devuelve: el contenido del archivo en bytes.
# Acepta las dos formas de envío del contrato:
#   - el CSV directo en el cuerpo (Content-Type: text/csv)
#   - un formulario multipart con el archivo en el campo "file"
# Lanza ApiError 413 si el archivo supera el tamaño máximo y 400 si el formulario no trae "file".
async def read_csv(request: Request) -> bytes:
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        raise ApiError(413, "LOTE_DEMASIADO_GRANDE", "El archivo supera el tamaño máximo permitido")

    if "multipart/form-data" in request.headers.get("content-type", "").lower():
        form = await request.form()
        upload = form.get("file")
        if upload is None or isinstance(upload, str):
            raise ApiError(400, "CSV_INVALIDO", "El formulario debe traer el archivo en el campo file")
        data = await upload.read()
    else:
        data = await request.body()

    if len(data) > MAX_BODY_BYTES:
        raise ApiError(413, "LOTE_DEMASIADO_GRANDE", "El archivo supera el tamaño máximo permitido")
    return data


# Ruta para enviar un lote.
# Recibe: el CSV (columna document), el encabezado Idempotency-Key, el token de la caja
#         y, si se quiere, purpose (por defecto VALIDACION_AFILIACION).
# Devuelve: 202 con el jobId. El trabajo queda corriendo en segundo plano.
# Si la caja repite la misma Idempotency-Key recibe el mismo jobId y no se procesa de nuevo.
@router.post("/api/v1/batch-checks", status_code=202, summary="Enviar un cruce por lote")
async def create_batch(request: Request, purpose: str | None = None, requester: str = Depends(require_caja)) -> JSONResponse:
    purpose = DEFAULT_PURPOSE if purpose is None else validate_purpose(purpose)
    key = (request.headers.get("idempotency-key") or "").strip()[:MAX_KEY_LENGTH] or None
    manager = request.app.state.batch

    job = manager.find_by_key(requester, key)
    if job is None:
        documents = parse_documents(await read_csv(request))
        job = manager.submit(requester, purpose, documents, key)
    return JSONResponse(status_code=202, content={"jobId": job.id, "status": job.status})


# Ruta para consultar un lote.
# Recibe: el jobId en la URL y el token de la caja que lo envió.
# Devuelve: status (PENDING, RUNNING o DONE), el avance y, al terminar, results con un
#           resultado por documento en el mismo orden del archivo.
# Lanza ApiError 404 si el lote no existe o pertenece a otra caja.
@router.get("/api/v1/batch-checks/{job_id}", summary="Estado y resultados de un lote")
async def read_batch(request: Request, job_id: str, requester: str = Depends(require_caja)) -> JSONResponse:
    job = request.app.state.batch.get(job_id, requester)
    if job is None:
        raise ApiError(404, "LOTE_NO_ENCONTRADO", "No existe un lote con ese jobId para esta caja")
    return JSONResponse(content=job.to_response())
