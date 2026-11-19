# Neo-Emporion

## Ejecutar

```bash
source venv/bin/activate
uvicorn main:app --reload
```

Abre <http://127.0.0.1:8000/docs>.

## HU-02 - Tipos de documento

La HU-02 expone los siguientes endpoints bajo `/api/v1`:

- `POST /parametrizacion/tipos-documento` - API-G05.
- `PUT /parametrizacion/tipos-documento/{id}` - API-G06.
- `GET /parametrizacion/tipos-documento` - API-I08.
- `PATCH /parametrizacion/tipos-documento/{id}/desactivar` - API-G07.

Al editar, `nombre` y `descripcion` son obligatorios. La consulta devuelve
directamente un arreglo en `data`, mientras conserva los parámetros
paginados `pagina` y `tamano`.

Las operaciones administrativas usan:

```text
Authorization: Bearer token-administrador
```

Ejecuta las pruebas con:

```bash
venv/bin/python -m pytest -v
```