import pytest

from app.domain.exceptions.tipo_documento import (
    CodigoTipoDocumentoDuplicado,
    TipoDocumentoEnUso,
)
from app.domain.models.tipo_documento import (
    EstadoTipoDocumento,
    TipoDocumento,
    TipoDocumentoCreate,
)


def test_nuevo_tipo_documento_activo():
    tipo = TipoDocumento(
        id=1,
        codigo="CC",
        nombre="Cédula de ciudadanía",
    )

    assert tipo.estado == EstadoTipoDocumento.ACTIVO


def test_editar_nombre_y_descripcion():
    tipo = TipoDocumento(
        id=1,
        codigo="NIT",
        nombre="NIT",
    )

    tipo.editar(
        nombre="Número de Identificación Tributaria",
        descripcion="Documento tributario",
    )

    assert tipo.nombre == "Número de Identificación Tributaria"
    assert tipo.descripcion == "Documento tributario"
    assert tipo.codigo == "NIT"


def test_desactivar_tipo_sin_uso():
    tipo = TipoDocumento(
        id=1,
        codigo="PA",
        nombre="Pasaporte",
    )

    tipo.desactivar(esta_en_uso=False)

    assert tipo.estado == EstadoTipoDocumento.INACTIVO


def test_desactivar_tipo_en_uso_no_cambia_estado():
    tipo = TipoDocumento(
        id=1,
        codigo="PA",
        nombre="Pasaporte",
    )

    with pytest.raises(TipoDocumentoEnUso):
        tipo.desactivar(esta_en_uso=True)

    assert tipo.estado == EstadoTipoDocumento.ACTIVO


# ── Unicidad del código (RN-48) ───────────────────────────────

def test_rn48_codigo_duplicado(servicio_tipo_documento):
    servicio_tipo_documento.registrar(
        TipoDocumentoCreate(codigo="NIT", nombre="Número de Identificación Tributaria")
    )

    with pytest.raises(CodigoTipoDocumentoDuplicado):
        servicio_tipo_documento.registrar(
            TipoDocumentoCreate(codigo="NIT", nombre="Otro nombre")
        )


def test_rn48_codigos_distintos_si_se_permiten(servicio_tipo_documento):
    cc = servicio_tipo_documento.registrar(
        TipoDocumentoCreate(codigo="CC", nombre="Cédula de ciudadanía")
    )
    nit = servicio_tipo_documento.registrar(
        TipoDocumentoCreate(codigo="NIT", nombre="Número de Identificación Tributaria")
    )

    assert cc.id != nit.id


def test_rn48_la_base_tambien_rechaza_codigo_repetido(repo_tipo_documento):
    repo_tipo_documento.crear(codigo="CC", nombre="Cédula de ciudadanía", descripcion=None)

    with pytest.raises(CodigoTipoDocumentoDuplicado):
        repo_tipo_documento.crear(codigo="CC", nombre="Otro nombre", descripcion=None)
