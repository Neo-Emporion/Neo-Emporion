# ─────────────────────────────────────────────────────────────
# CAPA API — HU-05 Definir formato de validación de tipo de documento
# MOD-01 Parametrización / SUB-01 Catálogos de Identificación
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.api.dependencies.seguridad import MENSAJE_401, MENSAJE_403, requiere_administrador
from app.api.schemas.respuesta import Respuesta, ejemplo_error, exito
from app.domain.exceptions.base import ErrorDominio
from app.domain.exceptions.formato import (
    EjemploNoCumplePatron,
    ErrorAccesoDatosFormato,
    FormatoConRegistros,
    LongitudesInconsistentes,
    PatronInvalido,
    TipoDocumentoInactivo,
)
from app.domain.exceptions.tipo_documento import TipoDocumentoNoExiste
from app.domain.models.formato_validacion import FormatoCreate, FormatoTipoDocumentoResponse
from app.repositories.formato_repository import formato_repository
from app.repositories.tipo_documento_repository import tipo_documento_repository
from app.services.consulta_registros_tipo_documento import consulta_registros_tipo_documento
from app.services.formato_service import FormatoService

# Crear el router con prefijo y etiqueta para la documentación.
# main.py lo registra bajo /api/v1.
router = APIRouter(
    prefix="/parametrizacion/tipos-documento",
    tags=["MOD-01 Parametrización · Formato de validación (HU-05)"],
)

# Instanciar el servicio con inyección de sus dependencias
service = FormatoService(repo=formato_repository, tipos=tipo_documento_repository,
                         registros=consulta_registros_tipo_documento)

# Mayor `id` que cabe en la base (entero de 64 bits)
ID_MAXIMO = 2**63 - 1

# Error de dominio -> código HTTP
CODIGOS_HTTP: dict[type[ErrorDominio], int] = {
    PatronInvalido: status.HTTP_400_BAD_REQUEST,
    EjemploNoCumplePatron: status.HTTP_400_BAD_REQUEST,
    LongitudesInconsistentes: status.HTTP_400_BAD_REQUEST,
    TipoDocumentoNoExiste: status.HTTP_404_NOT_FOUND,
    FormatoConRegistros: status.HTTP_409_CONFLICT,
    TipoDocumentoInactivo: status.HTTP_409_CONFLICT,
    ErrorAccesoDatosFormato: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def _a_http(e: ErrorDominio) -> HTTPException:
    # Busca el código por la clase del error o por sus clases padre.
    # Un error de dominio sin código registrado es un descuido: responde 500.
    for clase in type(e).__mro__:
        if clase in CODIGOS_HTTP:
            return HTTPException(status_code=CODIGOS_HTTP[clase], detail=e.mensaje)
    raise RuntimeError(f"Error de dominio sin código HTTP registrado: {type(e).__name__}") from e


# ── PUT /api/v1/parametrizacion/tipos-documento/{id}/formato (API-G08) ──
@router.put(
    "/{id}/formato",
    response_model=Respuesta[FormatoTipoDocumentoResponse],
    summary="API-G08 · Definir formato de validación",
    description=(
        "FUN-04. Define el formato que debe cumplir el número de un tipo de documento: "
        "patrón (expresión regular), longitud mínima y máxima, y un ejemplo. "
        "Solo Administrador.\n\n"
        "- `patron` debe ser una expresión regular válida y `ejemplo` debe cumplirla.\n"
        "- `longitud_min` debe ser mayor que 0 y menor o igual que `longitud_max`.\n"
        "- Un tipo de documento `INACTIVO` no admite definir formato.\n"
        "- RN-50: si el tipo ya tiene formato y existen compradores o vendedores "
        "registrados con ese tipo, el formato no puede modificarse."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Formato de validación definido exitosamente",
            {"id": 4, "codigo": "NIT", "formato": {
                "patron": "^[0-9]{9}-[0-9]$", "longitud_min": 11, "longitud_max": 11,
                "ejemplo": "900123456-7"}})}}},
        400: ejemplo_error("Patrón, ejemplo o longitudes no válidos",
                           "El patrón de validación no es válido"),
        401: ejemplo_error("Sin autenticar", MENSAJE_401),
        403: ejemplo_error("Sin permisos de administrador", MENSAJE_403),
        404: ejemplo_error("Tipo de documento inexistente", "El tipo de documento no existe"),
        409: ejemplo_error(
            "RN-50: formato con registros asociados, o tipo de documento inactivo",
            "No es posible modificar el formato porque existen registros asociados al tipo "
            "de documento"),
        503: ejemplo_error("Falla de base de datos",
                           "No fue posible definir el formato de validación"),
    },
)
def definir_formato(datos: FormatoCreate,
                    id: int = Path(..., le=ID_MAXIMO,
                                   description="Identificador del tipo de documento"),
                    _rol: str = Depends(requiere_administrador)):
    try:
        return exito("Formato de validación definido exitosamente", service.definir(id, datos))
    except ErrorDominio as e:
        raise _a_http(e) from e
