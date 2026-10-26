# [HU-14] Gestionar variantes de producto

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-03 Catálogo de Productos / SUB-09 Variantes |
| **Funcionalidades que cubre** | FUN-41 Registrar variante · FUN-42 Editar variante · FUN-43 Consultar/listar variantes · FUN-44 Eliminar variante |
| **Regla de negocio asociada** | RN-03: una variante no puede tener stock negativo |
| **APIs** | API-G29, API-G30, API-G31, API-G32 (agregadas en el Parcial 2) · relacionada con API-I01 Consultar Stock de Producto (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 14 |
| **Depende de** | HU-12, HU-13 |
| **Actor** | Vendedor (la consulta también la usan compradores) |

## 📖 Historia de Usuario

**Dado** que soy un vendedor con productos registrados en una categoría con atributos definidos,
**Para** ofrecer mis productos en distintas combinaciones (talla, color) con su propio precio y existencias,
**Que** necesito registrar, editar, consultar y eliminar variantes, de modo que los compradores elijan la opción que quieren y el sistema controle el stock de cada una.

## 🔁 Flujo Esperado

**Registrar variante**
- El vendedor selecciona un producto y define la combinación de atributos, el precio y el stock inicial.
- El sistema consume `POST /api/v1/catalogo/productos/{id}/variantes`.
- El backend valida que los atributos correspondan a los de la categoría, que la combinación no exista y que el stock no sea negativo (RN-03).

**Editar variante**
- El vendedor modifica el stock o el precio con `PUT /api/v1/catalogo/variantes/{id}`.

**Consultar / listar variantes**
- El usuario consulta las variantes disponibles de un producto con `GET /api/v1/catalogo/productos/{id}/variantes`.

**Eliminar variante**
- El vendedor retira una variante que ya no comercializa con `DELETE /api/v1/catalogo/variantes/{id}`.
- El backend valida que no esté en pedidos en curso y la elimina de la oferta.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` con `atributos` (valores por atributo), `precio` y `stock`.
- [ ] Se valida que los atributos obligatorios de la categoría estén diligenciados y que los valores de tipo lista sean permitidos.
- [ ] No se permiten dos variantes con la misma combinación de atributos en un mismo producto.
- [ ] El `stock` no puede ser negativo (RN-03) y el `precio` debe ser mayor que cero.
- [ ] Se expone un endpoint `PUT` para editar `precio` y `stock`; una edición no puede dejar el stock por debajo de cero.
- [ ] Se expone un endpoint `GET` que lista las variantes del producto con su precio y stock disponible.
- [ ] Se expone un endpoint `DELETE` que no permite eliminar variantes presentes en pedidos en curso.
- [ ] Solo el vendedor dueño del producto puede registrar, editar o eliminar variantes; la consulta es pública.

### 2. 📆 Estructura de la información

- [ ] Registro exitoso:

```json
{
  "mensaje": "Variante registrada exitosamente",
  "data": {
    "id": 21001,
    "producto_id": 8801,
    "atributos": { "Talla": "M", "Color": "Azul" },
    "precio": 45000,
    "stock": 30,
    "estado": "ACTIVA"
  },
  "success": true
}
```

- [ ] Listado exitoso:

```json
{
  "mensaje": "Consulta de variantes exitosa",
  "data": [
    { "id": 21001, "atributos": { "Talla": "M", "Color": "Azul" }, "precio": 45000, "stock": 30 },
    { "id": 21002, "atributos": { "Talla": "L", "Color": "Azul" }, "precio": 45000, "stock": 12 }
  ],
  "success": true
}
```

- [ ] Stock negativo:

```json
{
  "mensaje": "El stock no puede ser negativo",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Variantes

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Registrar variante | API-G29 | `POST` | `/api/v1/catalogo/productos/{id}/variantes` | Agregada en el Parcial 2 |
| Editar variante | API-G30 | `PUT` | `/api/v1/catalogo/variantes/{id}` | Agregada en el Parcial 2 |
| Consultar variantes | API-G31 | `GET` | `/api/v1/catalogo/productos/{id}/variantes` | Agregada en el Parcial 2 |
| Eliminar variante | API-G32 | `DELETE` | `/api/v1/catalogo/variantes/{id}` | Agregada en el Parcial 2 |
| (Relacionada) Consultar stock de producto | API-I01 | `GET` | `/api/v1/catalogo/productos/{id}/stock` | Inventario inicial (API interna) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Registrar | `id` | ruta | entero | Sí | Identificador del producto |
| Registrar | `atributos` | body | objeto | Sí | Valor de cada atributo de la categoría |
| Registrar | `precio` | body | decimal | Sí | Mayor que cero |
| Registrar | `stock` | body | entero | Sí | Cero o mayor |
| Editar | `id` | ruta | entero | Sí | Identificador de la variante |
| Editar | `precio`, `stock` | body | decimal / entero | Sí | Nuevos valores |
| Consultar | `id` | ruta | entero | Sí | Identificador del producto |
| Eliminar | `id` | ruta | entero | Sí | Identificador de la variante |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Registrar | `201 Created` | Variante creada |
| Editar | `200 OK` | Variante actualizada |
| Consultar | `200 OK` | Arreglo de variantes del producto |
| Eliminar | `200 OK` | Confirmación con el `id` eliminado |

### 📤 Ejemplo de comunicación – Petición de registro

```json
{
  "atributos": { "Talla": "M", "Color": "Azul" },
  "precio": 45000,
  "stock": 30
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Registrar una variante válida

- **Precondición:** El producto pertenece al vendedor y su categoría define los atributos Talla y Color.
- **Acción:** Ejecutar `POST /api/v1/catalogo/productos/8801/variantes` con una combinación nueva.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `estado` = `ACTIVA`

### ✅ Caso 2: Editar precio y stock

- **Precondición:** La variante `id = 21001` existe y es del vendedor.
- **Acción:** Ejecutar `PUT /api/v1/catalogo/variantes/21001` con `stock = 50`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El stock se actualiza

### ✅ Caso 3: Consultar variantes de un producto

- **Precondición:** El producto tiene variantes.
- **Acción:** Ejecutar `GET /api/v1/catalogo/productos/8801/variantes`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Se listan las variantes con precio y stock

### ✅ Caso 4: Eliminar una variante sin pedidos en curso

- **Precondición:** La variante no está en pedidos en curso.
- **Acción:** Ejecutar `DELETE /api/v1/catalogo/variantes/21001`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - La variante deja de aparecer en la oferta

### ❌ Caso 5: Stock negativo (RN-03)

- **Precondición:** Ninguna.
- **Acción:** Ejecutar el `POST` o el `PUT` con `stock = -5`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El stock no puede ser negativo"

### ❌ Caso 6: Combinación de atributos duplicada

- **Precondición:** Ya existe la variante Talla M, Color Azul.
- **Acción:** Ejecutar el `POST` con la misma combinación.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "Ya existe una variante con esa combinación de atributos"

### ❌ Caso 7: Atributo obligatorio faltante o valor no permitido

- **Precondición:** "Talla" es obligatorio y de tipo lista (S, M, L).
- **Acción:** Ejecutar el `POST` sin Talla o con Talla `XXL`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` indica el atributo inválido: "El atributo Talla es obligatorio" o "El valor del atributo Talla no es permitido"

### ❌ Caso 8: Precio inválido

- **Precondición:** Ninguna.
- **Acción:** Ejecutar el `POST` con `precio = 0`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El precio debe ser mayor que cero"

### ❌ Caso 9: Eliminar una variante en pedidos en curso

- **Precondición:** La variante está en al menos un pedido en curso.
- **Acción:** Ejecutar el `DELETE`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "No es posible eliminar la variante porque está en pedidos en curso"

### ❌ Caso 10: Variante o producto ajeno o inexistente

- **Precondición:** El producto o la variante pertenece a otro vendedor, o no existe.
- **Acción:** Ejecutar `POST`, `PUT` o `DELETE`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden` si es ajeno, o `404 Not Found` si no existe

### ❌ Caso 11: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud de variantes"

## ✅ Definición de Hecho

# Historia: Gestionar variantes de producto

## 📦 Alcance Funcional

- [ ] Los cuatro endpoints funcionan según lo definido.
- [ ] Se valida la combinación de atributos contra los de la categoría y se respeta RN-03.
- [ ] No se eliminan variantes presentes en pedidos en curso.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (atributos, duplicados, stock y precio).
- [ ] Se cubrieron los casos de error.
- [ ] Las pruebas funcionales de los 11 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error

## 🔐 Manejo de Errores

- [ ] Se devuelve `400`, `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
