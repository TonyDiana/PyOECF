# -*- coding: utf-8 *-*
"""
    :Propósito: Lectura de directorios TIFF, común a los lectores de la
                cámara (cam.py) y de lo propio de cada marca (marcas.py).
                Casi todos los RAW son TIFF o lo llevan dentro
    :Autor:     Tony Diana
    :Versión:   26.10.11
"""

# cSpell:ignore desplaz, kcom

__all__ = ["orden_tiff", "primer_directorio", "entero_tiff", "corto_tiff",
           "etiqueta_tiff", "lista_tiff", "ascii_tiff", "texto_ascii"]

# --- Bibliotecas estándar Python
import struct

# --- Bibliotecas internas
from .constantes import COM as KCOM


# --- Orden de bytes de la cabecera TIFF que empieza en pos («<» o «>»),
#     o None si ahí no hay una
def orden_tiff(datos: bytes, pos: int) -> str | None:
    return next((o for firma, o in KCOM.FIRMAS_TIFF
                 if datos.startswith(firma[:2], pos)), None)


# --- Dónde empieza el primer directorio de la cabecera TIFF que empieza
#     en pos (posición en datos). salto: dónde está su desplazamiento,
#     contando desde pos (en TIFF, 4; las notas de Fujifilm usan otro)
def primer_directorio(datos: bytes, pos: int, orden: str,
                      salto: int = KCOM.POS_PRIMER_DIRECTORIO) -> int:
    return pos + struct.unpack_from(orden + KCOM.FORMATO_ENTERO, datos,
                                    pos + salto)[0]


# --- Entero de 4 bytes guardado en el valor de una entrada TIFF: un
#     desplazamiento o el propio dato
def entero_tiff(valor: bytes, orden: str) -> int:
    return struct.unpack(orden + KCOM.FORMATO_ENTERO, valor)[0]


# --- Entero de 2 bytes guardado al principio del valor de una entrada
def corto_tiff(valor: bytes, orden: str) -> int:
    return struct.unpack(orden + KCOM.FORMATO_CORTO,
                         valor[:KCOM.BYTES_CORTO])[0]


# --- Busca una etiqueta en el directorio TIFF que empieza en inicio y
#     devuelve (tipo, cuenta, valor), o None si no está
def etiqueta_tiff(datos: bytes, inicio: int, orden: str,
                  buscada: int) -> tuple[int, int, bytes] | None:
    n = struct.unpack_from(orden + KCOM.FORMATO_CORTO, datos, inicio)[0]
    if not 1 <= n < KCOM.MAX_ENTRADAS:
        return None
    for i in range(n):
        tag, tipo, cuenta, valor = struct.unpack_from(
            orden + KCOM.FORMATO_ENTRADA, datos,
            inicio + KCOM.BYTES_CORTO + KCOM.BYTES_ENTRADA * i)
        if tag == buscada:
            return tipo, cuenta, valor
    return None


# --- Lista de cuenta enteros cortos con signo que empieza en pos
def lista_tiff(datos: bytes, pos: int, orden: str,
               cuenta: int) -> tuple[int, ...]:
    return struct.unpack_from(
        orden + KCOM.FORMATO_LISTA.format(cuenta=cuenta), datos, pos)


# --- Texto ASCII de una entrada TIFF. Si cabe en la entrada (4 bytes o
#     menos), va en ella; si no, la entrada dice dónde está, contando
#     desde la cabecera TIFF (base)
def ascii_tiff(datos: bytes, base: int, orden: str, cuenta: int,
               valor: bytes) -> str:
    if cuenta <= KCOM.BYTES_EN_ENTRADA:
        return texto_ascii(valor[:cuenta])
    desplaz = entero_tiff(valor, orden)
    return texto_ascii(datos[base + desplaz:base + desplaz + cuenta])


# --- Cadena ASCII terminada en cero, sin espacios sobrantes
def texto_ascii(bruto: bytes) -> str:
    return bruto.split(b"\x00")[0].decode("ascii", "replace").strip()
