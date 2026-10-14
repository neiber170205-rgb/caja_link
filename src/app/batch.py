# =============================================================================
# batch.py — Cruce por lote: revisar muchos documentos de una sola vez.
#
# La caja envía un archivo CSV y recibe de inmediato un jobId. El trabajo corre
# en segundo plano y la caja pregunta por su estado hasta que esté DONE.
#
# Ideas clave:
#   - Idempotencia: la misma Idempotency-Key devuelve el mismo jobId. Si la caja
#     reenvía el archivo por un corte de red, no se procesa dos veces.
#   - Paralelismo con tope: se consultan varios documentos a la vez, pero no
#     todos, para no saturar a las cajas.
#   - Ronda de repaso: los documentos que quedan INDETERMINADO se vuelven a
#     intentar una vez, más despacio. Así una falla momentánea no daña el lote.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# asyncio (estándar): corre el lote en segundo plano y limita cuántas consultas van a la vez.
# csv (estándar): lee el archivo CSV respetando comillas y separadores.
# io (estándar): permite leer un texto en memoria como si fuera un archivo.
# logging (estándar): deja el resumen de cada lote en el registro del servicio.
# dataclasses (estándar): clases que solo guardan datos.
import asyncio
import csv
import io
import logging
from dataclasses import dataclass, field

from app.audit import AuditLog
from app.domain.documents import normalize_document
from app.domain.models import RESULT_UNKNOWN, SOURCE_ONLINE, CheckResult, new_request_id
from app.domain.service import AffiliationService
from app.errors import ApiError

logger = logging.getLogger(__name__)

# Estados de un lote, según el contrato.
STATUS_PENDING = "PENDING"
STATUS_RUNNING = "RUNNING"
STATUS_DONE = "DONE"

# Resultado para una fila cuyo documento no es un número válido.
RESULT_INVALID_DOCUMENT = "DOCUMENTO_INVALIDO"

# Finalidad que se registra cuando el lote no declara una: cruzar afiliaciones es,
# por definición, validar afiliación.
DEFAULT_PURPOSE = "VALIDACION_AFILIACION"

# Límites de entrada, para que un archivo enorme no agote la memoria del servicio.
MAX_BODY_BYTES = 5 * 1024 * 1024
MAX_DOCUMENTS = 100_000

# Consultas simultáneas a las cajas que se permite un lote, en total: la primera
# ronda va rápido y la de repaso más despacio, para darle aire a una caja que venía
# fallando. Se midió en desarrollo que con más de unas 40 consultas a la vez el
# servicio se satura y el lote tarda más, no menos; por eso el tope es moderado.
ROUND_CAJA_REQUESTS = (24, 8)

# Mínimo de documentos en paralelo, aunque haya muchas cajas en línea.
MIN_DOCUMENTS_AT_ONCE = 4

# Segundos de pausa antes de la ronda de repaso.
ROUND_PAUSE_SECONDS = 3.0

# Pasado este tiempo el repaso se detiene (el contrato da 5 minutos por lote).
MAX_JOB_SECONDS = 240.0

# Cuántos lotes se conservan en memoria; al pasar de ahí se olvidan los terminados más viejos.
MAX_JOBS = 20


# Un lote y su avance.
#   id         identificador que se entrega a la caja (jobId)
#   requester  caja que lo envió: solo ella puede consultarlo
#   purpose    finalidad declarada
#   documents  documentos tal como llegaron en el archivo
#   status     PENDING, RUNNING o DONE
#   processed  documentos que ya tienen un primer resultado
#   results    un resultado por documento, en el orden del archivo (se llena al terminar)
@dataclass
class BatchJob:
    id: str
    requester: str
    purpose: str
    documents: list
    status: str = STATUS_PENDING
    processed: int = 0
    results: list = field(default_factory=list)

    # Escribe el estado del lote en el formato del contrato.
    # No recibe nada. Devuelve: el diccionario de la respuesta. "results" va vacío
    # hasta que el lote termina, para que preguntar por el avance sea liviano.
    def to_response(self) -> dict:
        return {
            "jobId": self.id,
            "status": self.status,
            "total": len(self.documents),
            "processed": self.processed,
            "results": self.results if self.status == STATUS_DONE else [],
        }


# Extrae los documentos de un archivo CSV.
# Recibe: el contenido del archivo en bytes.
# Devuelve: la lista de documentos tal como vienen escritos, en orden y sin normalizar.
# Lanza ApiError 400 si el archivo está vacío o no tiene la columna "document",
# y 413 si trae más documentos de los permitidos.
def parse_documents(data: bytes) -> list:
    text = data.decode("utf-8-sig", errors="replace")
    rows = [row for row in csv.reader(io.StringIO(text)) if any(cell.strip() for cell in row)]
    if not rows:
        raise ApiError(400, "CSV_VACIO", "El archivo no trae documentos")

    header = [cell.strip().lower() for cell in rows[0]]
    if "document" not in header:
        raise ApiError(400, "CSV_INVALIDO", "El archivo debe tener una columna llamada document")
    column = header.index("document")

    documents = [row[column] for row in rows[1:] if len(row) > column and row[column].strip()]
    if not documents:
        raise ApiError(400, "CSV_VACIO", "El archivo no trae documentos")
    if len(documents) > MAX_DOCUMENTS:
        raise ApiError(413, "LOTE_DEMASIADO_GRANDE", "Máximo {0} documentos por lote".format(MAX_DOCUMENTS))
    return documents


# Arma el resultado de un documento en el formato del contrato (igual al de la v1).
# Recibe: el documento como llegó, el documento normalizado (None si no es válido)
#         y el CheckResult de la consulta (None si no se alcanzó a consultar).
# Devuelve: el diccionario del resultado. "document" lleva el número normalizado y
#           "documentInput" el texto original, para que la caja lo ubique en su archivo.
# Un documento que no se pudo consultar queda INDETERMINADO, nunca NO_AFILIADO.
def build_entry(raw: str, document: str | None, check: CheckResult | None) -> dict:
    if document is None:
        return {"document": raw.strip(), "documentInput": raw, "result": RESULT_INVALID_DOCUMENT, "matches": [], "unavailable": []}
    if check is None:
        return {"document": document, "documentInput": raw, "result": RESULT_UNKNOWN, "matches": [], "unavailable": []}
    return {
        "document": document,
        "documentInput": raw,
        "result": check.result,
        "matches": [
            {"caja": a.caja, "validFrom": a.valid_from, "validTo": a.valid_to, "source": a.source, "asOf": a.as_of}
            for a in check.matches
        ],
        "unavailable": list(check.unavailable),
    }


class BatchManager:
    # Recibe: el servicio de consulta (el mismo de la consulta en línea) y la auditoría.
    def __init__(self, service: AffiliationService, audit: AuditLog):
        self.service = service
        self.audit = audit
        self.jobs = {}       # jobId -> BatchJob, en orden de llegada
        self.keys = {}       # (caja, Idempotency-Key) -> jobId
        self.tasks = set()   # tareas en segundo plano (se guardan para que no se pierdan)

    # Busca un lote ya creado con la misma llave de idempotencia.
    # Recibe: la caja que envía y la llave (puede ser None).
    # Devuelve: el BatchJob existente, o None si esa caja no ha usado esa llave.
    def find_by_key(self, requester: str, key: str | None) -> BatchJob | None:
        if not key:
            return None
        return self.jobs.get(self.keys.get((requester, key), ""))

    # Crea un lote y lo pone a correr en segundo plano.
    # Recibe: la caja que envía, la finalidad, los documentos y la llave de idempotencia.
    # Devuelve: el BatchJob. Si la llave ya se usó, devuelve el lote anterior sin crear otro.
    def submit(self, requester: str, purpose: str, documents: list, key: str | None) -> BatchJob:
        existing = self.find_by_key(requester, key)
        if existing is not None:
            return existing
        job = BatchJob(id=new_request_id(), requester=requester, purpose=purpose, documents=documents)
        self.jobs[job.id] = job
        if key:
            self.keys[(requester, key)] = job.id
        self.forget_old_jobs()
        task = asyncio.create_task(self.run(job))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return job

    # Entrega un lote solo a la caja que lo creó.
    # Recibe: el jobId y la caja que pregunta.
    # Devuelve: el BatchJob, o None si no existe o es de otra caja (no se revela cuál de las dos).
    def get(self, job_id: str, requester: str) -> BatchJob | None:
        job = self.jobs.get(job_id)
        return job if job is not None and job.requester == requester else None

    # Olvida los lotes terminados más viejos cuando hay más de MAX_JOBS en memoria.
    # No recibe ni devuelve nada. Los lotes que siguen corriendo nunca se olvidan.
    def forget_old_jobs(self) -> None:
        finished = [job_id for job_id, job in self.jobs.items() if job.status == STATUS_DONE]
        while len(self.jobs) > MAX_JOBS and finished:
            old_id = finished.pop(0)
            del self.jobs[old_id]
            self.keys = {key: job_id for key, job_id in self.keys.items() if job_id != old_id}

    # Calcula cuántos documentos se consultan a la vez en una ronda.
    # Recibe: la caja que envió el lote y el tope de consultas simultáneas a las cajas.
    # Devuelve: el número de documentos en paralelo. Cada documento abre una consulta por
    # cada caja en línea (las de archivo responden desde memoria), así que el tope se
    # reparte entre ellas: con más cajas en línea van menos documentos a la vez.
    def documents_at_once(self, requester: str, caja_requests: int) -> int:
        online = sum(1 for caja_id, connector in self.service.connectors.items()
                     if caja_id != requester and connector.source == SOURCE_ONLINE)
        return max(MIN_DOCUMENTS_AT_ONCE, caja_requests // max(1, online))

    # Consulta un grupo de documentos en paralelo, con un tope de consultas simultáneas.
    # Recibe: el lote, la lista de documentos normalizados, las posiciones a consultar,
    #         cuántos consultar a la vez, el diccionario posición -> CheckResult a llenar
    #         y la hora límite de la ronda (None si no tiene).
    # No devuelve nada: deja cada resultado en "checks" y actualiza el avance del lote.
    # Pasada la hora límite los documentos que falten conservan el resultado que tenían.
    async def run_round(self, job: BatchJob, documents: list, positions: list, concurrency: int, checks: dict, deadline: float | None) -> None:
        semaphore = asyncio.Semaphore(concurrency)
        loop = asyncio.get_running_loop()

        # Consulta un documento cuando el semáforo le da paso.
        async def check_one(position: int) -> None:
            async with semaphore:
                if deadline is not None and loop.time() >= deadline:
                    return
                check = await self.service.check(documents[position], job.requester)
                if position not in checks:
                    job.processed += 1
                checks[position] = check

        outcomes = await asyncio.gather(*(check_one(position) for position in positions), return_exceptions=True)
        failures = sum(1 for outcome in outcomes if isinstance(outcome, BaseException))
        if failures:
            logger.error("Lote %s: %d documentos fallaron de forma inesperada y quedan INDETERMINADO", job.id, failures)

    # Procesa un lote completo. Corre en segundo plano.
    # Recibe: el BatchJob. No devuelve nada: deja los resultados en el propio lote.
    # 1. Normaliza cada documento (los inválidos quedan marcados y no se consultan).
    # 2. Primera ronda con todos los documentos válidos.
    # 3. Ronda de repaso solo con los que quedaron INDETERMINADO, si hay tiempo.
    # 4. Escribe los resultados y la auditoría, y marca el lote como DONE.
    # Pase lo que pase el lote termina en DONE: un error inesperado deja los documentos
    # sin resolver como INDETERMINADO, nunca como NO_AFILIADO.
    async def run(self, job: BatchJob) -> None:
        loop = asyncio.get_running_loop()
        started = loop.time()
        job.status = STATUS_RUNNING

        documents = [normalize_document(raw) for raw in job.documents]
        pending = [position for position, document in enumerate(documents) if document is not None]
        job.processed = len(documents) - len(pending)
        checks = {}
        try:
            for round_number, caja_requests in enumerate(ROUND_CAJA_REQUESTS):
                deadline = None
                if round_number:
                    deadline = started + MAX_JOB_SECONDS
                    if loop.time() + ROUND_PAUSE_SECONDS >= deadline:
                        break
                    await asyncio.sleep(ROUND_PAUSE_SECONDS)
                concurrency = self.documents_at_once(job.requester, caja_requests)
                await self.run_round(job, documents, pending, concurrency, checks, deadline)
                pending = [p for p in pending if p not in checks or checks[p].result == RESULT_UNKNOWN]
                if not pending:
                    break
        except Exception:
            logger.exception("Lote %s: error inesperado; lo que falte queda INDETERMINADO", job.id)

        job.results = [build_entry(raw, documents[position], checks.get(position)) for position, raw in enumerate(job.documents)]
        for position, entry in enumerate(job.results):
            if documents[position] is not None:
                self.audit.record(job.id, job.requester, job.purpose, entry["result"], documents[position], channel="BATCH")
        job.processed = len(job.documents)
        job.status = STATUS_DONE
        logger.info("Lote %s terminado en %.1f s: %d documentos, %d sin resolver",
                    job.id, loop.time() - started, len(job.documents), len(pending))
