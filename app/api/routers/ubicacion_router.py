# ─────────────────────────────────────────────────────────────
# CAPA API — HU-01 Gestionar catálogo geográfico / HU-04 Publicar dato geográfico
# MOD-01 Parametrización / SUB-02 Catálogos Geográficos
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.dependencies.seguridad import MENSAJE_401, MENSAJE_403, requiere_administrador
from app.api.schemas.respuesta import Respuesta, RespuestaError, error, ejemplo_error, exito
from app.domain.exceptions.base import ErrorDominio
from app.domain.exceptions.ubicacion import (
    DesactivacionNoPermitida,
    ErrorAccesoDatos,
    ErrorPublicacionDatos,
    JerarquiaInvalida,
    PadreNoPublicado,
    UbicacionDuplicada,
    UbicacionInactiva,
    UbicacionNoEncontrada,
)
from app.domain.models.dato_geografico import (
    FiltroEstado,
    TipoUbicacion,
    UbicacionCreate,
    UbicacionDesactivada,
    UbicacionListado,
    UbicacionPublicada,
    UbicacionResponse,
    UbicacionUpdate,
)
from app.repositories.ubicacion_repository import ubicacion_repository
from app.services.consulta_direcciones import consulta_direcciones
from app.services.ubicacion_service import UbicacionService

# Crear el router con prefijo y etiqueta para la documentación.
# main.py lo registra bajo /api/v1.
router = APIRouter(
    prefix="/parametrizacion/ubicaciones",
    tags=["MOD-01 Parametrización · Catálogo geográfico (HU-01, HU-04)"],
)

# Instanciar el servicio con inyección del repositorio y de la consulta de direcciones
service = UbicacionService(repo=ubicacion_repository, direcciones=consulta_direcciones)


# Tamaño máximo de página del listado
TAMANO_MAXIMO = 100

# Error de dominio -> código HTTP
CODIGOS_HTTP: dict[type[ErrorDominio], int] = {
    JerarquiaInvalida: status.HTTP_400_BAD_REQUEST,
    UbicacionNoEncontrada: status.HTTP_404_NOT_FOUND,
    UbicacionDuplicada: status.HTTP_409_CONFLICT,
    DesactivacionNoPermitida: status.HTTP_409_CONFLICT,
    UbicacionInactiva: status.HTTP_409_CONFLICT,
    PadreNoPublicado: status.HTTP_409_CONFLICT,
    ErrorAccesoDatos: status.HTTP_503_SERVICE_UNAVAILABLE,
    ErrorPublicacionDatos: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def _a_http(e: ErrorDominio) -> HTTPException:
    # Busca el código por la clase del error o por sus clases padre.
    # Un error de dominio sin código registrado es un descuido: responde 500.
    for clase in type(e).__mro__:
        if clase in CODIGOS_HTTP:
            return HTTPException(status_code=CODIGOS_HTTP[clase], detail=e.mensaje)
    raise RuntimeError(f"Error de dominio sin código HTTP registrado: {type(e).__name__}") from e


# ── Ejemplos de error para Swagger ────────────────────────────
E400_JERARQUIA = ejemplo_error("Datos inválidos o jerarquía inválida",
                               "La jerarquía de la ubicación no es válida")
E401 = ejemplo_error("Sin autenticar", MENSAJE_401)
E403 = ejemplo_error("Sin permisos de administrador", MENSAJE_403)
E404 = ejemplo_error("Ubicación inexistente", "La ubicación no existe")
E409_DUPLICADO = ejemplo_error(
    "Ubicación duplicada",
    "Ya existe una ubicación con el mismo nombre o código en el mismo nivel")
E409_RN47 = ejemplo_error(
    "RN-47: tiene direcciones activas o ubicaciones hijas activas",
    "No es posible desactivar la ubicación porque tiene direcciones activas asociadas")
E409_PUBLICACION = {
    "model": RespuestaError,
    "description": "Ubicación inactiva o ubicación padre sin publicar",
    "content": {"application/json": {"examples": {
        "inactiva": error("No es posible publicar una ubicación inactiva"),
        "padre_no_publicado": error(
            "No es posible publicar la ubicación porque su ubicación padre no está publicada"),
    }}},
}
E503 = ejemplo_error("Falla de base de datos",
                     "No fue posible procesar la solicitud de ubicaciones")
E503_PUBLICACION = ejemplo_error("Falla de base de datos",
                                 "No fue posible publicar la ubicación")
EJEMPLO_UBICACION = {"id": 1203, "tipo": "CIUDAD", "nombre": "Bucaramanga", "codigo": "68001",
                     "padre_id": 68, "estado": "ACTIVO", "publicada": False}
EJEMPLO_PUBLICACION = {"id": 1203, "nombre": "Bucaramanga", "estado": "ACTIVO",
                       "publicada": True}


# ── POST /api/v1/parametrizacion/ubicaciones (API-G01) ────────
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Respuesta[UbicacionResponse],
    summary="API-G01 · Registrar ubicación",
    description=(
        "FUN-06. Registra un país, departamento o ciudad. Solo Administrador.\n\n"
        "- `padre_id` es obligatorio para `DEPARTAMENTO` (padre `PAIS`) y `CIUDAD` "
        "(padre `DEPARTAMENTO`); no se permite para `PAIS`.\n"
        "- No puede existir otra ubicación del mismo tipo, nombre y padre, ni otra con el "
        "mismo código.\n"
        "- Se crea con `estado = ACTIVO` y `publicada = false` (se publica con HU-04)."
    ),
    responses={
        201: {"content": {"application/json": {"example": exito(
            "Ubicación registrada exitosamente", EJEMPLO_UBICACION)}}},
        400: E400_JERARQUIA, 401: E401, 403: E403, 409: E409_DUPLICADO, 503: E503,
    },
)
def registrar_ubicacion(datos: UbicacionCreate,
                        _rol: str = Depends(requiere_administrador)):
    try:
        return exito("Ubicación registrada exitosamente", service.registrar(datos))
    except ErrorDominio as e:
        raise _a_http(e) from e


# ── PUT /api/v1/parametrizacion/ubicaciones/{id} (API-G02) ────
@router.put(
    "/{id}",
    response_model=Respuesta[UbicacionResponse],
    summary="API-G02 · Editar ubicación",
    description=(
        "FUN-07. Modifica nombre, código y padre de una ubicación. Solo Administrador.\n\n"
        "El `tipo` no puede modificarse (si se envía, se ignora). Se validan de nuevo la "
        "jerarquía y la duplicidad."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Ubicación actualizada exitosamente", EJEMPLO_UBICACION)}}},
        400: E400_JERARQUIA, 401: E401, 403: E403, 404: E404, 409: E409_DUPLICADO, 503: E503,
    },
)
def editar_ubicacion(datos: UbicacionUpdate,
                     id: int = Path(..., description="Identificador de la ubicación"),
                     _rol: str = Depends(requiere_administrador)):
    try:
        # TODO(pendiente): la HU no define el mensaje de edición exitosa.
        return exito("Ubicación actualizada exitosamente", service.editar(id, datos))
    except ErrorDominio as e:
        raise _a_http(e) from e


# ── GET /api/v1/parametrizacion/ubicaciones (API-I09) ─────────
@router.get(
    "",
    response_model=Respuesta[UbicacionListado],
    summary="API-I09 · Consultar / listar catálogo geográfico",
    description=(
        "FUN-08. Lista ubicaciones paginadas con su jerarquía (`padre_id`).\n\n"
        "Filtros opcionales: `tipo`, `padre_id` y `estado`. Por defecto solo se listan las "
        "`ACTIVO`; las desactivadas aparecen con `estado=INACTIVO` o `estado=TODOS`.\n\n"
        "Vista de consumo (HU-04): con `solo_publicadas=true` la API-I09 devuelve "
        "únicamente ubicaciones `ACTIVO` y `publicada = true`, para los módulos que "
        "consumen el catálogo geográfico."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Consulta de ubicaciones exitosa",
            {"pagina": 1, "tamano": 20, "total": 1, "ubicaciones": [
                {"id": 68, "tipo": "DEPARTAMENTO", "nombre": "Santander", "codigo": "68",
                 "padre_id": 1, "estado": "ACTIVO"}]})}}},
        400: ejemplo_error("Filtro o paginación inválidos", "El campo tipo no es válido"),
        503: E503,
    },
)
def listar_ubicaciones(
    tipo: Optional[TipoUbicacion] = Query(None, description="Filtra por tipo"),
    padre_id: Optional[int] = Query(None, description="Filtra por ubicación padre"),
    estado: FiltroEstado = Query(FiltroEstado.ACTIVO,
                                 description="ACTIVO (por defecto), INACTIVO o TODOS"),
    pagina: int = Query(1, ge=1, description="Número de página"),
    # Máximo 100 por decisión del dueño del proyecto (la HU no fija un tope).
    tamano: int = Query(20, ge=1, le=TAMANO_MAXIMO,
                        description=f"Elementos por página (máximo {TAMANO_MAXIMO})"),
    solo_publicadas: bool = Query(
        False,
        description="Vista de consumo (API-I09, HU-04): si es true, solo devuelve "
                    "ubicaciones ACTIVO y publicadas"),
):
    # TODO(pendiente): la HU-01 no indica qué roles pueden consultar el listado
    # (dice "el usuario"). Por ahora no exige autenticación.
    try:
        return exito("Consulta de ubicaciones exitosa",
                     service.listar(tipo, padre_id, estado, pagina, tamano,
                                    solo_publicadas))
    except ErrorDominio as e:
        raise _a_http(e) from e


# ── PATCH /api/v1/parametrizacion/ubicaciones/{id}/desactivar (API-G03) ──
@router.patch(
    "/{id}/desactivar",
    response_model=Respuesta[UbicacionDesactivada],
    summary="API-G03 · Desactivar ubicación",
    description=(
        "FUN-09. Marca la ubicación como `INACTIVO` (baja lógica: el registro no se "
        "elimina). Solo Administrador.\n\n"
        "RN-47: no se permite si tiene direcciones activas asociadas o ubicaciones hijas "
        "activas."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Ubicación desactivada exitosamente", {"id": 1203, "estado": "INACTIVO"})}}},
        401: E401, 403: E403, 404: E404, 409: E409_RN47, 503: E503,
    },
)
def desactivar_ubicacion(id: int = Path(..., description="Identificador de la ubicación"),
                         _rol: str = Depends(requiere_administrador)):
    try:
        return exito("Ubicación desactivada exitosamente", service.desactivar(id))
    except ErrorDominio as e:
        raise _a_http(e) from e


# ── PATCH /api/v1/parametrizacion/ubicaciones/{id}/publicar (API-G04) ──
@router.patch(
    "/{id}/publicar",
    response_model=Respuesta[UbicacionPublicada],
    summary="API-G04 · Publicar ubicación",
    description=(
        "FUN-10. Marca la ubicación como publicada (`publicada = true`) para que los "
        "módulos consumidores la vean por la API-I09. Solo Administrador.\n\n"
        "Validaciones:\n"
        "- La ubicación debe existir (`404` si no existe).\n"
        "- La ubicación debe estar `ACTIVO` (`409` si está inactiva).\n"
        "- Si la jerarquía exige padre (`DEPARTAMENTO` -> `PAIS`, `CIUDAD` -> "
        "`DEPARTAMENTO`), ese padre debe estar publicado (`409` si no lo está).\n"
        "- Es idempotente: publicar una ubicación ya publicada responde `200` sin cambios.\n\n"
        "A partir de la publicación, `GET /api/v1/parametrizacion/ubicaciones?"
        "solo_publicadas=true` (API-I09) la incluye para los demás módulos."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Ubicación publicada exitosamente", EJEMPLO_PUBLICACION)}}},
        401: E401, 403: E403, 404: E404,
        409: E409_PUBLICACION,
        503: E503_PUBLICACION,
    },
)
def publicar_ubicacion(id: int = Path(..., description="Identificador de la ubicación"),
                       _rol: str = Depends(requiere_administrador)):
    try:
        return exito("Ubicación publicada exitosamente", service.publicar(id))
    except ErrorDominio as e:
        raise _a_http(e) from e
