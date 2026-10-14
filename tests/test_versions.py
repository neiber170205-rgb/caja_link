# =============================================================================
# test_versions.py — Contrato versionado: la v2 agrega affiliateType y la v1 no cambia.
# =============================================================================

from conftest import auth

# Documento con afiliación en Caja Norte, consultado por Caja Oriente.
DOCUMENTO = "8873901472"
TIPOS = {"DEPENDIENTE", "INDEPENDIENTE", "PENSIONADO"}


# Consulta el documento en una versión del contrato y devuelve sus matches.
def matches(client, version: str) -> list:
    response = client.get("/api/{0}/affiliations/{1}?purpose=VALIDACION_AFILIACION".format(version, DOCUMENTO), headers=auth("ORIENTE"))
    assert response.status_code == 200
    body = response.json()
    assert body["matches"], "Se esperaba al menos una coincidencia"
    return body["matches"]


# Contrato: "GET /api/v2/affiliations/{document} agrega affiliateType
# (DEPENDIENTE, INDEPENDIENTE, PENSIONADO)".
def test_v2_incluye_affiliate_type(client):
    for match in matches(client, "v2"):
        assert match["affiliateType"] in TIPOS


# Contrato: "La v1 no cambia": sus matches no traen affiliateType.
def test_v1_no_incluye_affiliate_type(client):
    for match in matches(client, "v1"):
        assert "affiliateType" not in match
