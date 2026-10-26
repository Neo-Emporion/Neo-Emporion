# [HU-04] Publicar dato geográfico para otros módulos

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-01 Parametrización / SUB-02 Catálogos Geográficos |
| **Funcionalidad que cubre** | FUN-10 Publicar dato geográfico para consumo |
| **Regla de negocio asociada** | RN-47: un dato geográfico no puede desactivarse si existen direcciones activas asociadas (una ubicación publicada ya puede estar en uso) |
| **APIs** | API-G04 (agregada en el Parcial 2) · API-I09 Consultar Catálogo Geográfico (inventario inicial, la consumen otros módulos) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 4 |
| **Depende de** | HU-01 |
| **Actor** | Administrador de la plataforma |

## 📖 Historia de Usuario

**Dado** que soy el administrador de la plataforma y ya registré una ubicación en el catálogo geográfico,
**Para** habilitarla como dato oficial que consumen los demás módulos,
**Que** necesito publicar la ubicación, de modo que las direcciones de envío, los perfiles de vendedor y las zonas de cobertura solo puedan usar ubicaciones revisadas y vigentes.

## 🔁 Flujo Esperado

- El administrador selecciona una ubicación registrada.
- El sistema consume el endpoint `PATCH /api/v1/parametrizacion/ubicaciones/{id}/publicar`.
- El backend valida que la ubicación exista, esté `ACTIVO` y tenga su jerarquía completa (por ejemplo, una ciudad con departamento padre publicado).
- El backend marca la ubicación como `publicada = true`.
- A partir de ese momento, la API-I09 (Consultar Catálogo Geográfico) la incluye en las respuestas a los demás módulos.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `PATCH` con el `id` de la ubicación en la ruta.
- [ ] Se valida que la ubicación exista y esté `ACTIVO`.
- [ ] Se valida que el padre de la ubicación (departamento o país) ya esté publicado.
- [ ] La publicación es idempotente: publicar una ubicación ya publicada retorna `200` sin cambios.
- [ ] La API-I09 retorna a los demás módulos únicamente ubicaciones `ACTIVO` y `publicada = true`.
- [ ] La operación está permitida solo al rol Administrador.

### 2. 📆 Estructura de la información

- [ ] Publicación exitosa:

```json
{
  "mensaje": "Ubicación publicada exitosamente",
  "data": {
    "id": 1203,
    "nombre": "Bucaramanga",
    "estado": "ACTIVO",
    "publicada": true
  },
  "success": true
}
```

- [ ] Si el padre no está publicado:

```json
{
  "mensaje": "No es posible publicar la ubicación porque su ubicación padre no está publicada",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoint – Publicar ubicación

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Publicar ubicación | API-G04 | `PATCH` | `/api/v1/parametrizacion/ubicaciones/{id}/publicar` | Agregada en el Parcial 2 |

### 📥 Entradas

| Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|
| `id` | ruta | entero | Sí | Identificador de la ubicación a publicar |

### 📤 Salidas

| Código HTTP | Contenido de `data` |
|---|---|
| `200 OK` | Ubicación con `publicada = true` |

Nota: esta historia agrega el campo `publicada` (booleano, `false` por defecto al registrar) a la entidad de ubicación definida en HU-01.

### 📤 Ejemplo de comunicación – Consumo por otro módulo

Petición del módulo Usuarios: `GET /api/v1/parametrizacion/ubicaciones?tipo=CIUDAD&padre_id=68` (API-I09)

```json
{
  "mensaje": "Consulta de ubicaciones exitosa",
  "data": { "pagina": 1, "tamano": 20, "total": 1, "ubicaciones": [ { "id": 1203, "tipo": "CIUDAD", "nombre": "Bucaramanga", "codigo": "68001", "padre_id": 68, "estado": "ACTIVO" } ] },
  "success": true
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Publicar una ubicación válida

- **Precondición:** La ciudad existe, está `ACTIVO` y su departamento ya está publicado.
- **Acción:** Ejecutar `PATCH /api/v1/parametrizacion/ubicaciones/1203/publicar`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `publicada` = `true`

### ✅ Caso 2: Publicar una ubicación ya publicada

- **Precondición:** La ubicación ya tiene `publicada = true`.
- **Acción:** Ejecutar el mismo `PATCH`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - La ubicación no cambia

### ✅ Caso 3: Consumo solo de ubicaciones publicadas

- **Precondición:** Existen ubicaciones publicadas y no publicadas.
- **Acción:** Un módulo consulta `GET /api/v1/parametrizacion/ubicaciones` (API-I09).
- **Resultado esperado:**
  - Solo se retornan ubicaciones con `estado = ACTIVO` y `publicada = true`

### ❌ Caso 4: Padre no publicado

- **Precondición:** El departamento padre no está publicado.
- **Acción:** Ejecutar `PATCH` sobre una ciudad de ese departamento.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "No es posible publicar la ubicación porque su ubicación padre no está publicada"

### ❌ Caso 5: Ubicación inactiva

- **Precondición:** La ubicación tiene `estado = INACTIVO`.
- **Acción:** Ejecutar `PATCH .../publicar`.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "No es posible publicar una ubicación inactiva"

### ❌ Caso 6: Ubicación inexistente

- **Precondición:** No existe el `id = 99999`.
- **Acción:** Ejecutar `PATCH /api/v1/parametrizacion/ubicaciones/99999/publicar`.
- **Resultado esperado:**
  - Código HTTP `404 Not Found`
  - Campo `mensaje` contiene el texto: "La ubicación no existe"

### ❌ Caso 7: Usuario sin permisos

- **Precondición:** El usuario no es Administrador.
- **Acción:** Ejecutar `PATCH .../publicar`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`

### ❌ Caso 8: Falla de base de datos

- **Precondición:** La base de datos no está disponible.
- **Acción:** Ejecutar el endpoint bajo condiciones simuladas de fallo.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible publicar la ubicación"

## ✅ Definición de Hecho

# Historia: Publicar dato geográfico para otros módulos

## 📦 Alcance Funcional

- [ ] El endpoint publica la ubicación solo si cumple las validaciones (existe, activa y con padre publicado).
- [ ] La API-I09 retorna a los demás módulos únicamente ubicaciones activas y publicadas.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de la regla de publicación y de la idempotencia.
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

- [ ] Se devuelve `403`, `404` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
