# =============================================================================
# test_purpose.py — Finalidad obligatoria (Ley 1581: principio de finalidad).
# =============================================================================

from conftest import auth

RUTA = "/api/v1/affiliations/8873901472"


# Contrato: "Sin finalidad -> 400". Nadie consulta sin declarar para qué usará el dato.
def test_consulta_sin_purpose_responde_400(client):
    response = client.get(RUTA, headers=auth("ORIENTE"))
    assert response.status_code == 400


# Contrato: purpose ∈ TARIFA_SUBSIDIADA, SUBSIDIO_MONETARIO, VALIDACION_AFILIACION;
# cualquier otra finalidad -> 400.
def test_purpose_invalido_responde_400(client):
    response = client.get(RUTA + "?purpose=MERCADEO", headers=auth("ORIENTE"))
    assert response.status_code == 400
