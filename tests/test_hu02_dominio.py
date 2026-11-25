import pytest

from app.domain.exceptions.tipo_documento import (
    TipoDocumentoEnUso,
)
from app.domain.models.tipo_documento import (
    EstadoTipoDocumento,
    TipoDocumento,
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
