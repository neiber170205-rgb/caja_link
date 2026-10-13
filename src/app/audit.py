# =============================================================================
# audit.py — Registro de auditoría (trazabilidad, Ley 1581).
#
# Por cada consulta respondida se guarda quién preguntó, con qué finalidad y qué
# resultado obtuvo. El documento se guarda enmascarado: la auditoría sirve para
# rastrear el uso sin volverse otra copia de los datos personales.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# collections.deque (estándar): lista con tamaño máximo; al llenarse descarta lo más viejo,
#                               así la memoria del servicio no crece sin límite.
# datetime (estándar): hora exacta de cada consulta, en UTC.
from collections import deque
from datetime import datetime, timezone

from app.domain.documents import mask_document

# Máximo de entradas que se conservan en memoria.
DEFAULT_CAPACITY = 100_000


class AuditLog:
    # Recibe: cuántas entradas conservar como máximo.
    def __init__(self, capacity: int = DEFAULT_CAPACITY):
        self.entries = deque(maxlen=capacity)

    # Guarda una consulta respondida.
    # Recibe: el identificador de la consulta, la caja que preguntó, la finalidad declarada,
    #         el resultado entregado, el documento normalizado y el canal (ONLINE o BATCH).
    # Devuelve: la entrada guardada. El documento se enmascara aquí mismo, antes de guardar.
    def record(self, request_id: str, requesting_caja: str, purpose: str, result: str, document: str, channel: str = "ONLINE") -> dict:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "requestId": request_id,
            "requestingCaja": requesting_caja,
            "purpose": purpose,
            "result": result,
            "documentMasked": mask_document(document),
            "channel": channel,
        }
        self.entries.append(entry)
        return entry

    # Entrega las consultas más recientes.
    # Recibe: cuántas entradas devolver.
    # Devuelve: una lista de entradas, de la más nueva a la más vieja.
    def latest(self, limit: int) -> list:
        newest_first = reversed(self.entries)
        return [entry for _, entry in zip(range(limit), newest_first)]
