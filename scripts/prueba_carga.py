# =============================================================================
# prueba_carga.py — Prueba de carga del cruce por lote.
#
# Envía data/lote_10000.csv al servicio, espera a que el lote termine y reporta
# cuánto tardó, cuántos resultados llegaron y cuántos errores hubo.
#
# Uso:  python3 scripts/prueba_carga.py [CAJA]
#       CAJA es la caja que consulta: NORTE (por defecto), ORIENTE, CENTRO o SUR.
# Solo usa la biblioteca estándar de Python: no hay que instalar nada.
# =============================================================================

# --- Librerías (todas estándar) ----------------------------------------------
# json: interpreta las respuestas del servicio.
# sys: lee el argumento de la línea de comandos.
# time: mide la duración.
# urllib.request: hace las peticiones HTTP.
# uuid: genera una Idempotency-Key distinta en cada ejecución.
# pathlib: ubica los archivos del repositorio sin importar desde dónde se ejecute.
import json
import sys
import time
import urllib.request
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BATCH_URL = "http://localhost:8083/api/v1/batch-checks"

# Cada cuánto se pregunta por el estado y cuánto se espera como máximo (el contrato da 5 minutos).
POLL_SECONDS = 1
MAX_SECONDS = 300

# Resultados que el contrato permite para un documento.
VALID_RESULTS = ("AFILIADO_OTRA_CAJA", "NO_AFILIADO", "INDETERMINADO")


# Lee una variable de .env (o de .env.example si no existe), como hace el validador.
# Recibe: el nombre de la variable. Devuelve: su valor. Termina el programa si no la encuentra.
def read_env(name: str) -> str:
    for filename in (".env", ".env.example"):
        path = REPO / filename
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip()
    raise SystemExit("No se encontró {0} en .env".format(name))


# Hace una petición al servicio con el token de la caja.
# Recibe: método, dirección, token, cuerpo (bytes o None) y encabezados adicionales.
# Devuelve: la respuesta JSON convertida en diccionario.
def call(method: str, url: str, token: str, data=None, headers=None) -> dict:
    all_headers = dict(headers or {}, Authorization="Bearer " + token)
    request = urllib.request.Request(url, data=data, method=method, headers=all_headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())


# Ejecuta la prueba completa e imprime el reporte.
# No recibe nada (lee la caja de la línea de comandos). Devuelve: 0 si no hubo errores, 1 si los hubo.
def main() -> int:
    caja = (sys.argv[1] if len(sys.argv) > 1 else "NORTE").upper()
    token = read_env(caja + "_TOKEN")
    payload = (REPO / "data" / "lote_10000.csv").read_bytes()
    documents = len([line for line in payload.decode("utf-8").splitlines()[1:] if line.strip()])

    started = time.time()
    headers = {"Idempotency-Key": "carga-" + uuid.uuid4().hex, "Content-Type": "text/csv"}
    job = call("POST", BATCH_URL, token, payload, headers)["jobId"]
    while True:
        body = call("GET", BATCH_URL + "/" + job, token)
        if body["status"] == "DONE":
            break
        if time.time() - started > MAX_SECONDS:
            print("El lote no terminó en {0} segundos".format(MAX_SECONDS))
            return 1
        time.sleep(POLL_SECONDS)
    seconds = time.time() - started

    counts = {}
    for item in body["results"]:
        counts[item["result"]] = counts.get(item["result"], 0) + 1
    missing = documents - len(body["results"])
    invalid = sum(count for result, count in counts.items() if result not in VALID_RESULTS)
    errors = missing + invalid

    print("herramienta: script en Python (scripts/prueba_carga.py)")
    print("documentos: {0}".format(documents))
    print("duracion_segundos: {0:.0f}".format(seconds))
    print("errores: {0}".format(errors))
    print()
    print("caja que consulta: {0}".format(caja))
    for result, count in sorted(counts.items()):
        print("  {0}: {1}".format(result, count))
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
