# [HU-06] Publicar valor paramétrico para otros módulos

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-01 Parametrización / SUB-03 Catálogos Transaccionales |
| **Funcionalidad que cubre** | FUN-15 Publicar valor paramétrico para consumo |
| **Regla de negocio asociada** | RN-49: un valor paramétrico inactivo no puede ser consumido por otros módulos |
| **APIs** | API-G13 (agregada en el Parcial 2) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 6 |
| **Depende de** | HU-03 |
| **Actor** | Administrador de la plataforma |

## 📖 Historia de Usuario

**Dado** que soy el administrador de la plataforma y registré un valor paramétrico (estado, moneda, unidad de medida o método de pago),
**Para** habilitarlo como dato oficial que usan los demás módulos,
**Que** necesito publicar el valor, de modo que Pedidos, Pagos, Envíos y los demás módulos solo consuman datos maestros revisados y vigentes.

## 🔁 Flujo Esperado

- El administrador selecciona un valor paramétrico registrado.
- El sistema consume el endpoint `PATCH /api/v1/parametrizacion/valores/{id}/publicar`.
- El backend valida que el valor exista y esté `ACTIVO`.
- El backend lo marca como `publicado = true` y lo expone para consumo de otros módulos.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `PATCH` con el `id` del valor en la ruta.
- [ ] Se valida que el valor exista y esté `ACTIVO` (RN-49).
- [ ] La publicación es idempotente: publicar un valor ya publicado retorna `200` sin cambios.
- [ ] Los demás módulos consumen únicamente valores `ACTIVO` y `publicado = true`.
- [ ] La operación está permitida solo al rol Administrador.

### 2. 📆 Estructura de la información

- [ ] Publicación exitosa:

```json
{
  "mensaje": "Valor paramétrico publicado exitosamente",
  "data": {
    "id": 31,
    "categoria": "METODO_PAGO",
    "codigo": "PSE",
    "estado": "ACTIVO",
    "publicado": true
  },
  "success": true
}
```

- [ ] Si el valor está inactivo:

```json
{
  "mensaje": "No es posible publicar un valor paramétrico inactivo",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoint – Publicar valor

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Publicar valor paramétrico | API-G13 | `PATCH` | `/api/v1/parametrizacion/valores/{id}/publicar` | Agregada en el Parcial 2 |

### 📥 Entradas

| Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `id` | ruta | entero | Sí | Identificador del valor a publicar |

### 📤 Salidas

| Código HTTP | Contenido de `data` |
|---|---|
| `200 OK` | Valor con `publicado = true` |

Nota: esta historia agrega el campo `publicado` (booleano, `false` por defecto al registrar) a la entidad definida en HU-03. El listado de HU-03 para los administradores sigue mostrando todos los valores activos.

### 📤 Ejemplo de comunicación

Petición: `PATCH /api/v1/parametrizacion/valores/31/publicar` (sin cuerpo).

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Publicar un valor activo

- **Precondición:** El valor existe y está `ACTIVO`.
- **Acción:** Ejecutar `PATCH /api/v1/parametrizacion/valores/31/publicar`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `publicado` = `true`

### ✅ Caso 2: Publicar un valor ya publicado

- **Precondición:** El valor ya tiene `publicado = true`.
- **Acción:** Ejecutar el mismo `PATCH`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - El valor no cambia

### ✅ Caso 3: Consumo solo de valores publicados

- **Precondición:** Existen valores publicados y no publicados.
- **Acción:** Un módulo consulta los valores de una categoría para consumirlos.
- **Resultado esperado:**
  - Solo recibe valores `ACTIVO` y `publicado = true`

### ❌ Caso 4: Valor inactivo (RN-49)

- **Precondición:** El valor tiene `estado = INACTIVO`.
- **Acción:** Ejecutar `PATCH .../publicar`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "No es posible publicar un valor paramétrico inactivo"

### ❌ Caso 5: Valor inexistente

- **Precondición:** No existe el `id = 99999`.
- **Acción:** Ejecutar `PATCH /api/v1/parametrizacion/valores/99999/publicar`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "El valor paramétrico no existe"

### ❌ Caso 6: Usuario sin permisos

- **Precondición:** El usuario no es Administrador.
- **Acción:** Ejecutar `PATCH .../publicar`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`

### ❌ Caso 7: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar el endpoint bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible publicar el valor paramétrico"

## ✅ Definición de Hecho

# Historia: Publicar valor paramétrico para otros módulos

## 📦 Alcance Funcional

- [ ] El endpoint publica el valor solo si existe y está activo.
- [ ] Los demás módulos consumen únicamente valores activos y publicados (RN-49).
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de la regla de publicación y de la idempotencia.
- [ ] Se cubrieron los casos de error.
- [ ] Las pruebas funcionales de los 7 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoint documentado en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito del endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error

## 🔐 Manejo de Errores

- [ ] Se devuelve `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
