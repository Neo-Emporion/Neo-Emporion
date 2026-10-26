# [HU-12] Asignar atributos personalizados a categorías

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-03 Catálogo de Productos / SUB-08 Categorías y Atributos |
| **Funcionalidad que cubre** | FUN-40 Asignar atributos personalizados |
| **Regla de negocio asociada** | RN-05: un producto no puede pertenecer a una categoría inexistente o inactiva (los atributos solo se asignan a categorías vigentes) |
| **APIs** | API-G24 (agregada en el Parcial 2) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 12 |
| **Depende de** | HU-11 |
| **Actor** | Administrador de la plataforma |

## 📖 Historia de Usuario

**Dado** que soy el administrador de la plataforma y existe una categoría,
**Para** definir las características propias de los productos de esa categoría (talla, color, material),
**Que** necesito asignar atributos personalizados a la categoría, de modo que los vendedores describan sus productos y variantes de forma uniforme y los compradores puedan filtrarlos.

## 🔁 Flujo Esperado

- El administrador selecciona una categoría y define la lista de atributos: nombre, tipo, si es obligatorio y los valores permitidos.
- El sistema consume el endpoint `PUT /api/v1/catalogo/categorias/{id}/atributos`.
- El backend valida que la categoría exista y esté `ACTIVA` y que los atributos no se repitan.
- El backend guarda la definición de atributos de la categoría y retorna el resultado.
- Las subcategorías heredan los atributos de su categoría padre.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `PUT` que reemplaza la lista de atributos de la categoría.
- [ ] Cada atributo tiene `nombre`, `tipo` (`TEXTO`, `NUMERO` o `LISTA`), `obligatorio` y, si es `LISTA`, `valores_permitidos`.
- [ ] No se permiten dos atributos con el mismo nombre en la categoría (ni con uno heredado del padre).
- [ ] Un atributo de tipo `LISTA` debe tener al menos un valor permitido.
- [ ] No se puede retirar un atributo que ya esté en uso en variantes de productos de la categoría.
- [ ] Solo se asignan atributos a categorías `ACTIVA` (RN-05).
- [ ] La operación está permitida solo al rol Administrador.

### 2. 📆 Estructura de la información

- [ ] Asignación exitosa:

```json
{
  "mensaje": "Atributos asignados exitosamente",
  "data": {
    "categoria_id": 12,
    "atributos": [
      { "nombre": "Talla", "tipo": "LISTA", "obligatorio": true, "valores_permitidos": ["S", "M", "L"] },
      { "nombre": "Color", "tipo": "TEXTO", "obligatorio": true }
    ]
  },
  "success": true
}
```

- [ ] Atributo en uso:

```json
{
  "mensaje": "No es posible retirar el atributo Talla porque está en uso en variantes existentes",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoint – Atributos de categoría

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Asignar atributos a categoría | API-G24 | `PUT` | `/api/v1/catalogo/categorias/{id}/atributos` | Agregada en el Parcial 2 |

### 📥 Entradas

| Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `id` | ruta | entero | Sí | Identificador de la categoría |
| `atributos` | body | arreglo | Sí | Lista completa de atributos de la categoría |
| `atributos[].nombre` | body | texto | Sí | Nombre del atributo |
| `atributos[].tipo` | body | texto | Sí | `TEXTO`, `NUMERO` o `LISTA` |
| `atributos[].obligatorio` | body | booleano | Sí | Si debe diligenciarse en cada variante |
| `atributos[].valores_permitidos` | body | arreglo | Condicional | Obligatorio si el tipo es `LISTA` |

### 📤 Salidas

| Código HTTP | Contenido de `data` |
|---|---|
| `200 OK` | Categoría con su lista de atributos |

### 📤 Ejemplo de comunicación – Petición

```json
{
  "atributos": [
    { "nombre": "Talla", "tipo": "LISTA", "obligatorio": true, "valores_permitidos": ["S", "M", "L"] },
    { "nombre": "Color", "tipo": "TEXTO", "obligatorio": true }
  ]
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Asignar atributos a una categoría activa

- **Precondición:** La categoría `id = 12` existe y está `ACTIVA`.
- **Acción:** Ejecutar `PUT /api/v1/catalogo/categorias/12/atributos` con los atributos Talla y Color.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - La respuesta lista los atributos asignados

### ✅ Caso 2: Las subcategorías heredan los atributos

- **Precondición:** La categoría padre tiene atributos asignados.
- **Acción:** Consultar los atributos de una subcategoría.
- **Resultado esperado:**
  - La subcategoría incluye los atributos del padre

### ❌ Caso 3: Atributo duplicado

- **Precondición:** Ninguna.
- **Acción:** Ejecutar el `PUT` con dos atributos llamados "Color".
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "Existen atributos con el mismo nombre"

### ❌ Caso 4: Atributo de tipo LISTA sin valores

- **Precondición:** Ninguna.
- **Acción:** Ejecutar el `PUT` con un atributo `LISTA` y `valores_permitidos` vacío.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "Un atributo de tipo lista debe tener al menos un valor permitido"

### ❌ Caso 5: Retirar un atributo en uso

- **Precondición:** Existen variantes que usan el atributo "Talla".
- **Acción:** Ejecutar el `PUT` sin "Talla".
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "No es posible retirar el atributo Talla porque está en uso en variantes existentes"

### ❌ Caso 6: Categoría inactiva o inexistente (RN-05)

- **Precondición:** La categoría no existe (`id = 99999`) o está inactiva.
- **Acción:** Ejecutar el `PUT`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found` si no existe, o `409 Conflict` si está inactiva
  - Campo `mensaje` indica la causa

### ❌ Caso 7: Usuario sin permisos

- **Precondición:** El usuario no es Administrador.
- **Acción:** Ejecutar el `PUT`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`

### ❌ Caso 8: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar el endpoint bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible asignar los atributos"

## ✅ Definición de Hecho

# Historia: Asignar atributos personalizados a categorías

## 📦 Alcance Funcional

- [ ] El endpoint asigna atributos solo a categorías activas y valida duplicados y tipos.
- [ ] No se retiran atributos en uso.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de atributos, herencia y uso.
- [ ] Se cubrieron los casos de error.
- [ ] Las pruebas funcionales de los 8 casos están documentadas y pasadas.

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
