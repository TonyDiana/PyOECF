# -*- coding: utf-8 *-*
"""
    :Propósito: Constantes compartidas de la biblioteca BibOECF. Las que
                solo usa un módulo van en el suyo
    :Autor:     Tony Diana
    :Versión:   26.10.18
"""

# cSpell:ignore biboecf, rawpy

__all__ = ["COM"]

# --- Bibliotecas estándar Python
from pathlib import Path

# --- Bibliotecas internas
from bib import std


#
# --- Constantes comunes
class COM(std.EnumMutable):
    """ Constantes comunes de BibOECF. """

    # --- Recursos de la biblioteca: en su carpeta, junto a su código. Así
    #     viajan con biboecf, y el ejecutable los lleva en la misma ruta
    #     relativa (ver PyOECF.spec)
    CARPETA_RECURSOS = "rec"
    """Carpeta de los recursos de la biblioteca, junto a su código."""

    PLANTILLA_PSD = "Soportes.psd"
    """Plantilla de las láminas (PSD, RGB a 16 bits, 3300 × 2400 px)."""

    RUTA_PLANTILLA = Path(__file__).parent / CARPETA_RECURSOS / PLANTILLA_PSD
    """Ruta de la plantilla de las láminas."""

    PROMPT_IA = "prompt_ia.md"
    """Instrucciones para revisar el libro con una IA (su hoja IA), solo
    en español: en los recursos, para poder editarlas sin tocar el
    código."""

    RUTA_PROMPT_IA = Path(__file__).parent / CARPETA_RECURSOS / PROMPT_IA
    """Ruta de las instrucciones de la hoja IA."""

    # --- Archivos
    EXTENSIONES = (".arw", ".cr2", ".cr3", ".nef", ".raf")
    """Extensiones RAW (en minúsculas). Comprobadas con archivos reales:
    ARW, CR2, CR3, NEF y RAF."""

    EXTENSIONES_TIFF = (".tif", ".tiff")
    """Extensiones de las exportaciones del revelador (en minúsculas), para
    la segunda parte del análisis."""

    # --- Números
    CIEN = 100
    """Para pasar fracciones o divisores a porcentaje."""

    MARGEN_TV = 0.01
    """Margen al comparar tiempos: rawpy los da con poca precisión."""

    CANALES_RGB = 3
    """Canales de color: rojo, verde y azul (matriz de color de la cámara,
    imagen compuesta de la lámina y columnas por canal del libro)."""

    MAX_16 = 65535
    """Máximo de un valor de 16 bits (imagen compuesta de la lámina y
    tablas de las curvas ICC)."""

    # --- Criterios del método, que comparten la medida y el libro (el
    #     libro las escribe en su hoja Constantes)
    UMBRAL_RECORTE = 0.995
    """Recortado: un valor llega a esta fracción del máximo de su canal
    en la serie (en el libro, la constante KXL.C_UMBRAL_RECORTE)."""

    TOLERANCIA_LINEAL = 0.1
    """Tolerancia de linealidad, en zonas: un punto es lineal si se aparta
    menos de lo esperado; una Z-V de control que se aparta más de la ZV
    dice que la luz cambió (en el libro, KXL.C_TOLERANCIA_LINEAL)."""

    # --- CIELab (ISO/CIE 11664-4): L* de una luminancia relativa Y es
    #     (LAB_ESCALA · Y^(1/3)) − LAB_DESPLAZA, o LAB_PENDIENTE · Y por
    #     debajo de LAB_UMBRAL. Las usan el libro y la medida del revelador
    LAB_ESCALA = 116
    """CIELab: factor de la raíz cúbica de Y."""

    LAB_DESPLAZA = 16
    """CIELab: lo que se resta tras la raíz cúbica."""

    LAB_UMBRAL = 0.008856
    """CIELab: por debajo de esta Y, el tramo recto."""

    LAB_PENDIENTE = 903.3
    """CIELab: pendiente del tramo recto, por debajo de LAB_UMBRAL."""

    # --- TIFF (casi todos los RAW lo son o lo llevan dentro)
    BYTES_CABECERA = 262144
    """Bytes del principio del archivo (256 KiB) que se leen para buscar
    los datos de la cámara (marca, modelo, balance…)."""

    FIRMAS_TIFF = ((b"II*\x00", "<"), (b"MM\x00*", ">"))
    """Firmas de la cabecera TIFF, con su orden de bytes para struct."""

    BYTES_ORDEN = 2
    """Bytes de la marca de orden con que empieza la firma TIFF («II» o
    «MM»)."""

    TIPO_ASCII = 2
    """Tipo TIFF de una entrada de texto ASCII."""

    MAX_ENTRADAS = 200
    """Máximo de entradas creíble en un directorio TIFF: con más, no es un
    directorio de verdad."""

    BYTES_ENTRADA = 12
    """Tamaño de cada entrada de un directorio TIFF."""

    BYTES_EN_ENTRADA = 4
    """Tamaño del valor de una entrada: un dato que cabe aquí va en ella;
    si no, la entrada dice dónde está."""

    ETIQUETA_EXIF = 0x8769
    """Etiqueta TIFF del directorio EXIF."""

    ETIQUETA_NOTAS = 0x927C
    """Etiqueta EXIF de las notas del fabricante."""

    # --- TIFF: formatos de struct (sin el orden de bytes, que va delante)
    FORMATO_ENTERO = "I"
    """Entero de 4 bytes (desplazamientos y valores)."""

    FORMATO_CORTO = "H"
    """Entero de 2 bytes (como el número de entradas de un directorio)."""

    FORMATO_ENTRADA = "HHI4s"
    """Entrada de un directorio: etiqueta, tipo, cuenta y valor."""

    FORMATO_LISTA = "{cuenta}h"
    """Lista de cuenta enteros de 2 bytes con signo."""

    BYTES_CORTO = 2
    """Bytes de un entero de 2 (FORMATO_CORTO)."""

    POS_PRIMER_DIRECTORIO = 4
    """Posición, en la cabecera TIFF, del desplazamiento del primer
    directorio."""
