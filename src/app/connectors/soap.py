# =============================================================================
# soap.py — Conector para cajas que exponen un servicio SOAP 1.1 (XML).
#
# Lo usa Caja Oriente. Arma el sobre SOAP con las credenciales en el encabezado,
# rellena el documento con ceros a la izquierda y lee la respuesta XML.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# httpx: cliente HTTP asíncrono; hace el POST con el sobre SOAP y tiempo máximo.
# defusedxml: lee XML de forma segura (bloquea entidades externas y "bombas" de XML).
# xml.etree.ElementTree.ParseError (estándar): error que aparece cuando el XML está mal formado.
# xml.sax.saxutils.escape (estándar): escapa &, < y > para que un valor no rompa el XML.
import httpx
from defusedxml import DefusedXmlException
from defusedxml import ElementTree as SafeElementTree
from xml.etree.ElementTree import ParseError
from xml.sax.saxutils import escape

from app.connectors.base import CajaUnavailable, Connector
from app.domain.models import today_bogota

# Sobre SOAP de la operación de consulta. Los valores entre llaves se llenan en cada petición.
ENVELOPE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="{namespace}">'
    "<soapenv:Header><ser:Credenciales>"
    "<ser:Usuario>{user}</ser:Usuario><ser:Clave>{password}</ser:Clave>"
    "</ser:Credenciales></soapenv:Header>"
    "<soapenv:Body><ser:ConsultarAfiliacionRequest>"
    "<ser:NumeroDocumento>{document}</ser:NumeroDocumento>"
    "</ser:ConsultarAfiliacionRequest></soapenv:Body>"
    "</soapenv:Envelope>"
)


class SoapConnector(Connector):
    # Arma el XML de la petición para un documento.
    # Recibe: el documento ya rellenado con ceros a la izquierda.
    # Devuelve: el sobre SOAP como bytes UTF-8, con usuario y clave escapados.
    def build_envelope(self, padded_document: str) -> bytes:
        request = self.caja.request
        return ENVELOPE.format(
            namespace=escape(request.get("namespace", "")),
            user=escape(request.get("user", "")),
            password=escape(request.get("password", "")),
            document=escape(padded_document),
        ).encode("utf-8")

    # Consulta las afiliaciones de un documento en la caja SOAP.
    # Recibe: el documento normalizado (sin ceros a la izquierda).
    # Devuelve: lista de Affiliation (vacía si la caja responde Encontrado = false).
    # Lanza CajaUnavailable ante tiempo agotado, error de conexión, SOAP Fault o XML ilegible.
    # Del XML solo se leen fechas y tipo de afiliado; nombre, teléfono y dirección se ignoran.
    async def fetch(self, document: str) -> list:
        request = self.caja.request
        url = request.get("url")
        if not url:
            raise CajaUnavailable("no tiene URL configurada")

        # La caja identifica a las personas con una cantidad fija de dígitos. Un documento
        # más largo no puede existir allí: se responde "sin afiliaciones" sin consultarla.
        digits = int(request.get("document_digits", 0))
        if digits and len(document) > digits:
            return []
        padded = document.zfill(digits)

        headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": request.get("soap_action", "")}
        try:
            response = await self.http.post(url, content=self.build_envelope(padded), headers=headers, timeout=self.caja.timeout_seconds)
        except httpx.TimeoutException:
            raise CajaUnavailable("no respondió a tiempo") from None
        except httpx.HTTPError:
            raise CajaUnavailable("no se pudo conectar", retryable=True) from None

        # 503 = caída momentánea (se reintenta). Cualquier otro código distinto de 200 es
        # un SOAP Fault (credenciales o formato): reintentar no lo arregla.
        if response.status_code == 503:
            raise CajaUnavailable("respondió HTTP 503", retryable=True)
        if response.status_code != 200:
            raise CajaUnavailable("respondió HTTP {0}".format(response.status_code))

        try:
            root = SafeElementTree.fromstring(response.content)
        except (ParseError, DefusedXmlException):
            raise CajaUnavailable("respondió un XML inválido") from None

        fields = self.caja.response
        prefix = "{" + request.get("namespace", "") + "}"
        found = (root.findtext(".//" + prefix + fields.get("found", "Encontrado")) or "").strip().lower()
        if found == "false":
            return []
        if found != "true":
            raise CajaUnavailable("respondió un XML sin el campo de resultado")

        as_of = today_bogota()
        return [
            self.build_affiliation(
                node.findtext(prefix + fields.get("valid_from", "")),
                node.findtext(prefix + fields.get("valid_to", "")),
                node.findtext(prefix + fields.get("affiliate_type", "")),
                as_of,
            )
            for node in root.iter(prefix + fields.get("affiliation", "Afiliacion"))
        ]
