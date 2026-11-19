# HU-02 - Guía de pruebas manuales en Swagger

Esta guía permite comprobar manualmente los casos funcionales de
`HU-02_Gestionar_tipos_de_documento.md` desde la documentación interactiva
de FastAPI.

## 1. Estado actual y requisitos

Primero asegúrate de que la implementación de HU-02 esté presente y registrada
en `main.py`. Si Swagger solo muestra las rutas de HU-01, debes construir o
restaurar los archivos de HU-02 antes de ejecutar esta guía.

Desde la raíz del proyecto:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Abre <http://127.0.0.1:8000/docs>.

Los datos usan SQLite en memoria. Reiniciar `uvicorn` elimina todos los tipos
de documento registrados y deja una base limpia.

## 2. Configurar el token de administrador

El registro, la edición y la desactivación son operaciones administrativas.
Consulta el listado sin autorización.

1. Pulsa **Authorize** en Swagger.
2. En `BearerToken` escribe `token-administrador`.
3. Pulsa **Authorize** y luego **Close**.

Escribe solo `token-administrador`. Swagger agrega el prefijo `Bearer`
automáticamente.

Tokens disponibles para las pruebas:

| Token | Rol |
|---|---|
| `token-administrador` | ADMINISTRADOR |
| `token-comprador` | COMPRADOR |
| `token-vendedor` | VENDEDOR |

## 3. Caso 1 - Registrar un tipo válido

Abre:

```text
POST /api/v1/parametrizacion/tipos-documento
```

Pulsa **Try it out** y usa:

```json
{
  "codigo": "PA",
  "nombre": "Pasaporte"
}
```

Pulsa **Execute**.

Resultado esperado:

- HTTP `201 Created`.
- `mensaje` igual a `Tipo de documento registrado exitosamente`.
- `success` igual a `true`.
- `data.codigo` igual a `PA`.
- `data.nombre` igual a `Pasaporte`.
- `data.estado` igual a `ACTIVO`.

Anota el `id` devuelto. Lo necesitarás para editar y desactivar el tipo.

## 4. Caso 5 - Registrar un código duplicado

Primero registra `NIT`:

```json
{
  "codigo": "NIT",
  "nombre": "Número de Identificación Tributaria"
}
```

Resultado inicial esperado: HTTP `201`.

Luego repite exactamente el mismo cuerpo.

Resultado esperado:

- HTTP `409 Conflict`.
- `mensaje` igual a `Ya existe un tipo de documento con el código indicado`.
- `data` igual a `null`.
- `success` igual a `false`.
- No se crea un segundo registro.

## 5. Caso 2 - Editar el nombre sin cambiar el código

Abre:

```text
PUT /api/v1/parametrizacion/tipos-documento/{tipo_documento_id}
```

Usa el `id` obtenido al registrar `PA` y ejecuta con:

```json
{
  "codigo": "OTRO",
  "nombre": "Pasaporte internacional",
  "descripcion": "Documento de viaje"
}
```

Resultado esperado:

- HTTP `200 OK`.
- `mensaje` igual a `Tipo de documento actualizado exitosamente`.
- `success` igual a `true`.
- `data.codigo` sigue siendo `PA`.
- `data.nombre` cambia a `Pasaporte internacional`.
- `data.descripcion` cambia a `Documento de viaje`.

El campo `codigo` no se modifica aunque se envíe en el cuerpo. La
implementación debe seguir el caso de prueba y permitir omitir `descripcion`;
si se omite, debe conservar su valor actual.

## 6. Caso 3 - Consultar tipos activos

Abre:

```text
GET /api/v1/parametrizacion/tipos-documento
```

Ejecuta con:

- `estado`: `ACTIVO`
- `pagina`: `1`
- `tamano`: `20`

Resultado esperado:

- HTTP `200 OK`.
- `mensaje` igual a `Consulta de tipos de documento exitosa`.
- `success` igual a `true`.
- Solo aparecen registros con `estado=ACTIVO`.

Pruebas adicionales del listado:

| Parámetro `estado` | Resultado |
|---|---|
| `ACTIVO` | Solo tipos activos |
| `INACTIVO` | Solo tipos inactivos |
| `TODOS` | Activos e inactivos |

Este endpoint no requiere autenticación.

## 7. Caso 4 - Desactivar un tipo sin uso

Abre:

```text
PATCH /api/v1/parametrizacion/tipos-documento/{tipo_documento_id}/desactivar
```

Usa el `id` del tipo `PA` y pulsa **Execute**.

Resultado esperado:

- HTTP `200 OK`.
- `mensaje` igual a `Tipo de documento desactivado exitosamente`.
- `success` igual a `true`.
- `data.estado` igual a `INACTIVO`.
- El registro no se elimina.

Comprueba la conservación con:

```text
GET /api/v1/parametrizacion/tipos-documento?estado=TODOS
```

El tipo debe seguir apareciendo con estado `INACTIVO`.

## 8. Caso 6 - Enviar un campo obligatorio faltante

En el `POST` ejecuta:

```json
{
  "nombre": "Pasaporte"
}
```

Resultado esperado:

- HTTP `400 Bad Request`.
- `mensaje` igual a `El campo codigo es obligatorio`.
- `data` igual a `null`.
- `success` igual a `false`.

## 9. Caso 8 - Consultar o modificar un tipo inexistente

En:

```text
PUT /api/v1/parametrizacion/tipos-documento/99999
```

usa cualquier nombre válido. Luego prueba:

```text
PATCH /api/v1/parametrizacion/tipos-documento/99999/desactivar
```

Resultado esperado en ambas operaciones:

- HTTP `404 Not Found`.
- `mensaje` igual a `El tipo de documento no existe`.
- `data` igual a `null`.
- `success` igual a `false`.

## 10. Caso 9 - Usuario sin permisos de administrador

1. Pulsa **Authorize**.
2. Reemplaza `token-administrador` por `token-comprador`.
3. Ejecuta el `POST` con un código nuevo:

```json
{
  "codigo": "CE",
  "nombre": "Cédula de extranjería"
}
```

Resultado esperado:

- HTTP `403 Forbidden`.
- `mensaje` igual a `No tiene permisos para realizar esta operación`.
- `data` igual a `null`.
- `success` igual a `false`.
- No se crea el registro.

También puedes repetir la prueba con `token-vendedor`.

Para volver a las pruebas de administrador, pulsa **Authorize**, elimina el
token actual y autoriza nuevamente con `token-administrador`.

## 11. Prueba adicional sin autenticación

Con la autorización cerrada, ejecuta nuevamente una operación administrativa,
por ejemplo el `POST`.

Resultado esperado:

- HTTP `401 Unauthorized`.
- `mensaje` igual a `Se requiere un token de autenticación válido`.
- `data` igual a `null`.
- `success` igual a `false`.

## 12. Casos que deben verificarse automatizadamente

### Caso 7 - Desactivar un tipo en uso

La HU exige responder `409 Conflict` cuando compradores o vendedores activos
usan el tipo. El resultado manual no puede forzarse desde Swagger si los
módulos de compradores y vendedores aún no están implementados o si la
consulta de uso sigue siendo provisional.

Resultado esperado:

- HTTP `409 Conflict`.
- `mensaje` igual a
  `No es posible desactivar el tipo de documento porque está en uso`.
- `data` igual a `null`.
- `success` igual a `false`.
- El tipo conserva `estado=ACTIVO`.

Comprueba este caso con una prueba automatizada que simule registros asociados
mediante `monkeypatch`.

### Caso 10 - Falla de base de datos

Una caída real de SQLite no puede controlarse de forma segura desde Swagger.
El caso debe simularse en el repositorio o en el servicio.

Resultado esperado:

- HTTP `503 Service Unavailable`.
- `mensaje` definido por la implementación para la falla de base de datos.
- `data` igual a `null`.
- `success` igual a `false`.

## 13. Comprobación rápida

Ejecuta esta secuencia de menor a mayor dificultad:

1. Registrar `PA`.
2. Consultar el listado activo.
3. Editar el `id` de `PA`.
4. Desactivar el `id` de `PA`.
5. Consultar `estado=TODOS`.
6. Registrar `NIT` y luego repetirlo.
7. Registrar sin `codigo`.
8. Editar `id=99999`.
9. Probar el endpoint con `token-comprador`.
10. Ejecutar con sesión cerrada.

| Caso | Operación manual | HTTP esperado |
|---|---|---|
| 1 | Registrar `PA` | `201` |
| 2 | Editar el `id` de `PA` | `200` |
| 3 | Listar tipos activos | `200` |
| 4 | Desactivar el `id` de `PA` | `200` |
| 5 | Registrar `NIT` dos veces | Segunda petición `409` |
| 6 | Registrar sin `codigo` | `400` |
| 7 | Desactivar tipo en uso | `409` automatizado |
| 8 | Editar o desactivar `99999` | `404` |
| 9 | Registrar con rol comprador | `403` |
| 10 | Simular falla de base de datos | `503` automatizado |
