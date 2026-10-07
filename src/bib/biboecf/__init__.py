# -*- coding: utf-8 *-*
"""
    :Propósito:
        Este ``__init__`` hará las veces de un **MNS** (*Module Name Server*)
        que permite invocar cualquier elemento de la biblioteca **BibOECF**
        con un simple:

        ``from bib import biboecf``

    :Autor:     Tony Diana
    :Versión:   26.10.06
"""

# cSpell:ignore biboecf

__all__ = ["KC", "leer_cam",
           "KT", "es_tapada", "leer_exp", "texto_exp", "texto_f", "texto_iso",
           "KS", "Secuencia", "balance_personalizado", "buscar_raw",
           "secuencia",
           "KP", "calcular_k", "exp_relativa", "texto_zona", "zona"]

#
# --- raw (temporal)
#
from .src.temporal.raw import KC, leer_cam
from .src.temporal.raw import (KT, es_tapada, leer_exp, texto_exp, texto_f,
                               texto_iso)

#
# --- serie (temporal)
#
from .src.temporal.serie import (KS, Secuencia, balance_personalizado,
                                 buscar_raw, secuencia)
from .src.temporal.serie import KP, calcular_k, exp_relativa, texto_zona, zona
