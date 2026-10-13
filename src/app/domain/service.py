# =============================================================================
# service.py — El corazón de Caja Link: consultar todas las cajas y decidir.
#
# Pregunta a todas las cajas al mismo tiempo (menos a la que consulta), junta
# las afiliaciones vigentes y aplica las reglas del contrato para el resultado.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# asyncio (estándar): lanza las consultas a todas las cajas en paralelo y espera a que terminen.
# logging (estándar): deja registro de qué caja falló (sin escribir el documento).
import asyncio
import logging

from app.connectors.base import CajaUnavailable
from app.domain.models import (
    RESULT_AFFILIATED,
    RESULT_NOT_AFFILIATED,
    RESULT_UNKNOWN,
    CheckResult,
    today_bogota,
)

logger = logging.getLogger(__name__)


# Aplica la regla del contrato para decidir el resultado de una consulta.
# Recibe: las afiliaciones vigentes encontradas y las cajas que no respondieron.
# Devuelve: uno de los tres resultados.
#   - Hay al menos una afiliación vigente             -> AFILIADO_OTRA_CAJA
#   - No hay ninguna, pero alguna caja no respondió   -> INDETERMINADO
#   - No hay ninguna y todas las cajas respondieron   -> NO_AFILIADO
# NO_AFILIADO solo se afirma cuando se pudo preguntar a todas las cajas.
def decide_result(matches: list, unavailable: list) -> str:
    if matches:
        return RESULT_AFFILIATED
    if unavailable:
        return RESULT_UNKNOWN
    return RESULT_NOT_AFFILIATED


class AffiliationService:
    # Recibe: el diccionario id de la caja -> conector que arma la fábrica de conectores.
    def __init__(self, connectors: dict):
        self.connectors = connectors

    # Espera a que las cajas activas estén listas antes de recibir consultas.
    # Recibe: cuántos segundos esperar como máximo (todas las cajas se esperan a la vez).
    # No devuelve nada: deja en el registro qué cajas no alcanzaron a responder.
    async def warm_up(self, max_seconds: float) -> None:
        ready = await asyncio.gather(*(connector.warm_up(max_seconds) for connector in self.connectors.values()))
        for caja_id, is_ready in zip(self.connectors, ready):
            if not is_ready:
                logger.warning("Caja %s no estuvo lista al arrancar; se informará como no disponible", caja_id)

    # Consulta un documento en todas las cajas activas, excepto la que pregunta.
    # Recibe: el documento normalizado y el id de la caja que consulta (dueña del token).
    # Devuelve: un CheckResult con el resultado, las afiliaciones vigentes y las cajas caídas.
    # Las cajas se consultan en paralelo: el tiempo total es el de la caja más lenta,
    # no la suma de todas. Si un conector falla de forma inesperada también cuenta
    # como "no disponible": ante la duda nunca se responde NO_AFILIADO.
    async def check(self, document: str, requester: str) -> CheckResult:
        sources = [(caja_id, connector) for caja_id, connector in self.connectors.items() if caja_id != requester]
        outcomes = await asyncio.gather(*(connector.query(document) for _, connector in sources), return_exceptions=True)

        cutoff = today_bogota()
        matches, unavailable = [], []
        for (caja_id, _), outcome in zip(sources, outcomes):
            if isinstance(outcome, CajaUnavailable):
                logger.warning("Caja %s no disponible: %s", caja_id, outcome.reason)
                unavailable.append(caja_id)
            elif isinstance(outcome, BaseException):
                logger.error("Caja %s falló de forma inesperada: %r", caja_id, outcome)
                unavailable.append(caja_id)
            else:
                matches.extend(affiliation for affiliation in outcome if affiliation.is_current(cutoff))

        return CheckResult(result=decide_result(matches, unavailable), matches=tuple(matches), unavailable=tuple(unavailable))
