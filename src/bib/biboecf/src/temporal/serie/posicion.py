# -*- coding: utf-8 *-*
"""
    :Propósito: Posición de cada toma de la serie respecto a la referencia:
                k (tercios enteros) y zona
    :Autor:     Tony Diana
    :Versión:   26.10.06
"""

# cSpell:ignore

__all__ = ["KP", "calcular_k", "exp_relativa", "texto_zona", "zona"]

# --- Bibliotecas estándar Python
import math

# --- Bibliotecas internas
from bib import std


#
# --- Constantes de la posición
class KP(std.EnumMutable):
    """ Constantes de la posición de cada toma. """

    # --- Tercios por zona y zona de la referencia (Z-V)
    tercios = 3
    zona_ref = 5

    # --- Nombres de las zonas como en la plantilla PSD: Z0, Z0 1/3,
    #     Z0 2/3, Z1… Las zonas 5 y 10 van en romanos (ZV, ZX)
    prefijo = "Z"
    romanos = {5: "V", 10: "X"}
    fracciones = {1: "1/3", 2: "2/3"}


# --- Exposición relativa de una toma: t · ISO / f²
def exp_relativa(segundos: float, diafragma: float, iso: float) -> float:
    return segundos * iso / diafragma ** 2


# --- k: tercios enteros respecto a la referencia. Positivo si la toma
#     tiene MÁS exposición que la referencia
def calcular_k(exp: float, exp_ref: float) -> int:
    return round(KP.tercios * math.log2(exp / exp_ref))


# --- Zona de una toma: 5 + k/3 (la referencia es la zona 5)
def zona(k: int) -> float:
    return KP.zona_ref + k / KP.tercios


# --- Nombre de la zona de k: ZV, Z5 1/3, ZX…
def texto_zona(k: int) -> str:
    entera, tercio = divmod(KP.zona_ref * KP.tercios + k, KP.tercios)
    nombre = f"{KP.prefijo}{KP.romanos.get(entera, entera)}"
    if tercio:
        nombre = f"{nombre} {KP.fracciones[tercio]}"
    return nombre
