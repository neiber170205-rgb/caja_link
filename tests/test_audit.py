# =============================================================================
# test_audit.py — Auditoría: queda rastro de cada consulta sin exponer el documento.
# Cada prueba hace su propia consulta para no depender del orden de ejecución.
# =============================================================================

from conftest import auth

DOCUMENTO = "8873901472"
CAMPOS = ["timestamp", "requestingCaja", "purpose", "result", "documentMasked"]


# Hace una consulta con finalidad conocida y devuelve la entrada de auditoría más reciente.
def consultar_y_auditar(client) -> dict:
    consulta = client.get("/api/v1/affiliations/" + DOCUMENTO + "?purpose=TARIFA_SUBSIDIADA", headers=auth("CENTRO"))
    assert consulta.status_code == 200
    auditoria = client.get("/api/v1/audit?limit=100", headers=auth("ADMIN"))
    assert auditoria.status_code == 200
    propias = [entrada for entrada in auditoria.json() if entrada.get("requestingCaja") == "CENTRO" and entrada.get("purpose") == "TARIFA_SUBSIDIADA"]
    assert propias, "La consulta no quedó en la auditoría"
    return propias[0]


# Contrato: la auditoría trae timestamp, requestingCaja, purpose, result y documentMasked.
def test_auditoria_trae_los_campos_exigidos(client):
    entrada = consultar_y_auditar(client)
    for campo in CAMPOS:
        assert entrada.get(campo), "Falta el campo {0}".format(campo)
    assert entrada["requestingCaja"] == "CENTRO"
    assert entrada["result"] in {"AFILIADO_OTRA_CAJA", "NO_AFILIADO", "INDETERMINADO"}


# Ley 1581: la auditoría guarda el documento enmascarado, nunca completo.
def test_auditoria_enmascara_el_documento(client):
    enmascarado = consultar_y_auditar(client)["documentMasked"]
    assert DOCUMENTO not in enmascarado
    assert "*" in enmascarado
    assert enmascarado.endswith(DOCUMENTO[-4:])
