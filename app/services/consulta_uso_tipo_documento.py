# Consulta de uso de un tipo de documento (HU-02, desactivar tipo de documento).
# Es la API interna del módulo Usuarios (HU-07): responde si hay compradores
# ACTIVOS con el tipo, sin que Parametrización use la tabla de compradores.
# TODO(pendiente): sumar los vendedores activos cuando se construya HU-08.

from app.domain.exceptions.comprador import ErrorAccesoDatosComprador
from app.domain.exceptions.tipo_documento import ErrorAccesoDatosTipoDocumento
from app.domain.interfaces.consulta_uso_tipo_documento import (
    IConsultaUsoTipoDocumento,
)
from app.repositories.comprador_repository import CompradorRepository, comprador_repository


class ConsultaUsoTipoDocumento(IConsultaUsoTipoDocumento):
    def __init__(self, compradores: CompradorRepository):
        self.compradores = compradores

    def tiene_compradores_o_vendedores_activos(
        self, tipo_documento_id: int
    ) -> bool:
        try:
            return self.compradores.existe_con_tipo_documento(
                tipo_documento_id, solo_activos=True
            )
        except ErrorAccesoDatosComprador as exc:
            # Quien consulta es HU-02: responde su propio 503
            raise ErrorAccesoDatosTipoDocumento() from exc


consulta_uso_tipo_documento = ConsultaUsoTipoDocumento(comprador_repository)
