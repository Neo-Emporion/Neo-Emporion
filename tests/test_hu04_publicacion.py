# HU-04 Publicar dato geográfico para otros módulos — casos de prueba funcional
# (un test por cada caso de la HU, con el mismo código HTTP y el mismo `mensaje`)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.dependencies.seguridad import MENSAJE_403
from app.api.routers import ubicacion_router
from app.repositories.ubicacion_repository import UbicacionRepository
from app.services.ubicacion_service import UbicacionService
from main import app
from tests.conftest import ADMIN, COMPRADOR, URL, crear

# Mensajes exactos de la HU-04
MSG_PUBLICACION = "Ubicación publicada exitosamente"
MSG_PADRE = "No es posible publicar la ubicación porque su ubicación padre no está publicada"
MSG_INACTIVA = "No es posible publicar una ubicación inactiva"
MSG_NO_EXISTE = "La ubicación no existe"
MSG_FALLA_BD = "No fue posible publicar la ubicación"

VENDEDOR = {"Authorization": "Bearer token-vendedor"}


def assert_error(r, codigo, mensaje):
    """Verifica un error con el envoltorio { mensaje, data: null, success: false }."""
    assert r.status_code == codigo
    assert r.json() == {"mensaje": mensaje, "data": None, "success": False}


def publicar(client, id):
    """Publica una ubicación como administrador y devuelve la respuesta."""
    return client.patch(f"{URL}/{id}/publicar", headers=ADMIN)


def crear_ciudad(client, colombia_santander):
    """Crea la ciudad Bucaramanga bajo el departamento Santander."""
    _, santander = colombia_santander
    return crear(client, "CIUDAD", "Bucaramanga", "68001", santander).json()["data"]["id"]


# ✅ Caso 1: Publicar una ubicación válida
def test_caso1_publicar_ubicacion_valida(client, repo, colombia_santander):
    colombia, santander = colombia_santander
    ciudad = crear_ciudad(client, colombia_santander)

    # La jerarquía completa debe estar publicada: país y departamento primero
    assert publicar(client, colombia).status_code == 200
    assert publicar(client, santander).status_code == 200

    r = publicar(client, ciudad)
    assert r.status_code == 200
    assert r.json() == {
        "mensaje": MSG_PUBLICACION,
        "data": {"id": ciudad, "nombre": "Bucaramanga", "estado": "ACTIVO",
                 "publicada": True},
        "success": True,
    }
    assert repo.obtener_por_id(ciudad).publicada is True


# ✅ Caso 2: Publicar una ubicación ya publicada (idempotencia)
def test_caso2_publicar_ya_publicada_es_idempotente(client, repo, colombia_santander):
    colombia, santander = colombia_santander
    ciudad = crear_ciudad(client, colombia_santander)
    publicar(client, colombia)
    publicar(client, santander)

    primera = publicar(client, ciudad)
    antes = repo.obtener_por_id(ciudad).to_response()
    segunda = publicar(client, ciudad)
    despues = repo.obtener_por_id(ciudad).to_response()

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert segunda.json() == primera.json()
    assert segunda.json()["data"]["publicada"] is True
    # La ubicación no cambió
    assert despues == antes
    assert despues["publicada"] is True


# ✅ Caso 3: Consumo solo de ubicaciones activas y publicadas (API-I09)
def test_caso3_consumo_solo_ubicaciones_activas_y_publicadas(client, colombia_santander):
    colombia, santander = colombia_santander
    bucaramanga = crear_ciudad(client, colombia_santander)
    giron = crear(client, "CIUDAD", "Girón", "68307", santander).json()["data"]["id"]
    floridablanca = crear(client, "CIUDAD", "Floridablanca", "68276",
                          santander).json()["data"]["id"]

    # Publica país, departamento y dos ciudades
    for ubicacion in (colombia, santander, bucaramanga, floridablanca):
        assert publicar(client, ubicacion).status_code == 200
    # Floridablanca queda publicada pero INACTIVA
    assert client.patch(f"{URL}/{floridablanca}/desactivar",
                        headers=ADMIN).status_code == 200

    # Vista de consumo: solo ACTIVO y publicada = true
    r = client.get(URL, params={"solo_publicadas": True})
    assert r.status_code == 200
    ids = [u["id"] for u in r.json()["data"]["ubicaciones"]]
    assert ids == [colombia, santander, bucaramanga]
    assert all(u["estado"] == "ACTIVO" for u in r.json()["data"]["ubicaciones"])

    # Aunque el consumidor pida TODOS, la vista de consumo sigue filtrando ACTIVO
    r_todos = client.get(URL, params={"solo_publicadas": True, "estado": "TODOS"})
    assert [u["id"] for u in r_todos.json()["data"]["ubicaciones"]] == [
        colombia, santander, bucaramanga]

    # Filtros de la API-I09: ciudad publicada de un departamento
    r_filtrada = client.get(URL, params={"tipo": "CIUDAD", "padre_id": santander,
                                         "solo_publicadas": True})
    assert [u["id"] for u in r_filtrada.json()["data"]["ubicaciones"]] == [bucaramanga]

    # El uso administrativo (sin el parámetro) no cambia: incluye Girón (no publicada)
    # y excluye a Floridablanca por estar INACTIVA.
    ids_admin = [u["id"] for u in client.get(URL).json()["data"]["ubicaciones"]]
    assert ids_admin == [colombia, santander, bucaramanga, giron]


# ❌ Caso 4: Padre no publicado
def test_caso4_padre_no_publicado(client, repo, colombia_santander):
    colombia, _ = colombia_santander
    ciudad = crear_ciudad(client, colombia_santander)
    # Se publica el país, pero no el departamento padre de la ciudad
    assert publicar(client, colombia).status_code == 200

    r = publicar(client, ciudad)
    assert_error(r, 409, MSG_PADRE)
    assert repo.obtener_por_id(ciudad).publicada is False


# ❌ Caso 5: Ubicación inactiva
def test_caso5_ubicacion_inactiva(client, repo):
    pais = crear(client, "PAIS", "Colombia", "CO").json()["data"]["id"]
    assert client.patch(f"{URL}/{pais}/desactivar", headers=ADMIN).status_code == 200

    r = publicar(client, pais)
    assert_error(r, 409, MSG_INACTIVA)
    assert repo.obtener_por_id(pais).publicada is False


# ❌ Caso 6: Ubicación inexistente
def test_caso6_ubicacion_inexistente(client):
    assert_error(publicar(client, 99999), 404, MSG_NO_EXISTE)


# ❌ Caso 7: Usuario sin permisos
@pytest.mark.parametrize("headers", [COMPRADOR, VENDEDOR])
def test_caso7_usuario_sin_permisos(client, repo, colombia_santander, headers):
    _, santander = colombia_santander
    r = client.patch(f"{URL}/{santander}/publicar", headers=headers)
    assert_error(r, 403, MENSAJE_403)
    assert repo.obtener_por_id(santander).publicada is False


# ❌ Caso 8: Falla de base de datos
def test_caso8_falla_base_de_datos(tmp_path, direcciones, monkeypatch):
    # Base de datos inalcanzable: la carpeta del archivo SQLite no existe.
    motor_caido = create_engine(f"sqlite:///{tmp_path}/no_existe/bd.db")
    repo_caido = UbicacionRepository(sessionmaker(bind=motor_caido))
    monkeypatch.setattr(ubicacion_router, "service",
                        UbicacionService(repo_caido, direcciones))
    client = TestClient(app)

    assert_error(publicar(client, 1), 503, MSG_FALLA_BD)
