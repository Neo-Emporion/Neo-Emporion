# ─────────────────────────────────────────────────────────────
# DOMINIO — contrato para saber si otro módulo usa un valor paramétrico (RN-46)
# Los valores los consumen otros módulos (Pedidos, Pagos, Envíos...), que aún
# no están construidos.
# ─────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod


class IConsultaUsoValores(ABC):

    @abstractmethod
    def esta_en_uso(self, valor_id: int) -> bool:
        """True si algún otro módulo está utilizando el valor `valor_id` (RN-46).

        TODO(pendiente): cuando se conecte la consulta real, una falla del otro
        módulo debe reportarse con un error de dominio mapeado a 503 (CLAUDE.md §4);
        la HU no define su mensaje.
        """
