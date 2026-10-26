# [HU-07] Registrar e iniciar sesión como comprador

| Campo | Detalle |
|---|---|
| **Módulo / Submódulo** | MOD-02 Usuarios y Compradores / SUB-04 Registro y Autenticación |
| **Funcionalidades que cubre** | FUN-16 Registrar comprador · FUN-17 Iniciar sesión |
| **Reglas de negocio asociadas** | RN-51: no se puede registrar un comprador con un correo ya existente · RN-52: una cuenta desactivada no puede iniciar sesión · RN-55: la contraseña debe cumplir los requisitos mínimos de seguridad antes de almacenarse |
| **APIs** | API-G14, API-G15 (agregadas en el Parcial 2) · consume API-I08 Consultar Tipos de Documento (inventario inicial) |
| **Prioridad** | Crítica |
| **Orden de construcción** | 7 |
| **Depende de** | HU-02, HU-05 |
| **Actor** | Comprador |

## 📖 Historia de Usuario

**Dado** que soy una persona que quiere comprar en la plataforma,
**Para** tener una cuenta propia y acceder a ella de forma segura,
**Que** necesito registrarme con mis datos e iniciar sesión con mi correo y contraseña, de modo que pueda usar el carrito, hacer pedidos y consultar mis compras.

## 🔁 Flujo Esperado

**Registrar comprador**
- El comprador ingresa su tipo y número de documento, nombres, correo y contraseña.
- El sistema consume `POST /api/v1/usuarios/compradores`.
- El backend valida el número de documento contra el formato del tipo (consulta API-I08), que el correo no exista (RN-51) y que la contraseña cumpla los requisitos (RN-55).
- El backend almacena la contraseña cifrada, crea la cuenta en estado `ACTIVA` y retorna el comprador.

**Iniciar sesión**
- El comprador ingresa su correo y contraseña.
- El sistema consume `POST /api/v1/usuarios/sesiones`.
- El backend valida las credenciales y que la cuenta esté `ACTIVA` (RN-52).
- El backend retorna un token de acceso con su fecha de expiración.

## ✅ Criterios de Aceptación

### 1. 🔍 Estructura y lógica del servicio

- [ ] Se expone un endpoint `POST` de registro con `tipo_documento_id`, `numero_documento`, `nombres`, `apellidos`, `correo` y `contrasena`.
- [ ] El número de documento se valida con el formato del tipo (patrón y longitudes) definido en HU-05.
- [ ] Se valida que el correo no esté registrado (RN-51).
- [ ] Se valida que la contraseña tenga mínimo 8 caracteres, con mayúscula, minúscula y número (RN-55).
- [ ] La contraseña se almacena cifrada y nunca se retorna en las respuestas.
- [ ] Se expone un endpoint `POST` de inicio de sesión con `correo` y `contrasena`.
- [ ] Una cuenta `DESACTIVADA` no puede iniciar sesión (RN-52).
- [ ] Ante credenciales incorrectas se retorna un mensaje genérico, sin indicar si falló el correo o la contraseña.

### 2. 📆 Estructura de la información

- [ ] Registro exitoso:

```json
{
  "mensaje": "Comprador registrado exitosamente",
  "data": {
    "id": 5021,
    "nombres": "Laura",
    "apellidos": "Gómez",
    "correo": "laura.gomez@correo.com",
    "estado": "ACTIVA"
  },
  "success": true
}
```

- [ ] Inicio de sesión exitoso:

```json
{
  "mensaje": "Inicio de sesión exitoso",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "tipo": "Bearer",
    "expira_en": 3600
  },
  "success": true
}
```

## 🔧 Notas Técnicas

### 🚀 Endpoints – Registro y autenticación

| Operación | ID de la API | Método HTTP | Ruta | Origen en el inventario |
|---|---|---|---|---|
| Registrar comprador | API-G14 | `POST` | `/api/v1/usuarios/compradores` | Agregada en el Parcial 2 |
| Iniciar sesión | API-G15 | `POST` | `/api/v1/usuarios/sesiones` | Agregada en el Parcial 2 |
| (Consumida) Consultar tipos de documento | API-I08 | `GET` | `/api/v1/parametrizacion/tipos-documento` | Inventario inicial (API interna) |

### 📥 Entradas

| Operación | Parámetro | Ubicación | Tipo | Obligatorio | Descripción |
|---|---|---|---|---|---|
| Registrar | `tipo_documento_id` | body | entero | Sí | Tipo de documento activo |
| Registrar | `numero_documento` | body | texto | Sí | Número que cumple el formato del tipo |
| Registrar | `nombres`, `apellidos` | body | texto | Sí | Datos del comprador |
| Registrar | `correo` | body | texto | Sí | Correo único con formato válido |
| Registrar | `contrasena` | body | texto | Sí | Cumple requisitos mínimos de seguridad |
| Iniciar sesión | `correo` | body | texto | Sí | Correo registrado |
| Iniciar sesión | `contrasena` | body | texto | Sí | Contraseña de la cuenta |

### 📤 Salidas

| Operación | Código HTTP exitoso | Contenido de `data` |
|---|---|---|
| Registrar | `201 Created` | Comprador creado (sin contraseña) |
| Iniciar sesión | `200 OK` | `token`, `tipo` y `expira_en` (segundos) |

### 📤 Ejemplo de comunicación – Error de credenciales

```json
{
  "mensaje": "Correo o contraseña incorrectos",
  "data": null,
  "success": false
}
```

## 🧪 Requisitos de Pruebas

## 🔍 Casos de Prueba Funcional

### ✅ Caso 1: Registrar un comprador válido

- **Precondición:** El correo no existe y el documento cumple el formato del tipo.
- **Acción:** Ejecutar `POST /api/v1/usuarios/compradores` con datos válidos.
- **Resultado esperado:**
  - Código HTTP `201 Created`
  - Campo `estado` = `ACTIVA`
  - La respuesta no incluye la contraseña

### ✅ Caso 2: Iniciar sesión con credenciales correctas

- **Precondición:** Existe una cuenta `ACTIVA` con ese correo y contraseña.
- **Acción:** Ejecutar `POST /api/v1/usuarios/sesiones`.
- **Resultado esperado:**
  - Código HTTP `200 OK`
  - La respuesta incluye `token` y `expira_en`

### ❌ Caso 3: Correo ya registrado (RN-51)

- **Precondición:** Ya existe un comprador con el correo indicado.
- **Acción:** Ejecutar `POST /api/v1/usuarios/compradores` con ese correo.
- **Resultado esperado:**
  - Código HTTP `409 Conflict`
  - Campo `mensaje` contiene el texto: "Ya existe una cuenta registrada con ese correo"

### ❌ Caso 4: Contraseña que no cumple los requisitos (RN-55)

- **Precondición:** Datos válidos, contraseña `abc123`.
- **Acción:** Ejecutar `POST /api/v1/usuarios/compradores`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "La contraseña no cumple los requisitos mínimos de seguridad"

### ❌ Caso 5: Documento que no cumple el formato

- **Precondición:** El tipo de documento tiene un formato definido.
- **Acción:** Ejecutar el registro con un `numero_documento` que no cumple el patrón.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El número de documento no cumple el formato del tipo seleccionado"

### ❌ Caso 6: Datos obligatorios faltantes

- **Precondición:** Ninguna.
- **Acción:** Ejecutar el registro sin el campo `correo`.
- **Resultado esperado:**
  - Código HTTP `400 Bad Request`
  - Campo `mensaje` contiene el texto: "El campo correo es obligatorio"

### ❌ Caso 7: Credenciales incorrectas

- **Precondición:** Existe la cuenta, pero la contraseña enviada es incorrecta.
- **Acción:** Ejecutar `POST /api/v1/usuarios/sesiones`.
- **Resultado esperado:**
  - Código HTTP `401 Unauthorized`
  - Campo `mensaje` contiene el texto: "Correo o contraseña incorrectos"

### ❌ Caso 8: Cuenta desactivada (RN-52)

- **Precondición:** La cuenta tiene `estado = DESACTIVADA`.
- **Acción:** Ejecutar `POST /api/v1/usuarios/sesiones` con credenciales correctas.
- **Resultado esperado:**
  - Código HTTP `403 Forbidden`
  - Campo `mensaje` contiene el texto: "La cuenta se encuentra desactivada"

### ❌ Caso 9: Falla de base de datos o del módulo Parametrización

- **Precondición:** La base de datos o la consulta de tipos de documento no está disponible.
- **Acción:** Ejecutar el registro o el inicio de sesión.
- **Resultado esperado:**
  - Código HTTP `503 Service Unavailable`
  - Campo `mensaje` contiene el texto: "No fue posible procesar la solicitud en este momento"

## ✅ Definición de Hecho

# Historia: Registrar e iniciar sesión como comprador

## 📦 Alcance Funcional

- [ ] El registro y el inicio de sesión funcionan según lo definido.
- [ ] Se aplican las reglas RN-51, RN-52 y RN-55.
- [ ] La contraseña se almacena cifrada y no se expone en ninguna respuesta.
- [ ] Las respuestas JSON cumplen con el contrato definido.

## 🧪 Pruebas Completadas

- [ ] Se ejecutaron pruebas unitarias de las validaciones de dominio (correo único, contraseña, estado de cuenta).
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

- [ ] Se devuelve `400`, `401`, `403` y `409` según el caso.
- [ ] Se devuelve código HTTP `500` o `503` cuando no hay conexión a la base de datos.
- [ ] El campo `mensaje` en el JSON incluye un texto amigable y claro y no revela si falló el correo o la contraseña.
