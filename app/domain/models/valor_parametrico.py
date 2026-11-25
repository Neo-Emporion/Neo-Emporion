# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — HU-03 Gestionar catálogos transaccionales
# MOD-01 Parametrización / SUB-03 Catálogos Transaccionales
# Define la entidad ValorParametrico, sus schemas y sus reglas de negocio.
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.exceptions.valor import CategoriaInvalida, ValorEnUso


# ── Valores permitidos ────────────────────────────────────────
class CategoriaValor(str, Enum):
    ESTADO = "ESTADO"
    MONEDA = "MONEDA"
    UNIDAD_MEDIDA = "UNIDAD_MEDIDA"
    METODO_PAGO = "METODO_PAGO"


class EstadoValor(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


class FiltroEstadoValor(str, Enum):
    """Valores del filtro `estado` del listado. Por defecto ACTIVO (RN-49)."""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    TODOS = "TODOS"


# Largos máximos. La HU fija `nombre` (80); `codigo` y `descripcion` no los
# define: TODO(pendiente), ver "Registro de cambios" de la HU-03.
LARGO_MAXIMO_NOMBRE = 80
LARGO_MAXIMO_CODIGO = 50
LARGO_MAXIMO_DESCRIPCION = 255

CATEGORIAS = [c.value for c in CategoriaValor]


# ── Schema de ENTRADA: registrar (API-G09) ────────────────────
# `categoria` se recibe sin validar el tipo y la valida la entidad, para responder
# siempre el mensaje exacto de la HU ("La categoría indicada no es válida", Caso 6),
# aunque llegue un número, null o un texto que no es una categoría.
class ValorCreate(BaseModel):
    categoria: Any = Field(..., description="ESTADO, MONEDA, UNIDAD_MEDIDA o METODO_PAGO",
                           json_schema_extra={"type": "string", "enum": CATEGORIAS})
    codigo: str = Field(..., min_length=1, max_length=LARGO_MAXIMO_CODIGO,
                        description="Código del valor, único dentro de su categoría")
    nombre: str = Field(..., min_length=1, max_length=LARGO_MAXIMO_NOMBRE,
                        description="Nombre visible (máx. 80 caracteres)")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"examples": [
            {"categoria": "METODO_PAGO", "codigo": "PSE", "nombre": "Pago por PSE"}
        ]},
    )


# ── Schema de ENTRADA: editar (API-G10) ───────────────────────
# `categoria` y `codigo` NO están aquí porque no se modifican; si se envían, se ignoran.
# La HU marca `nombre` y `descripcion` como obligatorios: los dos deben venir en
# el body (`descripcion` puede ser null).
class ValorUpdate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=LARGO_MAXIMO_NOMBRE,
                        description="Nuevo nombre (máx. 80 caracteres)")
    descripcion: Optional[str] = Field(..., max_length=LARGO_MAXIMO_DESCRIPCION,
                                       description="Nueva descripción (obligatoria en el "
                                                   "body; puede ser null)")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={"examples": [
            {"nombre": "Pago en línea por PSE", "descripcion": "Débito desde cuenta bancaria"}
        ]},
    )


# ── Schemas de SALIDA ─────────────────────────────────────────
class ValorResponse(BaseModel):
    """Valor paramétrico (registro, edición y listado).
    Igual a los ejemplos de la HU: no incluye `descripcion`."""
    id: int
    categoria: CategoriaValor
    codigo: str
    nombre: str
    estado: EstadoValor

    model_config = ConfigDict(from_attributes=True)


class ValorDesactivado(BaseModel):
    id: int
    estado: EstadoValor


# ── Modelo interno del dominio (la "entidad real") ────────────
class ValorParametrico:
    def __init__(self, id: int, categoria: CategoriaValor, codigo: str, nombre: str,
                 descripcion: Optional[str] = None,
                 estado: EstadoValor = EstadoValor.ACTIVO):
        self.id = id
        self.categoria = categoria
        self.codigo = codigo
        self.nombre = nombre
        # Se registra sin descripción; se puede editar con el PUT (API-G10)
        self.descripcion = descripcion
        self.estado = estado

    # REGLA: la categoría debe ser una de las cuatro de la HU.
    # Se ignoran los espacios al inicio y al final (igual en el POST y en el GET).
    @staticmethod
    def validar_categoria(categoria: Any) -> CategoriaValor:
        if not isinstance(categoria, str):
            raise CategoriaInvalida()
        try:
            return CategoriaValor(categoria.strip())
        except ValueError:
            raise CategoriaInvalida() from None

    @property
    def esta_activo(self) -> bool:
        return self.estado == EstadoValor.ACTIVO

    # Editar: solo nombre y descripción; categoría, código y estado se conservan.
    # Una descripción vacía se guarda como "sin descripción" (None).
    def editar(self, nombre: str, descripcion: Optional[str]) -> None:
        self.nombre = nombre
        self.descripcion = descripcion or None

    # REGLA DE NEGOCIO RN-46: no desactivar un valor que usa otro módulo.
    # Si ya está INACTIVO no hay nada que desactivar: se deja igual (sin RN-46).
    def desactivar(self, esta_en_uso: bool) -> None:
        if not self.esta_activo:
            return
        if esta_en_uso:
            raise ValorEnUso()
        self.estado = EstadoValor.INACTIVO

    def to_response(self) -> dict:
        # `descripcion` no se expone: los ejemplos de la HU no la incluyen
        return {
            "id": self.id,
            "categoria": self.categoria,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "estado": self.estado,
        }
