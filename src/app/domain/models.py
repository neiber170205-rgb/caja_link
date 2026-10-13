# =============================================================================
# models.py — Modelo canónico de Caja Link.
#
# Cada caja responde en su propio formato (JSON, XML, archivo plano). Los
# conectores traducen todo a estas clases, y de aquí salen las respuestas v1 y
# v2. En este modelo NO existen nombre, dirección, teléfono, correo, salario ni
# beneficiarios: el dato mínimo se cumple porque esos datos nunca entran.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# secrets (estándar): números aleatorios seguros, para el identificador de la consulta.
# time (estándar): hora actual en milisegundos, también para el identificador.
# dataclasses (estándar): clases que solo guardan datos.
# datetime (estándar): fecha de hoy y zona horaria de Colombia.
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

# Finalidades permitidas por el contrato (Ley 1581: toda consulta declara para qué).
PURPOSES = ("TARIFA_SUBSIDIADA", "SUBSIDIO_MONETARIO", "VALIDACION_AFILIACION")

# Resultados posibles de una consulta.
RESULT_AFFILIATED = "AFILIADO_OTRA_CAJA"   # hay afiliación vigente en otra caja
RESULT_NOT_AFFILIATED = "NO_AFILIADO"      # todas las cajas respondieron y ninguna la tiene
RESULT_UNKNOWN = "INDETERMINADO"           # alguna caja no respondió y las demás no la tienen

# De dónde salió el dato.
SOURCE_ONLINE = "ONLINE"   # consulta en vivo a la caja
SOURCE_FILE = "FILE"       # archivo plano del día anterior

# Colombia no tiene horario de verano: siempre UTC-5.
BOGOTA = timezone(timedelta(hours=-5))

# Alfabeto Crockford base32 (sin I, L, O, U para que no se confundan al leer).
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


# Una afiliación de una persona en una caja, ya traducida al formato común.
#   caja            caja donde está afiliada (NORTE, ORIENTE...)
#   valid_from      fecha de inicio en formato AAAA-MM-DD
#   valid_to        fecha de fin en formato AAAA-MM-DD, o None si no tiene fin
#   affiliate_type  DEPENDIENTE, INDEPENDIENTE o PENSIONADO (solo se publica en v2)
#   source          ONLINE o FILE
#   as_of           fecha a la que corresponde la información
@dataclass(frozen=True)
class Affiliation:
    caja: str
    valid_from: str | None
    valid_to: str | None
    affiliate_type: str | None
    source: str
    as_of: str

    # Dice si la afiliación está vigente en una fecha.
    # Recibe: la fecha de corte en formato AAAA-MM-DD.
    # Devuelve: True si no tiene fecha de fin o si su fecha de fin es igual o posterior al corte.
    # (Las fechas AAAA-MM-DD se pueden comparar como texto: el orden alfabético es el cronológico.)
    def is_current(self, cutoff: str) -> bool:
        return self.valid_to is None or self.valid_to >= cutoff


# Resultado de consultar un documento en todas las cajas.
#   result       uno de los tres resultados del contrato
#   matches      afiliaciones vigentes encontradas en otras cajas
#   unavailable  cajas que no respondieron
@dataclass(frozen=True)
class CheckResult:
    result: str
    matches: tuple
    unavailable: tuple


# Devuelve la fecha de hoy en Colombia como texto AAAA-MM-DD.
# Se usa como fecha de corte de la consulta y como "asOf" de las fuentes en línea.
def today_bogota() -> str:
    return datetime.now(BOGOTA).date().isoformat()


# Genera el identificador único de una consulta (formato ULID, 26 caracteres).
# No recibe nada. Devuelve un texto como "01JABCD...": los primeros caracteres salen
# de la hora, así que los identificadores quedan ordenados por tiempo en la auditoría.
def new_request_id() -> str:
    value = (int(time.time() * 1000) << 80) | secrets.randbits(80)
    chars = []
    for _ in range(26):
        chars.append(CROCKFORD[value & 31])
        value >>= 5
    return "".join(reversed(chars))
