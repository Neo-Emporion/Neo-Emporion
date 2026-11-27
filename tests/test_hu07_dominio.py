# HU-07 — pruebas unitarias de las reglas de dominio y del cifrado/token
# (correo único se prueba en test_hu07_compradores.py: necesita el repositorio)

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from pydantic import ValidationError

from app.core import autenticacion
from app.core.autenticacion import (
    cifrar_contrasena,
    crear_token,
    decodificar_token,
    verificar_contrasena,
)
from app.domain.exceptions.comprador import (
    ContrasenaInsegura,
    CuentaDesactivada,
    DocumentoNoCumpleFormato,
    TipoDocumentoNoValido,
)
from app.domain.models.comprador import Comprador, CompradorCreate, EstadoCuenta, SesionCreate


def nuevo_comprador(estado=EstadoCuenta.ACTIVA):
    return Comprador(id=1, tipo_documento_id=1, numero_documento="1098765432",
                     nombres="Laura", apellidos="Gómez", correo="laura.gomez@correo.com",
                     contrasena_cifrada="pbkdf2_sha256$1$00$00", estado=estado)


# ── RN-55: requisitos mínimos de la contraseña ────────────────
@pytest.mark.parametrize("contrasena", ["Segura123", "Ñandú2024", "Aa1aaaaa"])
def test_rn55_contrasena_valida(contrasena):
    Comprador.validar_contrasena(contrasena)  # no lanza error


@pytest.mark.parametrize("contrasena", ["abc123", "Aa1aaaa", "segura123", "SEGURA123",
                                        "SeguraSegura", ""])
def test_rn55_contrasena_insegura(contrasena):
    with pytest.raises(ContrasenaInsegura) as e:
        Comprador.validar_contrasena(contrasena)
    assert e.value.mensaje == "La contraseña no cumple los requisitos mínimos de seguridad"


# ── Documento: tipo activo y formato (HU-02 / HU-05) ──────────
def test_documento_valido():
    Comprador.verificar_documento(tipo_activo=True, cumple_formato=True)


def test_documento_de_tipo_no_valido():
    with pytest.raises(TipoDocumentoNoValido):
        Comprador.verificar_documento(tipo_activo=False, cumple_formato=False)


def test_documento_que_no_cumple_formato():
    with pytest.raises(DocumentoNoCumpleFormato) as e:
        Comprador.verificar_documento(tipo_activo=True, cumple_formato=False)
    assert e.value.mensaje == "El número de documento no cumple el formato del tipo seleccionado"


# ── Estado de la cuenta (RN-52) ───────────────────────────────
def test_registrar_crea_cuenta_activa():
    c = Comprador.registrar(1, "1098765432", "Laura", "Gómez", "laura@correo.com", "x")
    assert c.estado == EstadoCuenta.ACTIVA
    assert c.id is None


def test_rn52_cuenta_activa_puede_iniciar_sesion():
    nuevo_comprador().verificar_puede_iniciar_sesion()


def test_rn52_cuenta_desactivada_no_puede_iniciar_sesion():
    with pytest.raises(CuentaDesactivada) as e:
        nuevo_comprador(EstadoCuenta.DESACTIVADA).verificar_puede_iniciar_sesion()
    assert e.value.mensaje == "La cuenta se encuentra desactivada"


def test_respuesta_sin_contrasena_ni_documento():
    assert nuevo_comprador().to_response() == {
        "id": 1, "nombres": "Laura", "apellidos": "Gómez",
        "correo": "laura.gomez@correo.com", "estado": EstadoCuenta.ACTIVA}


# ── Schemas de entrada ────────────────────────────────────────
DATOS = {"tipo_documento_id": 1, "numero_documento": "1098765432", "nombres": "Laura",
         "apellidos": "Gómez", "correo": "laura.gomez@correo.com", "contrasena": "Segura123"}


def test_correo_se_normaliza_en_minuscula_y_sin_espacios():
    assert CompradorCreate(**{**DATOS, "correo": " Laura.Gomez@CORREO.com "}).correo == \
        "laura.gomez@correo.com"
    assert SesionCreate(correo=" LAURA@x.com ", contrasena="a").correo == "laura@x.com"


def test_contrasena_no_se_recorta():
    assert CompradorCreate(**{**DATOS, "contrasena": " Segura123 "}).contrasena == " Segura123 "


@pytest.mark.parametrize("correo", ["laura", "laura@correo", "a b@c.com"])
def test_correo_con_formato_invalido(correo):
    with pytest.raises(ValidationError):
        CompradorCreate(**{**DATOS, "correo": correo})


# ── Cifrado de la contraseña ──────────────────────────────────
def test_contrasena_cifrada_se_verifica():
    cifrada = cifrar_contrasena("Segura123")
    assert cifrada != "Segura123"
    assert verificar_contrasena("Segura123", cifrada)
    assert not verificar_contrasena("Segura124", cifrada)


def test_cifrado_usa_salt_distinto_cada_vez():
    assert cifrar_contrasena("Segura123") != cifrar_contrasena("Segura123")


def test_verificar_con_valor_guardado_mal_formado():
    assert not verificar_contrasena("Segura123", "texto-plano")
    assert not verificar_contrasena("Segura123", "md5$1$00$00")


def test_verificar_usa_las_vueltas_guardadas(monkeypatch):
    # Una contraseña cifrada con otras vueltas se sigue verificando bien
    cifrada = cifrar_contrasena("Segura123")
    monkeypatch.setattr(autenticacion, "ITERACIONES", 2_000)
    assert verificar_contrasena("Segura123", cifrada)


# ── Token JWT ─────────────────────────────────────────────────
def test_token_contiene_sujeto_rol_y_expiracion():
    token, expira_en = crear_token("5021", "COMPRADOR")
    datos = decodificar_token(token)
    assert datos["sub"] == "5021"
    assert datos["rol"] == "COMPRADOR"
    assert datos["exp"] - datos["iat"] == expira_en


def test_token_expirado_no_es_valido():
    ahora = datetime.now(timezone.utc)
    token = jwt.encode({"sub": "1", "rol": "COMPRADOR", "exp": ahora - timedelta(seconds=1)},
                       autenticacion.SECRET_KEY, algorithm="HS256")
    assert decodificar_token(token) is None


def test_token_firmado_con_otra_clave_no_es_valido():
    token = jwt.encode({"sub": "1", "rol": "ADMINISTRADOR",
                        "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                       "otra-clave-que-no-es-la-del-servidor-1234", algorithm="HS256")
    assert decodificar_token(token) is None


def test_token_sin_rol_no_es_valido():
    token = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
                       autenticacion.SECRET_KEY, algorithm="HS256")
    assert decodificar_token(token) is None


def test_texto_que_no_es_token():
    assert decodificar_token("no-es-un-jwt") is None
