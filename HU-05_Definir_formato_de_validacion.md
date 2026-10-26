# [HU-05] Definir formato de validación de tipo de documento

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-01 Parametrización / SUB-01 Catálogos de Identificación |
| **Funcionalidad que cubre** | FUN-04 Definir formato de validación |
| **Regla de negocio asociada** | RN-50: el formato de validación de un tipo de documento no puede modificarse si ya existen registros asociados |
| **APIs** | API-G08 (agregada en el Parcial 2) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 5 |
| **Depende de** | HU-02 |
| **Actor** | Administrador de la plataforma |

## 📖 Historia de Usuario

**Dado** que soy el administrador de la plataforma y existe un tipo de documento registrado,
**Para** establecer el patrón que debe cumplir cada número de documento,
**Que** necesito definir el formato de validación de cada tipo (por ejemplo, el NIT con 9 dígitos más dígito de verificación), de modo que los registros de compradores y vendedores rechacen números de documento mal escritos.

## 🔁 Flujo Esperado

- El administrador selecciona un tipo de documento y define el patrón (expresión regular), la longitud mínima y máxima, y un ejemplo.
- El sistema consume el endpoint `PUT /api/v1/parametrizacion/tipos-documento/{id}/formato`.
- El backend valida que el patrón sea consistente (que se pueda evaluar y que sea coherente con las longitudes).
- El backend valida que no existan registros asociados al tipo (RN-50) si ya había un formato definido.
- El backend asocia el formato al tipo de documento y retorna el resultado.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `PUT` con `patron`, `longitud_min`, `longitud_max` y `ejemplo`.
- [ ] Se valida que `patron` sea una expresión regular válida y que `ejemplo` la cumpla.
- [ ] Se valida que `longitud_min` sea mayor que 0 y menor o igual que `longitud_max`.
- [ ] Si el tipo ya tiene un formato definido y existen compradores o vendedores registrados con ese tipo, no se permite modificarlo (RN-50).
- [ ] Un tipo de documento `INACTIVO` no admite definir formato.
- [ ] La operación está permitida solo al rol Administrador.

### 2. 📆 Estructura de la información

- [ ] Definición exitosa:

```json
{
  "mensaje": "Formato de validación definido exitosamente",
  "data": {
    "id": 4,
    "codigo": "NIT",
    "formato": {
      "patron": "^[0-9]{9}-[0-9]$",
      "longitud_min": 11,
      "longitud_max": 11,
      "ejemplo": "900123456-7"
    }
  },
  "success": true
}
```

- [ ] Si ya existen registros asociados:

```json
{
  "mensaje": "No es posible modificar el formato porque existen registros asociados al tipo de documento",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoint – Definir formato

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Definir formato de validación | API-G08 | `PUT` | `/api/v1/parametrizacion/tipos-documento/{id}/formato` | Agregada en el Parcial 2 |

### 📥 Entradas

| Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `id` | ruta | entero | Sí | Identificador del tipo de documento |
| `patron` | body | texto | Sí | Expresión regular que valida el número |
| `longitud_min` | body | entero | Sí | Longitud mínima del número |
| `longitud_max` | body | entero | Sí | Longitud máxima del número |
| `ejemplo` | body | texto | Sí | Ejemplo válido para mostrar al usuario |

### 📤 Salidas

| Código HTTP | Contenido de `data` |
|---|---|
| `200 OK` | Tipo de documento con su formato asociado |

### 📤 Ejemplo de comunicación – Petición

```json
{
  "patron": "^[0-9]{9}-[0-9]$",
  "longitud_min": 11,
  "longitud_max": 11,
  "ejemplo": "900123456-7"
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Definir el formato de un tipo sin registros

- **Precondición:** El tipo `NIT` está `ACTIVO` y no tiene registros asociados.
- **Acción:** Ejecutar `PUT /api/v1/parametrizacion/tipos-documento/4/formato` con un patrón válido.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El formato queda asociado al tipo
  - Campo `mensaje` contiene el texto: "Formato de validación definido exitosamente"

### ✅ Caso 2: Los registros usan el formato definido

- **Precondición:** El tipo `NIT` tiene formato definido.
- **Acción:** Registrar un vendedor con el número `900123456-7`.
- **Resultado esperado:**
  - El número es aceptado por cumplir el patrón

### ❌ Caso 3: Patrón inválido

- **Precondición:** El tipo existe y está `ACTIVO`.
- **Acción:** Ejecutar el `PUT` con `patron = "[0-9{"`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El patrón de validación no es válido"

### ❌ Caso 4: Ejemplo que no cumple el patrón

- **Precondición:** El tipo existe y está `ACTIVO`.
- **Acción:** Ejecutar el `PUT` con un `ejemplo` que no cumple el `patron`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El ejemplo no cumple el patrón definido"

### ❌ Caso 5: Longitudes inconsistentes

- **Precondición:** El tipo existe y está `ACTIVO`.
- **Acción:** Ejecutar el `PUT` con `longitud_min = 12` y `longitud_max = 8`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "La longitud mínima no puede ser mayor que la máxima"

### ❌ Caso 6: Modificar formato con registros asociados (RN-50)

- **Precondición:** El tipo ya tiene formato y existen compradores o vendedores con ese tipo.
- **Acción:** Ejecutar el `PUT` con un formato distinto.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - El formato anterior se conserva
  - Campo `mensaje` contiene el texto: "No es posible modificar el formato porque existen registros asociados al tipo de documento"

### ❌ Caso 7: Tipo inexistente o inactivo

- **Precondición:** El tipo no existe (`id = 99999`) o está `INACTIVO`.
- **Acción:** Ejecutar el `PUT` sobre ese tipo.
- **Resultado esperado:**
  - Código HTTP `404 Not Found` si no existe, o `409 Conflict` si está inactivo
  - Campo `mensaje` indica la causa

### ❌ Caso 8: Usuario sin permisos

- **Precondición:** El usuario no es Administrador.
- **Acción:** Ejecutar el `PUT`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`

### ❌ Caso 9: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar el endpoint bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible definir el formato de validación"

## ✅ Definición de Hecho

# Historia: Definir formato de validación de tipo de documento

## 📦 Alcance Funcional

- [ ] El endpoint valida el patrón, las longitudes y el ejemplo antes de guardar el formato.
- [ ] Se respeta RN-50: no se modifica un formato con registros asociados.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de la validación del patrón, de las longitudes y de RN-50.
- [ ] Se cubrieron los casos de error.
- [ ] Las pruebas funcionales de los 9 casos están documentadas y pasadas.

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
