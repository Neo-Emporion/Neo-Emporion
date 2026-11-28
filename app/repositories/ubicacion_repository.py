# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — HU-01 Gestionar catálogo geográfico
# Única responsabilidad: guardar y recuperar ubicaciones.
# Solo manipula datos. Sin lógica de negocio aquí.
# Usa SQLAlchemy (por defecto SQLite en memoria, según DATABASE_URL) y devuelve
# entidades DatoGeografico.
# - Código repetido rechazado por la base (IntegrityError) -> UbicacionDuplicada (HTTP 409)
# - Cualquier otro SQLAlchemyError -> ErrorAccesoDatos (HTTP 503), y se registra en el log
# ─────────────────────────────────────────────────────────────

import logging
from functools import wraps
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.core.database import Base, SessionLocal
from app.domain.exceptions.ubicacion import (
    ErrorAccesoDatos,
    UbicacionDuplicada,
    UbicacionNoEncontrada,
)
from app.domain.models.dato_geografico import DatoGeografico, EstadoUbicacion, TipoUbicacion

logger = logging.getLogger(__name__)


# ── Tabla "ubicaciones" (modelo ORM de SQLAlchemy) ────────────
class UbicacionTabla(Base):
    __tablename__ = "ubicaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # tipo y estado se guardan como texto, pero SQLAlchemy solo acepta valores del Enum
    tipo: Mapped[TipoUbicacion] = mapped_column(
        Enum(TipoUbicacion, native_enum=False, length=20), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    # Jerarquía: el padre es otra fila de esta misma tabla
    padre_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ubicaciones.id"), nullable=True)
    estado: Mapped[EstadoUbicacion] = mapped_column(
        Enum(EstadoUbicacion, native_enum=False, length=10), nullable=False)
    publicada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


def _a_entidad(fila: UbicacionTabla) -> DatoGeografico:
    """Convierte una fila de la tabla en la entidad de dominio."""
    return DatoGeografico(
        id=fila.id,
        tipo=fila.tipo,
        nombre=fila.nombre,
        codigo=fila.codigo,
        padre_id=fila.padre_id,
        estado=fila.estado,
        publicada=fila.publicada,
    )


def _manejar_errores_bd(metodo):
    """Traduce los errores de SQLAlchemy a errores de dominio."""
    @wraps(metodo)
    def envoltura(*args, **kwargs):
        try:
            return metodo(*args, **kwargs)
        except IntegrityError as e:
            # La columna `codigo` es única: si dos peticiones llegan a la vez con el
            # mismo código, la base rechaza la segunda. Es un duplicado, no una falla.
            raise UbicacionDuplicada() from e
        except SQLAlchemyError as e:
            logger.exception("Error de base de datos en %s", metodo.__qualname__)
            raise ErrorAccesoDatos() from e
    return envoltura


class UbicacionRepository:

    def __init__(self, sesiones: sessionmaker = SessionLocal):
        # Fábrica de sesiones de SQLAlchemy: cada operación abre y cierra su sesión
        self._sesiones = sesiones

    # ── Consultas ─────────────────────────────────────────────

    @_manejar_errores_bd
    def obtener_por_id(self, id: int) -> Optional[DatoGeografico]:
        with self._sesiones() as s:
            fila = s.get(UbicacionTabla, id)
            return _a_entidad(fila) if fila else None

    @_manejar_errores_bd
    def buscar_por_codigo(self, codigo: str) -> Optional[DatoGeografico]:
        with self._sesiones() as s:
            fila = s.scalars(
                select(UbicacionTabla).where(UbicacionTabla.codigo == codigo)).first()
            return _a_entidad(fila) if fila else None

    @_manejar_errores_bd
    def buscar_por_tipo_nombre_padre(self, tipo: TipoUbicacion, nombre: str,
                                     padre_id: Optional[int]) -> Optional[DatoGeografico]:
        # TODO(pendiente): la HU no dice si la comparación del nombre ignora
        # mayúsculas/tildes. Se compara el texto exacto.
        with self._sesiones() as s:
            fila = s.scalars(select(UbicacionTabla).where(
                UbicacionTabla.tipo == tipo,
                UbicacionTabla.nombre == nombre,
                UbicacionTabla.padre_id.is_(None) if padre_id is None
                else UbicacionTabla.padre_id == padre_id,
            )).first()
            return _a_entidad(fila) if fila else None

    @_manejar_errores_bd
    def existen_hijas_activas(self, padre_id: int) -> bool:
        with self._sesiones() as s:
            fila = s.scalars(select(UbicacionTabla.id).where(
                UbicacionTabla.padre_id == padre_id,
                UbicacionTabla.estado == EstadoUbicacion.ACTIVO,
            )).first()
            return fila is not None

    @_manejar_errores_bd
    def listar(self, tipo: Optional[TipoUbicacion], padre_id: Optional[int],
               estado: Optional[EstadoUbicacion], pagina: int, tamano: int,
               solo_publicadas: bool = False) -> tuple[list[DatoGeografico], int]:
        """Filtra y pagina. `estado=None` significa todos los estados.
        `solo_publicadas=True` agrega el filtro de publicación (vista de consumo
        de la API-I09, HU-04). Devuelve (elementos de la página, total)."""
        filtros = []
        if tipo is not None:
            filtros.append(UbicacionTabla.tipo == tipo)
        if padre_id is not None:
            filtros.append(UbicacionTabla.padre_id == padre_id)
        if estado is not None:
            filtros.append(UbicacionTabla.estado == estado)
        if solo_publicadas:
            filtros.append(UbicacionTabla.publicada.is_(True))

        with self._sesiones() as s:
            total = s.scalar(select(func.count()).select_from(UbicacionTabla).where(*filtros))
            filas = s.scalars(
                select(UbicacionTabla).where(*filtros)
                .order_by(UbicacionTabla.id)
                .offset((pagina - 1) * tamano)
                .limit(tamano)).all()
            return [_a_entidad(f) for f in filas], total

    # ── Escritura ─────────────────────────────────────────────

    @_manejar_errores_bd
    def crear(self, tipo: TipoUbicacion, nombre: str, codigo: str,
              padre_id: Optional[int]) -> DatoGeografico:
        with self._sesiones() as s:
            fila = UbicacionTabla(
                tipo=tipo,
                nombre=nombre,
                codigo=codigo,
                padre_id=padre_id,
                estado=EstadoUbicacion.ACTIVO,
                publicada=False,
            )
            s.add(fila)
            s.commit()
            return _a_entidad(fila)

    @_manejar_errores_bd
    def guardar(self, ubicacion: DatoGeografico) -> DatoGeografico:
        """Persiste los cambios de una ubicación existente (el tipo no se modifica)."""
        with self._sesiones() as s:
            fila = s.get(UbicacionTabla, ubicacion.id)
            if fila is None:
                raise UbicacionNoEncontrada()
            fila.nombre = ubicacion.nombre
            fila.codigo = ubicacion.codigo
            fila.padre_id = ubicacion.padre_id
            fila.estado = ubicacion.estado
            fila.publicada = ubicacion.publicada
            s.commit()
            return _a_entidad(fila)


# Instancia única compartida (Singleton simple)
ubicacion_repository = UbicacionRepository()
