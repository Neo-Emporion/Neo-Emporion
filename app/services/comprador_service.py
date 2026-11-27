# ─────────────────────────────────────────────────────────────
# CAPA SERVICIO — HU-07 Registrar e iniciar sesión como comprador
# Orquesta dominio + repositorio: valida la contraseña (RN-55), el documento
# (consultando al módulo Parametrización por la interfaz IConsultaTiposDocumento,
# API-I08), el correo único (RN-51) y la cuenta activa (RN-52).
# No importa nada de FastAPI aquí.
# ─────────────────────────────────────────────────────────────

from app.core.autenticacion import (
    ROL_COMPRADOR,
    cifrar_contrasena,
    crear_token,
    verificar_contrasena,
)
from app.domain.exceptions.comprador import (
    CorreoDuplicado,
    CredencialesIncorrectas,
    ErrorAccesoDatosComprador,
)
from app.domain.exceptions.formato import ErrorAccesoDatosFormato
from app.domain.exceptions.tipo_documento import ErrorAccesoDatosTipoDocumento
from app.domain.interfaces.consulta_tipos_documento import IConsultaTiposDocumento
from app.domain.models.comprador import (
    Comprador,
    CompradorCreate,
    CompradorResponse,
    SesionCreate,
    SesionResponse,
)
from app.repositories.comprador_repository import CompradorRepository


class CompradorService:

    def __init__(self, repo: CompradorRepository, tipos: IConsultaTiposDocumento):
        # Inyección de dependencias: repositorio de compradores y consulta de tipos
        # de documento del módulo Parametrización (API-I08)
        self.repo = repo
        self.tipos = tipos

    # ── FUN-16 Registrar comprador (API-G14) ──────────────────
    def registrar(self, datos: CompradorCreate) -> CompradorResponse:
        # RN-55: se valida antes de cifrar y almacenar
        Comprador.validar_contrasena(datos.contrasena)
        self._verificar_documento(datos.tipo_documento_id, datos.numero_documento)
        # RN-51: el correo no puede tener otra cuenta
        if self.repo.buscar_por_correo(datos.correo) is not None:
            raise CorreoDuplicado()
        nuevo = Comprador.registrar(
            tipo_documento_id=datos.tipo_documento_id,
            numero_documento=datos.numero_documento,
            nombres=datos.nombres,
            apellidos=datos.apellidos,
            correo=datos.correo,
            contrasena_cifrada=cifrar_contrasena(datos.contrasena),
        )
        return CompradorResponse(**self.repo.crear(nuevo).to_response())

    # ── FUN-17 Iniciar sesión (API-G15) ───────────────────────
    def iniciar_sesion(self, datos: SesionCreate) -> SesionResponse:
        comprador = self.repo.buscar_por_correo(datos.correo)
        if comprador is None:
            # Se cifra igual para que la respuesta tarde lo mismo que con un correo
            # existente: así el tiempo tampoco revela si el correo está registrado.
            cifrar_contrasena(datos.contrasena)
            raise CredencialesIncorrectas()
        if not verificar_contrasena(datos.contrasena, comprador.contrasena_cifrada):
            raise CredencialesIncorrectas()
        # RN-52: se revisa DESPUÉS de las credenciales, para no revelar el estado
        # de una cuenta a quien no conoce la contraseña.
        comprador.verificar_puede_iniciar_sesion()
        token, expira_en = crear_token(sujeto=str(comprador.id), rol=ROL_COMPRADOR)
        return SesionResponse(token=token, tipo="Bearer", expira_en=expira_en)

    # ── Apoyo interno ─────────────────────────────────────────
    def _verificar_documento(self, tipo_documento_id: int, numero: str) -> None:
        try:
            tipo_activo = self.tipos.tipo_esta_activo(tipo_documento_id)
            cumple_formato = tipo_activo and self.tipos.numero_cumple_formato(
                tipo_documento_id, numero)
        except (ErrorAccesoDatosTipoDocumento, ErrorAccesoDatosFormato) as e:
            # Falla del módulo Parametrización: responde el mensaje de la HU-07 (Caso 9)
            raise ErrorAccesoDatosComprador() from e
        Comprador.verificar_documento(tipo_activo, cumple_formato)
