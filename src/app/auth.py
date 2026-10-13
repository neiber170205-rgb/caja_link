# =============================================================================
# auth.py — Autenticación entre cajas.
#
# Cada caja consumidora tiene su propio token (NORTE_TOKEN, ORIENTE_TOKEN...).
# El token dice QUIÉN consulta: de ahí sale la caja que se excluye de la
# respuesta y la que queda en la auditoría. El administrador tiene un token
# aparte que solo sirve para leer la auditoría.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# hmac (estándar): compara tokens en tiempo constante, para que no se pueda adivinar
#                  un token midiendo cuánto tarda la respuesta.
# fastapi.Request: da acceso a los encabezados de la petición y al estado de la aplicación.
import hmac

from fastapi import Request

from app.config import Settings
from app.errors import ApiError
from dataclasses import dataclass

# Quién hace una petición, una vez validado su token.
#   caja      id de la caja (NORTE, ORIENTE...); None cuando es el administrador
#   is_admin  True solo cuando el token es el de administrador
# El rol va en un campo aparte y no en el nombre: así ninguna caja del catálogo
# puede hacerse pasar por administrador, se llame como se llame.
@dataclass(frozen=True)
class Identity:
    caja: str | None
    is_admin: bool = False



class Authenticator:
    # Arma la tabla de tokens válidos a partir de la configuración.
    # Recibe: el Settings del servicio.
    # Los tokens vacíos se ignoran: una caja sin token configurado no puede entrar.
    # Se aceptan los tokens de todas las cajas del catálogo, estén o no activas como fuente.
    def __init__(self, settings: Settings):
        self.tokens = [(caja.consumer_token.encode("utf-8"), Identity(caja=caja.id)) for caja in settings.cajas if caja.consumer_token]
        if settings.admin_token:
            self.tokens.append((settings.admin_token.encode("utf-8"), Identity(caja=None, is_admin=True)))


    # Averigua a quién pertenece el token de una petición.
    # Recibe: el valor del encabezado Authorization ("Bearer <token>") o None.
    # Devuelve: el id de la caja (NORTE, ORIENTE...), "ADMIN", o None si el token no es válido.
    # Se recorren todos los tokens aunque ya haya coincidido uno, para que el tiempo
    # de respuesta no revele cuál acertó.
    # Devuelve: la identidad (Identity) de quien consulta, o None si el token no es válido.
    def identify(self, header: str | None) -> Identity | None:
        if not header:
            return None
        scheme, _, token = header.strip().partition(" ")
        candidate = token.strip().encode("utf-8")
        if scheme.lower() != "bearer" or not candidate:
            return None
        identity = None
        for known, owner in self.tokens:
            if hmac.compare_digest(candidate, known) and identity is None:
                identity = owner
        return identity


# Identifica a quien hace la petición o la rechaza con 401.
# Recibe: la petición de FastAPI.
# Devuelve: el id de la caja o "ADMIN".
# Lanza ApiError 401 si no hay token o no corresponde a nadie.
def authenticate(request: Request) -> Identity:
    identity = request.app.state.authenticator.identify(request.headers.get("authorization"))
    if identity is None:
        raise ApiError(401, "NO_AUTENTICADO", "Falta el token o no es válido (Authorization: Bearer <token>)")
    return identity


# Dependencia de FastAPI para las rutas que solo pueden usar las cajas.
# Recibe: la petición. Devuelve: el id de la caja que consulta.
# Lanza 401 sin token válido y 403 si el token es el del administrador
# (el administrador audita, no consulta afiliaciones).
def require_caja(request: Request) -> str:
    identity = authenticate(request)
    if identity.is_admin:
        raise ApiError(403, "PROHIBIDO", "El token de administrador no puede consultar afiliaciones")
    return identity.caja

# Dependencia de FastAPI para las rutas que solo puede usar el administrador.
# Recibe: la petición. No devuelve nada útil (solo deja pasar).
# Lanza 401 sin token válido y 403 si el token es de una caja.
def require_admin(request: Request) -> str:
    identity = authenticate(request)
    if not identity.is_admin:
        raise ApiError(403, "PROHIBIDO", "La auditoría solo se consulta con el token de administrador")
    return identity
