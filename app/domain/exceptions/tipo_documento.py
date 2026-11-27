# CAPA DOMINIO — errores de negocio de HU-02

from app.domain.exceptions.base import ErrorDominio


class TipoDocumentoNoExiste(ErrorDominio):
    def __init__(self):
        super().__init__("El tipo de documento no existe")


class CodigoTipoDocumentoDuplicado(ErrorDominio):
    def __init__(self):
        super().__init__("Ya existe un tipo de documento con el código indicado")


class TipoDocumentoEnUso(ErrorDominio):
    def __init__(self):
        super().__init__(
            "No es posible desactivar el tipo de documento porque está en uso"
        )


class ErrorAccesoDatosTipoDocumento(ErrorDominio):
    # Texto definido en HU-02, Caso 10.
    def __init__(self):
        super().__init__(
            "No fue posible procesar la solicitud de tipos de documento"
        )
