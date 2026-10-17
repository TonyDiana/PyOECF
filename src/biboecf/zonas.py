# -*- coding: utf-8 *-*
"""
    :Propósito: Posición de cada toma de la serie respecto a la Z-V
                (tercioEV: tercios de paso enteros) y su zona: número y
                nombre
    :Autor:     Tony Diana
    :Versión:   26.10.09
"""

# cSpell:ignore

__all__ = ["KP", "exp_relativa", "calcular_tercio_exacto", "zona_tercio",
           "texto_zona"]

# --- Bibliotecas estándar Python
import math

# --- Bibliotecas internas
from bib import clases


#
# --- Constantes de la posición
class KP(clases.EnumMutable):
    """ Constantes de la posición de cada toma. """

    # --- Tercios por zona y zona de la referencia (Z-V)
    TERCIOS = 3
    ZONA_REF = 5

    # --- Desvío máximo, en tercios, entre la posición exacta de una toma
    #     y su tercio entero. Lo normal es el redondeo de los tiempos que
    #     rotula la cámara (0,20 en la R7); más, se avisa
    DESVIO_MAXIMO = 0.33

    # --- Tolerancia de linealidad, en zonas: un punto es lineal si se
    #     aparta menos de lo esperado; una Z-V de control que se aparta
    #     más de la ZV dice que la luz cambió (el libro la usa también: su
    #     constante ToleranciaLineal)
    TOLERANCIA_LINEAL = 0.1

    # --- Nombres de las zonas como en el fotómetro: Z0, Z0.3, Z0.7,
    #     Z1… Las zonas 5 y 10 van en romanos (ZV, ZV.3, ZX)
    PREFIJO = "Z"
    ROMANOS = {5: "V", 10: "X"}
    TERCIOS_TEXTO = ("", ".3", ".7")


# --- Exposición relativa de una toma: t · ISO / f²
def exp_relativa(segundos: float, diafragma: float, iso: float) -> float:
    return segundos * iso / diafragma ** 2


# --- Posición exacta de una toma, en tercios de paso (con decimales)
#     respecto a la referencia. Positiva si tiene MÁS exposición
def calcular_tercio_exacto(exp: float, exp_ref: float) -> float:
    return KP.TERCIOS * math.log2(exp / exp_ref)


# --- Zona entera (0 a 10) y tercio (0, 1 o 2) de un tercioEV: (5, 1)
#     es ZV.3. De aquí salen los nombres de pantalla y los de las copias
def zona_tercio(tercioEV: int) -> tuple[int, int]:
    return divmod(KP.ZONA_REF * KP.TERCIOS + tercioEV, KP.TERCIOS)


# --- Nombre de la zona de un tercioEV: ZV, ZV.3, Z9.7, ZX…
def texto_zona(tercioEV: int) -> str:
    entera, tercio = zona_tercio(tercioEV)
    return (f"{KP.PREFIJO}{KP.ROMANOS.get(entera, entera)}"
            f"{KP.TERCIOS_TEXTO[tercio]}")
