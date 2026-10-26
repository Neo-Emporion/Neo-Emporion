# [HU-09] Cargar y validar documentación legal contra el RUES

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-04 Vendedores y Verificación / SUB-11 Verificación Legal |
| **Funcionalidades que cubre** | FUN-51 Cargar documentación legal · FUN-52 Validar documentación contra el RUES |
| **Regla de negocio asociada** | RN-07: no se puede aprobar un vendedor si su certificado de Cámara de Comercio está vencido |
| **APIs** | API-G37, API-G38 (agregadas en el Parcial 2) · API externa API-E01 RUES (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 9 |
| **Depende de** | HU-08 |
| **Actor** | Vendedor (carga) y sistema (validación) |

## 📖 Historia de Usuario

**Dado** que soy un vendedor con una solicitud de registro creada,
**Para** demostrar que mi empresa está legalmente constituida y vigente,
**Que** necesito cargar mi certificado de Cámara de Comercio y mi NIT y que el sistema los valide contra el RUES, de modo que el administrador pueda decidir sobre mi aprobación con información verificada.

## 🔁 Flujo Esperado

**Cargar documentación legal**
- El vendedor adjunta el certificado de Cámara de Comercio y el NIT (PDF).
- El sistema consume `POST /api/v1/vendedores/{id}/documentos`.
- El backend valida el tipo y tamaño de los archivos, los almacena y cambia la solicitud a `EN_VERIFICACION`.

**Validar documentación contra el RUES**
- El sistema consume `POST /api/v1/vendedores/{id}/documentos/validar`.
- El backend consulta la API externa del RUES enviando el NIT del vendedor.
- El RUES responde con el estado del registro mercantil (vigente o no vigente), la razón social y la fecha de vigencia.
- El backend compara los datos con los de la solicitud y registra el resultado de la validación.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` multipart que recibe `certificado_camara_comercio` y `documento_nit` (solo PDF, máximo 5 MB cada uno).
- [ ] Solo se permite cargar documentos si la solicitud está en `REGISTRADO` o `DOCUMENTACION_PENDIENTE`.
- [ ] Se expone un endpoint `POST` de validación que consulta el RUES con el NIT del vendedor.
- [ ] La validación es exitosa solo si el RUES reporta registro `VIGENTE` y la razón social coincide con la registrada.
- [ ] Si el certificado está vencido, el resultado queda como `NO_VIGENTE` y no podrá aprobarse el vendedor (RN-07).
- [ ] Si el RUES no responde, la solicitud permanece en `EN_VERIFICACION` y el resultado queda `PENDIENTE`; no se rechaza automáticamente.
- [ ] Se conserva el resultado de cada validación (fecha, resultado y datos devueltos por el RUES).

### 2. 📆 Estructura de la información

- [ ] Carga exitosa:

```json
{
  "mensaje": "Documentación cargada exitosamente",
  "data": {
    "id": 310,
    "estado_onboarding": "EN_VERIFICACION",
    "documentos": ["certificado_camara_comercio", "documento_nit"]
  },
  "success": true
}
```

- [ ] Validación exitosa:

```json
{
  "mensaje": "Validación contra el RUES exitosa",
  "data": {
    "id": 310,
    "resultado_validacion": "VIGENTE",
    "razon_social_rues": "Distribuidora Andina S.A.S.",
    "fecha_vigencia": "2027-03-31"
  },
  "success": true
}
```

- [ ] Registro no vigente:

```json
{
  "mensaje": "El registro mercantil no se encuentra vigente",
  "data": { "id": 310, "resultado_validacion": "NO_VIGENTE", "fecha_vigencia": "2026-03-31" },
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Verificación legal

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Cargar documentación legal | API-G37 | `POST` | `/api/v1/vendedores/{id}/documentos` | Agregada en el Parcial 2 |
| Validar documentación contra el RUES | API-G38 | `POST` | `/api/v1/vendedores/{id}/documentos/validar` | Agregada en el Parcial 2 |
| (Externa) Consulta al RUES | API-E01 | Pendiente de definir | Definido por el proveedor | Inventario inicial (API externa) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Cargar | `id` | ruta | entero | Sí | Identificador del vendedor |
| Cargar | `certificado_camara_comercio` | body (archivo) | PDF | Sí | Certificado vigente de Cámara de Comercio |
| Cargar | `documento_nit` | body (archivo) | PDF | Sí | Documento del NIT |
| Validar | `id` | ruta | entero | Sí | Identificador del vendedor |
| Consulta RUES (externa) | NIT del vendedor | petición al RUES | texto | Sí | Número de NIT a verificar |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Cargar | `201 Created` | Solicitud con estado y documentos cargados |
| Validar | `200 OK` | Resultado (`VIGENTE`, `NO_VIGENTE` o `PENDIENTE`), razón social y fecha de vigencia |
| Respuesta del RUES (externa) | — | Estado del registro mercantil, razón social y fecha de vigencia |

### 📤 Ejemplo de comunicación – RUES no disponible

```json
{
  "mensaje": "No fue posible consultar el RUES. La validación queda pendiente",
  "data": { "id": 310, "resultado_validacion": "PENDIENTE" },
  "success": false
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Cargar documentación válida

- **Precondición:** La solicitud está en `REGISTRADO` y los archivos son PDF de menos de 5 MB.
- **Acción:** Ejecutar `POST /api/v1/vendedores/310/documentos` con ambos archivos.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `estado_onboarding` = `EN_VERIFICACION`

### ✅ Caso 2: Validación con registro vigente

- **Precondición:** Hay documentación cargada y el RUES reporta el NIT como vigente con la misma razón social.
- **Acción:** Ejecutar `POST /api/v1/vendedores/310/documentos/validar`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `resultado_validacion` = `VIGENTE`
  - El resultado queda registrado con su fecha

### ❌ Caso 3: Archivo con formato no permitido

- **Precondición:** La solicitud está en `REGISTRADO`.
- **Acción:** Cargar un archivo `.exe` o una imagen en lugar de un PDF.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "Los documentos deben cargarse en formato PDF"

### ❌ Caso 4: Archivo que supera el tamaño máximo

- **Precondición:** Un archivo pesa más de 5 MB.
- **Acción:** Ejecutar la carga.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El archivo supera el tamaño máximo permitido de 5 MB"

### ❌ Caso 5: Documento faltante

- **Precondición:** Ninguna.
- **Acción:** Ejecutar la carga sin `documento_nit`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "Debe cargar el certificado de Cámara de Comercio y el documento del NIT"

### ❌ Caso 6: Registro mercantil no vigente (RN-07)

- **Precondición:** El RUES reporta el registro como no vigente.
- **Acción:** Ejecutar la validación.
- **Resultado esperado:**
  - Campo `resultado_validacion` = `NO_VIGENTE`
  - Campo `success` = `false`
  - El vendedor no podrá ser aprobado

### ❌ Caso 7: Razón social que no coincide

- **Precondición:** La razón social del RUES difiere de la registrada.
- **Acción:** Ejecutar la validación.
- **Resultado esperado:**
  - Campo `resultado_validacion` = `NO_VIGENTE` o `INCONSISTENTE`, con `mensaje`: "La razón social no coincide con la registrada en el RUES"

### ❌ Caso 8: RUES no disponible

- **Precondición:** El servicio externo no responde.
- **Acción:** Ejecutar la validación.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `resultado_validacion` = `PENDIENTE`
  - La solicitud no se rechaza automáticamente

### ❌ Caso 9: Cargar documentos en una solicitud no permitida

- **Precondición:** La solicitud está `CANCELADO` o `APROBADO`.
- **Acción:** Ejecutar la carga.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "La solicitud no admite carga de documentos en su estado actual"

### ❌ Caso 10: Solicitud ajena o inexistente

- **Precondición:** La solicitud pertenece a otro vendedor o no existe.
- **Acción:** Ejecutar la carga o la validación.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden` o `404 Not Found`

## ✅ Definición de Hecho

# Historia: Cargar y validar documentación legal contra el RUES

## 📦 Alcance Funcional

- [ ] La carga valida formato, tamaño y completitud de los documentos.
- [ ] La validación consulta el RUES y registra el resultado (vigente, no vigente o pendiente).
- [ ] Un registro no vigente impide la aprobación (RN-07) y una falla del RUES no rechaza al vendedor.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de documentos y de la interpretación de la respuesta del RUES (con un simulador del servicio externo).
- [ ] Se cubrieron los casos de error y de indisponibilidad del RUES.
- [ ] Las pruebas funcionales de los 10 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error
- [ ] Se documenta la dependencia del servicio externo (RUES) y su comportamiento ante fallas.

## 🔐 Manejo de Errores

- [ ] Se devuelve `400`, `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos o al RUES.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
