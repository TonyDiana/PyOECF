# -*- coding: utf-8 *-*
"""
    :Propósito: Posición de cada toma de la serie respecto a la Z-V
                (tercioEV: tercios de paso enteros) y su zona: número y
                nombre
    :Autor:     Tony Diana
    :Versión:   26.10.18
"""

# cSpell:ignore

__all__ = ["KP", "exp_relativa", "calcular_tercio_exacto", "zona_tercio",
           "texto_zona"]

# --- Bibliotecas estándar Python
import math

# --- Bibliotecas internas
from bib import std


#
# --- Constantes de la posición
class KP(std.EnumMutable):
    """ Constantes de la posición de cada toma. """

    TERCIOS = 3
    """Tercios por zona."""

    ZONA_REF = 5
    """Zona de la referencia (Z-V)."""

    DEV_MAX = 0.33
    """Desvío máximo, en tercios, entre la posición exacta de una toma y su
    tercio entero. Lo normal es el redondeo de los tiempos que rotula la
    cámara (0,20 en la R7); más, se avisa."""

    PREFIJO = "Z"
    """Nombres de las zonas como en el fotómetro: Z0, Z0.3, Z0.7, Z1…
    Las zonas 5 y 10 van en romanos (ZV, ZV.3, ZX)."""

    ROMANOS = {ZONA_REF: "V", 10: "X"}
    """Diccionario para representar las zonas 5 (V) y 10 (X) en números
    romanos."""

    TERCIOS_TEXTO = ("", ".3", ".7")
    """Sufijos de texto para los tercios de zona."""


#
def exp_relativa(segundos: float, diafragma: float, iso: float) -> float:
    """Exposición relativa de una toma: t · ISO / f²."""
    return (segundos * iso) / (diafragma ** 2)


#
def calcular_tercio_exacto(exp: float, exp_ref: float) -> float:
    """Posición exacta de una toma, en tercios de paso (con decimales)
    respecto a la referencia. Positiva si tiene MÁS exposición."""
    return KP.TERCIOS * math.log2(exp / exp_ref)


#
def zona_tercio(tercioEV: int) -> tuple[int, int]:
    """Zona entera (0 a 10) y tercio (0, 1 o 2) de un tercioEV: (5, 1) es
    ZV.3. De aquí salen los nombres de pantalla y los de las copias."""
    return divmod((KP.ZONA_REF * KP.TERCIOS) + tercioEV, KP.TERCIOS)


#
def texto_zona(tercioEV: int) -> str:
    """Nombre de la zona de un tercioEV: ZV, ZV.3, Z9.7, ZX…"""
    entera, tercio = zona_tercio(tercioEV)
    return (f"{KP.PREFIJO}{KP.ROMANOS.get(entera, entera)}"
            f"{KP.TERCIOS_TEXTO[tercio]}")
