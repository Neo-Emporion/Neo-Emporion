# Guía para construir tu HU en Neo-Emporion

Sigue estos pasos **en orden**. Copia y pega los comandos en la terminal de VS Code (menú **Terminal → New Terminal**). Los comandos están escritos para **Ubuntu**. Si algo sale en rojo o no sale lo que aquí dice, **detente y avísame** antes de seguir.

---

## 0. Antes de empezar cada HU: los documentos

Cada vez que yo termine una HU te voy a enviar el **`CLAUDE.md` actualizado**. Siempre que lo recibas:

1. Copia `CLAUDE.md` en la **carpeta principal del proyecto** (donde está `main.py`) y **reemplaza** el que ya tenías.
2. Revisa que en esa misma carpeta estén también:
   - `guia-fastapi-arquitectura-capas.md`
   - el archivo de tu HU (ej. `HU-02_Gestionar_tipos_de_documento.md`)
3. Revisa que exista el archivo `.github/copilot-instructions.md`, que le explica a Copilot las reglas del proyecto. Te lo envío junto con el CLAUDE.md.

> En Ubuntu, las carpetas y archivos que empiezan con punto (como `.github`) están **ocultos** en el explorador de archivos. Presiona **`Ctrl + H`** para verlos. En el panel de archivos de VS Code sí se ven siempre.

> Estos archivos **no se suben a GitHub** (así lo pidió el profesor). Ya están configurados para que git los ignore. No los borres de tu carpeta.

---

## 1. Solo la primera vez: preparar el entorno

Si es la primera vez que usas entornos virtuales en tu Ubuntu, instala lo necesario (te pedirá tu contraseña):

```
sudo apt update
sudo apt install python3-venv python3-pip
```

Luego, en la carpeta del proyecto:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> El proyecto necesita **Python 3.10 o superior**. Revisa tu versión con `python3 --version`.

Sabrás que el entorno está activo porque al inicio de la línea de la terminal aparece **`(venv)`**.

**Cada vez que abras VS Code** solo tienes que activarlo:

```
source venv/bin/activate
```

---

## 2. Traer lo último y crear tu rama

Siempre se trabaja desde la rama **`development`**. Nunca directamente en `main`.

```
git checkout development
git pull
git checkout -b HU-02_Gestionar_tipos_de_documento
```

Cambia el nombre de la rama por el de tu HU (sin tildes ni espacios).

Comprueba que todo funciona **antes** de cambiar algo:

```
pytest -v
```

Todo debe salir en verde (`passed`).

---

## 3. Pedirle la HU a Copilot

1. Abre el chat de Copilot (ícono de Copilot arriba a la derecha, o `Ctrl + Alt + I`).
2. Arriba de la caja de texto elige el modo **Agent**, para que pueda crear y editar archivos.
3. Copia este mensaje, cambiando `HU-02_...` por el nombre de tu archivo:

```
Lee #file:CLAUDE.md, #file:guia-fastapi-arquitectura-capas.md y #file:HU-02_Gestionar_tipos_de_documento.md.
Construye esta HU siguiendo EXACTAMENTE el patrón de los archivos de HU-01
(ubicacion_router.py, ubicacion_service.py, dato_geografico.py, ubicacion_repository.py,
exceptions/ubicacion.py y sus pruebas).
Usa las rutas, campos, códigos HTTP y mensajes exactamente como dice la HU.
Convierte cada caso de prueba de la HU en un test de pytest.
Si algo no está definido en la HU, no lo inventes: márcalo como TODO(pendiente) y dime cuál es.
Antes de escribir código, dime qué archivos vas a crear y cuáles vas a modificar.
```

4. **Lee lo que te propone antes de aceptar.** Revisa que:
   - Los archivos nuevos tengan la forma `<recurso>_router.py`, `<recurso>_service.py`, etc.
   - Solo **agregue** líneas en `main.py`, `app/core/database.py` y `tests/conftest.py`, sin borrar nada.
   - **No toque** los archivos de HU-01 ni `errores.py`, `respuesta.py` o `seguridad.py`.

   Si quiere cambiar algo de esa lista, dile que no y avísame.

---

## 4. Probar

```
pytest -v
```

- **Todas** las pruebas deben pasar, también las de HU-01. Si falla una de HU-01, tu cambio rompió algo: dile a Copilot *"esta prueba de HU-01 falló, arréglalo sin modificar los archivos de HU-01"* y pégale el error.
- Prueba también a mano en Swagger:
  1. `uvicorn main:app --reload`
  2. Abre `http://localhost:8000/docs`
  3. Botón **Authorize** → escribe `token-administrador`

---

## 5. Anotar lo que la HU no define

Escribe en una nota todo lo que quedó como `TODO(pendiente)` o lo que decidieron Copilot y tú porque la HU no lo decía (por ejemplo: *"el mensaje de edición exitosa no está en la HU, se usó 'Tipo de documento actualizado exitosamente'"*). **Envíamela** junto con el aviso del paso 7, para agregarla al CLAUDE.md. Tú **no edites** el CLAUDE.md; así no se mezclan versiones.

---

## 6. Guardar y subir tu trabajo

```
git status
```

Revisa la lista: **no** deben aparecer `CLAUDE.md`, la guía, la HU, `venv/` ni archivos `.db`. Si aparecen, detente y avísame.

```
git add .
git commit -m "HU-02: agrega gestión de tipos de documento"
git push -u origin HU-02_Gestionar_tipos_de_documento
```

---

## 7. Avisarme

Cuando tu rama esté subida, escríbeme con:
- el nombre de tu rama,
- la nota del paso 5,
- el resultado de `pytest -v` (cuántas pruebas pasaron).

Yo me encargo de la integración: revisar tu rama y unirla a `development` y luego a `testing`. **Tú no hagas merge ni Pull Request.**

---

## Reglas de oro

- ❌ Solo haces push de **tu rama**. Nunca a `main`, `staging`, `testing` ni `development`.
- ❌ No hagas merge ni Pull Request; la integración la hago yo.
- ❌ No modifiques archivos de otras HU sin preguntar.
- ✅ Siempre `git pull` en `development` antes de empezar una HU nueva.
- ✅ `pytest -v` en verde antes de subir.
- ✅ Ante cualquier duda, pregunta antes de aceptar lo que proponga Copilot.
