# =============================================================================
# test_auth.py — Autenticación entre cajas y rol de administrador.
# =============================================================================

from conftest import auth

# Documento con afiliación en Caja Norte (datos de prueba del reto).
DOCUMENTO = "8873901472"
CONSULTA = "/api/v1/affiliations/" + DOCUMENTO + "?purpose=VALIDACION_AFILIACION"


# Contrato: "Sin token -> 401". Una caja sin token no puede consultar afiliaciones.
def test_consulta_sin_token_responde_401(client):
    response = client.get(CONSULTA)
    assert response.status_code == 401


# Contrato: cada caja se autentica con Authorization: Bearer <token>; un token que
# no pertenece a ninguna caja se rechaza igual que la ausencia de token.
def test_token_invalido_responde_401(client):
    response = client.get(CONSULTA, headers={"Authorization": "Bearer token-que-no-existe"})
    assert response.status_code == 401


# Contrato: la auditoría es "solo ADMIN_TOKEN"; una caja con token válido no la ve.
def test_auditoria_con_token_de_caja_responde_403(client):
    response = client.get("/api/v1/audit?limit=5", headers=auth("NORTE"))
    assert response.status_code == 403


# Contrato: GET /api/v1/audit con ADMIN_TOKEN entrega la lista de entradas.
def test_auditoria_con_admin_responde_200(client):
    response = client.get("/api/v1/audit?limit=5", headers=auth("ADMIN"))
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# Mínimo privilegio: el token de administrador sirve para auditar, no para
# consultar afiliaciones de personas.
def test_admin_no_puede_consultar_afiliaciones(client):
    response = client.get(CONSULTA, headers=auth("ADMIN"))
    assert response.status_code == 403
