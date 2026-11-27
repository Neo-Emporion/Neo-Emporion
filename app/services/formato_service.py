# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — HU-05 Definir formato de validación
# Orquesta dominio + repositorios: verifica que el tipo de documento exista y
# esté activo, le entrega a la entidad los datos para validar el formato y RN-50,
# y prepara la respuesta. No importa nada de FastAPI aquí.
# El tipo de documento se lee con el repositorio de HU-02: es el mismo
# submódulo (MOD-01 / SUB-01 Catálogos de Identificación).
# ─────────────────────────────────────────────────────────────

from app.domain.exceptions.formato import ErrorAccesoDatosFormato, TipoDocumentoInactivo
from app.domain.exceptions.tipo_documento import (
    ErrorAccesoDatosTipoDocumento,
    TipoDocumentoNoExiste,
)
from app.domain.interfaces.consulta_registros_tipo_documento import (
    IConsultaRegistrosTipoDocumento,
)
from app.domain.models.formato_validacion import (
    FormatoCreate,
    FormatoDatos,
    FormatoTipoDocumentoResponse,
    FormatoValidacion,
)
from app.domain.models.tipo_documento import EstadoTipoDocumento, TipoDocumento
from app.repositories.formato_repository import FormatoRepository
from app.repositories.tipo_documento_repository import TipoDocumentoRepository


class FormatoService:

    def __init__(self, repo: FormatoRepository, tipos: TipoDocumentoRepository,
                 registros: IConsultaRegistrosTipoDocumento):
        # Inyección de dependencias: repositorio de formatos, repositorio de tipos
        # de documento (HU-02) y consulta de registros asociados (RN-50)
        self.repo = repo
        self.tipos = tipos
        self.registros = registros

    # ── FUN-04 Definir formato de validación (API-G08) ────────
    def definir(self, tipo_documento_id: int, datos: FormatoCreate) -> FormatoTipoDocumentoResponse:
        tipo = self._obtener_tipo_activo(tipo_documento_id)
        nuevo = FormatoValidacion.crear(
            tipo_documento_id=tipo.id,
            patron=datos.patron,
            longitud_min=datos.longitud_min,
            longitud_max=datos.longitud_max,
            ejemplo=datos.ejemplo,
        )
        # RN-50: la regla vive en la entidad; el servicio le entrega los datos.
        # Solo se consultan los registros si ya había un formato definido.
        existente = self.repo.obtener_por_tipo(tipo.id)
        FormatoValidacion.verificar_modificacion(
            existente,
            tiene_registros=existente is not None
            and self.registros.tiene_registros_asociados(tipo.id),
        )
        guardado = self.repo.guardar(nuevo)
        return FormatoTipoDocumentoResponse(
            id=tipo.id, codigo=tipo.codigo, formato=FormatoDatos(**guardado.to_response()))

    # ── Apoyo interno ─────────────────────────────────────────
    def _obtener_tipo_activo(self, tipo_documento_id: int) -> TipoDocumento:
        try:
            tipo = self.tipos.obtener_por_id(tipo_documento_id)
        except ErrorAccesoDatosTipoDocumento as e:
            # Este endpoint responde el mensaje de la HU-05 (Caso 9)
            raise ErrorAccesoDatosFormato() from e
        if tipo is None:
            raise TipoDocumentoNoExiste()
        if tipo.estado != EstadoTipoDocumento.ACTIVO:
            raise TipoDocumentoInactivo()
        return tipo
