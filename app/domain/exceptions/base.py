# ─────────────────────────────────────────────────────────────
# DOMINIO — error base compartido por todos los módulos
# Cada módulo define sus errores en exceptions/<recurso>.py heredando de ErrorDominio.
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────


class ErrorDominio(Exception):
    """Error base del dominio. Guarda el mensaje que verá el cliente."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje
