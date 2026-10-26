# [HU-01] Gestionar catálogo geográfico

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-01 Parametrización / SUB-02 Catálogos Geográficos |
| **Funcionalidades que cubre** | FUN-06 Registrar dato geográfico · FUN-07 Editar dato geográfico · FUN-08 Consultar/listar catálogo geográfico · FUN-09 Desactivar dato geográfico |
| **Regla de negocio asociada** | RN-47: un dato geográfico no puede desactivarse si existen direcciones activas asociadas |
| **APIs** | API-G01, API-G02, API-G03 (agregadas en el Parcial 2) · API-I09 Consultar Catálogo Geográfico (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 1 |
| **Depende de** | — (ninguna) |
| **Actor** | Administrador de la plataforma |

## 📖 Historia de Usuario

**Dado** que soy el administrador de la plataforma,
**Para** mantener actualizado el catálogo de países, departamentos y ciudades,
**Que** necesito registrar, editar, consultar y desactivar ubicaciones geográficas, de modo que las direcciones de envío, los perfiles de vendedor y las cotizaciones de envío usen siempre datos geográficos únicos, jerárquicos y vigentes.

## 🔁 Flujo Esperado

**Registrar ubicación**
- El administrador ingresa tipo (`PAIS`, `DEPARTAMENTO` o `CIUDAD`), nombre, código y, si aplica, la ubicación padre.
- El sistema consume el endpoint `POST /api/v1/parametrizacion/ubicaciones`.
- El backend valida los datos, la jerarquía y que no exista una ubicación duplicada.
- El backend almacena la ubicación con estado `ACTIVO` y retorna el registro creado.

**Editar ubicación**
- El administrador selecciona una ubicación existente y modifica nombre, código o padre.
- El sistema consume el endpoint `PUT /api/v1/parametrizacion/ubicaciones/{id}`.
- El backend valida el cambio (duplicidad y jerarquía) y actualiza el registro.

**Consultar / listar catálogo**
- El usuario solicita el catálogo, opcionalmente filtrando por tipo, ubicación padre o estado.
- El sistema consume el endpoint `GET /api/v1/parametrizacion/ubicaciones`.
- El backend consulta los registros y retorna el listado paginado con su jerarquía.

**Desactivar ubicación**
- El administrador selecciona la ubicación que ya no se utiliza.
- El sistema consume el endpoint `PATCH /api/v1/parametrizacion/ubicaciones/{id}/desactivar`.
- El backend valida que no existan direcciones activas ni ubicaciones hijas activas asociadas (RN-47) y la marca como `INACTIVO`. El registro no se elimina físicamente.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` para registrar ubicaciones, con los campos `tipo`, `nombre`, `codigo` y `padre_id` (obligatorio para `DEPARTAMENTO` y `CIUDAD`; no permitido para `PAIS`).
- [ ] Se valida la jerarquía: un `DEPARTAMENTO` solo puede tener como padre un `PAIS`, y una `CIUDAD` solo puede tener como padre un `DEPARTAMENTO`.
- [ ] Se valida que no exista otra ubicación del mismo tipo, con el mismo nombre y el mismo padre, ni otra con el mismo código.
- [ ] Se expone un endpoint `PUT` para editar nombre, código y padre; el `tipo` no puede modificarse.
- [ ] Se expone un endpoint `GET` que lista ubicaciones con filtros opcionales `tipo`, `padre_id` y `estado`, y con paginación (`pagina`, `tamano`).
- [ ] Se expone un endpoint `PATCH` para desactivar una ubicación; no se permite desactivarla si tiene direcciones activas asociadas (RN-47) o ubicaciones hijas activas.
- [ ] Las ubicaciones desactivadas no aparecen en el listado por defecto (solo con `estado=INACTIVO` o `estado=TODOS`).
- [ ] Las operaciones de registro, edición y desactivación están permitidas únicamente al rol Administrador.

### 2. 📆 Estructura de la información

- [ ] Registro exitoso responde con la siguiente estructura:

```json
{
  "mensaje": "Ubicación registrada exitosamente",
  "data": {
    "id": 1203,
    "tipo": "CIUDAD",
    "nombre": "Bucaramanga",
    "codigo": "68001",
    "padre_id": 68,
    "estado": "ACTIVO",
    "publicada": false
  },
  "success": true
}
```

- [ ] La ubicación se registra con `publicada = false`; se habilita para los demás módulos con HU-04.
- [ ] Si la ubicación ya existe, el backend retorna:

```json
{
  "mensaje": "Ya existe una ubicación con el mismo nombre o código en el mismo nivel",
  "data": null,
  "success": false
}
```

- [ ] El listado responde con la siguiente estructura:

```json
{
  "mensaje": "Consulta de ubicaciones exitosa",
  "data": {
    "pagina": 1,
    "tamano": 20,
    "total": 1,
    "ubicaciones": [
      {
        "id": 68,
        "tipo": "DEPARTAMENTO",
        "nombre": "Santander",
        "codigo": "68",
        "padre_id": 1,
        "estado": "ACTIVO"
      }
    ]
  },
  "success": true
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Catálogo geográfico

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Registrar ubicación | API-G01 | `POST` | `/api/v1/parametrizacion/ubicaciones` | Agregada en el Parcial 2 |
| Editar ubicación | API-G02 | `PUT` | `/api/v1/parametrizacion/ubicaciones/{id}` | Agregada en el Parcial 2 |
| Consultar / listar ubicaciones | API-I09 (Consultar Catálogo Geográfico) | `GET` | `/api/v1/parametrizacion/ubicaciones` | Inventario inicial (API interna) |
| Desactivar ubicación | API-G03 | `PATCH` | `/api/v1/parametrizacion/ubicaciones/{id}/desactivar` | Agregada en el Parcial 2 |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Registrar | `tipo` | body | texto | Sí | `PAIS`, `DEPARTAMENTO` o `CIUDAD` |
| Registrar | `nombre` | body | texto | Sí | Nombre de la ubicación (máx. 100 caracteres) |
| Registrar | `codigo` | body | texto | Sí | Código único de la ubicación (ej. código DANE) |
| Registrar | `padre_id` | body | entero | Condicional | Obligatorio para departamento y ciudad |
| Editar | `id` | ruta | entero | Sí | Identificador de la ubicación |
| Editar | `nombre`, `codigo`, `padre_id` | body | texto / entero | Sí | Nuevos valores |
| Listar | `tipo` | query | texto | No | Filtra por tipo |
| Listar | `padre_id` | query | entero | No | Filtra por ubicación padre |
| Listar | `estado` | query | texto | No | `ACTIVO` (por defecto), `INACTIVO` o `TODOS` |
| Listar | `pagina`, `tamano` | query | entero | No | Paginación (por defecto 1 y 20) |
| Desactivar | `id` | ruta | entero | Sí | Identificador de la ubicación |

### 📤 Salidas

Todas las respuestas usan la misma estructura: `mensaje` (texto), `data` (objeto, listado o `null`) y `success` (booleano).

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Registrar | `201 Created` | Ubicación creada |
| Editar | `200 OK` | Ubicación actualizada |
| Listar | `200 OK` | Listado paginado de ubicaciones |
| Desactivar | `200 OK` | Ubicación con `estado = INACTIVO` |

### 📤 Ejemplo de comunicación – Desactivar ubicación

Petición: `PATCH /api/v1/parametrizacion/ubicaciones/1203/desactivar`

Respuesta exitosa:

```json
{
  "mensaje": "Ubicación desactivada exitosamente",
  "data": {
    "id": 1203,
    "estado": "INACTIVO"
  },
  "success": true
}
```

Respuesta cuando existen direcciones activas asociadas (RN-47):

```json
{
  "mensaje": "No es posible desactivar la ubicación porque tiene direcciones activas asociadas",
  "data": null,
  "success": false
}
```

### 🏗️ Ubicación en la arquitectura

- **API:** `Parametrizacion.API` expone los endpoints.
- **Servicio:** orquesta el caso de uso y la paginación.
- **Dominio:** entidad `DatoGeografico` y regla RN-47.
- **Repositorio:** acceso al esquema de datos del módulo Parametrización.

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Registrar una ciudad válida

- **Precondición:** Existe el departamento Santander (`id = 68`) y no existe la ciudad Bucaramanga.
- **Acción:** Ejecutar `POST /api/v1/parametrizacion/ubicaciones` con `tipo = CIUDAD`, `nombre = Bucaramanga`, `codigo = 68001`, `padre_id = 68`.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `estado` = `ACTIVO`
  - Campo `success` = `true`
  - Campo `mensaje` contiene el texto: "Ubicación registrada exitosamente"

### ✅ Caso 2: Editar el nombre de una ubicación

- **Precondición:** Existe la ubicación con `id = 1203`.
- **Acción:** Ejecutar `PUT /api/v1/parametrizacion/ubicaciones/1203` con un nombre corregido y sin duplicar otro registro del mismo nivel.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `nombre` con el valor actualizado
  - Campo `success` = `true`

### ✅ Caso 3: Listar departamentos activos de un país

- **Precondición:** El país Colombia (`id = 1`) tiene departamentos activos e inactivos.
- **Acción:** Ejecutar `GET /api/v1/parametrizacion/ubicaciones?tipo=DEPARTAMENTO&padre_id=1`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Solo se retornan departamentos con `estado = ACTIVO`
  - La respuesta incluye `pagina`, `tamano`, `total` y `ubicaciones`

### ✅ Caso 4: Desactivar una ubicación sin uso

- **Precondición:** La ubicación no tiene direcciones activas ni ubicaciones hijas activas.
- **Acción:** Ejecutar `PATCH /api/v1/parametrizacion/ubicaciones/1203/desactivar`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `estado` = `INACTIVO`
  - El registro sigue existiendo en la base de datos
  - La ubicación ya no aparece en el listado por defecto

### ❌ Caso 5: Registrar una ubicación duplicada

- **Precondición:** Ya existe la ciudad Bucaramanga con padre Santander.
- **Acción:** Ejecutar `POST /api/v1/parametrizacion/ubicaciones` con los mismos nombre y padre.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `success` = `false`
  - Campo `mensaje` contiene el texto: "Ya existe una ubicación con el mismo nombre o código en el mismo nivel"

### ❌ Caso 6: Registrar con jerarquía inválida

- **Precondición:** Existe un país con `id = 1`.
- **Acción:** Ejecutar `POST /api/v1/parametrizacion/ubicaciones` con `tipo = CIUDAD` y `padre_id = 1` (un país, no un departamento).
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "La jerarquía de la ubicación no es válida"

### ❌ Caso 7: Registrar con datos obligatorios faltantes

- **Precondición:** El usuario es administrador.
- **Acción:** Ejecutar `POST /api/v1/parametrizacion/ubicaciones` sin el campo `nombre`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` indica el campo faltante: "El campo nombre es obligatorio"

### ❌ Caso 8: Desactivar una ubicación con direcciones activas (RN-47)

- **Precondición:** La ciudad tiene al menos una dirección activa asociada.
- **Acción:** Ejecutar `PATCH /api/v1/parametrizacion/ubicaciones/{id}/desactivar`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - La ubicación conserva `estado = ACTIVO`
  - Campo `mensaje` contiene el texto: "No es posible desactivar la ubicación porque tiene direcciones activas asociadas"

### ❌ Caso 9: Editar o desactivar una ubicación inexistente

- **Precondición:** No existe una ubicación con `id = 99999`.
- **Acción:** Ejecutar `PUT` o `PATCH` sobre `/api/v1/parametrizacion/ubicaciones/99999`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "La ubicación no existe"

### ❌ Caso 10: Usuario sin permisos de administrador

- **Precondición:** El usuario autenticado no tiene rol Administrador.
- **Acción:** Ejecutar `POST /api/v1/parametrizacion/ubicaciones`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - No se crea ningún registro

### ❌ Caso 11: Falla de base de datos

- **Precondición:** La base de datos no está disponible o ocurre un error en la consulta.
- **Acción:** Ejecutar cualquiera de los endpoints bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud de ubicaciones"

## ✅ Definición de Hecho

# Historia: Gestionar catálogo geográfico

## 📦 Alcance Funcional

- [ ] Los cuatro endpoints (registrar, editar, listar y desactivar) funcionan según lo definido.
- [ ] Se valida la jerarquía país → departamento → ciudad y la unicidad por nombre, nivel y código.
- [ ] La desactivación respeta la regla RN-47 y es lógica (no elimina el registro).
- [ ] Las respuestas JSON cumplen con el contrato definido (`mensaje`, `data`, `success`).

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (jerarquía, duplicidad y RN-47).
- [ ] Se cubrieron los casos de error y de listado sin resultados.
- [ ] Las pruebas funcionales de los 11 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error

## 🔐 Manejo de Errores

- [ ] Se devuelve `400` para datos inválidos, `403` sin permisos, `404` para ubicaciones inexistentes y `409` para duplicados o desactivaciones no permitidas.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
