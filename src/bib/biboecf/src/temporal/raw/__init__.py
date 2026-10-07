# -*- coding: utf-8 *-*
"""
    :Propósito: Lectura de UN archivo RAW de la biblioteca BibOECF
    :Autor:     Tony Diana
    :Versión:   26.10.06
"""

# cSpell:ignore

__all__ = ["KC", "leer_cam",

           "KT", "es_tapada", "leer_exp", "texto_exp", "texto_f",
           "texto_iso"]

from .cam import KC, leer_cam
from .toma import (KT, es_tapada, leer_exp, texto_exp, texto_f,
                   texto_iso)
