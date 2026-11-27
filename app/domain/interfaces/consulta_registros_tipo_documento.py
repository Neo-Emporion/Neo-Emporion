# ─────────────────────────────────────────────────────────────
# DOMINIO — contrato para saber si hay registros con un tipo de documento (RN-50)
# Los compradores (HU-07, ya conectado) y los vendedores (HU-08, pendiente) son los
# que registran un número de documento con un tipo.
# ─────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod


class IConsultaRegistrosTipoDocumento(ABC):

    @abstractmethod
    def tiene_registros_asociados(self, tipo_documento_id: int) -> bool:
        """True si existen compradores o vendedores registrados con el tipo (RN-50)."""
