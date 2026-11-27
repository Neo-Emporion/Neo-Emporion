# ─────────────────────────────────────────────────────────────
# SCHEMAS — envoltorio común de todas las respuestas
# { "mensaje": "...", "data": {} | [] | null, "success": true|false }
# ─────────────────────────────────────────────────────────────

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Respuesta(BaseModel, Generic[T]):
    mensaje: str
    data: Optional[T] = None
    success: bool


class RespuestaError(BaseModel):
    mensaje: str
    data: None = None
    success: bool = False


def exito(mensaje: str, data: Any) -> dict:
    return {"mensaje": mensaje, "data": data, "success": True}


def error(mensaje: str) -> dict:
    return {"mensaje": mensaje, "data": None, "success": False}


def ejemplo_error(descripcion: str, mensaje: str) -> dict:
    """Arma la documentación OpenAPI de una respuesta de error con su ejemplo."""
    return {
        "model": RespuestaError,
        "description": descripcion,
        "content": {"application/json": {"example": error(mensaje)}},
    }
