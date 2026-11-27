# HU-05 — pruebas unitarias de las validaciones de dominio
# (la Definición de Hecho pide: validación del patrón, de las longitudes y de RN-50)

import pytest

from app.domain.exceptions.formato import (
    EjemploNoCumplePatron,
    FormatoConRegistros,
    LongitudesInconsistentes,
    PatronInvalido,
)
from app.domain.models.formato_validacion import FormatoValidacion

NIT = dict(tipo_documento_id=4, patron="^[0-9]{9}-[0-9]$", longitud_min=11, longitud_max=11,
           ejemplo="900123456-7")


def test_crear_formato_valido():
    f = FormatoValidacion.crear(**NIT)
    assert f.to_response() == {"patron": "^[0-9]{9}-[0-9]$", "longitud_min": 11,
                               "longitud_max": 11, "ejemplo": "900123456-7"}


# ── Validación del patrón ─────────────────────────────────────

@pytest.mark.parametrize("patron", ["[0-9{", "(abc", "*", "[a-", "a{99999999999}"])
def test_patron_invalido(patron):
    with pytest.raises(PatronInvalido):
        FormatoValidacion.crear(**{**NIT, "patron": patron})


def test_ejemplo_que_no_cumple_el_patron():
    with pytest.raises(EjemploNoCumplePatron):
        FormatoValidacion.crear(**{**NIT, "ejemplo": "ABCDEFGHI-J"})


def test_el_patron_debe_cumplirse_completo():
    # Sin anclas ^ y $, "123" aparece dentro de "A123", pero no la cumple completa
    with pytest.raises(EjemploNoCumplePatron):
        FormatoValidacion.crear(4, "[0-9]{3}", 1, 10, "A123")


# ── Validación de las longitudes ──────────────────────────────

def test_longitud_minima_mayor_que_maxima():
    with pytest.raises(LongitudesInconsistentes):
        FormatoValidacion.crear(**{**NIT, "longitud_min": 12, "longitud_max": 8})


def test_longitud_minima_igual_a_maxima_es_valida():
    assert FormatoValidacion.crear(**NIT).longitud_min == 11


@pytest.mark.parametrize("ejemplo", ["12", "123456789"])
def test_ejemplo_fuera_de_las_longitudes(ejemplo):
    with pytest.raises(EjemploNoCumplePatron):
        FormatoValidacion.crear(4, "^[0-9]+$", 3, 8, ejemplo)


def test_orden_de_validacion_patron_primero():
    # Si el patrón es inválido y además las longitudes son inconsistentes, se reporta el patrón
    with pytest.raises(PatronInvalido):
        FormatoValidacion.crear(4, "[0-9{", 12, 8, "x")


# ── Uso del formato por los registros (Caso 2) ────────────────

@pytest.mark.parametrize("numero, valido", [
    ("900123456-7", True),
    ("900123456", False),       # no cumple el patrón
    ("9001234567-8", False),    # no cumple el patrón y es más largo de lo permitido
    ("90012345A-7", False),     # letra
])
def test_numero_es_valido(numero, valido):
    assert FormatoValidacion.crear(**NIT).numero_es_valido(numero) is valido


# ── RN-50 ─────────────────────────────────────────────────────

def test_rn50_bloquea_si_hay_formato_y_registros():
    with pytest.raises(FormatoConRegistros):
        FormatoValidacion.verificar_modificacion(FormatoValidacion.crear(**NIT),
                                                 tiene_registros=True)


@pytest.mark.parametrize("hay_formato, tiene_registros", [
    (False, True),    # primera definición: se permite aunque haya registros
    (True, False),    # modificar sin registros: se permite
    (False, False),
])
def test_rn50_permite(hay_formato, tiene_registros):
    existente = FormatoValidacion.crear(**NIT) if hay_formato else None
    FormatoValidacion.verificar_modificacion(existente, tiene_registros)
