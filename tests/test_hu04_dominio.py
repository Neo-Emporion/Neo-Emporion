# HU-04 — pruebas unitarias de la regla de publicación y de la idempotencia

import pytest

from app.domain.exceptions.ubicacion import PadreNoPublicado, UbicacionInactiva
from app.domain.models.dato_geografico import DatoGeografico, EstadoUbicacion, TipoUbicacion


def pais(publicada=False, estado=EstadoUbicacion.ACTIVO):
    return DatoGeografico(1, TipoUbicacion.PAIS, "Colombia", "CO", None,
                          estado=estado, publicada=publicada)


def departamento(padre, publicada=False, estado=EstadoUbicacion.ACTIVO):
    return DatoGeografico(68, TipoUbicacion.DEPARTAMENTO, "Santander", "68", padre.id,
                          estado=estado, publicada=publicada)


def ciudad(padre, publicada=False, estado=EstadoUbicacion.ACTIVO):
    return DatoGeografico(1203, TipoUbicacion.CIUDAD, "Bucaramanga", "68001", padre.id,
                          estado=estado, publicada=publicada)


def test_publicar_pais_sin_padre():
    colombia = pais()
    colombia.publicar(padre=None)
    assert colombia.publicada is True
    assert colombia.estado == EstadoUbicacion.ACTIVO


def test_publicar_departamento_con_pais_publicado():
    colombia = pais(publicada=True)
    santander = departamento(colombia)
    santander.publicar(padre=colombia)
    assert santander.publicada is True


def test_publicar_ciudad_con_departamento_publicado():
    colombia = pais(publicada=True)
    santander = departamento(colombia, publicada=True)
    bucaramanga = ciudad(santander)
    bucaramanga.publicar(padre=santander)
    assert bucaramanga.publicada is True


@pytest.mark.parametrize("ubicacion, padre", [
    (departamento(pais()), pais()),          # padre no publicado
    (ciudad(departamento(pais())), None),    # padre inexistente
])
def test_publicar_con_padre_no_publicado(ubicacion, padre):
    with pytest.raises(PadreNoPublicado):
        ubicacion.publicar(padre=padre)
    assert ubicacion.publicada is False


@pytest.mark.parametrize("estado", [EstadoUbicacion.INACTIVO])
def test_publicar_ubicacion_inactiva(estado):
    colombia = pais(estado=estado)
    with pytest.raises(UbicacionInactiva):
        colombia.publicar(padre=None)
    assert colombia.publicada is False


def test_publicar_es_idempotente():
    colombia = pais(publicada=True)
    santander = departamento(colombia, publicada=True)
    bucaramanga = ciudad(santander, publicada=True)
    # Ya publicada: no vuelve a validar ni cambia nada (HU-04, Caso 2)
    bucaramanga.publicar(padre=None)
    assert bucaramanga.publicada is True
    assert (bucaramanga.nombre, bucaramanga.codigo, bucaramanga.padre_id) == (
        "Bucaramanga", "68001", 68)


def test_publicar_no_cambia_los_demas_campos():
    colombia = pais()
    colombia.publicar(padre=None)
    assert (colombia.id, colombia.tipo, colombia.nombre, colombia.codigo,
            colombia.padre_id, colombia.estado) == (
        1, TipoUbicacion.PAIS, "Colombia", "CO", None, EstadoUbicacion.ACTIVO)
