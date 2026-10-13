# =============================================================================
# config.py — Lee config/cajas.yaml y las variables de entorno.
#
# Aquí se decide QUÉ cajas existen y CÓMO se consulta cada una. El resto del
# servicio no conoce direcciones ni credenciales: las recibe ya resueltas.
# Sumar una caja = agregar una entrada al YAML y sus variables en .env.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# logging (estándar): escribe avisos en la salida del contenedor (docker compose logs).
# os (estándar): lee las variables de entorno que docker compose carga desde .env.
# dataclasses (estándar): crea clases que solo guardan datos, sin escribir __init__ a mano.
# typing (estándar): anotaciones de tipos para que se entienda qué recibe cada función.
# yaml (PyYAML): convierte el texto de cajas.yaml en diccionarios y listas de Python.
import logging
import os
from dataclasses import dataclass
from typing import Any, Mapping

import yaml

logger = logging.getLogger(__name__)

# Ruta del catálogo dentro del contenedor (docker-compose.yml monta ./config ahí).
DEFAULT_CONFIG_PATH = "/app/config/cajas.yaml"

# Textos que se aceptan como "verdadero" en variables como CAJA_SUR_ENABLED.
TRUE_VALUES = {"1", "true", "yes", "si", "sí", "on"}

# Sufijo de las claves del YAML que guardan el nombre de una variable de entorno.
ENV_SUFFIX = "_env"


# Configuración ya resuelta de una caja: lo que necesita un conector para consultarla.
#   id               nombre de la caja en mayúsculas (NORTE, ORIENTE, CENTRO, SUR)
#   enabled          si se consulta como fuente de afiliaciones
#   consumer_token   token con el que esa caja se autentica ante Caja Link
#   connector        tipo de conector: rest-json, soap o flat-file
#   request          cómo preguntarle (URL, ruta, credenciales), con los valores ya leídos del entorno
#   response         nombres de los campos de su respuesta y formato de sus fechas
#   affiliate_types  traducción de sus tipos de afiliado a los del contrato
#   timeout_seconds, retries, deadline_seconds: política de fallas
@dataclass(frozen=True)
class CajaConfig:
    id: str
    enabled: bool
    consumer_token: str
    connector: str
    request: dict
    response: dict
    affiliate_types: dict
    timeout_seconds: float
    retries: int
    deadline_seconds: float


# Configuración completa del servicio: todas las cajas y el token del administrador.
@dataclass(frozen=True)
class Settings:
    cajas: tuple
    admin_token: str


# Interpreta un texto o booleano como verdadero/falso.
# Recibe: el valor leído del YAML o del entorno ("true", "false", True, None...).
# Devuelve: True solo si el valor está en TRUE_VALUES; cualquier otra cosa es False.
def read_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in TRUE_VALUES


# Reemplaza las claves "algo_env" por "algo" con el valor de esa variable de entorno.
# Ejemplo: {"base_url_env": "CAJA_NORTE_URL"} pasa a ser {"base_url": "<valor de la variable>"}.
# Recibe: una sección del YAML (puede tener diccionarios anidados) y el entorno.
# Devuelve: un diccionario nuevo; si la variable no existe, el valor queda vacío ("").
def resolve_env(section: Any, env: Mapping[str, str]) -> Any:
    if not isinstance(section, dict):
        return section
    resolved = {}
    for key, value in section.items():
        if key.endswith(ENV_SUFFIX) and isinstance(value, str):
            resolved[key[: -len(ENV_SUFFIX)]] = env.get(value, "").strip()
        else:
            resolved[key] = resolve_env(value, env)
    return resolved


# Construye la configuración de una caja a partir de su entrada en el YAML.
# Recibe: la entrada de la caja, los valores por defecto y el entorno.
# Devuelve: un CajaConfig listo para usar.
# Una caja se activa con "enabled: true" o con "enabled_env: NOMBRE_DE_VARIABLE"
# (así el validador enciende Caja Sur cambiando solo el .env).
def build_caja(entry: dict, defaults: dict, env: Mapping[str, str]) -> CajaConfig:
    if "enabled_env" in entry:
        enabled = read_bool(env.get(entry["enabled_env"]))
    else:
        enabled = read_bool(entry.get("enabled", True))
    return CajaConfig(
        id=str(entry["id"]).strip().upper(),
        enabled=enabled,
        consumer_token=env.get(entry.get("consumer_token_env", ""), "").strip(),
        connector=str(entry["connector"]).strip().lower(),
        request=resolve_env(entry.get("request") or {}, env),
        response=dict(entry.get("response") or {}),
        affiliate_types={str(k).upper(): str(v).upper() for k, v in (entry.get("affiliate_types") or {}).items()},
        timeout_seconds=float(entry.get("timeout_seconds", defaults.get("timeout_seconds", 2.5))),
        retries=int(entry.get("retries", defaults.get("retries", 2))),
        deadline_seconds=float(entry.get("deadline_seconds", defaults.get("deadline_seconds", 3.5))),
    )


# Lee el catálogo de cajas y lo combina con las variables de entorno.
# Recibe: la ruta del YAML (por defecto la variable CAJAS_CONFIG o /app/config/cajas.yaml)
#         y el entorno (por defecto el del proceso).
# Devuelve: un Settings con todas las cajas, activas o no.
# Si el archivo no existe o está mal formado el servicio no arranca: es preferible
# fallar al iniciar que responder consultas con una configuración incompleta.
def load_settings(path: str | None = None, env: Mapping[str, str] | None = None) -> Settings:
    env = os.environ if env is None else env
    path = path or env.get("CAJAS_CONFIG") or DEFAULT_CONFIG_PATH
    with open(path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}

    defaults = raw.get("defaults") or {}
    cajas = tuple(build_caja(entry, defaults, env) for entry in raw.get("cajas") or [])
    if not cajas:
        raise ValueError("El catálogo {0} no declara ninguna caja".format(path))
    repeated = {caja.id for caja in cajas if sum(1 for other in cajas if other.id == caja.id) > 1}
    if repeated:
        raise ValueError("Cajas repetidas en {0}: {1}".format(path, ", ".join(sorted(repeated))))

    for caja in cajas:
        if not caja.consumer_token:
            logger.warning("La caja %s no tiene token de consumidor: no podrá consultar", caja.id)
    admin_token = env.get(raw.get("admin_token_env", "ADMIN_TOKEN"), "").strip()
    if not admin_token:
        logger.warning("No hay token de administrador: la auditoría no se podrá consultar")

    logger.info("Cajas activas como fuente: %s", ", ".join(c.id for c in cajas if c.enabled))
    return Settings(cajas=cajas, admin_token=admin_token)
