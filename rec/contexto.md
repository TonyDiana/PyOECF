# Contexto de PyOECF

<!-- cSpell:ignore biboecf, derecheo, derecheos, pano, pyexiv, rawpy, teselas, numpy, customtkinter, aquila -->

Punto de partida para cualquier agente que empiece a trabajar en este repositorio. Resume lo decidido hasta el 2026-10-05.


## Antes de nada

- Las instrucciones globales de Tony (`~/.claude/CLAUDE.md`) y la memoria de este proyecto se cargan solas si la sesión se abre en `~/Dev/Python/Aplicaciones/PyOECF`. Respetarlas: dislexia y TDA, literales nunca repetidos, siempre en español, «cd» = «confirma o desmiente».
- Estándar de programación: `rec/estrategias/Estrategia_slr.md`. Prevalece sobre cualquier otra indicación de estilo.
- Normas de la ayuda (MkDocs): `Repo/doc/mkdocs/USO.md`.
- Forma de trabajar: **paso a paso**. Proponer y esperar el sí antes de crear, cambiar o borrar. **Nunca quitar nada** sin su sí expreso. Cambiar **solo** donde Tony indique; lo demás, señalarlo aparte.


## Qué es PyOECF

Cálculo de la curva OECF de un sensor fotográfico a partir de una serie de RAW de una tarjeta gris y un paño de algodón gris, con materiales sencillos. Pensado para un aula.

Versión alfa: `VERSION` = `0.x`. El formato año.mes de la Estrategia llegará con la primera versión estable.


## Arquitectura

```text
biboecf  (src/bib/biboecf)   ← CASI TODO: lectura de RAW, solicitud de datos,
   │                            validación, cálculo, informe. Sin interfaz.
   ├── PyOECF                 ← aplicación delgada: su ventana + llamar a biboecf
   └── FotoEstación (FE)      ← hará lo mismo con su propia interfaz
```

- **Dos modos**: biboecf es la biblioteca; PyOECF, la aplicación independiente que la usa. PyOECF es el modelo de cómo la usará FE.
- **Dónde se trabaja**: el código de la biblioteca se escribe **en `src/bib/biboecf` de este repo**. Tony lo lleva él al repo real (`Bibliotecas/Foto/BibOECF`) con `bib.sh`. No escribir en ese repo ni en FE.
- **FE está parada** hasta que PyOECF funcione.
- **Dependencias de biboecf**: `rawpy` y `numpy`, y puede usar Std con `from bib import std` (criterio de toda la suite: una biblioteca no lleva otras dentro; las pone quien la usa, y PyOECF ya tiene `std` y `aquila` en `src/bib`).
- La interfaz se genera a partir de la **declaración de campos** de la pieza 1: ninguna interfaz define campos propios.


## Estado actual (0.2, alfa)

- `src/main.py`: solo una ventana de saludo (customtkinter), para probar el empaquetado.
- Ejecutables generados en GitHub con `PyOECF.spec` y el workflow `publicar_ejecutables.yml`: probados en Linux y Windows; macOS sin probar.
- Manual de usuario publicado en <https://tonydiana.github.io/PyOECF/> (fuentes en `doc/src_manual`).
- Flujo: `dev` → `master` (`gg mini dev` + commit) → `rec/scripts/Remoto_slr.sh` → rama `deploy` de GitHub.
- Dependencias del entorno: `rec/requirements/requirements.conf` (venv en `.venv`).
- Notas de diseño: apartado 3 de `rec/estrategias/bitacora/CLD_BITACORA.md` (allí ya está puesto al día lo de «Dos modos»).


## Siguiente paso

Pieza 1: **proponer** los nombres de los paquetes y módulos de `biboecf` (el módulo central se llama `kernel`, según la Estrategia) y el esquema de la declaración de campos y del informe. Esperar la confirmación de Tony antes de crear archivos.


## Pieza 1 · Documento original

Documento de Tony, tal como lo entregó (salvo el título del primer apartado).

### 1. Objetivo

Definir qué datos pide PyOECF al usuario, cuáles deduce solo, sus valores por defecto y sus validaciones, **sin depender de la interfaz** (la ventana Tk y la línea de órdenes se construirán después a partir de esta definición).

La pieza entrega tres cosas:

1. Una **solicitud de datos** declarativa (campos, tipos, defectos, origen, validadores).
2. Una **serie validada**: las tomas ordenadas, con su posición en tercios y su zona.
3. Un **informe** con los errores y avisos de la serie, para que cualquier interfaz lo muestre.

### 2. Contexto mínimo

- PyOECF es una biblioteca Python independiente, en un repositorio público de GitHub. No depende de FotoEstación (FE), que más adelante la vendorizará como submódulo.
- A partir de una serie de RAW de una tarjeta gris mide el comportamiento lineal del sensor, el recorte por canal y el margen para el derecheo. La salida es una hoja `.xlsx` y láminas PSD.
- Cada serie está en **una carpeta** y tiene **35 archivos**, en este orden de captura:
  1. Z-V con balance de blancos arbitrario (con ella se crea el balance personalizado).
  2. Z-V con el balance ya personalizado.
  3. 15 tercios hacia un lado.
  4. Z-V otra vez, al cambiar de lado.
  5. 15 tercios hacia el otro lado.
  6. Dos tomas con la tapa puesta, a 1/160 s.
- Se varía solo el tiempo de exposición. Diafragma e ISO son fijos. El lado por el que se empieza no es fijo: lo detecta el programa.
- Licencia: la del repositorio (`LICENSE_BIB.md`, **pendiente de confirmar para PyOECF**).
- Dependencias permitidas en esta pieza: la biblioteca estándar, `rawpy` y `numpy`. **Prohibido `pyexiv2`**, que es GPLv3 y choca con la licencia no comercial de la biblioteca; no lo uses ni como dependencia opcional.

### 3. Decisiones ya cerradas

#### 3.1 Lectura de cada RAW

- Con `rawpy`, y solo con él, se obtienen: tiempo de exposición (`raw.other.shutter_speed`), diafragma (`raw.other.aperture`), ISO (`raw.other.iso_speed`), fecha (`raw.other.timestamp`, resolución de 1 s), dimensiones visibles, patrón de color, canales, negro y blanco declarados. Está comprobado en CR3, CR2, ARW y RAF.
- El tiempo llega en coma flotante de 32 bits (1/125 s llega como `0.00800000037997961`). No lo compares por igualdad: usa una tolerancia relativa.
- **Marca y modelo** no los da `rawpy`. Se leen con un lector propio, sin dependencias (véase el apéndice). No se lee el número de serie, ni se guarda en ningún sitio.
- El ISO se anota en la cabecera, pero **no se mide por ISO** en esta versión.

#### 3.2 Orden de captura y referencia

- Se ordena por (fecha, número del nombre del archivo). La fecha tiene resolución de 1 s: los empates se deshacen con el número final del nombre. Si aun así hay ambigüedad, aviso.
- La **referencia** es la primera toma que no sea tapada. Sus ajustes fijan la Z-V.

#### 3.3 Posición de cada toma

- Exposición relativa: `t · ISO / f²`.
- `tercioEV = redondeo(3 · log2(exposición / exposición_de_referencia))`. Es un número entero interno: positivo si la toma tiene **más** exposición que la Z-V.
- Zona: `zona = 5 + tercioEV / 3`. Se nombran como en el fotómetro: `Z0`, `Z0.3`, `Z0.7`, `Z1`, …, `ZV`, …, `Z9.7`, `ZX`. Internamente se guarda el número (5,3333…), nunca el texto.
- Los tiempos que marca la cámara están redondeados. El redondeo a `tercioEV` solo sirve para decidir qué toma es cada una; cualquier cálculo posterior usará el tercio exacto, no el tiempo nominal. Ejemplo real: 1/13 s da `3·log2 = +9,80` y `tercioEV = +10`.
- **(?)** Aviso si `|3·log2(...) − tercioEV| > 0,33`. Es una propuesta: el desvío máximo observado en una serie real es 0,20.

#### 3.4 Secuencia esperada

Con `tercioEV = 0` como Z-V: Z-V, Z-V, tercioEV de ±1 a ±15 en un sentido, Z-V, tercioEV de ∓1 a ∓15, y las dos tapadas al final. El sentido de cada lado se deduce del signo de `tercioEV` de la primera toma distinta de la Z-V.

Las tapadas son a 1/160 s, que coincide con `tercioEV = −1` si la Z-V es 1/125 s: **por los ajustes no se distinguen** de un duplicado. En esta pieza solo se suponen las **dos últimas** de la secuencia. Reconocerlas por su contenido es de otra pieza.

#### 3.5 Errores y avisos

| Nivel | Condición | Ejemplo de mensaje |
|---|---|---|
| **Error** (detiene) | Archivos de cámaras o tamaños distintos | «`_MG_8170.CR3` tiene otro tamaño que el resto» |
| **Error** | Las dos primeras tomas no tienen los mismos ajustes | «La toma 2 tiene f/11 y la referencia f/9» |
| **Error** | **(?)** Cambia el ISO dentro de la serie | «La toma 18 tiene ISO 200 y la referencia ISO 100» |
| **Aviso** | Cambia el diafragma dentro de la serie | «La toma 18 tiene f/11 y la referencia f/9» |
| **Aviso** | Falta una posición (hueco) | «No hay toma en la zona 4 2/3» |
| **Aviso** | Posición repetida | «Hay dos tomas en la zona 6» |
| **Aviso** | Tomas de más o fuera de ±15 | «Hay 36 tomas; se esperaban 35» |
| **Aviso** | Falta la Z-V del cambio de lado | «La serie cambia de lado sin volver a la Z-V» |
| **Aviso** | Un lado no llega a ±15 | «El lado de las luces termina en la zona 8» |
| **Aviso** | Orden de captura distinto del esperado | «La toma `_MG_8180.CR3` está fuera de orden» |
| **Aviso** | **(?)** Desvío mayor que 0,33 tercios respecto a la rejilla | «La toma `_MG_8172.CR3` no encaja en los tercios» |

Los avisos no detienen el análisis: cada interfaz decide cómo mostrarlos. La estructura de la serie (qué falta y qué sobra) se informa, no se corrige.

### 4. Datos que pide el programa

Declara los campos de forma declarativa (nombre, etiqueta, tipo, defecto, origen, validadores), para generar la interfaz a partir de ella. **No acoples la pieza a `EnteDatos`**: PyOECF es independiente.

| Campo | Tipo | Origen | Defecto | Validación |
|---|---|---|---|---|
| `carpeta_serie` | ruta | usuario | obligatorio | existe y contiene RAW |
| `camara_marca` | texto | archivo, editable | lo leído | no vacío |
| `camara_modelo` | texto | archivo, editable | lo leído | no vacío |
| `derecheos_tercios` | lista de enteros ≥ 0 | usuario | `(0,)` | cada `d` es un número entero de tercios |
| `metodo_reduccion_pano` | texto | usuario | `"bicubica"` | uno de los métodos admitidos (**?** lista por decidir) |
| `lado_teselas` | entero o nulo | usuario | nulo (se calcula por serie en otra pieza) | múltiplo del periodo del patrón |
| `tolerancia_lado_teselas` | decimal | usuario | **(?)** 0,1 | mayor o igual que 0 |
| `ventana_pano` | cuatro enteros o nulo | usuario | nulo (se detecta y se confirma) | dentro del encuadre; al menos 1000 × 700 px |
| `plantilla_psd` | ruta o nulo | usuario | nulo | existe, si se indica |
| `texto_soporte` | texto | usuario | vacío | sin restricción |
| `carpeta_salida` | ruta | usuario | la de la serie | se puede escribir |

Los derecheos `d` se expresan en tercios (`1 = +1/3`, `2 = +2/3`, `3 = +1`…). Nunca en EV.

Datos que se **deducen** y no se piden: la lista de tomas ordenadas, la referencia, `tercioEV` y la zona de cada toma, el sentido de los lados, la fecha, el ISO, el diafragma, las dimensiones y el patrón de color.

### 5. Interfaz de la pieza

- **No** dibujes ventanas ni leas de la línea de órdenes. Expón una función que reciba los valores y devuelva la serie validada y el informe, y otra que devuelva la descripción de los campos.
- Todo lo que se muestre al usuario (etiquetas, avisos, errores) va en español y se separa del cálculo, para poder traducirlo después.
- Si falla la lectura de un archivo, se informa del archivo y no se aborta el resto.

### 6. Convenciones

La **Estrategia de programación** del repositorio (`rec/estrategias/Estrategia.md`) prevalece. En resumen:

- Identificadores en español, minúsculas con guion bajo, **sin tildes ni `ñ`** (por ejemplo `pano`, no `paño`). Comentarios en español.
- Comillas dobles siempre. Los docstrings no terminan en punto.
- Anotaciones de tipo obligatorias en toda función, método y propiedad.
- Cabecera de módulo con `:Propósito:`, `:Autor:` y `:Versión:`, `__all__` y las secciones de importación comentadas.
- Imports relativos dentro del paquete. Sin literales mágicos: diccionario de constantes al principio del módulo.
- Funciones si no hay persistencia. Si hay clases, `__slots__` lo primero.
- Los paquetes y módulos tienen nombres descriptivos y ningún módulo se llama igual que su paquete. **(?)** Propón los nombres y espera la aprobación.

### 7. Criterios de aceptación

Los RAW están en el disco del director y **no se suben nunca al repositorio** (añádelos al `.gitignore`).

1. **Serie real de la R7** (`_MG_8162` a `_MG_8193`, 32 archivos):
   - Orden por nombre ascendente y referencia `_MG_8162`.
   - Posiciones: `_MG_8163` en `tercioEV = +1`, `_MG_8177` en `+15`, `_MG_8178` en `0`, `_MG_8179` en `−1` y `_MG_8193` en `−15`.
   - Primer lado hacia más exposición, segundo hacia menos.
   - El informe da **avisos**, no errores: falta la segunda Z-V inicial y las dos tapadas.
2. **Carpeta con 13 tomas Z-V** (`_MG_8194`…`_MG_8206`, sin la `_MG_8198`): todas en `tercioEV = 0`, sin lados, con avisos de estructura. No debe fallar.
3. **Lectura de modelo** en seis archivos de cuatro formatos:

   | Formato | Archivo | Marca y modelo esperados |
   |---|---|---|
   | CR3 | `_MG_8162.CR3` | Canon · Canon EOS R7 |
   | CR2 | `_MG_5509.CR2` | Canon · Canon EOS 70D |
   | CR2 | `IMG_7222.CR2` | Canon · Canon EOS 80D |
   | ARW | `_DSC6275.ARW` | SONY · ILCE-6400 |
   | RAF | `x70_DSCF1276.RAF` | FUJIFILM · X70 |
   | RAF | `x-t3_DSCF1630.RAF` | FUJIFILM · X-T3 |

4. **Pruebas automáticas con listas de tiempos, sin RAW**: una serie de 35 correcta, una con un hueco, una con una repetida, un cambio de ISO (error), un cambio de diafragma (aviso) y el caso de `1/13 → tercioEV = +10`.
5. Ninguna prueba depende de archivos que no estén en el repositorio.

### 8. Fuera de alcance

El análisis (teselas, linealidad, recorte), el reconocimiento de las tapadas por su contenido, la ventana del paño, la hoja de cálculo, las láminas PSD, la interfaz gráfica, el empaquetado, la ficha por ISO y cualquier curva de revelado.

### 9. Forma de trabajar

Esta pieza se construye **paso a paso**. Primero propón los nombres de los paquetes y módulos y un esquema de los campos y del informe, y **espera la confirmación** antes de crear archivos. No avances a otra pieza sin que se te pida.

### Apéndice: lector de marca y modelo (probado)

Referencia comprobada en los seis archivos de la tabla anterior. No sigue la Estrategia: adáptala.

```python
import struct


def modelo_tiff(datos: bytes):
    # Busca cabeceras TIFF (II*\0 o MM\0*) en los primeros bytes del archivo
    # y lee Make (0x010F) y Model (0x0110) del primer directorio de etiquetas
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


## Pieza 1 · Cambios y propuestas posteriores al documento

- **Dos modos** (cambia el punto 2 del documento): ya no es solo una biblioteca; ver «Arquitectura». biboecf puede usar Std.
- **Contradicciones del documento con su criterio 1** (serie R7), con propuesta, **sin confirmar**:
    - Tapadas «las dos últimas», pero en la R7 las dos últimas son tomas normales. Propuesta: solo si las dos son de 1/160 s.
    - «Las dos primeras con ajustes distintos» es error, pero la R7 solo debe dar avisos. Propuesta: error si cambia diafragma o ISO; aviso si solo cambia el tiempo.
- **Puntos (?) con propuesta, sin confirmar**: desvío 0,33 → aviso; cambio de ISO → error; `metodo_reduccion_pano` → `area`, `bicubica`, `bilineal`; `tolerancia_lado_teselas` → 0,1.
- **Licencia**: el documento habla de `LICENSE_BIB.md`; el repo enlaza hoy `LICENSE_APP.md` (es aplicación). Sin decidir para biboecf.
- **RAW en el `.gitignore`**: pedido por el documento, aún sin hacer.
- **Ventana inicial** (modo aplicación, decidida): una sola ventana de arriba abajo: carpeta de la serie → lo leído (cámara editable, resumen e informe) → ajustes (los técnicos ocultos en «avanzados») → botón «Preparar», desactivado si hay errores. Pendiente: qué ajustes se ven siempre, y si los avisos hay que confirmarlos.
