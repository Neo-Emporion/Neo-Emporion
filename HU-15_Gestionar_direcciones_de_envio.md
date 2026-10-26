# [HU-15] Gestionar direcciones de envío

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-02 Usuarios y Compradores / SUB-06 Direcciones de Envío |
| **Funcionalidades que cubre** | FUN-26 Registrar dirección de envío · FUN-27 Editar dirección de envío · FUN-28 Consultar/listar direcciones · FUN-29 Eliminar dirección de envío |
| **Reglas de negocio asociadas** | RN-53: un comprador no puede eliminar una dirección asociada a un pedido en curso · RN-54: debe existir siempre una única dirección marcada como predeterminada por comprador |
| **APIs** | API-G16, API-G17, API-G18, API-G19 (agregadas en el Parcial 2) · consume API-I09 Consultar Catálogo Geográfico (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 15 |
| **Depende de** | HU-04, HU-07 |
| **Actor** | Comprador |

## 📖 Historia de Usuario

**Dado** que soy un comprador con sesión iniciada,
**Para** recibir mis pedidos en los lugares que yo elija,
**Que** necesito registrar, editar, consultar y eliminar mis direcciones de envío, de modo que pueda seleccionarlas rápidamente en el checkout y los envíos lleguen al destino correcto.

## 🔁 Flujo Esperado

**Registrar dirección**
- El comprador ingresa alias, nombre de quien recibe, teléfono de contacto, ciudad, dirección y referencias.
- El sistema consume `POST /api/v1/usuarios/direcciones`.
- El backend valida la ubicación con la API-I09 y guarda la dirección. Si es la primera del comprador, queda como predeterminada (RN-54).

**Editar dirección**
- El comprador modifica una dirección con `PUT /api/v1/usuarios/direcciones/{id}`.

**Consultar / listar direcciones**
- El comprador consulta sus direcciones guardadas con `GET /api/v1/usuarios/direcciones`.

**Eliminar dirección**
- El comprador elimina una dirección en desuso con `DELETE /api/v1/usuarios/direcciones/{id}`.
- El backend valida que no esté asociada a un pedido en curso (RN-53).

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` con `alias`, `nombre_receptor`, `telefono`, `ciudad_id`, `direccion` y `referencia` (opcional).
- [ ] La ciudad se valida consultando la API-I09: debe existir, estar activa y publicada.
- [ ] La primera dirección de un comprador queda marcada como predeterminada (RN-54).
- [ ] Se expone un endpoint `PUT` para editar los datos de una dirección propia.
- [ ] Se expone un endpoint `GET` que lista solo las direcciones del comprador autenticado.
- [ ] Se expone un endpoint `DELETE` que no permite eliminar direcciones asociadas a pedidos en curso (RN-53).
- [ ] Si se elimina la dirección predeterminada y quedan otras, la más reciente pasa a ser la predeterminada (RN-54).
- [ ] Un comprador solo puede ver y modificar sus propias direcciones.

### 2. 📆 Estructura de la información

- [ ] Registro exitoso:

```json
{
  "mensaje": "Dirección registrada exitosamente",
  "data": {
    "id": 4401,
    "alias": "Casa",
    "nombre_receptor": "Laura Gómez",
    "telefono": "3001234567",
    "ciudad_id": 1203,
    "direccion": "Calle 45 # 12-30, Apto 502",
    "predeterminada": true
  },
  "success": true
}
```

- [ ] Listado exitoso:

```json
{
  "mensaje": "Consulta de direcciones exitosa",
  "data": [
    { "id": 4401, "alias": "Casa", "ciudad_id": 1203, "direccion": "Calle 45 # 12-30, Apto 502", "predeterminada": true }
  ],
  "success": true
}
```

- [ ] Eliminación no permitida (RN-53):

```json
{
  "mensaje": "No es posible eliminar la dirección porque está asociada a un pedido en curso",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Direcciones de envío

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Registrar dirección | API-G16 | `POST` | `/api/v1/usuarios/direcciones` | Agregada en el Parcial 2 |
| Editar dirección | API-G17 | `PUT` | `/api/v1/usuarios/direcciones/{id}` | Agregada en el Parcial 2 |
| Consultar direcciones | API-G18 | `GET` | `/api/v1/usuarios/direcciones` | Agregada en el Parcial 2 |
| Eliminar dirección | API-G19 | `DELETE` | `/api/v1/usuarios/direcciones/{id}` | Agregada en el Parcial 2 |
| (Consumida) Consultar catálogo geográfico | API-I09 | `GET` | `/api/v1/parametrizacion/ubicaciones` | Inventario inicial (API interna) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Registrar / Editar | `alias` | body | texto | Sí | Nombre corto de la dirección (ej. "Casa") |
| Registrar / Editar | `nombre_receptor` | body | texto | Sí | Quien recibe el pedido |
| Registrar / Editar | `telefono` | body | texto | Sí | Teléfono de contacto |
| Registrar / Editar | `ciudad_id` | body | entero | Sí | Ciudad publicada del catálogo geográfico |
| Registrar / Editar | `direccion` | body | texto | Sí | Dirección completa |
| Registrar / Editar | `referencia` | body | texto | No | Indicaciones adicionales |
| Editar / Eliminar | `id` | ruta | entero | Sí | Identificador de la dirección |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Registrar | `201 Created` | Dirección creada |
| Editar | `200 OK` | Dirección actualizada |
| Consultar | `200 OK` | Arreglo de direcciones del comprador |
| Eliminar | `200 OK` | Confirmación con el `id` eliminado |

### 📤 Ejemplo de comunicación – Eliminar dirección

Petición: `DELETE /api/v1/usuarios/direcciones/4401`

```json
{ "mensaje": "Dirección eliminada exitosamente", "data": { "id": 4401 }, "success": true }
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Registrar la primera dirección

- **Precondición:** El comprador no tiene direcciones y la ciudad está publicada.
- **Acción:** Ejecutar `POST /api/v1/usuarios/direcciones` con datos válidos.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `predeterminada` = `true`

### ✅ Caso 2: Editar una dirección propia

- **Precondición:** La dirección existe y es del comprador.
- **Acción:** Ejecutar `PUT /api/v1/usuarios/direcciones/4401` con un teléfono nuevo.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El dato se actualiza

### ✅ Caso 3: Listar mis direcciones

- **Precondición:** El comprador tiene varias direcciones.
- **Acción:** Ejecutar `GET /api/v1/usuarios/direcciones`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Solo se listan las direcciones del comprador autenticado

### ✅ Caso 4: Eliminar una dirección sin pedidos en curso

- **Precondición:** La dirección no está asociada a pedidos en curso.
- **Acción:** Ejecutar `DELETE /api/v1/usuarios/direcciones/4401`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Si era la predeterminada y existen otras, otra queda como predeterminada

### ❌ Caso 5: Ciudad inválida

- **Precondición:** La ciudad no existe o no está publicada.
- **Acción:** Ejecutar el `POST` con ese `ciudad_id`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "La ciudad indicada no es válida"

### ❌ Caso 6: Datos obligatorios faltantes

- **Precondición:** Ninguna.
- **Acción:** Ejecutar el `POST` sin `direccion`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El campo direccion es obligatorio"

### ❌ Caso 7: Eliminar una dirección asociada a un pedido en curso (RN-53)

- **Precondición:** La dirección está asociada a un pedido en curso.
- **Acción:** Ejecutar el `DELETE`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - La dirección se conserva
  - Campo `mensaje` contiene el texto: "No es posible eliminar la dirección porque está asociada a un pedido en curso"

### ❌ Caso 8: Dirección de otro comprador

- **Precondición:** La dirección pertenece a otro comprador.
- **Acción:** Ejecutar `PUT` o `DELETE`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - Campo `mensaje` contiene el texto: "No tiene permisos sobre esta dirección"

### ❌ Caso 9: Dirección inexistente

- **Precondición:** No existe `id = 99999`.
- **Acción:** Ejecutar `PUT` o `DELETE`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "La dirección no existe"

### ❌ Caso 10: Sin sesión iniciada

- **Precondición:** La petición no incluye un token válido.
- **Acción:** Ejecutar cualquiera de los endpoints.
- **Resultado esperado:**
  - Código HTTP `401 Unauthorized`

### ❌ Caso 11: Falla de base de datos o de Parametrización

- **Precondición:** La base de datos o la API-I09 no está disponible.
- **Acción:** Ejecutar el `POST` o el `PUT`.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud de direcciones"

## ✅ Definición de Hecho

# Historia: Gestionar direcciones de envío

## 📦 Alcance Funcional

- [ ] Los cuatro endpoints funcionan según lo definido.
- [ ] Se aplican las reglas RN-53 y RN-54 y la validación de ubicación con la API-I09.
- [ ] Cada comprador solo accede a sus propias direcciones.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (ubicación, predeterminada y pedidos en curso).
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

- [ ] Se devuelve `400`, `401`, `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos o a Parametrización.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
