from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.dependencies.seguridad import (
    MENSAJE_401,
    MENSAJE_403,
    requiere_administrador,
)
from app.api.schemas.respuesta import Respuesta, ejemplo_error, exito
from app.domain.exceptions.base import ErrorDominio
from app.domain.exceptions.tipo_documento import (
    CodigoTipoDocumentoDuplicado,
    ErrorAccesoDatosTipoDocumento,
    TipoDocumentoEnUso,
    TipoDocumentoNoExiste,
)
from app.domain.models.tipo_documento import (
    FiltroEstadoTipoDocumento,
    TipoDocumentoCreate,
    TipoDocumentoDesactivado,
    TipoDocumentoListadoItem,
    TipoDocumentoResponse,
    TipoDocumentoUpdate,
)
from app.repositories.tipo_documento_repository import tipo_documento_repository
from app.services.consulta_uso_tipo_documento import consulta_uso_tipo_documento
from app.services.tipo_documento_service import TipoDocumentoService


router = APIRouter(
    prefix="/parametrizacion/tipos-documento",
    tags=["MOD-01 Parametrización · Tipos de documento (HU-02)"],
)

service = TipoDocumentoService(
    repo=tipo_documento_repository,
    consulta_uso=consulta_uso_tipo_documento,
)

CODIGOS_HTTP: dict[type[ErrorDominio], int] = {
    TipoDocumentoNoExiste: status.HTTP_404_NOT_FOUND,
    CodigoTipoDocumentoDuplicado: status.HTTP_409_CONFLICT,
    TipoDocumentoEnUso: status.HTTP_409_CONFLICT,
    ErrorAccesoDatosTipoDocumento: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def _a_http(error: ErrorDominio) -> HTTPException:
    for clase in type(error).__mro__:
        if clase in CODIGOS_HTTP:
            return HTTPException(
                status_code=CODIGOS_HTTP[clase],
                detail=error.mensaje,
            )
    raise RuntimeError(
        f"Error de dominio sin código HTTP registrado: {type(error).__name__}"
    ) from error


E401 = ejemplo_error("Sin autenticar", MENSAJE_401)
E403 = ejemplo_error("Sin permisos de administrador", MENSAJE_403)
E404 = ejemplo_error(
    "Tipo de documento inexistente",
    "El tipo de documento no existe",
)
E409_DUPLICADO = ejemplo_error(
    "Código duplicado",
    "Ya existe un tipo de documento con el código indicado",
)
E409_EN_USO = ejemplo_error(
    "Tipo de documento en uso",
    "No es posible desactivar el tipo de documento porque está en uso",
)
E503 = ejemplo_error(
    "Falla de base de datos",
    "No fue posible procesar la solicitud de tipos de documento",
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Respuesta[TipoDocumentoResponse],
    response_model_exclude_none=True,
    summary="API-G05 · Registrar tipo de documento",
    description=(
        "FUN-01. Registra un tipo de documento activo. Solo Administrador.\n\n"
        "RN-48: el código debe ser único, tener entre 2 y 10 caracteres "
        "y estar escrito en mayúsculas."
    ),
    responses={
        201: {"content": {"application/json": {"example": exito(
            "Tipo de documento registrado exitosamente",
            {
                "id": 4,
                "codigo": "NIT",
                "nombre": "Número de Identificación Tributaria",
                "estado": "ACTIVO",
            },
        )}}},
        400: ejemplo_error(
            "Datos inválidos",
            "El campo codigo es obligatorio",
        ),
        401: E401,
        403: E403,
        409: E409_DUPLICADO,
        503: E503,
    },
)
def registrar_tipo_documento(
    datos: TipoDocumentoCreate,
    _rol: str = Depends(requiere_administrador),
):
    try:
        return exito(
            "Tipo de documento registrado exitosamente",
            service.registrar(datos),
        )
    except ErrorDominio as error:
        raise _a_http(error) from error


@router.put(
    "/{id}",
    response_model=Respuesta[TipoDocumentoResponse],
    response_model_exclude_none=True,
    summary="API-G06 · Editar tipo de documento",
    description=(
        "FUN-02. Actualiza el nombre y la descripción obligatoria. "
        "Solo Administrador. El código no puede modificarse."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Tipo de documento actualizado exitosamente",
            {
                "id": 4,
                "codigo": "NIT",
                "nombre": "Número de Identificación Tributaria",
                "descripcion": "Documento tributario",
                "estado": "ACTIVO",
            },
        )}}},
        400: ejemplo_error("Datos inválidos", "El campo nombre es obligatorio"),
        401: E401,
        403: E403,
        404: E404,
        503: E503,
    },
)
def editar_tipo_documento(
    datos: TipoDocumentoUpdate,
    id: int = Path(..., description="Identificador del tipo de documento"),
    _rol: str = Depends(requiere_administrador),
):
    try:
        # TODO(pendiente): la HU no define el mensaje de edición exitosa.
        return exito(
            "Tipo de documento actualizado exitosamente",
            service.editar(id, datos),
        )
    except ErrorDominio as error:
        raise _a_http(error) from error


@router.get(
    "",
    response_model=Respuesta[list[TipoDocumentoListadoItem]],
    summary="API-I08 · Consultar / listar tipos de documento",
    description=(
        "FUN-03. Lista los tipos de documento (arreglo, sin paginación). "
        "Por defecto devuelve solo tipos activos."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Consulta de tipos de documento exitosa",
            [
                    {
                        "id": 1,
                        "codigo": "CC",
                        "nombre": "Cédula de ciudadanía",
                        "estado": "ACTIVO",
                    },
                    {
                        "id": 4,
                        "codigo": "NIT",
                        "nombre": "Número de Identificación Tributaria",
                        "estado": "ACTIVO",
                    },
            ],
        )}}},
        400: ejemplo_error("Filtro inválido", "El campo estado no es válido"),
        503: E503,
    },
)
def listar_tipos_documento(
    estado: FiltroEstadoTipoDocumento = Query(
        FiltroEstadoTipoDocumento.ACTIVO,
        description="ACTIVO (por defecto), INACTIVO o TODOS",
    ),
):
    try:
        return exito(
            "Consulta de tipos de documento exitosa",
            service.listar(estado),
        )
    except ErrorDominio as error:
        raise _a_http(error) from error


@router.patch(
    "/{id}/desactivar",
    response_model=Respuesta[TipoDocumentoDesactivado],
    summary="API-G07 · Desactivar tipo de documento",
    description=(
        "FUN-05. Marca el tipo como INACTIVO sin eliminarlo. "
        "Solo Administrador.\n\n"
        "No se permite desactivar si existen compradores o vendedores "
        "activos registrados con ese tipo."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Tipo de documento desactivado exitosamente",
            {"id": 4, "estado": "INACTIVO"},
        )}}},
        401: E401,
        403: E403,
        404: E404,
        409: E409_EN_USO,
        503: E503,
    },
)
def desactivar_tipo_documento(
    id: int = Path(..., description="Identificador del tipo de documento"),
    _rol: str = Depends(requiere_administrador),
):
    try:
        return exito(
            "Tipo de documento desactivado exitosamente",
            service.desactivar(id),
        )
    except ErrorDominio as error:
        raise _a_http(error) from error
