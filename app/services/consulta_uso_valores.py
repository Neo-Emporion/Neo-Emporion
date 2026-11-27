# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — consulta de uso de valores paramétricos por otros módulos (RN-46)
# Implementación provisional: los módulos que consumen valores (Pedidos, Pagos,
# Envíos...) aún no existen.
# ─────────────────────────────────────────────────────────────

import logging

from app.domain.interfaces.consulta_uso_valores import IConsultaUsoValores

logger = logging.getLogger(__name__)


class ConsultaUsoValoresProvisional(IConsultaUsoValores):

    def esta_en_uso(self, valor_id: int) -> bool:
        # TODO(pendiente): conectar con los módulos que consumen valores paramétricos
        # cuando se construyan (HU-16, HU-19, HU-22...). Mientras tanto ninguno los usa.
        logger.warning("RN-46 provisional: no se consulta el uso del valor %s "
                       "(módulos consumidores pendientes)", valor_id)
        return False


# Instancia única compartida (Singleton simple)
consulta_uso_valores = ConsultaUsoValoresProvisional()
