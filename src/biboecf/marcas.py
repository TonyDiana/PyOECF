# -*- coding: utf-8 *-*
"""
    :Propósito: Constantes y lecturas propias de cada marca de cámara: lo
                que cada una guarda a su manera en su RAW
    :Autor:     Tony Diana
    :Versión:   26.10.09
"""

# cSpell:ignore codigo, desplaz, exif, fuji, makernote, nikon, posicion
# cSpell:ignore shotinfo, sony

__all__ = ["KM", "leer_balance", "leer_kelvin"]

# --- Bibliotecas estándar Python
import re
import struct
from pathlib import Path

# --- Bibliotecas internas
from bib import clases
from .constantes import COM as KCOM
from .tiff import (ascii_tiff, corto_tiff, entero_tiff, etiqueta_tiff,
                   lista_tiff, orden_tiff, primer_directorio)


#
class KM(clases.EnumMutable):
    """ Constantes propias de cada marca. """

    # --- Todas guardan el balance de blancos en sus notas del fabricante
    #     (makernote), siempre al principio del archivo. Nikon, en texto;
    #     las demás, con un código propio de cada marca, que aquí se
    #     traduce a un nombre en inglés y mayúsculas, como el de Nikon. Un
    #     código que no está en la tabla se queda en número: «CODE 23»
    CODIGO_DESCONOCIDO = "CODE {codigo}"

    # --- Nombres de los balances que comparten varias marcas (los que la
    #     app traduce); los demás, escritos en su tabla
    B_AUTO = "AUTO"
    B_DAYLIGHT = "DAYLIGHT"
    B_CLOUDY = "CLOUDY"
    B_TUNGSTEN = "TUNGSTEN"
    B_FLUORESCENT = "FLUORESCENT"
    B_FLASH = "FLASH"
    B_CUSTOM = "CUSTOM"
    B_SHADE = "SHADE"
    B_KELVIN = "KELVIN"
    B_UNDERWATER = "UNDERWATER"
    B_INCANDESCENT = "INCANDESCENT"

    # --- Nikon. Sus notas empiezan con esta firma y, a salto_nikon
    #     bytes, llevan su propia cabecera TIFF: sus desplazamientos
    #     cuentan desde ella. La etiqueta 0x0005 es el balance, en texto:
    #     SUNNY, PRESET1, 5560K…
    FIRMA_NIKON = b"Nikon\x00\x02"
    SALTO_NIKON = 10
    ETIQUETA_BALANCE_NIKON = 0x0005

    # --- Canon. CR2: TIFF con «CR» en el byte 8; sus notas son un
    #     directorio sin cabecera propia. CR3: las notas van en la caja
    #     CMT3, con su propia cabecera TIFF justo detrás de la firma. En
    #     las dos, la etiqueta 0x0004 (ShotInfo) es una lista de enteros
    #     de 2 bytes, y el balance es el de la posición 7
    FIRMA_CR2 = b"CR"
    POSICION_FIRMA_CR2 = 8
    FIRMA_CR3 = b"CMT3"
    ETIQUETA_SHOTINFO_CANON = 0x0004
    POSICION_BALANCE_CANON = 7
    BALANCES_CANON = {0: B_AUTO, 1: B_DAYLIGHT, 2: B_CLOUDY, 3: B_TUNGSTEN,
                      4: B_FLUORESCENT, 5: B_FLASH, 6: B_CUSTOM,
                      7: "BLACK WHITE", 8: B_SHADE, 9: B_KELVIN,
                      14: "DAYLIGHT FLUORESCENT", 15: "CUSTOM1",
                      16: "CUSTOM2", 17: B_UNDERWATER, 18: "CUSTOM3",
                      19: "CUSTOM4", 23: "AUTO AMBIENCE"}

    # --- Canon: temperatura de color con que se hizo la toma (todas, no
    #     solo las de balance por Kelvin), en ColorData (etiqueta 0x4001),
    #     una lista de enteros de 2 bytes. La posición depende de su
    #     versión, que es el primer número: {versión: posición}. En CR2,
    #     ColorData va en las notas; en CR3, en otra cabecera TIFF cerca
    #     del final del archivo (sus metadatos de la toma): se busca en
    #     los últimos bytes_cola_cr3 bytes
    ETIQUETA_COLORDATA_CANON = 0x4001
    KELVIN_CANON = {9: 67, 10: 67, 13: 67, 15: 67, 48: 109}
    BYTES_COLA_CR3 = 262144

    # --- Sony. Sus notas empiezan con esta firma y su directorio va a
    #     salto_sony bytes; los desplazamientos cuentan desde el principio
    #     del archivo. La etiqueta 0x0115 es el balance
    FIRMA_SONY = b"SONY DSC \x00\x00\x00"
    SALTO_SONY = 12
    ETIQUETA_BALANCE_SONY = 0x0115
    BALANCES_SONY = {0x00: B_AUTO, 0x01: B_KELVIN, 0x10: B_DAYLIGHT,
                     0x20: B_CLOUDY, 0x30: B_SHADE, 0x40: B_TUNGSTEN,
                     0x50: B_FLASH, 0x60: B_FLUORESCENT, 0x70: B_CUSTOM,
                     0x80: B_UNDERWATER}

    # --- Sony: temperatura de color con que se hizo la toma (todas)
    ETIQUETA_KELVIN_SONY = 0xB021

    # --- Fujifilm. Sus notas empiezan con esta firma, seguida del
    #     desplazamiento de su directorio, que cuenta desde la firma.
    #     Siempre en orden de bytes Intel. La etiqueta 0x1002 es el
    #     balance
    FIRMA_FUJI = b"FUJIFILM\x0c\x00\x00\x00"
    SALTO_FUJI = 8
    ORDEN_FUJI = "<"
    ETIQUETA_BALANCE_FUJI = 0x1002
    BALANCES_FUJI = {0x000: B_AUTO, 0x001: "AUTO WHITE",
                     0x002: "AUTO AMBIENCE", 0x100: B_DAYLIGHT,
                     0x200: B_CLOUDY, 0x300: "DAYLIGHT FLUORESCENT",
                     0x301: "DAY WHITE FLUORESCENT",
                     0x302: "WHITE FLUORESCENT",
                     0x303: "WARM WHITE FLUORESCENT",
                     0x304: "LIVING ROOM FLUORESCENT", 0x400: B_INCANDESCENT,
                     0x500: B_FLASH, 0x600: B_UNDERWATER, 0xF00: B_CUSTOM,
                     0xF01: "CUSTOM2", 0xF02: "CUSTOM3", 0xF03: "CUSTOM4",
                     0xF04: "CUSTOM5", 0xFF0: B_KELVIN}

    # --- Fujifilm: temperatura de color, solo en balance por Kelvin
    ETIQUETA_KELVIN_FUJI = 0x1005

    # --- Nikon: en balance por temperatura de color, el nombre son los
    #     Kelvin seguidos de K (5600K)
    PATRON_KELVIN = r"^(\d+)K$"


#
def leer_balance(archivo: Path) -> str | None:
    """
    Nombre del balance de blancos de la toma, en inglés y mayúsculas
    (Nikon, tal como lo guarda: SUNNY, PRESET1, 5560K…; Canon, Sony y
    Fujifilm, traducido de su código: DAYLIGHT, TUNGSTEN, KELVIN…), o
    None si no se encuentra.
    """
    try:
        with open(archivo, "rb") as f:
            datos = f.read(KCOM.BYTES_CABECERA)
    except OSError:
        return None

    try:
        return (_balance_nikon(datos) or _balance_cr3(datos)
                or _balance_sony(datos) or _balance_fuji(datos)
                or _balance_cr2(datos))
    except struct.error:
        return None


#
def leer_kelvin(archivo: Path) -> int | None:
    """
    Temperatura de color, en Kelvin, con que se hizo la toma, o None si
    no se encuentra. Canon y Sony la guardan en todas las tomas; Nikon y
    Fujifilm, solo con el balance por Kelvin (Nikon, en su nombre:
    5600K).
    """
    try:
        with open(archivo, "rb") as f:
            datos = f.read(KCOM.BYTES_CABECERA)
            if datos.find(KM.FIRMA_CR3) != -1:
                f.seek(0, 2)
                f.seek(max(0, f.tell() - KM.BYTES_COLA_CR3))
                return _kelvin_cola_cr3(f.read())
    except (OSError, struct.error):
        return None

    try:
        return (_kelvin_nikon(datos) or _kelvin_sony(datos)
                or _kelvin_fuji(datos) or _kelvin_cr2(datos))
    except struct.error:
        return None


# --- Nombre de un código de balance según la tabla de su marca
def _nombre(codigo: int, tabla: dict[int, str]) -> str:
    return tabla.get(codigo, KM.CODIGO_DESCONOCIDO.format(codigo=codigo))


# --- Nikon: el balance, en texto, en sus notas
def _balance_nikon(datos: bytes) -> str | None:
    pos = datos.find(KM.FIRMA_NIKON)
    if pos == -1:
        return None
    base = pos + KM.SALTO_NIKON
    orden = orden_tiff(datos, base)
    if orden is None:
        return None
    inicio = primer_directorio(datos, base, orden)
    encontrada = etiqueta_tiff(datos, inicio, orden, KM.ETIQUETA_BALANCE_NIKON)
    if encontrada is None or encontrada[0] != KCOM.TIPO_ASCII:
        return None
    tipo, cuenta, valor = encontrada
    return ascii_tiff(datos, base, orden, cuenta, valor) or None


# --- Canon: el balance de ShotInfo, en el directorio de sus notas que
#     empieza en inicio (desplazamientos desde base)
def _balance_canon(datos: bytes, base: int, inicio: int,
                   orden: str) -> str | None:
    encontrada = etiqueta_tiff(datos, inicio, orden,
                               KM.ETIQUETA_SHOTINFO_CANON)
    if encontrada is None:
        return None
    tipo, cuenta, valor = encontrada
    lista = base + entero_tiff(valor, orden)
    codigo = lista_tiff(datos, lista, orden, cuenta)[
        KM.POSICION_BALANCE_CANON]
    return _nombre(codigo, KM.BALANCES_CANON)


# --- Canon CR3: las notas, en la caja CMT3
def _balance_cr3(datos: bytes) -> str | None:
    pos = datos.find(KM.FIRMA_CR3)
    if pos == -1:
        return None
    base = pos + len(KM.FIRMA_CR3)
    orden = orden_tiff(datos, base)
    if orden is None:
        return None
    inicio = primer_directorio(datos, base, orden)
    return _balance_canon(datos, base, inicio, orden)


# --- Canon CR2: TIFF → EXIF → notas
def _balance_cr2(datos: bytes) -> str | None:
    notas = _notas_cr2(datos)
    if notas is None:
        return None
    inicio, orden = notas
    return _balance_canon(datos, 0, inicio, orden)


# --- Canon CR2: dónde empieza el directorio de sus notas y su orden de
#     bytes, o None si no es un CR2
def _notas_cr2(datos: bytes) -> tuple[int, str] | None:
    orden = orden_tiff(datos, 0)
    if orden is None or not datos.startswith(KM.FIRMA_CR2,
                                             KM.POSICION_FIRMA_CR2):
        return None
    ifd0 = primer_directorio(datos, 0, orden)
    exif = etiqueta_tiff(datos, ifd0, orden, KCOM.ETIQUETA_EXIF)
    if exif is None:
        return None
    notas = etiqueta_tiff(datos, entero_tiff(exif[2], orden), orden,
                          KCOM.ETIQUETA_NOTAS)
    if notas is None:
        return None
    return entero_tiff(notas[2], orden), orden


# --- Canon: los Kelvin de ColorData, en el directorio que empieza en
#     inicio (desplazamientos desde base), según su versión
def _kelvin_canon(datos: bytes, base: int, inicio: int,
                  orden: str) -> int | None:
    encontrada = etiqueta_tiff(datos, inicio, orden,
                               KM.ETIQUETA_COLORDATA_CANON)
    if encontrada is None:
        return None
    tipo, cuenta, valor = encontrada
    lista = lista_tiff(datos, base + entero_tiff(valor, orden), orden,
                       cuenta)
    posicion = KM.KELVIN_CANON.get(lista[0])
    return lista[posicion] if posicion is not None else None


# --- Canon CR2: los Kelvin, en sus notas
def _kelvin_cr2(datos: bytes) -> int | None:
    notas = _notas_cr2(datos)
    if notas is None:
        return None
    inicio, orden = notas
    return _kelvin_canon(datos, 0, inicio, orden)


# --- Canon CR3: los Kelvin, en la cabecera TIFF del final del archivo
#     que tenga ColorData (cola: los últimos bytes del archivo)
def _kelvin_cola_cr3(cola: bytes) -> int | None:
    firma = KCOM.FIRMAS_TIFF[0][0]
    pos = cola.find(firma)
    while pos != -1:
        orden = orden_tiff(cola, pos)
        try:
            encontrado = (_kelvin_canon(cola, pos,
                                        primer_directorio(cola, pos, orden),
                                        orden)
                          if orden else None)
        except struct.error:
            encontrado = None
        if encontrado:
            return encontrado
        pos = cola.find(firma, pos + 1)
    return None


# --- Sony: un código en sus notas
def _balance_sony(datos: bytes) -> str | None:
    pos = datos.find(KM.FIRMA_SONY)
    orden = orden_tiff(datos, 0)
    if pos == -1 or orden is None:
        return None
    encontrada = etiqueta_tiff(datos, pos + KM.SALTO_SONY, orden,
                           KM.ETIQUETA_BALANCE_SONY)
    if encontrada is None:
        return None
    codigo = entero_tiff(encontrada[2], orden)
    return _nombre(codigo, KM.BALANCES_SONY)


# --- Sony: los Kelvin, en sus notas
def _kelvin_sony(datos: bytes) -> int | None:
    pos = datos.find(KM.FIRMA_SONY)
    orden = orden_tiff(datos, 0)
    if pos == -1 or orden is None:
        return None
    encontrada = etiqueta_tiff(datos, pos + KM.SALTO_SONY, orden,
                           KM.ETIQUETA_KELVIN_SONY)
    if encontrada is None:
        return None
    return entero_tiff(encontrada[2], orden) or None


# --- Nikon: los Kelvin, en el nombre del balance (5600K)
def _kelvin_nikon(datos: bytes) -> int | None:
    encontrado = re.match(KM.PATRON_KELVIN, _balance_nikon(datos) or "")
    return int(encontrado.group(1)) if encontrado else None


# --- Fujifilm: un código en sus notas
def _balance_fuji(datos: bytes) -> str | None:
    pos = datos.find(KM.FIRMA_FUJI)
    if pos == -1:
        return None
    orden = KM.ORDEN_FUJI
    inicio = primer_directorio(datos, pos, orden, KM.SALTO_FUJI)
    encontrada = etiqueta_tiff(datos, inicio, orden, KM.ETIQUETA_BALANCE_FUJI)
    if encontrada is None:
        return None
    codigo = corto_tiff(encontrada[2], orden)
    return _nombre(codigo, KM.BALANCES_FUJI)


# --- Fujifilm: los Kelvin, en sus notas (solo en balance por Kelvin)
def _kelvin_fuji(datos: bytes) -> int | None:
    pos = datos.find(KM.FIRMA_FUJI)
    if pos == -1:
        return None
    orden = KM.ORDEN_FUJI
    inicio = primer_directorio(datos, pos, orden, KM.SALTO_FUJI)
    encontrada = etiqueta_tiff(datos, inicio, orden, KM.ETIQUETA_KELVIN_FUJI)
    if encontrada is None:
        return None
    return corto_tiff(encontrada[2], orden) or None
