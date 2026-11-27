# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — API interna del módulo Parametrización: tipos de documento (API-I08)
# Implementa IConsultaTiposDocumento para que otros módulos (Usuarios HU-07,
# Vendedores HU-08) validen un documento sin usar las tablas de Parametrización.
# Lee el tipo (HU-02) y su formato (HU-05) con sus propios repositorios.
# Si la base falla, sale ErrorAccesoDatosTipoDocumento o ErrorAccesoDatosFormato:
# quien consume la interfaz los convierte en su propio 503.
# ─────────────────────────────────────────────────────────────

from app.domain.interfaces.consulta_tipos_documento import IConsultaTiposDocumento
from app.domain.models.tipo_documento import EstadoTipoDocumento
from app.repositories.formato_repository import FormatoRepository, formato_repository
from app.repositories.tipo_documento_repository import (
    TipoDocumentoRepository,
    tipo_documento_repository,
)


class ConsultaTiposDocumento(IConsultaTiposDocumento):

    def __init__(self, tipos: TipoDocumentoRepository, formatos: FormatoRepository):
        self.tipos = tipos
        self.formatos = formatos

    def tipo_esta_activo(self, tipo_documento_id: int) -> bool:
        tipo = self.tipos.obtener_por_id(tipo_documento_id)
        return tipo is not None and tipo.estado == EstadoTipoDocumento.ACTIVO

    def numero_cumple_formato(self, tipo_documento_id: int, numero: str) -> bool:
        formato = self.formatos.obtener_por_tipo(tipo_documento_id)
        # TODO(pendiente): la HU-07 no dice qué hacer si el tipo no tiene formato
        # definido. Se acepta cualquier número (no hay formato contra el cual validar).
        return formato is None or formato.numero_es_valido(numero)


# Instancia única compartida (Singleton simple)
consulta_tipos_documento = ConsultaTiposDocumento(tipo_documento_repository, formato_repository)
