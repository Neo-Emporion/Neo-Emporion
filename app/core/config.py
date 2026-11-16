# ─────────────────────────────────────────────────────────────
# CORE — configuración leída desde el archivo .env
# ─────────────────────────────────────────────────────────────

import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "Neo-Emporion")
APP_ENV = os.getenv("APP_ENV", "development")

# Base de datos emulada en memoria con SQLAlchemy (indicación del profesor).
# Si DATABASE_URL no está en el .env, se usa SQLite en memoria.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")
