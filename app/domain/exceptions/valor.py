# ─────────────────────────────────────────────────────────────
# DOMINIO — errores de negocio de HU-03 (catálogos transaccionales)
# Los lanzan la entidad, el servicio o el repositorio; el router los convierte
# en HTTPException.
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.exceptions.base import ErrorDominio


class ValorNoEncontrado(ErrorDominio):
    """El valor paramétrico solicitado no existe (HTTP 404)."""

    def __init__(self):
        super().__init__("El valor paramétrico no existe")


class ValorDuplicado(ErrorDominio):
    """Ya existe un valor con el mismo código en la categoría (HTTP 409)."""

    def __init__(self):
        super().__init__("Ya existe un valor con el mismo código en la categoría")


class CategoriaInvalida(ErrorDominio):
    """La categoría no es ESTADO, MONEDA, UNIDAD_MEDIDA ni METODO_PAGO (HTTP 400)."""

    def __init__(self):
        super().__init__("La categoría indicada no es válida")


class ValorEnUso(ErrorDominio):
    """RN-46: el valor está siendo utilizado por otro módulo (HTTP 409)."""

    def __init__(self):
        super().__init__(
            "No es posible desactivar el valor porque está siendo utilizado por otro módulo"
        )


class ErrorAccesoDatos(ErrorDominio):
    """Falla al acceder a los datos de valores paramétricos (HTTP 503)."""

    def __init__(self):
        super().__init__("No fue posible procesar la solicitud de valores paramétricos")
