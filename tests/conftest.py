# =============================================================================
# conftest.py — Lo que comparten todas las pruebas de Caja Link.
#
# pytest carga este archivo antes que cualquier test_*.py. Aquí viven:
#   - las direcciones del servicio y de Caja Norte (de variables de entorno);
#   - los tokens de cada caja y del administrador (de variables de entorno);
#   - una función para cambiar el modo de una caja con /__chaos que siempre
#     la devuelve a "ok", aunque la prueba falle.
# Ningún token ni dirección queda escrito aquí: docker compose los pasa desde .env.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# os (estándar): lee las variables de entorno.
# contextlib.contextmanager (estándar): permite usar "with caos(...)" en las pruebas.
# httpx: cliente HTTP con el que las pruebas llaman al servicio y a las cajas.
# pytest: marco de pruebas; aquí define los fixtures que reciben las pruebas.
import os
from contextlib import contextmanager

import httpx
import pytest

# Dirección del servicio Caja Link (docker-compose.yml la pone en CAJA_LINK_URL).
CAJA_LINK_URL = os.environ.get("CAJA_LINK_URL", "http://localhost:8083").rstrip("/")

# Dirección de Caja Norte; es la misma que usa el servicio y viene del .env.
CAJA_NORTE_URL = os.environ.get("CAJA_NORTE_URL", "http://localhost:9001").rstrip("/")

# Tiempo máximo de cada petición de prueba. Mayor que los 5 s del contrato para
# que una respuesta lenta se mida en la prueba y no corte la petición antes.
TIMEOUT_SECONDS = 15.0

# Cajas consumidoras y administrador: nombre -> variable de entorno con su token.
TOKEN_VARIABLES = {
    "NORTE": "NORTE_TOKEN",
    "ORIENTE": "ORIENTE_TOKEN",
    "CENTRO": "CENTRO_TOKEN",
    "SUR": "SUR_TOKEN",
    "ADMIN": "ADMIN_TOKEN",
}


# Lee el token de una caja o del administrador.
# Recibe: el nombre (NORTE, ORIENTE, CENTRO, SUR o ADMIN).
# Devuelve: el valor de la variable de entorno; si no está, la prueba se salta
#           con un mensaje claro en vez de fallar por una configuración incompleta.
def token(name: str) -> str:
    value = os.environ.get(TOKEN_VARIABLES[name], "").strip()
    if not value:
        pytest.skip("Falta la variable {0} en el entorno".format(TOKEN_VARIABLES[name]))
    return value


# Arma el encabezado de autenticación de una caja.
# Recibe: el nombre de la caja o ADMIN. Devuelve: {"Authorization": "Bearer <token>"}.
def auth(name: str) -> dict:
    return {"Authorization": "Bearer " + token(name)}


# Cambia el modo de una caja simulada con POST /__chaos.
# Recibe: la dirección de la caja y el modo ("ok", "down" o "slow").
# Lanza AssertionError si la caja no acepta el cambio.
def set_mode(caja_url: str, mode: str) -> None:
    response = httpx.post(caja_url + "/__chaos", json={"mode": mode}, timeout=TIMEOUT_SECONDS)
    assert response.status_code == 200, "La caja no aceptó el modo {0}: HTTP {1}".format(mode, response.status_code)


# Pone una caja en un modo mientras dura el bloque "with" y SIEMPRE la devuelve a "ok"
# al salir, aunque la prueba falle; así una prueba no deja la caja caída para las demás.
# Uso: with caos(CAJA_NORTE_URL, "down"): ...
@contextmanager
def caos(caja_url: str, mode: str):
    set_mode(caja_url, mode)
    try:
        yield
    finally:
        set_mode(caja_url, "ok")


# Cliente HTTP apuntando al servicio, compartido por todas las pruebas de la sesión.
@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url=CAJA_LINK_URL, timeout=TIMEOUT_SECONDS) as http:
        yield http


# Fixture con la función caos lista para usar en las pruebas que tumban Caja Norte.
# Uso: def test_algo(client, norte_caos): with norte_caos("down"): ...
@pytest.fixture
def norte_caos():
    return lambda mode: caos(CAJA_NORTE_URL, mode)
