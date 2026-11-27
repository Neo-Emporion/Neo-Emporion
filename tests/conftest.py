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
from app.api.routers import tipo_documento_router
from app.domain.interfaces.consulta_uso_tipo_documento import IConsultaUsoTipoDocumento
from app.repositories.tipo_documento_repository import TipoDocumentoRepository
from app.services.tipo_documento_service import TipoDocumentoService
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


class UsoTipoDocumentoSimulado(IConsultaUsoTipoDocumento):
    """Reemplaza la consulta real hasta que existan compradores y vendedores."""

    def __init__(self):
        self.tipos_en_uso: set[int] = set()

    def tiene_compradores_o_vendedores_activos(
        self, tipo_documento_id: int
    ) -> bool:
        return tipo_documento_id in self.tipos_en_uso


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


@pytest.fixture
def repo_tipo_documento():
    motor = crear_engine("sqlite:///:memory:")
    crear_tablas(motor)
    yield TipoDocumentoRepository(
        sessionmaker(bind=motor, expire_on_commit=False)
    )
    motor.dispose()


@pytest.fixture
def uso_tipo_documento():
    return UsoTipoDocumentoSimulado()


@pytest.fixture
def servicio_tipo_documento(repo_tipo_documento, uso_tipo_documento):
    return TipoDocumentoService(repo_tipo_documento, uso_tipo_documento)


@pytest.fixture
def client_tipo_documento(
    repo_tipo_documento,
    uso_tipo_documento,
    monkeypatch,
):
    servicio = TipoDocumentoService(repo_tipo_documento, uso_tipo_documento)
    monkeypatch.setattr(tipo_documento_router, "service", servicio)
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


# ── HU-03 Catálogos transaccionales ───────────────────────────
from app.api.routers import valor_router  # noqa: E402
from app.domain.interfaces.consulta_uso_valores import IConsultaUsoValores  # noqa: E402
from app.repositories.valor_repository import ValorRepository  # noqa: E402
from app.services.valor_service import ValorService  # noqa: E402

URL_VALORES = "/api/v1/parametrizacion/valores"


class UsoValoresSimulado(IConsultaUsoValores):
    """Reemplaza la consulta real de uso (los módulos consumidores aún no existen)."""

    def __init__(self):
        self.valores_en_uso: set[int] = set()

    def esta_en_uso(self, valor_id: int) -> bool:
        return valor_id in self.valores_en_uso


@pytest.fixture
def repo_valores():
    """Repositorio de valores sobre una base SQLite en memoria nueva para cada prueba."""
    motor = crear_engine("sqlite:///:memory:")
    crear_tablas(motor)
    yield ValorRepository(sessionmaker(bind=motor, expire_on_commit=False))
    motor.dispose()


@pytest.fixture
def uso_valores():
    return UsoValoresSimulado()


@pytest.fixture
def client_valores(repo_valores, uso_valores, monkeypatch):
    monkeypatch.setattr(valor_router, "service", ValorService(repo_valores, uso_valores))
    return TestClient(app)


def crear_valor(client, categoria, codigo, nombre):
    """Registra un valor paramétrico como administrador y devuelve la respuesta."""
    return client.post(URL_VALORES, json={"categoria": categoria, "codigo": codigo,
                                          "nombre": nombre}, headers=ADMIN)


# ── HU-05 Formato de validación de tipo de documento ──────────
from app.api.routers import formato_router  # noqa: E402
from app.domain.interfaces.consulta_registros_tipo_documento import (  # noqa: E402
    IConsultaRegistrosTipoDocumento,
)
from app.repositories.formato_repository import FormatoRepository  # noqa: E402
from app.services.formato_service import FormatoService  # noqa: E402


class RegistrosTipoDocumentoSimulados(IConsultaRegistrosTipoDocumento):
    """Reemplaza la consulta real (compradores HU-07 y vendedores HU-08 aún no existen)."""

    def __init__(self):
        self.tipos_con_registros: set[int] = set()

    def tiene_registros_asociados(self, tipo_documento_id: int) -> bool:
        return tipo_documento_id in self.tipos_con_registros


@pytest.fixture
def sesiones_formato():
    """Una base SQLite en memoria nueva, compartida por tipos de documento y formatos."""
    motor = crear_engine("sqlite:///:memory:")
    crear_tablas(motor)
    yield sessionmaker(bind=motor, expire_on_commit=False)
    motor.dispose()


@pytest.fixture
def tipos_formato(sesiones_formato):
    """Repositorio de tipos de documento (HU-02) sobre la base de la prueba."""
    return TipoDocumentoRepository(sesiones_formato)


@pytest.fixture
def repo_formatos(sesiones_formato):
    return FormatoRepository(sesiones_formato)


@pytest.fixture
def registros_tipo_documento():
    return RegistrosTipoDocumentoSimulados()


@pytest.fixture
def client_formato(repo_formatos, tipos_formato, registros_tipo_documento, monkeypatch):
    monkeypatch.setattr(formato_router, "service",
                        FormatoService(repo_formatos, tipos_formato, registros_tipo_documento))
    return TestClient(app)


# ── HU-07 Registrar e iniciar sesión como comprador ───────────
from app.api.routers import comprador_router  # noqa: E402
from app.core import autenticacion  # noqa: E402
from app.repositories.comprador_repository import CompradorRepository  # noqa: E402
from app.services.comprador_service import CompradorService  # noqa: E402
from app.services.consulta_tipos_documento import ConsultaTiposDocumento  # noqa: E402


@pytest.fixture(autouse=True)
def cifrado_rapido(monkeypatch):
    """Cifrar con 600 000 vueltas tarda casi medio segundo. En las pruebas se usan
    menos vueltas para que la suite sea rápida (el algoritmo es el mismo)."""
    monkeypatch.setattr(autenticacion, "ITERACIONES", 1_000)


@pytest.fixture
def sesiones_comprador():
    """Una base SQLite en memoria nueva, compartida por tipos, formatos y compradores."""
    motor = crear_engine("sqlite:///:memory:")
    crear_tablas(motor)
    yield sessionmaker(bind=motor, expire_on_commit=False)
    motor.dispose()


@pytest.fixture
def tipos_comprador(sesiones_comprador):
    """Repositorio de tipos de documento (HU-02) sobre la base de la prueba."""
    return TipoDocumentoRepository(sesiones_comprador)


@pytest.fixture
def formatos_comprador(sesiones_comprador):
    """Repositorio de formatos (HU-05) sobre la base de la prueba."""
    return FormatoRepository(sesiones_comprador)


@pytest.fixture
def repo_compradores(sesiones_comprador):
    return CompradorRepository(sesiones_comprador)


@pytest.fixture
def client_comprador(repo_compradores, tipos_comprador, formatos_comprador, monkeypatch):
    consulta = ConsultaTiposDocumento(tipos_comprador, formatos_comprador)
    monkeypatch.setattr(comprador_router, "service", CompradorService(repo_compradores, consulta))
    return TestClient(app)
