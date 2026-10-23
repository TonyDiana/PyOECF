# Memoria · PyOECF

<!-- cSpell:ignore biboecf, customtkinter, screeninfo, pyobjc, pyyaml, jsonl, aquila, meipass, Valencià, msgcat, choosedir, gris18, Morales, bicubica, bilineal, camara, derecheos, docu, INSTALACION, metodo, mkdocs, nojekyll, numpy, pano, pyexiv, pystray, rawpy, reduccion, teselas, venv, vendoriza, esCarpeta, KCOM, margenTV, pixls -->


## 1. Partes de `rec/contexto.md` que ya no valen

| Dice | Ahora |
|---|---|
| PyOECF tiene `std` y `aquila` en `src/bib` | `aquila` se ha quitado. `std` es una versión mínima (ver 2.1). Las traducciones van con dicts (ver 2.4) |
| `src/main.py` es una ventana de saludo | `src/main.py` solo arranca; la ventana está en `src/kernel/main.py` (ver 2.3) |
| Identificadores en español sin tildes ni `ñ`, «por ejemplo `pano`, no `paño`» (punto 6) | Nada de palabras con tilde o `ñ`, tampoco escritas sin ella: se usa otra, a menudo inglesa (`Review`, `Select`, `cam`, `btn`, `dev`…). «Paño» es `tela` en todo el código (2026-10-18/19) |
| Los docstrings no terminan en punto (punto 6) | Depende de para quién son (Tony, 2026-10-19): los que salen en la documentación (MkDocs: métodos, propiedades y funciones públicas, siempre con docstring, y las constantes que se usan fuera de su módulo) acaban en punto; los del programador (lo privado), no |
| Campos declarados (punto 4: `metodo_reduccion_pano`, `ventana_pano`, `derecheos_tercios`…) | La declaración de campos se borró (2026-10-18): no la usaba ninguna app. El recorte de la lámina reduce siempre por área y el derecheo no se analiza |


## 2. Estado del código

### 2.1 Std mínima: `src/bib/std/`

- PyOECF solo usa `std.EnumMutable` y `std.classproperty`.
- `src/bib/std/__init__.py` solo hace `from .clases_slr import EnumMutable, classproperty`.
- `clases_slr.py` es un **enlace simbólico** (relativo) al `clases.py` del repo real de Std (`~/Dev/Python/Bibliotecas/PythonStd/Std/src/python/clases.py`). Así el código está en un solo sitio.
- `BIB_std_slr` es un enlace a todo Std. Git lo ignora. Se borró la copia completa `src/bib/std/src/`.
- Sufijos de enlaces de Tony: `_slr` (relativo, fuera del repo pero dentro de `~/Dev`), `_sla` (absoluto), `_slp` (dentro del repo), `_sl` (pendiente de `SymlinksLocal_slr.sh --deducir`).
- Consecuencia: un `git clone` fuera de las máquinas de Tony no arranca, porque el enlace apunta fuera del repo. Tony lo acepta: Syncthing lleva todo `~/Dev` a sus máquinas.

### 2.2 Constantes de la app: `src/kernel/constantes.py` → clase `K`

- `nombre`, `usuario_github`, `repo_github` (`TonyDiana/PyOECF`), `url_help` (sale de los dos anteriores), `archivo_version`, `version`, `path` (único sitio que sabe de PyInstaller: `sys._MEIPASS`). OJO: el repositorio también está en `rec/scripts/remoto.conf` (bash).
- Iconos: `carpeta_recursos = "src/rec"` (antes `src/recursos`), `icono_tema_claro`, `icono_tema_oscuro`. No van en el `rec/` de la raíz porque `Remoto.sh` lo quita del despliegue.
- **Plantilla de las láminas** (`biboecf.RUTA_PLANTILLA`): `src/bib/biboecf/src/rec/Soportes.psd`, PSD RGB a 16 bits, 3300 × 2400 px, 48 MB. **Es de biboecf** (Tony, 2026-10-12): se lee junto a su código, así que FE la tiene igual. `PyOECF.spec` la mete en el ejecutable en la misma ruta relativa (`bib/biboecf/src/rec`); no se copia a `src/rec` ni lo hace `Remoto.sh`. La app ya no tiene `K.PLANTILLA_PSD`. **Va dentro del ejecutable, no se descarga** (decidido por Tony, 2026-10-11): funciona sin internet y plantilla y código van siempre juntos. Completarla con capas de 16 bits necesitará una biblioteca externa (`psd-tools`): pieza E.
- Idiomas: `K.ES`, `K.EN`, `K.CA` (valenciano) y sus nombres en `K.IDIOMAS` («Español», «English», «Valencià»).
- **Idioma al arrancar: el del sistema.** `_idioma_sistema()` mira las variables `LANGUAGE`, `LC_ALL`, `LC_MESSAGES` y `LANG` (en `K.VARIABLES_IDIOMA`); en Windows, el idioma de la interfaz; y como último recurso `locale.getlocale()`. Se queda con las dos primeras letras (`es_MX` → `es`). Si no lo conoce, inglés (`K.IDIOMA_DEFECTO`). No se recuerda el último idioma elegido.

### 2.3 Ventana principal: `src/kernel/main.py` → clase `Ventana`

```text
┌ PyOECF - Versión 0.5 ────────────────────────────────┐
│ [icono] Licencia académica de uso… © 2026 Tony Diana │
│ ┌ Lámina ──────────────────────────────────────────┐ │  ← al analizar
│ │ ┌────────────┐ │ Tamaño   ┌ mensajes ─────────┐ │ │
│ │ │  recorte   │ │ ● 100 %  │ 160 teselas fuera │ │ │
│ │ │  del paño  │ │ ○ 50 % … │ (y la generación) │ │ │
│ │ └────────────┘ │          └───────────────────┘ │ │
│ │                │                     [Generar] │ │
│ └──────────────────────────────────────────────────┘ │
│ ┌ Serie ───────────────────────────────────────────┐ │  ← al preparar
│ │ 37 imágenes · de Z0.3 a ZX                       │ │
│ │     0    1   …   V   …   9    X                  │ │
│ │ +0  [..] [..]   [..]    [..] [..]                │ │
│ │ +.3 …                                            │ │
│ │ +.7 …                                            │ │
│ │ [Incidencias (3)] Serie…  [Abrir res.] [Analizar] │ │
│ └──────────────────────────────────────────────────┘ │
│ ┌ Cámara ──────────────────────────────────────────┐ │  ← al elegir carpeta
│ │ Primera… Fecha… Modelo… f/9 · Tv · ISO   14 bits │ │
│ └──────────────────────────────────────────────────┘ │
│ ┌ Carpeta ─────────────────────────────────────────┐ │
│ │ [Seleccione…] [_ ruta _]              [Preparar] │ │
│ └──────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────┐ │
│ │ [Ayuda] [Nueva v.]  Idioma [Español ▾]   [Salir] │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

- Constantes de la ventana (textos, medidas, Tcl) en `Ventana.KV`, clase interna.
- **Estilo pedido por Tony: un método por caja**, con funciones internas (`_snake_case`, sin cierres) para lo que solo usa esa caja. Solo es método aparte lo que se llama desde fuera.
  - `caja_cabecera()`: icono, licencia a su derecha y autor (`K.derechos`) a la derecha del todo. Sin marco.
  - `caja_ayuda()`: Ayuda (abre la web), Idioma (`CambiarIdioma`) y Salir. Junto a Ayuda, el botón **Nueva versión X**, oculto: solo aparece si GitHub tiene una versión más nueva (ver 2.10).
  - `caja_carpeta()`: internas `_sin_ocultos()`, `_idioma()`, `_elegir()`, `_orden_linux()`, `_entorno_sistema()`, `_usar()`, `_dialogo_tk()`, `_esperar()`, `_es_la_vista()`, `_otra_carpeta()` (con espera al teclear) y `_mostrar_cam()`.
  - `caja_cam()`: se ejecuta **al elegir carpeta**. Internas `_construir_caja()`, `_nuevo_dato()` y `_str_exp()`. Crea `self.OECF = biboecf.OECF(carpeta)` y pinta: primera imagen (`OECF.primera`), fecha (`OECF.fecha`), modelo (`OECF.cam.nombre`, con la marca si el modelo no la lleva) la exposición de la Z-V en un solo texto (`OECF.TextoF/TextoTV/TextoISO`) y, detrás, la profundidad de bits (`OECF.bits`). El orden en pantalla es el de creación en `_construir_caja()`, no el de relleno. Al final, `ActivarCarpeta()`.
  - `caja_serie(OECF)`: la crea el botón **Preparar** (`Preparar()`), nueva cada vez. Internas `_ver_incidencias()`, `_leer_toma()`, `_fin_serie()`, `_resumen()`, `_copiar_toma()`, `_fin_copia()` y `_mostrar_rejilla()`. Dos fases, las dos una toma cada vez con `next()` y `after()`, con barra y texto de progreso, para que la ventana no se congele:
    1. **Lectura** (`OECF.Leer()`, «Leyendo 5 de 39…»). Al terminar, rejilla e incidencias.
    2. **Copia** a la carpeta `OECF` (`OECF.Copiar()`, «Copiando 5 de 37…»). Al terminar, `estudio.json` e `incidencias.txt` allí (ver 2.6), Analizar si la serie sirve y los botones de la caja Carpeta libres.
  - `caja_lamina(OECF)`: la crea el botón **Analizar** (`Analizar()`, que antes quita la anterior: `propias_serie`). Mide las teselas de la Z-V con `OECF.Seleccionar()` (unos 2 s con la ventana quieta y «Buscando el paño…») y actualiza el botón de incidencias (`ContarIncidencias()`). **Sin tarjeta gris**: lo dice (el texto de la incidencia `SIN_TARJETA`) y no hay más. Con tarjeta: dos secciones a todo el ancho, separadas por una línea del color del marco. A la izquierda, el recorte de la Z-V tal como saldrá en la lámina (`biboecf.revelar` + `recorte`, en una etiqueta de Tk con PPM: sin Pillow); sin paño, en su lugar el porqué (`TXT_PROBLEMA_PANO`) y que solo se generará el Excel. A la derecha: los tamaños (100, 50, 33 y 25 %; los que no caben, inactivos), a su lado la **ventanita de mensajes** (Tony, 2026-10-12: `Mensaje()` añade una línea traducible; la primera, las teselas rechazadas, con el mismo texto que la incidencia `RECHAZADAS`; después, el proceso de generar) y, abajo a la derecha, **Generar**: mide la serie (`OECF.Medir()`, una toma cada vez con `after()`, «Midiendo 5 de 33…» en la ventanita, que sustituye la línea), vuelve a grabar `estudio.json` con el análisis y escribe el libro `PyOECF.xlsx` en la carpeta `OECF` (si no se puede, por ejemplo abierto en Excel, lo dice). La lámina (pieza E), pendiente. Variables en `ReiniciarLamina()`.
- **Desplazamiento** (Tony, 2026-10-12: habrá alumnos con pantallas de 800 px): el cuerpo va dentro de un lienzo (`self.lienzo`). `Ajustar()` no deja que la ventana pase del alto del monitor principal (`MonitorPrincipal()`) menos `ARRIBA` y `RESERVA_ALTO`; si el contenido no cabe, aparece la barra (`self.barra`) y la rueda del ratón desplaza (`Rueda()`, en cualquier punto de la ventana principal, no en la de incidencias). Si cabe, la barra no se ve.
- **Dentro del monitor** (2026-10-14, en el portátil de Tony la ventana salía desplazada y fuera de la pantalla): `Centrar()` solo se llama al arrancar; al crecer, la ventana se ensanchaba hacia la derecha desde ese borde. Ahora `Ajustar()` termina con `MeterEnMonitor()`, que la mueve lo justo si se sale del monitor principal y no la toca si cabe. La posición se lee con `tk.Tk.wm_geometry()` (mismas unidades en que se pide; `winfo_y()` incluye la barra de título). Formato en `KV.TK_POSICION` y `KV.SEP_POSICION`. **[NO VERIFICADO en el portátil]**: probado en la torre simulando 1366 × 768.
- **Cajas en lista:** `CrearCaja(titulo, reiniciar, fija, marco)` apunta en `self.cajas` la fila de cada caja y su función de reinicio. `QuitarCajas(desde)` quita las de encima y todo lo que depende de ellas: la lectura en marcha, la ventana de incidencias, sus textos traducibles y sus atributos. La usan:
  - Carpeta, al cambiar de carpeta (si la ruta es distinta de la ya vista, comparadas como rutas).
  - Preparar, que quita las de encima de la caja Cámara (`propias_cam`). Si la carpeta falla, no queda ninguna caja Serie vieja.
  - Una caja nueva en el futuro no obliga a tocar `caja_carpeta()`: si se crea con `CrearCaja()`, se quita sola.
- Todas las variables de instancia se declaran con su tipo en el bloque «Variables de instancia» del `__init__`. `ReiniciarCam()` y `ReiniciarSerie()` solo les dan su valor inicial; los llaman el `__init__` y `QuitarCajas()`.
- **Permisos** (`OECF.puedeLeer`, `OECF.puedeEscribir`): sin permiso para leer o para escribir en la carpeta, la caja Cámara lo dice y Preparar no se activa. Si la copia falla igualmente (disco lleno; en Windows el permiso no siempre se sabe antes), `OECF.copias` queda vacío y se avisa bajo la rejilla con el error real del sistema (`OECF.errorCopia`, 2026-10-13), sin JSON ni Analizar.
- **Preparar vuelve a leer la carpeta** (2026-10-13): rehace la caja Cámara (un `OECF` nuevo desde el disco) antes de la serie. Antes reutilizaba la lista de RAW del momento de elegir la carpeta, y si se borraban archivos a mano entre medias, la copia fallaba (Genesis).
- `carpetaEscrita` (property) convierte la casilla en ruta y resuelve `~`. `ActivarCarpeta()` activa Preparar si la carpeta sirve (`biboecf.problema_carpeta()`) y Abrir resultados (en el pie de la rejilla) si ya se prepararon las copias, y ninguno mientras se lee o se copia. `AbrirResultados()` abre la carpeta `OECF` en el explorador del sistema.
- **Analizar revelado** (Tony, 2026-10-12), en la caja Carpeta, entre la ruta y Preparar: se ve si `OECF/estudio.json` ya tiene el análisis (`hay_analisis()`, tras Generar) y se activa si además hay en `OECF` TIFF con el nombre de una zona (`OECF.exportaciones`, nombres de `OECF.NombreZona()`, los mismos que las copias). Lo enseña y activa `ActivarCarpeta()`. Lo que hace (`AnalizarRevelado()` y `MedirTiff()`, la parte 2): lee el análisis del JSON (`leer_analisis()`), mide cada TIFF (`biboecf.lstar_tiff()`, una cada vez con `after()`, el progreso en su propia caja, **«Revelado»**, encima de la Cámara: quita las de encima, como Preparar), guarda el L* del revelador en el JSON (`grabar_analisis()`) y rehace `PyOECF.xlsx`. En TD: 31 de 31 en 19 s. Al acabar, en esa caja, **Abrir resultados** y, si hay paño, pregunta si **rehacer las láminas con las TIFF** (la opción B: `EmpezarLaminaTiff()` y `LeerLaminaTiff()`; las mismas láminas que ya haya, al menos la del 100 %; 9 s en TD). Variables en `ReiniciarRevelado()`.
- **Confirmación de Preparar** (`ConfirmarPreparar()`): Preparar borra la carpeta `OECF`; si ya tiene el análisis o exportaciones del revelador, una ventanita de CTk lo dice y pregunta (Cancelar por defecto: Intro, Escape y cerrar cancelan). La ventanita es genérica, `Confirmar(titulo, lineas, texto_si)`: la usan también las láminas desde las TIFF.
- **Elegir carpeta en Linux con el explorador del escritorio** (2026-10-15, hecho en el portátil y traído a la torre sin commit): el diálogo de Tk no ve los discos externos. `_elegir()` lanza `zenity` (o `kdialog`; en KDE, primero este) con `subprocess.Popen` y `_esperar()` mira cada `KV.ESPERA_EXPLORADOR` ms si se ha cerrado, sin bloquear la ventana. El proceso abierto vive en `self.explorador` (uno a la vez; antes era un `nonlocal`, quitado por la norma de sin cierres). Si no hay ninguno, o falla (código distinto de `SALIDA_ELEGIDA`/`SALIDA_CANCELADA`), se abre el de Tk. En el ejecutable de PyInstaller se le devuelve el `LD_LIBRARY_PATH` del sistema (`_entorno_sistema()`). En Windows y macOS, el de Tk como siempre. **[NO VERIFICADO]** el botón en la torre: solo arranque.
- Diálogo de carpetas (Tk de Linux, si no hay explorador): sin carpetas ocultas pero con la casilla para verlas, y en el idioma de la app (`KV.TCL_FALTAN` = `{original: {idioma: traducción}}`).
- Icono de la ventana (`SOicon()`): en Windows, `iconbitmap()` con `PyOECF.ico` (así customtkinter no pone el suyo a los 200 ms) y `EXE(icon=…)` en el `.spec`; en macOS, `BUNDLE(icon=PyOECF.icns)`; en los demás, `iconphoto()` según el tema. En Linux/Wayland GNOME la ventana no lo muestra sin un `.desktop`: Tony lo quitó de pendientes (2026-10-11).

### 2.4 Traducción

- Cada texto es un dict `{K.ES: …, K.EN: …, K.CA: …}` y `K.tr(texto)` lo devuelve en el idioma activo. **Todos los textos deben tener los tres idiomas**, o `K.tr()` falla.
- **Plurales:** los textos con número llevan `(singular, plural)` por idioma y se usan con `K.tr_n(texto, n)` (singular solo con 1). Ej.: «1 imagen», «Hay 1 toma tapada», «There is 1 Z-V».
- Cada elemento con texto se apunta con `ApuntarTexto()` o `Poner()`. Al cambiar de idioma, `Traducir()` lo rehace todo, incluida la rejilla y la ventana de incidencias.
- Valenciano normativo (AVL): «Seleccioneu», «Preparar», «Eixir», «preses», «graella». Tony puede revisar alguna palabra.
- **biboecf no traduce nada**: devuelve datos o notación neutra (`Z4.3`, `1/200 s`, `DAYLIGHT`). Vivirá también en FotoEstación (FE), que traduce con Babel. Si algo se mueve a biboecf, debe devolver datos, no frases.

### 2.5 Rejilla: `src/kernel/rejilla.py`

- Canvas de 11 zonas × 3 tercios. Sus números del protocolo (`tercios_lado`, `tapadas`, `anclas` = 2 iniciales + 1 de cambio + 1 final) salen de `biboecf.KS`. En una celda caben `max_lineas` (3) identificadores; si hay más, dice cuántos.
- La cuenta la hace la biblioteca (`OECF.enRejilla`, `celdas`, `fuera`, `vacias`, `repetidas`, `esAnalizable`); `rejilla.py` solo dibuja y pone los textos. `mostrar(OECF)`, `resumen(OECF)` e `incidencias(OECF)` reciben el objeto.
- **No van a la rejilla:** las tapadas, los balances de cámara y las Z-V iniciales de más (de la 3.ª en adelante). Las demás sobrantes **sí** (Tony quiere ver las repetidas que provocan).
- Bajo la rejilla, centrado bajo las celdas:
  ```text
  Serie completa                     (o «Faltan N posiciones»)
  Balance de blancos personalizado: sí · Balances de cámara: 6
  Tomas tapadas: 0 de 2
  ```
- **Pie de la rejilla** (`poner_pie`): el botón de incidencias alineado con la Z0; **Abrir resultados** y Analizar, seguidos, alineados con la ZX (Tony, 2026-10-12: Abrir resultados sale de la caja Carpeta); el resumen, centrado en el hueco entre ellos. Todo centrado en vertical. Botones como los demás de la ventana, separados por su `MARGEN`. **Con Generar a la vista** (2026-10-13), Abrir resultados se va a la caja Lámina, a la izquierda de Generar, y el de la Serie se oculta (`ResultadosEnSerie()`); si la caja Lámina desaparece y la Serie sigue, vuelve. El porcentaje de teselas rechazadas, con dos decimales.
- **Incidencias:** cuáles hay y en qué orden lo decide `biboecf.incidencias(OECF)` (códigos `KI` con sus datos, sin frases); `rejilla.py` solo las traduce (`TEXTOS_INCIDENCIA`). Así FE no tiene que copiar el criterio. Tras medir, **`LUZ_CAMBIO`** (2026-10-12): una Z-V de control se aparta de la ZV más que `KP.TOLERANCIA_LINEAL` (0,1 zonas): la luz cambió durante la serie; esa Z-V no entra en la media de las Z-V (`Analisis.controlesDesviados`). En TD, `_MG_8194` (el primer balance, tomado como Z-V final) recibió −0,18 zonas de luz con los mismos ajustes.
  - Incidencias: «Incidencias (N)», o «Sin incidencias» desactivado. Abre una ventana aparte con las incidencias, una por línea (así la ventana principal no crece más que la pantalla). También se graban en `OECF/incidencias.txt`, en el idioma de la ventana.
  - Analizar: activo solo si de Z1 a Z9 ninguna zona se queda sin toma y la serie tiene el mismo ISO (`OECF.esAnalizable`). Las repetidas no bloquean. PENDIENTE: lo que hace.
- **Incidencias, en orden:** ISO distinto en la serie (lo primero, porque impide analizar) · sin balance personalizado (dos textos: «No se hizo…» si la 2.ª ya es de un lado; «Las dos primeras Z-V tienen el mismo balance de blancos…» si las dos son Z-V con el mismo balance) · sobran Z-V al principio · falta un lado · falta la Z-V de cambio · sobran Z-V de cambio · falta la Z-V final · secuencia rota en NNNN (se esperaba Zx y es Zy) · «Hay N tomas fuera del orden esperado: 9522, 9523…» · tapadas distintas de 2 · tapadas con otro ISO · no hay balances de cámara · sin toma en cada posición vacía · posiciones con varias tomas · «Hay N tomas más allá de las zonas teóricas: 9553, 9554…» (las que pasan de Z0/ZX; también salen entre las de fuera del orden) · «Hay N tomas que se apartan de su tercio más de 0,33 tercios: 8172 (-0,41)…» (`OECF.desviadas`; no impide analizar).
- PROVISIONAL: la referencia de la serie es la primera imagen leída (en el protocolo es la Z-V, así que es correcta).

### 2.6 JSON del estudio: `src/biboecf/estudio.py`

- **Formato nuevo (2026-10-21, Tony; formato 1.0, en construcción hasta que FE lo lea).** Lo escribe y lo lee la bib; PyOECF solo da su nombre y versión y llama a la bib. Es para programas (FE), no para leerlo a mano: cada dato en un solo sitio, cada clave con un solo tipo de valor y siempre presente (`null` si no hay dato), claves en camelCase (siglas en mayúsculas: `WB`, `ZV`). La sangría se queda para depurar. Grupos, en su orden:
    - `oecf {version}`: el formato (`VERSION_JSON`); lo primero que mira quien lo lee.
    - `info {programa {nombre, version}, fecha, carpeta, camara {marca, modelo}}`: de dónde sale; nada se usa para calcular (`carpeta`, solo para saber el origen).
    - `serie {iso, balancePersonalizado, esAnalizable, saltos [{archivo, tercioEVEsperado, tercioEV}], tomas [{archivo, copia, f, tv, iso, fecha, tercioEV, WB, nombreWB, kelvin, bits, tapada, oscura, zona, parte}]}`. Sin recuentos (`tapadas`, `balances_camara`) ni el bloque `rejilla` (cómo dibuja PyOECF la serie; sale de las tomas y de las incidencias `SIN_TOMA`, `REPETIDA`, `FUERA`).
    - `incidencias`: `biboecf.Incidencia` con los archivos en vez de índices (`codigo`, antes `code`; campo nuevo `tercioEVs`).
    - `medida` (antes `analisis`; `review.KAN`, en camelCase): sin lo que es de la serie (cámara, fecha, exposición y bits de la ZV, copia de cada zona, nombre/Kelvin/multiplicadores de cámara de los balances) ni el L* del revelador; `leer_review(oecf)` (antes recibía la carpeta) los repone desde la serie y el revelado (`estudio._completar`). `tela` es `{x, y, ancho, alto}` o `null`, con `telaMotivo` aparte. Sin `version` (manda la de `oecf`).
    - `revelado {exportaciones [{tercioEV, archivo, bits, espacio, lstar, motivo}]}`: lo escribe `grabar_revelado(oecf, medidas)` al Analizar revelado (con `biboecf.medir_tiff` → `MedidaTiff`), y rehace las incidencias.
    - `resultados` (`Excel.resultados`, claves `KXL` en camelCase: `latitudTexturas`, `diferenciasMedias`, `mediaZV`, `finLineal`…).
- **Aviso de TIFF de menos de 16 bits** (`KRV.BITS_DEFINITIVOS`; decidido A, avisar): incidencia `KI.TIFF_8_BITS` (solo avisa; `n` y `tercioEVs`), calculada en `informe.incidencias` con `revelado.bits_tiff` (con caché por fecha de cambio); su texto en `rejilla.TEXTOS_INCIDENCIA` (tres idiomas, con `{zonas}`); una línea en la caja del revelado, y en el botón, la ventana e `incidencias.txt` (`ContarIncidencias`).
- **Probado (2026-10-21)** con una copia de TD en el scratchpad (sin escribir en la serie): restaura las 44 tomas del JSON antiguo y del nuevo; mide; `leer_review` da cámara, fecha, exposición, bits, copias y balances idénticos a lo medido; mide las 31 TIFF (16 bits, Adobe RGB) y graba el revelado; escribe el libro y `resultados`. Con dos TIFF pasadas a 8 bits: `TIFF_8_BITS` con ZV y Z6, en el JSON y con su texto en los tres idiomas. La ficha no se probó (el venv no tiene matplotlib).
- El Tv sale con ruido de rawpy (`0.00800000037…`); Tony lo deja así de momento.
- Historia: hasta 2026-10-21 vivía en `src/kernel/json_estudio.py`, con otro formato (claves sueltas en la raíz, `analisis`, `rejilla`, recuentos).

- **Movido a biboecf (2026-10-21, Tony): paso 1 de 4.** Tony: el `estudio.json` es el contrato por si biboecf pasa a ser una biblioteca general y otro programa hace el mismo estudio; en `kernel` quedan solo la ventana y la ejecución. El código vive ahora en `src/biboecf/estudio.py` (constantes `KES`, antes `KD`; las 8 funciones se piden como `biboecf.<función>`), copia de `json_estudio.py` sin cambiar lo que hace. Único cambio de formato: la clave `"pyoecf"` es ahora `"programa": {"nombre", "version"}` y `grabar_json(OECF, programa, version)` lo recibe de quien llama (`main.py` pasa `K.NOMBRE, K.version`). Tony no necesita compatibilidad con los JSON ya grabados. Pasos que faltan: (2) los ~15 literales de clave sueltos de `grabar_json` a `KES`, (3) campo con la versión del formato (ya existe `KAN.VERSION`, solo del análisis), (4) un tipo para `resultados` en vez de `dict`. **Borrados (2026-10-21, Tony):** `src/kernel/json_estudio.py` y la carpeta vacía `src/bib/biboecf/`.

- **Versión del formato del JSON (2026-10-21, Tony):** cabecera `"oecf": {"version": "1.0"}` (lo genérico; FE lo mira primero) y `"programa": {"nombre", "version"}` (qué software lo grabó; solo informa). El número vive en `src/biboecf/rec/VERSION_JSON` (una línea, `MAYOR.MENOR`; MAYOR = incompatible, MENOR = clave nueva; sin PARCHE: a quien lee no le cambia nada. **En construcción:** se queda en 1.0 hasta que FE lea el JSON por primera vez (**2026-10-23, pruebas de Tony, ya revertidas a 1.0:** con `1.0a` la app dijo «corrupto» en todas las carpetas, porque `estudio._partes` hace `int()` de cada trozo; la versión del formato SOLO admite números `MAYOR.MENOR`, y el `ValueError` caía en los `except` de lectura. Con `1.1` lee sin problema). Es la versión del formato, no la del programa: PyOECF puede subir y seguir escribiendo 1.x); en la raíz, `VERSION_JSON` es un enlace simbólico a él, solo para verlo. Ruta en `KCOM.RUTA_VERSION_JSON` (`biboecf.RUTA_VERSION_JSON`), metida en el ejecutable por `PyOECF.spec`; `estudio._version_formato` lee la primera línea no vacía. La regla de cuándo subirla está comentada en `KES.OECF`. La bib no tiene versión propia mientras viva dentro de PyOECF (se borraron `rec/VERSION` y `VERSION_BIB`). **Norma: los archivos VERSION tienen una sola línea** (GitHub, `macros_td.py`, `Remoto_slr.sh` y `K.version` lo dan por hecho; con dos, GitHub publicaría p. ej. `1.2bnotas`).

- **Reparto de la carpeta `OECF` por quién la busca (Tony, 2026-10-21):** `ANALISIS/` es para el usuario (libro, ficha, láminas e `incidencias.txt`, que pasa allí desde `CTRL/`; el usuario solo busca en `ANALISIS`); `estudio.json` y `ZONAS/`, para otros programas (FE); `CTRL/`, interna de PyOECF (RAW de control y, si algún día hace falta, `CTRL/PyOECF.json` con lo propio de la app, que no repetirá nada de `estudio.json`; no se crea hasta que haya algo real que guardar). En las series ya preparadas queda el `CTRL/incidencias.txt` antiguo (borrar a mano).

### 2.7 biboecf (`src/bib/biboecf/`)

- **Revisión módulo a módulo (2026-10-17/18, Tony):** el código está ahora en `src/biboecf/` y lo que sigue en este apartado conserva los nombres de antes. **Nombres sin tilde ni ñ** en el código (Tony: la palabra sin su tilde está mal escrita): `Analisis` → `Review` (`review.py`, `review_a_dict`, `review_de_dict`, `OECF.review`), `Seleccion` → `Select`, `fraccion` → `part` (`Select.part`, `part_recortada`), `desvio(s)` → `dev(s)` (`Review.dev`, `OECF.devs`, `KP.DEV_MAX`), `senal` → `signal` (`signal_para_snr`), `camara` → `cam` (`Review.cam`, `kelvin_cam`), `PANO_PEQUENO` → `PANO_MIN`, `CORTE_ATIPICOS` → `CORTE_RARO`; en docstrings y comentarios, «cámara» con su tilde. `bib.clases` se importa como `std` (`from bib import std`). Cambian también claves del JSON (`cam`, `kelvin_cam`, `matriz_cam_xyz`, `desviación_rechazadas`): los `estudio.json` anteriores ya no se leen (`leer_analisis` da `None`); son series de prueba y da igual (Tony). Los prefijos `_` y `__` de los módulos marcan los que quedan por revisar; al acabar uno, Tony le quita el prefijo. **Normas de la revisión:** prioridad de operadores siempre explícita con paréntesis, comprobando con números que el resultado no cambia; constantes públicas con docstring; sin cierres; `KCOM.CIEN` (o su alias `KLI.CIEN`) en todo «por cien» (`_teselas`, `ficha.py`, `libro.py`). **Hechos:**
    - `transferencia.py`: paréntesis en `snr_modelo`, `signal_para_snr`, `ajustar_transferencia` y `escala_mpx`. Un primer intento de Tony con paréntesis cambiaba `snr_modelo` (dividía la lectura entre la ganancia y quitaba el cuadrado a la proporcional); corregido: da lo mismo que antes y `snr_modelo(signal_para_snr(x)) = x`.
    - `cam.py`: docstrings en `KC`, el tipo de la entrada TIFF se desempaqueta antes de compararlo. Igual que antes con 13 RAW (CR2, CR3, ARW).
    - `_teselas.py`: `Select` pasa de `NamedTuple` (de un solo campo) a clase con `__slots__` y `motivo` como propiedad; los cierres `bajar` y `bloques` pasan a `_bajar` y `_bloques` (con parámetros); paréntesis en todo el módulo; constantes nuevas `KTE.CANALES_RAW` (4) y `KTE.BITS_PANTALLA` (8). **Fallo corregido en `_corte_otsu`** (reescrito en pasos: medias de los dos grupos y varianza entre clases): en la última clase no queda nadie encima, la fórmula antigua dividía un resto de redondeo entre 0 y salía infinito, y a veces ese corte (el último) ganaba (298 de 3000 conjuntos inventados; una toma de TD que no es la Z-V). Ahora sale NaN y no cuenta. Sin el fallo, igual que antes en los 3000; el paño de la Z-V de las 13 series de `gris18`, el mismo. Las demás funciones, iguales que antes con TD (R7) y Luis (Sony). Queda sin hacer: los nombres con tilde (`dispersion`, `pano`, `patron`, `indice`…), aparcados (tocan `review`, `kernel` y `libro`). Tony le quitó el prefijo: `teselas.py`.
    - `_zonas.py`: paréntesis en `exp_relativa` y `zona_tercio`, `#` antes de cada función, `KP.ROMANOS = {ZONA_REF: "V", 10: "X"}` (el 5 era `ZONA_REF` escrito a mano). En el docstring de `OECF.desviadas`, `KP.DESVIO_MAXIMO` → `KP.DEV_MAX`. Igual que antes en los tercioEV de −20 a 20 y en las exposiciones probadas. Tony le quitó el prefijo: `zonas.py`.
    - `_tiff.py`: paréntesis (el más traicionero, `not (1 <= n < KCOM.MAX_ENTRADAS)`), `#` antes de cada función y constante nueva `COM.BYTES_ORDEN` (2: la marca «II» o «MM» con que empieza la firma; antes, `firma[:2]`). Igual que antes en `leer_cam`, `leer_balance` y `leer_kelvin` con los 498 RAW de las 13 series. Tony le quitó el prefijo: `tiff.py`.
    - **Los demás, archivo a archivo, en orden** (Tony): `__init__.py`: `__all__` en orden alfabético (la norma de los `__init__`; los 52 nombres, todos existen e importados) y sangría de las importaciones de `teselas` y `transferencia`. De esos 52, 24 no los usa ninguna app (`buscar_pano`, `Cam`, `Exp`, `KTR`, `snr_modelo`…): la regla «solo lo que usan las apps» ya no se cumple; sin decidir (ver `CLD_TODO.md`).
    - `campos.py`: se borra lo que no usaba nadie (Tony: «si no, se buscará código fantasma dentro de un tiempo»): `Campo`, `campos()`, `validar()` y las constantes de los campos (`CARPETA_SERIE`, `METODO_REDUCCION` y su `metodo_reduccion_pano`, `METODO_AREA`, `METODOS` con `bilineal` y `bicubica`, que nunca se programaron: la lámina siempre reduce por área, `TIPO_RUTA`, `TIPO_OPCION`, `NO_ADMITIDO`). Quedan `problema_carpeta()` y los cuatro códigos de `KCA`, con docstring. Fuera también del `__init__`. El archivo pasa a llamarse **`carpeta.py`**. Nombres unificados con los textos de `main.py` (Tony: «cuanto más se unifique, mejor»): `KCA.NO_EXISTE` → `SIN_CARPETA`, `NO_LEGIBLE` → `SIN_PERMISO_LEER`, `NO_ESCRIBIBLE` → `SIN_PERMISO_ESCRIBIR` (como `TXT_SIN_CARPETA`, `TXT_SIN_PERMISO_LEER`, `TXT_SIN_PERMISO_ESCRIBIR`), y en `OECF`, `esLegible` → `puedeLeer` y `esEscribible` → `puedeEscribir`. Probado con carpetas sin permiso de lectura y de escritura.
    - `constantes.py`: cada constante de `COM` con su docstring (antes, un comentario por grupo); los grupos, con un título corto (recursos, archivos, números, CIELab, TIFF y formatos de struct). Las 28 se usan; los valores, los mismos.
    - **Constantes que pasan a `COM`** (2026-10-18, al revisar `constantes.py`): las que no eran propias de su módulo o estaban escritas en varios. `COM.CANALES_RGB` (3; sustituye a `KTE.CANALES_MATRIZ` y `KLA.CANALES_COMPUESTA`; `KLI.CANALES` queda como alias, como `KLI.CIEN`), `COM.MAX_16` (65535; sustituye a `KLA.MAX_16` y `KRV.ICC_MAXIMO_TABLA`), `COM.UMBRAL_RECORTE` (antes `KTE.UMBRAL_RECORTE`) y `COM.TOLERANCIA_LINEAL` (antes `KP.TOLERANCIA_LINEAL`), criterios del método que comparten la medida y el libro. `transferencia` y `review` ya no importan `KTE` ni `KP` para ellas. Los colores de la ficha ya salían casi todos del libro (`KFI.VERDE = KLI.CABECERA_FONDO`…); `EJES` y `CERO` comparten gris con el libro pero no papel, y se quedan. Comprobado con TD: los `resultados` del libro, iguales que los del JSON del 17 (0 diferencias); libro y ficha se escriben.
    - `ficha.py` (hecho): nombres sin tilde: `KFI.TAMANO*` → `LETRA*` (Tony prefirió `LETRA` a `LEN`: `len` es «cuántos hay» en Python), `SECCION_*` y `seccion()` → `APARTADO_*` y `apartado()` (también `LETRA_APARTADO` y `ENTRE_APARTADOS`), `GRAFICA_*` y `grafica_*()` → `GRAF_*` y `graf_*()`, `titulo_grafica` → `titulo_graf`, `exposicion` → `exp` y `_posicion` → `_pos`; en los textos de la ficha (`textos_libro.py`), `{camara}` → `{cam}` y `{exposicion}` → `{exp}`; `Libro.analisis` → `Libro.review` (solo lo usaba la ficha). `ejes(ax: Axes)` en vez de `object`; dos `# type: ignore` explicados (`rc_context`, que pide sus propios nombres de clave, y `cifra()`, hasta que `limites_texturas` declare bien lo que devuelve). Las palabras de matplotlib, al `cSpell:ignore`, **en orden alfabético** (norma de Tony, también en `teselas.py`). Quedan `{camara}` en la nota de gráficas del libro y en el cajetín de `main.py`. Ficha de TD escrita y leída: «Tu cámara: Canon EOS R7». `KLI.ORDEN_GRAFICAS` → `ORDEN_GRAF` y `FORMATO_TITULO_GRAFICA` → `FORMATO_TITULO_GRAF` (los usaba la ficha). Paréntesis explícitos en 15 líneas: la ficha de TD, con revelador y sin él, sale **igual píxel a píxel** (0 de 966 763 en cada página). **`KFI` sin docstrings** (acordado con Tony): es una clase de diseño de página y sus comentarios de grupo explican las constantes juntas. Duplicado pendiente para `libro.py`: el título numerado de una gráfica se monta igual en `Ficha.titulo_graf` y en el libro.
    - **`ficha.py`, diseño de la página 1 (2026-10-20, hablado con Tony):** franja verde con la exposición como en la pantalla, «ZV: f/9 · Tv 1/125 s · ISO 100» (lo que falta no sale), con una sola función, `OECF.TextoExp`, que usan la ficha y `main._texto_exp`; rótulos solo en `textos_excel.py` (`KXL.ROTULOS_EXP` = `T_F`, `T_TV`, `T_ISO`; `T_TV` pasa de «TV» a «Tv», también en la hoja Análisis, cuya fila ZV va ahora en el orden de `ROTULOS_EXP`; y «Tv» en el manual, `3) Captura`). **Orden f, Tv, ISO en todas partes:** campos de `Review`, claves `J_*` y JSON (`review_a_dict`/`review_de_dict`), creación en `kernel.py` y separador « · » solo en `OECF.KT.SEPARADOR` (`KV.SEP_RESUMEN` apunta a él); fuera `KV.TXT_EXP`, `TXT_F`, `TXT_ISO`. Notas partidas a mano (`partir()`, midiendo con Agg) para no pasar de la raya (`wrap=True` cortaba en el borde del papel); van desde arriba (`va="top"`) y devuelven dónde acaban: la tabla baja si la nota llega (`bajo_nota`, `NOTA_A_TABLA`). Escala de zonas **en peine**: un paso por tercio con su gris (el del L* objetivo: `PuntoCurva.salida`; antes, el esperado, que dejaba blanco todo desde la Z7 2/3) y su borde gris (`MARCO_TIRA`: el verde claro se confundía con el blanco desde la Z7, donde el esperado ya es 100); los pasos de zona entera, altos (`ALTO_ZONA`), y los de tercio, a 2/3 (`ALTO_TERCIO`; se probó 1/2 y a Tony le gustó mucho más 2/3) — esto era lo que Tony quería de «distintas alturas», no los dientes —; debajo, diente de zona (0.3) y de tercio (0.15), nombres solo en las enteras y la ZV en recuadro oscuro; los extremos de los tramos caen sobre un diente. `ESCALA` y las gráficas, calculadas desde `IZQUIERDA`/`DERECHA` (`GRAF_IZQUIERDA`); números sueltos de `cifra()` a `CIFRAS_*`. Ficha de TD escrita y mirada. **Pendiente de hablar:** las gráficas y la página 2.
    - `informe.py`: docstring en cada código de `KI`; `Incidencia.codigo` → `code` (también en `rejilla.py` y `main.py`; en el JSON, la clave de cada incidencia pasa a `code`); parámetro y local `seleccion` → `select`, local `indices` → `repetidas`; paréntesis. Igual que antes en las incidencias de las 13 series. Quedan dos con tilde que son de otros módulos: `OECF.seleccion` y `OECF.vacias` (`kernel`) y `KTE.RECHAZO_ASIMETRIA` (`teselas`, aparcado). Los campos de `Incidencia`, como los demás `NamedTuple`, siguen con comentarios.
    - **Plantilla `src/biboecf/rec/Soportes.psd` para los estudiantes** (2026-10-18, Tony): el cajetín, con el mismo criterio que aplica PyOECF (cuatro líneas repartidas a la misma distancia en el marco y alineadas a la izquierda, texto editable), pero con huecos para escribir a mano: «Cámara: ___», «Latitud recomendada: ___», «Fecha: ___», «Soporte: ___», con los huecos acabando todos en el mismo punto. Hecha con `Lamina` sin zonas, así que trae también lo demás que hace PyOECF: el nombre de cada capa de texto es su texto, la imagen de la capa redibujada en negro, sin el bloque `Txt2` y la vista previa rehecha sin las capas de ajuste. Comprobado: 55 capas, 16 bits, 3300 × 2400, ninguna otra capa cambiada; PyOECF sigue rellenando el cajetín desde ella. La plantilla anterior (textos de 2018: «Canon R7», «Luster JBP»…) está en git (commit d415c1e).
    - `lamina.py`: «cajetín» → **cartela** en el código (`GRUPO_CARTELA`, `MARCO_CARTELA`, `BORDE_CARTELA`, `rellenar_cartela()`, `self.__cartela`; los nombres del PSD, «Cajetín de datos» y «Cajetín», no cambian), `FIN_PARRAFO` → `FIN_LINEA` y `parrafo` → `bloque`; las capas se buscan con `isinstance(…, Group)` y `isinstance(…, TypeLayer)` (fuera 6 errores de Pylance), `KLA.TRANSFORM_X` y `TRANSFORM_Y` en vez de `transform[4]` y `[5]`, un `# type: ignore` explicado en `rawpy.ColorSpace`, paréntesis y `cSpell:ignore` ordenado. **Criterio de docstrings (Tony):** todo lo nuestro con docstring (VS Code lo enseña), lo externo (claves y valores que impone el formato PSD) sin docstring y con un comentario de grupo; qué sale en la documentación se decide en MkDocs (`members:`, `filters:`), no quitando docstrings. La lámina de TD, al 100 % y al 50 %, igual que antes: 55 capas, ninguna distinta, misma vista previa.
    - **`lamina.py` → `psd.py`** (Tony: «es más fácil entender psd que lámina»): clase `Lamina` → `Psd`, constantes `KLA` → `KPSD`; en `main.py`, `self.lamina` → `self.psd`, `lamina_tiff` → `psd_tiff`, `val_lamina_tiff` → `val_psd_tiff`, `caja_lamina` → `caja_psd`, `EmpezarLaminaTiff`/`LeerLaminaTiff`/`ReiniciarLamina` → `…Psd…`, y `TXT_LAMINA`, `TXT_FASE_LAMINA`, `TXT_LEYENDO_LAMINA`, `TXT_SIN_LAMINA`, `TXT_PREGUNTA_LAMINAS`, `TXT_TITULO_LAMINAS` → `…_PSD`. Los textos que ve el usuario siguen diciendo «lámina». Comprobado: escribe `Soportes100.psd` y `Soportes50.psd` con la cartela; la app importa.
    - **`libro.py` → `excel.py`** (Tony, como `psd`: más claro): clase `Libro` → `Excel`, constantes `KLI` → `KXL` (tres letras, como `KLI`: no se mueve ninguna línea), `self.__libro` y `libro` → `__excel` y `excel`, `TERCIOS_LIBRO` → `TERCIOS_EXCEL`; `src/kernel/textos_libro.py` → `textos_excel.py` y `textos_libro()` → `textos_excel()`; en `main.py`, `EXTENSION_LIBRO`, `TXT_LIBRO`, `TXT_ERROR_LIBRO` y `TXT_SIN_LIBRO` → `…EXCEL`. Hecho con el tokenizador de Python: solo nombres de código; los textos y comentarios en español («el libro», «Libro escrito») no cambian, salvo los que nombran el código (`KLI.F_*`, `Libro.filas`…). Comprobado con TD, con revelador y sin él: el `.xlsx` igual por dentro (29 partes, ninguna distinta salvo la fecha) y la ficha igual píxel a píxel. Quedan en `excel.py` tres sangrías mal (líneas 856, 1773 y 3074) que ya estaban en el commit, para su revisión.
    - `excel.py` (hecho). **Tanda 1, tipos:** `-> Format` y `-> Chart` (antes `-> object`) y `cast(Chart, …)` en los `add_chart`; de 314 avisos a 179. **Tanda 2, nombres sin tilde** (los de `excel.py` y sus claves en `textos_excel.py`; también `KTE.RECHAZO_DISPERSION`/`ASIMETRIA` → `RECHAZO_DISP`/`ASIM`, `ZonaMedida.panoDispersionRGB`/`panoRecortadoRGB` → `telaDispRGB`/`telaRecortadoRGB`, `KTR.PIXELES_MPX` → `PX_MPX`): hoja Análisis → **`RESUMEN`** (`fmt_resumen`, `T_HOJA_RESUMEN`…), paño → **`TELA`**, L* leído → **`APUNTADO`** (no `LECTURA`, que es el ruido de lectura), tamaño de letra → `LETRA`, de gráfica o marcador → `MEDIDA`, gráfica → `GRAF`, dispersión → `DISP`, desviación → `DEV`, máximo → `MAX` en constantes y `tope`/`topes` en variables (no tapan `max()`), mínimo → `MIN`/`piso`, sección → `APARTADO`, después → `TRAS`, señal → `SIGNAL`, fracción → `PART`, relación → `RATIO`, y otros. Los nombres definidos de Excel (`RelacionSR`…), los valores de las claves y las del JSON no cambian. Huecos de texto: `{camara}` → `{cam}` y `{maximo}` → `{tope}`. Hecho con el tokenizador y comprobando choques (`F_LECTURA` ya existía). Comprobado con TD, con revelador y sin él: el `.xlsx` igual por dentro y la ficha igual píxel a píxel; incidencias de Luis, bien. **Tanda 3:** cierres fuera (las 8 funciones internas pasan a métodos de `Excel` con sus datos por parámetro: `fmt_formula`, `rango_columna`, `celda_desp`, `rango_graf`, `linea_graf`, `marcador_graf`, `nueva_graf`; donde se usaban, `functools.partial` fija esos parámetros, p. ej. `fmt = partial(self.fmt_formula, banda)`, y las llamadas no cambian); `formula()` y `formula_matriz()` envuelven `write_formula` y `write_array_formula` con el único `# type: ignore` explicado (XlsxWriter declara el resultado como `int`); los valores internos de las claves `T_`, `F_` y `U_` siguen a su nombre (`T_HOJA_RESUMEN = "hoja_resumen"`), no los `C_` (nombres definidos de Excel, se ven en las fórmulas) ni los `R_`/`Z_` (claves del JSON); `numeros` → `cifras` (valores) o `formato_num` (formato de un eje), `numericas` → `cols_num`, `__rotulos` → `__etiquetas`. Avisos: de 314 a unos 30 (19 de Pylance, sangrías y lo que viene de otros módulos). Cada paso, con el `.xlsx` de TD igual por dentro. **Tanda 4 (hecho):** los 19 de Pylance arreglados de raíz, sin `# type: ignore`: las constantes del libro mezclan números y claves de texto, así que `valores_constantes()` devuelve `dict[str, Any]` (y sustituye a tres `dict((c[0], c[1]) for c in KXL.CONSTANTES)`); `limites_texturas()` devuelve `dict[str, Tramo]` (`Tramo` = sombra, luz y ancho; eso quita el `# type: ignore` de la ficha); donde se comprobaba `x[i] is None`, el valor va antes a una variable; `nueva_graf` sin el parámetro `fila`, que no usaba. Sangrías con el autopep8 de VS Code (solo E127, E128 y E131) en `excel.py`, `textos_excel.py` y `kernel.py`: textos idénticos salvo los huecos cambiados a propósito. **162 paréntesis explícitos** puestos con el árbol de sintaxis (comprobado: el árbol, idéntico). **Docstrings:** solo en las 21 constantes de `KXL` que usan otros archivos (ficha, `main.py`); las `T_` no (su texto está en `textos_excel.py`) ni las que solo usa el módulo (criterio de Tony, ver memoria). Claves del JSON: `R_MAX` → `"max"`, `R_FIN_LINEAL` → `"fin_lineal"` (FE aún no lee el JSON). **Flake8 limpio y 0 errores de Pylance.** `ZonaMedida.desviacion` → `dev` (en `review.py`; el JSON no cambia, su clave sigue siendo `J_DESVIACION`). Queda de fuera el resto de «pano» en el proyecto (→ «tela», pendiente).
    - `marcas.py`: nombres sin tilde (`codigo` → `code` y `CODIGO_DESCONOCIDO` → `CODE_DESCONOCIDO`, con su hueco `{code}`; `POSICION_*` → `POS_*`, `posicion` → `pos`; `PATRON_KELVIN` → `REGEX_KELVIN`); el resultado de `etiqueta_tiff` se desempaqueta (`_, cuenta, valor`) en vez de `[0]` y `[2]`, y en Nikon el tipo se compara tras desempaquetar; `f.seek(0, os.SEEK_END)` en vez de `seek(0, 2)`; `#` antes de cada función; 4 paréntesis (árbol igual) y 2 sangrías; `cSpell:ignore` en orden. `KM` sin docstrings: fuera solo la usa `textos_excel.py` como claves de texto (`B_*`). Igual que antes en `leer_balance` y `leer_kelvin` con los 498 RAW. Flake8 limpio.
    - `revelado.py`: nombres sin tilde (`analisis` → `review`, `RECORTE_MAXIMO` → `RECORTE_MAX`, `maximo` → `tope`, `ICC_PARAMETROS` → `ICC_PARAMS`, `parametros` → `params`, `funcion` → `func`, `leidos` → `crudos`); códigos de incidencia `TAMANO_DISTINTO` → `MEDIDA_DISTINTA` y `COMPRESION` → `COMPRIMIDA` (nombre y valor; también en `main.py`); `tif.pages.first` en vez de `pages[0]` (Pylance: siempre una página completa); 36 paréntesis (árbol igual); `#` antes de cada función; `cSpell:ignore` en orden. Comprobado con los 52 perfiles ICC del sistema (ghostscript y colord) y 22 TIFF fabricados con ellos al tamaño del sensor de TD (y uno pequeño y otro sin perfil): igual que antes. Flake8 limpio. De paso, `main.py`: sus sangrías descuadradas por los cambios de nombre de hoy, alineadas con autopep8 (árbol igual); Flake8 limpio.
    - **«pano» → «tela» en todo el proyecto** (Tony: «pano» se lee como panorámica): 147 cambios con el tokenizador, en 8 archivos: `Pano` → `Tela`, `buscar_pano` → `buscar_tela`, `SIN_PANO`/`PANO_MIN` → `SIN_TELA`/`TELA_MIN` (nombre y valor), `Review.pano` y `OECF.pano` → `.tela`, `ZonaMedida.pano_nivel`/`pano_dispersion`/`pano_recortado` → `tela_nivel`/`tela_disp`/`tela_recortado`, `ventana_pano`, `hay_pano`, `TXT_*_PANO` en `main.py`, y las claves del JSON (`"tela"`, `"tela_nivel"`…; FE aún no las lee). No cambian los textos con «paño». El nombre definido de Excel `PanoRecortadoMax` se quedó al principio (lo ve el estudiante); **2026-10-19, Tony («nada de pano»): pasa a `TelaRecortadoMax`** (`KXL.C_TELA_RECORTADO_MAX`, la nota de texturas de `textos_excel.py`, dos docstrings de `excel.py` y `prompt_ia.md`); la hoja Constantes se ordena al escribirla, así que cae en su sitio. TD: la misma ventana de tela.
    - `review.py`: `J_DESVIACION` → `J_DEV = "dev_rechazadas"`; `Review.revelador` declarado `tuple[float, ...]` (sin dato es NaN, no None); `_por_canal` → `_rgb_canales` (siempre da valor; quien admite None lo dice: fuera el `# type: ignore` del negro); `_tupla_num` para lo que nunca es None (el negro); `range(len(Transferencia._fields))` en vez de `range(3)`; 16 paréntesis (árbol igual); `#` antes de cada función. Comprobado: ida y vuelta del JSON y ruido de lectura de TD (4,46 / 3,72 / 4,43). Flake8 limpio. Queda de nombres con tilde `ZonaMedida.dispersion`/`dispersionRGB` (cruza con teselas, aparcado).
    - `kernel.py` (último de la revisión): 38 paréntesis (árbol igual) y sangrías; nombres sin tilde: `OECF.seleccion` → `OECF.select` (y `__select`), `OECF.vacias` → `OECF.huecos` (también en `informe`, `rejilla`, `main` y `json_estudio`, cuya clave del JSON pasa a `"huecos"`), `NO_VALIDO_NOMBRE` → `REGEX_RARO`, `ZONA_MIN/MAX_ANALISIS` → `ZONA_MIN/MAX_REVIEW`, `__tamano` → `__medida`, locales `maximos` → `topes` e `indices` → `pos_raw`; docstrings en `KT.NOMBRE_TAPADA` y `KT.PARTE_TAPADA` (las usa `json_estudio`). Comprobado midiendo TD: la misma tela, 6727 teselas buenas, ruido 4,46 / 3,72 / 4,43 y las mismas 4 incidencias. Flake8 limpio. **Con esto, todos los módulos de biboecf están revisados** (queda «dispersion» → «disp», aparcado).
    - `secuencia.py` (Tony, adelantado): `KS.MINIMO_LADO` → `KS.MIN_LADO` y `KS.MINIMO_BALANCES` → `KS.MIN_BALANCES` (como `MIN_TESELAS`, `MIN_ZONAS`); docstrings en las constantes de `KS`, en `Secuencia` y en `balance_personalizado` y `secuencia` (antes, comentarios encima); paréntesis; `tomas` pasa a `{índice: tercioEV}` de las leídas (fuera dos avisos de Pylance y sus dos `# type: ignore`); la local `indices` → `tomas_racha`; `#` antes de cada función; los dos `lambda` de «el lado más largo» (cierres sobre `rachas`) pasan a `_mas_larga(posiciones, rachas)`. `Secuencia` se queda `NamedTuple`: es un registro de datos sin comportamiento (a diferencia de `Select`). Igual que antes en las 13 series y en 30000 inventadas.
    - **2026-10-19, `kernel.py` rehecho:** el `kernel.py` revisado (punto de arriba) no llegó al commit `f177008` ni a los siguientes: tenía otra vez `vacias`, `seleccion`, `__tamano`… mientras `informe`, `rejilla` y `json_estudio` ya llamaban a `OECF.huecos` (habría fallado). Rehechos los nombres con los mismos de arriba (`select`, `huecos`, `ZONA_MIN/MAX_REVIEW`, `__medida`, `REGEX_RARO`, `topes`, `pos_raw`) y los docstrings de `NOMBRE_TAPADA` y `PARTE_TAPADA`; **no** los 38 paréntesis (no se pueden recuperar). Pylance: `temperatura()` con rojo, verde y azul por separado y `Medir` sale si `tela` es `None` (nunca pasa: la pone `Seleccionar`). **`json_estudio.py`:** `hay/leer/grabar_analisis` → `hay/leer/grabar_review`, `KD.ANALISIS` → `KD.REVIEW` (la clave del JSON sigue siendo `"analisis"`). **`main.py`:** 9 errores de Pylance (los «puede ser `None`» con `# type: ignore` como el resto del archivo; `ErrorInesperado(traza: TracebackType | None)`; `TextosCajetin` compara cada valor con `None`); nombres sin tilde: cajetín → **cartela** (como `psd.py`: `TXT_CARTELA_*`, `FORMATO_FECHA_CARTELA`, `TextosCartela`), `TXT_YA_ANALISIS` → `TXT_YA_REVIEW`, `{camara}` → `{cam}`, `{anio}` → `{year}`, `TK/SEP_POSICION` → `TK/SEP_POS`, `self.medicion` → `self.medida`, `analisis` → `review` (y `review_revelado`), `tamanos` → `sizes`, `opcion` → `radio`; `src/kernel/actualizacion.py` → **`update.py`**. Valenciano en el `cSpell:ignore` (lista manual, Tony). Problemas de VS Code: 0 en los tres. **`rejilla.py`:** `from bib import std` (antes `clases`, que ya no existe: la app no arrancaba); **fallo real:** `KR.TXT_LADOS` estaba dos veces y la segunda (los lados de la luz desigual) pisaba a la primera, así que la incidencia `LADOS` («Solo hay 1 lado») habría dado `KeyError`: la segunda pasa a `TXT_DONDE_LADO`; `FORMATO_DESVIO` → `FORMATO_DEV`, `posicion` → `pos`, `EXITO`/`TEXTO_EXITO` → `OK`/`TEXTO_OK`; valenciano en su `cSpell:ignore`. Problemas: 0. **`textos_excel.py`:** los nombres de las constantes del libro ya no se escriben a mano en los textos: van como huecos con el nombre de la constante de `KXL` en minúsculas y sin `C_` (`{snr_minima}`, `{mpx_referencia}`, `{tela_recortado_max}`…), y `Excel.con_nombres()` los rellena una sola vez al crear el libro, a partir de todas las `KXL.C_*` (una constante nueva sirve sin tocar nada). Comprobado: los 286 textos salen idénticos al commit anterior en los tres idiomas (salvo `PanoRecortadoMax` → `TelaRecortadoMax`). Valenciano en su `cSpell:ignore` (unas 315 palabras, sacadas quitando las que están en los diccionarios de español e inglés del sistema). Problemas: 0. **`main.py` sin cierres:** las funciones internas de `caja_carpeta`, `caja_cam`, `caja_serie`, `caja_psd`, `Ajustar` y `Confirmar` pasan a métodos `_x` de `Ventana` (junto a su caja, con su comentario); lo que compartían, a atributos declarados en el `__init__` y reiniciados en su `Reiniciar*` (`val_serie`, `barra_serie`, `val_copia`, `val_rejilla`, `boton_analizar`, `boton_generar`, `dialogo_confirmar`); las `lambda` que capturaban datos, a `functools.partial` con los datos a la vista: las de traducir, con `_componer(texto, **datos)` (también `ApuntarTexto`), y las demás con su método (`_texto_resumen`, `_texto_rejilla`, `_texto_fecha`, `_texto_exp`, `_texto_mensajes`, `_texto_psd_tiff`). Quedan cuatro *generator expressions* de una línea (no son funciones). Pylance y Flake8: 0. **Probado con la ventana manejada por un script** sobre una copia de TD: carpeta, Preparar (44 tomas, 42 copias), Analizar, Generar (6727 teselas buenas, libro, ficha, lámina; la luz que cambió), los tres idiomas, `Confirmar`, y Analizar revelado con tres TIFF sRGB fabricadas (3 de 3 medidas, libro y ficha rehechos, lámina desde las TIFF). Sin probar: el explorador de carpetas de Linux (necesita elegir a mano; su código solo cambió de sitio). **`main.py`, últimos nombres sin tilde:** `boton` → `btn` (`btn_preparar`, `btn_generar`, `BTN_RUEDA_ARRIBA`…; `botones` se queda: no lleva tilde), `codigo` → `code`, `leidas` → `reads`, `TAMANO_INCIDENCIAS` → `MEDIDA_INCIDENCIAS`, `TXT_TAMANO` → `TXT_MEDIDA`; fuera del `cSpell:ignore`. Sangrías con el autopep8 de VS Code (E127/E128/E131); árbol de sintaxis igual al de solo renombrar. Flake8: 0. **Nombres de las constantes del libro, en un solo sitio (`KXL.C_*`):** `prompt_ia.md` los lleva como huecos (59: `{snr_minima}`, `{zona_zv}`…) y la hoja IA los rellena con `Excel.con_nombre(texto)` (de ella sale ahora `con_nombres`, que hace lo mismo con todos los textos); comprobado: la hoja IA recibe el mismo texto que antes, letra a letra. En los docstrings y comentarios de `excel.py` (32) y `constantes.py` (2), el nombre del libro pasa a ser el de Python (`SNRMinima` → `C_SNR_MINIMA`), para que siga siendo cierto si el del libro cambia. **Ficha PDF en el ejecutable: [VERIFICADO por Tony, 2026-10-19]:** Generar con `./dist/PyOECF` escribe la ficha PDF. **Revisión de la app (`src/kernel/`) acabada:** 67 paréntesis explícitos (`main.py` 34, `rejilla.py` 25, `json_estudio.py` 5, `constantes.py` 3), puestos con una herramienta sobre el árbol de sintaxis (dentro de `and`/`or`, las comparaciones, cuentas y `not`; dentro de una comparación, las cuentas; en una cuenta, la parte de otra prioridad; en `x if c else y`, la condición y las cuentas; el signo menos de un número, no) y comprobado que el árbol no cambia. `biboecf/kernel.py` da 0 con ese criterio: sus paréntesis no se perdieron, solo los nombres. Docstrings: 63 funciones y métodos públicos (59 desde su comentario `# ---`, 4 nuevos: `version`, `caja_ayuda`, `caja_carpeta`, `caja_cam`), la línea `#` sola delante de cada método (también de los privados) y docstring en las 16 constantes que se usan fuera de su módulo (`K.NOMBRE`, `K.ES`…, `KA.URL_RELEASES`; las `TXT_*` no). Comprobado: sin los docstrings, el código es el mismo. `_idioma_sistema`: `codigo` → `code`. `contexto.md`: lo que ya no vale, en la tabla del apartado 1 (nombres sin tilde, docstrings con punto, campos borrados). Flake8 y Pylance: 0. Con la misma herramienta, los **seis paréntesis que se escaparon en biboecf**: las condiciones de `x if c else y` en `ficha.py` (2), `teselas.py` y `transferencia.py` (2), y `revelador or ((None,) * n)` en `excel.py`; árbol igual. Con eso, toda la app y biboecf dan 0 con ese criterio. **Últimos nombres sin tilde de biboecf** (los aparcados de `teselas.py` y «dispersion» → «disp», juntos): `dispersion` → `disp` en `Teselas`, `Medida`, `Tela` y `ZonaMedida` (y `dispersionRGB` → `dispRGB`, `dispersion_verde` → `disp_verde`, `_mediana_dispersion` → `_mediana_disp`; en `teselas`, `review`, `kernel`, `transferencia` y `excel`), `asimetria(_verde)` → `asim(_verde)`, `pixeles` → `px`, `patron` → `mosaico` (el mosaico de colores del sensor), `indice(s)` → `idx(s)`, `validas` → `usables` (no `buenas`: ya son las teselas buenas de la tarjeta). Las mismas palabras como locales en `informe`, `psd`, `json_estudio`, `main` y `rejilla` (cSpell no las marcaba: existen en inglés o como verbo), con los mismos nombres. La clave del JSON sigue siendo `"dispersion"` (`KAN.J_DISPERSION`, como `J_DESVIACION`). Hecho con el tokenizador (solo nombres de código) y comprobado que el árbol solo cambia en los nombres; el `estudio.json` de TD se lee y la ida y vuelta da lo mismo. Flake8: 0. **`Review` y `ZonaMedida`, clases y no tuplas** (Tony, 2026-10-19: «tiene demasiados métodos como para ser una tupla»): `@dataclass(frozen=True, slots=True, kw_only=True, eq=False)`. `kw_only` obliga a crearlas con los nombres de los campos: se reescribieron con nombres las cuatro construcciones (`OECF.Medir` y `review_de_dict`/`_zona_de_dict`), que iban por posición (25 y 9 campos, varios del mismo tipo seguidos: `alto`/`ancho`, `iso`/`tv`/`f`…); `eq=False` porque `motivos` es un array de numpy. `main.py`: `_replace` → `dataclasses.replace`. Criterio: tupla para solo datos y pocos campos; clase si tiene comportamiento propio o muchos campos. Comprobado: medir TD da el análisis **idéntico** (el JSON entero, byte a byte), el `estudio.json` de TD se lee y la ida y vuelta da lo mismo, libro y ficha se escriben, y crearla por posición o cambiarla da error. Flake8 y Pylance: 0. **Todas las `NamedTuple`, creadas con el nombre de cada campo** (Tony: «por supuesto que con nombre de campo»): 46 creaciones; las largas, un campo por línea; las tres con `*` reescritas sin él (`Cam(marca=…, modelo=…)`, `Tela(nivel=…, disp=…, histograma=…)`, y el verde de la curva con `_media` por campo en vez de recorrer `_fields` por posición). Comprobado con el código de antes y el de ahora sobre TD y Aaron: análisis, incidencias, curvas por canal, resultados del libro y cámara de cada RAW, **idénticos**. **Ayuda de desarrollo (`doc/src_dev`) con tablas automáticas** (2026-10-19): el hook común `Repo/doc/mkdocs/mapa_codigo.py` (en PyOECF, el enlace `doc/src_dev/mapa_codigo_slr.py`, declarado en `hooks:` del `mkdocs.yml`) cambia marcas de las páginas por tablas sacadas de su fuente, sin escribir nada dos veces: `<!-- mapa: src.biboecf -->` (y `src.kernel`) da la tabla de lo que expone (`__all__`) con la primera frase de cada docstring (la página de biboecf pasa de unas 41 000 líneas de HTML a una tabla de 56 filas), y `<!-- requisitos -->` da en `A)-Información/Y-Requerimientos.md` las tablas de `rec/requirements/requirements.conf` (paquete, versión y el comentario que tiene encima; un bloque por variable). `main` y `bib` siguen con `:::` de mkdocstrings (Tony). Anclas de las páginas de código: `#biboecf` y `#kernel` (antes, las tres `#bib`). **`SymlinksLocal` (Repo):** excepciones `ex: <ruta>` arriba del `.txt` para los enlaces que conservan su nombre (`index.md`, `1-Presentacion.md`; `LICENSE.md` siempre); el `.txt` lo genera `--leer`, no se edita a mano. **Caja Lámina, ventanita de mensajes** (Tony, 2026-10-19): los botones de tamaño reservaban 100 px (lo de customtkinter) y dejaban unos 48 px de hueco hasta la ventanita; ahora miden su contenido (`width=KV.ANCHO_CONTENIDO`, 0) y el hueco es `MARGEN` (10 px), como el de la línea vertical a «Tamaño». Las líneas de la ventanita se cortan a su ancho real (`_ajustar_mensajes`, con el evento `KV.TK_CAMBIO_MEDIDA`, que usa también el lienzo); `ANCHO_MENSAJES` queda como ancho inicial. **La ventana crecía al cambiar de idioma tras Generar:** al terminar, `ActivarCarpeta` enseña «Analizar revelado» y la caja Carpeta pide más ancho, pero nadie reajustaba la ventana hasta el siguiente `Ajustar` (el de `Traducir`); ahora se ajusta al aparecer o desaparecer el botón. Medido con TD: ventana 1156 px nada más acabar Generar e igual en los tres idiomas; hueco de 10 px en los tres.

- Todo está en `src/` (ya no hay `temporal/`):
    - `src/kernel.py`: `Exp` (f, tv, iso, siempre en ese orden), `Toma` y el objeto **`OECF`** (ver 2.9).
    - `src/secuencia.py`: el protocolo (`KS`), `Secuencia`, `secuencia(tercioEVs, oscuras)` y `balance_personalizado(tercioEVs, balances)`.
    - `src/zonas.py`: `KP` (con `DESVIO_MAXIMO`, 0,33 tercios), `exp_relativa`, `calcular_tercio_exacto`, `zona_tercio` (`(5, 1)` es ZV.3) y `texto_zona` (Z0, Z0.3, …, ZV, …, ZX).
    - `src/cam.py`: `Cam` (marca, modelo y `nombre`, sin repetir la marca), `KC` y `leer_cam()` (lector TIFF propio).
    - `src/marcas.py`: lo propio de cada marca (`KM`): `leer_balance()` y `leer_kelvin()` (ver abajo).
    - `src/constantes.py`: clase `COM` con las constantes compartidas: `extensiones`, `margenTV` y lo común de TIFF (`bytes_cabecera`, `firmas_tiff`, `tipo_ascii`, `max_entradas`, `bytes_entrada`, `bytes_en_entrada`, `etiqueta_exif`, `etiqueta_notas`, y los formatos de `struct`: `FORMATO_ENTERO`, `FORMATO_CORTO`, `FORMATO_ENTRADA`, `FORMATO_LISTA`, `BYTES_CORTO`, `POS_PRIMER_DIRECTORIO`). Se importa como `COM as KCOM`. Cada módulo tiene sus propias constantes (`KT`, `KS`, `KP`, `KC`, `KM`); las que usa más de uno van aquí.
    - `src/tiff.py`: lectura de directorios TIFF que comparten `cam.py` y `marcas.py`: `orden_tiff`, `primer_directorio`, `entero_tiff`, `corto_tiff`, `etiqueta_tiff`, `lista_tiff`, `ascii_tiff`, `texto_ascii`. **Es el único módulo que lee con `struct`**: `cam.py` y `marcas.py` no escriben formatos a mano (2026-10-12). `leer_cam()` devuelve `None` si el archivo no se puede abrir.
    - `src/teselas.py` (`KTE`; piezas B y C, 2026-10-12): teselas de **48 px** (la máscara de colores de una vale para todas). `medir_teselas()` → `Teselas` (nivel y dispersión por canal R0, G1, B2, G3; nivel, dispersión y asimetría del verde). `buscar_pano()` → `Ventana` del paño o el código de por qué no (corte de Otsu, sin número fijo por cámara). `seleccionar()` → `Seleccion` (motivo de cada tesela: buena, no es de tarjeta o rechazada por nivel, dispersión o asimetría; `rechazadas`, `porcentaje`, `hayTarjeta` con `MIN_TESELAS`). `oscuridad()` → `Oscuridad` (negro de las tapadas o el declarado; ruido del borde tapado izquierdo o de las tapadas, y si difieren). `medir_toma()` → `Medida` (tarjeta por canal, desviación de cada rechazada y `Pano` con su histograma). `fraccion_recortada()`, `matriz_color()` y `temperatura()` (McCamy). `revelar()` y `recorte()`, para la vista previa.
    - **Comprobado con la R7** frente a la hoja `Datos` del libro de Tony: los mismos archivos por zona y como mucho **0,01 zonas** de diferencia; ruido 4,46 / 3,72 / 4,43 (la guía decía 4,46 / 3,77 / 4,43); luz de la ZV 5058 K, estable de Z1 ⅔ a Z8 ⅔. Tarda unos 1,8 s por toma.
    - `src/analisis.py` (`KAN`): `Analisis` (lo medido en los RAW: lado, tamaño del sensor, motivo de cada tesela, paño, negro y ruido con su origen, matriz de la cámara, las 31 zonas y las demás Z-V) `ZonaMedida` (tarjeta y paño por canal y desviación de las rechazadas; `nivelRGB` y `dispersionRGB`). `analisis_a_dict()` y `analisis_de_dict()`: a datos de JSON y de vuelta (comprobado: ida y vuelta igual). El mapa de teselas va como texto, una cadena por fila: `.` buena, espacio no es tarjeta, `N`, `D` o `A` según el motivo. `BalanceMedido` (2026-10-12): cada toma de balance de la cámara, con su nombre, los Kelvin que guarda la cámara y los que de verdad aplica (la luz que sus multiplicadores dejan neutra; R7: Sombra 7000 → 6634 K, Flash 6084 → 5847 K); `Analisis.balancesDistintos`, sin repetir los iguales (Tony: las cinco «Kelvin» a 5600, una vez). La temperatura de la luz por zona se quitó: no servía (Tony). El análisis lleva también la cabecera del libro (cámara, fecha y exposición de la ZV).
    - `OECF.Medir()`: generador, una toma cada vez (33 en la R7, unos 60 s; 29 en la Sony de Sofía, unos 40 s); empieza dando `(0, total)` antes de calcular nada, para que «Midiendo 1 de…» salga al momento (2026-10-13); al terminar, `OECF.analisis`. El paño recortado se cuenta al final, con el máximo de la serie (`KTE.UMBRAL_RECORTE`, el mismo que la constante `UmbralRecorte` del libro).
    - `src/libro.py` (`KLI`, `Libro`; pieza D, hecha): el libro se escribe desde un `Analisis`, con XlsxWriter. Hechas `Constantes`, `Datos` y `Cálculo` (bloques 1 a 3; el 3, con sensor y revelador), comprobadas con el libro de Tony: el bloque 1 de la R7 da los resultados del apartado 6 de la guía (como mucho 0,02 zonas). Fórmulas protegidas (en blanco si falta un dato) y matriciales donde hacía falta (sin el `1000`). La media de las Z-V, matricial: solo las que no se apartan de la ZV más que `ToleranciaLineal`. Los textos, en la app: `src/kernel/textos_libro.py` (tres idiomas; el libro sale en el idioma de la ventana). **2026-10-13:** `Resumen` lleva la **profundidad RAW** bajo la fecha (`Analisis.bits`, `bits_raw` en el JSON; los análisis anteriores la dejan en blanco hasta volver a Generar). Un valor no finito (la dispersión infinita de una toma que mide 0) se escribe en blanco en `Datos` y se salta en `Rechazadas`, en vez de romper el libro. Si el libro falla por otra cosa que no sea `OSError`, la ventanita lo dice con el error y Generar se reactiva. Generar y las láminas desde las TIFF acaban con «Finalizado.». También del 2026-10-13: hoja **IA**, la última, con `src/bib/biboecf/src/rec/prompt_ia.md` (apéndice F); en `Cálculo`, la señal/ruido de un canal saturado (dispersión 0) dice `TextoSaturado` («saturado») en vez de 0, la nota del bloque 1 ya no la tapa la cabecera y, debajo de la tabla, una nota dice que la latitud usa el suelo por señal/ruido y que es asimétrica a propósito. Con TD, los resultados del bloque 1 siguen siendo los de 6.7. **2026-10-15:** las derivadas de `Constantes` (`LuzPorTercio`, `LuzZV`) se escriben con su valor calculado (`valores_constantes()`); antes el archivo guardaba 0 y un visor sin recálculo lo mostraba. Era la única de las 54 `write_formula` sin valor (revisión externa del libro, punto 3.5b). **Latitud de texturas** (2026-10-15, Tony): lo que el alumno lee como latitud de su cámara sale del **paño**, no de la señal/ruido de la tarjeta (esa sigue en Cálculo, bloque 1, para auditar). Datos tiene una sección «Paño por zona» (dispersión y fracción recortada por canal: `ZonaMedida.panoDispersionRGB` y `panoRecortadoRGB`); Cálculo, el bloque 4 (`bloque_texturas`, verde): textura del paño = √(dispersión paño² − dispersión tarjeta²), textura/ruido, textura conservada frente a la ZV y paño recortado, y los límites (`texturas()`, `limites_texturas()`). Sombras apreciables: donde la textura/ruido llega a `RoseTextura` = 5 (del criterio de Rose: Rose 1948, Burgess 1999; por píxel, así que no es Rose tal cual) y no vuelve a bajar hasta la ZV, interpolado y al tercio más próximo; recomendadas, `MargenSombras` = 1 tercio más arriba (un Rose más alto no es estable: de 5 a 6 mueve hasta 2 zonas). Luces apreciables: la última que conserva `TexturaConservada` = 50 % de la textura de la ZV; recomendadas, la última con `PanoRecortadoMax` = 10 % de paño recortado como mucho. Un tercio sin dato (toma sin medir: infinita) no corta la cadena. En Análisis, el bloque «Latitud de texturas», entre la cabecera y el ruido, en tercios (`NUM_TERCIOS`). **Validado con la vista de Tony en la R7 (TD)**: apreciable Z2 → Z8 ⅓ (6 ⅓ zonas), recomendada Z2 ⅓ → Z8 (5 ⅔); Tony: Z2 límite de textura apreciable, Z1 ⅔ no debe tener, Z8 ⅓ viable, Z8 su límite, Z8 ⅔ sin textura. Las 15 series de `gris18` generan el libro. **[NO VERIFICADO]**: el recálculo de las fórmulas en una hoja de cálculo (no hay LibreOffice en la torre); los valores guardados son los de Python. La textura depende del paño: entre series va de 0,29 a 0,46. `fila_canales` deja en blanco cualquier valor no finito (antes solo NaN: la serie de Sofía rompía el libro). **Formato (2026-10-15, Tony: nada debe salirse de la pantalla):** las notas largas (título de cada hoja y notas de sección) se escriben con `nota()`: ocupan las columnas de su tabla que caben en `KLI.ANCHO_NOTA` (165 caracteres, unos 1200 px), partidas en líneas, y la fila crece según `lineas()` (estimado: XlsxWriter no ajusta altos). Constantes, **por orden alfabético** y con «Qué es» a 100,71 de ancho, partido en líneas. En Datos, los rótulos de fila largos (ruido, negro, curva de transferencia) ocupan las tres primeras columnas (`rotulo_fila`) y las columnas de valores pasan a 14 (no cortaba «Multiplicador»). `prompt_ia.md` documenta la latitud de texturas (§2, §3 y §4, puntos 12 a 15). **Rechazadas** (2026-10-15, Tony): junto al recuento de cada motivo, una columna «Qué es» con lo que significa (`KLI.EXPLICA_MOTIVO`; los umbrales salen de `KTE`: `NIVEL_MAX_ZONAS`, `RAREZA`, `LADO`), y la nota dice que los filtros van en orden y cada tesela cuenta en el primero que no pasa. **Análisis en rejilla** (2026-10-15, idea de Tony, «el truco de siempre»): todas las filas miden lo mismo (`KLI.ALTO_REJILLA` = 15, el alto por defecto; `marco(alto=…)`), porque las dos tarjetas comparten filas y antes una estiraba las de la otra. Lo alto ocupa varias filas combinadas: título (`FILAS_TITULO_ANALISIS`), cabeceras (`cabecera_tarjeta`, `FILAS_CABECERA` / `FILAS_CABECERA_ALTA`), notas (`nota_tarjeta`, filas según sus líneas: `filas_texto`) y rótulos del ruido que no quepan en una línea. Se quitaron `alto_analisis`, los `ALTO_*_ANALISIS` y `FILAS_SUGERIDO`. Tarjeta derecha, tras las diferencias medias: **«Decisiones propias»** (Tony: los puntos de curva que decide el estudiante; solo para apuntarlos, el libro no los usa): barra, cabecera doble (zona, entrada, salida a cada lado, `LADOS_DECISIONES`) y `FILAS_DECISIONES` = 5 filas (10 puntos: Tony, «7 ya es una locura»), en color dato; zona validada con la lista de la tabla por zona, entrada y salida enteros de 0 a `EscalaCurva`. Justo debajo (Tony: fila 26), barra **«Recomendaciones»** y la tabla por zona: con la rejilla ya no se alinea con la cabecera de los balances (`analisis_derecha` sin `fila_cabecera`). **Gráficos** (2026-10-15, Tony: lo que más interesa al estudiante, primero): orden en `KLI.ORDEN_GRAFICAS` (curva tonal, diferencia en L\*, esperado y obtenido, desviación lineal, desviación completa, señal/ruido); el número del título sale de ahí (`FORMATO_TITULO_GRAFICA`) y los textos ya no lo llevan. Claves por contenido (`T_G_CURVA`…), no por número; las referencias por número (comentarios, `prompt_ia.md`, reglas de esta memoria) pasan a nombre. **Color del libro, verde** (2026-10-15, Tony): cabeceras, barras, filas alternas y bordes de tabla pasan de azul a verde (`CABECERA_FONDO` #548235, oscuro para que se lea el blanco; `BANDA` #E2EFDA; `BORDE_TABLA` #A9D08E); `azul_analisis` pasa a `fondo_analisis`. El azul del texto «dato» (#0000FF) no cambia: es otra cosa. **Ficha PDF de la cámara** (2026-10-15, maqueta aprobada por Tony): `src/ficha.py` (`KFI`, `Ficha(ruta, textos, libro)`), con **matplotlib** (`matplotlib~=3.11` en el `requirements.conf` de BibOECF; +16,4 MB medidos en un ejecutable de un archivo). No calcula nada: lo pide al libro (`Libro.analisis`, `valores_constantes`, `texturas`, `limites_texturas`, `nombre_balance`, `tercios_texto`, `curva`) y la curva tonal, a `Libro.puntos_curva()` (`PuntoCurva`), que usa también el bloque 3 de Cálculo (comprobado: el libro de TD sale igual, con margen de 1e-9). Dos páginas A4 en la gama verde: cabecera, latitud de texturas (escala de zonas en su gris con borde, tramos apreciable y recomendado, cifras), gráficas 1 y 2 (curva tonal y diferencia en L\*, con el número de `ORDEN_GRAFICAS`); recomendaciones (zonas enteras: esperado, revelador, entrada, salida; sin fase 2, rayas y la nota `T_SIN_FASE_2`), ruido y negro, balances. Sin datos del estudiante (Tony): Python no ve lo que escribe en el Excel; el revelador sale de las TIFF. Letra DejaVu Sans (va con matplotlib); estilo con `rc_context`, sin pyplot (no toca el estado global ni la ventana Tk). Separador decimal del idioma (`T_SEPARADOR_DECIMAL`). La app la escribe con el libro (`Ventana.EscribirFicha`) al pulsar Generar y al terminar Analizar revelado: `OECF/PyOECF.pdf`. Textos en `textos_libro.py` (`_F = biboecf.KFI`). **Probada con la serie de Sofía con fase 2** (2026-10-15): salió un fallo antiguo: `analisis._rgb` dividía entre cero si no hay ningún verde (su ruido es de la curva, `ORIGEN_CURVA`, y los verdes salen `None`); ahora el verde queda NaN y el libro lo deja en blanco. Analizar revelado solo capturaba `OSError` al rehacer el libro y, con otro error, la caja se quedaba a medias (parecía colgada): ahora captura cualquiera, lo dice (`TXT_ERROR_LIBRO`) y sigue, como Generar. En la ficha: sin dato, hueco en las gráficas y raya en las tablas (no 0 ni «nan»); las barras del revelador, siempre en su color (antes rojas las negativas: no casaban con la leyenda), con la leyenda encima; sin tomas de balance, la nota `T_SIN_BALANCES`. **Latitud contando las dos puntas** (2026-10-15, Tony: «de Z3 a Z8 son 6, no 5»; opción A, las dos latitudes igual): constante `AnchoZona` = 1 (Constantes) y `Libro.latitud()` = alto − bajo + `AnchoZona`, en la latitud sugerida (Cálculo, bloque 1) y en la de texturas (bloque 4, Análisis y ficha). El **rango** (techo − suelo) sigue siendo una distancia. **Probado en la app** con Carolina (D750): Generar escribió libro y ficha; texturas 8 zonas (Z2 → Z9) y 7 recomendadas (Z2 1/3 → Z8 1/3). **Espacio de color de las TIFF** (2026-10-15, Tony odia ProPhoto): el aviso de «espacio desconocido» recomienda solo **sRGB** (o, si no, Adobe RGB), que es la escala de la entrada y la salida de la curva; ProPhoto se sigue **aceptando** al medir (`revelado.py`), solo deja de recomendarse. **Preparar conserva las TIFF** (2026-10-16, Tony): `Copiar()` ya no borra la carpeta `OECF` entera; `OECF.Vaciar()` borra lo que hizo el programa y conserva las TIFF (`KCOM.EXTENSIONES_TIFF`) y las subcarpetas (el programa no las crea: son del usuario). La confirmación de Preparar solo salta si hay análisis (las TIFF ya no se pierden) y dice cuántas exportaciones se conservan (`TXT_TIFF_SE_CONSERVAN`, sustituye a `TXT_YA_TIFF`); `TXT_SE_BORRARA` dice ahora «el análisis se borrará». Probado `Vaciar()` en una carpeta de prueba. **Resumen final con los archivos** (2026-10-16): la ventana apunta en `self.escritos` lo que escribe cada tanda (Generar o Analizar revelado: libro, ficha y láminas; la ficha la apunta `EscribirFicha`) y la última línea es `TextoFinalizado()`: «Finalizado: PyOECF.xlsx, PyOECF.pdf, Soportes100.psd…». **Ningún error silencioso** (2026-10-16, Tony): `report_callback_exception` = `Ventana.ErrorInesperado`: el error que salte en un botón o en un `after` y nadie recoja va a la terminal, para la tarea en marcha, quita `leyendo`, reactiva la caja Carpeta y se dice en una ventana (`MostrarError`, `TXT_ERROR_INESPERADO`). El hilo de `ComprobarVersion` guarda en `error_version` lo que no sea de red y lo enseña `MostrarVersion`. Probado forzando un error en un `after`. **Resultados e incidencias en el JSON** (2026-10-16, Tony): FotoEstación no llevará biboecf (peso extra para algo que se usa al cambiar de cámara): leerá `estudio.json`, que debe bastar para las dos fases y el análisis final. Sección **`resultados`** (`Libro.resultados()`, grabada con `json_estudio.grabar_resultados` al acabar Generar y Analizar revelado): por canal (`canales()`: Z-V media, máximo, techo, suelo, rango, último lineal, primer recortado, suelos sugerido y excelente, latitud sugerida), latitud de texturas (sombras, luces, zonas; `null` sin paño), la curva zona a zona (esperado, objetivo, sensor, revelador, entrada, salida, punto) y las diferencias medias. **Sin constantes** (Tony: FE solo tendrá resultados) y sin textos: lo que no es número, `null`. Las **incidencias**, como códigos (`biboecf.Incidencia`, con nombres de archivo), en `grabar_json`. Los cálculos de Python del bloque 1 pasan a `zonas_canal()`, `maximos()`, `canales()` y `valor_suelo()` (`suelo_snr` solo da la fórmula); las fórmulas del Excel no cambian (Tony: calcular en dos sitios vale: las fórmulas tienen validez académica y de aprendizaje). Comprobado: el libro de Carolina sale igual que el de la app (0 celdas distintas en Cálculo, Análisis y Datos). **Decisiones del mismo día:** el derecheo nunca lo analizará el programa (fuera `derecheos_tercios` y la pieza H de pendientes); lo anotado de colores y de la licencia se queda como está. **Avisos de las rechazadas, uno por causa** (2026-10-16, Tony): `informe.avisos_rechazadas()` añade tras `RECHAZADAS` hasta tres incidencias: `TARJETA_SUCIA` (dispersión o asimetría por encima de `KTE.AVISO_SUCIA` = 1 %; por azar, con tarjeta limpia, ≈ 0,1-0,3 %), `LUZ_DESIGUAL` (nivel por encima de `AVISO_NIVEL` = 3 %, con `lados` si al menos `AVISO_LADO` = 80 % caen en una mitad: `Seleccion.ladosNivel`, `KTE.LADO_*`) y, por el total, `REVISAR_SERIE` (desde `AVISO_REVISAR` = 3 %) o `REPETIR_SERIE` (desde `AVISO_REPETIR` = 10 %). `Incidencia` gana el campo `lados`. Textos en `rejilla.py` (tres idiomas); la ventanita de la caja Lámina los dice tras las rechazadas (`KV.INCIDENCIAS_TESELAS`). Probado con mapas reales: TD sin avisos; Carolina, luz desigual a la izquierda y revisar. Umbrales provisionales (dos series). Aclaración del mismo día: `TAPADAS_MAL` en TD es correcta (el protocolo pide 2 tapadas y no las tiene). **Más del 2026-10-16:** al terminar Generar, si la carpeta OECF ya tiene TIFF (Preparar las conserva), pregunta si medirlas ya (`TXT_PREGUNTA_TIFF_YA`, botón Medir → `AnalizarRevelado`; Tony: «con aviso»). La nota de `SNRMinima` ya no dice que se cambia en la celda: «Es el criterio del método; para estudiar otro, use una copia del libro» (y `prompt_ia.md`, igual). Fuera `TextoInterpolado` (código sobrante). Los preajustes de Nikon (`PRESET2`) se traducen («Preajuste 2»: `KLI.PATRON_PRESET`, `T_PRESET`). En «Análisis», las filas de las zonas enteras, en negrita. **TIFF:** el espacio se reconoce por el nombre del perfil y, si no, por sus datos (`revelado.espacio_icc`: colorantes XYZ D50 frente a `KRV.COLORANTES`, ±0,01, y la luz de la curva rTRC en 0,5 frente a la del espacio, ±0,01; probado con los perfiles de colord y Ghostscript: sRGB, Adobe y ProPhoto sí, Rec. 709, Apple, NTSC y ECI no); una compresión que tifffile no abre (LZW) da `KRV.COMPRESION` y la app dice «expórtelas sin comprimir o en ZIP» (probado). En el JSON, las Z-V iniciales de más son `"control"` (`KT.PARTE_CONTROL`), no `"inicial"`. Ejecutable: `pyinstaller PyOECF.spec` da `dist/PyOECF` de 56 MB con matplotlib (DejaVu Sans, `backend_pdf`) y `Soportes.psd` dentro; arranca. Pruebas sin RAW para `secuencia()`: descartadas (Tony). **Probado por Tony en la app** (2026-10-16, Carolina): Preparar conserva las TIFF, el resumen final nombra los archivos, la pregunta de medir las TIFF al terminar Generar y la medida, el libro, la ficha y las láminas que siguen. **biboecf deja de ser una biblioteca** (2026-10-16, Tony; FE no la llevará): Tony movió el código de `src/bib/biboecf/src/` a `src/biboecf/` (con su `rec/`) y de Std dejó solo `src/bib/clases.py`. Adaptado: `src/biboecf/__init__.py` (el de antes, con `.src.xxx` → `.xxx`), `src/bib/__init__.py` (solo `clases`), las importaciones (`import biboecf`; `from bib import clases`, `clases.EnumMutable` y `clases.classproperty`) y `PyOECF.spec`. Las rutas de la plantilla y del prompt salen solas (`Path(__file__).parent / "rec"`). Comprobado: compila, la app arranca, libro y ficha de Carolina, y el ejecutable (lleva `biboecf/rec/`). Las rutas `src/bib/biboecf/src/…` que salen más arriba en esta memoria son las de antes. Dependencias del análisis (rawpy, numpy, XlsxWriter, psd-tools, tifffile, matplotlib): pasan al `rec/requirements/requirements.conf` de PyOECF (antes, en el de la BibOECF real; `requirements.sh` solo busca bibliotecas en `src/bib/`, así que ya no las encontraba). Borrados (Tony: «borra todo lo que sobre»): `src/biboecf/BIB_REAL_slr`, `src/biboecf/VERSION`, `rec/scripts/sl/bib_base.txt`, la línea `src/bib/std/BIB_std_slr` del `.gitignore` y, en `SymlinksLocal.txt`, los cuatro enlaces de `src/bib/` que ya no existen (si no, `SymlinksLocal_slr.sh` los habría vuelto a crear). El repositorio `Bibliotecas/Foto/BibOECF` ya lo había quitado Tony. **Con qué revelador se reveló:** no se pregunta (Tony): si quiere, el usuario lo apunta en el Excel; la exposición e ISO ya vienen en el análisis. **Resumen bajo la rejilla:** se queda como está (Tony, 2026-10-16), aunque repita tres incidencias: es el vistazo rápido, siempre a la vista; las incidencias, el detalle. **`rellenar_cuadros.jsx`** (rellenaba los 31 cuadros de referencia de la lámina): ya no hace falta (Tony, 2026-10-16). **Cajetín de la lámina relleno** (2026-10-16, Tony; antes «el cajetín no se toca»): `Lamina(…, cajetin)` recibe las líneas ya traducidas y `rellenar_cajetin()` las escribe en las capas de texto del grupo «Cajetín de datos», de arriba abajo, **como texto editable** (Tony: «quiero que sea texto editable»): el motor de texto (`Editor.Text`, tiradas de estilo y de párrafo, alineado a la izquierda), su copia (`Txt `, acaba en `\x00`), los límites (`bounds`, `boundingBox`) y la posición (`transform`), y además la imagen de la capa (el texto dibujado con la letra y el tamaño de la plantilla, Verdana 50, negro, con transparencia a 16 bits; la caja de la capa, la de la tinta), para que los visores lo enseñen. Repartidas a la misma distancia dentro del marco «Cajetín» (borde `KLA.BORDE_CAJETIN` = 10 px) y alineadas a la izquierda (la de «Soporte» estaba a la derecha). La letra: la del primer estilo (`FontSet`, su `.value`) con `matplotlib.font_manager.findfont` (sin ella, DejaVu Sans). Líneas (Tony): «Cámara: modelo», «Latitud recomendada: Z2 1/3 a Z8 1/3 (7 zonas)» (de los `resultados` del JSON: `json_estudio.leer_resultados`), «Fecha: 29 Oct 2026» (el día de las tomas, la ZV; meses en `KV.TXT_MESES`) y «Soporte: ____» (a mano); en los tres idiomas (`Ventana.TextosCajetin`). Probado: se relee el PSD con el texto nuevo, 16 bits y 55 capas, y la imagen compuesta lo enseña. Además se quita de la lámina el bloque global `Txt2` (`Tag.TEXT_ENGINE_DATA`): guarda otra copia de los textos del documento y Photoshop la usaba al editar (salía «23 Ene 2018» de la plantilla); sin ella, los rehace desde cada capa. **[VERIFICADO por Tony en Photoshop online, 2026-10-16]:** las cuatro líneas se ven y se editan con el texto nuevo.
    - `src/lamina.py` (`KLA`, `Lamina`; pieza E, 2026-10-12): la plantilla (`RUTA_PLANTILLA`) con sus 31 capas `Z00`…`Z10` (los mismos nombres que las copias) rellenas con el recorte del paño de cada zona, del centro de la misma ventana, reducido por área. **Revelado propio y neutro** (Tony: A ahora; con las TIFF, ya se verá cómo rehacerlas): balance de la toma, sin aclarado automático, sin curva, Adobe RGB (el perfil de la plantilla, potencia 2,2) y 16 bits. `Revelar()` (una zona cada vez; 24 s en TD), `Escribir(factor, destino)` (los 16 bits por canal con `set_data`: comprobado que se releen exactos; **no probado en Photoshop**) y `nombre(factor)` (`Soportes100.psd`, `Soportes50.psd`…). `biboecf.porcentaje(factor)`: el texto de los tamaños y los nombres. **También desde las TIFF del revelador** (opción B): `Lamina(…, sensor)` lee la exportación (ya en Adobe RGB y 16 bits, como la plantilla) y recoloca la ventana del paño con su recorte centrado. **Vista previa** (Tony, 2026-10-12: en XnView no se veían las texturas): `componer()` rehace la imagen compuesta que guarda el PSD (la que enseñan visores y miniaturas; Photoshop recompone desde las capas), sin las capas de ajuste (el grupo «Pruebas de procedimientos» de la plantilla: componerlas pediría `scipy`). Unos 20 s más por lámina, con «Lámina: escribiendo Soportes100.psd…». Si se quita ese grupo de la plantilla, la vista previa y Photoshop coinciden del todo.
    - `src/revelado.py` (`KRV`; parte 2, 2026-10-12): `lstar_tiff(analisis, ruta)`, el L* de la tarjeta en una exportación: la mediana de las teselas buenas del análisis, recolocadas con el recorte del revelador **supuesto centrado** (Lightroom, en la R7: 6960 × 4640 frente a 6984 × 4660 del sensor, 12 px por cada lado y 10 arriba y abajo), con 4 px de holgura (seguramente corrige la distorsión del objetivo: no hay un desplazamiento fijo, pero en la tarjeta, lisa, no importa). El color se pasa a luz lineal y a luminancia según el perfil ICC (`perfil_tiff()`: Adobe RGB, sRGB o ProPhoto; otro, `ESPACIO_DESCONOCIDO`). **Comprobado con TD**: frente a las medidas a mano de Tony en Photoshop, como mucho 2,3 L* de diferencia. Las TIFF de Lightroom no llevan metadatos del revelado (ni programa ni perfil). Las constantes de CIELAB, en `COM` (las usan el libro y esto). Solo se mide una TIFF de casi el mismo tamaño que el sensor (`RECORTE_MAXIMO`, un 2 % menos como mucho; Lightroom en la R7 recorta un 0,3–0,4 %): reducida o recortada, `TAMANO_DISTINTO`. La caja Revelado dice cuáles no se midieron y por qué, y las láminas desde las TIFF solo usan las medidas.
    - **Generar**, tras el libro: si hay paño, revela las 31 zonas («Lámina: revelando 5 de 31…») y escribe la lámina al 100 % y, si se eligió otro tamaño, también la de ese.
- **Reparto de la serie** (`secuencia()`): las tomas se agrupan en rachas (Z-V, positivas, negativas). **Si algo se repitió, la buena es la última vez:**
    - Lados: la última pareja de lados de signo contrario, seguidos o con Z-V de cambio en medio, con al menos `KS.MIN_LADO` (7) tomas cada uno. Si no hay, los dos más largos de signo contrario.
    - Iniciales: la racha de Z-V del principio. La ZV es la 2.ª inicial (la del balance personalizado).
    - **Z-V final** (obligatoria en el protocolo): la primera Z-V justo después del segundo lado. Marca el fin de la serie y va a la celda ZV de la rejilla. Si falta, incidencia.
    - **Tapadas:** las tomas oscuras (`Toma.oscura`: a 1/160 s y casi negras) que van **detrás de la Z-V final**. Sin final, no se buscan, y una oscura de antes (por ejemplo, una Z0 a 1/160) es una toma normal.
    - Balances de cámara: la racha de Z-V más larga que no sea la inicial ni la de cambio, sin la final ni las tapadas, con al menos `KS.MIN_BALANCES` (2) tomas, esté donde esté (la última si empatan). Si no hay tapadas, la final y los balances van seguidos: la primera de esa racha es la final.
    - Series antiguas sin Z-V final: si los balances van justo tras el segundo lado, el primero se toma por la final (Aaron: 6717). Tony lo acepta.
    - En cada lado, saltos si el tercioEV no avanza de uno en uno; lo que pasa de ±15 sobra.
    - Una carpeta es **una** serie: tarjeta y paño van juntos en la misma foto. Las series repetidas son repeticiones, no series distintas.
- **Balance de blancos** (`marcas.py`), en inglés y mayúsculas:
    - Nikon lo guarda en texto (`SUNNY`, `PRESET1`, `5600K`…); Canon (CR2 y CR3), Sony y Fujifilm, como código, que se traduce con su tabla (`KM.balances_*`). Un código desconocido sale como `CODE 23`.
    - **Kelvin con que se hizo la toma**: Canon (CR2: `ColorData` posición 67; CR3: `ColorData` al final del archivo, posición 109) y Sony (0xB021), en todas las tomas; Nikon (del nombre) y Fujifilm (0x1005), solo en balance por Kelvin.
    - Probado: Nikon, Canon CR2 y CR3, Sony. Fujifilm solo en Auto (los demás códigos, de ExifTool, sin probar).
- **`__all__` de biboecf: lo que la biblioteca expone, no lo que usa hoy la app** (Tony, 2026-10-19; sustituye a «solo lo que usan las apps», pensada para cuando FE llevaba biboecf): biboecf se comporta como biblioteca aunque viva dentro de PyOECF, por si mañana la usa otra app. El paquete ofrece sus objetos, los tipos que devuelven (`BalanceMedido` en `Review.balances`, `Select` en `OECF.select`) y sus utilidades (`leer_cam`, `leer_balance`, `leer_kelvin`, `KC`, `KCOM`); no los pasos internos que orquesta `OECF` (los de `teselas`, `tiff`, `secuencia`, `zonas`…), que se quedan en el `__all__` de su módulo. 56 nombres, en orden alfabético.
- Los `__all__` de los módulos van en orden de aparición y los de los `__init__`, en orden alfabético.
- **Constantes de clase en MAYÚSCULAS** (Estrategia): `KT.TV_TAPADA`, `KV.TXT_PREPARAR`, `K.ES`, `COM.MARGEN_TV`… en las 11 clases (`COM`, `KT`, `KS`, `KP`, `KC`, `KM`; `K`, `KV`, `KR`, `KD`, `KA`). No lo son, y siguen en minúsculas, `K.idioma` (cambia al elegir idioma) ni las propiedades y métodos de `K` (`version`, `path`, `derechos`, `tr`, `tr_n`). Cambio hecho el 2026-10-11.

### 2.8 Dependencias

- `screeninfo~=0.8.1` y `pyobjc-framework-Cocoa` (este solo en macOS) en `rec/requirements/requirements.conf`. En una máquina nueva: `rec/requirements/requirements_slr.sh --dev`.
- `babel` quitado de PyOECF.
- `toml` quitado del requirements.conf del repo real de Std: no se usa.
- `customtkinter~=6.0` (antes `>=6.0.0`, sin tope; cambio 2026-10-14): admite 6.x, no un 7.0 que pueda romper la interfaz.
- `tifffile>=2025.1` (biboecf) se queda sin tope: numera por fecha (2026.9.20), y `~=` lo cortaría cada año.

### 2.9 El objeto `OECF`: `src/bib/biboecf/src/kernel.py`

Es la entrada de la biblioteca: el alma de todo. La ventana solo pinta y traduce. Cada carpeta tiene su objeto: puede haber varios a la vez. Si la carpeta no existe o no tiene RAW, no falla.

```python
OECF = biboecf.OECF(path)   # lee la cámara y la 1.ª toma (la Z-V)
OECF.path, OECF.esCarpeta, OECF.puedeLeer, OECF.puedeEscribir
OECF.raws, OECF.primera
OECF.cam                    # Cam: marca, modelo, nombre
OECF.ZV, OECF.fecha, OECF.bits    # de la Z-V
for n in OECF.Leer(): …     # lee una toma cada vez; al acabar, reparte
OECF.tomas                  # Toma: exp, fecha, WB, oscura, nombreWB, bits, kelvin
OECF.tercioEVs, OECF.desvios, OECF.secuencia, OECF.partes, OECF.balancePersonalizado
OECF.zonas                  # {tercioEV: RAW} de las 31 (None si falta)
OECF.tapadas, OECF.WBs
OECF.enRejilla, OECF.celdas, OECF.fuera, OECF.vacias, OECF.repetidas
OECF.isoSerie, OECF.isoDistintos, OECF.tapadasOtroISO
OECF.desviadas              # de la rejilla, desvío > KP.DESVIO_MAXIMO
OECF.esAnalizable           # Z1 a Z9 sin huecos y el mismo ISO
for hechas, total in OECF.Copiar(): …   # copias a la carpeta OECF
OECF.carpeta, OECF.copias   # {RAW: copia}
OECF.TextoF(9), OECF.TextoTV(1/125), OECF.TextoISO(100)
```

- Properties de solo lectura, con docstring, sobre variables privadas declaradas en `__slots__`. Sin setters.
- Al terminar `Leer()`, `raws` y `tomas` quedan ordenados por fecha de disparo (ver 3.2).
- `Leer()` y `Copiar()` son generadores: una toma cada vez, para mostrar el progreso. Lo que va detrás del último `yield` no se ejecutaría si quien lee deja de pedir, así que el reparto y el apunte de las copias se hacen **antes** del último `yield`.
- **Copias** en la carpeta `OECF` de la serie (estructura de Tony, 2026-10-19, pensada para FE): `estudio.json` en la raíz (su ruta, solo en `_ruta` de `json_estudio.py`); `ZONAS/` con `Z00`, `Z00-3`, `Z00-7`, … `Z05` (la ZV) … `Z10` y las TIFF del revelador junto a su RAW; `CTRL/` con los balances de cámara `WB-01-DAYLIGHT`… (con el nombre del balance, si se sabe; el de Kelvin a mano con sus K, `WB-01-KELVIN-5600K`; de los repetidos, mismo nombre y multiplicadores, solo el último), las tapadas `DARK-1`, `DARK-2`, la 1.ª toma si la serie empieza con dos Z-V (`WB-CTRL`, property `wbCtrl`), las Z-V de control `ZV-INI`, `ZV-MEDIO` (cambio de lado) y `ZV-FIN` (property `zvs`; de cada una, la última; «ZV» de `texto_zona(0)`); `ANALISIS/` con el libro, la ficha, las láminas e `incidencias.txt` (`carpetaCtrl`, `carpetaAnalisis`; las dos se crean siempre). **JSON y `ZONAS/` es lo que se lleva FE.** Preparar vacía la anterior, también `ZONAS`, `CTRL` y `ANALISIS` (las borra si quedan vacías); conserva las TIFF y las subcarpetas del usuario; los originales no se tocan; solo el RAW. **ZV definitiva** (la de `ZONAS/Z05`, duplicada en `CTRL`): `ZV-MEDIO` o, si no hay, `ZV-INI`, que es la **última** de las iniciales; las iniciales repetidas no se copian ni se miden. La ZV la decide `secuencia()` (`Secuencia.zv`). **Se trabaja con las copias:** Seleccionar, Medir, la imagen de la ZV y la lámina leen las copias (`zonasCopia`).
- `esAnalizable`: de Z1 a Z9 ninguna zona sin toma, mirando `zonas` (las que se copian), y ninguna toma de la serie con otro ISO (`isoDistintos`). Las repetidas no bloquean.
- **Exportaciones del revelador** (TIFF, 2026-10-19): junto a su RAW, en `OECF/ZONAS/` (`OECF.exportaciones`); Vaciar las conserva.
- **Contexto preparada** (2026-10-19): al elegir una carpeta `OECF/` con su `estudio.json` (`es_preparada`), la serie se restaura del JSON y las copias sin leer originales (`restaurar_serie` → `OECF.Restaurar`, que vuelve a repartir con los datos de cada toma: el JSON guarda fecha, tapada y oscura; claves en `KD.T_*`). Sin Preparar ni rejilla: la caja Carpeta ofrece Analizar (directo a la caja del paño); las incidencias se graban igual. JSON antiguo o dañado: «vuelve a preparar la serie desde su carpeta». `OECF(path, buscar=False)` no busca RAW.
- **Escenario mínimo: JSON + TIFF** (2026-10-19): una carpeta con solo `estudio.json` y las TIFF del revelador (se llame como se llame) se restaura igual (`OECF.Restaurar(carpeta…)` fija `carpeta` a la elegida; la cámara, del JSON si no hay copias). Sin copias RAW (`copiasEnSitio` falso) no sale Analizar: solo Analizar revelado, que mide desde el análisis guardado; las TIFF se buscan en `ZONAS/` y, si no, junto al JSON (`exportaciones`); el libro, la ficha y las láminas van a su `ANALISIS/`. Probado por Tony con `gris18/ZONAS/locura`.
- **Caja Carpeta** (2026-10-19): sus botones, en un grupo (`botones_carpeta`) que ordena `ActivarCarpeta`: con análisis, «Analizar revelado» si hay TIFF del revelador o, si no, «Abrir resultados» (salvo que ya se vea otro; los tres a la vez ensanchan demasiado la ventana); y Preparar o, en una carpeta OECF preparada, Analizar.
- **Secuencia** (2026-10-19): de cualquier toma repetida vale la última (el estudiante repite si duda). Z-V final: las Z-V justo tras el 2.º lado con el balance de la serie (el de la ZV) y con una tapada detrás; si no, no hay final. Balances de cámara: con tapadas, las Z-V tras la última; sin ellas, las Z-V tras el 2.º lado desde la primera con otro balance que la serie (así no se pierde la del mismo balance que la serie, como `WB-11-FLASH` en TD). En TD, `_MG_8194` (KELVIN, sin tapadas detrás) dejó de ser final y pasó a balances: sale «Falta la Z-V final» y no el falso cambio de luz.
- **Sofía y Carolina** (resuelto 2026-10-19): en Sofía, una tapada negra ocupaba la ZV 1/3 porque, sin Z-V final, sus tapadas entraban en el 2.º lado; con las tapadas por exposición ya no ocupan zona (sin final, sobran). En la D750 de Carolina fallan las tres fuentes del ruido de lectura (LibRaw da margen 0 en sus NEF, no hay tapadas y la curva de transferencia no da lectura): los suelos de Cálculo salen con lectura 0, algo optimistas; en cámaras sin borde tapado, las tapadas son imprescindibles.
- **Tapadas** (2026-10-19): f/11 queda reservado para ellas: la serie nunca se hace a f/11 (lo dice el manual, `2) Preparación/4-fotometria.md` y el checklist de captura; Tony, 2026-10-19, sin regla extra en el código). Se identifican por la exposición, f/11 (`KT.F_TAPADA`, con margen `KT.MARGEN_F_TAPADA`: f/11 real es 11,31) y 1/160 (`Toma.tapada`); nunca van a los lados ni a una zona. Solo hay tapadas tras una Z-V final válida; sin final, sobran. El brillo comprueba que salieron casi negras (`Toma.oscura`): las que no, `tapadasConLuz`, con la incidencia `TAPADAS_CON_LUZ`, y no sirven para el negro ni se copian.
- **Paso de la serie** (2026-10-19): `Secuencia.paso` (y `OECF.paso`) = 1 por tercios o `KP.TERCIOS` por pasos enteros (todas las tomas de los lados en zona entera); los saltos se cuentan de paso en paso. Por pasos: incidencia `PASO_ENTERO`, solo se exigen las enteras de Z1 a Z9 (`EsNecesaria`), los tercios no salen como huecos y la lámina rellena cada tercio con su zona entera (`OECF.RellenarTercios`). Por medios pasos (`OECF.medioPaso`: al menos `KT.PARTE_MEDIOS` de las tomas de los lados se apartan medio tercio): incidencia `MEDIO_PASO`, que detiene; nunca se analiza.
- Multiplicadores del balance (`Toma.WB`) divididos por el verde, para comparar marcas. Profundidad de bits: la que hace falta para el nivel de blanco (16383 → 14), menos los bits finales que no usa ningún valor de la toma: la Sony ILCE-6400 guarda 12 bits multiplicados por 4 (todos múltiplos de 4) y sale 12 (2026-10-13).
- Probado con las 28 carpetas de `gris18` (CR2, CR3, NEF, ARW) y 3 RAF.

### 2.10 Nueva versión: `src/kernel/update.py`

- Al arrancar, un hilo lee el `VERSION` publicado en GitHub (`KA.URL_VERSION`: rama `deploy`, la misma que `RAMA_DESTINO` de `remoto.conf`), con 3 s como mucho. Si no hay internet, nada.
- `es_mas_nueva()` compara números y, si son iguales, la letra de revisión: `0.4` < `0.4a` < `0.4b` < `0.5`; `0.10` > `0.9`.
- La ventana mira cada 200 ms si ya respondió (`MostrarVersion`); si hay una más nueva, enseña el botón junto a Ayuda, que abre `https://github.com/TonyDiana/PyOECF/releases`.


## 3. Decisiones

Juntadas el 2026-10-07 de los antiguos `Decisiones.md` y `Avances.md`, puestas al día con el apartado 2. Las que ya no valen están en 4.3.

### 3.1 Arquitectura

- **El núcleo es la biblioteca biboecf** (`src/bib/biboecf/`). La usarán PyOECF y FotoEstación (FE). PyOECF es solo su ventana y las llamadas a biboecf.
- biboecf solo depende de la biblioteca estándar, `rawpy` y `numpy`. Puede usar Std (`from bib import std`), que pone quien la usa. Nada de interfaz ni de `customtkinter`.
- Los imports de biboecf son siempre **relativos**: no supone ningún `sys.path` de quien la usa. Su `__init__.py` es el MNS.
- La ventana **usa** biboecf, nunca al revés. biboecf no traduce nada (ver 2.4).
- **Prohibido `pyexiv2`** (GPLv3), ni siquiera como opcional.
- Los RAW de prueba **nunca** se suben al repositorio. Ninguna prueba depende de archivos que no estén en él.

### 3.2 Serie

- El protocolo de tomas está en el manual (`doc/src_manual/doc/3) Captura/2-pasoApaso.md`) y resumido en el apartado 5: 36 archivos más los balances de cámara.
- Solo varía el tiempo; diafragma e ISO fijos. El lado por el que se empieza lo detecta el programa.
- **Lo que para el proceso** (decidido por Tony, 2026-10-11; lo demás solo avisa): sin Preparar, si la carpeta no existe, no se puede leer, no tiene RAW o no se puede escribir en ella; sin Analizar, si falta alguna zona de Z1 a Z9, si cambia el ISO en la serie, si la copia falla o si no se leyó ninguna toma. Cámaras, tamaños o diafragmas distintos no se comprueban.
- **Cambio de ISO en la serie** (iniciales, lados, cambio y final) respecto al de la ZV: **impide analizar** (decidido por Tony, 2026-10-11). Tapadas con otro ISO: solo incidencia. Balances de cámara: el ISO no se mira.
- **Las dos primeras tomas deben ser Z-V con balances de blancos distintos** (la cámara guarda el balance en cada RAW). Si no, incidencia. Las Z-V iniciales de más no van a la rejilla. Solo se muestran los datos: no se reinterpreta la serie (por ejemplo, si el balance cambia en la 4.ª, no se toma esa como la del personalizado).
- **La 1.ª Z-V (la del balance personalizado) es solo tarjeta**, con otro encuadre y sin paño (Tony, 2026-10-12). Por eso el paño y las teselas se buscan en la 2.ª (la ZV de la serie, `OECF.zonas[0]`), y esa 1.ª **no es Z-V de control**: no se mide ni entra en la media (`OECF.Medir()`). En las series antiguas con una sola Z-V inicial (TD), esa es la ZV.
- Tapadas: se reconocen **por su contenido** (1/160 s y la imagen casi negra) y **solo detrás de la Z-V final** (ver 2.7).
- Orden: al elegir carpeta, por nombre (solo se lee la primera, para la caja Cámara). Al preparar, con todas leídas, **por fecha de disparo** y, a igual fecha (1 s), por nombre; las que no tienen fecha, al final (`OECF.__ordenar`). Así no importa que el contador de la cámara dé la vuelta (`_MG_9999` → `_MG_0001`), que se renombren los archivos o que haya dos tarjetas. Probado con TD renombrada en enlaces simbólicos: el mismo reparto.
- Referencia: la primera toma, que en el protocolo es la Z-V: `oecf.ZV` (PROVISIONAL, ver 2.5).
- La exposición se escribe siempre en el orden **f, Tv e ISO** (`Exp`).
- La estructura de la serie se informa, no se corrige. Si falla la lectura de un archivo, se informa y se sigue con el resto.

### 3.3 Lectura de cada RAW

- Con `rawpy`: tiempo, diafragma, ISO, fecha, dimensiones, patrón de color, canales, negro y blanco.
- El tiempo llega en coma flotante de 32 bits: se compara con **tolerancia relativa** (`KCOM.MARGEN_TV`), nunca por igualdad.
- Marca y modelo: lector propio, sin dependencias (`src/cam.py`). El número de serie no se lee ni se guarda.
- El ISO se anota, pero esta versión **no mide por ISO**.

### 3.4 Posición de cada toma

- Exposición relativa: `t · ISO / f²`.
- `tercioEV = redondeo(3 · log2(exposición / exposición_de_referencia))`: entero, positivo si hay más exposición que la Z-V.
- Zona: `5 + tercioEV / 3`. Se nombra como en el fotómetro (`Z0`, `Z0.3`, …, `ZV`, …, `ZX`), pero internamente se guarda el **número**, nunca el texto.
- `tercioEV` solo decide qué toma es cada una: los cálculos usan el tercio exacto, no el tiempo nominal.
- **Desvío** de cada toma: posición exacta (`3 · log2(…)`, con decimales) menos su `tercioEV`. Sale del redondeo de los tiempos que rotula la cámara (0,20 como máximo en la R7), no del obturador. Si una toma de la rejilla pasa de **0,33 tercios**, incidencia con el desvío de cada una (decidido por Tony, 2026-10-12).

### 3.5 Pieza 1 · Datos

- La pieza define qué datos se piden, cuáles se deducen, sus defectos y validaciones, **sin depender de la interfaz**. Entrega la serie validada y el informe de incidencias.
- Ni ventanas ni línea de órdenes: una función devuelve la descripción de los campos y otra recibe los valores y devuelve la serie validada y el informe.
- Los campos no se acoplan a `EnteDatos`. La ventana no define campos propios: salen de esta declaración.
- **Módulos** (2026-10-12): `src/campos.py`, hoy `carpeta.py` (`KCA`, `problema_carpeta()`; `Campo`, `campos()` y `validar()` se borraron el 2026-10-18: no los usaba nadie) e `src/informe.py` (`KI`, `Incidencia`, `incidencias()`). La serie validada es el objeto `OECF`.
- **[Sustituido 2026-10-18: la declaración de campos se borró, no la usaba ninguna app; el recorte de la lámina siempre reduce por área]** Solo se declaraban los campos seguros: `carpeta_serie` (obligatorio; debe existir, leerse, tener RAW y poder escribirse) y `metodo_reduccion_pano` (avanzado; `area`, `bilineal` o `bicubica`, **`area` por defecto**: conserva la luz media y no fabrica recortes en las luces).
- **Fuera, por decisión de Tony:** la cámara no es editable (solo se lee); la salida va siempre a la carpeta `OECF` de la serie; el cajetín de la lámina no se toca (sin `texto_soporte`); `derecheos_tercios`, fuera: el programa nunca analizará el derecheo (Tony, 2026-10-16). `lado_teselas` y `tolerancia_lado_teselas` no llegaron a existir: con las piezas B y C el lado de tesela quedó fijo (`KTE.LADO` = 48 px) y sin tolerancia (cerrado 2026-10-16); `ventana_pano` lo halla el programa; `plantilla_psd` va dentro del ejecutable.
- Los derecheos se expresan en **tercios**, nunca en EV.
- Se deducen y no se piden: tomas ordenadas, referencia, `tercioEV` y zona de cada toma, sentido de los lados, fecha, ISO, diafragma, dimensiones y patrón de color.

### 3.6 Ventana

- La de hoy está en 2.3. Una sola ventana, de arriba abajo, sin pasos.
- **Prevista** para cuando haya ajustes: los habituales a la vista y los técnicos bajo «Mostrar ajustes avanzados». Preparar, desactivado si hay alguna incidencia que impida seguir.
- **Sin icono en la bandeja del sistema**: no se usa `pystray`.
- **Sin ancho mínimo fijo**: la ventana se ajusta a su contenido, también al cambiar de idioma (Tony, 2026-10-11).

### 3.7 Infraestructura

- **Versión**: alfa, `0.x`. El formato año.mes de la Estrategia, solo cuando haya versión estable.
- **Releases**: una por versión; **nunca** se sobrescribe una existente. Las `0.x` se marcan como *pre-release*.
- **Entorno**: `rec/requirements/requirements.conf` es la única fuente de dependencias (pip y apt) y de la ruta del venv (`.venv`, dentro del repo). VS Code: venv activo en los terminales y depuración en `.vscode/launch.json`.
- **Despliegue**: `rec/scripts/remoto.conf`, `master` → `deploy` en GitHub, por SSH. `requirements.txt` solo existe en `deploy`, generado al publicar. `Remoto.sh` nunca despliega los enlaces `BIB_REAL_slr`.
- **GitHub**: rama por defecto `deploy`.
    - `publicar_web.yml` publica `doc/Manual` en <https://tonydiana.github.io/PyOECF/>, sin Jekyll (no hace falta `.nojekyll`).
    - `publicar_ejecutables.yml` hace los ejecutables de Windows, macOS y Linux con `PyOECF.spec`. **Si un sistema falla** (2026-10-13: en la 0.5a GitHub no dio máquina Mac dos veces), «Publicar» crea la release con los demás; al relanzar ese sistema («Re-run failed jobs»), su paquete se añade a la release, sin sobrescribir los que ya tiene.
- **Ejecutable de Linux** generado en `ubuntu-24.04` fijo: solo funciona en sistemas iguales o más nuevos.
- **macOS**: solo Apple Silicon, porque `rawpy` no publica paquetes para Mac con Intel.
- **Ejecutables de Windows y macOS probados** por Tony: funcionan (2026-10-11).
- **Documentación (MkDocs)**: dos fuentes, cada una con su `site_dir`. `doc/src_dev` → `doc/Datasheet` (desarrollo, no se despliega) y `doc/src_manual` → `doc/Manual` (manual de usuario, se publica). La norma de `site_dir` vive en `Repo/doc/mkdocs/USO.md`.
- **Instalación** explicada solo en `INSTALACION.md` (no en el manual), para no tenerla en dos sitios.

## 4. Historial

### 4.1 Versión 0.2 (2026-10-05): infraestructura y primera publicación

- El repo sube un nivel: `PyOECF/app/` → `PyOECF/`. Se rehacen enlaces simbólicos e `INHERIT` de MkDocs.
- El repo `docu` se integra en este: su manual pasa a `doc/src_manual`. Se archiva la rama `docu` de GitHub.
- `src/main.py`: ventana mínima de saludo para probar el empaquetado.
- Ejecutable de Linux probado en un equipo real ✅. Windows y macOS, pendientes de probar.

### 4.2 Versión 0.3

- El estado actual está en el apartado 2.
- 2026-10-07: nace el objeto `OECF` en `kernel.py` (antes se pensó como `Serie` en `secuencia.py`), con `Exp` y las constantes compartidas en `constantes.py`. `cam.py` vuelve a ser solo marca y modelo.
- 2026-10-07: el balance personalizado se comprueba de verdad, comparando el balance de blancos de las dos primeras Z-V. Con Aaron y Luis sale «no»: sus Z-V iniciales tienen todas el mismo balance (Luis lo cambia en la 4.ª).
- Aaron: «Falta la Z-V de cambio de lado» es correcto. Tras `_MG_6697` (+15) viene `_MG_6699` (−1): falta `_MG_6698`, que sería la Z-V de cambio. Faltan también otros números (`6677`-`6679`, `6682`, `6701`, `6715`, `6716`) y no tiene tapadas.

### 4.3 Decisiones sustituidas

| Decía | Ahora |
|---|---|
| Dos modos: FE vendoriza el repo de PyOECF entero | El núcleo es biboecf, una biblioteca aparte (3.1) |
| El núcleo no usa nada de `src/bib` (aquila, std) | `aquila` se ha quitado; biboecf puede usar Std (3.1) |
| Pendiente: qué rama vendoriza FE y la copia doble de `src/bib` | Ya no aplica: FE usará biboecf |
| Serie de 35 RAW | 35 más 10 balances de cámara (apartado 5) |
| Las tapadas se suponen las dos últimas | Se reconocen por su contenido y solo tras la Z-V final (2.7) |
| Referencia: primera toma que no sea tapada | La primera toma, provisional (2.5) |
| Errores (detienen) y avisos (no detienen) | Incidencias (2.5); si alguna detiene, pendiente (`CLD_TODO.md`, 4) |
| Textos en español, para traducirlos después | Tres idiomas con `K.tr`; biboecf sin textos (2.4) |
| Ventana: Serie, lo leído, Ajustes y Preparar | Cajas Serie, Cámara, Carpeta y Ayuda (2.3) |
| Guía (6): `CONTINUAR.md` y `TODO_DEV.md` | `CLD_BITACORA.md` y `CLD_TODO.md` |
| Guía: la rejilla en `src/kernel/temporal/rejilla.py` | `src/kernel/rejilla.py` (2.5) |
| Guía: nombres `Z0 1/3`, `Z0 2/3` | `Z0.3`, `Z0.7` (2.7) |
| Guía: orden por (fecha, número final del nombre); referencia, la primera toma no tapada | Fecha y, a igual fecha, nombre; referencia, la primera toma, provisional (3.2) |
| Guía: tabla de errores (cámaras o tamaños distintos, las dos primeras con ajustes distintos) y avisos | Incidencias; lo que para el proceso, en 3.2. Cámaras, tamaños y diafragmas no se comprueban |
| Guía (propuesta): cambio de ISO como error, de diafragma como aviso | El ISO impide analizar; el diafragma no se comprueba (3.2) |
| Guía: teselas de 96 px; filtros de dispersión y asimetría con umbral 0,15 y de nivel de 0,8 a 1,25 | 48 px; dispersión y asimetría, fuera las que se apartan más de 3 desviaciones robustas; nivel, más de 1/3 de zona (pieza B, 6.11) |
| Guía: paño detectado a unas 6 veces la dispersión de la tarjeta; el usuario lo confirma o lo indica a mano | Corte de Otsu y tres comprobaciones; Generar confirma; sin indicación manual (pieza C) |
| Guía (propuesta): negro de tapadas, luego borde tapado, luego declarado | Tapadas; si no, el declarado. El borde tapado da el ruido (pieza B) |
| Guía: `fraccion_en_limite` del JSON del extractor (región sin documentar) | Ya no existe: el paño recortado se cuenta con `KTE.UMBRAL_RECORTE` (2.7) |
| Guía: L\* medido con el cuentagotas en las 11 zonas enteras; tercios interpolados y marcados («Estimado» / «Interpolado») | Se miden las 31 exportaciones del revelador (parte 2); sin interpolación. Queda la constante `TextoInterpolado` (pendientes, 2) |
| Guía: el literal `1000` de `K9` en `Cálculo` | Fórmula matricial (2.7, libro) |
| Guía: textos del libro fijos en español | Tres idiomas, desde `src/kernel/textos_libro.py` (2.7) |
| Guía: temperatura de color de la luz por zona en la tabla de `Resumen` (pedido por Tony) | Quitada: no servía (Tony) |
| Guía: láminas al 100 y al 50 %, reducción bicúbica (Pillow) | 100, 50, 33 y 25 %, reducción por área (pieza C y E) |
| Guía: píxeles de la lámina, de Lightroom o de un revelado propio (abierto) | Revelado propio y neutro; también desde las TIFF del revelador (opción B) (2.7) |
| Guía: probar una capa de Curvas en la plantilla | Tony ya lo probó |
| Guía: plurales en las incidencias, iconos, ancho mínimo, `Decisiones.md` desactualizado, ejecutables de macOS y Windows | Hechos (2.4, 2.3, 3.6, este archivo, 3.7) |

### 4.4 Supercambio (2026-10-21): bitácora y normas comunes

- La carpeta `rec/estrategias/TODO/` pasa a `rec/estrategias/bitacora/`, igual en los 11 repos de Tony.
- Nombres: los archivos de Claude van en MAYÚSCULAS, sin tilde y con prefijo `CLD_` (`CLD_BITACORA.md`, antes `DEV_MEMORIA.md`; `CLD_TODO.md`, antes `DEV_PENDIENTES.md`); los de Tony, en PascalCase (`Todo.md`, `Bitácora.md`, `Changelog.md`).
- `CLAUDE.MD` pasa a `.claude/CLAUDE.md` y se versiona; importa `Repo/.claude/BASE.md`, la base común de todos los repos.
- Los 5 enlaces de «Mantenimiento» en `doc/src_dev` y sus líneas de `SymlinksLocal.txt` se renombran; `Bitácora.md` (personal de Tony) no se enlaza a la documentación.
- Reglas firmes en `~/.claude/CLAUDE.md`: nada de `.py` ni de git sin permiso explícito, y un mensaje que acaba en pregunta es solo diálogo.
- Commits de referencia en Gitea (`GitServer`, rama `dev`): «Previo a supercambio» y «Posterior a supercambio».

### 4.5 Serie restaurada y rehacer el informe (2026-10-22)

- **Formato nuevo de `estudio.json`, probado en la app por Tony.** 2026-10-21: Fabian Cruz (pCloud: preparar y Generar) y TD local (preparada de nuevo desde los originales: Generar y Analizar revelado). JSON con los 7 grupos, `revelado` con las 31 TIFF (16 bits, todas con L*), sin aviso de 8 bits (correcto), `incidencias.txt` en `ANALISIS/`, libro y ficha escritos. 2026-10-22: lo mismo con `TD/OECF` preparada de nuevo (con las TIFF del revelador ya en `ZONAS/`).
- **Carpetas con el JSON antiguo (`pyoecf 1.1`, claves sueltas en la raíz):** la app no las abre. `restaurar_serie` devuelve `None` y sale «No se puede abrir esta preparación: vuelve a preparar la serie desde su carpeta» (`TXT_ESTUDIO_ANTIGUO`). No hay compatibilidad por decisión de Tony (2026-10-21). El mismo mensaje sale con un JSON dañado o de una versión futura, porque no se lee `oecf.version`.
- **Fallo corregido: serie restaurada, Generar y medir los TIFF (Tony, 2026-10-22).** `TclError` por llamar a `configure` sobre un botón ya destruido. Traza: `_terminar_generar` → `AnalizarRevelado` → `QuitarCajas` → `ActivarCarpeta`, que hacía `self.btn_resultados.configure` sobre el botón Abrir resultados de la caja Lámina. Causa: en una serie restaurada no hay caja Serie (ni `rejilla`) y `ResultadosEnSerie(True)` salía sin reasignar `self.btn_resultados`, que seguía apuntando al botón destruido (con caja Serie lo reasigna al de la rejilla, por eso no saltó en las pruebas con Preparar). Arreglo: `ResultadosEnSerie(True)` asigna `self.btn_resultados = btn` (el de la rejilla; `None` sin caja Serie) antes del `return` temprano, y se quitó la asignación repetida del final de la función. Probado por Tony en la app (abrir `TD/OECF`, Analizar, Generar, medir los TIFF), sin fallos. Lo escrito por Generar se conserva aunque falle.
- **Rehacer el informe sin las copias de control (decidido por Tony, solo `CTRL/` por ahora; `ZONAS/` queda para después).** Con `medida` en el JSON, Analizar sale igual y Generar no mide: toma el análisis guardado (`leer_review`) y escribe libro, resultados, ficha y lámina, con un aviso de que se toman como buenos los datos del análisis anterior porque no se puede volver a leer (`{carpeta}` desde `KT.CARPETA_CTRL`, en los tres idiomas). Sin `grabar_json` en ese camino: pondría `revelado` a `null`. Por qué se puede: el `Review` sale entero del JSON (grupo `medida` más lo de la serie), y las dos cosas que parecían depender de `CTRL/` están guardadas: el negro y el ruido (origen `SOMBRAS`/`BORDE` o tapadas) y los balances (nombre, Kelvin y multiplicadores, de las tomas). Lo único de `Medir` que lee `CTRL/` son las tapadas y las Z-V de control. Comprobado en solo lectura con `TD/OECF`: 31 zonas, paño, negro y ruido, 8 balances, transferencia y 31 L*.
- **Paso 1 hecho (2026-10-22):** el informe de `_fin_medida` pasó a `_escribir_informe(review)` en `main.py` (libro, resultados en el JSON, ficha, incidencias y lámina), sin cambiar lo que hace. `_fin_medida` conserva `grabar_json` y llama a la nueva con `oecf.review`. Probado por Tony en la app (2026-10-22, `TD/OECF` con `CTRL/`): Generar escribe el libro, la ficha y las dos láminas (100 % y 25 %) igual que antes, y luego pregunta si mide las 31 exportaciones.
- **Paso 2 hecho (2026-10-22): Analizar y Generar sin las copias de control.** Tony: sin `CTRL/` la app era «todo o nada» (solo quedaba Analizar revelado: no pedía paño ni tamaño de lámina) por una única condición heredada del 2026-10-19, cuando Analizar siempre significaba medir. En `main.py`: (1) `ActivarCarpeta` muestra Analizar si hay copias **o** análisis guardado (`restaurada = preparada y (analisis o copiasEnSitio)`); (2) `_generar`, si faltan copias, no llama a `Medir` y va a `_rehacer_informe`; (3) `_rehacer_informe` lee el análisis (`leer_review`), pone el aviso `TXT_SIN_CONTROL` en la ventanita, una línea vacía (la que sustituye el libro, para no pisar el aviso) y llama a `_escribir_informe(review)`; sin `grabar_json`, que pondría `revelado` a `null`; si el análisis no se lee, lanza `ValueError` (`ERROR_ANALISIS_ILEGIBLE`) y lo recoge `ErrorInesperado`. La caja Lámina solo necesita la ZV de `ZONAS/`. Con las copias, todo sigue como antes. Limitación: sin medir no se recalcula `LUZ_CAMBIO` (necesita `oecf.review`), igual que en Analizar revelado. **Probado por Tony en la app (2026-10-22), con `CTRL` renombrada a `_CTRL` y la carpeta abierta por `Enlace a OECF`:** sale Analizar y la caja Lámina (paño, tamaños); Generar pone el aviso en la ventanita, antes de «Libro escrito» (la línea vacía evita que lo pise), y escribe libro, ficha y lámina. Con `CTRL/` puesta, Generar mide como siempre. En el JSON siguen `medida` y `resultados`; el `revelado` quedó a `null` en ese primer Generar porque el Generar con `CTRL/` de antes lo pone a `null` por diseño. **Comprobado después (2026-10-22, 21:01–21:04):** con `revelado` relleno por Analizar revelado (31 exportaciones con L\*), Generar sin `CTRL/` lo conserva (siguen las 31, con L\*), y el libro y la ficha pesan lo mismo que los rehechos por Analizar revelado y no lo que pesaban los escritos sin `revelado` (381210 y 53893 bytes, frente a 377442 y 52087): indicio de que llevan los L\* del revelador. Confirmado por Tony abriendo el libro (2026-10-22): la tabla por zona trae las dos diferencias (la del sensor casi 0 en los medios y la del revelador con valores) y Entrada y Salida calculadas, no en blanco.
- **Pregunta de medir las TIFF solo si aún no están medidas (Tony, 2026-10-22).** Al acabar Generar, «¿Medirlas ya con el análisis nuevo?» (`TXT_PREGUNTA_TIFF_YA`) sobraba cuando se rehízo con el análisis guardado y el `revelado` ya estaba medido. Primer intento (opción 3: no preguntar sin `CTRL/`, con `oecf.copiasEnSitio`), descartado por Tony: si el `revelado` está a `null` (TIFF exportadas y nunca medidas) había que seguir preguntando. Criterio final en `_terminar_generar`: hay TIFF y `leer_review(oecf).revelador` está vacío (el JSON no tiene su revelado). Tras un Generar normal el `revelado` queda a `null` (`grabar_json`), así que sigue preguntando como antes; sin `CTRL/` pregunta solo si no está medido. Sin textos nuevos. Límite: si se exportan TIFF distintas con el `revelado` ya medido, no pregunta (queda Analizar revelado).
- **Sin la copia de la ZV no hay Analizar (Tony, 2026-10-22; caso «no hay zonas»).** El paso 2 dejaba Analizar con solo «hay análisis guardado»: sin `ZONAS/` (JSON solo, que es lo que FE piensa que guardará el estudiante) salía Analizar y `Seleccionar` fallaba con `LibRawIOError` («Input/output error») al abrir `ZONAS/Z05.CR3`. Corregido en `ActivarCarpeta`: Analizar sale si hay todas las copias, o si hay análisis guardado y existe la copia de la ZV (`restaurada = preparada y (copiasEnSitio o (analisis y hay_zv))`). Con solo el JSON, la app no ofrece Analizar y no hace nada (queda Abrir resultados), como quiso Tony. Hallazgo en la prueba (carpeta de solo `estudio.json`, con otro nombre, en el scratchpad): la serie se restaura, `leer_review` sale completo y `Excel(...).escribir()` escribe un libro de 381210 bytes, igual que el real con los L\*: con solo el JSON se podría rehacer el libro (y la ficha, no probada), pero la app no ofrece cómo. Probado por Tony en la app con `_CTRL` y `_ZONAS`: solo Abrir resultados, sin error. **Aviso añadido (Tony, 2026-10-22):** `TXT_SIN_ZONAS` («Esta carpeta no tiene las imágenes de las zonas: no se puede analizar nada más con ella. Los resultados ya hechos siguen disponibles.»; EN y CA por DeepSeek, corregido en inglés «analyzed» —la app usa americano— y «produced»). En la rama de la serie restaurada, si falta la ZV se crea una caja «Serie» con una etiqueta (con ajuste de línea, `ANCHO_REVELADO`) que lo dice; `propias_serie` se recalcula tras la caja, como en `caja_serie`. `_hay_zv(oecf)` es el criterio único, usado por `ActivarCarpeta` y por este aviso. Probado por Tony en la app (2026-10-22): resuelto. Descartado por Tony (no hace falta): otro texto para el aviso de control cuando faltan también las zonas y hay TIFF en la raíz (Analizar revelado dice solo «tomas de control»).
- **`ErrorInesperado` no era un fallo (2026-10-22):** el TODO decía que repetía el error dentro del aviso. No es así: ya envuelve la reactivación de botones en un `try/except` que imprime el segundo fallo en la terminal (el tercer traceback de la traza) y enseña igual la ventana de error. La causa real era el botón destruido, ya corregida. Tony quitó el punto del TODO; no se hace `ActivarCarpeta` más defensiva (`winfo_exists`), porque taparía fallos reales.
- **Aviso de TIFF de 8 bits: aceptado sin probarlo en la ventana (Tony, 2026-10-22).** La app mide igual y avisa (`TIFF_8_BITS`: caja Revelado, botón de incidencias, ventana e `incidencias.txt`), sin rechazar: con 8 bits las sombras tienen muy pocos niveles (la zona 0, L\* ≈ 0,4, es un nivel de 255) y el L\* sale grueso, pero en medios y luces la medida es buena, y rechazar dejaría sin análisis a quien solo exporte en 8 bits. Rechazar (opción B) solo tendría sentido con el método cerrado y 16 bits como requisito. Probado antes solo fuera de la app (dos TIFF a 8 bits: ZV y Z6, en el JSON y con su texto en tres idiomas); el mecanismo de líneas de la caja Revelado es el mismo que enseñó hoy el aviso de control.
- **Mensajes de un JSON que no se abre: antiguo, dañado o de versión nueva (Tony, 2026-10-22).** Sustituye al mensaje único `TXT_ESTUDIO_ANTIGUO` (borrado por orden de Tony, junto con su uso). Regla: si la versión del JSON (`oecf.version`, `MAYOR.MENOR`) es **mayor que la que conoce la app, en cualquier parte** (2.0, 1.1 o 1.10; Tony: «es mayor también, tratar como la otra»), `TXT_ESTUDIO_NUEVO`: «Esta preparación es de una versión más nueva de PyOECF: actualiza la aplicación para abrirla». Si no se puede leer (cortado, sin `oecf`, con una versión que no son números o con claves que faltan), `TXT_ESTUDIO_DANADO`: «El archivo de estudio de esta carpeta está dañado y no se puede leer». El formato antiguo no tiene mensaje propio: cae en «dañado» (Tony: olvidar). Con versión igual o menor y legible se abre. En `estudio.py`: `_partes` (versión a tupla de enteros: 1.10 > 1.9), `_es_mas_nuevo(datos)`, `es_mas_nuevo(carpeta)` (pública, falsa si no se lee) y `restaurar_serie`, que devuelve `None` también si es más nuevo; `main.py` elige el texto con `biboecf.es_mas_nuevo`. Textos en EN y CA por DeepSeek (chat web), contrastados con una versión mía: coincidían salvo «in/of this folder»; elegidos «fitxer» (la app lo usa; no «arxiu») y «esta» (como `TXT_SIN_ZONAS`). Además, `ERROR_ANALISIS_ILEGIBLE` ya no lleva «estudio.json» escrito a mano. Comprobado con ocho JSON simulados en el scratchpad (versiones 1.0, 0.9, 1.1, 1.10, 2.0; cortado; sin `oecf`; versión «abc»): se abren los dos primeros, los tres siguientes dan «nueva» y los tres últimos «dañado».
- **Tipo propio para `resultados`: descartado (Tony, 2026-10-22).** Hoy `Excel.resultados()` devuelve un `dict` (claves `KXL.J_*`, que ya cubren las erratas). La idea de una clase para devolver datos, o de que PyOECF acepte parámetros para responder a otra app, se aparca: Tony no cree que otros tengan PyOECF instalado (pesa mucho), y lo más probable es que la otra app guarde el JSON, el libro y el PDF, que pesan menos. Nota de Tony: lo mejor será, llegado el momento, **generar un segundo JSON solo para esa app, junto al actual**. Sin definir.
- **`textos_excel.py` se queda en `src/kernel/` (Tony, 2026-10-22: descartado, «no demasiado lío»).** La opción comentada era pasar los textos en español a biboecf como tabla `clave → texto` (sin códigos de idioma), con la app guardando solo el inglés y el valenciano y el español como respaldo; en dos pasos (mover, y después cambiar `textos_excel()`). Se descarta porque es un cambio grande, choca con «biboecf sin idioma» (el español pasaría a ser el idioma de referencia de la biblioteca), la ganancia es pequeña (el riesgo de olvidar una traducción ya lo cubre el método DeepSeek, revisión de Claude y lectura de Tony) y hoy no falla nada.
- **Nombre del JSON (Tony, 2026-10-22): se queda `estudio.json`.** Se planteó llamarlo `OECF.json` (el nombre vive en un solo sitio del código, `estudio.py`, `ARCHIVO`; lo mencionan unos 15 archivos de documentación, entre ellos el manual); se descartó.
- **FE fuera del TODO (Tony, 2026-10-22):** se quitaron los puntos que dependían de FE: el nombre de la carpeta al regrabar el JSON, y la demo web de FE (`oecf.html` / `oecf.jinja`, desfasada: ver 6.10, que sigue como estaba; preguntaba si se alimenta con datos reales o sigue simulada, qué referencia usa la curva tonal, dónde vive —manual, FE o ambos— y si se une a la rejilla). Tony: cuando llegue FE se verá, con parámetros en PyOECF o un objeto. Las menciones de FE en esta bitácora y en el código se quedan (explican por qué el JSON y `ZONAS/` son como son).
- **Descartado por Tony, de momento (2026-10-22):** probar los tres casos de la pregunta de medir las TIFF (con `CTRL/`; sin `CTRL/` y `revelado` medido; sin `CTRL/` y `revelado` a `null`), y rehacer libro y ficha con solo el JSON (un botón sin Lámina; con solo el JSON el libro sale, probado en el scratchpad, la ficha no).
- **Fallo corregido: copias que no se encuentran si la carpeta se llama distinto (Tony, 2026-10-22).** Al abrir `TD/OECF` por un enlace llamado `Enlace a OECF`, Analizar daba `LibRawIOError: Input/output error` en `Seleccionar`. Causa: el JSON guarda cada `copia` relativa a la carpeta de la serie y empezando por el nombre de la carpeta (`OECF/ZONAS/Z05.CR3`), y `OECF.Restaurar` la resolvía contra `carpeta.parent`: solo valía si la carpeta se llamaba como al prepararla, al revés de lo que decía su docstring («se llame como se llame»). La prueba con `_OECF` (2026-10-22) solo funcionó porque la `TD/OECF` antigua seguía existiendo con los mismos nombres. Arreglo en `kernel.py` (`Restaurar`): se descarta el primer componente de la ruta y el resto se cuelga de la carpeta elegida (`carpeta.joinpath(*Path(copia).parts[1:])`); no cambia el formato del JSON. Comprobado en solo lectura: `TD/OECF` y `Enlace a OECF` dan la serie restaurada, la ZV existe y `leer_review` sale completo.
- **Analizar revelado sin `CTRL/` (Tony, 2026-10-22; `CTRL/` renombrada a `_CTRL` en `TD/OECF`):** ya funcionaba: `MedirTiff` toma el análisis guardado (`leer_review`), mide las 31 TIFF y rehace libro, resultados y ficha, y después pregunta si rehace las láminas, todo sin leer `CTRL/`. Lo que faltaba era decirlo: nuevo aviso `TXT_SIN_CONTROL` (tres idiomas, sin marcadores) y `_aviso_sin_control()` en `main.py`, que añade una línea a la caja Revelado cuando `copiasEnSitio` es falso. Probado por Tony en la app: sale entre «Libro rehecho» y «Ficha escrita», y la pregunta de las láminas aparece igual. **Texto (Tony, 2026-10-22):** sin jerga y sin nombrar la carpeta —el usuario no recuerda qué es CTRL ni la Z-V—: dice qué son («tomas de control de la serie: los balances de blancos, las tomas tapadas y las repeticiones de la toma de referencia que comprueban que la luz no cambió»). EN y CA traducidos por DeepSeek (chat web, sin clave de API) y corregidos al revisar: «covered shots» como en el resto de la app (no «capped»), «the series cannot be measured again» (no «it») y «bones» (dades es femenino).


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
| 6 | Z-V final | Se vuelve al tiempo de la Z-V: marca el fin de la serie (obligatoria) | 1 |
| 7 | Tapadas | Con la tapa puesta, el visor cubierto, f/8, 1/160 s y el mismo ISO que la serie, dos seguidas (opcionales) | 2 |
| 8 | Balances de blancos | Con la exposición de la Z-V, uno por cada balance que tenga la cámara (opcionales) | — |

La serie tiene **36 archivos**, más los balances de cámara. La fuente es el manual (`doc/src_manual/doc/3) Captura/2-pasoApaso.md`); si cambia, cambiar también esta tabla.

Con la Z-V en la zona V, quince tercios son cinco zonas: se llega a la zona 0 por un lado y a la zona X por el otro.


## Balances de blancos

En la toma 8 se hace una toma por cada uno de estos ajustes, en este orden. OJO: el manual pide solo «uno por cada balance que tenga la cámara», sin lista ni Kelvin fijos; el programa acepta cualquier número (al menos 2):

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






# El patrón 6 × 6 de Fujifilm (X-Trans)

## Qué es y por qué importa

La mayoría de los sensores tienen un filtro de color en bloques de **2 × 2** píxeles (patrón Bayer): un rojo, dos verdes y un azul. Los sensores X-Trans de Fujifilm usan un bloque de **6 × 6**, con una distribución distinta de los colores.

Si PyOECF da por hecho que el sensor es Bayer, medirá sobre los píxeles equivocados sin avisar. Estos son los datos comprobados con los RAF de muestra (X70 y X-T3):

| Dato | Bayer | X-Trans |
|---|---|---|
| Bloque que se repite | 2 × 2 | 6 × 6 |
| Colores distintos | 3 (dos verdes distinguibles) | 3 (un solo verde) |
| Verde | 50 % de los píxeles | 55,6 % |
| Rojo y azul | 25 % cada uno | 22,2 % cada uno |
| Índices de color que da `rawpy` | 0, 1, 2 y 3 | 0, 1 y 2 |

`rawpy` sigue describiendo el color como `RGBG`, aunque solo haya tres índices, así que **esa descripción no es fiable** para saber cuántos canales hay.

## Qué debe cumplir el código

1. **No suponer cuatro canales ni dos verdes.** No hay G1 y G2: la comprobación entre los dos verdes solo existe en Bayer.
2. **Tomar los canales del mapa de colores** que da `rawpy` para cada píxel, nunca de posiciones fijas del tipo `[0::2, 1::2]`, que solo valen para 2 × 2.
3. **El lado de las teselas debe ser múltiplo de 6**, y también de 2 para Bayer. Así cada tesela contiene los mismos colores en las mismas posiciones, y la máscara de colores de una tesela vale para todas. Con 48 px (6 × 8) se cumple en los dos casos.
4. **Los píxeles de cada canal cambian.** Con el lado `L`, el verde tiene `L² · 5/9` píxeles en X-Trans y `L² / 2` en Bayer. Con 48 px son 1280 y 1152, ambos por encima de los 1000 píxeles verdes que se piden para que los filtros sean fiables.
5. **El canal de referencia para los filtros** (dispersión, asimetría y nivel) es el verde, que en X-Trans es único.
6. **El modelo de cámara** se lee de la cabecera del RAF, en una cadena de longitud fija tras la firma `FUJIFILMCCD-RAW`, no de una estructura TIFF.

## Otras diferencias de los RAF de Fujifilm

Estas no son consecuencia del 6 × 6, pero afectan a la misma pieza:

- **No declaran límite de linealidad.** Para la cámara, `rawpy` devuelve el blanco nominal de 16383 y nada más. El límite hay que **medirlo en la serie**.
- **El borde tapado del sensor no sirve** para medir el negro. En la X70 hay una franja derecha de 52 columnas con ceros y una izquierda de 6 columnas mezclada. El negro sale de las tomas tapadas o del valor declarado (1020 en la X70 y 1018 en la X-T3).
- **El ISO base de la X70 es 200.** Según las fichas técnicas, sus RAF solo se graban entre ISO 200 y 6400, así que el ISO 100, que es ampliado, probablemente no da RAW.
- **La toma más rápida**: el obturador mecánico de la X70 llega a 1/4000 s, así que la Z-V debe ser de 1/125 s o más lenta.

## Cómo comprobarlo

Con las imágenes de muestra, la función que da el mapa de colores debe cumplir:

1. El patrón tiene forma 6 × 6.
2. Aparecen exactamente los índices 0, 1 y 2.
3. Las fracciones de verde, rojo y azul son 55,6 %, 22,2 % y 22,2 %.
4. El mapa de colores de una tesela de lado múltiplo de 6 se repite igual en toda la imagen.
5. El modelo sale como `X70` y `X-T3`, con marca `FUJIFILM`.

Las muestras son escenas y no una tarjeta gris, así que **no sirven para medir linealidad ni recorte**. Solo validan la lectura y el reparto de canales. Para el análisis completo hace falta una serie real hecha con una Fujifilm.

## Imágenes de muestra

Son archivos RAF de **raw.pixls.us**, una base pública de muestras de RAW que mantienen los proyectos de revelado libre. Su objetivo es que todas las muestras sean de dominio público (CC0), pero **algunas están marcadas con otra licencia**: comprueba la de cada archivo en la tabla del sitio antes de publicarlo o incluirlo en un repositorio.

- Fujifilm X70: <https://raw.pixls.us/data/Fujifilm/X70/>
- Fujifilm X-T3: <https://raw.pixls.us/data/Fujifilm/X-T3/>

| Cámara | Archivo | ISO | Tamaño | Enlace directo |
|---|---|---|---|---|
| X70 | `DSCF8848.RAF` | 6400 | 34 MB | <https://raw.pixls.us/data/Fujifilm/X70/DSCF8848.RAF> |
| X-T3 | `AFXT2720.RAF` | 160 | 56 MB | <https://raw.pixls.us/data/Fujifilm/X-T3/AFXT2720.RAF> |
| X-T3 | `AFXT2721.RAF` | 160 | 27 MB | <https://raw.pixls.us/data/Fujifilm/X-T3/AFXT2721.RAF> |

Los tres se han descargado y abierto con `rawpy`: dan un patrón de forma 6 × 6, tres colores con un 22,2 %, 55,6 % y 22,2 %, y negro declarado de 1020 (X70) y 1022 (X-T3). El X-T3 tiene el ISO base en 160, no en 200 como la X70.

Esos archivos se quedan en el disco local y **no se suben al repositorio**.

Las muestras que se usaron al principio, de la web de Kristoffer Trolle, ya no están disponibles: la página redirige al blog y los archivos dan error 404.


## 6. Método y diseño (guía de Claude web, 2026-10-12)

Escrito por Claude web en la sesión de diseño del 2026-10-12 para el agente de VS Code (antes, `análisis de luz.md`). Aquí queda lo que sigue valiendo; lo que el código ya cambió está en la tabla 4.3, lo abierto en `CLD_TODO.md` (apartado 5) y las normas de trabajo y las trampas en `CLAUDE.MD`. **Si algo de aquí no casa con el código, manda el código.**

Etiquetas: **[CERRADO]** decidido por Tony (no se cambia sin preguntar); **[VERIFICADO]** comprobado, con el sitio entre paréntesis.

### 6.1 Qué es PyOECF

- Herramienta Python **independiente** (repositorio público en **GitHub**), ejecutable único con PyInstaller `--onefile`. FotoEstación (FE) usará su núcleo, `biboecf`.
- **Propósito dual:**
  1. **Didáctico:** a partir de una serie de RAW de una tarjeta gris, mide la curva OECF del sensor (linealidad, recorte, suelo de ruido), da el rango útil y la latitud, y prepara la **lámina imprimible de 31 zonas** para evaluar latitud y derecheo.
  2. **Artículo** de continuación de la tesis doctoral de Tony (2012) sobre respuesta tonal y derecheo.
- **Los alumnos usan Excel.** La salida principal es un libro `.xlsx` que debe abrirse bien en Excel (Tony trabaja con ONLYOFFICE y LibreOffice, pero el destino es Excel).
- **Dependencias:** `rawpy` (LibRaw), `numpy`, `XlsxWriter`, `psd-tools` (MIT). **Ninguna puede ser GPL** (por eso está prohibido `pyexiv2`, 3.1).

### 6.2 Condiciones de la captura

El protocolo de tomas está en el apartado 5. Además:

- La Z-V final delimita la serie: lo que viene después son tapadas y balances.
- **Condiciones:** trípode, luz continua y estable, ISO base, diafragma fijo, RAW sin compresión si existe, pasos de 1/3 en la cámara, reducción de ruido de exposición larga desactivada. La Z-V se mide con exposímetro sobre la tarjeta, a 1/125 s o más lenta (para que 15 tercios no pasen de 1/4000 s).
- **Encuadre:** la tarjeta gris del 18 % ocupa **al menos la mitad** del encuadre; una **ventana pequeña y fija de paño con textura** (≥ 1000 × 700 px) ocupa **la mitad o menos**; cartulina negra de base. El paño tiene que ser el mismo en todas las tomas.
- Todo se muestra en **zonas y tercios**, nunca en EV. La única excepción es el eje en «pasos respecto a Z-V» de la gráfica de esperado y obtenido.

### 6.3 Del extractor de la guía a `teselas.py`

**[NO VERIFICADO]** El extractor de la guía (`pyoecf_extraer.py`) y su salida `serie_R7.json` no estaban en ningún sitio, y Tony duda de que llegaran a existir. `teselas.py` se escribió de cero y se comprobó con la hoja `Datos` del libro de Tony (2.7). De la guía queda como referencia:

- Valores del libro: **rojo** = `R0`, **verde** = media de `G1` y `G3`, **azul** = `B2`, todos **netos** (negro restado).
- Lo que pedía y ya está hecho: excluir el paño por posición antes de los filtros (la misma ventana recorta la lámina), las estadísticas del paño por toma y el ruido de lectura **por canal** (4,46 / 3,77 / 4,43 en la R7).

### 6.4 Definiciones físicas y matemáticas

Todo en **zonas** (una zona = un paso de luz). Las constantes llevan nombre (6.8.3).

| Magnitud | Definición |
|---|---|
| Esperado (zona) | `ZonaZV + tercios / TercioPorZona` |
| Obtenido (zona equivalente) | `ZonaZV + log_FactorZona(valor / ZV_media)`, por canal |
| Desviación | obtenido − esperado |
| Recortado | `valor ≥ UmbralRecorte × máximo del canal` |
| Techo | `ZonaZV + log(máximo / ZV_media)` |
| Suelo (ruido de lectura) | `ZonaZV − log(ZV_media / (ruido × RelacionSR))`. **Extrapolado, no medido** |
| Rango | techo − suelo |
| Último punto lineal | mayor zona con `|desviación| ≤ ToleranciaLineal` y sin recorte |
| Primer punto recortado | primera zona marcada como recortada, o «no alcanzado» |
| Señal/ruido (SNR) | `1 / dispersion_rel`; 0 si la dispersión es 0 |
| Suelo sugerido | primera zona con `SNR ≥ SNRMinima`. Resolución de un tercio |
| Latitud sugerida | último punto lineal − suelo sugerido |

- **Z-V media:** media de las Z-V de la serie (la de la tabla principal más las de control que no se apartan, 2.5).
- **El 12,0 de rango** de la R7 sale del ruido del canal verde. Antes se dijo 11,9 con el ruido medio de todos los canales: es definición, no medida.
- **El suelo no es utilizable por sí mismo:** «señal = ruido» no se distingue del fondo. Por eso la **latitud** usa el suelo por señal/ruido.
- **`SNRMinima` = 10 [CERRADO como sugerencia].** Viene de ISO 12232 (calidad «aceptable» 10:1; «excelente» 40:1), medida sobre copias impresas a unos 70 píxeles de sensor por centímetro (dato de segunda mano, no leído en la norma). La medida de PyOECF es por píxel dentro de la tesela e incluye la textura de la tarjeta, así que sale más baja que la señal/ruido real: el valor **no es un resultado, es una sugerencia**. El usuario decide el valor definitivo con la lámina PSD impresa. La SNR medida se aplana en unos 25 desde la zona 7, así que el umbral 40 es inalcanzable y el 20 deja casi sin latitud.
- **Linealidad medida, no declarada:** el límite se mide en la serie y por canal (en la R7 el blanco real es 15872 y el declarado 13036).

### 6.5 Curva tonal en L\*

- **Patrón («esperado») [CERRADO]:** ZV en **L\* 50**, **un paso de luz por zona**, recortado al blanco de pantalla (luminancia relativa 1). La luminancia de la ZV es `((50 + 16)/116)³ = 0,18419`. El blanco se alcanza en la zona **7,44**.
- **Objetivo [CERRADO como referencia]:** escala perceptual de **10 L\* por zona** (ZX en 100), la de la tesis. Se dibuja punteada.
- **El revelado se mide contra el Objetivo [CERRADO, Tony, 2026-10-20]:** sustituye a «revelador frente a esperado» (12/10). Lo que le sirve al estudiante es ver cuánto se separa el revelado de la escala que busca, para corregirlo. Libro y ficha: diferencia, falta y sobra del revelador = L\* revelador − objetivo; salida de la curva = sRGB del L\* objetivo (Z V 119, Z VIII 198); media de diferencias del revelador, con el objetivo. La gráfica de diferencia (libro y ficha) solo lleva el revelador; la diferencia del sensor sigue contra el esperado (auditoría: linealidad del sensor), en Cálculo y en la tabla de Análisis, con rótulos «(− esperado)» y «(− objetivo)». El Esperado sigue en la curva tonal (en la ficha, banda gris ancha y casi opaca, para que el sensor no lo tape). Z0 y Z X se quedan en las recomendaciones. Nueva `Excel.formula_luz` (inversa de CIELAB), que usan la luz del revelador y la salida. FE: se verá cuando toque.
- **Hoja Gráficos rehecha (Tony, 2026-10-20):** 1 curva tonal, 2 diferencia (− objetivo), 3 **tu curva** (nueva), 4 desviación del tramo lineal, 5 **balances de blancos** (nueva: Kelvin anotado y medido, de Datos), 6 señal/ruido. «Esperado y obtenido» y «Desviación, rango completo» no le sirven al estudiante medio: pasan a **auditoría**, sin número, al final de Cálculo (`KXL.GRAF_AUDITORIA`, `F_AUDITORIA`). **Tu curva:** las decisiones propias de Análisis (10 puntos: entrada y salida) se copian a una tabla en Cálculo (`TU_PUNTOS_*`); por zona, la entrada del revelador se pasa por ellos **en recta** entre el punto de abajo y el de arriba (`MAXIFS`/`MINIFS`, con (0, 0) y (255, 255) en los extremos; el libro se crea con `use_future_functions`), y de ahí su L* (`formula_luz_curva`, inversa de sRGB), la diferencia con el objetivo y falta/sobra para las barras lilas (`TU_*`, columnas 16–24 del bloque 3; `ANCHOS_CALCULO` pasa a 28). En Análisis, «Diferencia media con tu curva (− objetivo)». **Decisiones propias** (siguen siendo 10: Tony, en la práctica no se ponen más de 8, y en cámaras buenas 4 o 5): la zona, desplegable con «—» (`KXL.SIN_ZONA`: el punto no cuenta) y las 31 zonas; por defecto, de la Z0 a la Z9 (izquierda Z0–Z4, derecha ZV–Z9). La **entrada, fórmula** (la de esa zona en la tabla de recomendaciones, `INDEX`/`MATCH`; con «—», en blanco). La **salida, valor y no fórmula** (la recomendada, en azul): así el estudiante sabe que la puede cambiar libremente. La nota de Gráficos avisa de que Lightroom traza una curva suave. Nada de esto va en la ficha PDF (Tony: «en el PDF jamás saldrá»). `EJE_DIF_LSTAR` pasa a ±25 (con el objetivo, TD da de −17 a +20).
- **L\* 50 y no 128/128/128:** RGB 128 es neutro (a\* = b\* = 0) pero no es el medio: vale L\* 53,6 en sRGB, 54,0 en Adobe RGB y 60,7 en ProPhoto. L\* 50 es el entero más próximo al gris del 18 % (L\* 49,5), se teclea tal cual en Lab y en sRGB da 119. La diferencia entre 49,5 y 50 es de unos 0,03 EV.
- **Fórmulas CIELab** (norma **ISO/CIE 11664-4:2019**, Colorimetría, parte 4: espacio CIE 1976 L\*a\*b\*; la inversa está en su anexo A):
  - `t > 0,008856`: `L* = 116 · t^(1/3) − 16`; si no, `L* = 903,3 · t`.
  - Inversa: `L* > 8`: `t = ((L* + 16)/116)³`; si no, `t = L*/903,3`.
- **De dónde sale el L\* obtenido [CERRADO, Tony, 2026-10-12].** Lo que se quiere ver es **cómo actúa el revelador**, zona por zona, frente a lo esperado. El L\* calculado del RAW sale casi igual al esperado (el sensor es casi lineal: en la R7, como mucho +0,3 L\* en la Z0). Las diferencias grandes (−9 en Z1, +7,8 en Z6, en la tabla de Tony) las pone la curva del revelador (el perfil de Lightroom). Por eso se miden las **31 exportaciones** del revelador en las mismas teselas (parte 2, 2.7) y el libro compara, por zona, esperado, **sensor** y **revelador**.
- Valores de Tony (R7, revelado de Lightroom, medidos a mano en Photoshop): `Z0=0, Z1=1, Z2=6, Z3=15, Z4=31, Z5=50, Z6=75, Z7=90, Z8=98, Z9=99, Z10=100`.
- **Z8 de la R7 conserva textura aunque su valor teórico sea imposible** (116 L\*): el revelado de Adobe no recorta en seco, comprime las luces; el RAW todavía tiene el 92 % del paño sin recortar en Z8. «Z8 vale 100» describe el parche, no la textura.

### 6.6 Entrada y salida de la curva de Lightroom

- **[CERRADO]** El revelado se corrige con la **curva de tonos de Lightroom**, curva de puntos RGB (círculo blanco), **con «Perfeccionar saturación» a 0** para que solo cambie la luminosidad (a 100 también cambia la saturación).
- **[CERRADO por Tony]** Lightroom muestra **Entrada y Salida** de cada punto, se pueden **teclear** y van de **0 a 255**.
- La curva admite **16 puntos**: se usan las **11 zonas enteras**. Los tercios sirven para comprobar la forma.
- **Conversión:** entrada = `ROUND(EscalaCurva × sRGB(luz del revelador), 0)`; salida = lo mismo con la luz esperada. `sRGB(y)`: si `y ≤ 0,0031308`, `12,92 · y`; si no, `1,055 · y^(1/2,4) − 0,055`. Que esa escala sea la de sRGB está **sin comprobar** (pendientes, 5.3).
- La curva se aplica **después** de los controles básicos: el L\* del revelador se mide con los ajustes básicos ya puestos.

### 6.7 Datos de referencia: Canon R7, ISO 100, f/9, 1/125 s

32 CR3: `_MG_8162` (Z-V, `k` = 0), `_MG_8163` a `_MG_8177` (+1 a +15), `_MG_8178` (Z-V de control), `_MG_8179` a `_MG_8193` (−1 a −15). Sin segunda Z-V inicial, sin Z-V final y sin tapadas: el programa debe dar incidencias, no parar. Carpeta adicional con 13 Z-V a distintos balances: `_MG_8194` a `_MG_8206` (sin la `_MG_8198`), todas en `k = 0`.

**Resultados esperados por canal** (tolerancia 0,1; umbral de recorte 0,995; `SNRMinima` 10; `RelacionSR` 1):

| Canal | Z-V (media) | Máximo | Techo | Suelo | Rango | Último lineal | Primer recortado | Suelo por SNR | Latitud |
|---|---|---|---|---|---|---|---|---|---|
| Rojo | 686,0 | 15814 | 9,53 | −2,27 | 11,79 | 9,33 | 9,67 | 2,00 | 7,33 |
| Verde | 1159,12 | 15872 | 8,78 | −3,26 | 12,04 | 8,67 | 9,00 | 1,33 | 7,33 |
| Azul | 752,75 | 15871 | 9,40 | −2,41 | 11,81 | 9,00 | 9,33 | 2,00 | 7,00 |

- Ruido de lectura (niveles): rojo 4,46, verde 3,77, azul 4,43. Orden de recorte: verde, azul, rojo. Negro declarado 511/511/512/511; medido en el borde 512. Luz: unos 5070 K con Duv +0,0002.
- **Dispersión relativa del verde por zona:** Z0 0,156; zona 1 0,103; 2 0,085; 3 0,072; 4 0,065; ZV 0,060; 6 0,053; 7 0,044; 8 0,046; 8,67 0,041; recorte 0,0. SNR en el verde: 6,4 en Z0; 9,7 en la zona 1; 16,6 en la ZV; 24,2 en la zona 8,67.
- **Curva tonal** (con los 11 L\* de Tony): diferencia media |ΔL\*| = **5,2**. Entrada/salida de ejemplo: Z0 → 0/17; Z2 → 19/42; ZV → 119/119; ZX → 255/255.
- **Paño de la R7 (derecheo):** píxeles recortados en el paño por zona: 7⅔ → 0,6 %; 8 → 7,8 %; 8⅓ → 25,8 %; 8⅔ → 49,1 %. La tarjeta se recorta más tarde que el paño.

**Otras cámaras** (una sola Z-V cada una; cifras provisionales):

| Cámara | Formato | Negro | Blanco real | Margen sobre Z-V | Luz (K) |
|---|---|---|---|---|---|
| Canon R7 | CR3 | 511 | 15872 (13036 declarado) | 3,78 EV | 5063 |
| Canon 70D (×2 cuerpos) | CR2 | 2048 | 12277 | ~3,0 EV | 5160–5215 |
| Canon 80D | CR2 | 511 | 11892 | 3,13 EV | 5778 |
| Sony a6400 | ARW (con pérdida) | 512 | 15360 | 3,75 EV | 5101 |
| Fujifilm X70 | RAF | 1020 | sin dato de cámara | — | — |
| Fujifilm X-T3 | RAF | 1018–1022 | sin dato de cámara | — | — |

Ruido de lectura aproximado a ISO base: 80D 3,0; R7 3,8; 70D 6,7 (el borde de la 70D tiene una columna contaminada). Sony y Fujifilm no tienen borde tapado utilizable: su ruido saldría de las tapadas. Fujifilm X-Trans: ver «El patrón 6 × 6 de Fujifilm», más arriba.

### 6.8 El libro Excel

#### 6.8.1 Decisiones

- **[CERRADO] (Tony, 2026-10-12): el alumno no toca el libro.** Trabaja con la lámina PSD; el libro solo se lee.
- **[CERRADO] Se genera desde cero con `XlsxWriter`**, no con una plantilla ni con `openpyxl`:
  - `XlsxWriter` escribe el **resultado junto a cada fórmula** (`write_formula(…, valor)`), así que Excel en **Vista protegida** muestra los números sin recalcular. `openpyxl` no puede.
  - `openpyxl` **pierde las gráficas** de un libro que las trae al guardarlo.
  - El tamaño de la serie varía, y desde código los rangos se ajustan solos.
- **El diseño vive en constantes de código** (colores, anchos, textos). El libro de referencia de Tony (`~/pCloudDrive/NeoZonas/PyOECF_completo.xlsx`) es la **referencia visual**; el programa **no lo abre**.
- **Todo se calcula con fórmulas** del libro. La biblioteca escribe solo los datos medidos y los parámetros; la hoja hace el resto, con la réplica en Python de cada fórmula para la caché.
- **Comprobación (Tony, 2026-10-12): a mano**, abriendo el libro en ONLYOFFICE (recalcula al abrir) y comparando celdas clave con 6.7. LibreOffice no está instalado y no se instala; el conversor de ONLYOFFICE (`x2t`) no sirve: copia la caché sin recalcular (probado). En el libro de referencia: **1276 fórmulas, 0 diferencias, 0 errores** [VERIFICADO en LibreOffice].
- **No hay EV** en tablas ni textos. Solo el segundo eje de la gráfica de esperado y obtenido está en «pasos respecto a Z-V» (zona − 5).

#### 6.8.2 Formato (todas las hojas) [CERRADO]

1. **Cada hoja empieza en `B2`:** fila 1 y columna A en blanco; los bloques nunca pegados.
2. **Última columna visible = margen**, igual que la primera (mismo ancho, fijado explícitamente).
3. **Ocultas** las columnas a la derecha de la última y las filas por debajo del anillo (`set_column(ult+1, 16383, …, {"hidden": True})` y `set_default_row(hide_unused_rows=True)`).
4. **Marco «tarjeta»** en las hojas distintas de `Resumen`: anillo gris `#BFBFBF`, tarjeta interior con **borde negro medio** y relleno de una fila y una columna (columnas B y de cierre de 2,1; fila 2 en blanco). El contenido empieza en `C3`.
5. **Colores del texto:** dato azul `#0000FF` (lo leído de los RAW); literal naranja oscuro `#C55A11` (lo escrito por diseño); fórmula negro; rótulo o nota gris `#595959`.
6. **Tablas:** cabecera `#4F81BD` con letras blancas en negrita y ajuste de texto; filas alternas `#DCE6F1` y blanco; bordes finos `#95B3D7`. Cuadrícula oculta. Fuente **Arial 10**, salvo `Resumen`.
7. Orden de pestañas: `Análisis` (antes `Resumen`), `Gráficos`, `Datos`, `Constantes`, `Cálculo`, `Rechazadas` e `IA`. **Desde 2026-10-14**, de `Datos` en adelante se generan **ocultas**: el estudiante trabaja en `Análisis` y `Gráficos`.
8. Impresión: apaisada y ajustada a una página de ancho.

#### 6.8.3 Hoja `Constantes`

Cada constante tiene **nombre definido en el libro** y las fórmulas usan el nombre. Columnas Nombre, Valor, Unidad, Qué es.

| Nombre | Valor | Unidad | Qué es |
|---|---|---|---|
| `ZonaZV` | 5 | zona | Zona de la Z-V (la quinta) |
| `TercioPorZona` | 3 | tercios | Tercios en que se divide una zona |
| `FactorZona` | 2 | veces | Luz por zona |
| `LZV` | 50 | L\* | L\* del gris neutro en la ZV (entero) |
| `LPorZona` | 10 | L\* | Objetivo de la escala perceptual |
| `RelacionSR` | 1 | veces | SNR que define el suelo por ruido de lectura |
| `SNRMinima` | 10 | veces | SNR mínima **sugerida** de una zona utilizable |
| `ToleranciaLineal` | 0,1 | zonas | Desviación máxima para decir «lineal» |
| `UmbralRecorte` | 0,995 | fracción | Fracción del máximo desde la que un valor se considera recortado |
| `LabEscala`, `LabDesplaza`, `LabUmbral`, `LabPendiente` | 116; 16; 0,008856; 903,3 | | Constantes de CIELab |
| `SrgbUmbral`, `SrgbPendiente`, `SrgbEscala`, `SrgbGamma`, `SrgbDesplaza` | 0,0031308; 12,92; 1,055; 2,4; 0,055 | | Constantes de sRGB |
| `EscalaCurva` | 255 | número | Máximo de la escala de la curva de Lightroom |
| `TextoRecortado`, `TextoNoRecortado`, `TextoNinguno`, `TextoNoAlcanzado`, `TextoPunto` | SÍ; NO; ninguno; no alcanzado; ● | texto | Marcas |

Derivadas (fórmula): `LuzPorTercio` = `FactorZona^(1/TercioPorZona)`; `LuzZV` = la luminancia de `LZV` por la inversa de CIELab.

- Se usa `ZonaZV` y no `ZV` porque «ZV» también es una columna y los nombres no deben parecer referencias de celda.
- **No se pone el número 10 en ningún rótulo** de `SNRMinima`: si cambia, el texto quedaría desfasado. Debajo de la tabla, la nota de `SNRMinima` y la leyenda de colores.

#### 6.8.4 Hojas `Datos`, `Cálculo` y `Análisis` (antes `Resumen`)

- **`Datos`**: solo lo leído de la serie, **sin cálculos salvo la media de las Z-V**: serie por zonas (31 filas de Z0 a ZX, por **zonas** y no por archivos: zona, tercios, archivo, rojo, verde, azul y sus dispersiones), Z-V de control, su media, ruido de lectura y **L\* del revelador** (31 zonas). **Desde 2026-10-14** el L\* del revelador es fórmula: lee el «L\* leído» de `Análisis` y estima los tercios sin él (la diferencia con el esperado de las dos zonas enteras vecinas, repartida en recta; Tony, opción B). **No hay bloque de cámara en `Datos`** [CERRADO]: marca, modelo, fecha y Z-V van en `Resumen`.
- **`Cálculo`** (lee de `Datos` y `Constantes`; no guarda datos propios): bloque 1 por canal (Z-V media, máximo, techo, suelo, rango, último punto lineal, primer punto recortado, suelo y latitud sugeridos); bloque 2 por tercio (esperado, obtenido, desviación, recortado y SNR por canal, más tres columnas de referencia para dibujar las líneas horizontales de las gráficas); bloque 3, curva tonal por zona (esperado, sensor y revelador, sus diferencias, entrada y salida de la curva y punto de la curva). Las fórmulas no dan errores si falta un dato: salen en blanco.
- **`Análisis` (2026-10-14, boceto de Tony):** dos tarjetas una al lado de otra. Izquierda: cabecera, ruido y negro, balances. Derecha: sugerencia (sugerido, referencia y «es una sugerencia» en un solo texto), leyenda de lo estimado, diferencias medias, aviso sin L\* y tabla por zona con **«L\* leído»** (lo escribe el estudiante, normalmente solo las zonas enteras, o el programa con las TIFF, las 31). Lo estimado (Dif. revelador y Entrada de un tercio sin L\* leído), en otro color por formato condicional, sin columnas nuevas. Gráficas 5 y 6 con la serie del revelador siempre (`NA()` en Cálculo sin dato). Lo que sigue es la disposición anterior, como `Resumen`.
- **`Resumen` (hasta 2026-10-14)**: la disposición del libro de Tony (no se cambia sin su sí): cabecera con marca y modelo, fecha y exposición de la Z-V; barra «Sugerencia de revelado para contraste CIELab» con sus tres notas; diferencia media; y la tabla por zona con **las dos diferencias** (sensor y revelador) y **Entrada y Salida calculadas con el revelador**. Sin las exportaciones, en blanco, y una nota lo explica: en la parte 1, la diferencia del sensor sale casi 0 en los medios, y es el resultado, no un fallo. Anchos: A 9,71; B 2,57; C 23,29; D a I, 10,0; J 2,57; K 9,71. Anillo `#D9D9D9`, textos en Verdana.

#### 6.8.5 Hoja `Gráficos`

Seis gráficas que leen de `Cálculo`, en dos columnas y tres filas:

| N.º | Gráfica | Detalle |
|---|---|---|
| 1 | Esperado y obtenido | Eje izquierdo en zonas (−4 a 10); eje derecho en pasos respecto a Z-V (−9 a 5), alineados. Barras lilas `#B39DDB` desde el obtenido (verde) hasta el esperado |
| 2 | Desviación, tramo lineal | Una línea por canal, eje ±0,2 |
| 3 | Desviación, rango completo | Eje de −1,5 a 0,5: se ve la caída del recorte |
| 4 | Relación señal/ruido por zona | Eje 0 a 30; línea discontinua «Mínimo sugerido» |
| 5 | Curva tonal en L\* | Esperado, Objetivo (violeta `#7B3FA0` discontinuo), sensor y revelador |
| 6 | Diferencia en L\* | Columnas; las negativas en rojo |

Colores por canal: rojo `#C0392B`, verde `#2E8B57`, azul `#1F5FA8`.

Detalles técnicos que costó descubrir:

1. El segundo eje de la gráfica de esperado y obtenido es una serie auxiliar con `"y2_axis": True` y sin línea, con el rango desplazado en 5 y su entrada de leyenda eliminada.
2. Las líneas de máximos y mínimos de Excel no se dibujan en LibreOffice: por eso, barras de error.
3. Las líneas constantes (techo, suelo) necesitan una columna de 31 filas: una serie constante no se dibuja con dos puntos.
4. Los puntos recortados no se pintan de otro color (una serie no cambia de color según los datos).

#### 6.8.6 Hoja `Rechazadas` [CERRADO, Tony, 2026-10-12]

La última, detrás de `Cálculo`: las teselas **de tarjeta gris** que los filtros dejan fuera (sin paño, su margen ni las oscuras), cuántas y qué porcentaje, y un gráfico de dispersión: por zona, la desviación de cada rechazada respecto a las aceptadas, **en zonas**, **solo del verde**, una serie por motivo (dispersión, asimetría, nivel).

### 6.9 Láminas PSD

- Plantilla de Tony: `src/bib/biboecf/src/rec/Soportes.psd`, **3300 × 2400 px, 300 ppp, 16 bits RGB**, 31 cuadros de **500 × 350 px**. Las capas se llaman **`Z00`, `Z00-3`, `Z00-7`, `Z01`, …, `Z09-7`, `Z10`** (`Z05` es la ZV) y están en el grupo «Cuadros texturas».
- PyOECF rellena los 31 cuadros con el **recorte del paño**. **No toca capas de ajuste ni curvas** (las hace el alumno).
- Cajetín con los datos reales: se rellena luego; **no se hace PDF [CERRADO]**.
- `psd-tools` (MIT) escribe y lee 16 bits y conserva grupos y textos [VERIFICADO: sustituir una capa, guardar y reabrir con 52 capas intactas].
- **Cuadros de referencia:** L\* teórico por zona con ZV = 50, un paso de luz por zona, recortado a 100 (valores en el apéndice B). El selector Lab de Photoshop acepta **solo enteros**: 5, 7, 8, 10, 12, 15, 17, 20, 22, 26, 29, 33, 36, 41, 45, 50, 55, 61, 67, 74, 81, 89, 97, 100… El script `rellenar_cuadros.jsx` los rellena con decimales, con la transparencia bloqueada.

### 6.10 Demo web (FE)

`oecf.html` (simulador autónomo, sin dependencias) y `oecf.jinja` (para `static/html/oecf.html` de FE, en la misma carpeta que `expo.html`). **Desfasada** frente a lo decidido:

1. La pestaña «Curva tonal» ancla ZX en L\* 100 y deja la ZV en L\* 20,5; la referencia es ZV en 50 con un paso de luz por zona.
2. El sensor simulado tiene un hombro suave, 3,3 EV de margen y ruido 14; la R7 real se recorta de golpe, con unos 3,8 EV y ruido de 4.
3. No muestra la S del revelado.

### 6.11 Piezas de la guía

| Pieza | Contenido | Estado |
|---|---|---|
| **A** | Entrada y validación de la serie | Hecha (2.7, 2.9). Pruebas sin RAW: pendientes, 5.1 |
| **B** | Teselas: paño excluido, estadísticas del paño, ruido por canal, rechazadas | Hecha (2.7). Decidido con Tony: teselas de **48 px**; sin tarjeta (menos de **100** teselas buenas) no hay análisis; negro de las tapadas o el declarado; ruido del borde tapado, comparado con las tapadas si las hay; filtros de dispersión y asimetría a **3** desviaciones robustas y de nivel a **1/3 de zona**, en constantes |
| **C** | Ventana del paño desde la Z-V | Hecha (2.3). Caja «Lámina» con el recorte, tamaños 100 / 50 / 33 / 25 % (solo divisores enteros, por área; nunca por encima del 100 %) y Generar. Casos: tarjeta y paño → Excel y lámina; solo tarjeta → solo Excel; solo paño → nada. Tarjeta y paño en carpetas separadas: fuera |
| **D** | Generador del libro | Hecha (2.7) |
| **E** | Láminas PSD | Hecha (2.7): siempre `Soportes100.psd` y, si se elige otro tamaño, también ese |
| **F** | Integración en la ventana | Hecha (2.3) |
| **G** | Balances de blancos | Hecha (`BalanceMedido`; R7: Flash ≈ 5850 K, Sombra ≈ 6630 K) |
| **H** | Derecheo por tercio | Pendiente (5.1) |
| **I** | Tapadas y balance personalizado | Por hablar (5.1) |

### 6.12 Decisiones cerradas de la guía

1. Una carpeta = una serie; protocolo del apartado 5 con Z-V final obligatoria.
2. Todo en zonas y tercios; solo un eje en «pasos respecto a Z-V».
3. Libro `.xlsx` desde cero con `XlsxWriter`, valores en caché, apertura en Excel.
4. Reglas de formato de 6.8.2, orden de pestañas y colores del texto.
5. `Resumen` conserva la cabecera de Tony; los datos de la serie van en `Datos`.
6. Patrón ZV = L\* 50 con un paso de luz por zona; objetivo de 10 L\* por zona como referencia.
7. `SNRMinima` = 10 como **sugerencia**, comentada con ISO 12232.
8. Curva de tonos de Lightroom, curva de puntos RGB, Perfeccionar saturación a 0, entrada y salida tecleables de 0 a 255, 16 puntos.
9. Ventana del paño detectada desde la Z-V; el resto de tomas, con el mismo encuadre.
10. Sin PDF.
11. `biboecf` no traduce.
12. Repositorio en GitHub, ejecutable con PyInstaller `--onefile`.

### 6.13 Comprobación en Windows

**[VERIFICADO por Tony en Windows, 2026-10-12]:** el libro que genera PyOECF, en Excel, y la lámina PSD, en Photoshop: «todo perfecto». Lo que se pedía mirar: la Vista protegida (números sin «Habilitar edición»), el segundo eje de la gráfica 1, las barras lilas, las barras negativas en rojo de la gráfica 6, el Verdana de `Resumen` sin cortes y las fórmulas `SUMPRODUCT(MAX(…))`. Queda la lectura del 46,6 % en Lightroom (pendientes, 5.3).

### 6.14 Archivos de apoyo de la guía (los tiene Tony)

| Archivo | Contenido |
|---|---|
| `pieza_01_entrada_datos.md` | Entrada del programa y solicitud de datos |
| `pieza_02_rejilla_serie.md` | Rejilla de la serie |
| `Tomas.md` | Secuencia de tomas para el manual |
| `Fuji_6x6.md` | Patrón X-Trans y muestras (resumido más arriba, en este archivo) |
| `PyOECF_completo_v2.xlsx` | Libro de referencia visual y de fórmulas |
| `rellenar_cuadros.jsx` | Script de Photoshop que rellena los 31 cuadros con su L\* |
| `oecf.html` / `oecf.jinja` | Demo interactiva para FE (desfasada, 6.10) |

**Revisar el libro con una IA** (2026-10-13): ver el apéndice F.


## Apéndice A. Lector de marca y modelo (probado en 6 archivos)

Referencia comprobada con CR3, CR2, ARW y RAF. **No sigue la Estrategia: adáptala.**

```python
import struct


def modelo_tiff(datos: bytes):
    # Busca cabeceras TIFF (II*\0 o MM\0*) y lee Make (0x010F) y Model (0x0110)
    for firma, orden in ((b"II*\x00", "<"), (b"MM\x00*", ">")):
        pos = datos.find(firma)
        while pos != -1:
            try:
                desplaz = struct.unpack(orden + "I", datos[pos + 4:pos + 8])[0]
                n = struct.unpack(orden + "H", datos[pos + desplaz:pos + desplaz + 2])[0]
                if 1 <= n < 200:
                    res = {}
                    for i in range(n):
                        e = datos[pos + desplaz + 2 + 12 * i:pos + desplaz + 14 + 12 * i]
                        tag, tipo, cuenta, valor = struct.unpack(orden + "HHI4s", e)
                        if tag in (0x010F, 0x0110) and tipo == 2:
                            if cuenta <= 4:
                                s = valor[:cuenta]
                            else:
                                o = struct.unpack(orden + "I", valor)[0]
                                s = datos[pos + o:pos + o + cuenta]
                            res[tag] = s.split(b"\x00")[0].decode("ascii", "replace").strip()
                    if 0x0110 in res:
                        return res.get(0x010F, ""), res[0x0110]
            except Exception:
                pass
            pos = datos.find(firma, pos + 1)
    return None


def modelo_raf(datos: bytes):
    # Los RAF de Fujifilm llevan el modelo en una cadena fija tras la firma
    if datos[:15] == b"FUJIFILMCCD-RAW":
        return "FUJIFILM", datos[28:60].split(b"\x00")[0].decode("ascii", "replace").strip()
    return None

# Uso: leer los primeros 262144 bytes del archivo y probar modelo_raf y modelo_tiff
```

Resultados esperados: `Canon · Canon EOS R7`, `Canon · Canon EOS 70D`, `Canon · Canon EOS 80D`, `SONY · ILCE-6400`, `FUJIFILM · X70`, `FUJIFILM · X-T3`.

## Apéndice B. Tabla teórica pura (ZV = L\* 50, un paso de luz por zona, sin recortar ni redondear)

Los valores marcados con \* superan 100 y no se pueden representar (el esperado del libro los recorta a 100).

| Zona | +0 | +1/3 | +2/3 |
|---|---|---|---|
| Z0 | 5,20 | 6,55 | 8,25 |
| Z1 | 10,19 | 12,29 | 14,55 |
| Z2 | 17,00 | 19,64 | 22,50 |
| Z3 | 25,58 | 28,91 | 32,50 |
| Z4 | 36,38 | 40,58 | 45,11 |
| ZV | **50,00** | 55,28 | 60,99 |
| Z6 | 67,15 | 73,81 | 81,00 |
| Z7 | 88,77 | 97,16 | 106,22 \* |
| Z8 | 116,00 \* | 126,57 \* | 137,98 \* |
| Z9 | 150,31 \* | 163,62 \* | 178,00 \* |
| ZX | 193,54 \* | — | — |

Dos valores caen casi exactamente en x,50: Z2 2/3 = **22,4955** (redondea a 22) y Z3 2/3 = **32,5012** (redondea a 33). Úsalos como prueba de redondeo.

Luminancia relativa por zona entera: 0,58 %, 1,15 %, 2,30 %, 4,60 %, 9,21 %, **18,42 %**, 36,84 %, 73,67 %, 147,35 %, 294,7 %, 589,4 %. El blanco (100 %) se alcanza en la zona **7,44**.

## Apéndice C. Qué significa cada una de las dos escalas de zona

| Definición | L\* de Z7 | Cuándo se usa |
|---|---|---|
| Un paso de luz por zona (patrón) | 89 | Hablar de exposición |
| Escala perceptual de 10 L\* por zona | 70 | Hablar de la copia impresa |
| Tu medida en Photoshop (R7) | 90 | Dato |

Los dos criterios solo coinciden en la ZV y en ZX. En el artículo hay que decir en cada frase cuál se usa. De la ZV a ZX caben **2,44 EV** (no 5), y los pasos por zona de la escala perceptual van de unos 1,4 EV en las sombras a unos 0,4 en las luces.


## Errores de las revisiones de Gemini y DeepSeek (apéndices D y E)

Revisados con Tony el 2026-10-13. Lo válido de esas revisiones está en `CLD_TODO.md` (5.2); esto **no** se sigue:

- **DeepSeek:** cree que `J51` es la diferencia y que la entrada de la curva es `sRGB(diferencia)`. Falso: `J51` es la **luz obtenida**; la diferencia es `K51`. La fórmula y el texto de `Resumen` están bien.
- **DeepSeek:** dice que el esperado sale de **10 L\* por zona**. Falso: es ZV en L\* 50 con **un paso de luz por zona**; los 10 L\* por zona son el «Objetivo».
- **DeepSeek:** «16 zonas enteras (Z0 a ZX)». Son **11**; los 16 son los puntos que admite la curva.
- **DeepSeek:** el techo, sobre el último valor sin recortar. Error de concepto: el máximo de un canal recortado **es** el techo del sensor.
- **Gemini:** «85 filas de muestras». Son **31** posiciones.
- **Gemini:** el suelo sugerido usa una «S/N de 2 y 1,33». Esos números son la **zona** del suelo; el umbral es `SNRMinima` = 10.
- **Gemini:** la OECF «según ISO 14524 / ISO 12232». La OECF es de la 14524; la 12232 solo se cita para el criterio de señal/ruido.
- **Gemini:** «latitud útil ~7,3 EV». El número coincide, pero en el proyecto se habla en **zonas**, nunca en EV.

## Apéndice D. Conversación con Gemini

Dame tu opinión de esto

Es un libro de trabajo en Excel diseñado para el cálculo de la OECF (Opto-Electronic Conversion Function, según la norma ISO 14524 / ISO 12232) adaptado al Sistema de Zonas.

Puntos Fuertes
Estructura y Organización:

Separación Clara de Responsabilidades: La arquitectura de pestañas (Resumen, Gráficos, Datos, Constantes, Cálculo) sigue las buenas prácticas de modelado en Excel: los datos crudos, las constantes del sistema y la lógica de cálculo están diferenciados.

Uso de Nombres de Celdas/Rangos: Que la pestaña Constantes asigne nombres a cada variable facilita la lectura de las fórmulas y reduce los errores de mantenimiento.

Rigor Metodológico y Muestreo:

Muestreo Fino por Tercios de Zona: Capturar datos a intervalos de 1/3 EV (85 filas de muestras desde Z0 a ZX) proporciona la resolución necesaria para modelar la curva OECF y detectar codos o inflexiones en la respuesta del sensor.

Análisis Independiente por Canal (RGB): Evaluar el techo de saturación, ruido de lectura y rango dinámico de forma separada para Rojo, Verde y Azul permite detectar desbalances de balance de blancos o recorte prematuro de algún canal específico.

Integración Práctica (Lab y Lightroom):*

Sugerencia para Revelado Perceptual: El mapeo de valores L* medidos versus los esperados (según ISO/CIE 11664-4) traducidos directamente a puntos clave (0-255) para la curva de tonos de Lightroom es un puente práctico entre la caracterización de la cámara y el flujo de trabajo de revelado.

Observaciones y Áreas de Mejora
Evaluación de la Latitud Útil:

En la pestaña Cálculo, se define un Suelo sugerido por relación señal/ruido (S/N) de valor 2 en Rojo/Azul y 1.33 en Verde. Con estos umbrales se calcula una Latitud sugerida de ~7 a 7.33 zonas.

Recomendación: Asegurarse de que los criterios de la relación señal/ruido (S/N) o la definición de ruido de lectura estén alineados con los estándares específicos que se busquen aplicar (por ejemplo, ISO 12232 o criterios de aceptación visual según el medio de salida).

Cómputo en Sombras Profundas (Z0 a Z1):

En las zonas más oscuras, la relación señal/ruido disminuye notablemente y los errores de lectura o corriente oscura pueden distorsionar los valores calculados de L 
∗
 . La tabla de sugerencia en Resumen muestra correcciones acentuadas en las sombras (p. ej. diferencias de hasta −11 puntos L 
∗
 ).

Resumen General
Es un modelo técnico de caracterización fotográfica, muy bien estructurado, que automatiza la obtención de la curva OECF de la Canon R7 y proporciona referencias aplicables a la gestión de tono y color en revelado digital.

¿Podrías sugerirme un diseño de la hoja para que fuese más bonita?

Para lograr un diseño más profesional, limpio y visualmente atractivo en tu libro de Excel (sin perder la rigidez técnica del análisis OECF), te sugiero aplicar las siguientes mejoras de estructuración, jerarquía y diseño visual:

1. Paleta de Colores y Tipografía (Estilo Ejecutivo / Técnico)
Tipografía: Usa una fuente moderna y muy legible como Segoe UI, Aptos o Calibri, manteniendo un tamaño base de 10 u 11 pt para datos y 12–14 pt para encabezados.

Paleta de Colores Consistente:

Encabezados primarios (Títulos de sección): Azul marino oscuro (#1F4E78 o #1B365D) con texto en blanco y negrita.

Encabezados de tabla: Azul claro / grisáceo (#D9E1F2 o #EDF2F8) con texto oscuro (#262626).

Filas alternas (Zebra striping): Fondo blanco alternado con un gris extremadamente suave (#F8F9FA) para facilitar la lectura de tablas largas (como las de 85 filas en Datos y Cálculo).

Pestañas (Sheet Tabs): Asigna un color distintivo a cada pestaña para diferenciarlas rápidamente:

Resumen: Azul corporativo.

Gráficos: Verde suave o Violeta.

Datos: Gris / Neutro.

Constantes: Naranja / Ámbar (indica parámetros de entrada).

Cálculo: Azul acero.

2. Estructura y Maquetación por Pestaña
Pestaña Resumen (Panel de Control / Dashboard)
Ocultar la cuadrícula (Gridlines): Desactiva las líneas de cuadrícula en esta pestaña (Vista > Líneas de cuadrícula).

KPI Cards (Tarjetas de métricas clave): En lugar de celdas simples en la zona superior, crea "cajas de resumen" redondeadas o destacadas con borde suave para mostrar de un vistazo:

Cámara / Modelo: Canon R7

Ajustes: ISO 100 | 1/125s | f/9

Diferencia Media L 
∗
 : 5.17

Latitud Útil: ~7.3 EV

Tabla de Curva de Tonos para Lightroom:

Usa formato condicional en la columna Diferencia L 
∗
 : barra de datos bipolares (verde para desviaciones positivas, rojo/naranja suave para negativas) o escalas de color atenuadas.

Resalta visualmente los puntos principales de zona entera (Z0,Z1,…,ZX) con negrita y un ligero relleno de fondo, diferenciándolos de los tercios de zona.

Pestaña Constantes
Formato de Tabla Oficial (Ctrl + T): Convierte el rango en una Tabla Estructurada con encabezados resaltados.

Formato Diferenciado para Entradas: Pon un fondo suave (p. ej. amarillo/crema muy tenue #FFF2CC) a la columna de Valor para indicar al usuario que son campos editables.

Alineación:

Texto / Nombres / Descripción: Alineado a la izquierda.

Unidades: Centrado.

Valores numéricos: Alineado a la derecha.

Pestañas de Datos Masivos (Datos y Cálculo)
Inmovilizar Paneles: Aplica Vista > Inmovilizar paneles en la fila de encabezados para mantener visible la cabecera al desplazarte por las 85 filas.

Formato de Números Consistente:

Limita los decimales a 2 o 3 dígitos según la métrica (0.00 o 0.000) para evitar números de longitud variable que ensucian la vista.

Colores por Canal RGB:

En las columnas de datos de canales (Rojo, Verde, Azul), usa acentos de color muy suaves en los encabezados (rojo pastel #FCE4D6, verde pastel #E2EFDA, azul pastel #DDEBF7) para identificar el canal inmediatamente sin recargar la pantalla.

3. Resumen de Buenas Prácticas Visuales
Alineación: Texto a la izquierda, números a la derecha, códigos/unidades/zonas al centro.

Espaciado y Márgenes: Ajusta el ancho de las columnas con un margen de holgura (no dejes el texto pegado a los bordes de la celda).

Regla del Menos es Más: Evita bordes negros gruesos; prefiere líneas finas de color gris claro (#D9D9D9) para separar celdas.


## Apéndice E. Conversación con DeepSeeek


Dame tu opinión de esto
Opinión sobre PyOECF_completo.xlsx
He revisado el libro con calma. Es un trabajo muy serio, bien estructurado y metodológicamente sólido, pero también con algunos detalles que conviene pulir. Te doy mi opinión por partes.

1. Lo que está muy bien
Arquitectura del libro
La separación en hojas es limpia y profesional:

Datos → solo lo leído del RAW (con una única media calculada).

Constantes → todo parametrizado con nombres, no con celdas ni números sueltos.

Cálculo → no guarda datos propios, solo deriva.

Resumen → presentación para el usuario.

Gráficos → capa de visualización.

Esto es exactamente lo que se pide en un libro de ingeniería: separación entre dato, parámetro y resultado. La nota de colores (azul = dato, naranja = literal, negro = fórmula, gris = rótulo) es un detalle de calidad.

Uso de nombres definidos
Que las fórmulas usen ZonaZV, FactorZona, ToleranciaLineal, UmbralRecorte, etc., en lugar de $E$5 o 2, hace el libro auditable y portable. Es la diferencia entre una hoja de cálculo y una herramienta.

El método en sí
La idea de fondo es coherente:

Medir niveles RAW por zona y tercio.

Referir todo a la ZV (zona V = gris medio, L* = 50).

Calcular la latitud útil entre el techo (saturación) y el suelo (ruido de lectura).

Convertir a L* esperado con la escala perceptual (10 L* por zona).

Comparar con el L* medido con cuentagotas.

Generar una curva de puntos RGB en Lightroom con entrada = L* obtenido y salida = L* esperado, en escala 0–255.

El enfoque es correcto y estándar en colorimetría aplicada a fotografía. La referencia a ISO/CIE 11664-4:2019 está bien traída.

Detalles finos que se agradecen
La ZV de control (_MG_8178.CR3) además de la ZV principal (_MG_8162.CR3), y la media de todas.

El ruido de lectura medido en borde tapado (4.46 / 3.77 / 4.43), no supuesto.

El uso de RelacionSR = 1 para el suelo por ruido y SNRMinima = 10 como sugerencia (no como resultado), con nota explícita de que viene de ISO 12232.

La interpolación de tercios cuando no hay medida, marcada con TextoInterpolado = "sí".

La comprobación explícita: "el parche ZV debe leer 46,6 % en Revelar (119)".

La marca ● solo en zonas enteras (16 puntos máximo de la curva).

2. Puntos que revisaría
2.1. La ZV y el L* = 50
Dices en Constantes que LZV = 50 y que es "entero, para teclearlo en el selector Lab". Pero en la hoja Datos, la ZV medida tiene L* medido = 50 y el parche ZV debe leer 46,6 % (119/255). Eso es coherente con sRGB: 119/255 ≈ 0,4667 → L* ≈ 50. Está bien, pero conviene que quede explícito en algún sitio que *119 es el valor sRGB de L = 50**, no un valor arbitrario.

2.2. El techo por canal
excel
Techo = ZonaZV + LOG(E9/D9, FactorZona)
donde E9 es el máximo del canal y D9 la media de la ZV. Esto da el techo en zonas relativas a la ZV, lo cual es correcto. Pero ojo: el máximo se toma sobre toda la serie (MAX(Datos!F$8:F$38)), y en las zonas altas ya hay canales recortados (Z9, Z9 1/3, Z9 2/3, ZX). Si el máximo está recortado, el techo calculado no es el techo real del sensor, sino el techo del recorte. En la práctica da igual porque el Primer punto recortado te avisa, pero conceptualmente el techo debería calcularse sobre el último valor no recortado, no sobre el máximo bruto.

2.3. El suelo por ruido de lectura
excel
Suelo = ZonaZV - LOG(D9/(Datos!F51*RelacionSR), FactorZona)
Esto sitúa el suelo donde la señal iguala al ruido de lectura (RelacionSR = 1). Es una definición válida, pero muy conservadora: SNR = 1 es prácticamente invisible. Por eso después calculas el Suelo sugerido con SNRMinima = 10. Bien. Solo faltaría que en el Resumen se vea claramente cuál de los dos suelos se usa para la latitud sugerida (veo que usas el de SNR 10, que es lo sensato).

2.4. La latitud
excel
Latitud = I9 - K9   (Último punto lineal - Suelo sugerido)
Mezclas dos criterios: el techo lo pones en el último punto lineal (tolerancia 0,1 zonas) y el suelo en el suelo sugerido por SNR 10. Es una decisión defendible, pero no es simétrica. O usas linealidad en ambos extremos, o usas SNR en ambos. Tal como está, la latitud es "de lineal a SNR 10", lo cual conviene documentar en una nota.

2.5. Dispersión verde = 0 en zonas altas
En Datos, las filas Z9, Z9 1/3, Z9 2/3 y ZX tienen Dispersión verde = 0 (y en Z9 2/3 y ZX también rojo y azul = 0). Eso hace que Señal/ruido verde = 0 (por el IF(Datos!J8>0,...)), lo cual es correcto como salvaguarda, pero distorsiona el cálculo del Suelo sugerido (señal/ruido) porque esas filas quedan excluidas por el +($O$16:$O$46<SNRMinima)*1000. En la práctica funciona, pero es frágil. Yo añadiría una columna auxiliar que marque explícitamente "canal recortado / sin dato" y que el SUMPRODUCT filtre por esa marca, no por el valor 0.

2.6. La curva de Lightroom
El punto clave del método es:

Entrada = L* obtenido, Salida = L* esperado, ambos en 0–255 vía sRGB.

Pero en la hoja Cálculo, columna N (Entrada 0-255) se calcula como:

excel
ROUND(255 * sRGB(J), 0)
donde J es la diferencia I - F (Obtenido − Esperado), no el L* obtenido. Eso es un error conceptual grave, salvo que esté malinterpretando la estructura. Déjame releer…

En la fila 51:

I51 = Obtenido (L*)

F51 = Esperado (L*)

J51 = I51 - F51 → Diferencia

N51 = ROUND(255 * sRGB(J51), 0) → Entrada = sRGB(Diferencia)

O51 = ROUND(255 * sRGB(E51), 0) → Salida = sRGB(Luz esperada)

Eso no es lo que dice el Resumen ("Entrada = L obtenido y salida = L* esperado"). Si J es la diferencia, la entrada sería la diferencia en L, no el L* obtenido.

Aquí hay una incoherencia entre lo que dice el Resumen y lo que hace Cálculo. O el Resumen está mal redactado, o la fórmula de N está mal. Hay que aclararlo, porque es el corazón del método.

Posibilidades:

Si la curva debe ser Entrada = L obtenido, Salida = L esperado**, entonces N debería ser sRGB(I) y O debería ser sRGB(F). Pero entonces la curva no corrige nada, solo mapea lo medido a lo esperado… que es justo lo que se quiere. Vale.

Si la curva debe ser Entrada = L obtenido, Salida = L obtenido + corrección**, entonces O debería ser sRGB(I + (F - I)) = sRGB(F). Que es lo mismo que arriba.

Si la curva debe ser Entrada = L esperado, Salida = L obtenido**, entonces N = sRGB(F) y O = sRGB(I).

En cualquier caso, J (diferencia) no debería ser la entrada de la curva. Revisa esto, porque es el punto más delicado de todo el libro.

2.7. Punto de la curva en el Resumen
En Resumen, la columna H (Punto de la curva) lee =Cálculo!Q51, y en Cálculo Q51 = IF(MOD(D51,3)=0, "●", ""). Es decir, marca las zonas enteras. Correcto, porque Lightroom admite 16 puntos y hay 16 zonas enteras (Z0 a ZX). Bien.

Pero en el Resumen solo se muestran las filas 51–81 (31 filas = 31 tercios). Si Lightroom solo admite 16 puntos, sobran 15 filas en la tabla del Resumen. No es un error, pero puede confundir al usuario. Yo añadiría una nota: "solo las filas marcadas con ● son puntos de la curva; las demás son informativas".

2.8. La comprobación del 46,6 %
Dices: "el parche ZV debe leer 46,6 % en Revelar (119)". Eso es L = 50 en sRGB**. Correcto. Pero conviene verificar que en la hoja Cálculo, para la fila de la ZV (fila 61, D61 = 0), el valor O61 (Salida) sea efectivamente 119. Si E61 = Luz esperada para la ZV = LuzZV = luminancia de L 50 ≈ 0,1842, entonces sRGB(0,1842) ≈ 0,4667 → 255 * 0,4667 ≈ 119. Debería dar 119. Si no da 119, hay un desajuste en las constantes de sRGB o en LuzZV. Merece una comprobación explícita en el libro (una celda que diga "OK" o "revisar").

3. Sugerencias de mejora
Aclarar la fórmula de la curva. Es lo más importante. La entrada de la curva debe ser un L* (obtenido o esperado), no una diferencia. Corrige el Resumen o la fórmula, pero que coincidan.

Añadir una celda de validación que compruebe que O para la ZV = 119. Si no, que avise.

Separar "recortado" de "sin dato". En las zonas altas, Dispersión = 0 porque el canal está saturado, no porque no haya ruido. Una marca explícita evitaría malentendidos.

Documentar la asimetría de la latitud (lineal en el techo, SNR 10 en el suelo). Es una decisión válida, pero debe estar escrita.

Reducir la tabla del Resumen a los 16 puntos de la curva, o añadir la nota de que las filas sin ● son solo informativas.

En Constantes, LZV = 50 conviene acompañarlo de una nota: "L = 50 corresponde a 119/255 en sRGB, que es el 46,6 % que debe leer el parche ZV en Revelar"*.

El techo por canal debería calcularse sobre el último valor no recortado, no sobre el máximo bruto, para que sea el techo real del sensor y no el techo del recorte.

Internacionalización: el libro está en español, con nombres de constantes en español (ZonaZV, FactorZona). Es coherente, pero si va a circular, unos nombres en inglés o bilingües facilitarían el intercambio.

4. Valoración global
Es un libro muy por encima de la media de lo que se ve en fotografía técnica. Tiene:

Método claro y justificado.

Referencias normativas.

Separación dato / parámetro / resultado.

Constantes con nombre.

Interpolación marcada.

Comprobación cruzada (ZV de control, ruido de lectura medido).

El único punto que hay que corregir sí o sí es la incoherencia entre lo que dice el Resumen ("Entrada = L obtenido, Salida = L* esperado"*) y lo que hace Cálculo (N = sRGB(I - F)). Todo lo demás son refinamientos.

Si corriges eso y añades la celda de validación del 119, el libro queda listo para uso profesional. Buen trabajo.


## Apéndice F. Prompt para revisar el libro con una IA

Definitivo, redactado por Claude web (2026-10-13) con los errores de Gemini y DeepSeek. **Vive en `src/biboecf/rec/prompt_ia.md`** (antes, `src/bib/biboecf/src/rec/`; los nombres de las constantes van como huecos, `{snr_minima}`, que rellena `Excel.con_nombre`), junto a `Soportes.psd`, porque es de biboecf (Tony): solo en español; Tony lo edita ahí. El libro lo lee él mismo (`COM.RUTA_PROMPT_IA`, `biboecf.RUTA_PROMPT_IA`) y lo copia en su hoja **IA**, una línea por fila, en cada Generar; `PyOECF.spec` lo mete en el ejecutable en la misma ruta relativa que la plantilla. Para usarlo: dar a la IA el `PyOECF.xlsx` y pedirle que siga la hoja IA (o pegarle el archivo).
