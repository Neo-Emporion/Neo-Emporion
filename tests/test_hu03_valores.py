# HU-03 Gestionar catálogos transaccionales — casos de prueba funcional
# (al menos un test por cada caso de la HU, con el mismo código HTTP y el mismo `mensaje`)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.dependencies.seguridad import MENSAJE_401, MENSAJE_403
from app.api.routers import valor_router
from app.repositories.valor_repository import ValorRepository
from app.services.valor_service import ValorService
from main import app
from tests.conftest import ADMIN, COMPRADOR, URL_VALORES as URL, crear_valor as crear

# Mensajes exactos de la HU-03
MSG_REGISTRO = "Valor paramétrico registrado exitosamente"
MSG_EDICION = "Valor paramétrico actualizado exitosamente"  # TODO(pendiente): no definido en la HU
MSG_LISTADO = "Consulta de valores paramétricos exitosa"
MSG_DESACTIVACION = "Valor paramétrico desactivado exitosamente"  # TODO(pendiente): no definido
MSG_DUPLICADO = "Ya existe un valor con el mismo código en la categoría"
MSG_CATEGORIA = "La categoría indicada no es válida"
MSG_RN46 = "No es posible desactivar el valor porque está siendo utilizado por otro módulo"
MSG_NO_EXISTE = "El valor paramétrico no existe"
MSG_FALLA_BD = "No fue posible procesar la solicitud de valores paramétricos"


def assert_error(r, codigo, mensaje):
    """Verifica un error con el envoltorio { mensaje, data: null, success: false }."""
    assert r.status_code == codigo
    assert r.json() == {"mensaje": mensaje, "data": None, "success": False}


# ✅ Caso 1: Registrar un valor válido
def test_caso1_registrar_valor_valido(client_valores):
    r = crear(client_valores, "METODO_PAGO", "PSE", "Pago por PSE")
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["mensaje"] == MSG_REGISTRO
    # Estructura exacta del ejemplo de la HU
    assert cuerpo["data"] == {"id": cuerpo["data"]["id"], "categoria": "METODO_PAGO",
                              "codigo": "PSE", "nombre": "Pago por PSE", "estado": "ACTIVO"}


# ✅ Caso 2: Editar un valor
def test_caso2_editar_valor(client_valores):
    valor = crear(client_valores, "METODO_PAGO", "PSE", "Pago por PSE").json()["data"]
    r = client_valores.put(f"{URL}/{valor['id']}",
                           json={"nombre": "Pago en línea por PSE", "descripcion": None},
                           headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert r.json()["mensaje"] == MSG_EDICION
    # El nombre cambia; la categoría y el código se conservan
    assert r.json()["data"] == {"id": valor["id"], "categoria": "METODO_PAGO", "codigo": "PSE",
                                "nombre": "Pago en línea por PSE", "estado": "ACTIVO"}


# ✅ Caso 3: Listar valores de una categoría (solo ACTIVO, RN-49)
def test_caso3_listar_valores_activos(client_valores):
    cop = crear(client_valores, "MONEDA", "COP", "Peso colombiano").json()["data"]["id"]
    usd = crear(client_valores, "MONEDA", "USD", "Dólar").json()["data"]["id"]
    client_valores.patch(f"{URL}/{usd}/desactivar", headers=ADMIN)

    r = client_valores.get(URL, params={"categoria": "MONEDA"})
    assert r.status_code == 200
    assert r.json()["mensaje"] == MSG_LISTADO
    assert r.json()["success"] is True
    # `data` es un arreglo (estructura de la HU)
    assert r.json()["data"] == [{"id": cop, "categoria": "MONEDA", "codigo": "COP",
                                 "nombre": "Peso colombiano", "estado": "ACTIVO"}]


# ✅ Caso 4: Desactivar un valor sin uso
def test_caso4_desactivar_sin_uso(client_valores, repo_valores):
    valor = crear(client_valores, "METODO_PAGO", "PSE", "Pago por PSE").json()["data"]["id"]
    r = client_valores.patch(f"{URL}/{valor}/desactivar", headers=ADMIN)
    assert r.status_code == 200
    assert r.json() == {"mensaje": MSG_DESACTIVACION,
                        "data": {"id": valor, "estado": "INACTIVO"}, "success": True}
    # El registro se conserva (baja lógica)
    assert repo_valores.obtener_por_id(valor).estado == "INACTIVO"


# ❌ Caso 5: Registrar un valor duplicado
def test_caso5_registrar_duplicado(client_valores, repo_valores):
    crear(client_valores, "MONEDA", "COP", "Peso colombiano")
    r = crear(client_valores, "MONEDA", "COP", "Peso")
    assert_error(r, 409, MSG_DUPLICADO)
    # El original no cambia y no se creó otro registro
    assert [(v.codigo, v.nombre) for v in repo_valores.listar("MONEDA", None)] == [
        ("COP", "Peso colombiano")]


# ❌ Caso 6: Categoría no válida
def test_caso6_categoria_no_valida(client_valores, repo_valores):
    r = crear(client_valores, "COLORES", "ROJO", "Rojo")
    assert_error(r, 400, MSG_CATEGORIA)
    # No se creó nada en ninguna categoría
    assert all(repo_valores.listar(c, None) == []
               for c in ("ESTADO", "MONEDA", "UNIDAD_MEDIDA", "METODO_PAGO"))


# ❌ Caso 7: Desactivar un valor en uso (RN-46)
def test_caso7_desactivar_en_uso(client_valores, repo_valores, uso_valores):
    valor = crear(client_valores, "METODO_PAGO", "TC", "Tarjeta de crédito").json()["data"]["id"]
    uso_valores.valores_en_uso.add(valor)

    r = client_valores.patch(f"{URL}/{valor}/desactivar", headers=ADMIN)
    assert_error(r, 409, MSG_RN46)
    assert repo_valores.obtener_por_id(valor).estado == "ACTIVO"


# ❌ Caso 8: Valor inexistente
def test_caso8_editar_inexistente(client_valores):
    r = client_valores.put(f"{URL}/99999", json={"nombre": "X", "descripcion": None},
                           headers=ADMIN)
    assert_error(r, 404, MSG_NO_EXISTE)


def test_caso8_desactivar_inexistente(client_valores):
    r = client_valores.patch(f"{URL}/99999/desactivar", headers=ADMIN)
    assert_error(r, 404, MSG_NO_EXISTE)


# ❌ Caso 9: Usuario sin permisos
def test_caso9_sin_permisos(client_valores, repo_valores):
    r = client_valores.post(URL, json={"categoria": "MONEDA", "codigo": "COP",
                                       "nombre": "Peso colombiano"}, headers=COMPRADOR)
    assert_error(r, 403, MENSAJE_403)
    assert repo_valores.listar("MONEDA", None) == []  # no se creó ningún registro


# ❌ Caso 10: Falla de base de datos
def test_caso10_falla_base_de_datos(tmp_path, uso_valores, monkeypatch):
    # Base de datos inalcanzable: la carpeta del archivo SQLite no existe.
    motor_caido = create_engine(f"sqlite:///{tmp_path}/no_existe/bd.db")
    repo_caido = ValorRepository(sessionmaker(bind=motor_caido))
    monkeypatch.setattr(valor_router, "service", ValorService(repo_caido, uso_valores))
    client = TestClient(app)

    peticiones = [
        client.post(URL, json={"categoria": "MONEDA", "codigo": "COP",
                               "nombre": "Peso colombiano"}, headers=ADMIN),
        client.put(f"{URL}/1", json={"nombre": "X", "descripcion": None}, headers=ADMIN),
        client.get(URL, params={"categoria": "MONEDA"}),
        client.patch(f"{URL}/1/desactivar", headers=ADMIN),
    ]
    for r in peticiones:
        assert_error(r, 503, MSG_FALLA_BD)


# ── Casos adicionales (Definición de Hecho y decisiones del proyecto) ──

# Listado sin resultados (Definición de Hecho)
def test_listado_sin_resultados(client_valores):
    r = client_valores.get(URL, params={"categoria": "UNIDAD_MEDIDA"})
    assert r.status_code == 200
    assert r.json() == {"mensaje": MSG_LISTADO, "data": [], "success": True}


def test_listado_solo_de_la_categoria_pedida(client_valores):
    crear(client_valores, "MONEDA", "COP", "Peso colombiano")
    crear(client_valores, "METODO_PAGO", "PSE", "Pago por PSE")
    data = client_valores.get(URL, params={"categoria": "MONEDA"}).json()["data"]
    assert [v["codigo"] for v in data] == ["COP"]


@pytest.mark.parametrize("estado, esperados", [
    ("INACTIVO", [("USD", "INACTIVO")]),
    ("TODOS", [("COP", "ACTIVO"), ("USD", "INACTIVO")]),
])
def test_listado_filtro_estado(client_valores, estado, esperados):
    crear(client_valores, "MONEDA", "COP", "Peso colombiano")
    usd = crear(client_valores, "MONEDA", "USD", "Dólar").json()["data"]["id"]
    client_valores.patch(f"{URL}/{usd}/desactivar", headers=ADMIN)
    r = client_valores.get(URL, params={"categoria": "MONEDA", "estado": estado})
    assert r.status_code == 200
    assert [(v["codigo"], v["estado"]) for v in r.json()["data"]] == esperados


def test_listar_sin_categoria_responde_400(client_valores):
    assert_error(client_valores.get(URL), 400, "El campo categoria es obligatorio")


def test_listar_categoria_no_valida_responde_400(client_valores):
    assert_error(client_valores.get(URL, params={"categoria": "COLORES"}), 400, MSG_CATEGORIA)


def test_categoria_con_espacios_funciona_igual_en_post_y_get(client_valores):
    assert crear(client_valores, " MONEDA ", "COP", "Peso colombiano").status_code == 201
    r = client_valores.get(URL, params={"categoria": " MONEDA "})
    assert [v["codigo"] for v in r.json()["data"]] == ["COP"]


@pytest.mark.parametrize("categoria", [5, None, True, ["MONEDA"]])
def test_categoria_que_no_es_texto_responde_mensaje_de_la_hu(client_valores, categoria):
    r = client_valores.post(URL, json={"categoria": categoria, "codigo": "X", "nombre": "X"},
                            headers=ADMIN)
    assert_error(r, 400, MSG_CATEGORIA)


def test_listar_estado_no_valido_responde_400(client_valores):
    r = client_valores.get(URL, params={"categoria": "MONEDA", "estado": "OTRO"})
    assert_error(r, 400, "El campo estado no es válido")


# Unicidad: el mismo código sí se permite en otra categoría
def test_mismo_codigo_en_otra_categoria_si_se_permite(client_valores):
    assert crear(client_valores, "ESTADO", "ACT", "Activo").status_code == 201
    assert crear(client_valores, "METODO_PAGO", "ACT", "Otro").status_code == 201


def test_codigo_con_otras_mayusculas_no_es_duplicado(client_valores):
    # Registro de cambios #10: el código se compara exacto
    crear(client_valores, "MONEDA", "COP", "Peso colombiano")
    assert crear(client_valores, "MONEDA", "cop", "Otro").status_code == 201


def test_espacios_se_recortan_y_cuentan_como_duplicado(client_valores):
    r = crear(client_valores, "MONEDA", " COP ", "  Peso colombiano ")
    assert r.status_code == 201
    assert (r.json()["data"]["codigo"], r.json()["data"]["nombre"]) == ("COP", "Peso colombiano")
    assert_error(crear(client_valores, "MONEDA", "COP ", "Otro"), 409, MSG_DUPLICADO)


# Editar: categoría y código no cambian aunque se envíen
def test_editar_ignora_categoria_y_codigo(client_valores):
    valor = crear(client_valores, "MONEDA", "COP", "Peso colombiano").json()["data"]["id"]
    r = client_valores.put(f"{URL}/{valor}",
                           json={"categoria": "METODO_PAGO", "codigo": "XXX",
                                 "nombre": "Peso", "descripcion": "Moneda oficial"},
                           headers=ADMIN)
    assert r.status_code == 200
    assert (r.json()["data"]["categoria"], r.json()["data"]["codigo"]) == ("MONEDA", "COP")


def test_editar_guarda_descripcion_sin_exponerla(client_valores, repo_valores):
    valor = crear(client_valores, "MONEDA", "COP", "Peso colombiano").json()["data"]["id"]
    r = client_valores.put(f"{URL}/{valor}",
                           json={"nombre": "Peso colombiano", "descripcion": "Moneda oficial"},
                           headers=ADMIN)
    assert r.status_code == 200
    # La respuesta conserva la estructura de la HU (sin `descripcion`)...
    assert "descripcion" not in r.json()["data"]
    # ...pero la descripción sí quedó guardada
    assert repo_valores.obtener_por_id(valor).descripcion == "Moneda oficial"


def test_editar_un_valor_inactivo_lo_deja_inactivo(client_valores):
    # RN-49: editar no reactiva un valor; sigue sin aparecer en el listado por defecto
    valor = crear(client_valores, "MONEDA", "USD", "Dólar").json()["data"]["id"]
    client_valores.patch(f"{URL}/{valor}/desactivar", headers=ADMIN)
    r = client_valores.put(f"{URL}/{valor}", json={"nombre": "Dólar americano", "descripcion": None},
                           headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["data"]["estado"] == "INACTIVO"
    assert client_valores.get(URL, params={"categoria": "MONEDA"}).json()["data"] == []


def test_desactivar_dos_veces_responde_200(client_valores, uso_valores):
    # Registro de cambios #12; aunque luego quede "en uso", ya no aplica RN-46
    valor = crear(client_valores, "MONEDA", "USD", "Dólar").json()["data"]["id"]
    client_valores.patch(f"{URL}/{valor}/desactivar", headers=ADMIN)
    uso_valores.valores_en_uso.add(valor)
    r = client_valores.patch(f"{URL}/{valor}/desactivar", headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["data"] == {"id": valor, "estado": "INACTIVO"}


@pytest.mark.parametrize("metodo", ["put", "patch"])
def test_id_demasiado_grande_responde_400(client_valores, metodo):
    id_enorme = 2**63  # no cabe en un entero de 64 bits
    if metodo == "put":
        r = client_valores.put(f"{URL}/{id_enorme}", json={"nombre": "X", "descripcion": None},
                               headers=ADMIN)
    else:
        r = client_valores.patch(f"{URL}/{id_enorme}/desactivar", headers=ADMIN)
    assert_error(r, 400, "El campo id no es válido")


@pytest.mark.parametrize("cuerpo, mensaje", [
    ({"descripcion": None}, "El campo nombre es obligatorio"),
    ({"nombre": "Peso"}, "El campo descripcion es obligatorio"),
    ({"nombre": "", "descripcion": None}, "El campo nombre no es válido"),
    ({"nombre": "A" * 81, "descripcion": None}, "El campo nombre no es válido"),
    ({"nombre": "Peso", "descripcion": "A" * 256}, "El campo descripcion no es válido"),
])
def test_editar_datos_invalidos_responde_400(client_valores, cuerpo, mensaje):
    valor = crear(client_valores, "MONEDA", "COP", "Peso colombiano").json()["data"]["id"]
    assert_error(client_valores.put(f"{URL}/{valor}", json=cuerpo, headers=ADMIN), 400, mensaje)


@pytest.mark.parametrize("cuerpo, mensaje", [
    ({"codigo": "COP", "nombre": "Peso"}, "El campo categoria es obligatorio"),
    ({"categoria": "MONEDA", "nombre": "Peso"}, "El campo codigo es obligatorio"),
    ({"categoria": "MONEDA", "codigo": "COP"}, "El campo nombre es obligatorio"),
    ({"categoria": "MONEDA", "codigo": "COP", "nombre": "A" * 81}, "El campo nombre no es válido"),
    ({"categoria": "MONEDA", "codigo": "C" * 51, "nombre": "Peso"}, "El campo codigo no es válido"),
    ({"categoria": "MONEDA", "codigo": "   ", "nombre": "Peso"}, "El campo codigo no es válido"),
])
def test_registrar_datos_invalidos_responde_400(client_valores, cuerpo, mensaje):
    assert_error(client_valores.post(URL, json=cuerpo, headers=ADMIN), 400, mensaje)


# Seguridad: registrar, editar y desactivar son solo para el Administrador
@pytest.mark.parametrize("token, codigo, mensaje", [
    (None, 401, MENSAJE_401),
    ("token-invalido", 401, MENSAJE_401),
    ("token-comprador", 403, MENSAJE_403),
    ("token-vendedor", 403, MENSAJE_403),
])
@pytest.mark.parametrize("operacion", ["registrar", "editar", "desactivar"])
def test_operaciones_solo_administrador(client_valores, repo_valores,
                                        operacion, token, codigo, mensaje):
    valor = crear(client_valores, "MONEDA", "COP", "Peso colombiano").json()["data"]["id"]
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    if operacion == "registrar":
        r = client_valores.post(URL, json={"categoria": "MONEDA", "codigo": "USD",
                                           "nombre": "Dólar"}, headers=headers)
    elif operacion == "editar":
        r = client_valores.put(f"{URL}/{valor}", json={"nombre": "Otro", "descripcion": None},
                               headers=headers)
    else:
        r = client_valores.patch(f"{URL}/{valor}/desactivar", headers=headers)
    assert_error(r, codigo, mensaje)
    # No cambió nada
    valores = repo_valores.listar("MONEDA", None)
    assert [(v.codigo, v.nombre, v.estado) for v in valores] == [
        ("COP", "Peso colombiano", "ACTIVO")]
