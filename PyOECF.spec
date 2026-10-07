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

# --- Literales mágicos
NOMBRE = K.nombre
PUNTO_ENTRADA = SRC / "main.py"
ES_MAC = sys.platform == "darwin"

# --- Datos que no son código y deben ir dentro:
#     - el archivo de versión (K.archivo_version)
#     - los iconos de la ventana (K.iconos), en su carpeta de recursos
#     - temas de customtkinter: sin ellos la ventana falla al abrir
DATOS = [(str(RAIZ / K.archivo_version), ".")]
DATOS += [(str(RAIZ / K.carpeta_recursos / icono), K.carpeta_recursos)
          for icono in K.iconos]
DATOS += collect_data_files("customtkinter")

a = Analysis([str(PUNTO_ENTRADA)], datas=DATOS)
pyz = PYZ(a.pure)

if ES_MAC:
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True,
              name=NOMBRE, console=False)
    coll = COLLECT(exe, a.binaries, a.datas, name=NOMBRE)
    app = BUNDLE(coll, name=f"{NOMBRE}.app")

else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
              name=NOMBRE, console=False)
