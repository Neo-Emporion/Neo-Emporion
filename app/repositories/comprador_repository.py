# ─────────────────────────────────────────────────────────────
# CAPA REPOSITORIO — HU-07 Registrar e iniciar sesión como comprador
# Única responsabilidad: guardar y recuperar compradores.
# Solo manipula datos. Sin lógica de negocio aquí.
# Usa SQLAlchemy (por defecto SQLite en memoria, según DATABASE_URL) y devuelve
# entidades Comprador. Errores de la base:
#   - correo repetido (restricción UNIQUE) -> CorreoDuplicado (HTTP 409)
#   - cualquier otro                        -> ErrorAccesoDatosComprador (HTTP 503), con log
# ─────────────────────────────────────────────────────────────

import logging
from functools import wraps
from typing import Optional

from sqlalchemy import Enum, Integer, String, Text, exists, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.core.database import Base, SessionLocal
from app.domain.exceptions.comprador import CorreoDuplicado, ErrorAccesoDatosComprador
from app.domain.models.comprador import Comprador, EstadoCuenta

logger = logging.getLogger(__name__)


# ── Tabla "compradores" (modelo ORM de SQLAlchemy) ────────────
class CompradorTabla(Base):
    __tablename__ = "compradores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # id de un tipo de documento del módulo Parametrización. Sin llave foránea: cada
    # módulo es dueño de sus datos; el tipo se valida por IConsultaTiposDocumento (API-I08).
    tipo_documento_id: Mapped[int] = mapped_column(Integer, nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(50), nullable=False)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    # RN-51: un correo solo puede tener una cuenta (también lo valida el servicio)
    correo: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    # Solo la contraseña cifrada; la original nunca se guarda (RN-55)
    contrasena_cifrada: Mapped[str] = mapped_column(Text, nullable=False)
    estado: Mapped[EstadoCuenta] = mapped_column(
        Enum(EstadoCuenta, native_enum=False, length=11, create_constraint=True),
        nullable=False)


def _a_entidad(fila: CompradorTabla) -> Comprador:
    """Convierte una fila de la tabla en la entidad de dominio."""
    return Comprador(
        id=fila.id,
        tipo_documento_id=fila.tipo_documento_id,
        numero_documento=fila.numero_documento,
        nombres=fila.nombres,
        apellidos=fila.apellidos,
        correo=fila.correo,
        contrasena_cifrada=fila.contrasena_cifrada,
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
                # Dos registros a la vez con el mismo correo: la base rechaza el segundo
                raise CorreoDuplicado() from e
            logger.exception("Restricción de base de datos en %s", metodo.__qualname__)
            raise ErrorAccesoDatosComprador() from e
        except (SQLAlchemyError, LookupError, ValueError) as e:
            # LookupError/ValueError: un estado guardado que no está en EstadoCuenta
            logger.exception("Error de base de datos en %s", metodo.__qualname__)
            raise ErrorAccesoDatosComprador() from e
    return envoltura


class CompradorRepository:

    def __init__(self, sesiones: sessionmaker = SessionLocal):
        # Fábrica de sesiones de SQLAlchemy: cada operación abre y cierra su sesión
        self._sesiones = sesiones

    @_manejar_errores_bd
    def buscar_por_correo(self, correo: str) -> Optional[Comprador]:
        with self._sesiones() as s:
            fila = s.scalars(select(CompradorTabla).where(
                CompradorTabla.correo == correo)).first()
            return _a_entidad(fila) if fila else None

    @_manejar_errores_bd
    def crear(self, comprador: Comprador) -> Comprador:
        with self._sesiones() as s:
            fila = CompradorTabla(
                tipo_documento_id=comprador.tipo_documento_id,
                numero_documento=comprador.numero_documento,
                nombres=comprador.nombres,
                apellidos=comprador.apellidos,
                correo=comprador.correo,
                contrasena_cifrada=comprador.contrasena_cifrada,
                estado=comprador.estado,
            )
            s.add(fila)
            s.commit()
            return _a_entidad(fila)

    @_manejar_errores_bd
    def existe_con_tipo_documento(self, tipo_documento_id: int,
                                  solo_activos: bool = False) -> bool:
        """True si hay compradores registrados con el tipo de documento.
        Con solo_activos=True cuenta solo las cuentas ACTIVA."""
        filtros = [CompradorTabla.tipo_documento_id == tipo_documento_id]
        if solo_activos:
            filtros.append(CompradorTabla.estado == EstadoCuenta.ACTIVA)
        with self._sesiones() as s:
            return bool(s.scalar(select(exists().where(*filtros))))


# Instancia única compartida (Singleton simple)
comprador_repository = CompradorRepository()
