# ─────────────────────────────────────────────────────────────
# DOMINIO — errores de negocio de HU-01 (catálogo geográfico)
# El servicio los lanza y el router los convierte en HTTPException.
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.exceptions.base import ErrorDominio


class UbicacionNoEncontrada(ErrorDominio):
    """La ubicación solicitada no existe (HTTP 404)."""

    def __init__(self):
        super().__init__("La ubicación no existe")


class UbicacionDuplicada(ErrorDominio):
    """Ya existe una ubicación con el mismo nombre/nivel/padre o el mismo código (HTTP 409)."""

    def __init__(self):
        super().__init__("Ya existe una ubicación con el mismo nombre o código en el mismo nivel")


class JerarquiaInvalida(ErrorDominio):
    """La relación tipo/padre no respeta PAIS -> DEPARTAMENTO -> CIUDAD (HTTP 400)."""

    def __init__(self):
        super().__init__("La jerarquía de la ubicación no es válida")


class DesactivacionNoPermitida(ErrorDominio):
    """RN-47: la ubicación tiene direcciones activas o ubicaciones hijas activas (HTTP 409).

    Por decisión del dueño del proyecto, el caso de ubicaciones hijas activas
    usa el mismo mensaje de RN-47 (la HU no define un texto propio).
    """

    def __init__(self):
        super().__init__(
            "No es posible desactivar la ubicación porque tiene direcciones activas asociadas"
        )


class ErrorAccesoDatos(ErrorDominio):
    """Falla al acceder a los datos de ubicaciones (HTTP 503)."""

    def __init__(self):
        super().__init__("No fue posible procesar la solicitud de ubicaciones")
