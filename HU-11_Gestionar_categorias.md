# [HU-11] Gestionar categorías del catálogo

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-03 Catálogo de Productos / SUB-08 Categorías y Atributos |
| **Funcionalidades que cubre** | FUN-36 Registrar categoría · FUN-37 Editar categoría · FUN-38 Consultar/listar categorías · FUN-39 Eliminar categoría |
| **Regla de negocio asociada** | RN-04: no se puede eliminar una categoría que tenga productos asociados |
| **APIs** | API-G20, API-G21, API-G22, API-G23 (agregadas en el Parcial 2) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 11 |
| **Depende de** | HU-07 |
| **Actor** | Administrador de la plataforma (la consulta también la usan vendedores y compradores) |

## 📖 Historia de Usuario

**Dado** que soy el administrador de la plataforma,
**Para** organizar los productos en un árbol de categorías,
**Que** necesito registrar, editar, consultar y eliminar categorías, de modo que los vendedores clasifiquen sus productos y los compradores los encuentren fácilmente.

## 🔁 Flujo Esperado

**Registrar categoría**
- El administrador ingresa el nombre y, si es una subcategoría, la categoría padre.
- El sistema consume `POST /api/v1/catalogo/categorias`.
- El backend valida que el nombre no se repita dentro del mismo padre y crea la categoría con estado `ACTIVA`.

**Editar categoría**
- El administrador modifica el nombre o cambia su categoría padre.
- El sistema consume `PUT /api/v1/catalogo/categorias/{id}`.
- El backend valida el cambio y evita ciclos en el árbol.

**Consultar / listar categorías**
- El usuario solicita el árbol completo con `GET /api/v1/catalogo/categorias`.
- El backend retorna las categorías activas organizadas jerárquicamente.

**Eliminar categoría**
- El administrador selecciona una categoría sin productos.
- El sistema consume `DELETE /api/v1/catalogo/categorias/{id}`.
- El backend valida que no tenga productos ni subcategorías asociados (RN-04) y la elimina.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` con `nombre` y `padre_id` (opcional; si no se envía, es una categoría raíz).
- [ ] Se valida que no exista otra categoría con el mismo nombre bajo el mismo padre.
- [ ] Se expone un endpoint `PUT` que permite cambiar `nombre` y `padre_id`; no se permite que una categoría sea su propio ancestro.
- [ ] Se expone un endpoint `GET` que retorna el árbol jerárquico de categorías `ACTIVA`.
- [ ] Se expone un endpoint `DELETE` que no permite eliminar categorías con productos asociados (RN-04) ni con subcategorías.
- [ ] Las operaciones de registro, edición y eliminación están permitidas solo al rol Administrador; la consulta está abierta a usuarios autenticados y visitantes.

### 2. 📆 Estructura de la información

- [ ] Registro exitoso:

```json
{
  "mensaje": "Categoría registrada exitosamente",
  "data": { "id": 12, "nombre": "Camisetas", "padre_id": 5, "estado": "ACTIVA" },
  "success": true
}
```

- [ ] Consulta del árbol:

```json
{
  "mensaje": "Consulta de categorías exitosa",
  "data": [
    {
      "id": 5,
      "nombre": "Ropa",
      "hijas": [ { "id": 12, "nombre": "Camisetas", "hijas": [] } ]
    }
  ],
  "success": true
}
```

- [ ] Eliminación no permitida:

```json
{
  "mensaje": "No es posible eliminar la categoría porque tiene productos asociados",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Categorías

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Registrar categoría | API-G20 | `POST` | `/api/v1/catalogo/categorias` | Agregada en el Parcial 2 |
| Editar categoría | API-G21 | `PUT` | `/api/v1/catalogo/categorias/{id}` | Agregada en el Parcial 2 |
| Consultar categorías | API-G22 | `GET` | `/api/v1/catalogo/categorias` | Agregada en el Parcial 2 |
| Eliminar categoría | API-G23 | `DELETE` | `/api/v1/catalogo/categorias/{id}` | Agregada en el Parcial 2 |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Registrar | `nombre` | body | texto | Sí | Nombre de la categoría (máx. 80 caracteres) |
| Registrar | `padre_id` | body | entero | No | Categoría padre; vacío para raíz |
| Editar | `id` | ruta | entero | Sí | Identificador de la categoría |
| Editar | `nombre`, `padre_id` | body | texto / entero | Sí | Nuevos valores |
| Eliminar | `id` | ruta | entero | Sí | Identificador de la categoría |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Registrar | `201 Created` | Categoría creada |
| Editar | `200 OK` | Categoría actualizada |
| Consultar | `200 OK` | Árbol de categorías activas |
| Eliminar | `200 OK` | Confirmación con el `id` eliminado |

### 📤 Ejemplo de comunicación – Eliminar categoría

Petición: `DELETE /api/v1/catalogo/categorias/12`

```json
{ "mensaje": "Categoría eliminada exitosamente", "data": { "id": 12 }, "success": true }
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Registrar una subcategoría

- **Precondición:** Existe la categoría "Ropa" (`id = 5`) y no existe "Camisetas" bajo ella.
- **Acción:** Ejecutar `POST /api/v1/catalogo/categorias` con `nombre = Camisetas` y `padre_id = 5`.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `estado` = `ACTIVA`

### ✅ Caso 2: Editar el nombre de una categoría

- **Precondición:** Existe la categoría con `id = 12`.
- **Acción:** Ejecutar `PUT /api/v1/catalogo/categorias/12` con un nuevo `nombre`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El nombre se actualiza

### ✅ Caso 3: Consultar el árbol de categorías

- **Precondición:** Existen categorías raíz y subcategorías.
- **Acción:** Ejecutar `GET /api/v1/catalogo/categorias`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Las subcategorías aparecen anidadas bajo su padre

### ✅ Caso 4: Eliminar una categoría sin productos

- **Precondición:** La categoría no tiene productos ni subcategorías.
- **Acción:** Ejecutar `DELETE /api/v1/catalogo/categorias/12`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - La categoría ya no aparece en el árbol

### ❌ Caso 5: Categoría duplicada bajo el mismo padre

- **Precondición:** Ya existe "Camisetas" bajo "Ropa".
- **Acción:** Ejecutar el `POST` con el mismo nombre y padre.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "Ya existe una categoría con ese nombre en el mismo nivel"

### ❌ Caso 6: Padre inexistente

- **Precondición:** No existe la categoría `id = 99999`.
- **Acción:** Ejecutar el `POST` con `padre_id = 99999`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "La categoría padre no existe"

### ❌ Caso 7: Ciclo en el árbol

- **Precondición:** La categoría A es padre de B.
- **Acción:** Ejecutar `PUT` sobre A con `padre_id` = B.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "Una categoría no puede ser hija de sus propias subcategorías"

### ❌ Caso 8: Eliminar una categoría con productos (RN-04)

- **Precondición:** La categoría tiene al menos un producto asociado.
- **Acción:** Ejecutar `DELETE /api/v1/catalogo/categorias/{id}`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - La categoría se conserva
  - Campo `mensaje` contiene el texto: "No es posible eliminar la categoría porque tiene productos asociados"

### ❌ Caso 9: Categoría inexistente

- **Precondición:** No existe `id = 99999`.
- **Acción:** Ejecutar `PUT` o `DELETE` sobre ella.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "La categoría no existe"

### ❌ Caso 10: Usuario sin permisos

- **Precondición:** El usuario no es Administrador.
- **Acción:** Ejecutar `POST /api/v1/catalogo/categorias`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`

### ❌ Caso 11: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud de categorías"

## ✅ Definición de Hecho

# Historia: Gestionar categorías del catálogo

## 📦 Alcance Funcional

- [ ] Los cuatro endpoints funcionan según lo definido.
- [ ] Se respeta la jerarquía del árbol (sin ciclos ni duplicados) y la regla RN-04.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (duplicados, ciclos y RN-04).
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
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
