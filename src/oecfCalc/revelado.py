# -*- coding: utf-8 *-*
"""
    :Propósito: Segunda parte del análisis: el L* de la tarjeta en las
                exportaciones del revelador (TIFF), en las mismas teselas
                buenas que se eligieron en los RAW (las del análisis). El
                color de las TIFF (perfil, espacio y bits) se lee en leer
    :Autor:     Tony Diana
    :Versión:   26.10.26
"""

# cSpell:ignore iinfo, imagecodecs, imread, kcom, kicc, Lightroom, lstar, oecf
# cSpell:ignore recolocadas, tifffile

__all__ = ["KRV", "MedidaTiff", "lstar_tiff", "contraste_tela", "medir_tiff"]

# --- Bibliotecas estándar Python
from pathlib import Path
from typing import NamedTuple

# --- Bibliotecas externas
import numpy as np
import tifffile

# --- Bibliotecas internas
from bib import std
from bib.oecfMediadores import KFR
from kernel import COM as KCOM
from leer import KICC, bits_tiff, espacio_tiff, lineal
from .review import Review
from .teselas import KTE, Ventana, bloque_pantalla


#
class KRV(std.EnumMutable):
    """ Constantes de la medida de las exportaciones del revelador. """

    # --- Holgura dentro de cada tesela, en píxeles por lado: el revelador
    #     puede corregir la distorsión del objetivo y mover algo la imagen
    HOLGURA = 4

    # --- Recorte máximo del revelador, en fracción del sensor (ancho y
    #     alto): más, y la exportación no es a tamaño completo (reducida o
    #     recortada): sus teselas caerían en otro sitio. Lightroom, en la
    #     R7, recorta un 0,3 % de ancho y un 0,4 % de alto
    RECORTE_MAX = 0.02

    # --- Por qué no se pudo medir una exportación. Compresión: una que
    #     tifffile no abre sin otra biblioteca (LZW…: imagecodecs)
    ESPACIO_DESCONOCIDO = "ESPACIO_DESCONOCIDO"
    MEDIDA_DISTINTA = "MEDIDA_DISTINTA"
    SIN_TESELAS = "SIN_TESELAS"
    COMPRIMIDA = "COMPRIMIDA"

    # --- Bits de las exportaciones definitivas (en
    #     bib/oecfMediadores/common.py: los usa también FE)
    BITS_DEFINITIVOS = KFR.BITS_DEFINITIVOS

    # --- Contraste de la trama del paño (ver contraste_tela): se mide en
    #     el centro del rectángulo del paño, sin esta fracción de su ancho
    #     y de su alto por cada lado (sin dobladillo ni bordes), entre el
    #     percentil oscuro y el claro de sus bloques (Tony, 2026-11-13)
    MARGEN_TELA = 0.2
    PERCENTIL_OSCURO = 5
    PERCENTIL_CLARO = 95


#
# --- Lo medido en una exportación del revelador: su L* (None si no se
#     pudo medir) o por qué no (KRV; None si se midió), sus bits por
#     canal (None si no se pudo leer), su espacio de color (una clave de
#     KICC.ESPACIOS; None si no se reconoce) y el contraste de la trama
#     del paño en L* (None sin paño o si no se pudo medir). Un tipo por
#     campo: el JSON lo lee un programa
class MedidaTiff(NamedTuple):
    """ Medida de una exportación del revelador: L* o motivo, bits,
    espacio y contraste del paño. """
    lstar: float | None
    motivo: str | None
    bits: int | None
    espacio: str | None
    contraste: float | None = None


#
# --- De luminancia (luz lineal, de 0 a 1) a L* de CIELAB, en un número o
#     en una matriz
def _a_lstar(y: np.ndarray) -> np.ndarray:
    return np.where(y > KCOM.LAB_UMBRAL,
                    (KCOM.LAB_ESCALA * np.cbrt(y)) - KCOM.LAB_DESPLAZA,
                    KCOM.LAB_PENDIENTE * y)


#
# --- La exportación leída y su espacio de color (de KICC.ESPACIOS), o por
#     qué no se puede medir (KRV): espacio desconocido, compresión que
#     tifffile no abre o tamaño distinto del sensor (más recorte que
#     KRV.RECORTE_MAX)
def _leer_tiff(review: Review, ruta: Path) -> tuple[np.ndarray, tuple] | str:
    espacio = KICC.ESPACIOS.get(espacio_tiff(ruta) or "")
    if espacio is None:
        return KRV.ESPACIO_DESCONOCIDO
    try:
        imagen = tifffile.imread(ruta)
    except ValueError:
        return KRV.COMPRIMIDA
    alto, ancho = imagen.shape[:2]
    if not ((0 <= (review.alto - alto) <= (KRV.RECORTE_MAX * review.alto))
            and (0 <= (review.ancho - ancho)
            <= (KRV.RECORTE_MAX * review.ancho))):
        return KRV.MEDIDA_DISTINTA
    return imagen, espacio


#
# --- L* de la tarjeta en una exportación ya leída (ver lstar_tiff)
def _lstar(review: Review, imagen: np.ndarray, espacio: tuple) -> float | str:
    alto, ancho = imagen.shape[:2]
    tope = float(np.iinfo(imagen.dtype).max)

    # --- Mediana de cada tesela buena, dentro de la imagen recortada
    lado, holgura = review.lado, KRV.HOLGURA
    dy, dx = (review.alto - alto) // 2, (review.ancho - ancho) // 2
    medianas = []
    for f, c in zip(*np.nonzero(review.motivos == KTE.BUENA)):
        y0, x0 = (f * lado) - dy + holgura, (c * lado) - dx + holgura
        y1, x1 = y0 + lado - (2 * holgura), x0 + lado - (2 * holgura)
        if (y0 >= 0) and (x0 >= 0) and (y1 <= alto) and (x1 <= ancho):
            medianas.append(np.median(
                imagen[y0:y1, x0:x1].reshape(-1, imagen.shape[2]), axis=0))
    if not medianas:
        return KRV.SIN_TESELAS
    rgb = np.median(np.array(medianas), axis=0)[:3] / tope

    # --- A luz lineal, luminancia y L*
    y = float(np.dot(espacio[1], lineal(rgb, espacio)))
    return float(_a_lstar(np.array(y)))


#
# --- Contraste de la trama del paño en una exportación ya leída (ver
#     contraste_tela); None sin paño o si su centro se sale de la imagen
def _contraste(review: Review, imagen: np.ndarray,
               espacio: tuple) -> float | None:
    tela = review.tela
    if not isinstance(tela, Ventana):
        return None
    alto, ancho = imagen.shape[:2]
    dy, dx = (review.alto - alto) // 2, (review.ancho - ancho) // 2
    mx = int(tela.ancho * KRV.MARGEN_TELA)
    my = int(tela.alto * KRV.MARGEN_TELA)
    x0, x1 = tela.x - dx + mx, tela.x - dx + tela.ancho - mx
    y0, y1 = tela.y - dy + my, tela.y - dy + tela.alto - my
    if (x0 < 0) or (y0 < 0) or (x1 > ancho) or (y1 > alto):
        return None

    # --- Bloques de la escala de pantalla (los de la medida de los RAW),
    #     su color a luz lineal, luminancia y L*
    lado = bloque_pantalla(review.ancho)
    trozo = (imagen[y0:y1, x0:x1, :KCOM.CANALES_RGB].astype(np.float64)
             / float(np.iinfo(imagen.dtype).max))
    filas, columnas = trozo.shape[0] // lado, trozo.shape[1] // lado
    if (filas == 0) or (columnas == 0):
        return None
    bloques = (trozo[:(filas * lado), :(columnas * lado)]
               .reshape(filas, lado, columnas, lado, KCOM.CANALES_RGB)
               .mean(axis=(1, 3)))
    lstar = _a_lstar(lineal(bloques, espacio) @ np.array(espacio[1]))
    return float(np.percentile(lstar, KRV.PERCENTIL_CLARO)
                 - np.percentile(lstar, KRV.PERCENTIL_OSCURO))


#
def lstar_tiff(review: Review, ruta: Path) -> float | str:
    """
    L* de la tarjeta en una exportación del revelador: la mediana de las
    teselas buenas del análisis (recolocadas con el recorte del revelador,
    que se supone centrado), su color pasado a luminancia según el
    espacio de su perfil, y esta a L*. Si no se puede, por qué (KRV).
    """
    leida = _leer_tiff(review, ruta)
    if isinstance(leida, str):
        return leida
    return _lstar(review, *leida)


#
def contraste_tela(review: Review, ruta: Path) -> float | None:
    """
    Contraste de la trama del paño en una exportación del revelador: en el
    centro de su rectángulo (sin KRV.MARGEN_TELA por cada lado, y
    recolocado con el recorte del revelador), la diferencia de L* entre
    el percentil claro y el oscuro de sus bloques de la escala de
    pantalla (los de la medida de los RAW). None sin paño o si no se puede
    medir (Tony, 2026-11-13)
    """
    leida = _leer_tiff(review, ruta)
    if isinstance(leida, str):
        return None
    return _contraste(review, *leida)


#
def medir_tiff(review: Review, ruta: Path) -> MedidaTiff:
    """
    Todo lo que se guarda de una exportación del revelador: su L* o por
    qué no se pudo medir (ver lstar_tiff), sus bits, su espacio de color
    y el contraste de la trama del paño (ver contraste_tela). La
    exportación se lee una sola vez.
    """
    leida = _leer_tiff(review, ruta)
    if isinstance(leida, str):
        lstar, contraste = leida, None
    else:
        lstar, contraste = _lstar(review, *leida), _contraste(review, *leida)
    try:
        espacio = espacio_tiff(ruta)
    except (OSError, ValueError):
        espacio = None
    medido = isinstance(lstar, float)
    return MedidaTiff(lstar=lstar if medido else None,
                      motivo=None if medido else str(lstar),
                      bits=bits_tiff(ruta), espacio=espacio,
                      contraste=contraste)
