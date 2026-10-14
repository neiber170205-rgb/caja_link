# =============================================================================
# test_documents.py — Normalización del documento (puntos, espacios y ceros).
# =============================================================================

from urllib.parse import quote

from conftest import auth

# Documento con afiliación en Caja Norte, consultado por Caja Oriente.
DOCUMENTO = "8873901472"


# Consulta un documento escrito de cualquier forma y devuelve la respuesta.
def consultar(client, documento: str):
    ruta = "/api/v1/affiliations/" + quote(documento, safe="") + "?purpose=VALIDACION_AFILIACION"
    return client.get(ruta, headers=auth("ORIENTE"))


# Resume una respuesta en lo que debe ser igual sin importar cómo se escribió el
# documento: el resultado y las cajas donde aparece.
def resumen(response) -> tuple:
    body = response.json()
    return body["result"], sorted(match["caja"] for match in body["matches"])


# Contrato: "El documento se normaliza (puntos ...)". 8.873.901.472 es la misma persona.
def test_documento_con_puntos_da_el_mismo_resultado(client):
    esperado = resumen(consultar(client, DOCUMENTO))
    response = consultar(client, "8.873.901.472")
    assert response.status_code == 200
    assert resumen(response) == esperado


# Contrato: "El documento se normaliza (... ceros a la izquierda)", como los envía Caja Oriente.
def test_documento_con_ceros_da_el_mismo_resultado(client):
    esperado = resumen(consultar(client, DOCUMENTO))
    response = consultar(client, "00" + DOCUMENTO)
    assert response.status_code == 200
    assert resumen(response) == esperado


# Contrato: "El documento se normaliza (... espacios ...)".
def test_documento_con_espacios_da_el_mismo_resultado(client):
    esperado = resumen(consultar(client, DOCUMENTO))
    response = consultar(client, "8873 901 472")
    assert response.status_code == 200
    assert resumen(response) == esperado


# Un documento con letras no es un número de documento: se rechaza con 400 en vez
# de responder NO_AFILIADO sobre algo que no se pudo consultar.
def test_documento_con_letras_responde_400(client):
    response = consultar(client, "88739O1472")
    assert response.status_code == 400
