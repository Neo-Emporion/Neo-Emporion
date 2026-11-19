from abc import ABC, abstractmethod


class IConsultaUsoTipoDocumento(ABC):
    @abstractmethod
    def tiene_compradores_o_vendedores_activos(
        self, tipo_documento_id: int
    ) -> bool:
        """Indica si compradores o vendedores activos usan el tipo."""
