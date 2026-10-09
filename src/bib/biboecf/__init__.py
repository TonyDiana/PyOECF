# -*- coding: utf-8 *-*
"""
    :Propósito:
        Este ``__init__`` hará las veces de un **MNS** (*Module Name Server*)
        que permite invocar cualquier elemento de la biblioteca **BibOECF**
        con un simple:

        ``from bib import biboecf``

    :Autor:     Tony Diana
    :Versión:   26.10.07
"""

# cSpell:ignore biboecf

__all__ = ["Cam", "Exp", "KS", "OECF", "Secuencia", "texto_zona", "Toma",
           "zona_tercio"]

#
# --- OECF: la serie de tomas de una carpeta, con lo que se lee de ella
#
from .src.cam import Cam
from .src.kernel import Exp, OECF, Toma

#
# --- Protocolo y partes de la serie, y nombres de las zonas
#
from .src.secuencia import KS, Secuencia
from .src.zonas import texto_zona, zona_tercio
