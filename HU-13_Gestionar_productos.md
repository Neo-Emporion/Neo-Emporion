# [HU-13] Gestionar productos del catálogo

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-03 Catálogo de Productos / SUB-07 Gestión de Productos |
| **Funcionalidades que cubre** | FUN-31 Registrar producto · FUN-32 Editar producto · FUN-33 Consultar/listar productos · FUN-34 Desactivar producto |
| **Reglas de negocio asociadas** | RN-01: un producto no puede publicarse si el vendedor no está "activo" · RN-02: el precio no puede ser menor o igual a cero · RN-05: un producto no puede pertenecer a una categoría inexistente o inactiva · RN-09: un vendedor suspendido no puede publicar ni editar productos |
| **APIs** | API-G25, API-G26, API-G27, API-G28 (agregadas en el Parcial 2) · consume API-I07 Consultar Estado de Vendedor (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 13 |
| **Depende de** | HU-10, HU-11 |
| **Actor** | Vendedor (la consulta también la usan compradores y visitantes) |

## 📖 Historia de Usuario

**Dado** que soy un vendedor aprobado en la plataforma,
**Para** ofrecer mis productos a los compradores,
**Que** necesito registrar, editar, consultar y desactivar mis productos, de modo que el catálogo muestre información actualizada y solo productos de vendedores verificados.

## 🔁 Flujo Esperado

**Registrar producto**
- El vendedor ingresa nombre, descripción, categoría y precio base.
- El sistema consume `POST /api/v1/catalogo/productos`.
- El backend consulta el estado del vendedor (API-I07) y valida que esté `ACTIVO` (RN-01), que la categoría esté activa (RN-05) y que el precio sea mayor que cero (RN-02).
- El backend crea el producto con estado `ACTIVO` asociado al vendedor.

**Editar producto**
- El vendedor modifica los datos de uno de sus productos con `PUT /api/v1/catalogo/productos/{id}`.
- El backend repite las validaciones y verifica que el vendedor no esté suspendido (RN-09).

**Consultar / listar productos**
- El usuario consulta el catálogo con filtros de búsqueda mediante `GET /api/v1/catalogo/productos`.

**Desactivar producto**
- El vendedor retira un producto de la vitrina con `PATCH /api/v1/catalogo/productos/{id}/desactivar`; el historial se conserva.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` con `nombre`, `descripcion`, `categoria_id` y `precio_base`.
- [ ] Se consulta la API-I07 y solo se permite registrar si el vendedor está `ACTIVO` (RN-01).
- [ ] Un vendedor `SUSPENDIDO` no puede registrar ni editar productos (RN-09).
- [ ] `precio_base` debe ser mayor que cero (RN-02) y `categoria_id` debe corresponder a una categoría activa (RN-05).
- [ ] Se expone un endpoint `PUT` para editar; solo el vendedor dueño del producto puede hacerlo.
- [ ] Se expone un endpoint `GET` con filtros opcionales `categoria_id`, `vendedor_id`, `texto`, `estado`, `pagina` y `tamano`; por defecto solo retorna productos `ACTIVO`.
- [ ] Se expone un endpoint `PATCH` que desactiva el producto sin eliminar su historial.
- [ ] La consulta es pública; el registro, la edición y la desactivación requieren rol Vendedor.

### 2. 📆 Estructura de la información

- [ ] Registro exitoso:

```json
{
  "mensaje": "Producto registrado exitosamente",
  "data": {
    "id": 8801,
    "nombre": "Camiseta de algodón",
    "descripcion": "Camiseta básica 100% algodón",
    "categoria_id": 12,
    "vendedor_id": 310,
    "precio_base": 45000,
    "estado": "ACTIVO"
  },
  "success": true
}
```

- [ ] Listado exitoso:

```json
{
  "mensaje": "Consulta de productos exitosa",
  "data": {
    "pagina": 1,
    "tamano": 20,
    "total": 1,
    "productos": [
      { "id": 8801, "nombre": "Camiseta de algodón", "categoria_id": 12, "precio_base": 45000, "estado": "ACTIVO" }
    ]
  },
  "success": true
}
```

- [ ] Vendedor no activo:

```json
{
  "mensaje": "El vendedor no está activo y no puede publicar productos",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Productos

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Registrar producto | API-G25 | `POST` | `/api/v1/catalogo/productos` | Agregada en el Parcial 2 |
| Editar producto | API-G26 | `PUT` | `/api/v1/catalogo/productos/{id}` | Agregada en el Parcial 2 |
| Consultar productos | API-G27 | `GET` | `/api/v1/catalogo/productos` | Agregada en el Parcial 2 |
| Desactivar producto | API-G28 | `PATCH` | `/api/v1/catalogo/productos/{id}/desactivar` | Agregada en el Parcial 2 |
| (Consumida) Consultar estado de vendedor | API-I07 | `GET` | `/api/v1/vendedores/{id}/estado` | Inventario inicial (API interna) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Registrar / Editar | `nombre` | body | texto | Sí | Nombre del producto (máx. 120 caracteres) |
| Registrar / Editar | `descripcion` | body | texto | Sí | Descripción del producto |
| Registrar / Editar | `categoria_id` | body | entero | Sí | Categoría activa |
| Registrar / Editar | `precio_base` | body | decimal | Sí | Mayor que cero |
| Editar / Desactivar | `id` | ruta | entero | Sí | Identificador del producto |
| Listar | `categoria_id`, `vendedor_id`, `texto`, `estado` | query | varios | No | Filtros de búsqueda |
| Listar | `pagina`, `tamano` | query | entero | No | Paginación (por defecto 1 y 20) |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Registrar | `201 Created` | Producto creado |
| Editar | `200 OK` | Producto actualizado |
| Listar | `200 OK` | Listado paginado de productos |
| Desactivar | `200 OK` | Producto con `estado = INACTIVO` |

### 📤 Ejemplo de comunicación – Consulta del estado del vendedor (API-I07)

Petición del módulo Catálogo: `GET /api/v1/vendedores/310/estado`

```json
{ "mensaje": "Consulta de estado exitosa", "data": { "id": 310, "estado": "ACTIVO" }, "success": true }
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Registrar un producto válido

- **Precondición:** El vendedor está `ACTIVO`, la categoría está activa y el precio es mayor que cero.
- **Acción:** Ejecutar `POST /api/v1/catalogo/productos` con datos válidos.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `estado` = `ACTIVO`
  - El producto queda asociado al vendedor autenticado

### ✅ Caso 2: Editar un producto propio

- **Precondición:** El producto pertenece al vendedor y este no está suspendido.
- **Acción:** Ejecutar `PUT /api/v1/catalogo/productos/8801` con un nuevo precio.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El precio se actualiza

### ✅ Caso 3: Listar productos con filtros

- **Precondición:** Existen productos de varias categorías.
- **Acción:** Ejecutar `GET /api/v1/catalogo/productos?categoria_id=12&texto=camiseta`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Solo se retornan productos activos que cumplen los filtros

### ✅ Caso 4: Desactivar un producto

- **Precondición:** El producto pertenece al vendedor.
- **Acción:** Ejecutar `PATCH /api/v1/catalogo/productos/8801/desactivar`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `estado` = `INACTIVO`; el historial del producto se conserva y deja de aparecer en la vitrina

### ❌ Caso 5: Vendedor no activo (RN-01)

- **Precondición:** El vendedor está `REGISTRADO`, `EN_VERIFICACION` o `RECHAZADO`.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - Campo `mensaje` contiene el texto: "El vendedor no está activo y no puede publicar productos"

### ❌ Caso 6: Vendedor suspendido (RN-09)

- **Precondición:** El vendedor está `SUSPENDIDO`.
- **Acción:** Ejecutar el `POST` o el `PUT`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - Campo `mensaje` contiene el texto: "El vendedor está suspendido y no puede publicar ni editar productos"

### ❌ Caso 7: Precio inválido (RN-02)

- **Precondición:** Ninguna.
- **Acción:** Ejecutar el `POST` con `precio_base = 0`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El precio debe ser mayor que cero"

### ❌ Caso 8: Categoría inexistente o inactiva (RN-05)

- **Precondición:** La categoría no existe o está inactiva.
- **Acción:** Ejecutar el `POST` con ese `categoria_id`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "La categoría indicada no existe o está inactiva"

### ❌ Caso 9: Editar un producto ajeno

- **Precondición:** El producto pertenece a otro vendedor.
- **Acción:** Ejecutar el `PUT`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - Campo `mensaje` contiene el texto: "No tiene permisos sobre este producto"

### ❌ Caso 10: Producto inexistente

- **Precondición:** No existe `id = 99999`.
- **Acción:** Ejecutar `PUT` o `PATCH` sobre él.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "El producto no existe"

### ❌ Caso 11: No es posible consultar el estado del vendedor

- **Precondición:** La API-I07 no responde.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - No se crea el producto
  - Campo `mensaje` contiene el texto: "No fue posible validar el estado del vendedor"

### ❌ Caso 12: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud de productos"

## ✅ Definición de Hecho

# Historia: Gestionar productos del catálogo

## 📦 Alcance Funcional

- [ ] Los cuatro endpoints funcionan según lo definido.
- [ ] Se aplican las reglas RN-01, RN-02, RN-05 y RN-09.
- [ ] La desactivación es lógica y conserva el historial.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (precio, categoría y estado del vendedor).
- [ ] Se cubrieron los casos de error, incluida la indisponibilidad de la API-I07.
- [ ] Las pruebas funcionales de los 12 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error

## 🔐 Manejo de Errores

- [ ] Se devuelve `400`, `403` y `404` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos o al módulo Vendedores.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
