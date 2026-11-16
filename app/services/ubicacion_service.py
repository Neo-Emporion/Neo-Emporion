# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — HU-01 Gestionar catálogo geográfico
# Orquesta dominio + repositorio: valida jerarquía, duplicidad y RN-47,
# y prepara la respuesta. No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from typing import Optional

from app.domain.exceptions.ubicacion import UbicacionDuplicada, UbicacionNoEncontrada
from app.domain.interfaces.consulta_direcciones import IConsultaDirecciones
from app.domain.models.dato_geografico import (
    DatoGeografico,
    EstadoUbicacion,
    FiltroEstado,
    TipoUbicacion,
    UbicacionCreate,
    UbicacionDesactivada,
    UbicacionListado,
    UbicacionListadoItem,
    UbicacionResponse,
    UbicacionUpdate,
)
from app.repositories.ubicacion_repository import UbicacionRepository


class UbicacionService:

    def __init__(self, repo: UbicacionRepository, direcciones: IConsultaDirecciones):
        # Inyección de dependencias: recibe el repositorio y la consulta de direcciones
        self.repo = repo
        self.direcciones = direcciones

    # ── FUN-06 Registrar dato geográfico (API-G01) ────────────
    def registrar(self, datos: UbicacionCreate) -> UbicacionResponse:
        self._validar_jerarquia(datos.tipo, datos.padre_id)
        self._validar_duplicados(datos.tipo, datos.nombre, datos.codigo, datos.padre_id)
        u = self.repo.crear(
            tipo=datos.tipo,
            nombre=datos.nombre,
            codigo=datos.codigo,
            padre_id=datos.padre_id,
        )
        return UbicacionResponse(**u.to_response())

    # ── FUN-07 Editar dato geográfico (API-G02) ───────────────
    def editar(self, id: int, datos: UbicacionUpdate) -> UbicacionResponse:
        u = self._obtener(id)
        # La entidad valida la jerarquía (con su tipo actual) y aplica los cambios
        # en memoria; si luego hay duplicado, no se guarda nada.
        u.editar(datos.nombre, datos.codigo, datos.padre_id, self._buscar_padre(datos.padre_id))
        self._validar_duplicados(u.tipo, u.nombre, u.codigo, u.padre_id, excluir_id=u.id)
        u = self.repo.guardar(u)
        return UbicacionResponse(**u.to_response())

    # ── FUN-08 Consultar / listar catálogo (API-I09) ──────────
    def listar(self, tipo: Optional[TipoUbicacion], padre_id: Optional[int],
               estado: FiltroEstado, pagina: int, tamano: int) -> UbicacionListado:
        # TODOS = sin filtro de estado
        filtro = None if estado == FiltroEstado.TODOS else EstadoUbicacion(estado.value)
        elementos, total = self.repo.listar(tipo, padre_id, filtro, pagina, tamano)
        return UbicacionListado(
            pagina=pagina,
            tamano=tamano,
            total=total,
            ubicaciones=[UbicacionListadoItem(**u.to_response()) for u in elementos],
        )

    # ── FUN-09 Desactivar dato geográfico (API-G03) ───────────
    def desactivar(self, id: int) -> UbicacionDesactivada:
        u = self._obtener(id)
        # RN-47: la regla vive en la entidad; el servicio le entrega los datos.
        u.desactivar(
            tiene_direcciones_activas=self.direcciones.tiene_direcciones_activas(u.id),
            tiene_hijas_activas=self.repo.existen_hijas_activas(u.id),
        )
        u = self.repo.guardar(u)
        return UbicacionDesactivada(id=u.id, estado=u.estado)

    # ── Apoyo interno ─────────────────────────────────────────
    def _obtener(self, id: int) -> DatoGeografico:
        u = self.repo.obtener_por_id(id)
        if not u:
            # El servicio lanza la excepción; la API la captura
            raise UbicacionNoEncontrada()
        return u

    def _buscar_padre(self, padre_id: Optional[int]) -> Optional[DatoGeografico]:
        # TODO(pendiente): la HU no define qué responder si padre_id no existe.
        # Se entrega None y la entidad lo trata como jerarquía inválida (400).
        return self.repo.obtener_por_id(padre_id) if padre_id is not None else None

    def _validar_jerarquia(self, tipo: TipoUbicacion, padre_id: Optional[int]) -> None:
        DatoGeografico.validar_jerarquia(tipo, padre_id, self._buscar_padre(padre_id))

    def _validar_duplicados(self, tipo: TipoUbicacion, nombre: str, codigo: str,
                            padre_id: Optional[int], excluir_id: Optional[int] = None) -> None:
        # Regla: no puede existir otra ubicación con el mismo código,
        # ni otra del mismo tipo con el mismo nombre y el mismo padre.
        por_codigo = self.repo.buscar_por_codigo(codigo)
        por_nombre = self.repo.buscar_por_tipo_nombre_padre(tipo, nombre, padre_id)
        for existente in (por_codigo, por_nombre):
            if existente is not None and existente.id != excluir_id:
                raise UbicacionDuplicada()
