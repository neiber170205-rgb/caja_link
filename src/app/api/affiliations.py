# =============================================================================
# affiliations.py — Rutas de consulta en línea (v1 y v2).
#
#   GET /api/v1/affiliations/{document}?purpose=<finalidad>
#   GET /api/v2/affiliations/{document}?purpose=<finalidad>   (agrega affiliateType)
#
# Las dos versiones comparten toda la lógica; solo cambia cómo se escribe la
# respuesta. Así la v1 no cambia cuando evoluciona la v2.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# fastapi.APIRouter: agrupa rutas para registrarlas juntas en la aplicación.
# fastapi.Depends: ejecuta la autenticación antes de entrar a la función de la ruta.
# fastapi.Request: da acceso al estado de la aplicación (servicio y auditoría).
from fastapi import APIRouter, Depends, Request

from app.auth import require_caja
from app.domain.documents import normalize_document
from app.domain.models import PURPOSES, Affiliation, CheckResult, new_request_id
from app.errors import ApiError

router = APIRouter(tags=["Consulta en línea"])


# Valida la finalidad de la consulta (principio de finalidad, Ley 1581).
# Recibe: el parámetro purpose tal como llegó (o None si no vino).
# Devuelve: la finalidad validada.
# Lanza ApiError 400 si falta o no es una de las permitidas: sin finalidad no hay respuesta.
def validate_purpose(purpose: str | None) -> str:
    if not purpose:
        raise ApiError(400, "FINALIDAD_REQUERIDA", "El parámetro purpose es obligatorio: " + ", ".join(PURPOSES))
    if purpose not in PURPOSES:
        raise ApiError(400, "FINALIDAD_INVALIDA", "purpose debe ser uno de: " + ", ".join(PURPOSES))
    return purpose


# Valida y normaliza el documento de la ruta.
# Recibe: el documento como llegó en la URL (puede traer puntos, espacios o ceros).
# Devuelve: el documento normalizado.
# Lanza ApiError 400 si no es un número de documento válido.
def validate_document(raw: str) -> str:
    document = normalize_document(raw)
    if document is None:
        raise ApiError(400, "DOCUMENTO_INVALIDO", "El documento solo puede tener dígitos, puntos y espacios")
    return document


# Escribe una afiliación en el formato del contrato.
# Recibe: la Affiliation y si se debe incluir el tipo de afiliado (solo v2).
# Devuelve: el diccionario del match. Solo salen los campos permitidos (dato mínimo).
def serialize_match(affiliation: Affiliation, with_affiliate_type: bool) -> dict:
    match = {
        "caja": affiliation.caja,
        "validFrom": affiliation.valid_from,
        "validTo": affiliation.valid_to,
        "source": affiliation.source,
        "asOf": affiliation.as_of,
    }
    if with_affiliate_type:
        match["affiliateType"] = affiliation.affiliate_type
    return match


# Escribe la respuesta completa de una consulta en el formato del contrato.
# Recibe: el identificador de la consulta, el CheckResult y si es la versión 2.
# Devuelve: el diccionario que FastAPI convierte en JSON.
def serialize_check(request_id: str, check: CheckResult, with_affiliate_type: bool) -> dict:
    return {
        "requestId": request_id,
        "result": check.result,
        "matches": [serialize_match(affiliation, with_affiliate_type) for affiliation in check.matches],
        "unavailable": list(check.unavailable),
    }


# Lógica común de la consulta en línea para v1 y v2.
# Recibe: la petición, el documento de la URL, la finalidad, la caja que consulta
#         y si la respuesta lleva el tipo de afiliado.
# Devuelve: la respuesta del contrato.
# Pasos: validar finalidad -> normalizar documento -> consultar las cajas -> auditar -> responder.
async def run_check(request: Request, document: str, purpose: str | None, requester: str, with_affiliate_type: bool) -> dict:
    purpose = validate_purpose(purpose)
    normalized = validate_document(document)
    check = await request.app.state.service.check(normalized, requester)
    request_id = new_request_id()
    request.app.state.audit.record(request_id, requester, purpose, check.result, normalized)
    return serialize_check(request_id, check, with_affiliate_type)


# Ruta v1: ¿este documento tiene afiliación vigente en otra caja?
# Recibe: el documento en la URL, purpose en la consulta y el token de la caja.
# Devuelve: requestId, result, matches (caja, validFrom, validTo, source, asOf) y unavailable.
@router.get("/api/v1/affiliations/{document}", summary="Consulta de afiliación (v1)")
async def check_affiliation_v1(request: Request, document: str, purpose: str | None = None, requester: str = Depends(require_caja)) -> dict:
    return await run_check(request, document, purpose, requester, with_affiliate_type=False)


# Ruta v2: igual a la v1, y además cada match trae affiliateType
# (DEPENDIENTE, INDEPENDIENTE o PENSIONADO).
@router.get("/api/v2/affiliations/{document}", summary="Consulta de afiliación (v2, con tipo de afiliado)")
async def check_affiliation_v2(request: Request, document: str, purpose: str | None = None, requester: str = Depends(require_caja)) -> dict:
    return await run_check(request, document, purpose, requester, with_affiliate_type=True)
