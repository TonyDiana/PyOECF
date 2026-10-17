# -*- coding: utf-8 *-*
"""
    :Propósito: Curva de transferencia del ruido de una serie: de qué está
                hecho el ruido de la tarjeta en cada zona (lectura,
                fotones y una parte proporcional a la señal), ajustado
                con las zonas medidas; y lo que da el modelo: la
                señal/ruido de una señal y la señal de una señal/ruido
    :Autor:     Tony Diana
    :Versión:   26.10.14
"""

# cSpell:ignore analisis, biboecf

__all__ = ["KTR", "Transferencia", "ajustar_transferencia", "snr_modelo",
           "senal_para_snr", "escala_mpx"]

# --- Bibliotecas estándar Python
import math
from collections.abc import Sequence
from typing import TYPE_CHECKING, NamedTuple

# --- Bibliotecas externas
import numpy as np

# --- Bibliotecas internas
from bib import clases
from .teselas import KTE

if TYPE_CHECKING:
    from .analisis import ZonaMedida


#
class KTR(clases.EnumMutable):
    """ Constantes de la curva de transferencia. """

    # --- Modelo: ruido² = lectura² + señal / ganancia + (proporcional ×
    #     señal)², en niveles del RAW (sobre el negro). Lectura: el de la
    #     electrónica; ganancia: electrones por nivel (los fotones dan un
    #     ruido de raíz de los electrones); proporcional: lo que crece con
    #     la señal (luz que varía dentro de la tesela, diferencias entre
    #     píxeles…)
    #
    # --- Zonas que entran: con señal, sin ningún píxel recortado en el
    #     paño (más de MAX_RECORTADO) y por debajo del umbral de recorte
    #     de la tarjeta (KTE.UMBRAL_RECORTE del máximo de su canal). Con
    #     menos de MIN_ZONAS, no hay curva
    MAX_RECORTADO = 0.001
    MIN_ZONAS = 6

    # --- Píxeles por megapíxel (para normalizar la señal/ruido a un
    #     tamaño de referencia)
    PIXELES_MPX = 1e6


#
# --- La curva de un canal
class Transferencia(NamedTuple):
    """
    Curva de transferencia de un canal: ruido de lectura (niveles; NaN si
    la serie no lo distingue de 0), ganancia (electrones por nivel) y
    parte proporcional (fracción de la señal).
    """
    lectura: float
    ganancia: float
    proporcional: float


#
def ajustar_transferencia(zonas: Sequence["ZonaMedida | None"]
                          ) -> dict[str, Transferencia]:
    """
    Curva de transferencia de cada canal ({canal: Transferencia}), con
    las zonas de la serie (las 31; None si falta): mínimos cuadrados de
    ruido² frente a la señal, con peso relativo (cada zona cuenta igual,
    sea su ruido grande o pequeño). Los canales sin zonas bastantes o
    con un ajuste sin sentido (ganancia no positiva) no salen.
    """
    medidas = [z for z in zonas if z is not None]
    if not medidas:
        return {}
    curvas = {}
    for canal in medidas[0].nivel:
        maximo = max(z.nivel[canal] for z in medidas)
        senal, ruido2 = [], []
        for z in medidas:
            nivel, dispersion = z.nivel[canal], z.dispersion[canal]
            if (nivel > 0 and 0 < dispersion < math.inf
                    and z.pano_recortado.get(canal, 0.0)
                    <= KTR.MAX_RECORTADO
                    and nivel < KTE.UMBRAL_RECORTE * maximo):
                senal.append(nivel)
                ruido2.append((dispersion * nivel) ** 2)
        if len(senal) < KTR.MIN_ZONAS:
            continue
        s, v = np.array(senal), np.array(ruido2)
        peso = 1 / v
        matriz = np.column_stack((np.ones_like(s), s, s ** 2))
        lectura2, inversa, proporcional2 = np.linalg.lstsq(
            matriz * peso[:, None], v * peso, rcond=None)[0]
        if inversa <= 0:
            continue
        curvas[canal] = Transferencia(
            math.sqrt(lectura2) if lectura2 > 0 else math.nan,
            float(1 / inversa),
            math.sqrt(proporcional2) if proporcional2 > 0 else 0.0)
    return curvas


#
def escala_mpx(alto: int, ancho: int, referencia: float) -> float:
    """
    Cuánto se multiplica la señal/ruido de un píxel para llevarla a un
    sensor de referencia megapíxeles (la raíz del cociente de píxeles:
    al juntar píxeles, el ruido se promedia).
    """
    return math.sqrt(alto * ancho / (referencia * KTR.PIXELES_MPX))


#
def snr_modelo(curva: Transferencia, senal: float) -> float:
    """ Señal/ruido de un píxel con esta señal (niveles), según la curva. """
    lectura = 0.0 if math.isnan(curva.lectura) else curva.lectura
    return senal / math.sqrt(lectura ** 2 + senal / curva.ganancia
                             + (curva.proporcional * senal) ** 2)


#
def senal_para_snr(curva: Transferencia, snr: float) -> float | None:
    """
    Señal (niveles) a la que un píxel llega a esta señal/ruido, según la
    curva: la raíz positiva de (1 − snr²·p²)·S² − (snr²/g)·S − snr²·l² =
    0. None si no se llega nunca (la parte proporcional la frena antes).
    """
    lectura = 0.0 if math.isnan(curva.lectura) else curva.lectura
    t2 = snr ** 2
    a = 1 - t2 * curva.proporcional ** 2
    if a <= 0:
        return None
    b = t2 / curva.ganancia
    c = t2 * lectura ** 2
    return (b + math.sqrt(b ** 2 + 4 * a * c)) / (2 * a)
