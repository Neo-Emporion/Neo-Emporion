# [HU-20] Actualizar y consultar el estado del pedido

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-05 Pedidos / SUB-15 Gestión de Estados |
| **Funcionalidades que cubre** | FUN-71 Actualizar estado del pedido · FUN-72 Consultar estado del pedido · FUN-73 Consultar historial de estados |
| **Reglas de negocio asociadas** | RN-15: un pedido no puede pasar a "entregado" sin haber pasado antes por "enviado" · RN-12: un pedido no puede cancelarse si ya fue despachado (límite de la máquina de estados) |
| **APIs** | API-G49, API-G50 (agregadas en el Parcial 2) · API-I10 y API-I11 Actualizar Estado de Pedido, por confirmación de pago y por actualización de envío (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 20 |
| **Depende de** | HU-19 |
| **Actor** | Sistema (módulos Pagos y Envíos), vendedor (actualiza) y comprador (consulta) |

## 📖 Historia de Usuario

**Dado** que existe un pedido confirmado,
**Para** reflejar su avance real desde el pago hasta la entrega,
**Que** necesito que el sistema actualice el estado del pedido cuando Pagos o Envíos informan un cambio, y que el comprador pueda consultar el estado actual y su línea de tiempo, de modo que siempre sepa en qué etapa está su compra.

## 🔁 Flujo Esperado

**Actualizar estado (API interna)**
- El módulo Pagos (al confirmar el pago), el módulo Envíos (al cambiar el estado del envío) o el vendedor (al preparar el pedido) informan el nuevo estado.
- El sistema consume `PATCH /api/v1/pedidos/{id}/estado`.
- El backend valida que la transición esté permitida, registra el cambio en el historial y notifica al comprador (API-I05).

**Consultar estado**
- El comprador consulta la etapa actual con `GET /api/v1/pedidos/{id}/estado`.

**Consultar historial**
- El usuario consulta la línea de tiempo con `GET /api/v1/pedidos/{id}/historial-estados`.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se define la máquina de estados: `PENDIENTE_PAGO` → `PAGADO` → `EN_PREPARACION` → `ENVIADO` → `ENTREGADO`; y `CANCELADO` desde `PENDIENTE_PAGO`, `PAGADO` o `EN_PREPARACION`.
- [ ] El `PATCH` recibe `estado_nuevo` y `origen` (`PAGOS`, `ENVIOS` o `VENDEDOR`).
- [ ] Solo se aceptan transiciones válidas; no se puede pasar a `ENTREGADO` sin haber estado `ENVIADO` (RN-15) ni salir de `CANCELADO` o `ENTREGADO`.
- [ ] Cada cambio queda registrado en el historial con estado anterior, estado nuevo, origen y fecha.
- [ ] Al cambiar de estado se solicita una notificación al comprador (API-I05).
- [ ] El endpoint de estado retorna la etapa actual y la fecha del último cambio.
- [ ] El endpoint de historial retorna todos los cambios en orden cronológico.
- [ ] El comprador solo consulta sus pedidos; el vendedor consulta los pedidos de sus sub-órdenes.
- [ ] El `PATCH` solo puede ser invocado por los módulos internos o por el vendedor autorizado.

### 2. 📆 Estructura de la información

- [ ] Actualización exitosa:

```json
{
  "mensaje": "Estado del pedido actualizado",
  "data": { "pedido_id": 7001, "estado_anterior": "PENDIENTE_PAGO", "estado_nuevo": "PAGADO" },
  "success": true
}
```

- [ ] Consulta de estado:

```json
{
  "mensaje": "Consulta de estado exitosa",
  "data": { "pedido_id": 7001, "estado": "ENVIADO", "fecha_actualizacion": "2026-10-26T14:30:00Z" },
  "success": true
}
```

- [ ] Historial:

```json
{
  "mensaje": "Consulta de historial exitosa",
  "data": [
    { "estado": "PENDIENTE_PAGO", "origen": "PEDIDOS", "fecha": "2026-10-25T15:00:00Z" },
    { "estado": "PAGADO", "origen": "PAGOS", "fecha": "2026-10-25T15:01:10Z" }
  ],
  "success": true
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Estado del pedido

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Actualizar estado (por confirmación de pago) | API-I10 | `PATCH` | `/api/v1/pedidos/{id}/estado` | Inventario inicial (API interna) |
| Actualizar estado (por actualización de envío) | API-I11 | `PATCH` | `/api/v1/pedidos/{id}/estado` | Inventario inicial (API interna) |
| Consultar estado del pedido | API-G49 | `GET` | `/api/v1/pedidos/{id}/estado` | Agregada en el Parcial 2 |
| Consultar historial de estados | API-G50 | `GET` | `/api/v1/pedidos/{id}/historial-estados` | Agregada en el Parcial 2 |
| (Consumida) Enviar notificación | API-I05 | `POST` | `/api/v1/notificaciones/enviar` | Inventario inicial (API interna) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Actualizar | `id` | ruta | entero | Sí | Identificador del pedido |
| Actualizar | `estado_nuevo` | body | texto | Sí | Estado al que pasa el pedido |
| Actualizar | `origen` | body | texto | Sí | `PAGOS`, `ENVIOS` o `VENDEDOR` |
| Consultar estado / historial | `id` | ruta | entero | Sí | Identificador del pedido |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Actualizar | `200 OK` | Estado anterior y nuevo |
| Consultar estado | `200 OK` | Estado actual y fecha |
| Consultar historial | `200 OK` | Arreglo de cambios en orden cronológico |

### 📤 Ejemplo de comunicación – Petición de actualización desde Pagos

```json
{ "estado_nuevo": "PAGADO", "origen": "PAGOS" }
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Actualizar el estado tras la confirmación del pago

- **Precondición:** El pedido está `PENDIENTE_PAGO`.
- **Acción:** Pagos ejecuta `PATCH /api/v1/pedidos/7001/estado` con `estado_nuevo = PAGADO` y `origen = PAGOS`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El cambio queda en el historial
  - Se solicita la notificación al comprador

### ✅ Caso 2: Actualizar el estado por el envío

- **Precondición:** El pedido está `EN_PREPARACION`.
- **Acción:** Envíos ejecuta el `PATCH` con `estado_nuevo = ENVIADO` y `origen = ENVIOS`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `estado_nuevo` = `ENVIADO`

### ✅ Caso 3: Consultar el estado actual

- **Precondición:** El pedido pertenece al comprador.
- **Acción:** Ejecutar `GET /api/v1/pedidos/7001/estado`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Se retorna el estado y la fecha del último cambio

### ✅ Caso 4: Consultar el historial

- **Precondición:** El pedido tiene varios cambios de estado.
- **Acción:** Ejecutar `GET /api/v1/pedidos/7001/historial-estados`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Los cambios aparecen en orden cronológico

### ❌ Caso 5: Entregar sin haber enviado (RN-15)

- **Precondición:** El pedido está `PAGADO`.
- **Acción:** Ejecutar el `PATCH` con `estado_nuevo = ENTREGADO`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - El estado no cambia
  - Campo `mensaje` contiene el texto: "La transición de estado no está permitida"

### ❌ Caso 6: Cambiar el estado de un pedido cerrado

- **Precondición:** El pedido está `CANCELADO` o `ENTREGADO`.
- **Acción:** Ejecutar el `PATCH`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "El pedido ya no admite cambios de estado"

### ❌ Caso 7: Estado u origen no válido

- **Precondición:** Ninguna.
- **Acción:** Ejecutar el `PATCH` con `estado_nuevo = "XYZ"`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El estado indicado no es válido"

### ❌ Caso 8: Pedido inexistente

- **Precondición:** No existe `id = 99999`.
- **Acción:** Ejecutar cualquiera de los endpoints.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "El pedido no existe"

### ❌ Caso 9: Pedido de otro comprador

- **Precondición:** El pedido pertenece a otro comprador.
- **Acción:** Ejecutar `GET .../estado` o `GET .../historial-estados`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`

### ❌ Caso 10: Actualización por un actor no autorizado

- **Precondición:** Un comprador intenta ejecutar el `PATCH`.
- **Acción:** Ejecutar el `PATCH`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - El estado no cambia

### ❌ Caso 11: Falla en la notificación

- **Precondición:** La API-I05 no responde.
- **Acción:** Ejecutar un `PATCH` válido.
- **Resultado esperado:**
  - El estado se actualiza igualmente y la notificación queda pendiente de reenvío
  - La respuesta indica que la notificación no pudo enviarse

### ❌ Caso 12: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud del estado del pedido"

## ✅ Definición de Hecho

# Historia: Actualizar y consultar el estado del pedido

## 📦 Alcance Funcional

- [ ] Los endpoints de actualización, consulta y historial funcionan según lo definido.
- [ ] Solo se permiten las transiciones de la máquina de estados (RN-15) y cada cambio queda en el historial.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de la máquina de estados (transiciones válidas e inválidas).
- [ ] Se cubrieron los casos de error, incluida la falla de notificaciones.
- [ ] Las pruebas funcionales de los 12 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error
- [ ] Se documenta el diagrama de estados del pedido.

## 🔐 Manejo de Errores

- [ ] Se devuelve `400`, `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
