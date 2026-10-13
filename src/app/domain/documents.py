# =============================================================================
# documents.py — Reglas sobre el número de documento.
#
# Cada caja escribe el documento a su manera (con puntos, con espacios, con ceros
# a la izquierda). Aquí se lleva a una sola forma para comparar, y se enmascara
# antes de guardarlo en la auditoría.
# =============================================================================

# --- Librerías ---------------------------------------------------------------
# re (estándar): expresiones regulares, para quitar separadores y validar dígitos.
import re

# Caracteres que la gente usa como separador y que no hacen parte del número:
# espacios (de cualquier tipo), puntos, comas y guiones.
SEPARATORS = re.compile(r"[\s.,\-]")

# Solo dígitos 0-9 (no se usa str.isdigit porque acepta símbolos como "²").
ONLY_DIGITS = re.compile(r"[0-9]+")

# Largo máximo aceptado después de normalizar. Los documentos colombianos tienen
# hasta 10 dígitos; se deja margen sin aceptar cadenas absurdas.
MAX_DIGITS = 15

# Cuántos dígitos del final se dejan visibles al enmascarar.
VISIBLE_DIGITS = 4


# Lleva un documento a su forma única: solo dígitos y sin ceros a la izquierda.
# Recibe: el texto tal como llegó ("001.098.765.432", " 1098 765 432 "...).
# Devuelve: el documento normalizado ("1098765432"), o None si no es válido
#           (tiene letras, queda vacío o es demasiado largo).
def normalize_document(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = SEPARATORS.sub("", str(raw))
    if not ONLY_DIGITS.fullmatch(cleaned):
        return None
    cleaned = cleaned.lstrip("0")
    if not cleaned or len(cleaned) > MAX_DIGITS:
        return None
    return cleaned


# Oculta el documento para la auditoría dejando visibles solo los últimos dígitos.
# Recibe: el documento ya normalizado ("1098765432").
# Devuelve: el documento enmascarado ("******5432"). Nunca muestra más de 4 dígitos
#           y en documentos cortos muestra menos, para no revelar el número completo.
def mask_document(document: str) -> str:
    visible = min(VISIBLE_DIGITS, max(0, len(document) - VISIBLE_DIGITS))
    hidden = len(document) - visible
    return "*" * hidden + document[hidden:]
