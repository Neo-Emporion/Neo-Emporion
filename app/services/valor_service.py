# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — HU-03 Gestionar catálogos transaccionales
# Orquesta dominio + repositorio: valida la unicidad y le entrega a la entidad
# los datos para validar la categoría y RN-46. No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.domain.exceptions.valor import ValorDuplicado, ValorNoEncontrado
from app.domain.interfaces.consulta_uso_valores import IConsultaUsoValores
from app.domain.models.valor_parametrico import (
    EstadoValor,
    FiltroEstadoValor,
    ValorCreate,
    ValorDesactivado,
    ValorParametrico,
    ValorResponse,
    ValorUpdate,
)
from app.repositories.valor_repository import ValorRepository


class ValorService:

    def __init__(self, repo: ValorRepository, uso: IConsultaUsoValores):
        # Inyección de dependencias: recibe el repositorio y la consulta de uso (RN-46)
        self.repo = repo
        self.uso = uso

    # ── FUN-11 Registrar valor paramétrico (API-G09) ──────────
    def registrar(self, datos: ValorCreate) -> ValorResponse:
        categoria = ValorParametrico.validar_categoria(datos.categoria)
        # Regla: el par (categoria, codigo) no puede existir previamente
        if self.repo.buscar_por_categoria_codigo(categoria, datos.codigo) is not None:
            raise ValorDuplicado()
        v = self.repo.crear(categoria=categoria, codigo=datos.codigo, nombre=datos.nombre)
        return ValorResponse(**v.to_response())

    # ── FUN-12 Editar valor paramétrico (API-G10) ─────────────
    def editar(self, id: int, datos: ValorUpdate) -> ValorResponse:
        v = self._obtener(id)
        v.editar(datos.nombre, datos.descripcion)
        v = self.repo.guardar(v)
        return ValorResponse(**v.to_response())

    # ── FUN-13 Consultar / listar catálogos (API-G11) ─────────
    def listar(self, categoria: str, estado: FiltroEstadoValor) -> list[ValorResponse]:
        cat = ValorParametrico.validar_categoria(categoria)
        # TODOS = sin filtro de estado; ACTIVO/INACTIVO se pasan tal cual
        # (el valor por defecto ACTIVO, RN-49, lo fija el router)
        filtro = None if estado == FiltroEstadoValor.TODOS else EstadoValor(estado.value)
        return [ValorResponse(**v.to_response()) for v in self.repo.listar(cat, filtro)]

    # ── FUN-14 Desactivar valor paramétrico (API-G12) ─────────
    def desactivar(self, id: int) -> ValorDesactivado:
        v = self._obtener(id)
        # RN-46: la regla vive en la entidad; el servicio le entrega el dato de uso.
        # Solo se consulta el uso si el valor está activo (si no, no hay nada que desactivar).
        v.desactivar(esta_en_uso=v.esta_activo and self.uso.esta_en_uso(v.id))
        v = self.repo.guardar(v)
        return ValorDesactivado(id=v.id, estado=v.estado)

    # ── Apoyo interno ─────────────────────────────────────────
    def _obtener(self, id: int) -> ValorParametrico:
        v = self.repo.obtener_por_id(id)
        if not v:
            # El servicio lanza la excepción; la API la captura
            raise ValorNoEncontrado()
        return v
