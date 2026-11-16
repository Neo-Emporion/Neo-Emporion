# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — consulta de direcciones activas por ubicación (RN-47)
# Implementación provisional: el módulo de direcciones (HU-15) aún no existe.
# ─────────────────────────────────────────────────────────────

import logging

from app.domain.interfaces.consulta_direcciones import IConsultaDirecciones

logger = logging.getLogger(__name__)


class ConsultaDireccionesProvisional(IConsultaDirecciones):

    def tiene_direcciones_activas(self, ubicacion_id: int) -> bool:
        # TODO(pendiente): conectar con el servicio público de direcciones
        # cuando se construya HU-15. Mientras tanto no hay direcciones registradas.
        logger.warning("RN-47 provisional: no se consultan direcciones de la ubicación %s "
                       "(HU-15 pendiente)", ubicacion_id)
        return False


# Instancia única compartida (Singleton simple)
consulta_direcciones = ConsultaDireccionesProvisional()
