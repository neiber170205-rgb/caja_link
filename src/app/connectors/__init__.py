# =============================================================================
# connectors — Fábrica de conectores.
#
# Relaciona el campo "connector" de config/cajas.yaml con la clase que sabe
# hablar ese protocolo. Para soportar un protocolo nuevo se escribe su clase y
# se agrega una línea a CONNECTOR_TYPES; para sumar una caja que usa un protocolo
# ya soportado no se toca el código.
# =============================================================================

from app.config import Settings
from app.connectors.base import CajaUnavailable, Connector
from app.connectors.flat_file import FlatFileConnector
from app.connectors.rest_json import RestJsonConnector
from app.connectors.soap import SoapConnector

# Tipo de conector declarado en el YAML -> clase que lo implementa.
CONNECTOR_TYPES = {
    "rest-json": RestJsonConnector,
    "soap": SoapConnector,
    "flat-file": FlatFileConnector,
}


# Crea un conector por cada caja activa del catálogo.
# Recibe: la configuración del servicio y el cliente HTTP compartido.
# Devuelve: un diccionario id de la caja -> conector, en el orden del YAML.
# Lanza ValueError si una caja activa pide un tipo de conector que no existe
# (error de configuración: el servicio no debe arrancar a medias).
def build_connectors(settings: Settings, http) -> dict:
    connectors = {}
    for caja in settings.cajas:
        if not caja.enabled:
            continue
        connector_class = CONNECTOR_TYPES.get(caja.connector)
        if connector_class is None:
            raise ValueError("La caja {0} usa un conector desconocido: {1}".format(caja.id, caja.connector))
        connectors[caja.id] = connector_class(caja, http)
    return connectors
