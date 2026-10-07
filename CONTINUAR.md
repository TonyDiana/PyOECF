# Continuar el trabajo en PyOECF

<!-- cSpell:ignore biboecf, customtkinter, screeninfo, pyobjc, pyyaml, jsonl, aquila, meipass, Valencià, msgcat, choosedir -->

Nota para Claude web (2026-10-07), escrita al terminar una sesión de Claude Code. Sustituye a la del 2026-10-06.

No tienes acceso al disco ni al repo: Tony te pegará los archivos que hagan falta. Si necesitas ver uno, pídeselo por su ruta. Las rutas de esta nota son relativas a la raíz del repo, `~/Dev/Python/Aplicaciones/PyOECF`.


## 1. Antes de nada

- Responder **siempre en español**. Tony tiene dislexia y TDA: explica en pasos claros y **no repitas literales** (usa constantes con nombre). Si ves un literal repetido, señálalo sin esperar a que lo pida.
- «cd» = «confirma o desmiente».
- Cambiar **solo** lo que Tony indique; lo demás, señalarlo aparte. **Nunca quitar nada** sin su sí expreso.
- Antes de cambios grandes, **proponer y esperar el sí**. Tony suele decir «no te lances a lo loco y hablemos».
- Estándar de programación: `rec/estrategias/Estrategia_slr.md`. Arquitectura y pieza 1: `rec/contexto.md` (ver apartado 2).
- Versión actual: **0.3** (alfa; las 0.x son pre-release a propósito).
- En Claude Code, la sesión de hoy es `5ba2f4f7-757b-48c2-b517-3d611b6253d2`, por si Tony quiere retomarla allí.


## 2. Partes de `rec/contexto.md` que ya no valen

| Dice | Ahora |
|---|---|
| PyOECF tiene `std` y `aquila` en `src/bib` | `aquila` se ha quitado. `std` es una versión mínima (ver 3.1). Las traducciones van con dicts (ver 3.4) |
| `src/main.py` es una ventana de saludo | `src/main.py` solo arranca; la ventana está en `src/kernel/main.py` (ver 3.3) |


## 3. Estado del código

### 3.1 Std mínima: `src/bib/std/`

- PyOECF solo usa `std.EnumMutable` y `std.classproperty`.
- `src/bib/std/__init__.py` solo hace `from .clases_slr import EnumMutable, classproperty`.
- `clases_slr.py` es un **enlace simbólico** (relativo) al `clases.py` del repo real de Std (`~/Dev/Python/Bibliotecas/PythonStd/Std/src/python/clases.py`). Así el código está en un solo sitio.
- `BIB_std_slr` es un enlace a todo Std. Git lo ignora. Se borró la copia completa `src/bib/std/src/`.
- Sufijos de enlaces de Tony: `_slr` (relativo, fuera del repo pero dentro de `~/Dev`), `_sla` (absoluto), `_slp` (dentro del repo), `_sl` (pendiente de `SymlinksLocal_slr.sh --deducir`).
- Consecuencia: un `git clone` fuera de las máquinas de Tony no arranca, porque el enlace apunta fuera del repo. Tony lo acepta: Syncthing lleva todo `~/Dev` a sus máquinas.

### 3.2 Constantes de la app: `src/kernel/constantes.py` → clase `K`

- `nombre`, `url_help`, `archivo_version`, `version`, `path` (único sitio que sabe de PyInstaller: `sys._MEIPASS`).
- Iconos: `carpeta_recursos = "src/rec"` (antes `src/recursos`), `icono_tema_claro`, `icono_tema_oscuro`. No van en el `rec/` de la raíz porque `Remoto.sh` lo quita del despliegue.
- Idiomas: `K.es`, `K.en`, `K.ca` (valenciano) y sus nombres en `K.idiomas` («Español», «English», «Valencià»).
- **Idioma al arrancar: el del sistema.** `_idioma_sistema()` mira las variables `LANGUAGE`, `LC_ALL`, `LC_MESSAGES` y `LANG` (en `K.variables_idioma`); en Windows, el idioma de la interfaz; y como último recurso `locale.getlocale()`. Se queda con las dos primeras letras (`es_MX` → `es`). Si no lo conoce, inglés (`K.idioma_defecto`). No se recuerda el último idioma elegido.

### 3.3 Ventana principal: `src/kernel/main.py` → clase `Ventana`

```text
┌ PyOECF - Versión 0.3 ────────────────────────────────┐
│ ┌ Serie ───────────────────────────────────────────┐ │  ← al analizar
│ │ 37 imágenes · de Z0 1/3 a Z11 1/3                │ │
│ │     0    1   …   V   …   9    X                  │ │
│ │ +0  [..] [..]   [..]    [..] [..]                │ │
│ │ +1/3 …                                           │ │
│ │ +2/3 …                       [..] [Incidencias 3]│ │
│ │    30 de 31 posiciones · El análisis continúa…   │ │
│ └──────────────────────────────────────────────────┘ │
│ ┌ Cámara ──────────────────────────────────────────┐ │  ← al analizar
│ │ Primera imagen … Marca … Modelo … f/ … Tv … ISO  │ │
│ └──────────────────────────────────────────────────┘ │
│ ┌ Carpeta ─────────────────────────────────────────┐ │
│ │ [Seleccione carpeta] [___ ruta ___]   [Analizar] │ │
│ └──────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────┐ │
│ │ [Ayuda]        Idioma [Español ▾]        [Salir] │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

- Constantes de la ventana (textos, medidas, Tcl) en `Ventana.KV`, clase interna.
- **Estilo pedido por Tony: un método por caja**, con funciones internas para lo que solo usa esa caja. Solo es método aparte lo que se llama desde fuera.
  - `caja_ayuda()`
  - `caja_carpeta()`: internas `sin_ocultos()`, `en_su_idioma()`, `elegir()` y `otra_carpeta()`.
  - `caja_cam()`: lo ejecuta el botón Analizar. Internas `construir_caja()` y `nuevo_dato()`. Construye la caja la primera vez, rellena los datos de la primera imagen y llama a `caja_serie()`.
  - `caja_serie(raws, exp_primera)`: se crea **nueva en cada análisis**. Internas `ver_incidencias()`, `leer_toma()`, `fin_serie()` y `mostrar_rejilla()`. Lee una imagen cada vez con `after()`, para que la ventana no se congele.
- **Cajas en lista:** `nueva_caja(titulo, reiniciar)` apunta en `self.cajas` la fila de cada caja y su función de reinicio. `quitar_cajas(desde)` quita las de encima y todo lo que depende de ellas: la lectura en marcha, la ventana de incidencias, sus textos traducibles y sus atributos. La usan:
  - Carpeta, al cambiar de carpeta (si la ruta es distinta de la analizada, comparadas como rutas).
  - Cámara, al empezar cada análisis. Si la carpeta falla, no queda ninguna caja Serie vieja.
  - Una caja nueva en el futuro no obliga a tocar `caja_carpeta()`: si se crea con `nueva_caja()`, se quita sola.
- `reiniciar_cam()` y `reiniciar_serie()` declaran los atributos de esas cajas. Los llama el `__init__` y `quitar_cajas()`.
- `carpeta_escrita()` convierte la casilla en ruta y resuelve `~`. `activar_analizar()` activa Analizar solo si hay ruta y no se está leyendo.
- Diálogo de carpetas (Tk de Linux): sin carpetas ocultas pero con la casilla para verlas, y en el idioma de la app (`KV.tcl_faltan` = `{original: {idioma: traducción}}`).
- Icono de la ventana: en Linux/Wayland GNOME no lo muestra (haría falta un `.desktop`); en Windows customtkinter pone el suyo a los 200 ms (haría falta `iconbitmap` con un `.ico` y `EXE(icon=…)` en el `.spec`). Sin decidir.

### 3.4 Traducción

- Cada texto es un dict `{K.es: …, K.en: …, K.ca: …}` y `K.tr(texto)` lo devuelve en el idioma activo. **Todos los textos deben tener los tres idiomas**, o `K.tr()` falla.
- Cada elemento con texto se apunta con `traducible()` o `poner()`. Al cambiar de idioma, `traducir()` lo rehace todo, incluida la rejilla y la ventana de incidencias.
- Valenciano normativo (AVL): «Seleccioneu», «Analitzar», «Eixir», «preses», «graella». Tony puede revisar alguna palabra.
- **biboecf no traduce nada**: devuelve datos o notación neutra (`Z4 1/3`, `1/200 s`). Vivirá también en FotoEstación (FE), que traduce con Babel. Si algo se mueve a biboecf, debe devolver datos, no frases.

### 3.5 Rejilla: `src/kernel/temporal/rejilla.py` (TEMPORAL)

- Canvas de 11 zonas × 3 tercios. `repartir()` coloca cada toma en su celda; `resumen()` da el contador y la conclusión; `incidencias()` da la lista completa (sin toma, repetidas, Z-V distintas de 3, fuera de la rejilla).
- El botón de incidencias va **dentro de la rejilla**, en el hueco de ZX 2/3 (`KR.pos_boton`): «Incidencias N», o «Sin incidencias» desactivado. Abre una ventana aparte con las incidencias, una por línea.
- El resumen va en una línea, centrado bajo las celdas.
- Se hizo así porque listar avisos bajo la rejilla hacía la ventana más grande que la pantalla y Tk la dibujaba mal.
- PROVISIONAL: la referencia de la serie es la primera imagen leída. Por eso con series mezcladas salen muchas tomas fuera.

### 3.6 Dependencias

- `screeninfo~=0.8.1` y `pyobjc-framework-Cocoa` (este solo en macOS) en `rec/requirements/requirements.conf`. En una máquina nueva: `rec/requirements/requirements_slr.sh --dev`.
- `babel` quitado de PyOECF.
- `toml` quitado del requirements.conf del repo real de Std: no se usa.


## 4. Pendiente

1. **Plurales:** con una sola toma sale «Hay 1 tomas» / «There are 1 shots» / «Hi ha 1 preses». Hay que separar singular y plural.
2. **Resumen redundante:** con la serie completa sale «31 de 31 posiciones · Serie completa en las 31 posiciones.».
3. **Iconos** en Windows y Linux (ver 3.3).
4. **Ventana:** ¿ancho mínimo fijo para que no cambie de tamaño al cambiar de idioma?
5. **Pieza 1:** proponer los nombres de los módulos de `biboecf` y el esquema de la declaración de campos y del informe. Esperar el sí antes de crear archivos.
6. Señalados sin decidir:
   - `rec/estrategias/Decisiones.md`: su apartado «Dos modos» está desactualizado.
   - Probar el ejecutable en macOS y en Windows (detección del idioma en Windows sin probar).
   - La copia de std que lleva FE no tiene el cambio de toml (FE está parado).



## 5. Capturas 

# Secuencia de tomas

Las tomas de una serie se guardan en una misma carpeta y se hacen en este orden. El programa deduce solo por cuál de los dos lados se empezó.

| N.º | Toma | Qué se hace | Archivos |
|---|---|---|---|
| 1 | Z-V con balance arbitrario | Se dispara con el balance que tenga la cámara | 1 |
| 2 | Z-V con balance personalizado | Se crea el balance con la tarjeta y se dispara de nuevo | 1 |
| 3 | Un lado | Se cambia solo el tiempo, de 1/3 en 1/3, sin repetir ni saltar ninguno | 15 |
| 4 | Z-V de cambio de lado | Se vuelve al tiempo de la Z-V | 1 |
| 5 | El otro lado | Igual que el 3, en sentido contrario | 15 |
| 6 | Tapadas | Con la tapa puesta, el visor cubierto, el mismo ISO y a 1/160 s, dos seguidas | 2 |
| 7 | Balances de blancos | Con la exposición de la Z-V, se cambia solo el balance en cada toma | 10 |

La serie tiene **35 archivos** y los balances añaden otros **10**, hasta un total de **45**.

Con la Z-V en la zona V, quince tercios son cinco zonas: se llega a la zona 0 por un lado y a la zona X por el otro.


## Balances de blancos

En la toma 7 se hace una toma por cada uno de estos ajustes, en este orden:

1. Auto
2. Luz día
3. Nublado
4. Sombra
5. Tungsteno
6. Fluorescente
7. Flash
8. Temperatura de color manual a 3200 K
9. Temperatura de color manual a 5600 K
10. Temperatura de color manual a 6500 K

El balance personalizado ya está en la toma 2. Si la cámara no tiene alguno de estos ajustes, se omite.