# [HU-08] Registrar y gestionar el onboarding del vendedor

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-04 Vendedores y Verificación / SUB-10 Registro y Onboarding |
| **Funcionalidades que cubre** | FUN-46 Registrar nuevo vendedor · FUN-47 Editar datos de registro · FUN-48 Consultar estado de onboarding · FUN-49 Cancelar registro |
| **Reglas de negocio asociadas** | RN-08: no pueden existir dos vendedores activos con el mismo NIT · RN-06: un vendedor no puede pasar a estado "activo" sin aprobación de verificación legal |
| **APIs** | API-G33, API-G34, API-G35, API-G36 (agregadas en el Parcial 2) · consume API-I08 Consultar Tipos de Documento y API-I09 Consultar Catálogo Geográfico (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 8 |
| **Depende de** | HU-04, HU-05, HU-07 |
| **Actor** | Vendedor (empresa que desea vender en la plataforma) |

## 📖 Historia de Usuario

**Dado** que soy una empresa legalmente constituida que quiere vender en la plataforma,
**Para** iniciar mi proceso de incorporación como vendedor,
**Que** necesito registrar los datos de mi empresa, corregirlos antes de la verificación, consultar en qué etapa está mi solicitud y cancelarla si decido no continuar, de modo que mi tienda pueda ser verificada y habilitada para vender.

## 🔁 Flujo Esperado

**Registrar vendedor**
- El vendedor ingresa tipo y número de documento (NIT), razón social, correo, teléfono, ciudad y dirección.
- El sistema consume `POST /api/v1/vendedores`.
- El backend valida el NIT contra el formato del tipo (API-I08), la ciudad (API-I09) y que no exista otro vendedor activo con el mismo NIT (RN-08).
- El backend crea la solicitud con estado `REGISTRADO` y la deja pendiente de documentación.

**Editar datos de registro**
- El vendedor corrige información básica mientras la solicitud no esté en verificación.
- El sistema consume `PUT /api/v1/vendedores/{id}`.

**Consultar estado de onboarding**
- El vendedor consulta la etapa actual de su solicitud con `GET /api/v1/vendedores/{id}/onboarding`.

**Cancelar registro**
- El vendedor retira su solicitud antes de completarla con `PATCH /api/v1/vendedores/{id}/cancelar-registro`.
- El backend cambia el estado a `CANCELADO`.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` con `tipo_documento_id`, `numero_documento`, `razon_social`, `correo`, `telefono`, `ciudad_id` y `direccion`.
- [ ] El número de documento se valida con el formato del tipo y la ciudad debe existir, estar activa y publicada.
- [ ] No se permite registrar un NIT que ya pertenece a un vendedor activo (RN-08).
- [ ] La solicitud nace en estado `REGISTRADO`; el vendedor no queda `ACTIVO` hasta ser aprobado (RN-06).
- [ ] Se expone un endpoint `PUT` que solo permite editar mientras el estado sea `REGISTRADO` o `DOCUMENTACION_PENDIENTE`.
- [ ] Se expone un endpoint `GET` que retorna la etapa actual: `REGISTRADO`, `DOCUMENTACION_PENDIENTE`, `EN_VERIFICACION`, `APROBADO`, `RECHAZADO` o `CANCELADO`.
- [ ] Se expone un endpoint `PATCH` de cancelación, permitido solo antes de la aprobación.
- [ ] Cada vendedor solo puede consultar, editar y cancelar su propia solicitud.

### 2. 📆 Estructura de la información

- [ ] Registro exitoso:

```json
{
  "mensaje": "Solicitud de vendedor registrada exitosamente",
  "data": {
    "id": 310,
    "razon_social": "Distribuidora Andina S.A.S.",
    "numero_documento": "900123456-7",
    "estado_onboarding": "REGISTRADO"
  },
  "success": true
}
```

- [ ] Consulta de estado:

```json
{
  "mensaje": "Consulta de onboarding exitosa",
  "data": {
    "id": 310,
    "estado_onboarding": "DOCUMENTACION_PENDIENTE",
    "etapa_siguiente": "Cargar la documentación legal"
  },
  "success": true
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Onboarding del vendedor

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Registrar vendedor | API-G33 | `POST` | `/api/v1/vendedores` | Agregada en el Parcial 2 |
| Editar datos de registro | API-G34 | `PUT` | `/api/v1/vendedores/{id}` | Agregada en el Parcial 2 |
| Consultar estado de onboarding | API-G35 | `GET` | `/api/v1/vendedores/{id}/onboarding` | Agregada en el Parcial 2 |
| Cancelar registro | API-G36 | `PATCH` | `/api/v1/vendedores/{id}/cancelar-registro` | Agregada en el Parcial 2 |
| (Consumida) Tipos de documento | API-I08 | `GET` | `/api/v1/parametrizacion/tipos-documento` | Inventario inicial (API interna) |
| (Consumida) Catálogo geográfico | API-I09 | `GET` | `/api/v1/parametrizacion/ubicaciones` | Inventario inicial (API interna) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Registrar | `tipo_documento_id`, `numero_documento` | body | entero / texto | Sí | Identificación de la empresa (NIT) |
| Registrar | `razon_social` | body | texto | Sí | Nombre legal de la empresa |
| Registrar | `correo`, `telefono` | body | texto | Sí | Datos de contacto |
| Registrar | `ciudad_id`, `direccion` | body | entero / texto | Sí | Ubicación de la empresa |
| Editar | `id` | ruta | entero | Sí | Identificador de la solicitud |
| Editar | `razon_social`, `correo`, `telefono`, `ciudad_id`, `direccion` | body | texto / entero | Sí | Datos corregidos |
| Consultar / Cancelar | `id` | ruta | entero | Sí | Identificador de la solicitud |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Registrar | `201 Created` | Solicitud creada con `estado_onboarding` |
| Editar | `200 OK` | Solicitud actualizada |
| Consultar | `200 OK` | Etapa actual y etapa siguiente |
| Cancelar | `200 OK` | Solicitud con `estado_onboarding = CANCELADO` |

### 📤 Ejemplo de comunicación – Cancelar registro

```json
{
  "mensaje": "Registro cancelado exitosamente",
  "data": { "id": 310, "estado_onboarding": "CANCELADO" },
  "success": true
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Registrar un vendedor válido

- **Precondición:** El NIT no pertenece a un vendedor activo y cumple el formato; la ciudad existe y está publicada.
- **Acción:** Ejecutar `POST /api/v1/vendedores` con datos válidos.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `estado_onboarding` = `REGISTRADO`

### ✅ Caso 2: Editar datos antes de la verificación

- **Precondición:** La solicitud está en `REGISTRADO`.
- **Acción:** Ejecutar `PUT /api/v1/vendedores/310` con un teléfono corregido.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El teléfono se actualiza

### ✅ Caso 3: Consultar el estado de la solicitud

- **Precondición:** La solicitud existe y pertenece al vendedor autenticado.
- **Acción:** Ejecutar `GET /api/v1/vendedores/310/onboarding`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Se retorna la etapa actual

### ✅ Caso 4: Cancelar el registro

- **Precondición:** La solicitud no está `APROBADO`.
- **Acción:** Ejecutar `PATCH /api/v1/vendedores/310/cancelar-registro`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `estado_onboarding` = `CANCELADO`

### ❌ Caso 5: NIT ya registrado por un vendedor activo (RN-08)

- **Precondición:** Existe un vendedor `ACTIVO` con el mismo NIT.
- **Acción:** Ejecutar `POST /api/v1/vendedores` con ese NIT.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "Ya existe un vendedor activo con el NIT indicado"

### ❌ Caso 6: NIT que no cumple el formato

- **Precondición:** El tipo NIT tiene formato definido.
- **Acción:** Ejecutar el registro con un NIT mal formado.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El número de documento no cumple el formato del tipo seleccionado"

### ❌ Caso 7: Ciudad inexistente o no publicada

- **Precondición:** La ciudad no existe o no está publicada.
- **Acción:** Ejecutar el registro con ese `ciudad_id`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "La ciudad indicada no es válida"

### ❌ Caso 8: Editar una solicitud en verificación

- **Precondición:** La solicitud está en `EN_VERIFICACION`.
- **Acción:** Ejecutar `PUT /api/v1/vendedores/310`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "La solicitud no puede editarse en su estado actual"

### ❌ Caso 9: Cancelar una solicitud ya aprobada

- **Precondición:** La solicitud está `APROBADO`.
- **Acción:** Ejecutar `PATCH /api/v1/vendedores/310/cancelar-registro`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "No es posible cancelar una solicitud ya aprobada"

### ❌ Caso 10: Solicitud de otro vendedor o inexistente

- **Precondición:** La solicitud pertenece a otro vendedor, o no existe.
- **Acción:** Ejecutar `GET`, `PUT` o `PATCH` sobre ella.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden` si pertenece a otro vendedor, o `404 Not Found` si no existe

### ❌ Caso 11: Falla de base de datos o de Parametrización

- **Precondición:** La base de datos o las consultas API-I08 / API-I09 no están disponibles.
- **Acción:** Ejecutar el registro.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud de registro"

## ✅ Definición de Hecho

# Historia: Registrar y gestionar el onboarding del vendedor

## 📦 Alcance Funcional

- [ ] Los cuatro endpoints funcionan según lo definido.
- [ ] Se aplican las reglas RN-08 y RN-06 (el vendedor no queda activo sin aprobación).
- [ ] La edición y la cancelación respetan las etapas permitidas.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (NIT, estados y transiciones).
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

- [ ] Se devuelve `400`, `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos o a Parametrización.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
