# [HU-21] Dividir pedido multi-vendedor en sub-órdenes

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-05 Pedidos / SUB-15 Gestión de Estados |
| **Funcionalidad que cubre** | FUN-75 Dividir pedido por vendedor |
| **Regla de negocio asociada** | RN-14: un pedido con productos de varios vendedores debe dividirse en sub-órdenes independientes |
| **APIs** | API-G51 (agregada en el Parcial 2) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 21 |
| **Depende de** | HU-10, HU-19 |
| **Actor** | Sistema (módulo Pedidos) |

## 📖 Historia de Usuario

**Dado** que un comprador confirmó un pedido con productos de uno o varios vendedores,
**Para** que cada vendedor gestione su propia preparación, entrega y liquidación,
**Que** necesito que el sistema divida el pedido en sub-órdenes, una por vendedor, de modo que cada sub-orden se atienda y se siga de forma independiente.

## 🔁 Flujo Esperado

- El sistema identifica los vendedores de los ítems del pedido confirmado.
- El sistema consume el endpoint `POST /api/v1/pedidos/{id}/dividir`.
- El backend crea una sub-orden por cada vendedor, con sus ítems, subtotal y su propio estado.
- El backend deja el pedido como agrupador de las sub-órdenes y retorna el resultado.
- Cada sub-orden se gestiona de forma independiente (preparación, guía y liquidación).

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` con el `id` del pedido en la ruta.
- [ ] Solo se puede dividir un pedido confirmado (estados `PENDIENTE_PAGO`, `PAGADO` o `EN_PREPARACION`) que no haya sido dividido antes.
- [ ] Se crea exactamente una sub-orden por vendedor distinto presente en el pedido (RN-14).
- [ ] Un pedido de un solo vendedor genera una única sub-orden.
- [ ] Cada sub-orden contiene solo los ítems de su vendedor y su subtotal; la suma de subtotales de las sub-órdenes es igual al subtotal del pedido.
- [ ] Cada sub-orden nace con el mismo estado del pedido y evoluciona de forma independiente.
- [ ] Solo se incluyen vendedores en estado `ACTIVO`; si alguno no lo está, la división se rechaza.
- [ ] La operación es invocada por el sistema (módulo Pedidos) y no por el comprador.

### 2. 📆 Estructura de la información

- [ ] División exitosa:

```json
{
  "mensaje": "Pedido dividido exitosamente",
  "data": {
    "pedido_id": 7001,
    "sub_ordenes": [
      { "sub_orden_id": 7001001, "vendedor_id": 310, "items": 2, "subtotal": 90000, "estado": "PENDIENTE_PAGO" },
      { "sub_orden_id": 7001002, "vendedor_id": 412, "items": 1, "subtotal": 35000, "estado": "PENDIENTE_PAGO" }
    ]
  },
  "success": true
}
```

- [ ] Pedido ya dividido:

```json
{
  "mensaje": "El pedido ya fue dividido en sub-órdenes",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoint – Dividir pedido

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Dividir pedido por vendedor | API-G51 | `POST` | `/api/v1/pedidos/{id}/dividir` | Agregada en el Parcial 2 |

### 📥 Entradas

| Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `id` | ruta | entero | Sí | Identificador del pedido a dividir |

### 📤 Salidas

| Código HTTP | Contenido de `data` |
|---|---|
| `201 Created` | `pedido_id` y arreglo de sub-órdenes (id, vendedor, cantidad de ítems, subtotal y estado) |

### 📤 Ejemplo de comunicación

Petición: `POST /api/v1/pedidos/7001/dividir` (sin cuerpo).

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Dividir un pedido con dos vendedores

- **Precondición:** El pedido tiene ítems de los vendedores 310 y 412 y no ha sido dividido.
- **Acción:** Ejecutar `POST /api/v1/pedidos/7001/dividir`.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Se crean dos sub-órdenes, una por vendedor
  - La suma de los subtotales coincide con el subtotal del pedido

### ✅ Caso 2: Pedido de un solo vendedor

- **Precondición:** Todos los ítems son del mismo vendedor.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Se crea una única sub-orden

### ✅ Caso 3: Las sub-órdenes evolucionan de forma independiente

- **Precondición:** El pedido fue dividido en dos sub-órdenes.
- **Acción:** Cambiar el estado de una sub-orden a `ENVIADO`.
- **Resultado esperado:**
  - La otra sub-orden conserva su estado

### ❌ Caso 4: Pedido ya dividido

- **Precondición:** El pedido ya tiene sub-órdenes.
- **Acción:** Ejecutar de nuevo el `POST`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - No se crean sub-órdenes adicionales
  - Campo `mensaje` contiene el texto: "El pedido ya fue dividido en sub-órdenes"

### ❌ Caso 5: Pedido en un estado que no permite la división

- **Precondición:** El pedido está `CANCELADO`, `ENVIADO` o `ENTREGADO`.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "El pedido no puede dividirse en su estado actual"

### ❌ Caso 6: Vendedor que no está activo

- **Precondición:** Uno de los vendedores del pedido no está `ACTIVO`.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - No se crea ninguna sub-orden
  - Campo `mensaje` contiene el texto: "El pedido incluye un vendedor que no está activo"

### ❌ Caso 7: Pedido inexistente o sin ítems

- **Precondición:** No existe el pedido o no tiene ítems.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found` si no existe, o `400 Bad Request` si no tiene ítems

### ❌ Caso 8: Invocación por un actor no autorizado

- **Precondición:** Un comprador intenta ejecutar la operación.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`

### ❌ Caso 9: Falla de base de datos

- **Precondición:** La base de datos no está disponible a mitad de la operación.
- **Acción:** Ejecutar el `POST` bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - No quedan sub-órdenes parciales (la operación es atómica)
  - Campo `mensaje` contiene el texto: "No fue posible dividir el pedido"

## ✅ Definición de Hecho

# Historia: Dividir pedido multi-vendedor en sub-órdenes

## 📦 Alcance Funcional

- [ ] El endpoint genera una sub-orden por vendedor (RN-14).
- [ ] La suma de los subtotales de las sub-órdenes coincide con la del pedido.
- [ ] La operación es atómica: o se crean todas las sub-órdenes o ninguna.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de la agrupación por vendedor y de la consistencia de subtotales.
- [ ] Se cubrieron los casos de error.
- [ ] Las pruebas funcionales de los 9 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoint documentado en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito del endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error

## 🔐 Manejo de Errores

- [ ] Se devuelve `400`, `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
