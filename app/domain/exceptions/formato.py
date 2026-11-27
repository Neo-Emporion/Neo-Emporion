# ─────────────────────────────────────────────────────────────
# DOMINIO — errores de negocio de HU-05 (formato de validación)
# Los lanzan la entidad, el servicio o el repositorio; el router los convierte
# en HTTPException.
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.exceptions.base import ErrorDominio


class PatronInvalido(ErrorDominio):
    """El patrón no es una expresión regular válida (HTTP 400)."""

    def __init__(self):
        super().__init__("El patrón de validación no es válido")


class EjemploNoCumplePatron(ErrorDominio):
    """El ejemplo no cumple el patrón o las longitudes definidas (HTTP 400)."""

    def __init__(self):
        super().__init__("El ejemplo no cumple el patrón definido")


class LongitudesInconsistentes(ErrorDominio):
    """La longitud mínima es mayor que la máxima (HTTP 400)."""

    def __init__(self):
        super().__init__("La longitud mínima no puede ser mayor que la máxima")


class FormatoConRegistros(ErrorDominio):
    """RN-50: el tipo ya tiene formato y existen registros asociados (HTTP 409)."""

    def __init__(self):
        super().__init__(
            "No es posible modificar el formato porque existen registros asociados "
            "al tipo de documento"
        )


class TipoDocumentoInactivo(ErrorDominio):
    """Un tipo de documento INACTIVO no admite definir formato (HTTP 409)."""

    def __init__(self):
        # TODO(pendiente): la HU-05 (Caso 7) no define el texto; solo dice que indique la causa.
        super().__init__("El tipo de documento está inactivo")


class ErrorAccesoDatosFormato(ErrorDominio):
    """Falla al acceder a los datos al definir el formato (HTTP 503)."""

    def __init__(self):
        # Texto definido en HU-05, Caso 9.
        super().__init__("No fue posible definir el formato de validación")
