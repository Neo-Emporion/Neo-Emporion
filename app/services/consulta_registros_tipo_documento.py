# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — consulta de registros asociados a un tipo de documento (RN-50, HU-05)
# Es la API interna del módulo Usuarios (HU-07): responde si hay compradores
# registrados con el tipo, sin que Parametrización use la tabla de compradores.
# TODO(pendiente): sumar los vendedores cuando se construya HU-08.
# ─────────────────────────────────────────────────────────────

from app.domain.exceptions.comprador import ErrorAccesoDatosComprador
from app.domain.exceptions.formato import ErrorAccesoDatosFormato
from app.domain.interfaces.consulta_registros_tipo_documento import (
    IConsultaRegistrosTipoDocumento,
)
from app.repositories.comprador_repository import CompradorRepository, comprador_repository


class ConsultaRegistrosTipoDocumento(IConsultaRegistrosTipoDocumento):

    def __init__(self, compradores: CompradorRepository):
        self.compradores = compradores

    def tiene_registros_asociados(self, tipo_documento_id: int) -> bool:
        # RN-50 habla de registros: cuenta cualquier comprador, activo o no
        try:
            return self.compradores.existe_con_tipo_documento(tipo_documento_id)
        except ErrorAccesoDatosComprador as e:
            # Quien consulta es HU-05: responde su propio 503
            raise ErrorAccesoDatosFormato() from e


# Instancia única compartida (Singleton simple)
consulta_registros_tipo_documento = ConsultaRegistrosTipoDocumento(comprador_repository)
