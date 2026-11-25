# ─────────────────────────────────────────────────────────────
# CAPA API — HU-03 Gestionar catálogos transaccionales
# MOD-01 Parametrización / SUB-03 Catálogos Transaccionales
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.dependencies.seguridad import MENSAJE_401, MENSAJE_403, requiere_administrador
from app.api.schemas.respuesta import Respuesta, ejemplo_error, exito
from app.domain.exceptions.base import ErrorDominio
from app.domain.exceptions.valor import (
    CategoriaInvalida,
    ErrorAccesoDatos,
    ValorDuplicado,
    ValorEnUso,
    ValorNoEncontrado,
)
from app.domain.models.valor_parametrico import (
    CATEGORIAS,
    FiltroEstadoValor,
    ValorCreate,
    ValorDesactivado,
    ValorResponse,
    ValorUpdate,
)
from app.repositories.valor_repository import valor_repository
from app.services.consulta_uso_valores import consulta_uso_valores
from app.services.valor_service import ValorService

# Crear el router con prefijo y etiqueta para la documentación.
# main.py lo registra bajo /api/v1.
router = APIRouter(
    prefix="/parametrizacion/valores",
    tags=["MOD-01 Parametrización · Catálogos transaccionales (HU-03)"],
)

# Instanciar el servicio con inyección del repositorio y de la consulta de uso (RN-46)
service = ValorService(repo=valor_repository, uso=consulta_uso_valores)


# Mayor `id` que cabe en la base (entero de 64 bits). Uno mayor responde 400
# "El campo id no es válido" en lugar de un error interno.
ID_MAXIMO = 2**63 - 1

# Error de dominio -> código HTTP
CODIGOS_HTTP: dict[type[ErrorDominio], int] = {
    CategoriaInvalida: status.HTTP_400_BAD_REQUEST,
    ValorNoEncontrado: status.HTTP_404_NOT_FOUND,
    ValorDuplicado: status.HTTP_409_CONFLICT,
    ValorEnUso: status.HTTP_409_CONFLICT,
    ErrorAccesoDatos: status.HTTP_503_SERVICE_UNAVAILABLE,
}


def _a_http(e: ErrorDominio) -> HTTPException:
    # Busca el código por la clase del error o por sus clases padre.
    # Un error de dominio sin código registrado es un descuido: responde 500.
    for clase in type(e).__mro__:
        if clase in CODIGOS_HTTP:
            return HTTPException(status_code=CODIGOS_HTTP[clase], detail=e.mensaje)
    raise RuntimeError(f"Error de dominio sin código HTTP registrado: {type(e).__name__}") from e


# ── Ejemplos para Swagger ─────────────────────────────────────
E400_CATEGORIA = ejemplo_error("Datos inválidos o categoría no válida",
                               "La categoría indicada no es válida")
E401 = ejemplo_error("Sin autenticar", MENSAJE_401)
E403 = ejemplo_error("Sin permisos de administrador", MENSAJE_403)
E404 = ejemplo_error("Valor inexistente", "El valor paramétrico no existe")
E409_DUPLICADO = ejemplo_error("Valor duplicado en la categoría",
                               "Ya existe un valor con el mismo código en la categoría")
E409_RN46 = ejemplo_error(
    "RN-46: el valor está siendo utilizado por otro módulo",
    "No es posible desactivar el valor porque está siendo utilizado por otro módulo")
E503 = ejemplo_error("Falla de base de datos",
                     "No fue posible procesar la solicitud de valores paramétricos")
EJEMPLO_VALOR = {"id": 31, "categoria": "METODO_PAGO", "codigo": "PSE",
                 "nombre": "Pago por PSE", "estado": "ACTIVO"}


# ── POST /api/v1/parametrizacion/valores (API-G09) ────────────
@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Respuesta[ValorResponse],
    summary="API-G09 · Registrar valor paramétrico",
    description=(
        "FUN-11. Registra un valor en una categoría. Solo Administrador.\n\n"
        "- `categoria`: `ESTADO`, `MONEDA`, `UNIDAD_MEDIDA` o `METODO_PAGO`.\n"
        "- El par (`categoria`, `codigo`) no puede existir previamente.\n"
        "- Se crea con `estado = ACTIVO`."
    ),
    responses={
        201: {"content": {"application/json": {"example": exito(
            "Valor paramétrico registrado exitosamente", EJEMPLO_VALOR)}}},
        400: E400_CATEGORIA, 401: E401, 403: E403, 409: E409_DUPLICADO, 503: E503,
    },
)
def registrar_valor(datos: ValorCreate,
                    _rol: str = Depends(requiere_administrador)):
    try:
        return exito("Valor paramétrico registrado exitosamente", service.registrar(datos))
    except ErrorDominio as e:
        raise _a_http(e) from e


# ── PUT /api/v1/parametrizacion/valores/{id} (API-G10) ────────
@router.put(
    "/{id}",
    response_model=Respuesta[ValorResponse],
    summary="API-G10 · Editar valor paramétrico",
    description=(
        "FUN-12. Modifica `nombre` y `descripcion` de un valor. Solo Administrador.\n\n"
        "Los dos campos son obligatorios en el body (`descripcion` puede ser `null`). "
        "`categoria` y `codigo` no se modifican (si se envían, se ignoran)."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Valor paramétrico actualizado exitosamente",
            {**EJEMPLO_VALOR, "nombre": "Pago en línea por PSE"})}}},
        400: ejemplo_error("Datos inválidos", "El campo nombre es obligatorio"),
        401: E401, 403: E403, 404: E404, 503: E503,
    },
)
def editar_valor(datos: ValorUpdate,
                 id: int = Path(..., le=ID_MAXIMO, description="Identificador del valor"),
                 _rol: str = Depends(requiere_administrador)):
    try:
        # TODO(pendiente): la HU no define el mensaje de edición exitosa.
        return exito("Valor paramétrico actualizado exitosamente", service.editar(id, datos))
    except ErrorDominio as e:
        raise _a_http(e) from e


# ── GET /api/v1/parametrizacion/valores (API-G11) ─────────────
@router.get(
    "",
    response_model=Respuesta[list[ValorResponse]],
    summary="API-G11 · Consultar valores paramétricos",
    description=(
        "FUN-13. Lista los valores de una categoría (arreglo, sin paginación).\n\n"
        "`categoria` es obligatoria. Por defecto solo se retornan los `ACTIVO` (RN-49); "
        "los desactivados aparecen con `estado=INACTIVO` o `estado=TODOS`."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Consulta de valores paramétricos exitosa",
            [{"id": 30, "categoria": "METODO_PAGO", "codigo": "TC",
              "nombre": "Tarjeta de crédito", "estado": "ACTIVO"}, EJEMPLO_VALOR])}}},
        400: E400_CATEGORIA, 503: E503,
    },
)
def listar_valores(
    categoria: str = Query(..., description="Categoría a consultar",
                           json_schema_extra={"enum": CATEGORIAS}),
    estado: FiltroEstadoValor = Query(FiltroEstadoValor.ACTIVO,
                                 description="ACTIVO (por defecto), INACTIVO o TODOS"),
):
    # TODO(pendiente): la HU-03 no indica qué roles pueden consultar
    # ("el usuario o módulo"). Por ahora no exige autenticación, igual que HU-01.
    try:
        return exito("Consulta de valores paramétricos exitosa",
                     service.listar(categoria, estado))
    except ErrorDominio as e:
        raise _a_http(e) from e


# ── PATCH /api/v1/parametrizacion/valores/{id}/desactivar (API-G12) ──
@router.patch(
    "/{id}/desactivar",
    response_model=Respuesta[ValorDesactivado],
    summary="API-G12 · Desactivar valor paramétrico",
    description=(
        "FUN-14. Marca el valor como `INACTIVO` (baja lógica: el registro se conserva). "
        "Solo Administrador.\n\n"
        "RN-46: no se permite si el valor está siendo utilizado por otro módulo."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Valor paramétrico desactivado exitosamente", {"id": 31, "estado": "INACTIVO"})}}},
        401: E401, 403: E403, 404: E404, 409: E409_RN46, 503: E503,
    },
)
def desactivar_valor(id: int = Path(..., le=ID_MAXIMO, description="Identificador del valor"),
                     _rol: str = Depends(requiere_administrador)):
    try:
        # TODO(pendiente): la HU no define el mensaje de desactivación exitosa.
        return exito("Valor paramétrico desactivado exitosamente", service.desactivar(id))
    except ErrorDominio as e:
        raise _a_http(e) from e
