# [HU-10] Aprobar o rechazar la verificación del vendedor

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-04 Vendedores y Verificación / SUB-11 Verificación Legal |
| **Funcionalidad que cubre** | FUN-53 Aprobar o rechazar vendedor |
| **Reglas de negocio asociadas** | RN-06: un vendedor no puede pasar a estado "activo" sin aprobación de verificación legal · RN-07: no se puede aprobar un vendedor con certificado vencido · RN-08: no pueden existir dos vendedores activos con el mismo NIT |
| **APIs** | API-G39 (agregada en el Parcial 2) · API-I07 Consultar Estado de Vendedor (inventario inicial, refleja el resultado de esta decisión) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 10 |
| **Depende de** | HU-09 |
| **Actor** | Administrador de la plataforma |

## 📖 Historia de Usuario

**Dado** que soy el administrador de la plataforma y un vendedor ya cargó y validó su documentación,
**Para** decidir si puede vender en la plataforma,
**Que** necesito aprobar o rechazar su verificación, de modo que solo las empresas legalmente constituidas y vigentes queden activas y puedan publicar productos.

## 🔁 Flujo Esperado

- El administrador revisa el resultado de la validación contra el RUES y elige `APROBAR` o `RECHAZAR` (con el motivo).
- El sistema consume el endpoint `PATCH /api/v1/vendedores/{id}/verificacion`.
- El backend valida las condiciones de aprobación (registro vigente, sin documento vencido, NIT sin duplicar).
- El backend actualiza el estado del vendedor: `ACTIVO` si se aprueba o `RECHAZADO` si se rechaza.
- El nuevo estado queda disponible para los demás módulos mediante la API-I07 (Consultar Estado de Vendedor).

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `PATCH` con `decision` (`APROBAR` o `RECHAZAR`) y `motivo`.
- [ ] Solo se puede decidir sobre solicitudes en estado `EN_VERIFICACION`.
- [ ] Para aprobar, la última validación debe ser `VIGENTE` (RN-07) y no debe existir otro vendedor `ACTIVO` con el mismo NIT (RN-08).
- [ ] El `motivo` es obligatorio al rechazar.
- [ ] Solo al aprobar el vendedor pasa a `ACTIVO` (RN-06).
- [ ] Se registra quién decidió, cuándo y con qué motivo.
- [ ] La operación está permitida solo al rol Administrador.

### 2. 📆 Estructura de la información

- [ ] Aprobación exitosa:

```json
{
  "mensaje": "Vendedor aprobado exitosamente",
  "data": {
    "id": 310,
    "estado_vendedor": "ACTIVO",
    "decidido_por": "admin@plataforma.com",
    "fecha_decision": "2026-10-25T15:10:00Z"
  },
  "success": true
}
```

- [ ] Rechazo exitoso:

```json
{
  "mensaje": "Vendedor rechazado",
  "data": { "id": 310, "estado_vendedor": "RECHAZADO", "motivo": "Registro mercantil no vigente" },
  "success": true
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoint – Verificación del vendedor

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Aprobar o rechazar vendedor | API-G39 | `PATCH` | `/api/v1/vendedores/{id}/verificacion` | Agregada en el Parcial 2 |
| (Relacionada) Consultar estado de vendedor | API-I07 | `GET` | `/api/v1/vendedores/{id}/estado` | Inventario inicial (API interna) |

### 📥 Entradas

| Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `id` | ruta | entero | Sí | Identificador del vendedor |
| `decision` | body | texto | Sí | `APROBAR` o `RECHAZAR` |
| `motivo` | body | texto | Condicional | Obligatorio al rechazar (máx. 300 caracteres) |

### 📤 Salidas

| Código HTTP | Contenido de `data` |
|---|---|
| `200 OK` | Vendedor con su nuevo `estado_vendedor` (`ACTIVO` o `RECHAZADO`) y datos de la decisión |

### 📤 Ejemplo de comunicación – Petición

```json
{ "decision": "RECHAZAR", "motivo": "Registro mercantil no vigente" }
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Aprobar un vendedor con registro vigente

- **Precondición:** La solicitud está `EN_VERIFICACION` con validación `VIGENTE` y el NIT no está duplicado.
- **Acción:** Ejecutar `PATCH /api/v1/vendedores/310/verificacion` con `decision = APROBAR`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `estado_vendedor` = `ACTIVO`
  - La API-I07 retorna `activo` para ese vendedor

### ✅ Caso 2: Rechazar un vendedor con motivo

- **Precondición:** La solicitud está `EN_VERIFICACION`.
- **Acción:** Ejecutar el `PATCH` con `decision = RECHAZAR` y un `motivo`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `estado_vendedor` = `RECHAZADO`
  - El motivo queda registrado

### ❌ Caso 3: Aprobar con registro no vigente (RN-07)

- **Precondición:** La última validación es `NO_VIGENTE`.
- **Acción:** Ejecutar el `PATCH` con `decision = APROBAR`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "No es posible aprobar al vendedor porque su registro mercantil no está vigente"

### ❌ Caso 4: Aprobar sin validación realizada

- **Precondición:** La validación está `PENDIENTE` o no se ha realizado.
- **Acción:** Ejecutar el `PATCH` con `decision = APROBAR`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "La documentación del vendedor aún no ha sido validada"

### ❌ Caso 5: NIT ya activo en otro vendedor (RN-08)

- **Precondición:** Existe otro vendedor `ACTIVO` con el mismo NIT.
- **Acción:** Ejecutar el `PATCH` con `decision = APROBAR`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "Ya existe un vendedor activo con el NIT indicado"

### ❌ Caso 6: Rechazar sin motivo

- **Precondición:** La solicitud está `EN_VERIFICACION`.
- **Acción:** Ejecutar el `PATCH` con `decision = RECHAZAR` sin `motivo`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El motivo es obligatorio al rechazar"

### ❌ Caso 7: Solicitud que no está en verificación

- **Precondición:** La solicitud está `REGISTRADO`, `CANCELADO` o ya decidida.
- **Acción:** Ejecutar el `PATCH`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "La solicitud no se encuentra en verificación"

### ❌ Caso 8: Vendedor inexistente

- **Precondición:** No existe `id = 99999`.
- **Acción:** Ejecutar el `PATCH`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "El vendedor no existe"

### ❌ Caso 9: Usuario sin permisos de administrador

- **Precondición:** El usuario no es Administrador.
- **Acción:** Ejecutar el `PATCH`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - El estado del vendedor no cambia

### ❌ Caso 10: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar el endpoint bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible registrar la decisión de verificación"

## ✅ Definición de Hecho

# Historia: Aprobar o rechazar la verificación del vendedor

## 📦 Alcance Funcional

- [ ] El endpoint aprueba o rechaza solo solicitudes en verificación.
- [ ] Se aplican las reglas RN-06, RN-07 y RN-08.
- [ ] El estado del vendedor queda disponible para los demás módulos mediante la API-I07.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las reglas de aprobación y de las transiciones de estado.
- [ ] Se cubrieron los casos de error.
- [ ] Las pruebas funcionales de los 10 casos están documentadas y pasadas.

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
