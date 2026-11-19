import logging
from functools import wraps

from sqlalchemy import CheckConstraint, Enum, Integer, String, Text, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.core.database import Base, SessionLocal
from app.domain.exceptions.tipo_documento import (
    CodigoTipoDocumentoDuplicado,
    ErrorAccesoDatosTipoDocumento,
)
from app.domain.models.tipo_documento import (
    EstadoTipoDocumento,
    FiltroEstadoTipoDocumento,
    TipoDocumento,
)

logger = logging.getLogger(__name__)


class TipoDocumentoTabla(Base):
    __tablename__ = "tipos_documento"
    __table_args__ = (
        CheckConstraint(
            "length(codigo) BETWEEN 2 AND 10 AND codigo = upper(codigo)",
            name="ck_tipos_documento_codigo",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[EstadoTipoDocumento] = mapped_column(
        Enum(EstadoTipoDocumento, native_enum=False, length=10),
        nullable=False,
    )


def _a_entidad(fila: TipoDocumentoTabla) -> TipoDocumento:
    return TipoDocumento(
        id=fila.id,
        codigo=fila.codigo,
        nombre=fila.nombre,
        descripcion=fila.descripcion,
        estado=fila.estado,
    )


def _manejar_errores_bd(metodo):
    @wraps(metodo)
    def envoltura(*args, **kwargs):
        try:
            return metodo(*args, **kwargs)
        except IntegrityError as exc:
            raise CodigoTipoDocumentoDuplicado() from exc
        except SQLAlchemyError as exc:
            logger.exception("Error de base de datos en %s", metodo.__qualname__)
            raise ErrorAccesoDatosTipoDocumento() from exc
    return envoltura


class TipoDocumentoRepository:
    def __init__(self, sesiones: sessionmaker = SessionLocal):
        self._sesiones = sesiones

    @_manejar_errores_bd
    def obtener_por_id(self, tipo_documento_id: int) -> TipoDocumento | None:
        with self._sesiones() as session:
            fila = session.get(TipoDocumentoTabla, tipo_documento_id)
            return _a_entidad(fila) if fila else None

    @_manejar_errores_bd
    def buscar_por_codigo(self, codigo: str) -> TipoDocumento | None:
        with self._sesiones() as session:
            fila = session.scalars(
                select(TipoDocumentoTabla).where(
                    TipoDocumentoTabla.codigo == codigo
                )
            ).first()
            return _a_entidad(fila) if fila else None

    @_manejar_errores_bd
    def listar(
        self,
        estado: FiltroEstadoTipoDocumento,
        pagina: int,
        tamano: int,
    ) -> tuple[list[TipoDocumento], int]:
        filtros = []
        if estado != FiltroEstadoTipoDocumento.TODOS:
            filtros.append(TipoDocumentoTabla.estado == EstadoTipoDocumento(estado.value))

        with self._sesiones() as session:
            total = session.scalar(
                select(func.count()).select_from(TipoDocumentoTabla).where(*filtros)
            )
            filas = session.scalars(
                select(TipoDocumentoTabla)
                .where(*filtros)
                .order_by(TipoDocumentoTabla.id)
                .offset((pagina - 1) * tamano)
                .limit(tamano)
            ).all()
            return [_a_entidad(fila) for fila in filas], total

    @_manejar_errores_bd
    def crear(
        self,
        codigo: str,
        nombre: str,
        descripcion: str | None,
    ) -> TipoDocumento:
        with self._sesiones() as session:
            fila = TipoDocumentoTabla(
                codigo=codigo,
                nombre=nombre,
                descripcion=descripcion,
                estado=EstadoTipoDocumento.ACTIVO,
            )
            session.add(fila)
            session.commit()
            session.refresh(fila)
            return _a_entidad(fila)

    @_manejar_errores_bd
    def guardar(self, tipo_documento: TipoDocumento) -> TipoDocumento:
        with self._sesiones() as session:
            fila = session.get(TipoDocumentoTabla, tipo_documento.id)
            if fila is None:
                from app.domain.exceptions.tipo_documento import TipoDocumentoNoExiste
                raise TipoDocumentoNoExiste()
            fila.nombre = tipo_documento.nombre
            fila.descripcion = tipo_documento.descripcion
            fila.estado = tipo_documento.estado
            session.commit()
            session.refresh(fila)
            return _a_entidad(fila)


tipo_documento_repository = TipoDocumentoRepository()
