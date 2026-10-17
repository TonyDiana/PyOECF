# -*- coding: utf-8 *-*
"""
    :Propósito: Marca y modelo de la cámara de un RAW.
    :Autor:     Tony Diana
    :Versión:   26.10.09
"""

# cSpell:ignore desplaz, fujifilmccd, kcom

__all__ = ["Cam", "KC", "leer_cam"]

# --- Bibliotecas estándar Python
import struct
from pathlib import Path
from typing import NamedTuple

# --- Bibliotecas internas
from bib import clases
from .constantes import COM as KCOM
from .tiff import ascii_tiff, etiqueta_tiff, primer_directorio, texto_ascii


#
class KC(clases.EnumMutable):
    """ Constantes del lector de marca y modelo. """

    # --- TIFF: etiquetas Make y Model (lo común de TIFF, en COM)
    ETIQUETA_MARCA = 0x010F
    ETIQUETA_MODELO = 0x0110

    # --- RAF de Fujifilm: firma y posición fija del modelo
    FIRMA_RAF = b"FUJIFILMCCD-RAW"
    MARCA_RAF = "FUJIFILM"
    MODELO_RAF = slice(28, 60)


#
class Cam(NamedTuple):
    """ Cámara de una toma: marca y modelo tal como los guarda el RAW. """
    marca: str
    modelo: str

    #
    @property
    def nombre(self) -> str:
        """
        Saber el nombre de la cámara, para mostrarlo: el modelo, que ya
        suele llevar la marca («Canon EOS 70D», «NIKON D750»); si no la
        lleva, marca y modelo («SONY ZV-E10»).
        """
        palabra = (self.marca.split() or [""])[0]
        if self.modelo.upper().startswith(palabra.upper()):
            return self.modelo
        return f"{self.marca} {self.modelo}"


#
def leer_cam(archivo: Path) -> Cam | None:
    """ Marca y modelo de la cámara, o None si no se encuentran o el
        archivo no se puede leer. """
    try:
        with open(archivo, "rb") as f:
            datos = f.read(KCOM.BYTES_CABECERA)
    except OSError:
        return None
    encontrada = _cam_raf(datos) or _cam_tiff(datos)
    return Cam(*encontrada) if encontrada else None


# --- Los RAF llevan el modelo en una cadena fija tras la firma
def _cam_raf(datos: bytes) -> tuple[str, str] | None:
    if not datos.startswith(KC.FIRMA_RAF):
        return None
    return KC.MARCA_RAF, texto_ascii(datos[KC.MODELO_RAF])


# --- Busca cabeceras TIFF y lee Make y Model del primer directorio
def _cam_tiff(datos: bytes) -> tuple[str, str] | None:
    for firma, orden in KCOM.FIRMAS_TIFF:
        pos = datos.find(firma)

        while pos != -1:
            try:
                encontrado = _directorio_tiff(datos, pos, orden)

            except struct.error:
                encontrado = None

            if encontrado:
                return encontrado

            pos = datos.find(firma, pos + 1)

    return None


# --- Make y Model del directorio TIFF que empieza en pos, o None
def _directorio_tiff(datos: bytes, pos: int,
                     orden: str) -> tuple[str, str] | None:
    inicio = primer_directorio(datos, pos, orden)

    reads = {}
    for etiqueta in (KC.ETIQUETA_MARCA, KC.ETIQUETA_MODELO):
        encontrada = etiqueta_tiff(datos, inicio, orden, etiqueta)

        if encontrada and encontrada[0] == KCOM.TIPO_ASCII:
            tipo, cuenta, valor = encontrada
            reads[etiqueta] = ascii_tiff(datos, pos, orden, cuenta, valor)

    if KC.ETIQUETA_MODELO not in reads:
        return None

    return reads.get(KC.ETIQUETA_MARCA, ""), reads[KC.ETIQUETA_MODELO]
