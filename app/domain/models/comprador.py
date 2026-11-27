# ─────────────────────────────────────────────────────────────
# CAPA DOMINIO — HU-07 Registrar e iniciar sesión como comprador
# MOD-02 Usuarios y Compradores / SUB-04 Registro y Autenticación
# Define la entidad Comprador, sus schemas y sus reglas de negocio.
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

import re
import string
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.exceptions.comprador import (
    ContrasenaInsegura,
    CuentaDesactivada,
    DocumentoNoCumpleFormato,
    TipoDocumentoNoValido,
)

# Mayor entero que cabe en la base (entero de 64 bits)
ENTERO_MAXIMO = 2**63 - 1

# RN-55: mínimo 8 caracteres, con mayúscula, minúscula y número
LONGITUD_MINIMA_CONTRASENA = 8

# Formato básico de correo: algo@dominio.ext, sin espacios
PATRON_CORREO = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


class EstadoCuenta(str, Enum):
    ACTIVA = "ACTIVA"
    DESACTIVADA = "DESACTIVADA"


def _recortar(valor: Any) -> Any:
    """Quita espacios al inicio y al final de los textos."""
    return valor.strip() if isinstance(valor, str) else valor


def _normalizar_correo(valor: Any) -> Any:
    """El correo se compara sin espacios y en minúscula (Laura@x.com = laura@x.com)."""
    return valor.strip().lower() if isinstance(valor, str) else valor


# ── Schema de ENTRADA: registrar comprador (API-G14) ──────────
class CompradorCreate(BaseModel):
    tipo_documento_id: int = Field(..., gt=0, le=ENTERO_MAXIMO,
                                   description="Tipo de documento activo (HU-02)")
    numero_documento: str = Field(..., min_length=1, max_length=50,
                                  description="Número que cumple el formato del tipo (HU-05)")
    nombres: str = Field(..., min_length=1, max_length=100, description="Nombres del comprador")
    apellidos: str = Field(..., min_length=1, max_length=100,
                           description="Apellidos del comprador")
    correo: str = Field(..., max_length=254, description="Correo único con formato válido")
    # La contraseña NO se recorta: los espacios forman parte de ella.
    contrasena: str = Field(..., description="Mínimo 8 caracteres, con mayúscula, "
                                             "minúscula y número (RN-55)")

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"tipo_documento_id": 1, "numero_documento": "1098765432", "nombres": "Laura",
         "apellidos": "Gómez", "correo": "laura.gomez@correo.com", "contrasena": "Segura123"}
    ]})

    _recortar_textos = field_validator("numero_documento", "nombres", "apellidos",
                                       mode="before")(_recortar)
    _normalizar = field_validator("correo", mode="before")(_normalizar_correo)

    @field_validator("correo")
    @classmethod
    def correo_con_formato(cls, valor: str) -> str:
        if not PATRON_CORREO.fullmatch(valor):
            raise ValueError("El correo no tiene un formato válido")
        return valor


# ── Schema de ENTRADA: iniciar sesión (API-G15) ───────────────
class SesionCreate(BaseModel):
    correo: str = Field(..., description="Correo registrado")
    contrasena: str = Field(..., description="Contraseña de la cuenta")

    model_config = ConfigDict(json_schema_extra={"examples": [
        {"correo": "laura.gomez@correo.com", "contrasena": "Segura123"}
    ]})

    _normalizar = field_validator("correo", mode="before")(_normalizar_correo)


# ── Schemas de SALIDA ─────────────────────────────────────────
class CompradorResponse(BaseModel):
    """Comprador registrado. Nunca incluye la contraseña."""
    id: int
    nombres: str
    apellidos: str
    correo: str
    estado: EstadoCuenta


class SesionResponse(BaseModel):
    token: str
    tipo: str = "Bearer"
    expira_en: int = Field(..., description="Segundos hasta que el token expira")


# ── Modelo interno del dominio (la "entidad real") ────────────
class Comprador:
    def __init__(self, id: Optional[int], tipo_documento_id: int, numero_documento: str,
                 nombres: str, apellidos: str, correo: str, contrasena_cifrada: str,
                 estado: EstadoCuenta = EstadoCuenta.ACTIVA):
        self.id = id
        self.tipo_documento_id = tipo_documento_id
        self.numero_documento = numero_documento
        self.nombres = nombres
        self.apellidos = apellidos
        self.correo = correo
        self.contrasena_cifrada = contrasena_cifrada
        self.estado = estado

    # REGLA DE NEGOCIO RN-55: la contraseña debe cumplir los requisitos mínimos
    # ANTES de cifrarse y almacenarse.
    @staticmethod
    def validar_contrasena(contrasena: str) -> None:
        if (len(contrasena) < LONGITUD_MINIMA_CONTRASENA
                or not any(c.isupper() for c in contrasena)
                or not any(c.islower() for c in contrasena)
                or not any(c in string.digits for c in contrasena)):
            raise ContrasenaInsegura()

    # El documento debe ser de un tipo activo y cumplir su formato (HU-02 y HU-05).
    # El servicio consulta al módulo Parametrización y le entrega aquí las respuestas.
    @staticmethod
    def verificar_documento(tipo_activo: bool, cumple_formato: bool) -> None:
        if not tipo_activo:
            raise TipoDocumentoNoValido()
        if not cumple_formato:
            raise DocumentoNoCumpleFormato()

    # Todo comprador nuevo queda con la cuenta ACTIVA.
    @staticmethod
    def registrar(tipo_documento_id: int, numero_documento: str, nombres: str,
                  apellidos: str, correo: str, contrasena_cifrada: str) -> "Comprador":
        return Comprador(id=None, tipo_documento_id=tipo_documento_id,
                         numero_documento=numero_documento, nombres=nombres,
                         apellidos=apellidos, correo=correo,
                         contrasena_cifrada=contrasena_cifrada, estado=EstadoCuenta.ACTIVA)

    # REGLA DE NEGOCIO RN-52: una cuenta desactivada no puede iniciar sesión.
    def verificar_puede_iniciar_sesion(self) -> None:
        if self.estado != EstadoCuenta.ACTIVA:
            raise CuentaDesactivada()

    def to_response(self) -> dict:
        # La contraseña (ni cifrada) nunca sale en las respuestas.
        # tipo_documento_id y numero_documento se guardan, pero el ejemplo de la HU no los trae.
        return {
            "id": self.id,
            "nombres": self.nombres,
            "apellidos": self.apellidos,
            "correo": self.correo,
            "estado": self.estado,
        }
