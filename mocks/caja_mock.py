"""Cajas simuladas para Caja Link (solo biblioteca estándar).

CAJA=norte   REST JSON  GET  /api/v1/afiliados/{documento}        X-Api-Key
CAJA=oriente SOAP/XML   POST /ws/AfiliacionService                credenciales en el Header SOAP
CAJA=sur     REST JSON  GET  /v2/people/{documento}/memberships   Authorization: Bearer

Todas exponen POST /__chaos {"mode": "ok" | "down" | "slow"} para provocar fallas.
"""

import json
import os
import random
import re
import threading
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KIND = os.environ.get("CAJA", "norte").lower()
PORT = int(os.environ.get("PORT", "8080"))
SLOW_SECONDS = float(os.environ.get("SLOW_SECONDS", "8"))
FLAKY_RATE = float(os.environ.get("FLAKY_RATE", "0"))
NORTE_KEY = os.environ.get("CAJA_NORTE_API_KEY", "norte-key")
ORIENTE_USER = os.environ.get("CAJA_ORIENTE_USER", "caja-link")
ORIENTE_PASSWORD = os.environ.get("CAJA_ORIENTE_PASSWORD", "oriente-pass")
SUR_TOKEN = os.environ.get("CAJA_SUR_TOKEN", "sur-token")

with open(os.path.join(os.environ.get("DATA_DIR", "/data"), KIND + ".json"), encoding="utf-8") as handle:
    DATA = json.load(handle)

STATE = {"mode": "ok"}
LOCK = threading.Lock()
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
ORI_NS = "http://cajaoriente.example/afiliacion"

WSDL = """<?xml version="1.0" encoding="UTF-8"?>
<definitions xmlns="http://schemas.xmlsoap.org/wsdl/" xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
             xmlns:tns="{ns}" targetNamespace="{ns}" name="AfiliacionService">
  <message name="ConsultarAfiliacionRequest"><part name="NumeroDocumento" type="xsd:string"/></message>
  <message name="ConsultarAfiliacionResponse"><part name="Persona" type="tns:Persona"/></message>
  <portType name="AfiliacionPort">
    <operation name="ConsultarAfiliacion">
      <input message="tns:ConsultarAfiliacionRequest"/><output message="tns:ConsultarAfiliacionResponse"/>
    </operation>
  </portType>
  <binding name="AfiliacionBinding" type="tns:AfiliacionPort">
    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>
    <operation name="ConsultarAfiliacion"><soap:operation soapAction="ConsultarAfiliacion"/></operation>
  </binding>
  <service name="AfiliacionService">
    <port name="AfiliacionPort" binding="tns:AfiliacionBinding"><soap:address location="http://localhost:9002/ws/AfiliacionService"/></port>
  </service>
</definitions>
""".format(ns=ORI_NS)


def soap_envelope(body_xml):
    return '<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:soapenv="{0}" xmlns:ori="{1}"><soapenv:Body>{2}</soapenv:Body></soapenv:Envelope>'.format(SOAP_NS, ORI_NS, body_xml)


def soap_fault(code, message):
    return soap_envelope("<soapenv:Fault><faultcode>{0}</faultcode><faultstring>{1}</faultstring></soapenv:Fault>".format(code, message))


def esc(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        payload = body if isinstance(body, bytes) else (body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _body(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        return self.rfile.read(length) if length else b""

    def _chaos_gate(self):
        """Returns True when the request was already answered by a chaos mode."""
        mode = STATE["mode"]
        if mode == "down" or (FLAKY_RATE and random.random() < FLAKY_RATE):
            self._send(503, {"error": "SERVICIO_NO_DISPONIBLE", "caja": KIND.upper()})
            return True
        if mode == "slow":
            time.sleep(SLOW_SECONDS)
        return False

    def _chaos(self):
        if self.command == "GET":
            return self._send(200, {"caja": KIND.upper(), "mode": STATE["mode"]})
        try:
            mode = json.loads(self._body() or b"{}").get("mode")
        except ValueError:
            mode = None
        if mode not in ("ok", "down", "slow"):
            return self._send(400, {"error": "mode debe ser ok, down o slow"})
        with LOCK:
            STATE["mode"] = mode
        return self._send(200, {"caja": KIND.upper(), "mode": mode})

    def do_GET(self):
        if self.path == "/__chaos":
            return self._chaos()
        if self._chaos_gate():
            return None
        if self.path == "/health":
            return self._send(200, {"status": "UP", "caja": KIND.upper()})
        if KIND == "norte":
            return self._norte()
        if KIND == "sur":
            return self._sur()
        if KIND == "oriente" and self.path.split("?")[0] == "/ws/AfiliacionService" and "wsdl" in self.path.lower():
            return self._send(200, WSDL, "text/xml; charset=utf-8")
        return self._send(404, {"error": "RUTA_NO_ENCONTRADA"})

    def do_POST(self):
        if self.path == "/__chaos":
            return self._chaos()
        if self._chaos_gate():
            return None
        if KIND == "oriente" and self.path == "/ws/AfiliacionService":
            return self._oriente()
        return self._send(404, {"error": "RUTA_NO_ENCONTRADA"})

    def _norte(self):
        match = re.match(r"^/api/v1/afiliados/([^/?]+)$", self.path)
        if not match:
            return self._send(404, {"error": "RUTA_NO_ENCONTRADA"})
        if self.headers.get("X-Api-Key") != NORTE_KEY:
            return self._send(401, {"error": "API_KEY_INVALIDA"})
        documento = match.group(1)
        if not documento.isdigit():
            return self._send(400, {"error": "DOCUMENTO_INVALIDO", "detalle": "solo dígitos, sin puntos ni espacios"})
        record = DATA.get(documento)
        if record is None:
            return self._send(404, {"error": "NO_ENCONTRADO", "documento": documento})
        return self._send(200, dict({"documento": documento}, **record))

    def _sur(self):
        match = re.match(r"^/v2/people/([0-9]+)/memberships$", self.path)
        if not match:
            return self._send(404, {"error": "not_found"})
        if self.headers.get("Authorization") != "Bearer " + SUR_TOKEN:
            return self._send(401, {"error": "unauthorized"})
        record = DATA.get(match.group(1))
        if record is None:
            return self._send(404, {"error": "person_not_found"})
        return self._send(200, record)

    def _oriente(self):
        try:
            root = ET.fromstring(self._body())
        except ET.ParseError:
            return self._send(500, soap_fault("soapenv:Client", "XML mal formado"), "text/xml; charset=utf-8")
        user = root.findtext(".//{%s}Usuario" % ORI_NS)
        password = root.findtext(".//{%s}Clave" % ORI_NS)
        if user != ORIENTE_USER or password != ORIENTE_PASSWORD:
            return self._send(500, soap_fault("soapenv:Client.Autenticacion", "Credenciales inválidas"), "text/xml; charset=utf-8")
        raw = root.findtext(".//{%s}NumeroDocumento" % ORI_NS) or ""
        documento = raw.replace(".", "").replace(" ", "").strip()
        if not re.match(r"^[0-9]{12}$", documento):
            return self._send(500, soap_fault("soapenv:Client.Formato", "Formato de documento inválido: se esperan 12 dígitos con ceros a la izquierda"), "text/xml; charset=utf-8")
        record = DATA.get(documento)
        shown = "{0}.{1}.{2}.{3}".format(documento[:3], documento[3:6], documento[6:9], documento[9:])
        if record is None:
            body = "<ori:ConsultarAfiliacionResponse><ori:Encontrado>false</ori:Encontrado><ori:NumeroDocumento>{0}</ori:NumeroDocumento></ori:ConsultarAfiliacionResponse>".format(shown)
            return self._send(200, soap_envelope(body), "text/xml; charset=utf-8")
        afiliaciones = "".join(
            "<ori:Afiliacion><ori:FechaIngreso>{0}</ori:FechaIngreso><ori:FechaRetiro>{1}</ori:FechaRetiro><ori:TipoAfiliado>{2}</ori:TipoAfiliado></ori:Afiliacion>".format(
                a["fechaIngreso"], a["fechaRetiro"], a["tipoAfiliado"]
            )
            for a in record["afiliaciones"]
        )
        body = (
            "<ori:ConsultarAfiliacionResponse><ori:Encontrado>true</ori:Encontrado><ori:Persona>"
            "<ori:NumeroDocumento>{0}</ori:NumeroDocumento><ori:NombreCompleto>{1}</ori:NombreCompleto>"
            "<ori:Telefono>{2}</ori:Telefono><ori:Direccion>{3}</ori:Direccion>"
            "<ori:Afiliaciones>{4}</ori:Afiliaciones></ori:Persona></ori:ConsultarAfiliacionResponse>"
        ).format(shown, esc(record["nombreCompleto"]), esc(record["telefono"]), esc(record["direccion"]), afiliaciones)
        return self._send(200, soap_envelope(body), "text/xml; charset=utf-8")

    def log_message(self, fmt, *args):
        return


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 256


if __name__ == "__main__":
    print("Caja {0} escuchando en {1} ({2} documentos)".format(KIND.upper(), PORT, len(DATA)), flush=True)
    Server(("0.0.0.0", PORT), Handler).serve_forever()
