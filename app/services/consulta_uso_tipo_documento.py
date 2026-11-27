# Implementación provisional hasta construir HU-07 y HU-08.
# TODO(pendiente): conectar con compradores y vendedores reales.

from app.domain.interfaces.consulta_uso_tipo_documento import (
    IConsultaUsoTipoDocumento,
)


class ConsultaUsoTipoDocumentoProvisional(IConsultaUsoTipoDocumento):
    def tiene_compradores_o_vendedores_activos(
        self, tipo_documento_id: int
    ) -> bool:
        return False


consulta_uso_tipo_documento = ConsultaUsoTipoDocumentoProvisional()
