# HU-05 Definir formato de validación de tipo de documento — casos de prueba funcional
# (al menos un test por cada caso de la HU, con el mismo código HTTP y el mismo `mensaje`)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.dependencies.seguridad import MENSAJE_401, MENSAJE_403
from app.api.routers import formato_router
from app.domain.exceptions.tipo_documento import ErrorAccesoDatosTipoDocumento
from app.repositories.formato_repository import FormatoRepository
from app.repositories.tipo_documento_repository import TipoDocumentoRepository
from app.services.formato_service import FormatoService
from main import app
from tests.conftest import ADMIN, COMPRADOR

# Mensajes de la HU-05 (MSG_NO_EXISTE es el texto de HU-02; MSG_INACTIVO es TODO(pendiente))
MSG_DEFINIDO = "Formato de validación definido exitosamente"
MSG_PATRON = "El patrón de validación no es válido"
MSG_EJEMPLO = "El ejemplo no cumple el patrón definido"
MSG_LONGITUDES = "La longitud mínima no puede ser mayor que la máxima"
MSG_RN50 = ("No es posible modificar el formato porque existen registros asociados "
            "al tipo de documento")
MSG_NO_EXISTE = "El tipo de documento no existe"
MSG_INACTIVO = "El tipo de documento está inactivo"  # TODO(pendiente): no definido en la HU
MSG_FALLA_BD = "No fue posible definir el formato de validación"

FORMATO_NIT = {"patron": "^[0-9]{9}-[0-9]$", "longitud_min": 11, "longitud_max": 11,
               "ejemplo": "900123456-7"}


def url(tipo_id):
    return f"/api/v1/parametrizacion/tipos-documento/{tipo_id}/formato"


def assert_error(r, codigo, mensaje):
    """Verifica un error con el envoltorio { mensaje, data: null, success: false }."""
    assert r.status_code == codigo
    assert r.json() == {"mensaje": mensaje, "data": None, "success": False}


@pytest.fixture
def nit(tipos_formato):
    """Tipo de documento NIT activo, sin formato."""
    return tipos_formato.crear(codigo="NIT", nombre="Número de Identificación Tributaria",
                               descripcion=None).id


# ✅ Caso 1: Definir el formato de un tipo sin registros
def test_caso1_definir_formato(client_formato, repo_formatos, nit):
    r = client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN)
    assert r.status_code == 200
    # Estructura exacta del ejemplo de la HU
    assert r.json() == {"mensaje": MSG_DEFINIDO, "success": True,
                        "data": {"id": nit, "codigo": "NIT", "formato": FORMATO_NIT}}
    # El formato queda asociado al tipo
    assert repo_formatos.obtener_por_tipo(nit).patron == FORMATO_NIT["patron"]


# ✅ Caso 2: Los registros usan el formato definido
def test_caso2_numero_que_cumple_el_formato_es_aceptado(client_formato, repo_formatos, nit):
    # Los vendedores se registran en HU-08 (aún no existe): se prueba la validación
    # que usará ese registro con el formato guardado del tipo NIT.
    client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN)
    formato = repo_formatos.obtener_por_tipo(nit)
    assert formato.numero_es_valido("900123456-7") is True
    assert formato.numero_es_valido("900123456") is False


# ❌ Caso 3: Patrón inválido
def test_caso3_patron_invalido(client_formato, repo_formatos, nit):
    r = client_formato.put(url(nit), json={**FORMATO_NIT, "patron": "[0-9{"}, headers=ADMIN)
    assert_error(r, 400, MSG_PATRON)
    assert repo_formatos.obtener_por_tipo(nit) is None


def test_caso3_patron_con_repeticion_demasiado_grande(client_formato, nit):
    # No se puede evaluar: también es un patrón inválido
    r = client_formato.put(url(nit), json={**FORMATO_NIT, "patron": "a{99999999999}"},
                           headers=ADMIN)
    assert_error(r, 400, MSG_PATRON)


# ❌ Caso 4: Ejemplo que no cumple el patrón
def test_caso4_ejemplo_no_cumple_patron(client_formato, repo_formatos, nit):
    r = client_formato.put(url(nit), json={**FORMATO_NIT, "ejemplo": "ABCDEFGHI-J"},
                           headers=ADMIN)
    assert_error(r, 400, MSG_EJEMPLO)
    assert repo_formatos.obtener_por_tipo(nit) is None


# ❌ Caso 5: Longitudes inconsistentes
def test_caso5_longitudes_inconsistentes(client_formato, repo_formatos, nit):
    r = client_formato.put(url(nit), json={**FORMATO_NIT, "longitud_min": 12, "longitud_max": 8},
                           headers=ADMIN)
    assert_error(r, 400, MSG_LONGITUDES)
    assert repo_formatos.obtener_por_tipo(nit) is None


# ❌ Caso 6: Modificar formato con registros asociados (RN-50)
def test_caso6_modificar_con_registros(client_formato, repo_formatos, registros_tipo_documento,
                                       nit):
    client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN)
    registros_tipo_documento.tipos_con_registros.add(nit)

    distinto = {"patron": "^[0-9]{10}$", "longitud_min": 10, "longitud_max": 10,
                "ejemplo": "9001234567"}
    r = client_formato.put(url(nit), json=distinto, headers=ADMIN)
    assert_error(r, 409, MSG_RN50)
    # El formato anterior se conserva
    assert repo_formatos.obtener_por_tipo(nit).to_response() == FORMATO_NIT


# ❌ Caso 7: Tipo inexistente o inactivo
def test_caso7_tipo_inexistente(client_formato):
    assert_error(client_formato.put(url(99999), json=FORMATO_NIT, headers=ADMIN), 404,
                 MSG_NO_EXISTE)


def test_caso7_tipo_inactivo(client_formato, tipos_formato, repo_formatos, nit):
    tipo = tipos_formato.obtener_por_id(nit)
    tipo.desactivar(esta_en_uso=False)
    tipos_formato.guardar(tipo)

    assert_error(client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN), 409,
                 MSG_INACTIVO)
    assert repo_formatos.obtener_por_tipo(nit) is None


# ❌ Caso 8: Usuario sin permisos
def test_caso8_sin_permisos(client_formato, repo_formatos, nit):
    r = client_formato.put(url(nit), json=FORMATO_NIT, headers=COMPRADOR)
    assert_error(r, 403, MENSAJE_403)
    assert repo_formatos.obtener_por_tipo(nit) is None


# ❌ Caso 9: Falla de base de datos
def test_caso9_falla_base_de_datos(tmp_path, registros_tipo_documento, monkeypatch):
    # Base de datos inalcanzable: la carpeta del archivo SQLite no existe.
    sesiones_caidas = sessionmaker(bind=create_engine(f"sqlite:///{tmp_path}/no_existe/bd.db"))
    monkeypatch.setattr(formato_router, "service", FormatoService(
        FormatoRepository(sesiones_caidas), TipoDocumentoRepository(sesiones_caidas),
        registros_tipo_documento))
    r = TestClient(app).put(url(1), json=FORMATO_NIT, headers=ADMIN)
    assert_error(r, 503, MSG_FALLA_BD)


# ── Casos adicionales (Definición de Hecho y decisiones del proyecto) ──

def test_falla_al_guardar_el_formato_responde_503(client_formato, repo_formatos, nit,
                                                  monkeypatch):
    def guardar_falla(formato):
        from app.domain.exceptions.formato import ErrorAccesoDatosFormato
        raise ErrorAccesoDatosFormato()
    monkeypatch.setattr(repo_formatos, "guardar", guardar_falla)
    assert_error(client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN), 503,
                 MSG_FALLA_BD)


def test_falla_al_leer_el_tipo_responde_mensaje_de_la_hu05(client_formato, tipos_formato, nit,
                                                           monkeypatch):
    # Aunque la falla venga del repositorio de HU-02, el mensaje es el del Caso 9
    def obtener_falla(tipo_id):
        raise ErrorAccesoDatosTipoDocumento()
    monkeypatch.setattr(tipos_formato, "obtener_por_id", obtener_falla)
    assert_error(client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN), 503,
                 MSG_FALLA_BD)


# RN-50 solo aplica si ya había un formato definido
def test_primera_definicion_con_registros_si_se_permite(client_formato,
                                                       registros_tipo_documento, nit):
    registros_tipo_documento.tipos_con_registros.add(nit)
    assert client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN).status_code == 200


def test_modificar_sin_registros_si_se_permite(client_formato, repo_formatos, nit):
    client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN)
    nuevo = {"patron": "^[0-9]{10}$", "longitud_min": 10, "longitud_max": 10,
             "ejemplo": "9001234567"}
    r = client_formato.put(url(nit), json=nuevo, headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["data"]["formato"] == nuevo
    assert repo_formatos.obtener_por_tipo(nit).to_response() == nuevo


def test_mismo_formato_con_registros_tambien_se_bloquea(client_formato,
                                                       registros_tipo_documento, nit):
    client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN)
    registros_tipo_documento.tipos_con_registros.add(nit)
    assert_error(client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN), 409, MSG_RN50)


def test_ejemplo_fuera_de_las_longitudes(client_formato, nit):
    # Cumple el patrón, pero tiene 3 caracteres y el mínimo es 5
    r = client_formato.put(url(nit), json={"patron": "^[0-9]+$", "longitud_min": 5,
                                           "longitud_max": 8, "ejemplo": "123"}, headers=ADMIN)
    assert_error(r, 400, MSG_EJEMPLO)


@pytest.mark.parametrize("campo", ["patron", "longitud_min", "longitud_max", "ejemplo"])
def test_campo_obligatorio_faltante(client_formato, nit, campo):
    cuerpo = {k: v for k, v in FORMATO_NIT.items() if k != campo}
    assert_error(client_formato.put(url(nit), json=cuerpo, headers=ADMIN), 400,
                 f"El campo {campo} es obligatorio")


@pytest.mark.parametrize("cuerpo, mensaje", [
    ({**FORMATO_NIT, "longitud_min": 0}, "El campo longitud_min no es válido"),
    ({**FORMATO_NIT, "longitud_min": -1}, "El campo longitud_min no es válido"),
    ({**FORMATO_NIT, "longitud_max": "once"}, "El campo longitud_max no es válido"),
    ({**FORMATO_NIT, "longitud_max": 10**30}, "El campo longitud_max no es válido"),
    ({**FORMATO_NIT, "longitud_min": 10**30}, "El campo longitud_min no es válido"),
    ({**FORMATO_NIT, "patron": ""}, "El campo patron no es válido"),
    ({**FORMATO_NIT, "ejemplo": ""}, "El campo ejemplo no es válido"),
])
def test_datos_invalidos_responden_400(client_formato, nit, cuerpo, mensaje):
    assert_error(client_formato.put(url(nit), json=cuerpo, headers=ADMIN), 400, mensaje)


@pytest.mark.parametrize("token, codigo, mensaje", [
    (None, 401, MENSAJE_401),
    ("token-invalido", 401, MENSAJE_401),
    ("token-vendedor", 403, MENSAJE_403),
])
def test_solo_administrador(client_formato, repo_formatos, nit, token, codigo, mensaje):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    assert_error(client_formato.put(url(nit), json=FORMATO_NIT, headers=headers), codigo, mensaje)
    assert repo_formatos.obtener_por_tipo(nit) is None


def test_id_demasiado_grande_responde_400(client_formato):
    assert_error(client_formato.put(url(2**63), json=FORMATO_NIT, headers=ADMIN), 400,
                 "El campo id no es válido")


def test_definir_formato_no_cambia_el_listado_de_hu02(client_formato, nit):
    # El JSON del listado de tipos de documento (HU-02) sigue igual
    client_formato.put(url(nit), json=FORMATO_NIT, headers=ADMIN)
    from app.api.routers import tipo_documento_router
    from app.services.tipo_documento_service import TipoDocumentoService
    from tests.conftest import UsoTipoDocumentoSimulado
    servicio_hu02 = TipoDocumentoService(formato_router.service.tipos, UsoTipoDocumentoSimulado())
    original = tipo_documento_router.service
    tipo_documento_router.service = servicio_hu02
    try:
        data = TestClient(app).get("/api/v1/parametrizacion/tipos-documento").json()["data"]
    finally:
        tipo_documento_router.service = original
    assert data == [{"id": nit, "codigo": "NIT", "nombre": "Número de Identificación Tributaria",
                     "estado": "ACTIVO"}]
