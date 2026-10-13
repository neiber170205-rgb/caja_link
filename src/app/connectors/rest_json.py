# =============================================================================
# rest_json.py — Conector para cajas que exponen un servicio REST con JSON.
#
# Sirve para cualquier caja REST: la ruta, la forma de autenticarse y los nombres
# de los campos vienen de config/cajas.yaml. Por eso Caja Norte y Caja Sur usan
# este mismo código aunque sus respuestas sean distintas.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# httpx: cliente HTTP asíncrono; hace el GET a la caja con tiempo máximo.
import httpx

from app.connectors.base import CajaUnavailable, Connector
from app.domain.models import today_bogota


class RestJsonConnector(Connector):
    # Arma los encabezados de autenticación según el tipo declarado en la configuración.
    # No recibe nada (lee self.caja.request["auth"]).
    # Devuelve: un diccionario de encabezados.
    #   type: header -> un encabezado propio, por ejemplo X-Api-Key: <valor>
    #   type: bearer -> Authorization: Bearer <valor>
    def auth_headers(self) -> dict:
        auth = self.caja.request.get("auth") or {}
        value = auth.get("value", "")
        if auth.get("type") == "bearer":
            return {"Authorization": "Bearer " + value}
        if auth.get("type") == "header":
            return {auth.get("header", "X-Api-Key"): value}
        return {}

    # Decide si un 404 significa de verdad "esta persona no existe en la caja".
    # Recibe: la respuesta HTTP de la caja.
    # Devuelve: True solo si el cuerpo trae el código de error declarado en
    #           "not_found_error". Un 404 distinto (ruta mal configurada, por ejemplo)
    #           NO cuenta: tratarlo como "no existe" produciría un falso NO_AFILIADO.
    def is_person_not_found(self, response: httpx.Response) -> bool:
        expected = self.caja.response.get("not_found_error")
        if not expected:
            return True
        try:
            body = response.json()
        except ValueError:
            return False
        return isinstance(body, dict) and body.get("error") == expected

    # Consulta las afiliaciones de un documento en la caja REST.
    # Recibe: el documento normalizado.
    # Devuelve: lista de Affiliation (vacía si la caja confirma que la persona no existe).
    # Lanza CajaUnavailable ante tiempo agotado, error de conexión, 5xx o respuesta ilegible.
    # Solo se leen las fechas y el tipo de afiliado: los datos personales que la caja
    # envía (nombre, salario, correo...) se descartan aquí y no entran al servicio.
    async def fetch(self, document: str) -> list:
        request = self.caja.request
        base_url = request.get("base_url")
        if not base_url:
            raise CajaUnavailable("no tiene URL configurada")
        url = base_url.rstrip("/") + request.get("path", "").replace("{document}", document)

        try:
            response = await self.http.get(url, headers=self.auth_headers(), timeout=self.caja.timeout_seconds)
        except httpx.TimeoutException:
            raise CajaUnavailable("no respondió a tiempo") from None
        except httpx.HTTPError:
            raise CajaUnavailable("no se pudo conectar", retryable=True) from None

        if response.status_code == 404 and self.is_person_not_found(response):
            return []
        if response.status_code >= 500:
            raise CajaUnavailable("respondió HTTP {0}".format(response.status_code), retryable=True)
        if response.status_code != 200:
            raise CajaUnavailable("respondió HTTP {0}".format(response.status_code))

        try:
            body = response.json()
        except ValueError:
            raise CajaUnavailable("respondió un JSON inválido") from None
        fields = self.caja.response
        items = body.get(fields.get("affiliations", "")) if isinstance(body, dict) else None
        if not isinstance(items, list):
            raise CajaUnavailable("respondió sin lista de afiliaciones")

        as_of = today_bogota()
        return [
            self.build_affiliation(
                item.get(fields.get("valid_from")),
                item.get(fields.get("valid_to")),
                item.get(fields.get("affiliate_type")),
                as_of,
            )
            for item in items
            if isinstance(item, dict)
        ]
