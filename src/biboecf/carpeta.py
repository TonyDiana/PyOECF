# -*- coding: utf-8 *-*
"""
    :Propósito: Problemas de la carpeta de una serie: códigos, sin textos
                (cada interfaz los traduce)
    :Autor:     Tony Diana
    :Versión:   26.10.18
"""

# cSpell:ignore oecf

__all__ = ["KCA", "problema_carpeta"]

# --- Bibliotecas internas
from bib import std
from .kernel import OECF


#
class KCA(std.EnumMutable):
    """ Problemas de la carpeta, en el orden en que se comprueban. """

    SIN_CARPETA = "SIN_CARPETA"
    """La carpeta no existe."""

    SIN_PERMISO_LEER = "SIN_PERMISO_LEER"
    """Sin permiso para leer la carpeta."""

    SIN_RAW = "SIN_RAW"
    """La carpeta no tiene RAW."""

    SIN_PERMISO_ESCRIBIR = "SIN_PERMISO_ESCRIBIR"
    """Sin permiso para escribir en la carpeta (para la carpeta OECF, donde van
    los resultados)."""


#
def problema_carpeta(oecf: OECF) -> str | None:
    """
    Problema de la carpeta de una serie (KCA), o None si sirve: debe
    existir, poder leerse, tener RAW y poder escribirse (para la carpeta
    OECF, donde van los resultados).
    """
    if not oecf.esCarpeta:
        return KCA.SIN_CARPETA
    if not oecf.puedeLeer:
        return KCA.SIN_PERMISO_LEER
    if not oecf.raws:
        return KCA.SIN_RAW
    if not oecf.puedeEscribir:
        return KCA.SIN_PERMISO_ESCRIBIR
    return None
