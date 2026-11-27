# ─────────────────────────────────────────────────────────────
# CORE — conexión a la base de datos con SQLAlchemy
# Con "sqlite:///:memory:" la base vive en la memoria del proceso:
# se crea al arrancar el servidor y se pierde al detenerlo.
# ─────────────────────────────────────────────────────────────

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import DATABASE_URL


class Base(DeclarativeBase):
    """Clase base de todas las tablas (modelos ORM)."""


def crear_engine(url: str) -> Engine:
    if url.startswith("sqlite"):
        opciones = {"connect_args": {"check_same_thread": False}}
        if ":memory:" in url:
            # StaticPool: todas las sesiones comparten la MISMA conexión,
            # si no, cada conexión vería una base en memoria vacía distinta.
            # Nota: como los endpoints son síncronos, FastAPI los ejecuta en varios
            # hilos que comparten esa conexión. Con mucha concurrencia SQLite podría
            # fallar de forma intermitente (responde 503). Es aceptable en el
            # prototipo; con un motor real (PostgreSQL, etc.) se usa un pool normal.
            opciones["poolclass"] = StaticPool
        return create_engine(url, **opciones)
    return create_engine(url)


engine = crear_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def crear_tablas(motor: Engine = engine) -> None:
    """Crea en la base todas las tablas registradas en Base."""
    # Importar los modelos ORM para que queden registrados en Base.metadata
    import app.repositories.ubicacion_repository  # noqa: F401
    import app.repositories.tipo_documento_repository  # noqa: F401
    import app.repositories.valor_repository  # noqa: F401
    import app.repositories.formato_repository  # noqa: F401
    Base.metadata.create_all(bind=motor)
