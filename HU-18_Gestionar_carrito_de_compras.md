# [HU-18] Gestionar el carrito de compras

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-05 Pedidos / SUB-13 Carrito de Compras |
| **Funcionalidades que cubre** | FUN-61 Agregar producto al carrito · FUN-62 Editar cantidad en el carrito · FUN-63 Consultar carrito · FUN-64 Eliminar producto del carrito · FUN-65 Vaciar carrito |
| **Regla de negocio asociada** | RN-03: una variante no puede tener stock negativo (el carrito no admite cantidades mayores al stock disponible) |
| **APIs** | API-G40, API-G41, API-G42, API-G43, API-G44 (agregadas en el Parcial 2) · consume API-I01 Consultar Stock de Producto (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 18 |
| **Depende de** | HU-07, HU-14 |
| **Actor** | Comprador |

## 📖 Historia de Usuario

**Dado** que soy un comprador con sesión iniciada,
**Para** reunir los productos que quiero comprar antes de pagar,
**Que** necesito agregar productos al carrito, cambiar sus cantidades, consultarlo, quitar ítems o vaciarlo, de modo que pueda revisar mi compra y su subtotal antes del checkout.

## 🔁 Flujo Esperado

**Agregar producto**
- El comprador elige una variante y una cantidad.
- El sistema consume `POST /api/v1/pedidos/carrito/items`.
- El backend consulta el stock (API-I01) y valida la cantidad. Si la variante ya está en el carrito, suma la cantidad.

**Editar cantidad**
- El comprador cambia la cantidad de un ítem con `PUT /api/v1/pedidos/carrito/items/{id}`.

**Consultar carrito**
- El comprador consulta los productos agregados y el subtotal con `GET /api/v1/pedidos/carrito`.

**Eliminar producto / Vaciar carrito**
- El comprador quita un ítem con `DELETE /api/v1/pedidos/carrito/items/{id}` o elimina todos con `DELETE /api/v1/pedidos/carrito`.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` con `variante_id` y `cantidad` (entero mayor o igual a 1).
- [ ] Antes de agregar o editar, se consulta la API-I01 y la cantidad total no puede superar el stock disponible.
- [ ] Solo se pueden agregar variantes de productos `ACTIVO`.
- [ ] Si la variante ya existe en el carrito, se acumula la cantidad en el mismo ítem.
- [ ] Se expone un endpoint `PUT` que reemplaza la cantidad de un ítem propio.
- [ ] Se expone un endpoint `GET` que retorna los ítems con precio unitario, subtotal por ítem y subtotal del carrito.
- [ ] Se exponen endpoints `DELETE` para quitar un ítem y para vaciar el carrito.
- [ ] Cada comprador tiene un solo carrito y solo puede ver y modificar el suyo.
- [ ] El carrito se muestra con el precio y la disponibilidad vigentes al momento de consultarlo.
- [ ] El parámetro `variante_id` se envía a la API-I01 como parámetro adicional a los definidos en el inventario inicial (id de producto y cantidad).

### 2. 📆 Estructura de la información

- [ ] Producto agregado:

```json
{
  "mensaje": "Producto agregado al carrito",
  "data": {
    "item_id": 9101,
    "variante_id": 21001,
    "cantidad": 2,
    "precio_unitario": 45000,
    "subtotal_item": 90000
  },
  "success": true
}
```

- [ ] Consulta del carrito:

```json
{
  "mensaje": "Consulta del carrito exitosa",
  "data": {
    "items": [
      { "item_id": 9101, "producto": "Camiseta de algodón", "atributos": { "Talla": "M", "Color": "Azul" }, "cantidad": 2, "precio_unitario": 45000, "subtotal_item": 90000 }
    ],
    "subtotal": 90000
  },
  "success": true
}
```

- [ ] Stock insuficiente:

```json
{
  "mensaje": "La cantidad solicitada supera el stock disponible",
  "data": { "stock_disponible": 3 },
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Carrito

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Agregar producto al carrito | API-G40 | `POST` | `/api/v1/pedidos/carrito/items` | Agregada en el Parcial 2 |
| Editar cantidad en el carrito | API-G41 | `PUT` | `/api/v1/pedidos/carrito/items/{id}` | Agregada en el Parcial 2 |
| Consultar carrito | API-G42 | `GET` | `/api/v1/pedidos/carrito` | Agregada en el Parcial 2 |
| Eliminar producto del carrito | API-G43 | `DELETE` | `/api/v1/pedidos/carrito/items/{id}` | Agregada en el Parcial 2 |
| Vaciar carrito | API-G44 | `DELETE` | `/api/v1/pedidos/carrito` | Agregada en el Parcial 2 |
| (Consumida) Consultar stock de producto | API-I01 | `GET` | `/api/v1/catalogo/productos/{id}/stock` | Inventario inicial (API interna) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Agregar | `variante_id` | body | entero | Sí | Variante a agregar |
| Agregar / Editar | `cantidad` | body | entero | Sí | Mayor o igual a 1 |
| Editar / Eliminar | `id` | ruta | entero | Sí | Identificador del ítem del carrito |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Agregar | `201 Created` | Ítem agregado o actualizado |
| Editar | `200 OK` | Ítem actualizado |
| Consultar | `200 OK` | Ítems y subtotal del carrito |
| Eliminar / Vaciar | `200 OK` | Confirmación y carrito actualizado |

### 📤 Ejemplo de comunicación – Consulta de stock (API-I01)

Petición del módulo Pedidos: `GET /api/v1/catalogo/productos/8801/stock?cantidad=2&variante_id=21001`

```json
{ "mensaje": "Consulta de stock exitosa", "data": { "disponible": true, "stock_actual": 30, "precio": 45000 }, "success": true }
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Agregar un producto con stock suficiente

- **Precondición:** La variante tiene stock 30 y el carrito está vacío.
- **Acción:** Ejecutar `POST /api/v1/pedidos/carrito/items` con `variante_id = 21001` y `cantidad = 2`.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - El carrito contiene el ítem con su subtotal

### ✅ Caso 2: Agregar una variante que ya está en el carrito

- **Precondición:** El carrito ya tiene 2 unidades de la variante.
- **Acción:** Agregar 1 unidad más de la misma variante.
- **Resultado esperado:**
  - El ítem queda con cantidad 3 (no se crea un ítem duplicado)

### ✅ Caso 3: Editar la cantidad de un ítem

- **Precondición:** Existe el ítem `id = 9101` en el carrito del comprador.
- **Acción:** Ejecutar `PUT /api/v1/pedidos/carrito/items/9101` con `cantidad = 5`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El subtotal se recalcula

### ✅ Caso 4: Consultar el carrito

- **Precondición:** El carrito tiene ítems.
- **Acción:** Ejecutar `GET /api/v1/pedidos/carrito`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Se listan los ítems y el subtotal del carrito

### ✅ Caso 5: Eliminar un ítem y vaciar el carrito

- **Precondición:** El carrito tiene ítems.
- **Acción:** Ejecutar `DELETE .../carrito/items/9101` y luego `DELETE .../carrito`.
- **Resultado esperado:**
  - Código HTTP `200 OK` en ambos casos
  - Al final el carrito queda sin ítems y con subtotal 0

### ❌ Caso 6: Cantidad mayor al stock

- **Precondición:** La variante tiene stock 3.
- **Acción:** Agregar `cantidad = 5`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "La cantidad solicitada supera el stock disponible"

### ❌ Caso 7: Cantidad inválida

- **Precondición:** Ninguna.
- **Acción:** Agregar con `cantidad = 0` o negativa.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "La cantidad debe ser mayor o igual a 1"

### ❌ Caso 8: Variante inexistente o de producto inactivo

- **Precondición:** La variante no existe o su producto está `INACTIVO`.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found` si no existe, o `409 Conflict` si el producto está inactivo
  - Campo `mensaje` indica la causa

### ❌ Caso 9: Ítem de otro comprador o inexistente

- **Precondición:** El ítem pertenece al carrito de otro comprador o no existe.
- **Acción:** Ejecutar `PUT` o `DELETE` sobre él.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "El ítem no existe en su carrito"

### ❌ Caso 10: Sin sesión iniciada

- **Precondición:** La petición no incluye un token válido.
- **Acción:** Ejecutar cualquiera de los endpoints.
- **Resultado esperado:**
  - Código HTTP `401 Unauthorized`

### ❌ Caso 11: No es posible consultar el stock

- **Precondición:** La API-I01 no responde.
- **Acción:** Agregar o editar un ítem.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - El carrito no cambia
  - Campo `mensaje` contiene el texto: "No fue posible validar la disponibilidad del producto"

### ❌ Caso 12: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud del carrito"

## ✅ Definición de Hecho

# Historia: Gestionar el carrito de compras

## 📦 Alcance Funcional

- [ ] Los cinco endpoints funcionan según lo definido.
- [ ] Toda cantidad se valida contra el stock con la API-I01.
- [ ] Cada comprador accede únicamente a su carrito.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias del cálculo de subtotales y de las validaciones de cantidad y stock.
- [ ] Se cubrieron los casos de error, incluida la indisponibilidad de la API-I01.
- [ ] Las pruebas funcionales de los 12 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error

## 🔐 Manejo de Errores

- [ ] Se devuelve `400`, `401`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos o al módulo Catálogo.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
