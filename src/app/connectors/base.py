# =============================================================================
# base.py — Lo que tienen en común todos los conectores.
#
# Un conector sabe hablar UN protocolo (REST JSON, SOAP o archivo plano) y
# traduce la respuesta de la caja al modelo común (Affiliation). Aquí vive la
# política de fallas: tiempo máximo, reintentos y la regla de oro del reto:
# si una caja no responde se informa como "no disponible", nunca como "no afiliado".
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# asyncio (estándar): permite esperar varias cajas a la vez y cortar la espera con un tope.
# datetime (estándar): convierte las fechas de cada caja al formato AAAA-MM-DD.
# urllib.parse.urlsplit (estándar): separa una URL en servidor y puerto.
import asyncio
from datetime import datetime
from urllib.parse import urlsplit

from app.config import CajaConfig
from app.domain.models import SOURCE_ONLINE, Affiliation

# Pausa base entre reintentos, en segundos (se multiplica por el número de intento).
RETRY_PAUSE_SECONDS = 0.1

# Pausa entre intentos de conexión mientras se espera a una caja al arrancar.
WARM_UP_PAUSE_SECONDS = 0.25


# Error que lanza un conector cuando la caja no pudo dar una respuesta confiable.
#   reason     explicación corta para el registro (sin datos personales)
#   retryable  True si vale la pena reintentar de inmediato (la caja falló rápido)
class CajaUnavailable(Exception):
    def __init__(self, reason: str, retryable: bool = False):
        super().__init__(reason)
        self.reason = reason
        self.retryable = retryable


# Clase base de los conectores. Cada protocolo hereda de ella y escribe su propio fetch().
class Connector:
    # Origen del dato que entrega este conector (los de archivo lo cambian a FILE).
    source = SOURCE_ONLINE

    # Guarda la configuración de la caja y el cliente HTTP compartido por todo el servicio.
    # Recibe: el CajaConfig de la caja y el cliente httpx (los conectores de archivo no lo usan).
    def __init__(self, caja: CajaConfig, http=None):
        self.caja = caja
        self.http = http

    # Pide a la caja TODAS las afiliaciones de un documento (vigentes e históricas).
    # Recibe: el documento normalizado (solo dígitos, sin ceros a la izquierda).
    # Devuelve: una lista de Affiliation; lista vacía si la persona no existe en la caja.
    # Lanza CajaUnavailable si la caja no respondió o respondió algo que no se entiende.
    # Cada conector concreto debe escribir este método.
    async def fetch(self, document: str) -> list:
        raise NotImplementedError

    # Consulta la caja aplicando la política de fallas de config/cajas.yaml.
    # Recibe: el documento normalizado.
    # Devuelve: la lista de Affiliation que entregó fetch().
    # - Si la caja falla rápido (503, conexión rechazada) reintenta hasta "retries" veces.
    # - Si no responde a tiempo NO reintenta: ya gastó el tiempo de esa consulta.
    # - En total nunca espera más de "deadline_seconds".
    # Lanza CajaUnavailable cuando se agotan los intentos o el tiempo.
    async def query(self, document: str) -> list:
        try:
            async with asyncio.timeout(self.caja.deadline_seconds):
                attempt = 0
                while True:
                    try:
                        return await self.fetch(document)
                    except CajaUnavailable as error:
                        if not error.retryable or attempt >= self.caja.retries:
                            raise
                        attempt += 1
                        await asyncio.sleep(RETRY_PAUSE_SECONDS * attempt)
        except TimeoutError:
            raise CajaUnavailable("superó el tiempo máximo de espera") from None

    # Dice a qué servidor y puerto se conecta este conector, para comprobarlo al arrancar.
    # No recibe nada. Devuelve: una tupla (servidor, puerto), o None si el conector no usa
    # la red (los de archivo) o la caja no tiene URL configurada.
    def endpoint(self) -> tuple | None:
        url = self.caja.request.get("base_url") or self.caja.request.get("url")
        if not url:
            return None
        parts = urlsplit(url)
        if not parts.hostname:
            return None
        return parts.hostname, parts.port or (443 if parts.scheme == "https" else 80)

    # Espera, al arrancar el servicio, a que la caja acepte conexiones.
    # Recibe: cuántos segundos esperar como máximo.
    # Devuelve: True si la caja quedó lista, False si se acabó el tiempo.
    # Evita que las primeras consultas después de un reinicio salgan INDETERMINADO solo
    # porque la caja todavía estaba encendiendo. Si la caja no aparece el servicio
    # arranca igual: en las consultas se informará como no disponible.
    async def warm_up(self, max_seconds: float) -> bool:
        target = self.endpoint()
        if target is None:
            return True
        loop = asyncio.get_running_loop()
        limit = loop.time() + max_seconds
        while True:
            try:
                _, writer = await asyncio.wait_for(asyncio.open_connection(*target), timeout=1.0)
                writer.close()
                return True
            except (OSError, TimeoutError):
                if loop.time() + WARM_UP_PAUSE_SECONDS >= limit:
                    return False
                await asyncio.sleep(WARM_UP_PAUSE_SECONDS)

    # Convierte una fecha de la caja al formato común AAAA-MM-DD.
    # Recibe: el texto de la fecha tal como lo entrega la caja (o None / vacío).
    # Devuelve: la fecha en AAAA-MM-DD, o None si la caja no informó fecha.
    # Lanza CajaUnavailable si la fecha no tiene el formato esperado: sin fechas
    # confiables no se puede afirmar si la afiliación está vigente.
    def to_iso_date(self, raw) -> str | None:
        text = str(raw).strip() if raw is not None else ""
        if not text:
            return None
        try:
            return datetime.strptime(text, self.caja.response.get("date_format", "%Y-%m-%d")).date().isoformat()
        except ValueError:
            raise CajaUnavailable("fecha con formato inesperado") from None

    # Traduce el tipo de afiliado de la caja al del contrato.
    # Recibe: el código propio de la caja ("D", "DEP", "DEPENDENT"...).
    # Devuelve: DEPENDIENTE, INDEPENDIENTE o PENSIONADO; None si la caja usa un código no declarado.
    def to_affiliate_type(self, raw) -> str | None:
        return self.caja.affiliate_types.get(str(raw or "").strip().upper())

    # Arma una Affiliation del modelo común con los datos crudos de la caja.
    # Recibe: fecha de inicio, fecha de fin y tipo de afiliado como los entrega la caja,
    #         y la fecha a la que corresponde la información (as_of).
    # Devuelve: la Affiliation lista para usar en el resto del servicio.
    def build_affiliation(self, valid_from, valid_to, affiliate_type, as_of: str) -> Affiliation:
        return Affiliation(
            caja=self.caja.id,
            valid_from=self.to_iso_date(valid_from),
            valid_to=self.to_iso_date(valid_to),
            affiliate_type=self.to_affiliate_type(affiliate_type),
            source=self.source,
            as_of=as_of,
        )
