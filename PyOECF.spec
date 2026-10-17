# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
# Receta de PyInstaller para PyOECF: ÚNICO sitio con las opciones de
# empaquetado. La usan igual la prueba local y el workflow
# .github/workflows/publicar_ejecutables.yml:
#
#   pyinstaller PyOECF.spec
#
# Windows y Linux → un único archivo ejecutable.
# macOS           → una aplicación PyOECF.app (PyInstaller desaconseja un
#                   único archivo con ventana en macOS).
# =============================================================================

# cSpell:ignore customtkinter, SPECPATH

# --- Bibliotecas estándar Python
import sys
from pathlib import Path

# --- PyInstaller
from PyInstaller.utils.hooks import collect_data_files

# --- Constantes de la aplicación: el .spec las LEE, no las repite.
#     src/ al path para poder importar kernel (como hace src/main.py)
RAIZ = Path(SPECPATH)               # --- Carpeta de este archivo
SRC = RAIZ / "src"                  # --- Código fuente
sys.path.insert(0, str(SRC))
from kernel.constantes import K     # noqa: E402
import biboecf                      # noqa: E402

# --- Literales mágicos
NOMBRE = K.NOMBRE
PUNTO_ENTRADA = SRC / "main.py"
ES_MAC = sys.platform == "darwin"

# --- Datos que no son código y deben ir dentro:
#     - el archivo de versión (K.ARCHIVO_VERSION)
#     - los iconos de la ventana (K.ICONOS), en su carpeta de recursos,
#       el .ico, que la ventana usa en Windows, y el PNG de la cabecera
#     - la plantilla PSD de las láminas (biboecf.RUTA_PLANTILLA), 48 MB,
#       en la misma ruta relativa que en el código (biboecf/rec):
#       biboecf la busca junto a su código, también en el ejecutable
#     - las instrucciones de la hoja IA del libro (biboecf.RUTA_PROMPT_IA),
#       igual que la plantilla
#     - temas de customtkinter: sin ellos la ventana falla al abrir
DATOS = [(str(RAIZ / K.ARCHIVO_VERSION), ".")]
REC = RAIZ / K.CARPETA_RECURSOS
DATOS += [(str(REC / icono), K.CARPETA_RECURSOS)
          for icono in (*K.ICONOS, K.ICONO_ICO, K.ICONO_PNG)]
PLANTILLA = biboecf.RUTA_PLANTILLA
DATOS += [(str(ruta), str(ruta.parent.relative_to(SRC)))
          for ruta in (PLANTILLA, biboecf.RUTA_PROMPT_IA)]
DATOS += collect_data_files("customtkinter")

a = Analysis([str(PUNTO_ENTRADA)], datas=DATOS)
pyz = PYZ(a.pure)

if ES_MAC:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
              name=NOMBRE, console=False)
    coll = COLLECT(exe, a.binaries, a.datas, name=NOMBRE)
    app = BUNDLE(coll, name=f"{NOMBRE}.app",
                 icon=str(REC / K.ICONO_ICNS))

else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
              name=NOMBRE, console=False, icon=str(REC / K.ICONO_ICO))
