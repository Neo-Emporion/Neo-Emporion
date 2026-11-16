# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — HU-01 Gestionar catálogo geográfico
# MOD-01 Parametrización / SUB-02 Catálogos Geográficos
# Define la entidad DatoGeografico, sus schemas y sus reglas de negocio.
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.exceptions.ubicacion import DesactivacionNoPermitida, JerarquiaInvalida


# ── Valores permitidos ────────────────────────────────────────
class TipoUbicacion(str, Enum):
    PAIS = "PAIS"
    DEPARTAMENTO = "DEPARTAMENTO"
    CIUDAD = "CIUDAD"


class EstadoUbicacion(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


class FiltroEstado(str, Enum):
    """Valores del filtro `estado` del listado. Por defecto ACTIVO."""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    TODOS = "TODOS"


# REGLA DE NEGOCIO (jerarquía): tipo de padre que exige cada tipo.
# PAIS no tiene padre; DEPARTAMENTO cuelga de PAIS; CIUDAD cuelga de DEPARTAMENTO.
PADRE_REQUERIDO: dict[TipoUbicacion, Optional[TipoUbicacion]] = {
    TipoUbicacion.PAIS: None,
    TipoUbicacion.DEPARTAMENTO: TipoUbicacion.PAIS,
    TipoUbicacion.CIUDAD: TipoUbicacion.DEPARTAMENTO,
}


# Largo máximo del código (la HU no lo fija; coincide con la columna de la tabla)
LARGO_MAXIMO_CODIGO = 50


# ── Schema de ENTRADA: registrar (API-G01) ────────────────────
class UbicacionCreate(BaseModel):
    tipo: TipoUbicacion = Field(..., description="PAIS, DEPARTAMENTO o CIUDAD")
    nombre: str = Field(..., min_length=1, max_length=100,
                        description="Nombre de la ubicación (máx. 100 caracteres)")
    codigo: str = Field(..., min_length=1, max_length=LARGO_MAXIMO_CODIGO,
                        description="Código único de la ubicación (ej. código DANE)")
    padre_id: Optional[int] = Field(
        None, description="Obligatorio para DEPARTAMENTO y CIUDAD; no permitido para PAIS")

    model_config = ConfigDict(
        str_strip_whitespace=True,  # "  Bucaramanga " se guarda como "Bucaramanga"
        json_schema_extra={"examples": [
            {"tipo": "CIUDAD", "nombre": "Bucaramanga", "codigo": "68001", "padre_id": 68}
        ]},
    )


# ── Schema de ENTRADA: editar (API-G02) ───────────────────────
# El `tipo` NO está aquí porque no puede modificarse. Si el cliente lo envía, se ignora.
# La HU marca nombre, codigo y padre_id como obligatorios al editar: los tres deben
# venir en el body. Para un PAIS, padre_id se envía como null.
class UbicacionUpdate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100,
                        description="Nuevo nombre (máx. 100 caracteres)")
    codigo: str = Field(..., min_length=1, max_length=LARGO_MAXIMO_CODIGO,
                        description="Nuevo código único")
    padre_id: Optional[int] = Field(
        ..., description="Nuevo padre (obligatorio en el body). "
                         "DEPARTAMENTO y CIUDAD: id del padre; PAIS: null")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"examples": [
            {"nombre": "Bucaramanga", "codigo": "68001", "padre_id": 68}
        ]},
    )


# ── Schemas de SALIDA ─────────────────────────────────────────
class UbicacionResponse(BaseModel):
    """Ubicación completa (registro y edición)."""
    id: int
    tipo: TipoUbicacion
    nombre: str
    codigo: str
    padre_id: Optional[int]
    estado: EstadoUbicacion
    publicada: bool

    model_config = ConfigDict(from_attributes=True)


class UbicacionListadoItem(BaseModel):
    """Elemento del listado. La HU-01 no incluye `publicada` en el listado."""
    id: int
    tipo: TipoUbicacion
    nombre: str
    codigo: str
    padre_id: Optional[int]
    estado: EstadoUbicacion

    model_config = ConfigDict(from_attributes=True)


class UbicacionListado(BaseModel):
    pagina: int
    tamano: int
    total: int
    ubicaciones: list[UbicacionListadoItem]


class UbicacionDesactivada(BaseModel):
    id: int
    estado: EstadoUbicacion


# ── Modelo interno del dominio (la "entidad real") ────────────
class DatoGeografico:
    def __init__(self, id: int, tipo: TipoUbicacion, nombre: str, codigo: str,
                 padre_id: Optional[int],
                 estado: EstadoUbicacion = EstadoUbicacion.ACTIVO,
                 publicada: bool = False):
        self.id = id
        self.tipo = tipo
        self.nombre = nombre
        self.codigo = codigo
        self.padre_id = padre_id
        self.estado = estado
        # Por defecto False: una ubicación nueva no está publicada; se publica con HU-04.
        self.publicada = publicada

    # REGLA DE NEGOCIO: jerarquía PAIS -> DEPARTAMENTO -> CIUDAD
    @staticmethod
    def validar_jerarquia(tipo: TipoUbicacion, padre_id: Optional[int],
                          padre: Optional["DatoGeografico"]) -> None:
        """Valida que el padre sea coherente con el tipo.

        - PAIS: no admite padre_id.
        - DEPARTAMENTO: padre_id obligatorio y el padre debe ser un PAIS.
        - CIUDAD: padre_id obligatorio y el padre debe ser un DEPARTAMENTO.
        `padre` es la ubicación encontrada con `padre_id` (None si no existe).
        """
        tipo_padre = PADRE_REQUERIDO[tipo]
        if tipo_padre is None:
            if padre_id is not None:
                raise JerarquiaInvalida()
            return
        if padre_id is None or padre is None or padre.tipo != tipo_padre:
            raise JerarquiaInvalida()
        # TODO(pendiente): la HU no dice si el padre puede estar INACTIVO. No se valida.

    # Editar: el tipo no cambia; los nuevos datos deben respetar la jerarquía.
    # La duplicidad la valida el servicio, porque necesita consultar el repositorio.
    def editar(self, nombre: str, codigo: str, padre_id: Optional[int],
               padre: Optional["DatoGeografico"]) -> None:
        self.validar_jerarquia(self.tipo, padre_id, padre)
        self.nombre = nombre
        self.codigo = codigo
        self.padre_id = padre_id

    # REGLA DE NEGOCIO RN-47: no desactivar con direcciones activas
    # (ni con ubicaciones hijas activas, según el flujo de la HU-01).
    def desactivar(self, tiene_direcciones_activas: bool, tiene_hijas_activas: bool) -> None:
        if tiene_direcciones_activas or tiene_hijas_activas:
            raise DesactivacionNoPermitida()
        self.estado = EstadoUbicacion.INACTIVO

    def to_response(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "nombre": self.nombre,
            "codigo": self.codigo,
            "padre_id": self.padre_id,
            "estado": self.estado,
            "publicada": self.publicada,
        }
