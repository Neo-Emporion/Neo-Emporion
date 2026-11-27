# ─────────────────────────────────────────────────────────────
# CAPA API — HU-07 Registrar e iniciar sesión como comprador
# MOD-02 Usuarios y Compradores / SUB-04 Registro y Autenticación
# Solo recibe peticiones y llama al servicio.
# Aquí NO hay lógica de negocio.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status

from app.api.schemas.respuesta import Respuesta, ejemplo_error, exito
from app.domain.exceptions.base import ErrorDominio
from app.domain.exceptions.comprador import (
    ContrasenaInsegura,
    CorreoDuplicado,
    CredencialesIncorrectas,
    CuentaDesactivada,
    DocumentoNoCumpleFormato,
    ErrorAccesoDatosComprador,
    TipoDocumentoNoValido,
)
from app.domain.models.comprador import (
    CompradorCreate,
    CompradorResponse,
    SesionCreate,
    SesionResponse,
)
from app.repositories.comprador_repository import comprador_repository
from app.services.comprador_service import CompradorService
from app.services.consulta_tipos_documento import consulta_tipos_documento

# Crear el router con prefijo y etiqueta para la documentación.
# main.py lo registra bajo /api/v1.
router = APIRouter(
    prefix="/usuarios",
    tags=["MOD-02 Usuarios y Compradores · Registro y autenticación (HU-07)"],
)

# Instanciar el servicio con inyección de sus dependencias
service = CompradorService(repo=comprador_repository, tipos=consulta_tipos_documento)

# Error de dominio -> código HTTP
CODIGOS_HTTP: dict[type[ErrorDominio], int] = {
    ContrasenaInsegura: status.HTTP_400_BAD_REQUEST,
    DocumentoNoCumpleFormato: status.HTTP_400_BAD_REQUEST,
    TipoDocumentoNoValido: status.HTTP_400_BAD_REQUEST,
    CredencialesIncorrectas: status.HTTP_401_UNAUTHORIZED,
    CuentaDesactivada: status.HTTP_403_FORBIDDEN,
    CorreoDuplicado: status.HTTP_409_CONFLICT,
    ErrorAccesoDatosComprador: status.HTTP_503_SERVICE_UNAVAILABLE,
}

MSG_503 = "No fue posible procesar la solicitud en este momento"


def _a_http(e: ErrorDominio) -> HTTPException:
    # Busca el código por la clase del error o por sus clases padre.
    # Un error de dominio sin código registrado es un descuido: responde 500.
    for clase in type(e).__mro__:
        if clase in CODIGOS_HTTP:
            return HTTPException(status_code=CODIGOS_HTTP[clase], detail=e.mensaje)
    raise RuntimeError(f"Error de dominio sin código HTTP registrado: {type(e).__name__}") from e


# ── POST /api/v1/usuarios/compradores (API-G14) ───────────────
@router.post(
    "/compradores",
    status_code=status.HTTP_201_CREATED,
    response_model=Respuesta[CompradorResponse],
    summary="API-G14 · Registrar comprador",
    description=(
        "FUN-16. Crea la cuenta de un comprador en estado `ACTIVA`. No requiere token.\n\n"
        "- `numero_documento` debe cumplir el formato del tipo de documento (HU-05), "
        "que se consulta al módulo Parametrización (API-I08). El tipo debe estar `ACTIVO`.\n"
        "- RN-51: no puede existir otra cuenta con el mismo `correo` "
        "(se compara sin espacios y sin distinguir mayúsculas).\n"
        "- RN-55: `contrasena` de mínimo 8 caracteres, con mayúscula, minúscula y número.\n"
        "- La contraseña se guarda cifrada y nunca se devuelve."
    ),
    responses={
        201: {"content": {"application/json": {"example": exito(
            "Comprador registrado exitosamente",
            {"id": 5021, "nombres": "Laura", "apellidos": "Gómez",
             "correo": "laura.gomez@correo.com", "estado": "ACTIVA"})}}},
        400: ejemplo_error("Datos faltantes o inválidos, contraseña insegura (RN-55), "
                           "tipo de documento inexistente o INACTIVO, o documento que no "
                           "cumple el formato",
                           "La contraseña no cumple los requisitos mínimos de seguridad"),
        409: ejemplo_error("RN-51: correo ya registrado",
                           "Ya existe una cuenta registrada con ese correo"),
        503: ejemplo_error("Falla de base de datos o del módulo Parametrización", MSG_503),
    },
)
def registrar_comprador(datos: CompradorCreate):
    try:
        return exito("Comprador registrado exitosamente", service.registrar(datos))
    except ErrorDominio as e:
        raise _a_http(e) from e


# ── POST /api/v1/usuarios/sesiones (API-G15) ──────────────────
@router.post(
    "/sesiones",
    response_model=Respuesta[SesionResponse],
    summary="API-G15 · Iniciar sesión",
    description=(
        "FUN-17. Valida `correo` y `contrasena` y devuelve un token de acceso JWT "
        "(`tipo` Bearer) y `expira_en` (segundos). No requiere token.\n\n"
        "- Si el correo o la contraseña no coinciden, el mensaje es el mismo en ambos "
        "casos: no revela cuál de los dos falló.\n"
        "- RN-52: una cuenta `DESACTIVADA` no puede iniciar sesión.\n"
        "- El token se envía en el encabezado `Authorization: Bearer <token>`."
    ),
    responses={
        200: {"content": {"application/json": {"example": exito(
            "Inicio de sesión exitoso",
            {"token": "eyJhbGciOiJIUzI1NiIs...", "tipo": "Bearer", "expira_en": 3600})}}},
        400: ejemplo_error("Datos faltantes", "El campo correo es obligatorio"),
        401: ejemplo_error("Credenciales incorrectas", "Correo o contraseña incorrectos"),
        403: ejemplo_error("RN-52: cuenta desactivada", "La cuenta se encuentra desactivada"),
        503: ejemplo_error("Falla de base de datos", MSG_503),
    },
)
def iniciar_sesion(datos: SesionCreate):
    try:
        return exito("Inicio de sesión exitoso", service.iniciar_sesion(datos))
    except ErrorDominio as e:
        raise _a_http(e) from e
