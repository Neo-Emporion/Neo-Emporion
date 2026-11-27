# ─────────────────────────────────────────────────────────────
# DEPENDENCIAS — autenticación Bearer y control de roles
# Se aceptan dos clases de token:
#   1. El token JWT real que entrega POST /api/v1/usuarios/sesiones (HU-07).
#      Hoy solo lo obtienen los compradores.
#   2. Tokens fijos de prueba (SIMULADOS), porque todavía no existen cuentas de
#      administrador (ninguna HU del prototipo las define) ni de vendedor (HU-08).
#      token-comprador también se conserva, para no cambiar las pruebas de HU-01 a HU-05
#      que lo usan, aunque el comprador ya tiene token real.
#      TODO(pendiente): quitar token-comprador cuando los endpoints necesiten el id del
#      comprador (HU-15; ese token no lo trae), token-vendedor al construir HU-08 y
#      token-administrador cuando se defina cómo se crean las cuentas de administrador.
# Uso en Swagger: botón "Authorize" -> pegar el token (por ejemplo, token-administrador)
# ─────────────────────────────────────────────────────────────

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.autenticacion import (
    ROL_ADMINISTRADOR,
    ROL_COMPRADOR,
    ROL_VENDEDOR,
    decodificar_token,
)

# Tokens de prueba -> rol
TOKENS_SIMULADOS: dict[str, str] = {
    "token-administrador": ROL_ADMINISTRADOR,
    "token-comprador": ROL_COMPRADOR,
    "token-vendedor": ROL_VENDEDOR,
}

# TODO(pendiente): la HU-01 solo exige 403 sin permisos (Caso 10). El 401 sin token
# y ambos textos son decisión provisional del proyecto (la HU-07 tampoco los define).
MENSAJE_401 = "Se requiere un token de autenticación válido"
MENSAJE_403 = "No tiene permisos para realizar esta operación"

esquema_bearer = HTTPBearer(
    auto_error=False,
    description="Token JWT de POST /api/v1/usuarios/sesiones, o un token de prueba: "
                "token-administrador, token-vendedor, token-comprador",
)


def _no_autenticado() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=MENSAJE_401,
        headers={"WWW-Authenticate": "Bearer"},
    )


def obtener_rol(
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(esquema_bearer),
) -> str:
    """Devuelve el rol del token o responde 401 si falta, no es válido o ya expiró."""
    if credenciales is None:
        raise _no_autenticado()
    token = credenciales.credentials
    if token in TOKENS_SIMULADOS:
        return TOKENS_SIMULADOS[token]
    datos = decodificar_token(token)
    if datos is None:
        raise _no_autenticado()
    return datos["rol"]


def requiere_administrador(rol: str = Depends(obtener_rol)) -> str:
    """Permite el paso solo al rol Administrador; si no, 403."""
    if rol != ROL_ADMINISTRADOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MENSAJE_403)
    return rol
