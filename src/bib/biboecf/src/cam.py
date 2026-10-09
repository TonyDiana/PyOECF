# -*- coding: utf-8 *-*
"""
    :Propósito: Marca y modelo de la cámara de un RAW.
    :Autor:     Tony Diana
    :Versión:   26.10.09
"""

# cSpell:ignore desplaz, fujifilmccd,

__all__ = ["Cam", "KC", "leer_cam"]

# --- Bibliotecas estándar Python
import struct
from pathlib import Path
from typing import NamedTuple

# --- Bibliotecas internas
from bib import std


#
class KC(std.EnumMutable):
    """ Constantes del lector de marca y modelo. """

    # --- Bytes del principio del archivo donde se busca el modelo
    bytes_cabecera = 262144

    # --- TIFF: firmas con su orden de bytes, etiquetas Make y Model,
    #     tipo ASCII, máximo de entradas creíble y tamaño de cada entrada
    firmas_tiff = ((b"II*\x00", "<"), (b"MM\x00*", ">"))
    etiqueta_marca = 0x010F
    etiqueta_modelo = 0x0110
    tipo_ascii = 2
    max_entradas = 200
    bytes_entrada = 12
    bytes_en_entrada = 4

    # --- RAF de Fujifilm: firma y posición fija del modelo
    firma_raf = b"FUJIFILMCCD-RAW"
    marca_raf = "FUJIFILM"
    modelo_raf = slice(28, 60)


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
    """ Marca y modelo de la cámara, o None si no se encuentran. """
    with open(archivo, "rb") as f:
        datos = f.read(KC.bytes_cabecera)
    encontrada = _cam_raf(datos) or _cam_tiff(datos)
    return Cam(*encontrada) if encontrada else None


# --- Los RAF llevan el modelo en una cadena fija tras la firma
def _cam_raf(datos: bytes) -> tuple[str, str] | None:
    if not datos.startswith(KC.firma_raf):
        return None
    return KC.marca_raf, _texto(datos[KC.modelo_raf])


# --- Busca cabeceras TIFF y lee Make y Model del primer directorio
def _cam_tiff(datos: bytes) -> tuple[str, str] | None:
    for firma, orden in KC.firmas_tiff:
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
    desplaz = struct.unpack_from(orden + "I", datos, pos + 4)[0]
    inicio = pos + desplaz
    n = struct.unpack_from(orden + "H", datos, inicio)[0]
    if not 1 <= n < KC.max_entradas:
        return None

    reads = {}
    for i in range(n):
        tag, tipo, cuenta, valor = struct.unpack_from(
            orden + "HHI4s", datos, inicio + 2 + KC.bytes_entrada * i)

        if (tag in (KC.etiqueta_marca, KC.etiqueta_modelo)
                and tipo == KC.tipo_ascii):
            if cuenta <= KC.bytes_en_entrada:
                bruto = valor[:cuenta]
            else:
                o = struct.unpack(orden + "I", valor)[0]
                bruto = datos[pos + o:pos + o + cuenta]
            reads[tag] = _texto(bruto)

    if KC.etiqueta_modelo not in reads:
        return None

    return reads.get(KC.etiqueta_marca, ""), reads[KC.etiqueta_modelo]


# --- Cadena ASCII terminada en cero, sin espacios sobrantes
def _texto(bruto: bytes) -> str:
    return bruto.split(b"\x00")[0].decode("ascii", "replace").strip()
