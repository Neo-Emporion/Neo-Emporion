# [HU-17] Cotizar y comparar costos de envío

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-07 Envíos y Logística / SUB-19 Cotización de Envío |
| **Funcionalidades que cubre** | FUN-91 Cotizar costo de envío · FUN-92 Consultar histórico de cotizaciones · FUN-93 Comparar tarifas entre transportadoras |
| **Regla de negocio asociada** | RN-23: el costo de envío no puede ser inferior al mínimo definido por la transportadora |
| **APIs** | API-G55, API-G56 (agregadas en el Parcial 2) · API-I03 Cotizar Envío y API externa API-E03 Transportadora (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 17 |
| **Depende de** | HU-15, HU-16 |
| **Actor** | Comprador (en el checkout) y sistema (módulo Pedidos) |

## 📖 Historia de Usuario

**Dado** que soy un comprador con una dirección de entrega y productos en mi carrito,
**Para** conocer cuánto cuesta y cuánto demora el envío antes de pagar,
**Que** necesito cotizar el envío, comparar las opciones de distintas transportadoras y consultar las cotizaciones anteriores de mi pedido, de modo que pueda elegir con información clara.

## 🔁 Flujo Esperado

**Cotizar costo de envío (API interna)**
- El módulo Pedidos envía la dirección de destino y el peso del pedido al sistema.
- El sistema consume `POST /api/v1/envios/cotizaciones` (API-I03).
- El backend aplica las reglas de HU-16 (peso máximo y zonas excluidas), consulta la API externa de la transportadora y devuelve costo y tiempo estimado.

**Comparar tarifas entre transportadoras**
- El comprador solicita la comparación con `POST /api/v1/envios/cotizaciones/comparar`.
- El backend consulta cada transportadora disponible y retorna las opciones ordenadas por costo.

**Consultar histórico de cotizaciones**
- El comprador consulta las cotizaciones de un pedido con `GET /api/v1/envios/cotizaciones?pedido_id=...`.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] La API-I03 recibe `ciudad_destino_id` (o dirección de destino) y `peso_kg`, y devuelve `costo` y `tiempo_estimado_dias`.
- [ ] Se rechazan pesos mayores al máximo y destinos en zonas excluidas (reglas de HU-16).
- [ ] El costo devuelto no puede ser inferior al mínimo de la transportadora (RN-23).
- [ ] La validación de las zonas de cobertura del vendedor (RN-25) se integra cuando esté disponible la HU-45.
- [ ] El endpoint de comparación retorna una opción por transportadora disponible, ordenadas de menor a mayor costo.
- [ ] Si una transportadora no responde, se omite de la comparación y se informa; la cotización continúa con las demás.
- [ ] Cada cotización se guarda para el histórico (fecha, transportadora, costo, tiempo y `pedido_id` si existe).
- [ ] El endpoint de histórico lista solo las cotizaciones del comprador autenticado.

### 2. 📆 Estructura de la información

- [ ] Cotización exitosa:

```json
{
  "mensaje": "Cotización de envío exitosa",
  "data": {
    "transportadora": "Servientrega",
    "costo": 12000,
    "tiempo_estimado_dias": 3
  },
  "success": true
}
```

- [ ] Comparación exitosa:

```json
{
  "mensaje": "Comparación de tarifas exitosa",
  "data": [
    { "transportadora": "Servientrega", "costo": 12000, "tiempo_estimado_dias": 3 },
    { "transportadora": "Coordinadora", "costo": 13500, "tiempo_estimado_dias": 2 }
  ],
  "success": true
}
```

- [ ] Destino sin cobertura:

```json
{
  "mensaje": "El destino seleccionado no tiene cobertura de envío",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Cotización de envío

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Cotizar costo de envío | API-I03 (Cotizar Envío) | `POST` | `/api/v1/envios/cotizaciones` | Inventario inicial (API interna) |
| Comparar tarifas entre transportadoras | API-G55 | `POST` | `/api/v1/envios/cotizaciones/comparar` | Agregada en el Parcial 2 |
| Consultar histórico de cotizaciones | API-G56 | `GET` | `/api/v1/envios/cotizaciones` | Agregada en el Parcial 2 |
| (Externa) Consulta de tarifas a la transportadora | API-E03 | Pendiente de definir | Definido por el proveedor | Inventario inicial (API externa) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Cotizar / Comparar | `ciudad_destino_id` | body | entero | Sí | Ciudad de destino |
| Cotizar / Comparar | `peso_kg` | body | decimal | Sí | Peso total del pedido |
| Cotizar / Comparar | `pedido_id` | body | entero | No | Pedido al que se asocia la cotización |
| Histórico | `pedido_id` | query | entero | Sí | Pedido a consultar |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Cotizar | `200 OK` | Transportadora, costo y tiempo estimado |
| Comparar | `200 OK` | Opciones por transportadora, de menor a mayor costo |
| Histórico | `200 OK` | Cotizaciones anteriores del pedido |

### 📤 Ejemplo de comunicación – Petición de cotización

```json
{ "ciudad_destino_id": 1203, "peso_kg": 2.5, "pedido_id": 7001 }
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Cotizar un envío válido

- **Precondición:** El destino tiene cobertura y el peso no supera el máximo.
- **Acción:** Ejecutar `POST /api/v1/envios/cotizaciones` con ciudad y peso válidos.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - La respuesta incluye `costo` y `tiempo_estimado_dias`

### ✅ Caso 2: Comparar tarifas

- **Precondición:** Hay dos transportadoras disponibles.
- **Acción:** Ejecutar `POST /api/v1/envios/cotizaciones/comparar`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Se retorna una opción por transportadora, de menor a mayor costo

### ✅ Caso 3: Consultar el histórico de un pedido

- **Precondición:** El pedido tiene cotizaciones guardadas.
- **Acción:** Ejecutar `GET /api/v1/envios/cotizaciones?pedido_id=7001`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Se listan las cotizaciones con fecha, transportadora, costo y tiempo

### ✅ Caso 4: Una transportadora no responde durante la comparación

- **Precondición:** Una de dos transportadoras no está disponible.
- **Acción:** Ejecutar la comparación.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Se retorna la opción de la transportadora disponible y se informa que la otra no respondió

### ❌ Caso 5: Peso superior al máximo

- **Precondición:** `peso_maximo_kg = 30`.
- **Acción:** Cotizar con `peso_kg = 45`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El peso del pedido supera el máximo permitido para envío"

### ❌ Caso 6: Destino en zona excluida

- **Precondición:** La ciudad está entre las zonas excluidas.
- **Acción:** Cotizar hacia esa ciudad.
- **Resultado esperado:**
  - Código HTTP `422 Unprocessable Entity`
  - Campo `mensaje` contiene el texto: "El destino seleccionado no tiene cobertura de envío"

### ❌ Caso 7: Datos obligatorios faltantes o inválidos

- **Precondición:** Ninguna.
- **Acción:** Cotizar sin `peso_kg` o con peso menor o igual a cero.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` indica el dato inválido

### ❌ Caso 8: Ninguna transportadora disponible

- **Precondición:** La API externa de todas las transportadoras no responde.
- **Acción:** Ejecutar la cotización o la comparación.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible cotizar el envío en este momento"

### ❌ Caso 9: Histórico de un pedido ajeno o inexistente

- **Precondición:** El pedido pertenece a otro comprador o no existe.
- **Acción:** Ejecutar `GET /api/v1/envios/cotizaciones?pedido_id=...`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden` si es ajeno, o `404 Not Found` si no existe

### ❌ Caso 10: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud de cotización"

## ✅ Definición de Hecho

# Historia: Cotizar y comparar costos de envío

## 📦 Alcance Funcional

- [ ] La cotización, la comparación y el histórico funcionan según lo definido.
- [ ] Se aplican las reglas de peso máximo, zonas excluidas y RN-23.
- [ ] La comparación tolera la falla de una transportadora.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las reglas de cotización y de la ordenación de opciones (con un simulador de la API de la transportadora).
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

- [ ] Se devuelve `400`, `403`, `404` y `422` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos o a la transportadora.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
