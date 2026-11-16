# ─────────────────────────────────────────────────────────────
# API — convierte los errores al envoltorio común { mensaje, data: null, success: false }
# - HTTPException (de los routers, de seguridad.py y los 404/405 de rutas inexistentes)
# - Errores de validación de Pydantic -> 400 (la HU pide 400, no el 422 por defecto)
# - Cualquier otro error inesperado    -> 500 (se registra en el log)
# ─────────────────────────────────────────────────────────────

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.schemas.respuesta import error

logger = logging.getLogger(__name__)

# TODO(pendiente): la HU no define estos textos.
MENSAJE_JSON_INVALIDO = "El cuerpo de la solicitud no es un JSON válido"
MENSAJE_CUERPO_OBLIGATORIO = "El cuerpo de la solicitud es obligatorio"
MENSAJE_CUERPO_INVALIDO = "El cuerpo de la solicitud no es válido"
# TODO(pendiente): la HU no define el texto del 500 (su Definición de Hecho admite 500 o 503).
MENSAJE_500 = "Ocurrió un error interno al procesar la solicitud"

# Primer elemento de `loc` que indica DÓNDE vino el dato (no es el nombre del campo)
_ORIGENES = ("body", "query", "path", "header", "cookie")


def _mensaje_validacion(exc: RequestValidationError) -> str:
    """Construye un mensaje claro a partir del primer error de validación."""
    primero = exc.errors()[0]
    tipo = primero.get("type", "")
    if tipo == "json_invalid":
        return MENSAJE_JSON_INVALIDO

    loc = list(primero.get("loc", []))
    if loc and loc[0] in _ORIGENES:
        loc = loc[1:]
    if not loc:
        # El error es del cuerpo completo (no viene, o no es un objeto JSON)
        return MENSAJE_CUERPO_OBLIGATORIO if tipo == "missing" else MENSAJE_CUERPO_INVALIDO

    campo = str(loc[-1])
    if tipo == "missing":
        # Texto definido en HU-01, Caso 7: "El campo nombre es obligatorio"
        return f"El campo {campo} es obligatorio"
    # TODO(pendiente): la HU no define el texto para valores inválidos.
    return f"El campo {campo} no es válido"


def registrar_manejadores(app: FastAPI) -> None:

    @app.exception_handler(StarletteHTTPException)
    async def manejar_http(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content=error(str(exc.detail)),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def manejar_validacion(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error(_mensaje_validacion(exc)),
        )

    @app.exception_handler(Exception)
    async def manejar_inesperado(request: Request, exc: Exception):
        # Un error no previsto también responde con el envoltorio, y queda en el log
        logger.exception("Error no controlado en %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error(MENSAJE_500),
        )
