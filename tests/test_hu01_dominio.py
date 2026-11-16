# HU-01 — pruebas unitarias de las reglas de dominio (jerarquía y RN-47)

import pytest

from app.domain.models.dato_geografico import DatoGeografico, EstadoUbicacion, TipoUbicacion
from app.domain.exceptions.ubicacion import DesactivacionNoPermitida, JerarquiaInvalida

PAIS = DatoGeografico(1, TipoUbicacion.PAIS, "Colombia", "CO", None)
DEPTO = DatoGeografico(68, TipoUbicacion.DEPARTAMENTO, "Santander", "68", 1)
CIUDAD = DatoGeografico(1203, TipoUbicacion.CIUDAD, "Bucaramanga", "68001", 68)


@pytest.mark.parametrize("tipo, padre", [
    (TipoUbicacion.PAIS, None),
    (TipoUbicacion.DEPARTAMENTO, PAIS),
    (TipoUbicacion.CIUDAD, DEPTO),
])
def test_jerarquia_valida(tipo, padre):
    DatoGeografico.validar_jerarquia(tipo, padre.id if padre else None, padre)


@pytest.mark.parametrize("tipo, padre_id, padre", [
    (TipoUbicacion.PAIS, 1, PAIS),            # un país no admite padre
    (TipoUbicacion.DEPARTAMENTO, None, None),  # departamento sin padre
    (TipoUbicacion.DEPARTAMENTO, 68, DEPTO),   # departamento bajo departamento
    (TipoUbicacion.CIUDAD, 1, PAIS),           # ciudad bajo país (Caso 6)
    (TipoUbicacion.CIUDAD, 1203, CIUDAD),      # ciudad bajo ciudad
    (TipoUbicacion.CIUDAD, 555, None),         # padre inexistente
])
def test_jerarquia_invalida(tipo, padre_id, padre):
    with pytest.raises(JerarquiaInvalida):
        DatoGeografico.validar_jerarquia(tipo, padre_id, padre)


def test_nueva_ubicacion_activa_y_no_publicada():
    u = DatoGeografico(1, TipoUbicacion.PAIS, "Colombia", "CO", None)
    assert u.estado == EstadoUbicacion.ACTIVO
    assert u.publicada is False


def test_desactivar_sin_uso():
    u = DatoGeografico(1, TipoUbicacion.CIUDAD, "Bucaramanga", "68001", 68)
    u.desactivar(tiene_direcciones_activas=False, tiene_hijas_activas=False)
    assert u.estado == EstadoUbicacion.INACTIVO


@pytest.mark.parametrize("direcciones, hijas", [(True, False), (False, True), (True, True)])
def test_rn47_no_desactiva_en_uso(direcciones, hijas):
    u = DatoGeografico(1, TipoUbicacion.DEPARTAMENTO, "Santander", "68", 1)
    with pytest.raises(DesactivacionNoPermitida):
        u.desactivar(tiene_direcciones_activas=direcciones, tiene_hijas_activas=hijas)
    assert u.estado == EstadoUbicacion.ACTIVO


def test_editar_cambia_datos_y_conserva_tipo():
    u = DatoGeografico(1203, TipoUbicacion.CIUDAD, "Bucaramnga", "68001", 68)
    u.editar("Bucaramanga", "68001", 68, DEPTO)
    assert (u.nombre, u.tipo, u.padre_id) == ("Bucaramanga", TipoUbicacion.CIUDAD, 68)


def test_editar_con_jerarquia_invalida_no_cambia_nada():
    u = DatoGeografico(1203, TipoUbicacion.CIUDAD, "Bucaramanga", "68001", 68)
    with pytest.raises(JerarquiaInvalida):
        u.editar("Otro", "999", 1, PAIS)  # una ciudad no puede colgar de un país
    assert (u.nombre, u.codigo, u.padre_id) == ("Bucaramanga", "68001", 68)


# ── Duplicidad (regla de la HU-01, aplicada por el servicio) ──
# La Definición de Hecho pide pruebas unitarias de jerarquía, duplicidad y RN-47.

from app.domain.exceptions.ubicacion import UbicacionDuplicada, UbicacionNoEncontrada
from app.domain.models.dato_geografico import UbicacionCreate
from app.services.ubicacion_service import UbicacionService


@pytest.fixture
def servicio(repo, direcciones):
    s = UbicacionService(repo, direcciones)
    pais = s.registrar(UbicacionCreate(tipo="PAIS", nombre="Colombia", codigo="CO"))
    s.registrar(UbicacionCreate(tipo="DEPARTAMENTO", nombre="Santander", codigo="68",
                                padre_id=pais.id))
    return s


def test_duplicado_por_tipo_nombre_y_padre(servicio):
    with pytest.raises(UbicacionDuplicada):
        servicio.registrar(UbicacionCreate(tipo="DEPARTAMENTO", nombre="Santander",
                                           codigo="99", padre_id=1))


def test_duplicado_por_codigo(servicio):
    with pytest.raises(UbicacionDuplicada):
        servicio.registrar(UbicacionCreate(tipo="DEPARTAMENTO", nombre="Boyacá",
                                           codigo="68", padre_id=1))


def test_mismo_nombre_otro_tipo_no_es_duplicado(servicio):
    # Mismo nombre que el departamento, pero es una CIUDAD (otro nivel)
    r = servicio.registrar(UbicacionCreate(tipo="CIUDAD", nombre="Santander",
                                           codigo="68999", padre_id=2))
    assert r.tipo == TipoUbicacion.CIUDAD


def test_editarse_a_si_misma_no_es_duplicado(servicio):
    from app.domain.models.dato_geografico import UbicacionUpdate
    r = servicio.editar(2, UbicacionUpdate(nombre="Santander", codigo="68", padre_id=1))
    assert r.nombre == "Santander"


# ── Repositorio: la base también protege la unicidad del código ──

def test_codigo_repetido_en_la_base_es_duplicado(repo):
    # Simula dos peticiones simultáneas que pasaron la validación del servicio
    repo.crear(TipoUbicacion.PAIS, "Colombia", "CO", None)
    with pytest.raises(UbicacionDuplicada):
        repo.crear(TipoUbicacion.PAIS, "Otro", "CO", None)


def test_guardar_ubicacion_inexistente(repo):
    with pytest.raises(UbicacionNoEncontrada):
        repo.guardar(DatoGeografico(99999, TipoUbicacion.PAIS, "X", "X", None))
