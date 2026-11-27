# HU-07 Registrar e iniciar sesión como comprador — casos de prueba funcional
# (al menos un test por cada caso de la HU, con el mismo código HTTP y el mismo `mensaje`)

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import sessionmaker

from app.api.dependencies.seguridad import MENSAJE_401, MENSAJE_403
from app.api.routers import comprador_router, formato_router, tipo_documento_router
from app.core.autenticacion import decodificar_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.database import crear_engine
from app.domain.models.comprador import EstadoCuenta
from app.domain.models.formato_validacion import FormatoValidacion
from app.domain.models.tipo_documento import EstadoTipoDocumento
from app.repositories.comprador_repository import CompradorRepository, CompradorTabla
from app.repositories.formato_repository import FormatoRepository
from app.repositories.tipo_documento_repository import TipoDocumentoRepository
from app.services.comprador_service import CompradorService
from app.services.consulta_registros_tipo_documento import ConsultaRegistrosTipoDocumento
from app.services.consulta_tipos_documento import ConsultaTiposDocumento
from app.services.consulta_uso_tipo_documento import ConsultaUsoTipoDocumento
from app.services.formato_service import FormatoService
from app.services.tipo_documento_service import TipoDocumentoService
from main import app
from tests.conftest import ADMIN

URL_REGISTRO = "/api/v1/usuarios/compradores"
URL_SESIONES = "/api/v1/usuarios/sesiones"

# Mensajes de la HU-07 (MSG_TIPO_NO_VALIDO es TODO(pendiente): no definido en la HU)
MSG_REGISTRADO = "Comprador registrado exitosamente"
MSG_SESION = "Inicio de sesión exitoso"
MSG_RN51 = "Ya existe una cuenta registrada con ese correo"
MSG_RN55 = "La contraseña no cumple los requisitos mínimos de seguridad"
MSG_FORMATO = "El número de documento no cumple el formato del tipo seleccionado"
MSG_CREDENCIALES = "Correo o contraseña incorrectos"
MSG_RN52 = "La cuenta se encuentra desactivada"
MSG_FALLA = "No fue posible procesar la solicitud en este momento"
MSG_TIPO_NO_VALIDO = "El tipo de documento indicado no es válido"

CONTRASENA = "Segura123"


def assert_error(r, codigo, mensaje):
    """Verifica un error con el envoltorio { mensaje, data: null, success: false }."""
    assert r.status_code == codigo
    assert r.json() == {"mensaje": mensaje, "data": None, "success": False}


@pytest.fixture
def cedula(tipos_comprador, formatos_comprador):
    """Tipo de documento CC activo con formato: solo dígitos, de 6 a 10."""
    tipo = tipos_comprador.crear("CC", "Cédula de ciudadanía", None)
    formatos_comprador.guardar(FormatoValidacion.crear(
        tipo.id, patron="^[0-9]+$", longitud_min=6, longitud_max=10, ejemplo="1098765432"))
    return tipo.id


@pytest.fixture
def datos(cedula):
    """Cuerpo válido de registro (el de la HU)."""
    return {"tipo_documento_id": cedula, "numero_documento": "1098765432",
            "nombres": "Laura", "apellidos": "Gómez",
            "correo": "laura.gomez@correo.com", "contrasena": CONTRASENA}


@pytest.fixture
def laura(client_comprador, datos):
    """Registra a Laura y devuelve su id."""
    return client_comprador.post(URL_REGISTRO, json=datos).json()["data"]["id"]


def desactivar_cuenta(sesiones, comprador_id):
    # La HU-07 no tiene endpoint para desactivar cuentas: se cambia directo en la base
    with sesiones() as s:
        s.execute(update(CompradorTabla).where(CompradorTabla.id == comprador_id)
                  .values(estado=EstadoCuenta.DESACTIVADA))
        s.commit()


def login(client, correo="laura.gomez@correo.com", contrasena=CONTRASENA):
    return client.post(URL_SESIONES, json={"correo": correo, "contrasena": contrasena})


# ── ✅ Caso 1: Registrar un comprador válido ──────────────────
def test_caso1_registrar_comprador_valido(client_comprador, repo_compradores, datos):
    r = client_comprador.post(URL_REGISTRO, json=datos)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["mensaje"] == MSG_REGISTRADO
    assert cuerpo["success"] is True
    assert cuerpo["data"] == {"id": cuerpo["data"]["id"], "nombres": "Laura",
                              "apellidos": "Gómez", "correo": "laura.gomez@correo.com",
                              "estado": "ACTIVA"}
    # La respuesta no incluye la contraseña (ni cifrada)
    assert CONTRASENA not in r.text
    assert "contrasena" not in r.text
    # Se guardó cifrada, nunca en texto plano
    guardado = repo_compradores.buscar_por_correo("laura.gomez@correo.com")
    assert guardado.contrasena_cifrada != CONTRASENA
    assert guardado.contrasena_cifrada.startswith("pbkdf2_sha256$")


# ── ✅ Caso 2: Iniciar sesión con credenciales correctas ──────
def test_caso2_iniciar_sesion(client_comprador, laura):
    r = login(client_comprador)
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["mensaje"] == MSG_SESION
    assert cuerpo["success"] is True
    assert set(cuerpo["data"]) == {"token", "tipo", "expira_en"}
    assert cuerpo["data"]["tipo"] == "Bearer"
    assert cuerpo["data"]["expira_en"] == ACCESS_TOKEN_EXPIRE_MINUTES * 60
    # El token es un JWT firmado con el id y el rol del comprador
    contenido = decodificar_token(cuerpo["data"]["token"])
    assert contenido["sub"] == str(laura)
    assert contenido["rol"] == "COMPRADOR"


def test_caso2_correo_sin_distinguir_mayusculas(client_comprador, laura):
    assert login(client_comprador, correo="  Laura.Gomez@CORREO.com ").status_code == 200


# ── ❌ Caso 3: Correo ya registrado (RN-51) ───────────────────
def test_caso3_correo_ya_registrado(client_comprador, repo_compradores, datos, laura):
    otro = {**datos, "nombres": "Otra", "numero_documento": "1000000001"}
    assert_error(client_comprador.post(URL_REGISTRO, json=otro), 409, MSG_RN51)


def test_caso3_correo_repetido_con_mayusculas_y_espacios(client_comprador, datos, laura):
    otro = {**datos, "correo": " LAURA.GOMEZ@correo.com "}
    assert_error(client_comprador.post(URL_REGISTRO, json=otro), 409, MSG_RN51)


# ── ❌ Caso 4: Contraseña que no cumple los requisitos (RN-55) ─
def test_caso4_contrasena_abc123(client_comprador, repo_compradores, datos):
    r = client_comprador.post(URL_REGISTRO, json={**datos, "contrasena": "abc123"})
    assert_error(r, 400, MSG_RN55)
    assert repo_compradores.buscar_por_correo(datos["correo"]) is None


@pytest.mark.parametrize("contrasena", [
    "Segura1",      # 7 caracteres
    "segura123",    # sin mayúscula
    "SEGURA123",    # sin minúscula
    "SeguraSegura",  # sin número
    "",
])
def test_caso4_otras_contrasenas_inseguras(client_comprador, datos, contrasena):
    r = client_comprador.post(URL_REGISTRO, json={**datos, "contrasena": contrasena})
    assert_error(r, 400, MSG_RN55)


# ── ❌ Caso 5: Documento que no cumple el formato ─────────────
@pytest.mark.parametrize("numero", ["ABC123456", "12345", "12345678901"])
def test_caso5_documento_no_cumple_formato(client_comprador, repo_compradores, datos, numero):
    r = client_comprador.post(URL_REGISTRO, json={**datos, "numero_documento": numero})
    assert_error(r, 400, MSG_FORMATO)
    assert repo_compradores.buscar_por_correo(datos["correo"]) is None


# ── ❌ Caso 6: Datos obligatorios faltantes ───────────────────
def test_caso6_sin_correo(client_comprador, datos):
    sin_correo = {k: v for k, v in datos.items() if k != "correo"}
    assert_error(client_comprador.post(URL_REGISTRO, json=sin_correo), 400,
                 "El campo correo es obligatorio")


@pytest.mark.parametrize("campo", ["tipo_documento_id", "numero_documento", "nombres",
                                   "apellidos", "contrasena"])
def test_caso6_otros_campos_obligatorios(client_comprador, datos, campo):
    cuerpo = {k: v for k, v in datos.items() if k != campo}
    assert_error(client_comprador.post(URL_REGISTRO, json=cuerpo), 400,
                 f"El campo {campo} es obligatorio")


@pytest.mark.parametrize("campo", ["correo", "contrasena"])
def test_caso6_login_sin_campo(client_comprador, campo):
    cuerpo = {"correo": "laura.gomez@correo.com", "contrasena": CONTRASENA}
    del cuerpo[campo]
    assert_error(client_comprador.post(URL_SESIONES, json=cuerpo), 400,
                 f"El campo {campo} es obligatorio")


# ── ❌ Caso 7: Credenciales incorrectas ───────────────────────
def test_caso7_contrasena_incorrecta(client_comprador, laura):
    assert_error(login(client_comprador, contrasena="Incorrecta123"), 401, MSG_CREDENCIALES)


def test_caso7_correo_inexistente_responde_el_mismo_mensaje(client_comprador, laura):
    # No revela si falló el correo o la contraseña
    assert_error(login(client_comprador, correo="nadie@correo.com"), 401, MSG_CREDENCIALES)


# ── ❌ Caso 8: Cuenta desactivada (RN-52) ─────────────────────
def test_caso8_cuenta_desactivada(client_comprador, sesiones_comprador, laura):
    desactivar_cuenta(sesiones_comprador, laura)
    assert_error(login(client_comprador), 403, MSG_RN52)


def test_caso8_desactivada_con_contrasena_incorrecta_responde_401(client_comprador,
                                                                   sesiones_comprador, laura):
    # Sin la contraseña correcta no se revela que la cuenta está desactivada
    desactivar_cuenta(sesiones_comprador, laura)
    assert_error(login(client_comprador, contrasena="Incorrecta123"), 401, MSG_CREDENCIALES)


# ── ❌ Caso 9: Falla de base de datos o del módulo Parametrización ─
@pytest.fixture
def base_caida():
    """Sesiones de una base en memoria SIN tablas: toda consulta falla."""
    motor = crear_engine("sqlite:///:memory:")
    yield sessionmaker(bind=motor, expire_on_commit=False)
    motor.dispose()


def test_caso9_falla_base_de_datos_al_registrar(client_comprador, tipos_comprador,
                                                formatos_comprador, base_caida, datos,
                                                monkeypatch):
    consulta = ConsultaTiposDocumento(tipos_comprador, formatos_comprador)
    monkeypatch.setattr(comprador_router, "service",
                        CompradorService(CompradorRepository(base_caida), consulta))
    assert_error(client_comprador.post(URL_REGISTRO, json=datos), 503, MSG_FALLA)


def test_caso9_falla_base_de_datos_al_iniciar_sesion(client_comprador, tipos_comprador,
                                                     formatos_comprador, base_caida,
                                                     monkeypatch):
    consulta = ConsultaTiposDocumento(tipos_comprador, formatos_comprador)
    monkeypatch.setattr(comprador_router, "service",
                        CompradorService(CompradorRepository(base_caida), consulta))
    assert_error(login(client_comprador), 503, MSG_FALLA)


@pytest.mark.parametrize("falla", ["tipos", "formatos"])
def test_caso9_falla_del_modulo_parametrizacion(client_comprador, repo_compradores,
                                                tipos_comprador, formatos_comprador,
                                                base_caida, datos, monkeypatch, falla):
    tipos = TipoDocumentoRepository(base_caida) if falla == "tipos" else tipos_comprador
    formatos = FormatoRepository(base_caida) if falla == "formatos" else formatos_comprador
    monkeypatch.setattr(comprador_router, "service", CompradorService(
        repo_compradores, ConsultaTiposDocumento(tipos, formatos)))
    assert_error(client_comprador.post(URL_REGISTRO, json=datos), 503, MSG_FALLA)


# ── Complementarios (no son casos de la HU) ───────────────────
def test_tipo_documento_inexistente(client_comprador, datos):
    r = client_comprador.post(URL_REGISTRO, json={**datos, "tipo_documento_id": 999})
    assert_error(r, 400, MSG_TIPO_NO_VALIDO)


def test_tipo_documento_inactivo(client_comprador, tipos_comprador, cedula, datos):
    tipo = tipos_comprador.obtener_por_id(cedula)
    tipo.estado = EstadoTipoDocumento.INACTIVO
    tipos_comprador.guardar(tipo)
    assert_error(client_comprador.post(URL_REGISTRO, json=datos), 400, MSG_TIPO_NO_VALIDO)


def test_tipo_sin_formato_acepta_cualquier_numero(client_comprador, tipos_comprador, datos):
    pasaporte = tipos_comprador.crear("PA", "Pasaporte", None)
    cuerpo = {**datos, "tipo_documento_id": pasaporte.id, "numero_documento": "AB-12"}
    assert client_comprador.post(URL_REGISTRO, json=cuerpo).status_code == 201


@pytest.mark.parametrize("correo", ["laura", "laura@correo", "laura gomez@correo.com", ""])
def test_correo_con_formato_invalido(client_comprador, datos, correo):
    assert_error(client_comprador.post(URL_REGISTRO, json={**datos, "correo": correo}), 400,
                 "El campo correo no es válido")


def test_textos_se_guardan_sin_espacios(client_comprador, datos):
    r = client_comprador.post(URL_REGISTRO, json={**datos, "nombres": "  Laura ",
                                                  "numero_documento": " 1098765432 "})
    assert r.status_code == 201
    assert r.json()["data"]["nombres"] == "Laura"


def test_registro_y_login_sin_token(client_comprador, datos):
    # Son endpoints públicos: no piden encabezado Authorization
    assert client_comprador.post(URL_REGISTRO, json=datos).status_code == 201
    assert login(client_comprador).status_code == 200


# ── El token real funciona con la seguridad de los demás módulos ─
def test_token_de_comprador_es_aceptado_pero_no_es_administrador(client_comprador, laura):
    token = login(client_comprador).json()["data"]["token"]
    r = TestClient(app).post("/api/v1/parametrizacion/ubicaciones",
                             json={"tipo": "PAIS", "nombre": "Colombia", "codigo": "CO"},
                             headers={"Authorization": f"Bearer {token}"})
    # Token válido (no es 401), pero el rol COMPRADOR no puede administrar (403)
    assert_error(r, 403, MENSAJE_403)


def test_token_falsificado_responde_401(client_comprador, laura):
    # Mismo contenido que un token real, pero firmado con otra clave: la firma no coincide
    contenido = decodificar_token(login(client_comprador).json()["data"]["token"])
    falso = jwt.encode({**contenido, "rol": "ADMINISTRADOR"},
                       "clave-que-no-es-la-del-servidor-0123456789", algorithm="HS256")
    r = TestClient(app).post("/api/v1/parametrizacion/ubicaciones",
                             json={"tipo": "PAIS", "nombre": "Colombia", "codigo": "CO"},
                             headers={"Authorization": f"Bearer {falso}"})
    assert_error(r, 401, MENSAJE_401)


# ── Conexión con HU-05 (RN-50) y HU-02 (tipo en uso) ──────────
FORMATO_CC = {"patron": "^[0-9]+$", "longitud_min": 6, "longitud_max": 12,
              "ejemplo": "123456789"}


def test_rn50_no_se_modifica_el_formato_con_compradores_registrados(
        client_comprador, repo_compradores, tipos_comprador, formatos_comprador, cedula,
        laura, monkeypatch):
    monkeypatch.setattr(formato_router, "service", FormatoService(
        formatos_comprador, tipos_comprador, ConsultaRegistrosTipoDocumento(repo_compradores)))
    r = TestClient(app).put(f"/api/v1/parametrizacion/tipos-documento/{cedula}/formato",
                            json=FORMATO_CC, headers=ADMIN)
    assert_error(r, 409, "No es posible modificar el formato porque existen registros "
                         "asociados al tipo de documento")


def test_hu02_no_se_desactiva_un_tipo_con_compradores_activos(
        client_comprador, repo_compradores, tipos_comprador, cedula, laura, monkeypatch):
    monkeypatch.setattr(tipo_documento_router, "service", TipoDocumentoService(
        tipos_comprador, ConsultaUsoTipoDocumento(repo_compradores)))
    r = TestClient(app).patch(f"/api/v1/parametrizacion/tipos-documento/{cedula}/desactivar",
                              headers=ADMIN)
    assert_error(r, 409, "No es posible desactivar el tipo de documento porque está en uso")


def test_hu02_si_se_desactiva_un_tipo_con_compradores_desactivados(
        client_comprador, repo_compradores, tipos_comprador, sesiones_comprador, cedula,
        laura, monkeypatch):
    desactivar_cuenta(sesiones_comprador, laura)
    monkeypatch.setattr(tipo_documento_router, "service", TipoDocumentoService(
        tipos_comprador, ConsultaUsoTipoDocumento(repo_compradores)))
    r = TestClient(app).patch(f"/api/v1/parametrizacion/tipos-documento/{cedula}/desactivar",
                              headers=ADMIN)
    assert r.status_code == 200


# Si la tabla de compradores falla, HU-05 y HU-02 responden su propio 503 (no un 500)
def test_rn50_falla_de_compradores_responde_503_de_hu05(
        client_comprador, tipos_comprador, formatos_comprador, cedula, base_caida,
        monkeypatch):
    monkeypatch.setattr(formato_router, "service", FormatoService(
        formatos_comprador, tipos_comprador,
        ConsultaRegistrosTipoDocumento(CompradorRepository(base_caida))))
    r = TestClient(app).put(f"/api/v1/parametrizacion/tipos-documento/{cedula}/formato",
                            json=FORMATO_CC, headers=ADMIN)
    assert_error(r, 503, "No fue posible definir el formato de validación")


def test_hu02_falla_de_compradores_responde_503_de_hu02(
        client_comprador, tipos_comprador, cedula, base_caida, monkeypatch):
    monkeypatch.setattr(tipo_documento_router, "service", TipoDocumentoService(
        tipos_comprador, ConsultaUsoTipoDocumento(CompradorRepository(base_caida))))
    r = TestClient(app).patch(f"/api/v1/parametrizacion/tipos-documento/{cedula}/desactivar",
                              headers=ADMIN)
    assert_error(r, 503, "No fue posible procesar la solicitud de tipos de documento")
