# -*- coding: utf-8 *-*
"""
    :Propósito: Posición de cada toma de la serie respecto a la Z-V
                (tercioEV: tercios de paso enteros) y su zona: número y
                nombre
    :Autor:     Tony Diana
    :Versión:   26.10.09
"""

# cSpell:ignore

__all__ = ["KP", "exp_relativa", "calcular_tercioEV", "zona_tercio",
           "texto_zona"]

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

    # --- Nombres de las zonas como en el fotómetro: Z0, Z0.3, Z0.7,
    #     Z1… Las zonas 5 y 10 van en romanos (ZV, ZV.3, ZX)
    prefijo = "Z"
    romanos = {5: "V", 10: "X"}
    tercios_texto = ("", ".3", ".7")


# --- Exposición relativa de una toma: t · ISO / f²
def exp_relativa(segundos: float, diafragma: float, iso: float) -> float:
    return segundos * iso / diafragma ** 2


# --- tercioEV: tercios de paso enteros respecto a la referencia.
#     Positivo si la toma tiene MÁS exposición que la referencia
def calcular_tercioEV(exp: float, exp_ref: float) -> int:
    return round(KP.tercios * math.log2(exp / exp_ref))


# --- Zona entera (0 a 10) y tercio (0, 1 o 2) de un tercioEV: (5, 1)
#     es ZV.3. De aquí salen los nombres de pantalla y los de las copias
def zona_tercio(tercioEV: int) -> tuple[int, int]:
    return divmod(KP.zona_ref * KP.tercios + tercioEV, KP.tercios)


# --- Nombre de la zona de un tercioEV: ZV, ZV.3, Z9.7, ZX…
def texto_zona(tercioEV: int) -> str:
    entera, tercio = zona_tercio(tercioEV)
    return (f"{KP.prefijo}{KP.romanos.get(entera, entera)}"
            f"{KP.tercios_texto[tercio]}")
