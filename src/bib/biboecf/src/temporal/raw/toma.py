# -*- coding: utf-8 *-*
"""
    :Propósito: Datos de una toma RAW leídos con rawpy. De momento, solo
                la exposición: tiempo (Tv), diafragma (f) e ISO
    :Autor:     Tony Diana
    :Versión:   26.10.06
"""

# cSpell:ignore imread, rawpy

__all__ = ["KT", "es_tapada", "leer_exp", "texto_exp", "texto_f",
           "texto_iso"]

# --- Bibliotecas estándar Python
import math
from pathlib import Path

# --- Bibliotecas externas
import rawpy

# --- Bibliotecas internas
from bib import std


#
# --- Constantes de la toma
class KT(std.EnumMutable):
    """ Constantes de la lectura de una toma. """

    # --- Extensiones RAW (en minúsculas). Comprobadas con archivos reales:
    #     CR3, CR2, ARW y RAF. NEF (Nikon), sin comprobar todavía
    extensiones = (".cr3", ".cr2", ".arw", ".raf", ".nef")

    # --- Unidad del tiempo de exposición al mostrarlo
    segundos = "s"

    # --- Decimales del diafragma: rawpy lo da en coma flotante de 32 bits
    decimales_f = 1

    # --- Tomas tapadas (tapa puesta y visor cubierto): se disparan a este
    #     tiempo y quedan casi en negro. Brillo: media del RAW sobre el
    #     nivel de negro, en tanto por uno del rango útil. En series
    #     reales, una tapada da 0.0003 y una toma normal, de 0.02 a 0.06
    tv_tapada = 1 / 160
    brillo_tapada = 0.005

    # --- Margen al comparar tiempos: rawpy los da con poca precisión
    margen_tv = 0.01


# --- Exposición de la toma: (segundos, diafragma, ISO), o None si no se
#     puede leer. Se abre el RAW una sola vez para los tres
def leer_exp(archivo: Path) -> tuple[float, float, float] | None:
    try:
        with rawpy.imread(str(archivo)) as raw:
            return (float(raw.other.shutter_speed),
                    float(raw.other.aperture),
                    float(raw.other.iso_speed))
    except (rawpy.LibRawError, OSError):                        # type: ignore
        return None


# --- ¿Es una toma tapada? Solo se mira la imagen de las tomas al tiempo
#     de las tapadas, para no leer la de todas. False si no se puede leer
def es_tapada(archivo: Path, segundos: float) -> bool:
    if not math.isclose(segundos, KT.tv_tapada, rel_tol=KT.margen_tv):
        return False
    try:
        with rawpy.imread(str(archivo)) as raw:
            negro = sum(raw.black_level_per_channel) / len(
                raw.black_level_per_channel)
            brillo = ((raw.raw_image_visible.mean() - negro)
                      / (raw.white_level - negro))
    except (rawpy.LibRawError, OSError):                        # type: ignore
        return False
    return bool(brillo < KT.brillo_tapada)


# --- Tiempo como lo marca la cámara: 1/125 s, o 2 s si pasa del segundo
def texto_exp(segundos: float) -> str:
    if segundos < 1:
        return f"1/{round(1 / segundos)} {KT.segundos}"
    return f"{segundos:g} {KT.segundos}"


# --- Diafragma sin ceros sobrantes: 9, 5.6
def texto_f(diafragma: float) -> str:
    return f"{round(diafragma, KT.decimales_f):g}"


# --- ISO como número entero: 100
def texto_iso(iso: float) -> str:
    return str(round(iso))
