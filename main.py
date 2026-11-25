# ─────────────────────────────────────────────────────────────
# PUNTO DE ENTRADA — crea la app FastAPI y registra los routers
# Todas las rutas de negocio quedan bajo el prefijo /api/v1
# ─────────────────────────────────────────────────────────────

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.api.errores import registrar_manejadores
from app.api.schemas.respuesta import exito
from app.api.routers.ubicacion_router import router as ubicacion_router
from app.api.routers.tipo_documento_router import router as tipo_documento_router
from app.api.routers.valor_router import router as valor_router
from app.core.config import APP_ENV, APP_NAME
from app.core.database import crear_tablas


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # Al arrancar: crea las tablas en la base de datos (en memoria)
    crear_tablas()
    yield


app = FastAPI(
    title=APP_NAME,
    description="Marketplace multi-vendedor B2B2C — Web Services (arquitectura de capas)",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)

# Respuestas de error con el envoltorio { mensaje, data, success }
registrar_manejadores(app)

# MOD-01 Parametrización — HU-01 Catálogo geográfico
app.include_router(ubicacion_router, prefix="/api/v1")
# MOD-01 Parametrización — HU-02 Tipos de documento
app.include_router(tipo_documento_router, prefix="/api/v1")
# MOD-01 Parametrización — HU-03 Catálogos transaccionales
app.include_router(valor_router, prefix="/api/v1")


def generar_openapi():
    """FastAPI documenta un 422 automático en cada endpoint, pero en este proyecto
    los errores de validación responden 400 (ver app/api/errores.py). Se quita el 422."""
    if app.openapi_schema:
        return app.openapi_schema
    esquema = get_openapi(title=app.title, version=app.version,
                          description=app.description, routes=app.routes)
    for metodos in esquema["paths"].values():
        for operacion in metodos.values():
            operacion.get("responses", {}).pop("422", None)
    app.openapi_schema = esquema
    return esquema


app.openapi = generar_openapi


@app.get("/", tags=["Root"])
def inicio():
    return exito("Neo-Emporion API funcionando", None)


@app.get("/health", tags=["Root"])
def health():
    return exito("Servicio disponible",
                 {"status": "ok", "version": app.version, "environment": APP_ENV})


# ── Para correr directamente con: python main.py ─────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
