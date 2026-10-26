# [HU-22] Procesar el pago del pedido

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-06 Pagos y Facturación / SUB-16 Procesamiento de Pago |
| **Funcionalidades que cubre** | FUN-76 Procesar pago del pedido · FUN-78 Reintentar pago fallido |
| **Regla de negocio asociada** | RN-16: un pago no puede procesarse por un monto diferente al total confirmado del pedido |
| **APIs** | API-G52 (agregada en el Parcial 2) · API-I02 Procesar Pago del Pedido, API-I10 Actualizar Estado de Pedido (por confirmación de pago) y API externa API-E02 Pasarela de Pagos (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 22 |
| **Depende de** | HU-19 |
| **Actor** | Sistema (módulo Pedidos) y comprador (reintento) |

## 📖 Historia de Usuario

**Dado** que existe un pedido confirmado pendiente de pago,
**Para** cobrar al comprador de forma segura,
**Que** necesito que el sistema envíe el cobro a la pasarela de pagos, registre el resultado y permita reintentar si el pago falla, de modo que el pedido avance solo cuando el pago esté aprobado.

## 🔁 Flujo Esperado

**Procesar pago (API interna)**
- El módulo Pedidos envía el id del pedido, el monto y el método de pago.
- El sistema consume `POST /api/v1/pagos/procesar` (API-I02).
- El backend valida que el monto coincida con el total del pedido (RN-16), envía la solicitud a la pasarela externa (API-E02) y recibe el resultado.
- El backend registra la transacción con su estado (`APROBADO`, `RECHAZADO` o `PENDIENTE`).
- Si el pago es aprobado, el backend informa al módulo Pedidos para que actualice el estado a `PAGADO` (API-I10).

**Reintentar pago fallido**
- El comprador solicita reintentar con `POST /api/v1/pagos/{id}/reintentar`.
- El backend valida que el pedido siga vigente y reenvía la solicitud a la pasarela.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] La API-I02 recibe `pedido_id`, `monto`, `metodo_pago` y, cuando aplica, `token_pago` generado por la pasarela.
- [ ] Se valida que `monto` sea igual al total a pagar del pedido (RN-16).
- [ ] Solo se procesa el pago de pedidos en estado `PENDIENTE_PAGO` y sin un pago aprobado previo.
- [ ] Se envía la solicitud a la pasarela y se registra la transacción con `id_transaccion`, estado y fecha.
- [ ] Un pago `APROBADO` dispara la actualización del pedido a `PAGADO`.
- [ ] Un pago `RECHAZADO` deja el pedido en `PENDIENTE_PAGO` y habilita el reintento.
- [ ] Si la pasarela responde de forma diferida, la transacción queda `PENDIENTE` y se consulta su resultado (definición del mecanismo de notificación de la pasarela pendiente).
- [ ] El endpoint de reintento solo se permite si el último pago fue `RECHAZADO`, el pedido sigue en `PENDIENTE_PAGO` y no se superan 3 intentos.
- [ ] El sistema no almacena datos de tarjeta; solo el token y el resultado de la transacción.
- [ ] El comprador solo puede reintentar el pago de sus propios pedidos.

### 2. 📆 Estructura de la información

- [ ] Pago aprobado:

```json
{
  "mensaje": "Pago procesado exitosamente",
  "data": {
    "pago_id": 5501,
    "pedido_id": 7001,
    "estado": "APROBADO",
    "id_transaccion": "TX-90817263",
    "monto": 93000
  },
  "success": true
}
```

- [ ] Pago rechazado:

```json
{
  "mensaje": "El pago fue rechazado por la entidad",
  "data": { "pago_id": 5501, "pedido_id": 7001, "estado": "RECHAZADO", "intentos": 1 },
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Pago

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Procesar pago del pedido | API-I02 (Procesar Pago del Pedido) | `POST` | `/api/v1/pagos/procesar` | Inventario inicial (API interna) |
| Reintentar pago fallido | API-G52 | `POST` | `/api/v1/pagos/{id}/reintentar` | Agregada en el Parcial 2 |
| (Externa) Cobro en la pasarela | API-E02 | Pendiente de definir | Definido por el proveedor (Wompi/PayU) | Inventario inicial (API externa) |
| (Relacionada) Actualizar estado de pedido por pago | API-I10 | `PATCH` | `/api/v1/pedidos/{id}/estado` | Inventario inicial (API interna) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Procesar | `pedido_id` | body | entero | Sí | Pedido a cobrar |
| Procesar | `monto` | body | decimal | Sí | Debe igualar el total a pagar |
| Procesar | `metodo_pago` | body | texto | Sí | Método de pago seleccionado |
| Procesar | `token_pago` | body | texto | Condicional | Token del medio de pago de la pasarela |
| Reintentar | `id` | ruta | entero | Sí | Identificador del pago fallido |
| Reintentar | `token_pago` | body | texto | Condicional | Nuevo token si el anterior expiró |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Procesar | `200 OK` | Estado de la transacción e `id_transaccion` |
| Reintentar | `200 OK` | Nuevo resultado de la transacción e intentos realizados |

### 📤 Ejemplo de comunicación – Petición de la API-I02

```json
{ "pedido_id": 7001, "monto": 93000, "metodo_pago": "TC", "token_pago": "tok_8f2a..." }
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Pago aprobado

- **Precondición:** El pedido está `PENDIENTE_PAGO` y la pasarela aprueba el cobro.
- **Acción:** Ejecutar `POST /api/v1/pagos/procesar` con el monto correcto.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `estado` = `APROBADO`
  - El pedido pasa a `PAGADO`

### ✅ Caso 2: Reintentar un pago rechazado

- **Precondición:** El último pago del pedido fue `RECHAZADO` y llevan menos de 3 intentos.
- **Acción:** Ejecutar `POST /api/v1/pagos/5501/reintentar`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Se registra un nuevo intento y, si es aprobado, el pedido pasa a `PAGADO`

### ❌ Caso 3: Pago rechazado por la entidad

- **Precondición:** La pasarela rechaza el cobro.
- **Acción:** Ejecutar el `POST` de procesar pago.
- **Resultado esperado:**
  - Campo `estado` = `RECHAZADO`
  - El pedido permanece en `PENDIENTE_PAGO`

### ❌ Caso 4: Monto distinto al total (RN-16)

- **Precondición:** El total a pagar es 93000.
- **Acción:** Ejecutar el `POST` con `monto = 80000`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - No se envía nada a la pasarela
  - Campo `mensaje` contiene el texto: "El monto no coincide con el total del pedido"

### ❌ Caso 5: Pedido que no admite pago

- **Precondición:** El pedido está `PAGADO` o `CANCELADO`.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "El pedido no admite un nuevo pago"

### ❌ Caso 6: Reintentar un pago que no fue rechazado

- **Precondición:** El pago está `APROBADO` o `PENDIENTE`.
- **Acción:** Ejecutar el endpoint de reintento.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "Solo se puede reintentar un pago rechazado"

### ❌ Caso 7: Superar el máximo de reintentos

- **Precondición:** El pedido ya tiene 3 intentos rechazados.
- **Acción:** Ejecutar el endpoint de reintento.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "Se alcanzó el máximo de intentos de pago"

### ❌ Caso 8: Reintentar el pago de otro comprador o inexistente

- **Precondición:** El pago pertenece a otro comprador o no existe.
- **Acción:** Ejecutar el endpoint de reintento.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden` si es ajeno, o `404 Not Found` si no existe

### ❌ Caso 9: La pasarela no responde

- **Precondición:** La API externa de la pasarela no está disponible.
- **Acción:** Ejecutar el `POST` de procesar pago.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - El pedido permanece en `PENDIENTE_PAGO`
  - Campo `mensaje` contiene el texto: "No fue posible comunicarse con la pasarela de pagos"

### ❌ Caso 10: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible registrar el pago"

## ✅ Definición de Hecho

# Historia: Procesar el pago del pedido

## 📦 Alcance Funcional

- [ ] El cobro y el reintento funcionan según lo definido.
- [ ] Se aplica RN-16 y el pedido solo avanza con pago aprobado.
- [ ] No se almacenan datos de tarjeta.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de la validación del monto, de los estados del pago y del límite de reintentos (con un simulador de la pasarela).
- [ ] Se cubrieron los casos de error y de indisponibilidad de la pasarela.
- [ ] Las pruebas funcionales de los 10 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error
- [ ] Se documenta la dependencia de la pasarela de pagos y su comportamiento ante fallas.

## 🔐 Manejo de Errores

- [ ] Se devuelve `400`, `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos o a la pasarela.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
