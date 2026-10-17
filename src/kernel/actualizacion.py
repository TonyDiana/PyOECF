# -*- coding: utf-8 *-*
"""
    :Propósito: Comprueba si hay una versión de PyOECF más nueva que la
                instalada: lee el archivo VERSION publicado en GitHub.
                Solo con la biblioteca estándar, sin dependencias
    :Autor:     Tony Diana
    :Versión:   26.10.10
"""

# cSpell:ignore github, numeros

__all__ = ["KA", "es_mas_nueva", "version_publicada"]

# --- Bibliotecas estándar Python
import re
import urllib.request

# --- Bibliotecas internas
from bib import clases
from .constantes import K


#
# --- Constantes de la actualización
class KA(clases.EnumMutable):
    """ Constantes de la comprobación de versión. """

    # --- Repositorio público (el de K) y rama publicada. OJO:
    #     rama_publicada es el mismo valor que RAMA_DESTINO en
    #     rec/scripts/remoto.conf
    REPO = K.REPO_GITHUB
    RAMA_PUBLICADA = "deploy"

    # --- El VERSION publicado y la página de descargas
    URL_VERSION = (f"https://raw.githubusercontent.com/{REPO}/"
                   f"{RAMA_PUBLICADA}/{K.ARCHIVO_VERSION}")
    URL_RELEASES = f"https://github.com/{REPO}/releases"

    # --- Segundos como mucho para la respuesta de GitHub
    ESPERA = 3

    # --- Partes de una versión: sus números y la letra de revisión del
    #     final, si la hay. 0.4 → (0, 4) y «»; 26.10b → (26, 10) y «b».
    #     Sin letra va antes que con letra: 0.4 < 0.4a < 0.4b < 0.5
    PATRON_NUMEROS = r"\d+"
    PATRON_LETRA = r"[a-z]*$"


#
def version_publicada() -> str | None:
    """
    Versión publicada en GitHub, o None si no se puede saber (sin
    internet, GitHub no responde…). Puede tardar hasta KA.ESPERA
    segundos: llamarla fuera de la ventana (en un hilo).
    """
    try:
        with urllib.request.urlopen(KA.URL_VERSION,
                                    timeout=KA.ESPERA) as respuesta:
            return respuesta.read().decode("utf-8").strip() or None
    except (OSError, ValueError):
        return None


#
def es_mas_nueva(publicada: str, instalada: str) -> bool:
    """
    Saber si la versión publicada es más nueva que la instalada,
    comparando sus números (0.10 es más nueva que 0.9) y, si son
    iguales, su letra de revisión (0.4a es más nueva que 0.4).
    """
    def _partes(version: str) -> tuple[tuple[int, ...], str]:
        numeros = tuple(int(n)
                        for n in re.findall(KA.PATRON_NUMEROS, version))
        letra = re.search(KA.PATRON_LETRA, version.lower())
        return numeros, letra.group(0) if letra else ""
    return _partes(publicada) > _partes(instalada)
