# [HU-19] Confirmar pedido (checkout)

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-05 Pedidos / SUB-14 Checkout |
| **Funcionalidades que cubre** | FUN-66 Seleccionar dirección de entrega · FUN-67 Seleccionar método de pago · FUN-68 Aplicar cupón en checkout · FUN-69 Confirmar pedido |
| **Reglas de negocio asociadas** | RN-11: un pedido no puede confirmarse si algún ítem no tiene stock disponible · RN-13: el total del pedido debe ser igual a la suma de los subtotales menos los descuentos aplicados |
| **APIs** | API-G45, API-G46, API-G47, API-G48 (agregadas en el Parcial 2) · consume API-I01 Consultar Stock, API-I03 Cotizar Envío, API-I06 Validar Cupón y API-I05 Enviar Notificación (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 19 |
| **Depende de** | HU-03, HU-15, HU-17, HU-18 |
| **Actor** | Comprador |

## 📖 Historia de Usuario

**Dado** que soy un comprador con productos en mi carrito,
**Para** finalizar mi compra,
**Que** necesito elegir la dirección de entrega y el método de pago, aplicar un cupón si tengo uno y confirmar el pedido, de modo que el sistema valide la disponibilidad, calcule el total con el envío y deje el pedido listo para el pago.

## 🔁 Flujo Esperado

**Seleccionar dirección de entrega**
- El comprador elige una de sus direcciones.
- El sistema consume `PUT /api/v1/pedidos/checkout/direccion`.
- El backend valida que la dirección sea del comprador y su ciudad esté publicada, la asocia al checkout y cotiza el envío (API-I03).

**Seleccionar método de pago**
- El comprador elige el método con `PUT /api/v1/pedidos/checkout/metodo-pago`.
- El backend valida que el método esté habilitado en Parametrización y lo asocia al checkout.

**Aplicar cupón**
- El comprador ingresa el código con `POST /api/v1/pedidos/checkout/cupon`.
- El backend valida el cupón con el módulo Promociones (API-I06) y aplica el descuento.

**Confirmar pedido**
- El comprador confirma con `POST /api/v1/pedidos`.
- El backend verifica el stock de cada ítem (API-I01, RN-11), calcula el total (RN-13) y crea el pedido en estado `PENDIENTE_PAGO`.
- El backend notifica al comprador que su pedido quedó registrado (API-I05).
- El cobro se realiza después en la HU-22 y la guía de envío en la HU-23; esta historia no los ejecuta.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `PUT` de dirección con `direccion_id`; la dirección debe ser del comprador autenticado.
- [ ] Al asociar la dirección se cotiza el envío y se guarda `costo_envio` en el checkout.
- [ ] Se expone un endpoint `PUT` de método de pago con `metodo_pago_id`; solo se aceptan métodos activos y publicados.
- [ ] Se expone un endpoint `POST` de cupón con `codigo`; el descuento se aplica solo si el cupón es válido (API-I06) y solo se permite un cupón por checkout.
- [ ] Se expone un endpoint `POST` de confirmación; requiere carrito con ítems, dirección y método de pago seleccionados.
- [ ] No se confirma el pedido si algún ítem no tiene stock suficiente (RN-11).
- [ ] El total del pedido es la suma de los subtotales menos los descuentos (RN-13); el valor a pagar suma además el costo de envío.
- [ ] Al confirmar, el pedido se crea en `PENDIENTE_PAGO` y se solicita la notificación al comprador; el cobro (HU-22) y la guía (HU-23) quedan fuera de esta historia.
- [ ] El carrito se conserva hasta que el pago sea aprobado (HU-22).
- [ ] La confirmación es idempotente: reenviar la misma solicitud no crea pedidos duplicados.

### 2. 📆 Estructura de la información

- [ ] Dirección seleccionada:

```json
{
  "mensaje": "Dirección de entrega asociada al checkout",
  "data": { "direccion_id": 4401, "costo_envio": 12000, "tiempo_estimado_dias": 3 },
  "success": true
}
```

- [ ] Pedido confirmado:

```json
{
  "mensaje": "Pedido confirmado exitosamente",
  "data": {
    "pedido_id": 7001,
    "estado": "PENDIENTE_PAGO",
    "subtotal": 90000,
    "descuento": 9000,
    "total": 81000,
    "costo_envio": 12000,
    "total_a_pagar": 93000
  },
  "success": true
}
```

- [ ] Stock insuficiente:

```json
{
  "mensaje": "Algunos productos no tienen stock suficiente",
  "data": { "items_sin_stock": [ { "variante_id": 21001, "stock_disponible": 1 } ] },
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Checkout

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Seleccionar dirección de entrega | API-G45 | `PUT` | `/api/v1/pedidos/checkout/direccion` | Agregada en el Parcial 2 |
| Seleccionar método de pago | API-G46 | `PUT` | `/api/v1/pedidos/checkout/metodo-pago` | Agregada en el Parcial 2 |
| Aplicar cupón en checkout | API-G47 | `POST` | `/api/v1/pedidos/checkout/cupon` | Agregada en el Parcial 2 |
| Confirmar pedido | API-G48 | `POST` | `/api/v1/pedidos` | Agregada en el Parcial 2 |
| (Consumida) Consultar stock | API-I01 | `GET` | `/api/v1/catalogo/productos/{id}/stock` | Inventario inicial (API interna) |
| (Consumida) Cotizar envío | API-I03 | `POST` | `/api/v1/envios/cotizaciones` | Inventario inicial (API interna) |
| (Consumida) Validar cupón | API-I06 | `GET` | `/api/v1/promociones/cupones/{codigo}/validar` | Inventario inicial (API interna) |
| (Consumida) Enviar notificación | API-I05 | `POST` | `/api/v1/notificaciones/enviar` | Inventario inicial (API interna) |

Integraciones: el cobro lo realiza la HU-22 y la guía de envío la HU-23, ambas construidas después de esta historia y que parten del pedido en `PENDIENTE_PAGO` que aquí se crea. Solo el envío de la notificación (HU-25) se prueba con un simulador (mock) hasta que esa historia esté disponible. El descuento definitivo del stock tras la venta se implementa en HU-28.

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Dirección | `direccion_id` | body | entero | Sí | Dirección del comprador |
| Método de pago | `metodo_pago_id` | body | entero | Sí | Método de pago activo y publicado |
| Cupón | `codigo` | body | texto | Sí | Código del cupón |
| Confirmar | `Idempotency-Key` | encabezado | texto | Sí | Identificador único de la solicitud para evitar duplicados |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Dirección | `200 OK` | Dirección asociada y costo de envío |
| Método de pago | `200 OK` | Método asociado |
| Cupón | `200 OK` | Código y valor del descuento aplicado |
| Confirmar | `201 Created` | Pedido con estado y totales |

### 📤 Ejemplo de comunicación – Validar cupón (API-I06)

Petición del módulo Pedidos: `GET /api/v1/promociones/cupones/PROMO10/validar?monto=90000`

```json
{ "mensaje": "Cupón válido", "data": { "valido": true, "descuento": 9000 }, "success": true }
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Seleccionar dirección y cotizar el envío

- **Precondición:** El comprador tiene un carrito con ítems y una dirección con ciudad publicada.
- **Acción:** Ejecutar `PUT /api/v1/pedidos/checkout/direccion` con `direccion_id = 4401`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - La respuesta incluye `costo_envio` y `tiempo_estimado_dias`

### ✅ Caso 2: Seleccionar un método de pago habilitado

- **Precondición:** El método está activo y publicado.
- **Acción:** Ejecutar `PUT /api/v1/pedidos/checkout/metodo-pago`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El método queda asociado al checkout

### ✅ Caso 3: Aplicar un cupón válido

- **Precondición:** El cupón es válido para el monto del carrito.
- **Acción:** Ejecutar `POST /api/v1/pedidos/checkout/cupon` con el código.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El descuento se refleja en el total

### ✅ Caso 4: Confirmar un pedido válido

- **Precondición:** Hay dirección y método de pago, y todos los ítems tienen stock.
- **Acción:** Ejecutar `POST /api/v1/pedidos`.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `estado` = `PENDIENTE_PAGO`
  - `total` = subtotal menos descuento (RN-13)
  - El pedido queda listo para ser pagado (HU-22)

### ✅ Caso 5: Reenviar la misma confirmación

- **Precondición:** El pedido ya fue confirmado con una `Idempotency-Key`.
- **Acción:** Ejecutar de nuevo `POST /api/v1/pedidos` con la misma clave.
- **Resultado esperado:**
  - Se retorna el mismo pedido y no se crea uno nuevo

### ❌ Caso 6: Dirección de otro comprador o ciudad no válida

- **Precondición:** La dirección no pertenece al comprador o su ciudad no está publicada.
- **Acción:** Ejecutar el `PUT` de dirección.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden` si es ajena, o `400 Bad Request` si la ciudad no es válida

### ❌ Caso 7: Destino sin cobertura de envío

- **Precondición:** La API-I03 indica que el destino no tiene cobertura.
- **Acción:** Ejecutar el `PUT` de dirección.
- **Resultado esperado:**
  - Código HTTP `422 Unprocessable Entity`
  - Campo `mensaje` contiene el texto: "El destino seleccionado no tiene cobertura de envío"

### ❌ Caso 8: Método de pago no habilitado

- **Precondición:** El método está inactivo.
- **Acción:** Ejecutar el `PUT` de método de pago.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El método de pago seleccionado no está habilitado"

### ❌ Caso 9: Cupón inválido o vencido

- **Precondición:** El cupón no existe, está vencido o no cumple el monto mínimo.
- **Acción:** Ejecutar el `POST` de cupón.
- **Resultado esperado:**
  - Código HTTP `422 Unprocessable Entity`
  - Campo `mensaje` contiene el texto: "El cupón no es válido"
  - No se modifica el total

### ❌ Caso 10: Confirmar con stock insuficiente (RN-11)

- **Precondición:** Un ítem tiene más cantidad que el stock disponible.
- **Acción:** Ejecutar `POST /api/v1/pedidos`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - No se crea el pedido
  - La respuesta lista los ítems sin stock

### ❌ Caso 11: Confirmar sin los datos del checkout completos

- **Precondición:** Falta la dirección, el método de pago o el carrito está vacío.
- **Acción:** Ejecutar `POST /api/v1/pedidos`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` indica el dato faltante: "Debe seleccionar la dirección de entrega antes de confirmar"

### ❌ Caso 12: Falla de un módulo o de la base de datos

- **Precondición:** Catálogo, Envíos, Promociones o la base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - No se crea un pedido incompleto
  - Campo `mensaje` contiene el texto: "No fue posible completar el checkout en este momento"

## ✅ Definición de Hecho

# Historia: Confirmar pedido (checkout)

## 📦 Alcance Funcional

- [ ] Los cuatro endpoints funcionan según lo definido.
- [ ] Se aplican las reglas RN-11 y RN-13.
- [ ] La confirmación es idempotente y no deja pedidos incompletos ante una falla.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias del cálculo de totales y de las validaciones previas a la confirmación.
- [ ] Se cubrieron los casos de error, con un simulador del módulo Notificaciones.
- [ ] Las pruebas funcionales de los 12 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error
- [ ] Se documenta la secuencia de llamadas a otros módulos durante la confirmación.

## 🔐 Manejo de Errores

- [ ] Se devuelve `400`, `403`, `409` y `422` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos o a otro módulo.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
