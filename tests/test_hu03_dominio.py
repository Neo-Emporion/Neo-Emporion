# HU-03 — pruebas unitarias de las validaciones de dominio
# (la Definición de Hecho pide: unicidad, uso y estado)

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError

from app.domain.exceptions.valor import (
    CategoriaInvalida,
    ErrorAccesoDatos,
    ValorDuplicado,
    ValorEnUso,
    ValorNoEncontrado,
)
from app.domain.models.valor_parametrico import (
    CategoriaValor,
    EstadoValor,
    FiltroEstadoValor,
    ValorCreate,
    ValorParametrico,
)
from app.repositories.valor_repository import _manejar_errores_bd
from app.services.valor_service import ValorService


def nuevo_valor():
    return ValorParametrico(31, CategoriaValor.METODO_PAGO, "PSE", "Pago por PSE")


# ── Estado ────────────────────────────────────────────────────

def test_nuevo_valor_activo_y_sin_descripcion():
    v = nuevo_valor()
    assert v.estado == EstadoValor.ACTIVO
    assert v.descripcion is None


@pytest.mark.parametrize("categoria", ["ESTADO", "MONEDA", "UNIDAD_MEDIDA", "METODO_PAGO"])
def test_categorias_validas(categoria):
    assert ValorParametrico.validar_categoria(categoria) == CategoriaValor(categoria)


def test_categoria_con_espacios_es_valida():
    assert ValorParametrico.validar_categoria("  MONEDA ") == CategoriaValor.MONEDA


@pytest.mark.parametrize("categoria", ["COLORES", "moneda", "", 5, None, ["MONEDA"]])
def test_categoria_invalida(categoria):
    with pytest.raises(CategoriaInvalida):
        ValorParametrico.validar_categoria(categoria)


def test_editar_cambia_nombre_y_descripcion_y_conserva_categoria_y_codigo():
    v = nuevo_valor()
    v.editar("Pago en línea", "Débito bancario")
    assert (v.nombre, v.descripcion) == ("Pago en línea", "Débito bancario")
    assert (v.categoria, v.codigo) == (CategoriaValor.METODO_PAGO, "PSE")


def test_descripcion_vacia_se_guarda_como_none():
    v = nuevo_valor()
    v.editar("Pago por PSE", "")
    assert v.descripcion is None


def test_editar_no_cambia_el_estado():
    v = nuevo_valor()
    v.desactivar(esta_en_uso=False)
    v.editar("Otro nombre", None)
    assert v.estado == EstadoValor.INACTIVO


def test_to_response_no_expone_descripcion():
    v = nuevo_valor()
    v.editar("Pago por PSE", "Interna")
    assert set(v.to_response()) == {"id", "categoria", "codigo", "nombre", "estado"}


# ── Uso (RN-46) ───────────────────────────────────────────────

def test_desactivar_sin_uso():
    v = nuevo_valor()
    v.desactivar(esta_en_uso=False)
    assert v.estado == EstadoValor.INACTIVO


def test_rn46_no_desactiva_en_uso():
    v = nuevo_valor()
    with pytest.raises(ValorEnUso):
        v.desactivar(esta_en_uso=True)
    assert v.estado == EstadoValor.ACTIVO


def test_desactivar_un_valor_ya_inactivo_no_aplica_rn46():
    # Registro de cambios #12: si ya está INACTIVO se deja igual, sin error
    v = nuevo_valor()
    v.desactivar(esta_en_uso=False)
    v.desactivar(esta_en_uso=True)
    assert v.estado == EstadoValor.INACTIVO


# ── Unicidad (regla aplicada por el servicio) ─────────────────

@pytest.fixture
def servicio(repo_valores, uso_valores):
    s = ValorService(repo_valores, uso_valores)
    s.registrar(ValorCreate(categoria="MONEDA", codigo="COP", nombre="Peso colombiano"))
    return s


def test_duplicado_por_categoria_y_codigo(servicio):
    with pytest.raises(ValorDuplicado):
        servicio.registrar(ValorCreate(categoria="MONEDA", codigo="COP", nombre="Otro"))


def test_mismo_codigo_otra_categoria_no_es_duplicado(servicio):
    r = servicio.registrar(ValorCreate(categoria="METODO_PAGO", codigo="COP", nombre="Otro"))
    assert r.categoria == CategoriaValor.METODO_PAGO


def test_listar_filtro_activo_excluye_inactivos(servicio):
    usd = servicio.registrar(ValorCreate(categoria="MONEDA", codigo="USD", nombre="Dólar"))
    servicio.desactivar(usd.id)
    assert [v.codigo for v in servicio.listar("MONEDA", FiltroEstadoValor.ACTIVO)] == ["COP"]


# ── Repositorio: la base también protege la unicidad ──────────

def test_par_repetido_en_la_base_es_duplicado(repo_valores):
    # Simula dos peticiones simultáneas que pasaron la validación del servicio
    repo_valores.crear(CategoriaValor.MONEDA, "COP", "Peso colombiano")
    with pytest.raises(ValorDuplicado):
        repo_valores.crear(CategoriaValor.MONEDA, "COP", "Otro")


def test_guardar_valor_inexistente(repo_valores):
    with pytest.raises(ValorNoEncontrado):
        repo_valores.guardar(ValorParametrico(99999, CategoriaValor.MONEDA, "X", "X"))


def test_codigo_distinto_en_mayusculas_no_es_duplicado(servicio):
    # Registro de cambios #10: el código se compara exacto
    r = servicio.registrar(ValorCreate(categoria="MONEDA", codigo="cop", nombre="Otro"))
    assert r.codigo == "cop"


# ── Traducción de errores de la base ─────────────────────────

def _que_lanza(error):
    @_manejar_errores_bd
    def metodo():
        raise error
    return metodo


def test_error_unique_es_duplicado():
    error = IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed: valores"))
    with pytest.raises(ValorDuplicado):
        _que_lanza(error)()


def test_otra_restriccion_no_es_duplicado():
    error = IntegrityError("INSERT", {}, Exception("NOT NULL constraint failed: valores.nombre"))
    with pytest.raises(ErrorAccesoDatos):
        _que_lanza(error)()


def test_falla_de_conexion_es_error_de_acceso():
    with pytest.raises(ErrorAccesoDatos):
        _que_lanza(OperationalError("SELECT", {}, Exception("unable to open database")))()


@pytest.mark.parametrize("error", [LookupError("'XX' is not among the defined enum values"),
                                   ValueError("dato inválido")])
def test_dato_guardado_ilegible_es_error_de_acceso(error):
    with pytest.raises(ErrorAccesoDatos):
        _que_lanza(error)()


def test_la_base_rechaza_una_categoria_fuera_del_enum(repo_valores):
    with repo_valores._sesiones() as s:
        with pytest.raises(IntegrityError):
            s.execute(text("INSERT INTO valores_parametricos (categoria, codigo, nombre, estado) "
                           "VALUES ('XX', 'A', 'A', 'ACTIVO')"))
