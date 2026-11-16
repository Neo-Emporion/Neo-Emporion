# ─────────────────────────────────────────────────────────────
# DEPENDENCIAS — autenticación Bearer SIMULADA y control de roles
# TODO(pendiente): reemplazar por el token real (JWT) cuando se construya HU-07.
# Mientras tanto se aceptan tokens fijos de prueba, cada uno asociado a un rol.
# Uso en Swagger: botón "Authorize" -> escribir, por ejemplo, token-administrador
# ─────────────────────────────────────────────────────────────

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ROL_ADMINISTRADOR = "ADMINISTRADOR"
ROL_COMPRADOR = "COMPRADOR"
ROL_VENDEDOR = "VENDEDOR"

# Tokens de prueba -> rol
TOKENS_SIMULADOS: dict[str, str] = {
    "token-administrador": ROL_ADMINISTRADOR,
    "token-comprador": ROL_COMPRADOR,
    "token-vendedor": ROL_VENDEDOR,
}

# TODO(pendiente): la HU-01 solo exige 403 sin permisos (Caso 10). El 401 sin token
# y ambos textos son decisión provisional del proyecto hasta HU-07.
MENSAJE_401 = "Se requiere un token de autenticación válido"
MENSAJE_403 = "No tiene permisos para realizar esta operación"

esquema_bearer = HTTPBearer(auto_error=False, description="Token Bearer (simulado hasta HU-07)")


def obtener_rol(
    credenciales: Optional[HTTPAuthorizationCredentials] = Depends(esquema_bearer),
) -> str:
    """Devuelve el rol del token o responde 401 si falta o no es válido."""
    if credenciales is None or credenciales.credentials not in TOKENS_SIMULADOS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=MENSAJE_401,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TOKENS_SIMULADOS[credenciales.credentials]


def requiere_administrador(rol: str = Depends(obtener_rol)) -> str:
    """Permite el paso solo al rol Administrador; si no, 403."""
    if rol != ROL_ADMINISTRADOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=MENSAJE_403)
    return rol
