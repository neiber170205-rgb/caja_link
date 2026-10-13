# =============================================================================
# flat_file.py — Conector para cajas que publican un archivo plano diario.
#
# Lo usa Caja Centro, que no tiene servicio en línea: cada noche deja un archivo
# con la información del día anterior. El conector carga en memoria el archivo
# más reciente y responde desde ahí, indicando source = FILE y la fecha de corte.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# fnmatch (estándar): compara nombres de archivo contra un patrón como "centro_afiliados_*.txt".
# logging (estándar): avisa en el registro cuando se carga un archivo nuevo.
# os (estándar): lista la carpeta donde la caja deja sus archivos.
import fnmatch
import logging
import os

from app.connectors.base import CajaUnavailable, Connector
from app.domain.documents import normalize_document
from app.domain.models import SOURCE_FILE

logger = logging.getLogger(__name__)


class FlatFileConnector(Connector):
    source = SOURCE_FILE

    # Prepara el conector con la memoria vacía; el archivo se carga en la primera consulta.
    # Recibe: el CajaConfig de la caja (el cliente HTTP no se usa).
    def __init__(self, caja, http=None):
        super().__init__(caja, http)
        self.loaded = None   # (ruta, fecha de modificación, tamaño) del archivo cargado
        self.index = {}      # documento normalizado -> lista de Affiliation

    # Busca el archivo más reciente de la carpeta de la caja.
    # No recibe nada (lee la carpeta y el patrón de la configuración).
    # Devuelve: una tupla (ruta, fecha de modificación, tamaño).
    # El nombre termina en AAAAMMDD, así que el mayor nombre es el archivo más nuevo.
    # Lanza CajaUnavailable si la carpeta no existe o no hay ningún archivo.
    def latest_file(self) -> tuple:
        folder = self.caja.request.get("dir")
        pattern = self.caja.request.get("pattern", "*.txt")
        try:
            names = [entry.name for entry in os.scandir(folder) if entry.is_file() and fnmatch.fnmatch(entry.name, pattern)]
        except (OSError, TypeError):
            raise CajaUnavailable("no se puede leer la carpeta del archivo") from None
        if not names:
            raise CajaUnavailable("no hay archivo publicado")
        path = os.path.join(folder, max(names))
        info = os.stat(path)
        return path, info.st_mtime, info.st_size

    # Lee un archivo completo y arma el índice en memoria.
    # Recibe: la ruta del archivo.
    # Devuelve: un diccionario documento -> lista de Affiliation.
    # Formato: línea 1 "FECHA_CORTE|AAAA-MM-DD", línea 2 los nombres de las columnas y
    # después una fila por afiliación. Las columnas se ubican por NOMBRE, no por posición,
    # y solo se leen documento, fechas y tipo: nombre y salario nunca se cargan.
    # Lanza CajaUnavailable si falta la fecha de corte o alguna columna obligatoria.
    def load(self, path: str) -> dict:
        fields = self.caja.response
        delimiter = self.caja.request.get("delimiter", "|")
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                lines = handle.read().splitlines()
        except OSError:
            raise CajaUnavailable("no se puede leer el archivo") from None
        if len(lines) < 2:
            raise CajaUnavailable("el archivo está incompleto")

        first = lines[0].split(delimiter)
        if len(first) < 2 or first[0].strip() != fields.get("cutoff", "FECHA_CORTE"):
            raise CajaUnavailable("el archivo no trae fecha de corte")
        as_of = first[1].strip()

        header = [name.strip() for name in lines[1].split(delimiter)]
        try:
            columns = {key: header.index(fields[key]) for key in ("document", "valid_from", "valid_to", "affiliate_type")}
        except (KeyError, ValueError):
            raise CajaUnavailable("el archivo no trae las columnas esperadas") from None

        index, skipped = {}, 0
        for line in lines[2:]:
            parts = line.split(delimiter)
            if len(parts) < len(header):
                skipped += bool(line.strip())
                continue
            document = normalize_document(parts[columns["document"]])
            if document is None:
                skipped += 1
                continue
            affiliation = self.build_affiliation(
                parts[columns["valid_from"]], parts[columns["valid_to"]], parts[columns["affiliate_type"]], as_of)
            index.setdefault(document, []).append(affiliation)
        logger.info("Caja %s: archivo %s cargado (%d documentos, %d filas omitidas, corte %s)",
                    self.caja.id, os.path.basename(path), len(index), skipped, as_of)
        return index

    # Carga el archivo al arrancar el servicio, para que la primera consulta ya sea rápida.
    # Recibe: el tiempo máximo de espera (no se usa: leer el archivo es inmediato).
    # Devuelve: True si el archivo quedó cargado, False si no hay archivo legible.
    async def warm_up(self, max_seconds: float) -> bool:
        try:
            await self.fetch("0")
            return True
        except CajaUnavailable:
            return False

    # Consulta las afiliaciones de un documento en el archivo más reciente.
    # Recibe: el documento normalizado.
    # Devuelve: lista de Affiliation con source = FILE y as_of = fecha de corte (vacía si no está).
    # Antes de responder revisa si la caja publicó un archivo más nuevo y lo recarga.
    # Lanza CajaUnavailable si no hay archivo legible: no se puede afirmar "no afiliado".
    async def fetch(self, document: str) -> list:
        current = self.latest_file()
        if current != self.loaded:
            self.index = self.load(current[0])
            self.loaded = current
        return list(self.index.get(document, []))
