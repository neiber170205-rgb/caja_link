# =============================================================================
# errors.py — Error propio de la API.
#
# Cualquier parte del servicio puede lanzar ApiError para cortar la petición con
# un código HTTP y un mensaje claro. main.py lo convierte en la respuesta JSON
# {"error": "CODIGO", "message": "explicación"}.
# =============================================================================


# Error que termina la petición con una respuesta HTTP controlada.
#   status   código HTTP (400, 401, 403, 404...)
#   code     código corto y estable para programas ("FINALIDAD_INVALIDA")
#   message  explicación para personas, sin datos personales
class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
