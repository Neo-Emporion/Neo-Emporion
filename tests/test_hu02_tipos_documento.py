from unittest.mock import Mock

import pytest

from app.domain.exceptions.tipo_documento import ErrorAccesoDatosTipoDocumento
from app.domain.models.tipo_documento import TipoDocumentoCreate
from app.services.tipo_documento_service import TipoDocumentoService


RUTA = "/api/v1/parametrizacion/tipos-documento"
ADMIN = {"Authorization": "Bearer token-administrador"}
COMPRADOR = {"Authorization": "Bearer token-comprador"}


def registrar(
    servicio: TipoDocumentoService,
    codigo: str,
    nombre: str,
):
    return servicio.registrar(
        TipoDocumentoCreate(codigo=codigo, nombre=nombre)
    )


def test_caso_1_registrar_tipo_documento_valido(client_tipo_documento):
    respuesta = client_tipo_documento.post(
        RUTA,
        json={"codigo": "PA", "nombre": "Pasaporte"},
        headers=ADMIN,
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "mensaje": "Tipo de documento registrado exitosamente",
        "data": {
            "id": 1,
            "codigo": "PA",
            "nombre": "Pasaporte",
            "estado": "ACTIVO",
        },
        "success": True,
    }


def test_caso_2_editar_nombre_sin_cambiar_codigo(
    client_tipo_documento,
    servicio_tipo_documento,
):
    tipo = registrar(
        servicio_tipo_documento,
        "PA",
        "Pasaporte",
    )

    respuesta = client_tipo_documento.put(
        f"{RUTA}/{tipo.id}",
        json={
            "codigo": "OTRO",
            "nombre": "Pasaporte internacional",
            "descripcion": "Documento de viaje",
        },
        headers=ADMIN,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["codigo"] == "PA"
    assert respuesta.json()["data"]["nombre"] == "Pasaporte internacional"
    assert respuesta.json()["data"]["descripcion"] == "Documento de viaje"


def test_editar_sin_descripcion_responde_400(
    client_tipo_documento,
    servicio_tipo_documento,
):
    tipo = registrar(
        servicio_tipo_documento,
        "PA",
        "Pasaporte",
    )
    respuesta = client_tipo_documento.put(
        f"{RUTA}/{tipo.id}",
        json={"nombre": "Pasaporte internacional"},
        headers=ADMIN,
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["mensaje"] == "El campo descripcion es obligatorio"


def test_caso_3_listar_solo_tipos_activos(
    client_tipo_documento,
    servicio_tipo_documento,
):
    activo = registrar(servicio_tipo_documento, "PA", "Pasaporte")
    inactivo = registrar(servicio_tipo_documento, "NIT", "NIT")
    servicio_tipo_documento.desactivar(inactivo.id)

    respuesta = client_tipo_documento.get(RUTA)

    assert respuesta.status_code == 200
    assert respuesta.json()["mensaje"] == (
        "Consulta de tipos de documento exitosa"
    )
    assert isinstance(respuesta.json()["data"], list)
    assert [item["id"] for item in respuesta.json()["data"]] == [activo.id]


def test_caso_4_desactivar_tipo_sin_uso(
    client_tipo_documento,
    servicio_tipo_documento,
):
    tipo = registrar(servicio_tipo_documento, "PA", "Pasaporte")

    respuesta = client_tipo_documento.patch(
        f"{RUTA}/{tipo.id}/desactivar",
        headers=ADMIN,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["estado"] == "INACTIVO"
    assert respuesta.json()["mensaje"] == (
        "Tipo de documento desactivado exitosamente"
    )
    consulta = client_tipo_documento.get(RUTA, params={"estado": "TODOS"})
    assert tipo.id in [item["id"] for item in consulta.json()["data"]]
    tipo_consulta = next(
        item for item in consulta.json()["data"] if item["id"] == tipo.id
    )
    assert tipo_consulta["estado"] == "INACTIVO"


def test_caso_5_codigo_duplicado(
    client_tipo_documento,
    servicio_tipo_documento,
):
    registrar(
        servicio_tipo_documento,
        "NIT",
        "Número de Identificación Tributaria",
    )

    respuesta = client_tipo_documento.post(
        RUTA,
        json={
            "codigo": "NIT",
            "nombre": "Otro nombre",
        },
        headers=ADMIN,
    )

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "mensaje": "Ya existe un tipo de documento con el código indicado",
        "data": None,
        "success": False,
    }


def test_caso_6_codigo_obligatorio_faltante(client_tipo_documento):
    respuesta = client_tipo_documento.post(
        RUTA,
        json={"nombre": "Pasaporte"},
        headers=ADMIN,
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["mensaje"] == "El campo codigo es obligatorio"
    assert respuesta.json()["success"] is False


def test_editar_sin_nombre_responde_400(
    client_tipo_documento,
):
    respuesta = client_tipo_documento.put(
        f"{RUTA}/1",
        json={"descripcion": "Documento de viaje"},
        headers=ADMIN,
    )

    assert respuesta.status_code == 400
    assert respuesta.json()["mensaje"] == "El campo nombre es obligatorio"


def test_caso_7_no_desactivar_tipo_en_uso(
    client_tipo_documento,
    servicio_tipo_documento,
    uso_tipo_documento,
):
    tipo = registrar(servicio_tipo_documento, "PA", "Pasaporte")
    uso_tipo_documento.tipos_en_uso.add(tipo.id)

    respuesta = client_tipo_documento.patch(
        f"{RUTA}/{tipo.id}/desactivar",
        headers=ADMIN,
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["mensaje"] == (
        "No es posible desactivar el tipo de documento porque está en uso"
    )
    existente = servicio_tipo_documento.repo.obtener_por_id(tipo.id)
    assert existente.estado.value == "ACTIVO"


def test_caso_8_tipo_inexistente(
    client_tipo_documento,
):
    editar = client_tipo_documento.put(
        f"{RUTA}/99999",
        json={"nombre": "Nombre", "descripcion": "Descripción"},
        headers=ADMIN,
    )
    desactivar = client_tipo_documento.patch(
        f"{RUTA}/99999/desactivar",
        headers=ADMIN,
    )

    for respuesta in (editar, desactivar):
        assert respuesta.status_code == 404
        assert respuesta.json()["mensaje"] == "El tipo de documento no existe"


def test_caso_9_usuario_sin_rol_administrador(
    client_tipo_documento,
):
    respuesta = client_tipo_documento.post(
        RUTA,
        json={"codigo": "PA", "nombre": "Pasaporte"},
        headers=COMPRADOR,
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["mensaje"] == (
        "No tiene permisos para realizar esta operación"
    )
    assert respuesta.json()["success"] is False


def test_operaciones_administrativas_sin_token_responden_401(
    client_tipo_documento,
):
    respuestas = [
        client_tipo_documento.post(
            RUTA,
            json={"codigo": "PA", "nombre": "Pasaporte"},
        ),
        client_tipo_documento.put(
            f"{RUTA}/1",
            json={"nombre": "Pasaporte", "descripcion": "Documento de viaje"},
        ),
        client_tipo_documento.patch(f"{RUTA}/1/desactivar"),
    ]

    for respuesta in respuestas:
        assert respuesta.status_code == 401
        assert respuesta.json()["mensaje"] == (
            "Se requiere un token de autenticación válido"
        )


def test_caso_10_falla_de_base_de_datos(
    client_tipo_documento,
    servicio_tipo_documento,
    monkeypatch,
):
    falla = Mock(side_effect=ErrorAccesoDatosTipoDocumento)
    monkeypatch.setattr(servicio_tipo_documento.repo, "buscar_por_codigo", falla)
    monkeypatch.setattr(servicio_tipo_documento.repo, "obtener_por_id", falla)
    monkeypatch.setattr(servicio_tipo_documento.repo, "listar", falla)

    respuestas = [
        client_tipo_documento.post(
            RUTA,
            json={"codigo": "PA", "nombre": "Pasaporte"},
            headers=ADMIN,
        ),
        client_tipo_documento.put(
            f"{RUTA}/1",
            json={
                "nombre": "Pasaporte actualizado",
                "descripcion": "Descripción actualizada",
            },
            headers=ADMIN,
        ),
        client_tipo_documento.get(RUTA),
        client_tipo_documento.patch(
            f"{RUTA}/1/desactivar",
            headers=ADMIN,
        ),
    ]

    for respuesta in respuestas:
        assert respuesta.status_code == 503
        assert respuesta.json() == {
            "mensaje": (
                "No fue posible procesar la solicitud de tipos de documento"
            ),
            "data": None,
            "success": False,
        }


@pytest.mark.parametrize(
    "codigo",
    ["pa", "P", "PASAPORTE1234"],
)
def test_codigo_invalido(
    client_tipo_documento,
    codigo,
):
    respuesta = client_tipo_documento.post(
        RUTA,
        json={"codigo": codigo, "nombre": "Tipo válido"},
        headers=ADMIN,
    )

    assert respuesta.status_code == 400
