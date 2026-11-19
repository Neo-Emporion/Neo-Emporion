from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.exceptions.tipo_documento import TipoDocumentoEnUso


class EstadoTipoDocumento(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"


class FiltroEstadoTipoDocumento(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    TODOS = "TODOS"


class TipoDocumentoCreate(BaseModel):
    codigo: str = Field(
        ..., min_length=2, max_length=10,
        description="Código único de 2 a 10 caracteres en mayúscula",
        json_schema_extra={"example": "NIT"},
    )
    nombre: str = Field(
        ..., min_length=1, max_length=80,
        description="Nombre del tipo de documento",
        json_schema_extra={"example": "Número de Identificación Tributaria"},
    )
    descripcion: Optional[str] = Field(
        default=None,
        description="Descripción opcional del tipo de documento",
    )

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("codigo")
    @classmethod
    def codigo_en_mayuscula(cls, value: str) -> str:
        if not value.isupper():
            raise ValueError("El código debe estar en mayúscula")
        return value

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, value: str) -> str:
        if not value:
            raise ValueError("El nombre es obligatorio")
        return value


class TipoDocumentoUpdate(BaseModel):
    nombre: str = Field(
        ..., min_length=1, max_length=80,
        description="Nuevo nombre del tipo de documento",
    )
    descripcion: str = Field(
        ...,
        min_length=1,
        description="Nueva descripción del tipo de documento",
    )

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, value: str) -> str:
        if not value:
            raise ValueError("El nombre es obligatorio")
        return value


class TipoDocumentoResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    estado: EstadoTipoDocumento

    model_config = ConfigDict(from_attributes=True)


class TipoDocumentoListadoItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    estado: EstadoTipoDocumento

    model_config = ConfigDict(from_attributes=True)


class TipoDocumentoDesactivado(BaseModel):
    id: int
    estado: EstadoTipoDocumento


class TipoDocumento:
    def __init__(
        self,
        id: int,
        codigo: str,
        nombre: str,
        descripcion: Optional[str] = None,
        estado: EstadoTipoDocumento = EstadoTipoDocumento.ACTIVO,
    ):
        self.id = id
        self.codigo = codigo
        self.nombre = nombre
        self.descripcion = descripcion
        self.estado = estado

    def editar(
        self,
        nombre: str,
        descripcion: str,
    ) -> None:
        self.nombre = nombre
        self.descripcion = descripcion

    def desactivar(self, esta_en_uso: bool) -> None:
        if esta_en_uso:
            raise TipoDocumentoEnUso()
        self.estado = EstadoTipoDocumento.INACTIVO

    def to_response(self) -> dict:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "estado": self.estado,
        }
