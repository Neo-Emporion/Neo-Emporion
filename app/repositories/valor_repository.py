# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — HU-03 Gestionar catálogos transaccionales
# Única responsabilidad: guardar y recuperar valores paramétricos.
# Solo manipula datos. Sin lógica de negocio aquí.
# Usa SQLAlchemy (por defecto SQLite en memoria, según DATABASE_URL) y devuelve
# entidades ValorParametrico.
# - Par (categoria, codigo) repetido rechazado por la base (UNIQUE) -> ValorDuplicado (HTTP 409)
# - Cualquier otro error de la base, o un dato guardado que no se puede leer
#   -> ErrorAccesoDatos (HTTP 503), y se registra en el log
# ─────────────────────────────────────────────────────────────

import logging
from functools import wraps
from typing import Optional

from sqlalchemy import Enum, Integer, String, UniqueConstraint, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.core.database import Base, SessionLocal
from app.domain.exceptions.valor import ErrorAccesoDatos, ValorDuplicado, ValorNoEncontrado
from app.domain.models.valor_parametrico import (
    LARGO_MAXIMO_CODIGO,
    LARGO_MAXIMO_DESCRIPCION,
    LARGO_MAXIMO_NOMBRE,
    CategoriaValor,
    EstadoValor,
    ValorParametrico,
)

logger = logging.getLogger(__name__)


# ── Tabla "valores_parametricos" (modelo ORM de SQLAlchemy) ───
class ValorTabla(Base):
    __tablename__ = "valores_parametricos"
    # Regla de la HU: el par (categoria, codigo) no puede repetirse
    __table_args__ = (UniqueConstraint("categoria", "codigo", name="uq_valor_categoria_codigo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # create_constraint: la base rechaza cualquier categoría o estado fuera del Enum
    categoria: Mapped[CategoriaValor] = mapped_column(
        Enum(CategoriaValor, native_enum=False, length=20, create_constraint=True),
        nullable=False)
    codigo: Mapped[str] = mapped_column(String(LARGO_MAXIMO_CODIGO), nullable=False)
    nombre: Mapped[str] = mapped_column(String(LARGO_MAXIMO_NOMBRE), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(
        String(LARGO_MAXIMO_DESCRIPCION), nullable=True)
    estado: Mapped[EstadoValor] = mapped_column(
        Enum(EstadoValor, native_enum=False, length=10, create_constraint=True),
        nullable=False)


def _a_entidad(fila: ValorTabla) -> ValorParametrico:
    """Convierte una fila de la tabla en la entidad de dominio."""
    return ValorParametrico(
        id=fila.id,
        categoria=fila.categoria,
        codigo=fila.codigo,
        nombre=fila.nombre,
        descripcion=fila.descripcion,
        estado=fila.estado,
    )


def _manejar_errores_bd(metodo):
    """Traduce los errores de SQLAlchemy a errores de dominio."""
    @wraps(metodo)
    def envoltura(*args, **kwargs):
        try:
            return metodo(*args, **kwargs)
        except IntegrityError as e:
            if "UNIQUE" in str(e.orig).upper():
                # Si dos peticiones llegan a la vez con el mismo (categoria, codigo),
                # la base rechaza la segunda. Es un duplicado, no una falla.
                raise ValorDuplicado() from e
            # Otra restricción (NOT NULL, CHECK...): es una falla, no un duplicado
            logger.exception("Restricción de base de datos en %s", metodo.__qualname__)
            raise ErrorAccesoDatos() from e
        except SQLAlchemyError as e:
            logger.exception("Error de base de datos en %s", metodo.__qualname__)
            raise ErrorAccesoDatos() from e
        except (LookupError, ValueError) as e:
            # Un dato guardado que no corresponde al Enum no se puede leer
            logger.exception("Dato inválido en la base en %s", metodo.__qualname__)
            raise ErrorAccesoDatos() from e
    return envoltura


class ValorRepository:

    def __init__(self, sesiones: sessionmaker = SessionLocal):
        # Fábrica de sesiones de SQLAlchemy: cada operación abre y cierra su sesión
        self._sesiones = sesiones

    # ── Consultas ─────────────────────────────────────────────

    @_manejar_errores_bd
    def obtener_por_id(self, id: int) -> Optional[ValorParametrico]:
        with self._sesiones() as s:
            fila = s.get(ValorTabla, id)
            return _a_entidad(fila) if fila else None

    @_manejar_errores_bd
    def buscar_por_categoria_codigo(self, categoria: CategoriaValor,
                                    codigo: str) -> Optional[ValorParametrico]:
        # TODO(pendiente): la HU no dice si "cop" y "COP" son el mismo código.
        # Se compara el texto exacto.
        with self._sesiones() as s:
            fila = s.scalars(select(ValorTabla).where(
                ValorTabla.categoria == categoria,
                ValorTabla.codigo == codigo,
            )).first()
            return _a_entidad(fila) if fila else None

    @_manejar_errores_bd
    def listar(self, categoria: CategoriaValor,
               estado: Optional[EstadoValor]) -> list[ValorParametrico]:
        """Valores de una categoría. `estado=None` significa todos los estados."""
        filtros = [ValorTabla.categoria == categoria]
        if estado is not None:
            filtros.append(ValorTabla.estado == estado)
        with self._sesiones() as s:
            filas = s.scalars(select(ValorTabla).where(*filtros).order_by(ValorTabla.id)).all()
            return [_a_entidad(f) for f in filas]

    # ── Escritura ─────────────────────────────────────────────

    @_manejar_errores_bd
    def crear(self, categoria: CategoriaValor, codigo: str, nombre: str) -> ValorParametrico:
        with self._sesiones() as s:
            fila = ValorTabla(
                categoria=categoria,
                codigo=codigo,
                nombre=nombre,
                descripcion=None,
                estado=EstadoValor.ACTIVO,
            )
            s.add(fila)
            s.commit()
            return _a_entidad(fila)

    @_manejar_errores_bd
    def guardar(self, valor: ValorParametrico) -> ValorParametrico:
        """Persiste los cambios de un valor existente (categoría y código no se modifican)."""
        with self._sesiones() as s:
            fila = s.get(ValorTabla, valor.id)
            if fila is None:
                raise ValorNoEncontrado()
            fila.nombre = valor.nombre
            fila.descripcion = valor.descripcion
            fila.estado = valor.estado
            s.commit()
            return _a_entidad(fila)


# Instancia única compartida (Singleton simple)
valor_repository = ValorRepository()
