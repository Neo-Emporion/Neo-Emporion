# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — HU-05 Definir formato de validación
# Única responsabilidad: guardar y recuperar el formato de cada tipo de documento.
# Solo manipula datos. Sin lógica de negocio aquí.
# Usa SQLAlchemy (por defecto SQLite en memoria, según DATABASE_URL) y devuelve
# entidades FormatoValidacion. Cualquier error de la base (SQLAlchemyError)
# -> ErrorAccesoDatosFormato (HTTP 503), y se registra en el log.
# ─────────────────────────────────────────────────────────────

import logging
from functools import wraps
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Text, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.core.database import Base, SessionLocal
from app.domain.exceptions.formato import ErrorAccesoDatosFormato
from app.domain.models.formato_validacion import FormatoValidacion

logger = logging.getLogger(__name__)


# ── Tabla "formatos_validacion" (modelo ORM de SQLAlchemy) ────
# Un formato por tipo de documento (tabla de HU-02 "tipos_documento").
class FormatoTabla(Base):
    __tablename__ = "formatos_validacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo_documento_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_documento.id"), nullable=False, unique=True)
    patron: Mapped[str] = mapped_column(Text, nullable=False)
    longitud_min: Mapped[int] = mapped_column(Integer, nullable=False)
    longitud_max: Mapped[int] = mapped_column(Integer, nullable=False)
    ejemplo: Mapped[str] = mapped_column(Text, nullable=False)


def _a_entidad(fila: FormatoTabla) -> FormatoValidacion:
    """Convierte una fila de la tabla en la entidad de dominio."""
    return FormatoValidacion(
        tipo_documento_id=fila.tipo_documento_id,
        patron=fila.patron,
        longitud_min=fila.longitud_min,
        longitud_max=fila.longitud_max,
        ejemplo=fila.ejemplo,
    )


def _manejar_errores_bd(metodo):
    """Traduce los errores de la base a errores de dominio."""
    @wraps(metodo)
    def envoltura(*args, **kwargs):
        try:
            return metodo(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.exception("Error de base de datos en %s", metodo.__qualname__)
            raise ErrorAccesoDatosFormato() from e
    return envoltura


class FormatoRepository:

    def __init__(self, sesiones: sessionmaker = SessionLocal):
        # Fábrica de sesiones de SQLAlchemy: cada operación abre y cierra su sesión
        self._sesiones = sesiones

    @_manejar_errores_bd
    def obtener_por_tipo(self, tipo_documento_id: int) -> Optional[FormatoValidacion]:
        with self._sesiones() as s:
            fila = s.scalars(select(FormatoTabla).where(
                FormatoTabla.tipo_documento_id == tipo_documento_id)).first()
            return _a_entidad(fila) if fila else None

    @_manejar_errores_bd
    def guardar(self, formato: FormatoValidacion) -> FormatoValidacion:
        """Crea el formato del tipo de documento, o lo reemplaza si ya existía."""
        with self._sesiones() as s:
            fila = s.scalars(select(FormatoTabla).where(
                FormatoTabla.tipo_documento_id == formato.tipo_documento_id)).first()
            if fila is None:
                fila = FormatoTabla(tipo_documento_id=formato.tipo_documento_id)
                s.add(fila)
            fila.patron = formato.patron
            fila.longitud_min = formato.longitud_min
            fila.longitud_max = formato.longitud_max
            fila.ejemplo = formato.ejemplo
            s.commit()
            return _a_entidad(fila)


# Instancia única compartida (Singleton simple)
formato_repository = FormatoRepository()
