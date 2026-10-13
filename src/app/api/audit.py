# =============================================================================
# audit.py (API) — Ruta para leer la auditoría.
#
#   GET /api/v1/audit?limit=100     solo con el token de administrador
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# fastapi.APIRouter: agrupa rutas para registrarlas juntas en la aplicación.
# fastapi.Depends: exige el token de administrador antes de entrar a la función.
# fastapi.Request: da acceso al registro de auditoría guardado en la aplicación.
from fastapi import APIRouter, Depends, Request

from app.auth import require_admin

router = APIRouter(tags=["Auditoría"])

# Límites del parámetro limit.
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000


# Ruta de auditoría: últimas consultas respondidas, de la más nueva a la más vieja.
# Recibe: limit (cuántas entradas; entre 1 y 1000) y el token de administrador.
# Devuelve: una lista de entradas con timestamp, requestingCaja, purpose, result y
#           documentMasked (el documento nunca aparece completo).
@router.get("/api/v1/audit", summary="Auditoría de consultas (solo administrador)")
async def read_audit(request: Request, limit: int = DEFAULT_LIMIT, _: str = Depends(require_admin)) -> list:
    limit = max(1, min(limit, MAX_LIMIT))
    return request.app.state.audit.latest(limit)
