# =============================================================================
# test_privacy.py — Dato mínimo (Ley 1581) y secretos fuera del código.
# =============================================================================

import os
from pathlib import Path

from conftest import TOKEN_VARIABLES, auth

# Campos que el contrato prohíbe: nombre, dirección, teléfono, correo, salario y
# beneficiarios, con los nombres que usan las cajas (en español y en inglés).
CAMPOS_PROHIBIDOS = {
    "nombre", "nombres", "nombrecompleto", "name", "fullname", "firstname", "lastname", "apellidos",
    "direccion", "address", "telefono", "phone", "celular", "correo", "email", "mail",
    "salario", "salary", "monthlysalary", "ingresos", "beneficiarios", "beneficiaries", "person",
}

# Documentos que existen en las cajas y cuyas respuestas traen datos personales.
DOCUMENTOS = ["8873901472", "1315966777", "91336507", "3712776370"]

# Carpetas del repositorio montadas en solo lectura en el contenedor de pruebas.
CARPETAS_REVISADAS = [Path("/repo/src"), Path("/repo/config")]

# Variables del .env con secretos: tokens de las cajas y claves ante las cajas simuladas.
VARIABLES_SECRETAS = list(TOKEN_VARIABLES.values()) + ["CAJA_NORTE_API_KEY", "CAJA_ORIENTE_PASSWORD", "CAJA_SUR_TOKEN"]


# Recorre un JSON y devuelve todas sus claves en minúsculas y sin separadores.
def claves(valor) -> set:
    if isinstance(valor, dict):
        encontradas = {clave.lower().replace("_", "") for clave in valor}
        for hijo in valor.values():
            encontradas |= claves(hijo)
        return encontradas
    if isinstance(valor, list):
        return set().union(*(claves(hijo) for hijo in valor)) if valor else set()
    return set()


# Contrato: "Prohibido incluir: nombre, dirección, teléfono, correo, salario,
# beneficiarios". Se revisan v1 y v2 con documentos que sí tienen esos datos en las cajas.
def test_respuesta_no_contiene_datos_personales(client):
    for version in ("v1", "v2"):
        for documento in DOCUMENTOS:
            response = client.get("/api/{0}/affiliations/{1}?purpose=VALIDACION_AFILIACION".format(version, documento), headers=auth("ORIENTE"))
            assert response.status_code == 200
            prohibidas = claves(response.json()) & CAMPOS_PROHIBIDOS
            assert not prohibidas, "{0} {1} expone {2}".format(version, documento, prohibidas)


# Regla 6 del reto: ningún archivo puede tener escrito el valor de un token, clave o
# contraseña. Se busca cada valor del entorno en src/ y config/.
def test_secretos_no_estan_escritos_en_el_codigo():
    archivos = [ruta for carpeta in CARPETAS_REVISADAS for ruta in carpeta.rglob("*") if ruta.is_file() and "__pycache__" not in ruta.parts]
    assert any(ruta.suffix == ".py" for ruta in archivos), "No se encontró el código montado en /repo/src"

    secretos = {nombre: os.environ[nombre] for nombre in VARIABLES_SECRETAS if len(os.environ.get(nombre, "")) >= 6}
    assert secretos, "No hay secretos en el entorno para comparar"
    for ruta in archivos:
        contenido = ruta.read_text(encoding="utf-8", errors="ignore")
        for nombre, valor in secretos.items():
            assert valor not in contenido, "El valor de {0} está escrito en {1}".format(nombre, ruta)
