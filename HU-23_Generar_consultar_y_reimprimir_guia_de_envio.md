# [HU-23] Generar, consultar y reimprimir guía de envío

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-07 Envíos y Logística / SUB-20 Gestión de Guías |
| **Funcionalidades que cubre** | FUN-96 Generar guía de envío · FUN-97 Consultar guía de envío · FUN-99 Reimprimir etiqueta de envío |
| **Reglas de negocio asociadas** | RN-21: no se puede generar una guía de envío para un pedido sin el pago aprobado · RN-22: una guía anulada no puede reutilizarse para otro despacho |
| **APIs** | API-G57, API-G58 (agregadas en el Parcial 2) · API-I04 Generar Guía de Envío y API externa API-E03 Transportadora (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 23 |
| **Depende de** | HU-17, HU-22 |
| **Actor** | Sistema (módulo Pedidos), vendedor y comprador |

## 📖 Historia de Usuario

**Dado** que un pedido tiene el pago aprobado,
**Para** despachar los productos con la transportadora,
**Que** necesito que el sistema genere la guía de envío con su número y etiqueta, y que el vendedor pueda consultarla y volver a imprimir la etiqueta, de modo que el paquete salga con la documentación correcta.

## 🔁 Flujo Esperado

**Generar guía (API interna)**
- El módulo Pedidos envía el id del pedido y la dirección de destino.
- El sistema consume `POST /api/v1/envios/guias` (API-I04).
- El backend valida que el pago esté aprobado (RN-21) y solicita la guía a la API externa de la transportadora (API-E03).
- La transportadora responde con el número de guía y la etiqueta, y el backend los asocia al pedido.

**Consultar guía**
- El usuario consulta los datos de la guía con `GET /api/v1/envios/guias/{id}`.

**Reimprimir etiqueta**
- El vendedor solicita de nuevo la etiqueta con `GET /api/v1/envios/guias/{id}/etiqueta`.
- El backend recupera los datos de la guía y genera el archivo nuevamente.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] La API-I04 recibe `pedido_id` y `direccion_destino` (ciudad y dirección); en pedidos divididos recibe también `sub_orden_id` (parámetro adicional a los definidos en el inventario inicial, necesario para generar una guía por sub-orden).
- [ ] Solo se genera la guía si el pago del pedido está `APROBADO` (RN-21).
- [ ] Solo se genera una guía activa por pedido o sub-orden.
- [ ] Se solicita la guía a la transportadora y se guarda `numero_guia`, `transportadora`, `etiqueta` y fecha.
- [ ] El estado inicial de la guía es `GENERADA`.
- [ ] Un `numero_guia` anulado no puede asignarse a otro despacho (RN-22).
- [ ] Se expone un endpoint `GET` para consultar la guía (número, transportadora, estado y etiqueta).
- [ ] Se expone un endpoint `GET` que entrega la etiqueta en PDF para reimprimirla.
- [ ] El vendedor consulta y reimprime solo las guías de sus sub-órdenes; el comprador consulta solo las de sus pedidos.

### 2. 📆 Estructura de la información

- [ ] Guía generada:

```json
{
  "mensaje": "Guía de envío generada exitosamente",
  "data": {
    "guia_id": 3301,
    "pedido_id": 7001,
    "numero_guia": "SRV-20261025-8841",
    "transportadora": "Servientrega",
    "estado": "GENERADA",
    "etiqueta_url": "/api/v1/envios/guias/3301/etiqueta"
  },
  "success": true
}
```

- [ ] Consulta de guía:

```json
{
  "mensaje": "Consulta de guía exitosa",
  "data": { "guia_id": 3301, "numero_guia": "SRV-20261025-8841", "transportadora": "Servientrega", "estado": "GENERADA" },
  "success": true
}
```

- [ ] Pago no aprobado:

```json
{
  "mensaje": "No es posible generar la guía porque el pago del pedido no está aprobado",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Guías de envío

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Generar guía de envío | API-I04 (Generar Guía de Envío) | `POST` | `/api/v1/envios/guias` | Inventario inicial (API interna) |
| Consultar guía de envío | API-G57 | `GET` | `/api/v1/envios/guias/{id}` | Agregada en el Parcial 2 |
| Reimprimir etiqueta de envío | API-G58 | `GET` | `/api/v1/envios/guias/{id}/etiqueta` | Agregada en el Parcial 2 |
| (Externa) Solicitud de guía a la transportadora | API-E03 | Pendiente de definir | Definido por el proveedor | Inventario inicial (API externa) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Generar | `pedido_id` | body | entero | Sí | Pedido a despachar |
| Generar | `sub_orden_id` | body | entero | Condicional | Obligatorio en pedidos divididos |
| Generar | `direccion_destino` | body | objeto | Sí | Ciudad y dirección de entrega |
| Consultar / Reimprimir | `id` | ruta | entero | Sí | Identificador de la guía |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Generar | `201 Created` | Guía con número, transportadora, estado y enlace de la etiqueta |
| Consultar | `200 OK` | Datos de la guía |
| Reimprimir | `200 OK` | Archivo PDF de la etiqueta |

### 📤 Ejemplo de comunicación – Petición de la API-I04

```json
{
  "pedido_id": 7001,
  "sub_orden_id": 7001001,
  "direccion_destino": { "ciudad_id": 1203, "direccion": "Calle 45 # 12-30, Apto 502" }
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Generar una guía con pago aprobado

- **Precondición:** El pedido tiene el pago `APROBADO` y la transportadora responde.
- **Acción:** Ejecutar `POST /api/v1/envios/guias` con los datos del pedido.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - La respuesta incluye `numero_guia` y `etiqueta_url`
  - Campo `estado` = `GENERADA`

### ✅ Caso 2: Consultar una guía

- **Precondición:** La guía existe y es del vendedor o del comprador autenticado.
- **Acción:** Ejecutar `GET /api/v1/envios/guias/3301`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Se retornan número, transportadora y estado

### ✅ Caso 3: Reimprimir la etiqueta

- **Precondición:** La guía existe y no está anulada.
- **Acción:** Ejecutar `GET /api/v1/envios/guias/3301/etiqueta`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Se entrega el archivo PDF con la misma información de la guía

### ❌ Caso 4: Generar guía sin pago aprobado (RN-21)

- **Precondición:** El pago del pedido está `PENDIENTE` o `RECHAZADO`.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - No se solicita la guía a la transportadora
  - Campo `mensaje` contiene el texto: "No es posible generar la guía porque el pago del pedido no está aprobado"

### ❌ Caso 5: Guía ya generada para el pedido

- **Precondición:** El pedido o sub-orden ya tiene una guía activa.
- **Acción:** Ejecutar de nuevo el `POST`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "El pedido ya tiene una guía de envío activa"

### ❌ Caso 6: Datos obligatorios faltantes

- **Precondición:** Ninguna.
- **Acción:** Ejecutar el `POST` sin `direccion_destino`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` indica el dato faltante

### ❌ Caso 7: Reimprimir una guía anulada (RN-22)

- **Precondición:** La guía está `ANULADA`.
- **Acción:** Ejecutar `GET .../etiqueta`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "La guía fue anulada y no puede reimprimirse"

### ❌ Caso 8: Guía inexistente o de otro usuario

- **Precondición:** La guía no existe o pertenece a otro vendedor o comprador.
- **Acción:** Ejecutar cualquiera de los `GET`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found` si no existe, o `403 Forbidden` si es ajena

### ❌ Caso 9: La transportadora no responde o rechaza la solicitud

- **Precondición:** La API externa de la transportadora no está disponible o devuelve un error.
- **Acción:** Ejecutar el `POST`.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - No se registra ninguna guía
  - Campo `mensaje` contiene el texto: "No fue posible generar la guía con la transportadora"

### ❌ Caso 10: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud de guías de envío"

## ✅ Definición de Hecho

# Historia: Generar, consultar y reimprimir guía de envío

## 📦 Alcance Funcional

- [ ] La generación, la consulta y la reimpresión funcionan según lo definido.
- [ ] Se aplican las reglas RN-21 y RN-22 y solo existe una guía activa por pedido o sub-orden.
- [ ] La falla de la transportadora no deja guías incompletas.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (pago aprobado, guía única y guía anulada) con un simulador de la transportadora.
- [ ] Se cubrieron los casos de error y de indisponibilidad de la transportadora.
- [ ] Las pruebas funcionales de los 10 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error
- [ ] Se documenta la dependencia del servicio externo de la transportadora.

## 🔐 Manejo de Errores

- [ ] Se devuelve `400`, `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos o a la transportadora.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
