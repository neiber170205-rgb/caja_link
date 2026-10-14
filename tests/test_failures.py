# =============================================================================
# test_failures.py — Tolerancia a fallas: una caja caída o lenta nunca produce
# un falso NO_AFILIADO. Cada prueba devuelve Caja Norte a "ok" al terminar.
# =============================================================================

import time

from conftest import auth

# Documento que no está en ninguna caja: con todas arriba sería NO_AFILIADO.
INEXISTENTE = "999"
CONSULTA = "/api/v1/affiliations/" + INEXISTENTE + "?purpose=VALIDACION_AFILIACION"

# Tope del contrato para responder aunque una caja esté lenta.
TOPE_SEGUNDOS = 5.0


# Contrato: "Si alguna caja no responde y no hay coincidencia en las demás ->
# INDETERMINADO, con la caja en unavailable". Nunca NO_AFILIADO.
def test_caja_caida_responde_indeterminado(client, norte_caos):
    with norte_caos("down"):
        response = client.get(CONSULTA, headers=auth("ORIENTE"))
    assert response.status_code == 200
    body = response.json()
    assert body["result"] == "INDETERMINADO"
    assert "NORTE" in body["unavailable"]


# Contrato: "Respuesta en menos de 5 segundos aunque una caja esté lenta".
# La caja lenta queda en unavailable en vez de hacer esperar la respuesta.
def test_caja_lenta_responde_en_menos_de_5_segundos(client, norte_caos):
    with norte_caos("slow"):
        inicio = time.monotonic()
        response = client.get(CONSULTA, headers=auth("ORIENTE"))
        duracion = time.monotonic() - inicio
    assert response.status_code == 200
    assert duracion < TOPE_SEGUNDOS, "Tardó {0:.1f} s".format(duracion)
    body = response.json()
    assert body["result"] == "INDETERMINADO"
    assert "NORTE" in body["unavailable"]
