# HU-01 Gestionar catálogo geográfico — casos de prueba funcional
# (al menos un test por cada caso de la HU, con el mismo código HTTP y el mismo `mensaje`)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.dependencies.seguridad import MENSAJE_401, MENSAJE_403
from app.api.errores import (
    MENSAJE_500,
    MENSAJE_CUERPO_INVALIDO,
    MENSAJE_JSON_INVALIDO,
)
from app.api.routers import ubicacion_router
from app.repositories.ubicacion_repository import UbicacionRepository
from app.services.ubicacion_service import UbicacionService
from main import app
from tests.conftest import ADMIN, COMPRADOR, URL, crear

# Mensajes exactos de la HU-01
MSG_REGISTRO = "Ubicación registrada exitosamente"
MSG_EDICION = "Ubicación actualizada exitosamente"  # TODO(pendiente): no definido en la HU
MSG_LISTADO = "Consulta de ubicaciones exitosa"
MSG_DESACTIVACION = "Ubicación desactivada exitosamente"
MSG_DUPLICADO = "Ya existe una ubicación con el mismo nombre o código en el mismo nivel"
MSG_JERARQUIA = "La jerarquía de la ubicación no es válida"
MSG_RN47 = "No es posible desactivar la ubicación porque tiene direcciones activas asociadas"
MSG_NO_EXISTE = "La ubicación no existe"
MSG_FALLA_BD = "No fue posible procesar la solicitud de ubicaciones"


def assert_error(r, codigo, mensaje):
    """Verifica un error con el envoltorio { mensaje, data: null, success: false }."""
    assert r.status_code == codigo
    assert r.json() == {"mensaje": mensaje, "data": None, "success": False}


# ✅ Caso 1: Registrar una ciudad válida
def test_caso1_registrar_ciudad_valida(client, colombia_santander):
    _, santander = colombia_santander
    r = crear(client, "CIUDAD", "Bucaramanga", "68001", santander)
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["mensaje"] == MSG_REGISTRO
    assert cuerpo["data"] == {"id": cuerpo["data"]["id"], "tipo": "CIUDAD",
                              "nombre": "Bucaramanga", "codigo": "68001",
                              "padre_id": santander, "estado": "ACTIVO", "publicada": False}


# ✅ Caso 2: Editar el nombre de una ubicación
def test_caso2_editar_nombre(client, colombia_santander):
    _, santander = colombia_santander
    ciudad = crear(client, "CIUDAD", "Bucaramnga", "68001", santander).json()["data"]
    r = client.put(f"{URL}/{ciudad['id']}",
                   json={"nombre": "Bucaramanga", "codigo": "68001", "padre_id": santander},
                   headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["mensaje"] == MSG_EDICION
    assert r.json()["data"]["nombre"] == "Bucaramanga"
    assert r.json()["data"]["tipo"] == "CIUDAD"


# ✅ Caso 3: Listar departamentos activos de un país
def test_caso3_listar_departamentos_activos(client, colombia_santander):
    colombia, _ = colombia_santander
    boyaca = crear(client, "DEPARTAMENTO", "Boyacá", "15", colombia).json()["data"]["id"]
    client.patch(f"{URL}/{boyaca}/desactivar", headers=ADMIN)

    r = client.get(URL, params={"tipo": "DEPARTAMENTO", "padre_id": colombia})
    assert r.status_code == 200
    assert r.json()["mensaje"] == MSG_LISTADO
    assert r.json()["success"] is True
    data = r.json()["data"]
    assert set(data) == {"pagina", "tamano", "total", "ubicaciones"}
    assert data["pagina"] == 1 and data["tamano"] == 20
    assert data["total"] == 1
    assert [u["nombre"] for u in data["ubicaciones"]] == ["Santander"]
    assert all(u["estado"] == "ACTIVO" for u in data["ubicaciones"])


# ✅ Caso 4: Desactivar una ubicación sin uso
def test_caso4_desactivar_sin_uso(client, repo, colombia_santander):
    _, santander = colombia_santander
    ciudad = crear(client, "CIUDAD", "Bucaramanga", "68001", santander).json()["data"]["id"]

    r = client.patch(f"{URL}/{ciudad}/desactivar", headers=ADMIN)
    assert r.status_code == 200
    assert r.json() == {"mensaje": MSG_DESACTIVACION,
                        "data": {"id": ciudad, "estado": "INACTIVO"}, "success": True}
    # El registro sigue existiendo (baja lógica)
    assert repo.obtener_por_id(ciudad) is not None
    # Ya no aparece en el listado por defecto...
    ids = [u["id"] for u in client.get(URL).json()["data"]["ubicaciones"]]
    assert ciudad not in ids
    # ...pero sí con estado=INACTIVO
    ids_inactivos = [u["id"] for u in
                     client.get(URL, params={"estado": "INACTIVO"}).json()["data"]["ubicaciones"]]
    assert ciudad in ids_inactivos


# ❌ Caso 5: Registrar una ubicación duplicada (mismo nombre y padre)
def test_caso5_registrar_duplicada(client, colombia_santander):
    _, santander = colombia_santander
    crear(client, "CIUDAD", "Bucaramanga", "68001", santander)
    r = crear(client, "CIUDAD", "Bucaramanga", "68999", santander)
    assert_error(r, 409, MSG_DUPLICADO)


# ❌ Caso 5 (variante): mismo código
def test_caso5b_registrar_codigo_duplicado(client, colombia_santander):
    _, santander = colombia_santander
    crear(client, "CIUDAD", "Bucaramanga", "68001", santander)
    r = crear(client, "CIUDAD", "Floridablanca", "68001", santander)
    assert_error(r, 409, MSG_DUPLICADO)


# ❌ Caso 6: Registrar con jerarquía inválida
def test_caso6_jerarquia_invalida(client, colombia_santander):
    colombia, _ = colombia_santander
    r = crear(client, "CIUDAD", "Bucaramanga", "68001", colombia)
    assert_error(r, 400, MSG_JERARQUIA)


# ❌ Caso 7: Registrar con datos obligatorios faltantes
def test_caso7_falta_nombre(client, colombia_santander):
    _, santander = colombia_santander
    r = client.post(URL, json={"tipo": "CIUDAD", "codigo": "68001", "padre_id": santander},
                    headers=ADMIN)
    assert_error(r, 400, "El campo nombre es obligatorio")


# ❌ Caso 8: Desactivar una ubicación con direcciones activas (RN-47)
def test_caso8_desactivar_con_direcciones(client, repo, direcciones, colombia_santander):
    _, santander = colombia_santander
    ciudad = crear(client, "CIUDAD", "Bucaramanga", "68001", santander).json()["data"]["id"]
    direcciones.ubicaciones_con_direcciones.add(ciudad)

    r = client.patch(f"{URL}/{ciudad}/desactivar", headers=ADMIN)
    assert_error(r, 409, MSG_RN47)
    assert repo.obtener_por_id(ciudad).estado == "ACTIVO"


# ❌ Caso 9: Editar o desactivar una ubicación inexistente
def test_caso9_editar_inexistente(client):
    r = client.put(f"{URL}/99999", json={"nombre": "X", "codigo": "X", "padre_id": None}, headers=ADMIN)
    assert_error(r, 404, MSG_NO_EXISTE)


def test_caso9_desactivar_inexistente(client):
    r = client.patch(f"{URL}/99999/desactivar", headers=ADMIN)
    assert_error(r, 404, MSG_NO_EXISTE)


# ❌ Caso 10: Usuario sin permisos de administrador
def test_caso10_sin_permisos(client, repo):
    r = client.post(URL, json={"tipo": "PAIS", "nombre": "Colombia", "codigo": "CO"},
                    headers=COMPRADOR)
    assert_error(r, 403, MENSAJE_403)
    assert repo.listar(None, None, None, 1, 20)[1] == 0  # no se creó ningún registro


# ❌ Caso 11: Falla de base de datos
def test_caso11_falla_base_de_datos(tmp_path, direcciones, monkeypatch):
    # Base de datos inalcanzable: la carpeta del archivo SQLite no existe,
    # así que SQLAlchemy falla al intentar conectarse.
    motor_caido = create_engine(f"sqlite:///{tmp_path}/no_existe/bd.db")
    repo_caido = UbicacionRepository(sessionmaker(bind=motor_caido))
    monkeypatch.setattr(ubicacion_router, "service", UbicacionService(repo_caido, direcciones))
    client = TestClient(app)

    peticiones = [
        client.post(URL, json={"tipo": "PAIS", "nombre": "Colombia", "codigo": "CO"},
                    headers=ADMIN),
        client.put(f"{URL}/1", json={"nombre": "X", "codigo": "X", "padre_id": None}, headers=ADMIN),
        client.get(URL),
        client.patch(f"{URL}/1/desactivar", headers=ADMIN),
    ]
    for r in peticiones:
        assert_error(r, 503, MSG_FALLA_BD)


# ── Casos adicionales (Definición de Hecho y decisiones del proyecto) ──

# Listado sin resultados (Definición de Hecho)
def test_listado_sin_resultados(client):
    r = client.get(URL)
    assert r.status_code == 200
    assert r.json() == {"mensaje": MSG_LISTADO, "success": True,
                        "data": {"pagina": 1, "tamano": 20, "total": 0, "ubicaciones": []}}


def test_listado_paginado(client):
    for i in range(3):
        crear(client, "PAIS", f"Pais {i}", f"P{i}")
    data = client.get(URL, params={"pagina": 2, "tamano": 2}).json()["data"]
    assert data["total"] == 3
    assert [u["nombre"] for u in data["ubicaciones"]] == ["Pais 2"]


# Criterio 1: las desactivadas aparecen con estado=INACTIVO o estado=TODOS
def test_listado_estado_todos(client, colombia_santander):
    colombia, santander = colombia_santander
    boyaca = crear(client, "DEPARTAMENTO", "Boyacá", "15", colombia).json()["data"]["id"]
    client.patch(f"{URL}/{boyaca}/desactivar", headers=ADMIN)

    data = client.get(URL, params={"tipo": "DEPARTAMENTO", "estado": "TODOS"}).json()["data"]
    assert data["total"] == 2
    estados = {u["id"]: u["estado"] for u in data["ubicaciones"]}
    assert estados == {santander: "ACTIVO", boyaca: "INACTIVO"}


def test_listado_no_incluye_publicada(client, colombia_santander):
    # La estructura del listado en la HU no trae `publicada`
    item = client.get(URL).json()["data"]["ubicaciones"][0]
    assert set(item) == {"id", "tipo", "nombre", "codigo", "padre_id", "estado"}


# Duplicidad: el mismo nombre sí se permite con otro padre (otro nivel)
def test_mismo_nombre_con_otro_padre_si_se_permite(client, colombia_santander):
    colombia, santander = colombia_santander
    antioquia = crear(client, "DEPARTAMENTO", "Antioquia", "05", colombia).json()["data"]["id"]
    assert crear(client, "CIUDAD", "Barbosa", "68077", santander).status_code == 201
    assert crear(client, "CIUDAD", "Barbosa", "05079", antioquia).status_code == 201


# RN-47: hijas activas bloquean la desactivación del padre
def test_desactivar_con_hijas_activas(client, repo, colombia_santander):
    colombia, _ = colombia_santander
    r = client.patch(f"{URL}/{colombia}/desactivar", headers=ADMIN)
    assert_error(r, 409, MSG_RN47)
    assert repo.obtener_por_id(colombia).estado == "ACTIVO"


# ...pero una hija INACTIVA no bloquea
def test_desactivar_con_hijas_inactivas_si_se_permite(client, colombia_santander):
    colombia, santander = colombia_santander
    assert client.patch(f"{URL}/{santander}/desactivar", headers=ADMIN).status_code == 200
    r = client.patch(f"{URL}/{colombia}/desactivar", headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["data"]["estado"] == "INACTIVO"


# Editar: el tipo no cambia, y se validan de nuevo duplicidad y jerarquía
def test_editar_no_cambia_tipo(client, colombia_santander):
    _, santander = colombia_santander
    ciudad = crear(client, "CIUDAD", "Bucaramanga", "68001", santander).json()["data"]["id"]
    r = client.put(f"{URL}/{ciudad}",
                   json={"tipo": "PAIS", "nombre": "Bucaramanga", "codigo": "68001",
                         "padre_id": santander},
                   headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["data"]["tipo"] == "CIUDAD"


def test_editar_a_nombre_duplicado_responde_409(client, colombia_santander):
    _, santander = colombia_santander
    crear(client, "CIUDAD", "Bucaramanga", "68001", santander)
    otra = crear(client, "CIUDAD", "Girón", "68307", santander).json()["data"]["id"]
    r = client.put(f"{URL}/{otra}",
                   json={"nombre": "Bucaramanga", "codigo": "68307", "padre_id": santander},
                   headers=ADMIN)
    assert_error(r, 409, MSG_DUPLICADO)


def test_editar_a_codigo_duplicado_responde_409(client, colombia_santander):
    _, santander = colombia_santander
    crear(client, "CIUDAD", "Bucaramanga", "68001", santander)
    otra = crear(client, "CIUDAD", "Girón", "68307", santander).json()["data"]["id"]
    r = client.put(f"{URL}/{otra}",
                   json={"nombre": "Girón", "codigo": "68001", "padre_id": santander},
                   headers=ADMIN)
    assert_error(r, 409, MSG_DUPLICADO)


def test_editar_con_jerarquia_invalida(client, colombia_santander):
    colombia, santander = colombia_santander
    ciudad = crear(client, "CIUDAD", "Bucaramanga", "68001", santander).json()["data"]["id"]
    r = client.put(f"{URL}/{ciudad}",
                   json={"nombre": "Bucaramanga", "codigo": "68001", "padre_id": colombia},
                   headers=ADMIN)
    assert_error(r, 400, MSG_JERARQUIA)


def test_editar_con_padre_inexistente(client, colombia_santander):
    _, santander = colombia_santander
    ciudad = crear(client, "CIUDAD", "Bucaramanga", "68001", santander).json()["data"]["id"]
    r = client.put(f"{URL}/{ciudad}",
                   json={"nombre": "Bucaramanga", "codigo": "68001", "padre_id": 99999},
                   headers=ADMIN)
    assert_error(r, 400, MSG_JERARQUIA)


# La HU marca padre_id como obligatorio al editar: debe venir en el body
def test_editar_sin_padre_id_responde_400(client, colombia_santander):
    _, santander = colombia_santander
    r = client.put(f"{URL}/{santander}", json={"nombre": "Santander", "codigo": "68"},
                   headers=ADMIN)
    assert_error(r, 400, "El campo padre_id es obligatorio")


def test_editar_pais_con_padre_id_null(client, colombia_santander):
    colombia, _ = colombia_santander
    r = client.put(f"{URL}/{colombia}",
                   json={"nombre": "República de Colombia", "codigo": "CO", "padre_id": None},
                   headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["data"]["nombre"] == "República de Colombia"
    assert r.json()["data"]["padre_id"] is None


# Los espacios al inicio y al final se recortan
def test_espacios_se_recortan_y_cuentan_como_duplicado(client, colombia_santander):
    _, santander = colombia_santander
    r = crear(client, "CIUDAD", "  Bucaramanga ", " 68001 ", santander)
    assert r.status_code == 201
    assert (r.json()["data"]["nombre"], r.json()["data"]["codigo"]) == ("Bucaramanga", "68001")
    assert_error(crear(client, "CIUDAD", "Bucaramanga ", "68999", santander), 409,
                 MSG_DUPLICADO)


# Jerarquía al registrar
def test_pais_con_padre_es_jerarquia_invalida(client, colombia_santander):
    colombia, _ = colombia_santander
    assert_error(crear(client, "PAIS", "Perú", "PE", colombia), 400, MSG_JERARQUIA)


def test_departamento_sin_padre_es_jerarquia_invalida(client):
    assert_error(crear(client, "DEPARTAMENTO", "Santander", "68"), 400, MSG_JERARQUIA)


# Seguridad: registrar, editar y desactivar son solo para el Administrador
@pytest.mark.parametrize("token, codigo, mensaje", [
    (None, 401, MENSAJE_401),
    ("token-invalido", 401, MENSAJE_401),
    ("token-comprador", 403, MENSAJE_403),
    ("token-vendedor", 403, MENSAJE_403),
])
@pytest.mark.parametrize("operacion", ["registrar", "editar", "desactivar"])
def test_operaciones_solo_administrador(client, repo, colombia_santander,
                                        operacion, token, codigo, mensaje):
    colombia, santander = colombia_santander
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if operacion == "registrar":
        r = client.post(URL, json={"tipo": "PAIS", "nombre": "Perú", "codigo": "PE"},
                        headers=headers)
    elif operacion == "editar":
        r = client.put(f"{URL}/{santander}",
                       json={"nombre": "Otro", "codigo": "68", "padre_id": colombia}, headers=headers)
    else:
        r = client.patch(f"{URL}/{santander}/desactivar", headers=headers)
    assert_error(r, codigo, mensaje)
    # No cambió nada: siguen solo Colombia y Santander, con sus datos originales
    _, total = repo.listar(None, None, None, 1, 20)
    assert total == 2
    s = repo.obtener_por_id(santander)
    assert (s.nombre, s.estado) == ("Santander", "ACTIVO")


# Datos inválidos -> 400 (no el 422 por defecto de FastAPI)
@pytest.mark.parametrize("cuerpo, mensaje", [
    ({"tipo": "CIUDADX", "nombre": "A", "codigo": "1"}, "El campo tipo no es válido"),
    ({"tipo": "PAIS", "nombre": "A" * 101, "codigo": "1"}, "El campo nombre no es válido"),
    ({"tipo": "PAIS", "nombre": "", "codigo": "1"}, "El campo nombre no es válido"),
    ({"tipo": "PAIS", "nombre": "   ", "codigo": "1"}, "El campo nombre no es válido"),
    ({"tipo": "PAIS", "nombre": "A", "codigo": "   "}, "El campo codigo no es válido"),
    ({"tipo": "PAIS", "nombre": "A", "codigo": "1" * 51}, "El campo codigo no es válido"),
    ({"tipo": "PAIS", "nombre": "A"}, "El campo codigo es obligatorio"),
    ({"nombre": "A", "codigo": "1"}, "El campo tipo es obligatorio"),
    ([{"tipo": "PAIS"}], MENSAJE_CUERPO_INVALIDO),
])
def test_registrar_datos_invalidos_responde_400(client, cuerpo, mensaje):
    assert_error(client.post(URL, json=cuerpo, headers=ADMIN), 400, mensaje)


def test_json_mal_formado_responde_400(client):
    r = client.post(URL, content='{"tipo": ', headers={**ADMIN,
                                                      "Content-Type": "application/json"})
    assert_error(r, 400, MENSAJE_JSON_INVALIDO)


@pytest.mark.parametrize("params, mensaje", [
    ({"pagina": 0}, "El campo pagina no es válido"),
    ({"tamano": 0}, "El campo tamano no es válido"),
    ({"tamano": 101}, "El campo tamano no es válido"),  # máximo 100
    ({"estado": "OTRO"}, "El campo estado no es válido"),
    ({"tipo": "BARRIO"}, "El campo tipo no es válido"),
])
def test_listar_filtros_invalidos_responde_400(client, params, mensaje):
    assert_error(client.get(URL, params=params), 400, mensaje)


def test_listar_tamano_maximo_100(client):
    r = client.get(URL, params={"tamano": 100})
    assert r.status_code == 200
    assert r.json()["data"]["tamano"] == 100


# Un error inesperado también responde con el envoltorio
def test_error_inesperado_responde_500_con_envoltorio(monkeypatch):
    class ServicioRoto:
        def listar(self, *args):
            raise RuntimeError("falla no prevista")

    monkeypatch.setattr(ubicacion_router, "service", ServicioRoto())
    r = TestClient(app, raise_server_exceptions=False).get(URL)
    assert_error(r, 500, MENSAJE_500)


# Los endpoints generales también usan el envoltorio
def test_inicio_y_health_usan_envoltorio(client):
    for ruta in ("/", "/health"):
        cuerpo = client.get(ruta).json()
        assert set(cuerpo) == {"mensaje", "data", "success"}
        assert cuerpo["success"] is True
