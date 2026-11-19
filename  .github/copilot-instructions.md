# Instrucciones para Copilot — proyecto Neo-Emporion

Ayudas a construir historias de usuario (HU) del proyecto Neo-Emporion: un marketplace B2B2C hecho con **Python + FastAPI**, solo APIs (sin frontend). Responde siempre en **español** y explica de forma clara qué hiciste y por qué.

## Antes de escribir código
1. Lee **`CLAUDE.md`** (contexto y decisiones del proyecto) y el archivo de la HU (`HU-XX_*.md`). Si se contradicen, **manda la HU**.
2. Usa como **plantilla los archivos de HU-01** y copia su forma exactamente:
   - `app/domain/models/dato_geografico.py` (schemas + entidad con reglas y `to_response()`)
   - `app/domain/exceptions/ubicacion.py` (errores con el mensaje exacto de la HU)
   - `app/repositories/ubicacion_repository.py` (tabla SQLAlchemy + repositorio + instancia única al final)
   - `app/services/ubicacion_service.py` (servicio que recibe el repositorio en el constructor)
   - `app/api/routers/ubicacion_router.py` (router que llama al servicio y convierte errores en HTTPException)
   - `tests/test_hu01_ubicaciones.py` y `tests/test_hu01_dominio.py` (pruebas)
3. **No inventes.** Si la HU no define algo (un mensaje, una regla, un caso), escríbelo en el código como `# TODO(pendiente): ...` y avísale al usuario para que lo consulte con el equipo.

## Reglas que no se pueden romper
- **Capas:** API (router) → Servicio → Dominio ← Repositorio. Las reglas de negocio van en el dominio o el servicio, **nunca en el router**. El dominio no importa FastAPI ni SQLAlchemy.
- **Nombres:** el archivo de dominio se llama como la **entidad** de la HU (`app/domain/models/<entidad>.py`). Router, servicio, repositorio y excepciones se llaman como el **recurso** de la HU: `<recurso>_router.py`, `<recurso>_service.py`, `<recurso>_repository.py`, `exceptions/<recurso>.py`. Siempre con guion bajo, nunca con punto.
- **Base de datos:** SQLAlchemy sobre SQLite en memoria. La tabla ORM vive en el repositorio y hereda de `Base` (`app/core/database.py`). Cada método del repositorio abre su sesión con `SessionLocal` y usa el decorador que convierte `SQLAlchemyError` en el error `503` de la HU.
- **Errores de dominio:** heredan de `ErrorDominio` (`app/domain/exceptions/base.py`) y llevan el **mensaje exacto** de la HU.
- **Toda respuesta** usa el envoltorio `{ "mensaje": ..., "data": ..., "success": ... }`. Usa `exito()` de `app/api/schemas/respuesta.py`. Los errores ya los envuelve `app/api/errores.py`.
- **Códigos HTTP:** `201` creado, `200` OK, `400` datos inválidos (no `422`), `401` sin token, `403` sin permisos, `404` no existe, `409` duplicado o conflicto, `503` falla de base de datos.
- **Seguridad:** usa `Depends(requiere_administrador)` de `app/api/dependencies/seguridad.py` (tokens de prueba: `token-administrador`, `token-comprador`, `token-vendedor`).
- **Rutas** bajo `/api/v1`, en español y `snake_case`, **exactamente** como dice la HU. Estados en MAYÚSCULAS.
- **Swagger:** cada endpoint lleva `summary` con el ID de la API (ej. `"API-G05 · Registrar tipo de documento"`), `description` y ejemplos de éxito y de error.

## Archivos compartidos (tócalos solo para AGREGAR, nunca para cambiar lo que ya existe)
- `main.py`: agrega `app.include_router(<recurso>_router, prefix="/api/v1")`.
- `app/core/database.py`: en `crear_tablas` agrega el import de tu repositorio.
- `tests/conftest.py`: agrega tus propios fixtures con nombres nuevos; no modifiques los de HU-01.
- **No modifiques** `app/api/errores.py`, `app/api/schemas/respuesta.py`, `app/api/dependencies/seguridad.py` ni los archivos de otras HU. Si crees que hace falta, pregúntale al usuario.

## Pruebas
- Un test por cada caso de prueba de la HU (✅ y ❌), con el **mismo código HTTP** y el **mismo texto de `mensaje`** (compara con `==`).
- Pruebas unitarias del dominio en `tests/test_huXX_dominio.py`.
- Antes de terminar, **toda** la suite debe pasar: `pytest -v`. Si falla una prueba de otra HU, tu cambio rompió algo.
