# -*- coding: utf-8 *-*
"""
    :Propósito: Constantes de PyOECF
    :Autor:     Tony Diana
    :Versión:   26.10.17
"""

# cSpell:ignore anni, annus, github, meipass, primus, ultimus
# cSpell:ignore Valencià, windll

__all__ = ["K"]

# --- Bibliotecas estándar Python
import locale
import os
import sys
from pathlib import Path

# --- Bibliotecas internas
from bib import std


#
# --- Código de idioma del sistema, si es uno de los conocidos; si no, el
#     de por defecto. Linux y macOS lo dicen en variables de entorno
#     (es_ES.UTF-8, o es:en en LANGUAGE); Windows, en su idioma de la
#     interfaz. Solo cuentan las dos primeras letras
def _idioma_sistema(variables: tuple[str, ...], conocidos: dict,
                    defecto: str) -> str:
    code = next((os.environ[v] for v in variables if os.environ.get(v)),
                "")
    if (not code) and sys.platform.startswith("win"):
        import ctypes
        _x = ctypes.windll.kernel32.GetUserDefaultUILanguage()  # type: ignore
        interfaz = _x

        code = locale.windows_locale.get(interfaz, "")

    if not code:
        code = locale.getlocale()[0] or ""

    code = code[:2].lower()
    return code if (code in conocidos) else defecto


#
# --- Constantes PyOECF
class K(std.EnumMutable):
    """ Constantes de PyOECF. """

    # --- Identidad del proyecto: nombre, usuario de GitHub, su
    #     repositorio y la web de ayuda (GitHub Pages). OJO: el
    #     repositorio también está en rec/scripts/remoto.conf (bash)
    NOMBRE = "PyOECF"
    """ Nombre del programa (ventana, archivos de resultados). """
    USUARIO_GITHUB = "TonyDiana"
    REPO_GITHUB = f"{USUARIO_GITHUB}/{NOMBRE}"
    """ Repositorio en GitHub: usuario/nombre. """
    URL_HELP = f"https://{USUARIO_GITHUB.lower()}.github.io/{NOMBRE}/"
    """ Web de ayuda (GitHub Pages). """

    # --- Autor y años del copyright: el primero y el de la última
    #     publicación. Al publicar en un año nuevo, cambiar annus_ultimus
    #     (no se toma del reloj: el año del copyright es el de publicación)
    AUTOR = "Tony Diana"
    ANNUS_PRIMUS = 2026
    ANNUS_ULTIMUS = 2026

    #
    @std.classproperty
    def derechos(cls) -> str:
        """
        «© 2026 Tony Diana», o «© 2026–2027 Tony Diana» si hay varios años.
        """
        anni = str(cls.ANNUS_PRIMUS)
        if cls.ANNUS_ULTIMUS != cls.ANNUS_PRIMUS:
            anni += f"–{cls.ANNUS_ULTIMUS}"
        return f"© {anni} {cls.AUTOR}"

    # --- Idiomas: código y nombre en su propio idioma. Cada texto
    #     traducible es un dict {código: texto}
    ES = "es"
    """ Código del español. """
    EN = "en"
    """ Código del inglés. """
    CA = "ca"
    """ Código del valenciano (ca_ES@valencia). """
    IDIOMAS = {ES: "Español", EN: "English", CA: "Valencià"}
    """ Idiomas de la app: {código: nombre en su propio idioma}. """

    # --- Idioma activo: al arrancar, el del sistema (inglés si PyOECF no
    #     lo conoce); cambia en marcha al elegir otro. Variables de
    #     entorno que lo indican, por orden de prioridad
    IDIOMA_DEFECTO = EN
    VARIABLES_IDIOMA = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")
    idioma = _idioma_sistema(VARIABLES_IDIOMA, IDIOMAS, IDIOMA_DEFECTO)
    """ Código del idioma activo (cambia al elegir otro en la lista). """

    #
    @classmethod
    def tr(cls, texto: dict) -> str:
        """ Devuelve el texto en el idioma activo. """
        return texto[cls.idioma]

    #
    # --- Textos con número: cada idioma lleva (singular, plural). En los
    #     tres idiomas, singular solo con 1
    @classmethod
    def tr_n(cls, texto: dict, n: int) -> str:
        """ Devuelve el texto en el idioma activo, en singular o plural. """
        singular, plural = texto[cls.idioma]
        return singular if (n == 1) else plural

    #
    # --- Versión: archivo en la raíz del proyecto (PyOECF.spec lo mete en
    #     el ejecutable leyendo este mismo nombre)
    ARCHIVO_VERSION = "VERSION"
    """ Archivo con la versión, en la raíz del proyecto. """

    #
    # --- Icono de la ventana, en la carpeta de recursos: uno para cada
    #     tema (PyOECF.spec lo mete en el ejecutable leyendo estos nombres).
    #     NO en el rec/ de la raíz: Remoto.sh lo quita de la rama de
    #     despliegue (solo ese; src/rec se despliega)
    CARPETA_RECURSOS = "src/rec"
    """ Carpeta de los recursos de la app, desde la raíz del proyecto. """
    ICONO_TEMA_CLARO = "logo_n.png"
    """ Icono de la ventana con tema claro: negro. """
    ICONO_TEMA_OSCURO = "logo_b.png"
    """ Icono de la ventana con tema oscuro: blanco. """
    ICONOS = (ICONO_TEMA_CLARO, ICONO_TEMA_OSCURO)

    # --- Icono del programa: el del .exe de Windows y el del .app de
    #     macOS (barra de tareas, Dock). Diana negra sobre gris 18 %, el
    #     de la carta de gris. El .ico va también en la ventana de Windows
    ICONO_ICO = "PyOECF.ico"
    """ Icono de Windows (.exe y ventana). """
    ICONO_ICNS = "PyOECF.icns"

    # --- El mismo icono en PNG, a su tamaño, para la cabecera de la ventana
    ICONO_PNG = "PyOECF.png"
    """ Icono de la cabecera de la ventana. """

    #
    @std.classproperty
    def version(cls) -> str:
        """ Versión del programa: la del archivo VERSION de la raíz. """
        ruta = cls.path / cls.ARCHIVO_VERSION
        return ruta.read_text(encoding="utf-8").strip()

    #
    # --- Atributo de sys donde PyInstaller deja la carpeta de sus datos.
    #     ÚNICO sitio que lo conoce: quien necesite una carpeta del
    #     programa, la pide a K.path
    ATRIBUTO_PYINSTALLER = "_MEIPASS"

    #
    @std.classproperty
    def path(cls) -> Path:
        """ Carpeta del proyecto. """

        # --- Empaquetado: PyInstaller copia los datos a su propia carpeta
        empaquetado = getattr(sys, cls.ATRIBUTO_PYINSTALLER, None)
        if empaquetado:
            return Path(empaquetado)

        # --- Desde el código: este archivo vive en <raíz>/src/kernel/
        return Path(__file__).resolve().parents[2]
