# ─────────────────────────────────────────────────────────────
# DOMINIO — contrato para saber si una ubicación tiene direcciones activas (RN-47)
# Las direcciones pertenecen al módulo Usuarios y Compradores (HU-15).
# ─────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod


class IConsultaDirecciones(ABC):

    @abstractmethod
    def tiene_direcciones_activas(self, ubicacion_id: int) -> bool:
        """True si hay al menos una dirección ACTIVA asociada a `ubicacion_id` (RN-47)."""
