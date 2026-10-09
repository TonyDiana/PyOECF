# -*- coding: utf-8 *-*
"""
    :Propósito: Constantes de PyOECF
    :Autor:     Tony Diana
    :Versión:   26.10.05
"""

# cSpell:ignore anni, annus, meipass, primus, ultimus

__all__ = ["K"]

# --- Bibliotecas estándar Python
import locale
import os
import sys
from pathlib import Path

# --- Bibliotecas internas
from bib import std


# --- Código de idioma del sistema, si es uno de los conocidos; si no, el
#     de por defecto. Linux y macOS lo dicen en variables de entorno
#     (es_ES.UTF-8, o es:en en LANGUAGE); Windows, en su idioma de la
#     interfaz. Solo cuentan las dos primeras letras
def _idioma_sistema(variables: tuple[str, ...], conocidos: dict,
                    defecto: str) -> str:
    codigo = next((os.environ[v] for v in variables if os.environ.get(v)),
                  "")
    if not codigo and sys.platform.startswith("win"):
        import ctypes
        interfaz = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        codigo = locale.windows_locale.get(interfaz, "")
    if not codigo:
        codigo = locale.getlocale()[0] or ""

    codigo = codigo[:2].lower()
    return codigo if codigo in conocidos else defecto


#
# --- Constantes PyOECF
class K(std.EnumMutable):
    """ Constantes de PyOECF. """

    # --- Identidad del proyecto
    nombre = "PyOECF"
    url_help = "https://tonydiana.github.io/PyOECF/"

    # --- Autor y años del copyright: el primero y el de la última
    #     publicación. Al publicar en un año nuevo, cambiar annus_ultimus
    #     (no se toma del reloj: el año del copyright es el de publicación)
    autor = "Tony Diana"
    annus_primus = 2026
    annus_ultimus = 2026

    # --- «© 2026 Tony Diana», o «© 2026–2027 Tony Diana» si hay varios
    #     años
    @std.classproperty
    def derechos(cls) -> str:
        anni = str(cls.annus_primus)
        if cls.annus_ultimus != cls.annus_primus:
            anni += f"–{cls.annus_ultimus}"
        return f"© {anni} {cls.autor}"

    # --- Idiomas: código y nombre en su propio idioma. Cada texto
    #     traducible es un dict {código: texto}
    es = "es"
    en = "en"
    ca = "ca"                   # --- Valenciano (ca_ES@valencia)
    idiomas = {es: "Español", en: "English", ca: "Valencià"}

    # --- Idioma activo: al arrancar, el del sistema (inglés si PyOECF no
    #     lo conoce); cambia en marcha al elegir otro. Variables de
    #     entorno que lo indican, por orden de prioridad
    idioma_defecto = en
    variables_idioma = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")
    idioma = _idioma_sistema(variables_idioma, idiomas, idioma_defecto)

    @classmethod
    def tr(cls, texto: dict) -> str:
        """ Devuelve el texto en el idioma activo. """
        return texto[cls.idioma]

    # --- Textos con número: cada idioma lleva (singular, plural). En los
    #     tres idiomas, singular solo con 1
    @classmethod
    def tr_n(cls, texto: dict, n: int) -> str:
        """ Devuelve el texto en el idioma activo, en singular o plural. """
        singular, plural = texto[cls.idioma]
        return singular if n == 1 else plural

    #
    # --- Versión: archivo en la raíz del proyecto (PyOECF.spec lo mete en
    #     el ejecutable leyendo este mismo nombre)
    archivo_version = "VERSION"

    #
    # --- Icono de la ventana, en la carpeta de recursos: uno para cada
    #     tema (PyOECF.spec lo mete en el ejecutable leyendo estos nombres).
    #     NO en el rec/ de la raíz: Remoto.sh lo quita de la rama de
    #     despliegue (solo ese; src/rec se despliega)
    carpeta_recursos = "src/rec"
    icono_tema_claro = "logo_n.png"         # --- Negro, sobre fondo claro
    icono_tema_oscuro = "logo_b.png"        # --- Blanco, sobre fondo oscuro
    iconos = (icono_tema_claro, icono_tema_oscuro)

    # --- Icono del programa: el del .exe de Windows y el del .app de
    #     macOS (barra de tareas, Dock). Diana negra sobre gris 18 %, el
    #     de la carta de gris. El .ico va también en la ventana de Windows
    icono_ico = "PyOECF.ico"
    icono_icns = "PyOECF.icns"

    # --- El mismo icono en PNG, a su tamaño, para la cabecera de la ventana
    icono_png = "PyOECF.png"

    @std.classproperty
    def version(cls) -> str:
        ruta = cls.path / cls.archivo_version
        return ruta.read_text(encoding="utf-8").strip()

    #
    # --- Atributo de sys donde PyInstaller deja la carpeta de sus datos.
    #     ÚNICO sitio que lo conoce: quien necesite una carpeta del
    #     programa, la pide a K.path
    atributo_pyinstaller = "_MEIPASS"

    # --- Carpeta del proyecto
    @std.classproperty
    def path(cls) -> Path:

        # --- Empaquetado: PyInstaller copia los datos a su propia carpeta
        empaquetado = getattr(sys, cls.atributo_pyinstaller, None)
        if empaquetado:
            return Path(empaquetado)

        # --- Desde el código: este archivo vive en <raíz>/src/kernel/
        return Path(__file__).resolve().parents[2]
