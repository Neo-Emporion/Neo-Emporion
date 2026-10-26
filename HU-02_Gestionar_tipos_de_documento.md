# [HU-02] Gestionar tipos de documento

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-01 Parametrización / SUB-01 Catálogos de Identificación |
| **Funcionalidades que cubre** | FUN-01 Registrar tipo de documento · FUN-02 Editar tipo de documento · FUN-03 Consultar/listar tipos de documento · FUN-05 Desactivar tipo de documento |
| **Regla de negocio asociada** | RN-48: no pueden existir dos tipos de documento con el mismo código |
| **APIs** | API-G05, API-G06, API-G07 (agregadas en el Parcial 2) · API-I08 Consultar Tipos de Documento (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 2 |
| **Depende de** | — (ninguna) |
| **Actor** | Administrador de la plataforma (la consulta también la usan los módulos Usuarios y Vendedores) |

## 📖 Historia de Usuario

**Dado** que soy el administrador de la plataforma,
**Para** mantener actualizado el catálogo de tipos de identificación (cédula, NIT, RUT, pasaporte),
**Que** necesito registrar, editar, consultar y desactivar tipos de documento, de modo que el registro de compradores y la verificación de vendedores solo acepten documentos válidos y sin ambigüedad.

## 🔁 Flujo Esperado

**Registrar tipo de documento**
- El administrador ingresa el código y el nombre del nuevo tipo (ej. `NIT`, "Número de Identificación Tributaria").
- El sistema consume el endpoint `POST /api/v1/parametrizacion/tipos-documento`.
- El backend valida que el código no esté duplicado (RN-48) y almacena el tipo con estado `ACTIVO`.

**Editar tipo de documento**
- El administrador selecciona un tipo y modifica su nombre o descripción.
- El sistema consume `PUT /api/v1/parametrizacion/tipos-documento/{id}`.
- El backend valida el cambio y actualiza el registro. El código no se modifica.

**Consultar / listar tipos de documento**
- El administrador o un módulo solicitante pide el listado.
- El sistema consume `GET /api/v1/parametrizacion/tipos-documento`.
- El backend consulta los registros y retorna el listado.

**Desactivar tipo de documento**
- El administrador selecciona el tipo que ya no se utiliza.
- El sistema consume `PATCH /api/v1/parametrizacion/tipos-documento/{id}/desactivar`.
- El backend valida que no afecte registros existentes y lo marca como `INACTIVO` (no se elimina físicamente).

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` que recibe `codigo` (único, 2 a 10 caracteres en mayúscula) y `nombre`.
- [ ] Se valida que no exista otro tipo de documento con el mismo `codigo` (RN-48).
- [ ] Se expone un endpoint `PUT` que permite editar `nombre` y `descripcion`; el `codigo` no puede modificarse.
- [ ] Se expone un endpoint `GET` que retorna los tipos de documento, con filtro opcional `estado` (por defecto solo `ACTIVO`).
- [ ] Se expone un endpoint `PATCH` que desactiva el tipo; no se permite desactivarlo si existen compradores o vendedores activos registrados con ese tipo.
- [ ] Las operaciones de registro, edición y desactivación están permitidas solo al rol Administrador. La consulta está abierta a los módulos internos.

### 2. 📆 Estructura de la información

- [ ] Registro exitoso:

```json
{
  "mensaje": "Tipo de documento registrado exitosamente",
  "data": {
    "id": 4,
    "codigo": "NIT",
    "nombre": "Número de Identificación Tributaria",
    "estado": "ACTIVO"
  },
  "success": true
}
```

- [ ] Si el código ya existe:

```json
{
  "mensaje": "Ya existe un tipo de documento con el código indicado",
  "data": null,
  "success": false
}
```

- [ ] Listado exitoso:

```json
{
  "mensaje": "Consulta de tipos de documento exitosa",
  "data": [
    { "id": 1, "codigo": "CC", "nombre": "Cédula de ciudadanía", "estado": "ACTIVO" },
    { "id": 4, "codigo": "NIT", "nombre": "Número de Identificación Tributaria", "estado": "ACTIVO" }
  ],
  "success": true
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Tipos de documento

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Registrar tipo de documento | API-G05 | `POST` | `/api/v1/parametrizacion/tipos-documento` | Agregada en el Parcial 2 |
| Editar tipo de documento | API-G06 | `PUT` | `/api/v1/parametrizacion/tipos-documento/{id}` | Agregada en el Parcial 2 |
| Consultar / listar tipos de documento | API-I08 (Consultar Tipos de Documento) | `GET` | `/api/v1/parametrizacion/tipos-documento` | Inventario inicial (API interna) |
| Desactivar tipo de documento | API-G07 | `PATCH` | `/api/v1/parametrizacion/tipos-documento/{id}/desactivar` | Agregada en el Parcial 2 |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Registrar | `codigo` | body | texto | Sí | Código único del tipo (ej. `CC`, `NIT`, `RUT`, `PA`) |
| Registrar | `nombre` | body | texto | Sí | Nombre del tipo (máx. 80 caracteres) |
| Editar | `id` | ruta | entero | Sí | Identificador del tipo |
| Editar | `nombre`, `descripcion` | body | texto | Sí | Nuevos valores |
| Listar | `estado` | query | texto | No | `ACTIVO` (por defecto), `INACTIVO` o `TODOS` |
| Desactivar | `id` | ruta | entero | Sí | Identificador del tipo |

### 📤 Salidas

Todas las respuestas usan `mensaje`, `data` y `success`.

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Registrar | `201 Created` | Tipo de documento creado |
| Editar | `200 OK` | Tipo de documento actualizado |
| Listar | `200 OK` | Arreglo de tipos de documento |
| Desactivar | `200 OK` | Tipo con `estado = INACTIVO` |

### 📤 Ejemplo de comunicación – Desactivar tipo de documento

Petición: `PATCH /api/v1/parametrizacion/tipos-documento/4/desactivar`

```json
{
  "mensaje": "Tipo de documento desactivado exitosamente",
  "data": { "id": 4, "estado": "INACTIVO" },
  "success": true
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Registrar un tipo de documento válido

- **Precondición:** No existe un tipo con código `PA`.
- **Acción:** Ejecutar `POST /api/v1/parametrizacion/tipos-documento` con `codigo = PA` y `nombre = Pasaporte`.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `estado` = `ACTIVO`
  - Campo `mensaje` contiene el texto: "Tipo de documento registrado exitosamente"

### ✅ Caso 2: Editar el nombre de un tipo de documento

- **Precondición:** Existe el tipo con `id = 4`.
- **Acción:** Ejecutar `PUT /api/v1/parametrizacion/tipos-documento/4` con un nuevo `nombre`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El `nombre` se actualiza y el `codigo` permanece igual

### ✅ Caso 3: Listar tipos de documento activos

- **Precondición:** Existen tipos activos e inactivos.
- **Acción:** Ejecutar `GET /api/v1/parametrizacion/tipos-documento`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Solo se retornan tipos con `estado = ACTIVO`

### ✅ Caso 4: Desactivar un tipo de documento sin uso

- **Precondición:** Ningún comprador ni vendedor activo usa el tipo.
- **Acción:** Ejecutar `PATCH /api/v1/parametrizacion/tipos-documento/{id}/desactivar`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `estado` = `INACTIVO` y el registro se conserva en la base de datos

### ❌ Caso 5: Registrar un código duplicado (RN-48)

- **Precondición:** Ya existe el tipo con código `NIT`.
- **Acción:** Ejecutar `POST /api/v1/parametrizacion/tipos-documento` con `codigo = NIT`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "Ya existe un tipo de documento con el código indicado"

### ❌ Caso 6: Registrar con datos obligatorios faltantes

- **Precondición:** El usuario es administrador.
- **Acción:** Ejecutar `POST` sin el campo `codigo`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El campo codigo es obligatorio"

### ❌ Caso 7: Desactivar un tipo en uso

- **Precondición:** Existen compradores o vendedores activos registrados con ese tipo.
- **Acción:** Ejecutar `PATCH /api/v1/parametrizacion/tipos-documento/{id}/desactivar`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - El tipo conserva `estado = ACTIVO`
  - Campo `mensaje` contiene el texto: "No es posible desactivar el tipo de documento porque está en uso"

### ❌ Caso 8: Tipo de documento inexistente

- **Precondición:** No existe un tipo con `id = 99999`.
- **Acción:** Ejecutar `PUT` o `PATCH` sobre `/api/v1/parametrizacion/tipos-documento/99999`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "El tipo de documento no existe"

### ❌ Caso 9: Usuario sin permisos de administrador

- **Precondición:** El usuario autenticado no es Administrador.
- **Acción:** Ejecutar `POST /api/v1/parametrizacion/tipos-documento`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - No se crea ningún registro

### ❌ Caso 10: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud de tipos de documento"

## ✅ Definición de Hecho

# Historia: Gestionar tipos de documento

## 📦 Alcance Funcional

- [ ] Los cuatro endpoints (registrar, editar, listar y desactivar) funcionan según lo definido.
- [ ] Se valida la unicidad del código (RN-48) y la desactivación respeta los registros en uso.
- [ ] La desactivación es lógica y el código no puede modificarse.
- [ ] Las respuestas JSON cumplen con el contrato definido (`mensaje`, `data`, `success`).

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (unicidad y uso).
- [ ] Se cubrieron los casos de error y de listado sin resultados.
- [ ] Las pruebas funcionales de los 10 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error

## 🔐 Manejo de Errores

- [ ] Se devuelve `400` para datos inválidos, `403` sin permisos, `404` para tipos inexistentes y `409` para duplicados o desactivaciones no permitidas.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
