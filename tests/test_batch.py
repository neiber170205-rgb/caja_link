# =============================================================================
# test_batch.py — Cruce por lote: envío, idempotencia, estado y resultados.
#
# Cada prueba usa un lote pequeño (4 documentos de los datos del reto) para que
# la suite siga siendo rápida, y una Idempotency-Key nueva en cada ejecución
# para no recibir un lote viejo de una corrida anterior.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# time (estándar): mide el tope de espera mientras el lote termina.
# uuid (estándar): genera una Idempotency-Key distinta en cada ejecución.
import time
import uuid

from conftest import auth

# Ruta del lote.
LOTE = "/api/v1/batch-checks"

# Datos de prueba del reto.
AFILIADO_NORTE = "8873901472"   # afiliado en Caja Norte
AFILIADO_CENTRO = "1315966777"  # afiliado en Caja Centro (archivo plano)
INEXISTENTE = "999"             # no está en ninguna caja
CON_FORMATO = "88.739.01472"    # el afiliado de Norte escrito con puntos

DOCUMENTOS = [AFILIADO_NORTE, AFILIADO_CENTRO, INEXISTENTE, CON_FORMATO]

# Caja que envía los lotes de estas pruebas (Norte no se excluye a sí misma así).
CAJA = "ORIENTE"

# Segundos máximos que una prueba espera el estado DONE antes de fallar.
TOPE_ESPERA_SEGUNDOS = 60.0


# Arma el CSV del lote con la columna document.
# Recibe: la lista de documentos. Devuelve: el archivo en bytes.
def csv_de(documentos: list) -> bytes:
    return ("document\n" + "\n".join(documentos) + "\n").encode("utf-8")


# Envía un lote con el token de una caja.
# Recibe: el cliente, la Idempotency-Key, la caja y los documentos.
# Devuelve: la respuesta HTTP tal cual, para que cada prueba revise lo que necesita.
def enviar_lote(client, llave: str, caja: str = CAJA, documentos: list = DOCUMENTOS):
    headers = dict(auth(caja), **{"Idempotency-Key": llave, "Content-Type": "text/csv"})
    return client.post(LOTE, content=csv_de(documentos), headers=headers)


# Pregunta por el lote hasta que esté DONE, con un tope de tiempo para que una
# falla no deje la prueba colgada.
# Recibe: el cliente, el jobId y la caja que lo envió. Devuelve: el cuerpo JSON final.
def esperar_done(client, job_id: str, caja: str = CAJA) -> dict:
    limite = time.monotonic() + TOPE_ESPERA_SEGUNDOS
    while True:
        response = client.get(LOTE + "/" + job_id, headers=auth(caja))
        assert response.status_code == 200
        body = response.json()
        if body["status"] == "DONE":
            return body
        assert time.monotonic() < limite, "El lote no terminó en {0} s (estado {1})".format(TOPE_ESPERA_SEGUNDOS, body["status"])
        time.sleep(0.5)


# Llave de idempotencia nueva para cada ejecución.
def llave_nueva() -> str:
    return "prueba-lote-" + uuid.uuid4().hex


# Contrato: POST /api/v1/batch-checks responde 202 con el jobId.
def test_lote_responde_202_con_job_id(client):
    response = enviar_lote(client, llave_nueva())
    assert response.status_code == 202
    assert response.json()["jobId"]


# Contrato: "Repetir con la misma llave devuelve el mismo jobId".
def test_misma_llave_devuelve_el_mismo_job_id(client):
    llave = llave_nueva()
    primero = enviar_lote(client, llave)
    segundo = enviar_lote(client, llave)
    assert primero.status_code == 202
    assert segundo.status_code == 202
    assert primero.json()["jobId"] == segundo.json()["jobId"]


# Contrato: el lote termina en DONE con un resultado por documento, en el orden del archivo.
def test_lote_termina_en_done_con_un_resultado_por_documento(client):
    job_id = enviar_lote(client, llave_nueva()).json()["jobId"]
    body = esperar_done(client, job_id)
    assert len(body["results"]) == len(DOCUMENTOS)
    assert [entrada["documentInput"] for entrada in body["results"]] == DOCUMENTOS


# El lote usa el mismo servicio que la consulta en línea: para cada documento el
# resultado y las cajas que coinciden deben ser los mismos.
def test_lote_coincide_con_la_consulta_en_linea(client):
    job_id = enviar_lote(client, llave_nueva()).json()["jobId"]
    resultados = esperar_done(client, job_id)["results"]

    for documento, entrada in zip(DOCUMENTOS, resultados):
        response = client.get("/api/v1/affiliations/" + documento + "?purpose=VALIDACION_AFILIACION", headers=auth(CAJA))
        assert response.status_code == 200
        en_linea = response.json()
        assert entrada["result"] == en_linea["result"], documento
        assert sorted(m["caja"] for m in entrada["matches"]) == sorted(m["caja"] for m in en_linea["matches"]), documento


# Contrato: "Sin token -> 401", también en el lote.
def test_lote_sin_token_responde_401(client):
    response = client.post(LOTE, content=csv_de(DOCUMENTOS), headers={"Idempotency-Key": llave_nueva(), "Content-Type": "text/csv"})
    assert response.status_code == 401


# Un jobId que no existe responde 404 (LOTE_NO_ENCONTRADO), no un lote vacío.
def test_lote_inexistente_responde_404(client):
    response = client.get(LOTE + "/no-existe-" + uuid.uuid4().hex, headers=auth(CAJA))
    assert response.status_code == 404
