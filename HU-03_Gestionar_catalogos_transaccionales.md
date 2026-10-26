# [HU-03] Gestionar catálogos transaccionales

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-01 Parametrización / SUB-03 Catálogos Transaccionales |
| **Funcionalidades que cubre** | FUN-11 Registrar valor paramétrico · FUN-12 Editar valor paramétrico · FUN-13 Consultar/listar catálogos transaccionales · FUN-14 Desactivar valor paramétrico |
| **Reglas de negocio asociadas** | RN-46: no se puede eliminar un valor paramétrico utilizado por otro módulo (aplicada a la desactivación, que es la baja lógica) · RN-49: un valor inactivo no puede ser consumido por otros módulos |
| **APIs** | API-G09, API-G10, API-G11, API-G12 (agregadas en el Parcial 2) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 3 |
| **Depende de** | — (ninguna) |
| **Actor** | Administrador de la plataforma |

## 📖 Historia de Usuario

**Dado** que soy el administrador de la plataforma,
**Para** administrar en un solo lugar los estados, monedas, unidades de medida y métodos de pago que usan todos los módulos,
**Que** necesito registrar, editar, consultar y desactivar valores paramétricos por categoría, de modo que los demás módulos reutilicen datos maestros consistentes en lugar de repetirlos.

## 🔁 Flujo Esperado

**Registrar valor**
- El administrador ingresa la categoría (`ESTADO`, `MONEDA`, `UNIDAD_MEDIDA` o `METODO_PAGO`), el código y el nombre.
- El sistema consume `POST /api/v1/parametrizacion/valores`.
- El backend valida que no esté duplicado en la categoría y lo almacena con estado `ACTIVO`.

**Editar valor**
- El administrador selecciona el valor y modifica su nombre o descripción.
- El sistema consume `PUT /api/v1/parametrizacion/valores/{id}`.
- El backend valida el cambio y actualiza el registro.

**Consultar / listar catálogos**
- El usuario o módulo solicita los valores de una categoría.
- El sistema consume `GET /api/v1/parametrizacion/valores?categoria=...`.
- El backend retorna los valores de la categoría.

**Desactivar valor**
- El administrador selecciona el valor en desuso.
- El sistema consume `PATCH /api/v1/parametrizacion/valores/{id}/desactivar`.
- El backend valida que no afecte procesos en curso (RN-46) y lo marca como `INACTIVO`.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` con `categoria`, `codigo` y `nombre`.
- [ ] Se valida que el par (`categoria`, `codigo`) no exista previamente.
- [ ] Se expone un endpoint `PUT` para editar `nombre` y `descripcion`; `categoria` y `codigo` no se modifican.
- [ ] Se expone un endpoint `GET` con parámetro `categoria`; por defecto solo retorna valores `ACTIVO` (RN-49).
- [ ] Se expone un endpoint `PATCH` para desactivar; no se permite si el valor está siendo utilizado por otro módulo (RN-46).
- [ ] Las operaciones de registro, edición y desactivación están permitidas solo al rol Administrador.

### 2. 📆 Estructura de la información

- [ ] Registro exitoso:

```json
{
  "mensaje": "Valor paramétrico registrado exitosamente",
  "data": {
    "id": 31,
    "categoria": "METODO_PAGO",
    "codigo": "PSE",
    "nombre": "Pago por PSE",
    "estado": "ACTIVO"
  },
  "success": true
}
```

- [ ] Listado exitoso por categoría:

```json
{
  "mensaje": "Consulta de valores paramétricos exitosa",
  "data": [
    { "id": 30, "categoria": "METODO_PAGO", "codigo": "TC", "nombre": "Tarjeta de crédito", "estado": "ACTIVO" },
    { "id": 31, "categoria": "METODO_PAGO", "codigo": "PSE", "nombre": "Pago por PSE", "estado": "ACTIVO" }
  ],
  "success": true
}
```

- [ ] Si el valor está en uso al desactivar:

```json
{
  "mensaje": "No es posible desactivar el valor porque está siendo utilizado por otro módulo",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Valores paramétricos

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Registrar valor paramétrico | API-G09 | `POST` | `/api/v1/parametrizacion/valores` | Agregada en el Parcial 2 |
| Editar valor paramétrico | API-G10 | `PUT` | `/api/v1/parametrizacion/valores/{id}` | Agregada en el Parcial 2 |
| Consultar valores paramétricos | API-G11 | `GET` | `/api/v1/parametrizacion/valores` | Agregada en el Parcial 2 |
| Desactivar valor paramétrico | API-G12 | `PATCH` | `/api/v1/parametrizacion/valores/{id}/desactivar` | Agregada en el Parcial 2 |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Registrar | `categoria` | body | texto | Sí | `ESTADO`, `MONEDA`, `UNIDAD_MEDIDA` o `METODO_PAGO` |
| Registrar | `codigo` | body | texto | Sí | Código del valor, único dentro de su categoría |
| Registrar | `nombre` | body | texto | Sí | Nombre visible (máx. 80 caracteres) |
| Editar | `id` | ruta | entero | Sí | Identificador del valor |
| Editar | `nombre`, `descripcion` | body | texto | Sí | Nuevos valores |
| Listar | `categoria` | query | texto | Sí | Categoría a consultar |
| Listar | `estado` | query | texto | No | `ACTIVO` (por defecto), `INACTIVO` o `TODOS` |
| Desactivar | `id` | ruta | entero | Sí | Identificador del valor |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Registrar | `201 Created` | Valor creado |
| Editar | `200 OK` | Valor actualizado |
| Listar | `200 OK` | Arreglo de valores de la categoría |
| Desactivar | `200 OK` | Valor con `estado = INACTIVO` |

### 📤 Ejemplo de comunicación – Consultar valores

Petición: `GET /api/v1/parametrizacion/valores?categoria=MONEDA`

```json
{
  "mensaje": "Consulta de valores paramétricos exitosa",
  "data": [ { "id": 12, "categoria": "MONEDA", "codigo": "COP", "nombre": "Peso colombiano", "estado": "ACTIVO" } ],
  "success": true
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Registrar un valor válido

- **Precondición:** No existe el código `PSE` en la categoría `METODO_PAGO`.
- **Acción:** Ejecutar `POST /api/v1/parametrizacion/valores` con `categoria = METODO_PAGO`, `codigo = PSE`, `nombre = Pago por PSE`.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `estado` = `ACTIVO`

### ✅ Caso 2: Editar un valor

- **Precondición:** Existe el valor con `id = 31`.
- **Acción:** Ejecutar `PUT /api/v1/parametrizacion/valores/31` con un nuevo `nombre`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El nombre cambia; la categoría y el código se conservan

### ✅ Caso 3: Listar valores de una categoría

- **Precondición:** La categoría `MONEDA` tiene valores activos e inactivos.
- **Acción:** Ejecutar `GET /api/v1/parametrizacion/valores?categoria=MONEDA`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Solo se retornan valores `ACTIVO` (RN-49)

### ✅ Caso 4: Desactivar un valor sin uso

- **Precondición:** Ningún módulo usa el valor.
- **Acción:** Ejecutar `PATCH /api/v1/parametrizacion/valores/{id}/desactivar`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `estado` = `INACTIVO` y el registro se conserva

### ❌ Caso 5: Registrar un valor duplicado

- **Precondición:** Ya existe `COP` en la categoría `MONEDA`.
- **Acción:** Ejecutar `POST` con `categoria = MONEDA` y `codigo = COP`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "Ya existe un valor con el mismo código en la categoría"

### ❌ Caso 6: Categoría no válida

- **Precondición:** El usuario es administrador.
- **Acción:** Ejecutar `POST` con `categoria = COLORES`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "La categoría indicada no es válida"

### ❌ Caso 7: Desactivar un valor en uso (RN-46)

- **Precondición:** Otro módulo utiliza el valor (por ejemplo, un método de pago con transacciones en curso).
- **Acción:** Ejecutar `PATCH /api/v1/parametrizacion/valores/{id}/desactivar`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - El valor conserva `estado = ACTIVO`
  - Campo `mensaje` contiene el texto: "No es posible desactivar el valor porque está siendo utilizado por otro módulo"

### ❌ Caso 8: Valor inexistente

- **Precondición:** No existe el `id = 99999`.
- **Acción:** Ejecutar `PUT` o `PATCH` sobre `/api/v1/parametrizacion/valores/99999`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "El valor paramétrico no existe"

### ❌ Caso 9: Usuario sin permisos

- **Precondición:** El usuario no es Administrador.
- **Acción:** Ejecutar `POST /api/v1/parametrizacion/valores`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`

### ❌ Caso 10: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud de valores paramétricos"

## ✅ Definición de Hecho

# Historia: Gestionar catálogos transaccionales

## 📦 Alcance Funcional

- [ ] Los cuatro endpoints funcionan según lo definido.
- [ ] Se valida la unicidad por categoría y la baja respeta el uso por otros módulos (RN-46).
- [ ] Los valores inactivos no se retornan a los consumidores (RN-49).
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (unicidad, uso y estado).
- [ ] Se cubrieron los casos de error y de listado sin resultados.
- [ ] Las pruebas funcionales de los 10 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error

## 🔐 Manejo de Errores

- [ ] Se devuelve `400`, `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
