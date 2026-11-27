# ─────────────────────────────────────────────────────────────
# DOMINIO — contrato para saber si hay registros con un tipo de documento (RN-50)
# Los compradores (HU-07) y los vendedores (HU-08) son los que registran un
# número de documento con un tipo; esos módulos aún no están construidos.
# ─────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod


class IConsultaRegistrosTipoDocumento(ABC):

    @abstractmethod
    def tiene_registros_asociados(self, tipo_documento_id: int) -> bool:
        """True si existen compradores o vendedores registrados con el tipo (RN-50)."""
