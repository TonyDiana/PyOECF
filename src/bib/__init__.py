# -*- coding: utf-8 *-*
"""
    :Propósito:

        **MNS** (*Module Name Server*) de las bibliotecas externas.
        Permite invocar cualquier elemento de la biblioteca con un simple:

        ``from bib import <<módulo>>``

    :Autor:     Tony Diana
    :Versión:   26.10.05
"""

# cSpell:ignore aquila, biboecf

__all__ = ["biboecf", "std"]

from . import std
from . import biboecf
