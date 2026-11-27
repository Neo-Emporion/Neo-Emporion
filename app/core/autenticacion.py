# ─────────────────────────────────────────────────────────────
# CORE — cifrado de contraseñas y token de acceso JWT (HU-07)
# - Contraseñas: PBKDF2-SHA256 de la librería estándar (hashlib), con un salt
#   aleatorio por contraseña. Se guarda "pbkdf2_sha256$iteraciones$salt$resumen";
#   la contraseña original nunca se guarda.
# - Token: JWT firmado con HS256 (PyJWT) usando SECRET_KEY del .env.
# No importa nada de FastAPI ni de base de datos aquí.
# ─────────────────────────────────────────────────────────────

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY

# Roles de la plataforma (van dentro del token, en el campo "rol")
ROL_ADMINISTRADOR = "ADMINISTRADOR"
ROL_COMPRADOR = "COMPRADOR"
ROL_VENDEDOR = "VENDEDOR"

ALGORITMO_JWT = "HS256"
ALGORITMO_CIFRADO = "pbkdf2_sha256"
# Número de vueltas de PBKDF2 recomendado por OWASP para SHA-256.
# Más vueltas = más lento adivinar contraseñas por fuerza bruta.
ITERACIONES = 600_000


def _resumen(contrasena: str, salt: bytes, iteraciones: int) -> bytes:
    # "surrogatepass": un JSON puede traer caracteres sueltos que UTF-8 no admite
    return hashlib.pbkdf2_hmac("sha256", contrasena.encode("utf-8", "surrogatepass"),
                               salt, iteraciones)


def cifrar_contrasena(contrasena: str) -> str:
    """Devuelve la contraseña cifrada, lista para guardar en la base."""
    salt = secrets.token_bytes(16)
    resumen = _resumen(contrasena, salt, ITERACIONES)
    return f"{ALGORITMO_CIFRADO}${ITERACIONES}${salt.hex()}${resumen.hex()}"


def verificar_contrasena(contrasena: str, cifrada: str) -> bool:
    """True si la contraseña corresponde a la cifrada que está en la base."""
    try:
        algoritmo, iteraciones, salt_hex, resumen_hex = cifrada.split("$")
        if algoritmo != ALGORITMO_CIFRADO:
            return False
        calculado = _resumen(contrasena, bytes.fromhex(salt_hex), int(iteraciones))
        esperado = bytes.fromhex(resumen_hex)
    except ValueError:
        # Valor guardado con un formato que no se reconoce
        return False
    # compare_digest tarda lo mismo aunque los valores difieran al inicio
    return hmac.compare_digest(calculado, esperado)


def crear_token(sujeto: str, rol: str) -> tuple[str, int]:
    """Crea el token de acceso. Devuelve (token, segundos hasta que expira)."""
    expira_en = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    ahora = datetime.now(timezone.utc)
    datos = {"sub": sujeto, "rol": rol, "iat": ahora,
             "exp": ahora + timedelta(seconds=expira_en)}
    return jwt.encode(datos, SECRET_KEY, algorithm=ALGORITMO_JWT), expira_en


def decodificar_token(token: str) -> Optional[dict]:
    """Devuelve los datos del token, o None si es inválido, fue alterado o ya expiró."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO_JWT],
                          options={"require": ["sub", "rol", "exp"]})
    except jwt.InvalidTokenError:
        return None
