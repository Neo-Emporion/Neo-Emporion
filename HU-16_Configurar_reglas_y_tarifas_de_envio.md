# [HU-16] Configurar reglas y tarifas de envío

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-07 Envíos y Logística / SUB-19 Cotización de Envío |
| **Funcionalidades que cubre** | FUN-94 Configurar reglas de cotización · FUN-95 Actualizar tarifas de envío |
| **Regla de negocio asociada** | RN-23: el costo de envío no puede ser inferior al mínimo definido por la transportadora |
| **APIs** | API-G53, API-G54 (agregadas en el Parcial 2) · apoya a API-I03 Cotizar Envío y a la API externa API-E03 Transportadora (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 16 |
| **Depende de** | HU-03, HU-04 |
| **Actor** | Administrador de la plataforma |

## 📖 Historia de Usuario

**Dado** que soy el administrador de la plataforma,
**Para** controlar cómo se calculan los costos de envío,
**Que** necesito configurar las reglas de cotización (peso máximo, zonas excluidas) y actualizar las tarifas informadas por las transportadoras, de modo que las cotizaciones que ven los compradores sean correctas y respeten los mínimos pactados con cada transportadora.

## 🔁 Flujo Esperado

**Configurar reglas de cotización**
- El administrador define el peso máximo por envío y las zonas excluidas (ubicaciones del catálogo geográfico).
- El sistema consume `PUT /api/v1/envios/reglas-cotizacion`.
- El backend valida los valores y las ubicaciones, y guarda la configuración.

**Actualizar tarifas de envío**
- El administrador registra los cambios de tarifa informados por una transportadora: zona, rango de peso, valor, costo mínimo y tiempo estimado.
- El sistema consume `PUT /api/v1/envios/tarifas`.
- El backend valida que ningún valor sea inferior al mínimo de la transportadora (RN-23) y actualiza las tarifas.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `PUT` de reglas con `peso_maximo_kg` y `zonas_excluidas` (lista de `ubicacion_id`).
- [ ] `peso_maximo_kg` debe ser mayor que cero y las zonas excluidas deben existir en el catálogo geográfico.
- [ ] Se expone un endpoint `PUT` de tarifas con `transportadora`, `zona_id`, rangos de peso, `valor`, `costo_minimo` y `tiempo_estimado_dias`.
- [ ] Ninguna tarifa puede tener `valor` inferior a `costo_minimo` de la transportadora (RN-23).
- [ ] Los rangos de peso de una misma zona y transportadora no pueden superponerse.
- [ ] Las tarifas actualizadas se aplican a las cotizaciones nuevas; las cotizaciones ya generadas no cambian.
- [ ] Las operaciones están permitidas solo al rol Administrador.

### 2. 📆 Estructura de la información

- [ ] Reglas configuradas:

```json
{
  "mensaje": "Reglas de cotización configuradas exitosamente",
  "data": { "peso_maximo_kg": 30, "zonas_excluidas": [2210, 2215] },
  "success": true
}
```

- [ ] Tarifas actualizadas:

```json
{
  "mensaje": "Tarifas de envío actualizadas exitosamente",
  "data": { "transportadora": "Servientrega", "tarifas_actualizadas": 3 },
  "success": true
}
```

- [ ] Tarifa por debajo del mínimo:

```json
{
  "mensaje": "El valor de la tarifa no puede ser inferior al costo mínimo de la transportadora",
  "data": null,
  "success": false
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Reglas y tarifas

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Configurar reglas de cotización | API-G53 | `PUT` | `/api/v1/envios/reglas-cotizacion` | Agregada en el Parcial 2 |
| Actualizar tarifas de envío | API-G54 | `PUT` | `/api/v1/envios/tarifas` | Agregada en el Parcial 2 |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Reglas | `peso_maximo_kg` | body | decimal | Sí | Peso máximo permitido por envío |
| Reglas | `zonas_excluidas` | body | arreglo de enteros | No | Ubicaciones sin cobertura de envío |
| Tarifas | `transportadora` | body | texto | Sí | Nombre de la transportadora |
| Tarifas | `tarifas[].zona_id` | body | entero | Sí | Ubicación de destino |
| Tarifas | `tarifas[].peso_desde_kg`, `peso_hasta_kg` | body | decimal | Sí | Rango de peso |
| Tarifas | `tarifas[].valor` | body | decimal | Sí | Valor del envío para ese rango |
| Tarifas | `tarifas[].costo_minimo` | body | decimal | Sí | Costo mínimo definido por la transportadora |
| Tarifas | `tarifas[].tiempo_estimado_dias` | body | entero | Sí | Tiempo estimado de entrega |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Reglas | `200 OK` | Configuración vigente |
| Tarifas | `200 OK` | Transportadora y cantidad de tarifas actualizadas |

### 📤 Ejemplo de comunicación – Petición de tarifas

```json
{
  "transportadora": "Servientrega",
  "tarifas": [
    { "zona_id": 1203, "peso_desde_kg": 0, "peso_hasta_kg": 5, "valor": 12000, "costo_minimo": 9000, "tiempo_estimado_dias": 3 }
  ]
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Configurar reglas válidas

- **Precondición:** Las ubicaciones excluidas existen.
- **Acción:** Ejecutar `PUT /api/v1/envios/reglas-cotizacion` con `peso_maximo_kg = 30`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - La configuración queda vigente para nuevas cotizaciones

### ✅ Caso 2: Actualizar tarifas válidas

- **Precondición:** Los valores son mayores o iguales al costo mínimo y los rangos no se superponen.
- **Acción:** Ejecutar `PUT /api/v1/envios/tarifas` con tarifas válidas.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - Campo `tarifas_actualizadas` indica la cantidad actualizada

### ❌ Caso 3: Peso máximo inválido

- **Precondición:** Ninguna.
- **Acción:** Ejecutar el `PUT` de reglas con `peso_maximo_kg = 0`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El peso máximo debe ser mayor que cero"

### ❌ Caso 4: Zona excluida inexistente

- **Precondición:** La ubicación no existe.
- **Acción:** Ejecutar el `PUT` de reglas con ese `ubicacion_id`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "Una de las zonas indicadas no existe"

### ❌ Caso 5: Tarifa por debajo del costo mínimo (RN-23)

- **Precondición:** `costo_minimo = 9000`.
- **Acción:** Ejecutar el `PUT` de tarifas con `valor = 7000`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El valor de la tarifa no puede ser inferior al costo mínimo de la transportadora"

### ❌ Caso 6: Rangos de peso superpuestos

- **Precondición:** Dos rangos de la misma zona y transportadora se cruzan (0–5 y 3–8).
- **Acción:** Ejecutar el `PUT` de tarifas.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "Los rangos de peso de una misma zona no pueden superponerse"

### ❌ Caso 7: Transportadora no reconocida

- **Precondición:** La transportadora no está configurada en el sistema.
- **Acción:** Ejecutar el `PUT` de tarifas con `transportadora = "Desconocida"`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "La transportadora indicada no es válida"

### ❌ Caso 8: Usuario sin permisos

- **Precondición:** El usuario no es Administrador.
- **Acción:** Ejecutar cualquiera de los `PUT`.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`

### ❌ Caso 9: Falla de base de datos o de Parametrización

- **Precondición:** La base de datos o el catálogo geográfico no está disponible.
- **Acción:** Ejecutar cualquiera de los endpoints.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible guardar la configuración de envíos"

## ✅ Definición de Hecho

# Historia: Configurar reglas y tarifas de envío

## 📦 Alcance Funcional

- [ ] Ambos endpoints funcionan según lo definido.
- [ ] Se aplica RN-23 y se validan los rangos de peso y las zonas.
- [ ] Las tarifas nuevas se aplican a cotizaciones futuras sin alterar las ya generadas.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (mínimo, rangos y zonas).
- [ ] Se cubrieron los casos de error.
- [ ] Las pruebas funcionales de los 9 casos están documentadas y pasadas.

## 📄 Documentación Técnica

- [ ] Endpoints documentados en Swagger / OpenAPI.
- [ ] Se describe:
  - Propósito de cada endpoint
  - Campos de entrada y salida
  - Ejemplo de respuesta exitosa
  - Ejemplo de error

## 🔐 Manejo de Errores

- [ ] Se devuelve `400` y `403` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro para el usuario técnico o frontend.
