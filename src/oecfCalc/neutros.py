# -*- coding: utf-8 *-*
"""
    :Propósito: Los Kelvin neutros: qué Kelvin poner en la cámara para que
                salga neutra con cada luz habitual (cálida, sol, flash y
                LED frío), a partir de los balances de blancos medidos, y
                su paso a datos de JSON. Es un cálculo propio del OECF, sin
                textos: lo usan el PDF y el JSON (y, en adelante, el libro)
    :Autor:     Tony Diana
    :Versión:   26.11.14
"""

# cSpell:ignore extrapola, mired, oecf

__all__ = ["KNE", "RangoNeutro", "rangos_neutros", "rangos_a_dict"]

# --- Bibliotecas estándar Python
from dataclasses import dataclass

# --- Bibliotecas internas
from bib import std
from bib.oecfMediadores import KRES
from .review import BalanceMedido


#
class KNE(std.EnumMutable):
    """ Constantes de los Kelvin neutros. """

    # --- Códigos de las luces habituales: los de KRES, que también lee FE.
    #     No llevan texto: quien los enseña (el PDF, el libro) los traduce
    #     con estos mismos nombres
    LUZ_CALIDA = KRES.LUZ_CALIDA
    LUZ_FLASH = KRES.LUZ_FLASH
    LUZ_LED_FRIO = KRES.LUZ_LED_FRIO
    LUZ_SOL = KRES.LUZ_SOL

    # --- Qué Kelvin poner en la cámara para que salga neutra con cada luz
    #     habitual (su código y su Kelvin, de menor a mayor: no en orden
    #     alfabético), con esta tolerancia en mired (MIRED entre los
    #     Kelvin). Los Kelvin de la cámara se redondean a REDONDEO_KELVIN, y
    #     hacen falta al menos PUNTOS_NEUTRAS balances con Kelvin anotado y
    #     medido. Si la luz queda fuera de lo medido, se estima prolongando
    #     la curva hasta EXTRAPOLA_MIRED mired más allá (y se marca como
    #     estimado); más lejos, sin datos. 5500 K es una referencia, no el
    #     Sol de mediodía; los LED de tienda son de 3200 o 6400 K (Tony,
    #     2026-11-13: «prefiero una estimación que una nada»)
    EXTRAPOLA_MIRED = 15
    LUCES_NEUTRAS = ((LUZ_CALIDA, 3200), (LUZ_SOL, 5000),
                     (LUZ_FLASH, 5500), (LUZ_LED_FRIO, 6400))
    MIRED = 1000000
    PUNTOS_NEUTRAS = 2
    REDONDEO_KELVIN = 10
    TOLERANCIA_MIRED = 5


#
# --- Una luz de KNE.LUCES_NEUTRAS: se crea siempre con los nombres de los
#     campos (kw_only)
@dataclass(frozen=True, slots=True, kw_only=True)
class RangoNeutro:
    """
    Los Kelvin neutros de una luz: su código (KNE.LUZ_*), su Kelvin, el
    Kelvin mínimo y máximo de la luz dentro de la tolerancia, el Kelvin
    mínimo y máximo que poner en la cámara (None si la luz queda fuera de
    lo medido) y si es una estimación
    """
    luz: str
    kelvin: int
    luzDesde: int
    luzHasta: int
    camDesde: int | None
    camHasta: int | None
    esEstimado: bool


#
def rangos_neutros(balances: list[BalanceMedido]) -> list[RangoNeutro]:
    """
    Por cada luz de KNE.LUCES_NEUTRAS, sus Kelvin neutros (ver
    RangoNeutro). Se invierte la curva de los balances (Kelvin anotado →
    medido) con una recta entre cada par de puntos, en mired; el medido que
    se busca es el de la luz. Fuera de lo medido se prolonga la recta de
    los dos últimos puntos, hasta KNE.EXTRAPOLA_MIRED mired (estimación);
    más lejos, los dos Kelvin de la cámara son None. Con menos de
    KNE.PUNTOS_NEUTRAS balances, ninguna luz.
    """
    puntos = sorted(
        (_mired(b.kelvin), _mired(b.kelvin_cam))
        for b in balances
        if (b.kelvin is not None) and (b.kelvin_cam is not None))
    if len(puntos) < KNE.PUNTOS_NEUTRAS:
        return []
    rangos = []
    for clave, kelvin in KNE.LUCES_NEUTRAS:
        centro = _mired(kelvin)
        bajo = centro - KNE.TOLERANCIA_MIRED
        alto = centro + KNE.TOLERANCIA_MIRED
        luz = (_kelvin_redondo(alto), _kelvin_redondo(bajo))
        fuera = max(puntos[0][0] - bajo, alto - puntos[-1][0], 0)
        if fuera > KNE.EXTRAPOLA_MIRED:
            rangos.append(RangoNeutro(
                luz=clave, kelvin=kelvin, luzDesde=luz[0], luzHasta=luz[1],
                camDesde=None, camHasta=None, esEstimado=False))
            continue
        en_cam = (_interpolar(puntos, bajo), _interpolar(puntos, alto))
        rangos.append(RangoNeutro(
            luz=clave, kelvin=kelvin, luzDesde=luz[0], luzHasta=luz[1],
            camDesde=_kelvin_redondo(max(en_cam)),
            camHasta=_kelvin_redondo(min(en_cam)), esEstimado=fuera > 0))
    return rangos


#
def rangos_a_dict(rangos: list[RangoNeutro]) -> list[dict]:
    """
    Los Kelvin neutros como datos de JSON (resultados.kelvinNeutros, con
    las claves de KRES): una entrada por luz, sin textos
    """
    return [{KRES.N_LUZ: r.luz, KRES.N_KELVIN: r.kelvin,
             KRES.N_LUZ_DESDE: r.luzDesde, KRES.N_LUZ_HASTA: r.luzHasta,
             KRES.N_CAM_DESDE: r.camDesde, KRES.N_CAM_HASTA: r.camHasta,
             KRES.N_ES_ESTIMADO: r.esEstimado}
            for r in rangos]


#
def _mired(kelvin: float) -> float:
    """ Mired de una temperatura de color: KNE.MIRED entre los Kelvin
        (a más Kelvin, menos mired). """
    return KNE.MIRED / kelvin


#
def _kelvin_redondo(mired: float) -> int:
    """ Kelvin de un mired, redondeado a KNE.REDONDEO_KELVIN. """
    return int(round((KNE.MIRED / mired) / KNE.REDONDEO_KELVIN)
               * KNE.REDONDEO_KELVIN)


#
def _interpolar(puntos: list[tuple[float, float]], x: float) -> float:
    """
    y de una x, con una recta entre cada par de puntos (x, y) ordenados
    por x. Fuera de ellos, se prolonga la recta de los dos primeros o de
    los dos últimos. Si dos puntos tienen la misma x, vale la y del
    primero.
    """
    pares = list(zip(puntos, puntos[1:]))
    if x < puntos[0][0]:
        pares = pares[:1]
    elif x > puntos[-1][0]:
        pares = pares[-1:]
    for (x0, y0), (x1, y1) in pares:
        if (x0 <= x <= x1) or (x < puntos[0][0]) or (x > puntos[-1][0]):
            if x1 == x0:
                return y0
            return y0 + ((y1 - y0) * ((x - x0) / (x1 - x0)))
    return puntos[-1][1]
