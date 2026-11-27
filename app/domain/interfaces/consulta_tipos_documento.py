# ─────────────────────────────────────────────────────────────
# DOMINIO — contrato para consultar tipos de documento (API-I08) desde otro módulo
# MOD-02 Usuarios (HU-07) y MOD-04 Vendedores (HU-08) validan el documento con el
# tipo (HU-02) y su formato (HU-05), que son datos del módulo Parametrización.
# Si la base de Parametrización falla (SQLAlchemyError), los métodos lanzan
# ErrorAccesoDatosTipoDocumento o ErrorAccesoDatosFormato: el módulo que consume
# la interfaz los convierte en su propio 503 (ver CompradorService._verificar_documento).
# ─────────────────────────────────────────────────────────────

from abc import ABC, abstractmethod


class IConsultaTiposDocumento(ABC):

    @abstractmethod
    def tipo_esta_activo(self, tipo_documento_id: int) -> bool:
        """True si el tipo de documento existe y está ACTIVO."""

    @abstractmethod
    def numero_cumple_formato(self, tipo_documento_id: int, numero: str) -> bool:
        """True si el número cumple el formato del tipo (HU-05).
        Llamarlo SOLO si tipo_esta_activo() devolvió True: para un tipo que no existe
        también devuelve True, porque no encuentra formato.
        TODO(pendiente): si el tipo no tiene formato definido, cualquier número se acepta
        (la HU-07 no lo define)."""
