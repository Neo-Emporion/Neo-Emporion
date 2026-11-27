# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — consulta de registros asociados a un tipo de documento (RN-50)
# Implementación provisional: compradores (HU-07) y vendedores (HU-08) aún no existen.
# ─────────────────────────────────────────────────────────────

import logging

from app.domain.interfaces.consulta_registros_tipo_documento import (
    IConsultaRegistrosTipoDocumento,
)

logger = logging.getLogger(__name__)


class ConsultaRegistrosTipoDocumentoProvisional(IConsultaRegistrosTipoDocumento):

    def tiene_registros_asociados(self, tipo_documento_id: int) -> bool:
        # TODO(pendiente): conectar con compradores (HU-07) y vendedores (HU-08)
        # cuando se construyan. Mientras tanto no hay registros.
        logger.warning("RN-50 provisional: no se consultan registros del tipo de documento %s "
                       "(HU-07 y HU-08 pendientes)", tipo_documento_id)
        return False


# Instancia única compartida (Singleton simple)
consulta_registros_tipo_documento = ConsultaRegistrosTipoDocumentoProvisional()
