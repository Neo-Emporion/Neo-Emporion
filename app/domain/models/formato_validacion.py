# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — HU-05 Definir formato de validación de tipo de documento
# MOD-01 Parametrización / SUB-01 Catálogos de Identificación
# Define la entidad FormatoValidacion, sus schemas y sus reglas de negocio.
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.domain.exceptions.formato import (
    EjemploNoCumplePatron,
    FormatoConRegistros,
    LongitudesInconsistentes,
    PatronInvalido,
)


# Mayor entero que cabe en la base (entero de 64 bits)
ENTERO_MAXIMO = 2**63 - 1


# ── Schema de ENTRADA: definir formato (API-G08) ──────────────
class FormatoCreate(BaseModel):
    patron: str = Field(..., min_length=1,
                        description="Expresión regular que valida el número de documento")
    # La HU exige que la longitud mínima sea mayor que 0. El tope ENTERO_MAXIMO es el
    # mayor entero que cabe en la base: uno mayor responde 400 en lugar de un error interno.
    longitud_min: int = Field(..., gt=0, le=ENTERO_MAXIMO, description="Longitud mínima del número")
    longitud_max: int = Field(..., le=ENTERO_MAXIMO, description="Longitud máxima del número")
    ejemplo: str = Field(..., min_length=1,
                         description="Ejemplo válido para mostrar al usuario")

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"patron": "^[0-9]{9}-[0-9]$", "longitud_min": 11, "longitud_max": 11,
         "ejemplo": "900123456-7"}
    ]})


# ── Schemas de SALIDA ─────────────────────────────────────────
class FormatoDatos(BaseModel):
    patron: str
    longitud_min: int
    longitud_max: int
    ejemplo: str


class FormatoTipoDocumentoResponse(BaseModel):
    """Tipo de documento con su formato asociado (estructura de la HU-05)."""
    id: int
    codigo: str
    formato: FormatoDatos


# ── Modelo interno del dominio (la "entidad real") ────────────
class FormatoValidacion:
    def __init__(self, tipo_documento_id: int, patron: str, longitud_min: int,
                 longitud_max: int, ejemplo: str):
        self.tipo_documento_id = tipo_documento_id
        self.patron = patron
        self.longitud_min = longitud_min
        self.longitud_max = longitud_max
        self.ejemplo = ejemplo

    # REGLA: el formato debe ser consistente antes de guardarse.
    # Orden: patrón evaluable -> longitudes coherentes -> ejemplo que cumple ambos.
    @staticmethod
    def crear(tipo_documento_id: int, patron: str, longitud_min: int,
              longitud_max: int, ejemplo: str) -> "FormatoValidacion":
        try:
            re.compile(patron)
        except (re.error, OverflowError, RecursionError):
            # re.error: sintaxis inválida (ej. "[0-9{"); OverflowError: repetición
            # demasiado grande (ej. "a{99999999999}"); RecursionError: anidamiento extremo
            raise PatronInvalido() from None
        if longitud_min > longitud_max:
            raise LongitudesInconsistentes()
        formato = FormatoValidacion(tipo_documento_id, patron, longitud_min, longitud_max,
                                    ejemplo)
        if not formato.numero_es_valido(ejemplo):
            raise EjemploNoCumplePatron()
        return formato

    # Un número cumple el formato si el patrón coincide con el número COMPLETO
    # y su largo está entre la longitud mínima y la máxima.
    # Lo usarán los registros de compradores (HU-07) y vendedores (HU-08).
    # TODO(pendiente): un patrón con backtracking catastrófico (ej. "^(a+)+$") puede
    # tardar mucho con ciertos números. Hoy solo lo define el Administrador; revisarlo
    # (tope de largo o tiempo máximo de evaluación) al conectar HU-07 y HU-08.
    def numero_es_valido(self, numero: str) -> bool:
        return (self.longitud_min <= len(numero) <= self.longitud_max
                and re.fullmatch(self.patron, numero) is not None)

    # REGLA DE NEGOCIO RN-50: si ya había un formato definido y existen registros
    # asociados al tipo, el formato no puede modificarse. La primera vez se permite.
    @staticmethod
    def verificar_modificacion(existente: Optional["FormatoValidacion"],
                               tiene_registros: bool) -> None:
        if existente is not None and tiene_registros:
            raise FormatoConRegistros()

    def to_response(self) -> dict:
        return {
            "patron": self.patron,
            "longitud_min": self.longitud_min,
            "longitud_max": self.longitud_max,
            "ejemplo": self.ejemplo,
        }
