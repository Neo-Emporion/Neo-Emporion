from app.domain.exceptions.tipo_documento import (
    CodigoTipoDocumentoDuplicado,
    TipoDocumentoNoExiste,
)
from app.domain.interfaces.consulta_uso_tipo_documento import (
    IConsultaUsoTipoDocumento,
)
from app.domain.models.tipo_documento import (
    FiltroEstadoTipoDocumento,
    TipoDocumentoCreate,
    TipoDocumentoDesactivado,
    TipoDocumentoListadoItem,
    TipoDocumentoResponse,
    TipoDocumentoUpdate,
)
from app.repositories.tipo_documento_repository import TipoDocumentoRepository


class TipoDocumentoService:
    def __init__(
        self,
        repo: TipoDocumentoRepository,
        consulta_uso: IConsultaUsoTipoDocumento,
    ):
        self.repo = repo
        self.consulta_uso = consulta_uso

    def registrar(self, datos: TipoDocumentoCreate) -> TipoDocumentoResponse:
        existente = self.repo.buscar_por_codigo(datos.codigo)
        if existente is not None:
            raise CodigoTipoDocumentoDuplicado()
        tipo = self.repo.crear(
            codigo=datos.codigo,
            nombre=datos.nombre,
            descripcion=datos.descripcion,
        )
        return TipoDocumentoResponse(**tipo.to_response())

    def editar(
        self,
        tipo_documento_id: int,
        datos: TipoDocumentoUpdate,
    ) -> TipoDocumentoResponse:
        tipo = self._obtener(tipo_documento_id)
        tipo.editar(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
        )
        tipo = self.repo.guardar(tipo)
        return TipoDocumentoResponse(**tipo.to_response())

    def listar(
        self,
        estado: FiltroEstadoTipoDocumento,
    ) -> list[TipoDocumentoListadoItem]:
        tipos = self.repo.listar(estado)
        return [
            TipoDocumentoListadoItem(**tipo.to_response())
            for tipo in tipos
        ]

    def desactivar(
        self,
        tipo_documento_id: int,
    ) -> TipoDocumentoDesactivado:
        tipo = self._obtener(tipo_documento_id)
        tipo.desactivar(
            esta_en_uso=self.consulta_uso.tiene_compradores_o_vendedores_activos(
                tipo_documento_id
            )
        )
        tipo = self.repo.guardar(tipo)
        return TipoDocumentoDesactivado(id=tipo.id, estado=tipo.estado)

    def _obtener(self, tipo_documento_id: int):
        tipo = self.repo.obtener_por_id(tipo_documento_id)
        if tipo is None:
            raise TipoDocumentoNoExiste()
        return tipo
