# =============================================================================
# test_results.py — Resultados de la consulta en línea.
# =============================================================================

from conftest import auth

# Datos de prueba del reto.
AFILIADO_NORTE = "8873901472"   # afiliado en Caja Norte
AFILIADO_CENTRO = "1315966777"  # afiliado en Caja Centro (archivo plano)
INEXISTENTE = "999"             # no está en ninguna caja


# Consulta un documento con el token de una caja y devuelve el cuerpo JSON.
def consultar(client, documento: str, caja: str) -> dict:
    response = client.get("/api/v1/affiliations/" + documento + "?purpose=VALIDACION_AFILIACION", headers=auth(caja))
    assert response.status_code == 200
    return response.json()


# Contrato: "Se excluye la caja que consulta". Norte aparece cuando pregunta Oriente,
# pero no cuando pregunta la propia Norte.
def test_caja_consultante_no_aparece_en_matches(client):
    desde_oriente = consultar(client, AFILIADO_NORTE, "ORIENTE")
    assert "NORTE" in [match["caja"] for match in desde_oriente["matches"]]

    desde_norte = consultar(client, AFILIADO_NORTE, "NORTE")
    assert "NORTE" not in [match["caja"] for match in desde_norte["matches"]]
    assert "NORTE" not in desde_norte["unavailable"]


# Contrato de Caja Centro: las coincidencias del archivo plano se informan con
# source FILE y asOf igual a la FECHA_CORTE del archivo (2026-10-03).
def test_match_de_centro_trae_source_file_y_asof(client):
    body = consultar(client, AFILIADO_CENTRO, "NORTE")
    assert body["result"] == "AFILIADO_OTRA_CAJA"
    centro = [match for match in body["matches"] if match["caja"] == "CENTRO"]
    assert centro, "Se esperaba una coincidencia en CENTRO"
    assert centro[0]["source"] == "FILE"
    assert centro[0]["asOf"] == "2026-10-03"


# Contrato: NO_AFILIADO solo cuando todas las cajas respondieron y ninguna tiene
# afiliación vigente.
def test_documento_inexistente_responde_no_afiliado(client):
    body = consultar(client, INEXISTENTE, "ORIENTE")
    assert body["result"] == "NO_AFILIADO"
    assert body["matches"] == []
    assert body["unavailable"] == []
