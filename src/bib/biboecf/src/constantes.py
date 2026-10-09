# -*- coding: utf-8 *-*
"""
    :Propósito: Constantes compartidas de la biblioteca BibOECF. Las que
                solo usa un módulo van en el suyo
    :Autor:     Tony Diana
    :Versión:   26.10.07
"""

# cSpell:ignore biboecf, rawpy

__all__ = ["COM"]

# --- Bibliotecas internas
from bib import std


#
# --- Constantes comunes
class COM(std.EnumMutable):
    """ Constantes comunes de BibOECF. """

    # --- Extensiones RAW (en minúsculas). Comprobadas con archivos reales:
    #     ARW, CR2, CR3 y RAF. NEF (Nikon), sin comprobar todavía
    extensiones = (".arw", ".cr2", ".cr3", ".nef", ".raf")

    # --- Margen al comparar tiempos: rawpy los da con poca precisión
    margenTV = 0.01
