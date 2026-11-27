# ─────────────────────────────────────────────────────────────
# CORE — configuración leída desde el archivo .env
# ─────────────────────────────────────────────────────────────

import logging
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Neo-Emporion")
APP_ENV = os.getenv("APP_ENV", "development")

# Base de datos emulada en memoria con SQLAlchemy (indicación del profesor).
# Si DATABASE_URL no está en el .env, se usa SQLite en memoria.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# Seguridad (HU-07). SECRET_KEY firma los tokens JWT. Si no está en el .env se genera
# una al azar en cada arranque: los tokens dejan de servir al reiniciar el servidor,
# igual que los datos de la base en memoria.
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_hex(32)
    logging.getLogger(__name__).warning(
        "SECRET_KEY no está definida en el .env: se generó una clave temporal. Los tokens "
        "dejan de servir cada vez que el servidor se reinicia (también con --reload).")
# Duración del token en minutos. 60 = 3600 segundos, como el ejemplo de la HU-07.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
