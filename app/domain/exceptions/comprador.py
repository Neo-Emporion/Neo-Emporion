# ─────────────────────────────────────────────────────────────
# DOMINIO — errores de negocio de HU-07 (registro e inicio de sesión del comprador)
# Los lanzan la entidad, el servicio o el repositorio; el router los convierte
# en HTTPException.
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.exceptions.base import ErrorDominio


class ContrasenaInsegura(ErrorDominio):
    """RN-55: la contraseña no cumple los requisitos mínimos (HTTP 400)."""

    def __init__(self):
        # Texto definido en HU-07, Caso 4.
        super().__init__("La contraseña no cumple los requisitos mínimos de seguridad")


class DocumentoNoCumpleFormato(ErrorDominio):
    """El número de documento no cumple el formato del tipo (HU-05) (HTTP 400)."""

    def __init__(self):
        # Texto definido en HU-07, Caso 5.
        super().__init__("El número de documento no cumple el formato del tipo seleccionado")


class TipoDocumentoNoValido(ErrorDominio):
    """El tipo de documento no existe o está INACTIVO (HTTP 400)."""

    def __init__(self):
        # TODO(pendiente): la HU-07 pide un tipo de documento activo, pero no define el texto.
        super().__init__("El tipo de documento indicado no es válido")


class CorreoDuplicado(ErrorDominio):
    """RN-51: ya existe una cuenta con ese correo (HTTP 409)."""

    def __init__(self):
        # Texto definido en HU-07, Caso 3.
        super().__init__("Ya existe una cuenta registrada con ese correo")


class CredencialesIncorrectas(ErrorDominio):
    """Correo o contraseña incorrectos, sin decir cuál de los dos falló (HTTP 401)."""

    def __init__(self):
        # Texto definido en HU-07, Caso 7.
        super().__init__("Correo o contraseña incorrectos")


class CuentaDesactivada(ErrorDominio):
    """RN-52: una cuenta DESACTIVADA no puede iniciar sesión (HTTP 403)."""

    def __init__(self):
        # Texto definido en HU-07, Caso 8.
        super().__init__("La cuenta se encuentra desactivada")


class ErrorAccesoDatosComprador(ErrorDominio):
    """Falla de la base de datos o del módulo Parametrización (HTTP 503)."""

    def __init__(self):
        # Texto definido en HU-07, Caso 9.
        super().__init__("No fue posible procesar la solicitud en este momento")
