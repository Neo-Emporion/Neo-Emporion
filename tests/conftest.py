# Configuración compartida de las pruebas.
# Cada prueba usa una base SQLite EN MEMORIA nueva (datos limpios) y una
# consulta de direcciones simulada que se puede ajustar por prueba.
# Como en la guía el router crea su `service` una sola vez, aquí se
# reemplaza ese `service` por uno conectado a la base de prueba.

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.api.routers import ubicacion_router
from app.core.database import crear_engine, crear_tablas
from app.domain.interfaces.consulta_direcciones import IConsultaDirecciones
from app.repositories.ubicacion_repository import UbicacionRepository
from app.services.ubicacion_service import UbicacionService
from main import app

URL = "/api/v1/parametrizacion/ubicaciones"
ADMIN = {"Authorization": "Bearer token-administrador"}
COMPRADOR = {"Authorization": "Bearer token-comprador"}


class DireccionesSimuladas(IConsultaDirecciones):
    """Reemplaza la consulta real de direcciones (HU-15 aún no existe)."""

    def __init__(self):
        self.ubicaciones_con_direcciones: set[int] = set()

    def tiene_direcciones_activas(self, ubicacion_id: int) -> bool:
        return ubicacion_id in self.ubicaciones_con_direcciones


@pytest.fixture
def repo():
    """Repositorio sobre una base SQLite en memoria nueva para cada prueba."""
    motor = crear_engine("sqlite:///:memory:")
    crear_tablas(motor)
    yield UbicacionRepository(sessionmaker(bind=motor, expire_on_commit=False))
    motor.dispose()


@pytest.fixture
def direcciones():
    return DireccionesSimuladas()


@pytest.fixture
def client(repo, direcciones, monkeypatch):
    monkeypatch.setattr(ubicacion_router, "service", UbicacionService(repo, direcciones))
    return TestClient(app)


def crear(client, tipo, nombre, codigo, padre_id=None):
    """Registra una ubicación como administrador y devuelve la respuesta."""
    cuerpo = {"tipo": tipo, "nombre": nombre, "codigo": codigo}
    if padre_id is not None:
        cuerpo["padre_id"] = padre_id
    return client.post(URL, json=cuerpo, headers=ADMIN)


@pytest.fixture
def colombia_santander(client):
    """Crea el país Colombia y el departamento Santander. Devuelve sus ids."""
    pais = crear(client, "PAIS", "Colombia", "CO").json()["data"]["id"]
    depto = crear(client, "DEPARTAMENTO", "Santander", "68", pais).json()["data"]["id"]
    return pais, depto
