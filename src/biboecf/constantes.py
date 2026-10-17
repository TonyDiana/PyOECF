# -*- coding: utf-8 *-*
"""
    :Propósito: Constantes compartidas de la biblioteca BibOECF. Las que
                solo usa un módulo van en el suyo
    :Autor:     Tony Diana
    :Versión:   26.10.12
"""

# cSpell:ignore biboecf, rawpy

__all__ = ["COM"]

# --- Bibliotecas estándar Python
from pathlib import Path

# --- Bibliotecas internas
from bib import clases


#
# --- Constantes comunes
class COM(clases.EnumMutable):
    """ Constantes comunes de BibOECF. """

    # --- Plantilla de las láminas (PSD, RGB a 16 bits, 3300 × 2400 px):
    #     en la carpeta de recursos de la biblioteca, junto a su código.
    #     Así viaja con biboecf a PyOECF y a FE, y el ejecutable la lleva
    #     en la misma ruta relativa (ver PyOECF.spec)
    CARPETA_RECURSOS = "rec"
    PLANTILLA_PSD = "Soportes.psd"
    RUTA_PLANTILLA = Path(__file__).parent / CARPETA_RECURSOS / PLANTILLA_PSD

    # --- Instrucciones para revisar el libro con una IA (su hoja IA),
    #     solo en español: en los mismos recursos, para poder editarlas
    #     sin tocar el código (el ejecutable las lleva igual que la
    #     plantilla)
    PROMPT_IA = "prompt_ia.md"
    RUTA_PROMPT_IA = Path(__file__).parent / CARPETA_RECURSOS / PROMPT_IA

    # --- Extensiones RAW (en minúsculas). Comprobadas con archivos reales:
    #     ARW, CR2, CR3, NEF y RAF
    EXTENSIONES = (".arw", ".cr2", ".cr3", ".nef", ".raf")

    # --- Para pasar fracciones o divisores a porcentaje
    CIEN = 100

    # --- CIELAB (ISO/CIE 11664-4): L* de una luminancia relativa Y es
    #     LAB_ESCALA · Y^(1/3) − LAB_DESPLAZA, o LAB_PENDIENTE · Y por
    #     debajo de LAB_UMBRAL. Las usan el libro y la medida del revelador
    LAB_ESCALA = 116
    LAB_DESPLAZA = 16
    LAB_UMBRAL = 0.008856
    LAB_PENDIENTE = 903.3

    # --- Extensiones de las exportaciones del revelador (en minúsculas),
    #     para la segunda parte del análisis
    EXTENSIONES_TIFF = (".tif", ".tiff")

    # --- Margen al comparar tiempos: rawpy los da con poca precisión
    MARGEN_TV = 0.01

    # --- Bytes del principio del archivo que se leen para buscar los
    #     datos de la cámara (marca, modelo, balance…)
    BYTES_CABECERA = 262144

    # --- TIFF (casi todos los RAW lo son o lo llevan dentro): firmas con
    #     su orden de bytes, tipo ASCII, máximo de entradas creíble en un
    #     directorio, tamaño de cada entrada y de su valor, y etiquetas
    #     del directorio EXIF y, dentro de él, de las notas del fabricante
    FIRMAS_TIFF = ((b"II*\x00", "<"), (b"MM\x00*", ">"))
    TIPO_ASCII = 2
    MAX_ENTRADAS = 200
    BYTES_ENTRADA = 12
    BYTES_EN_ENTRADA = 4
    ETIQUETA_EXIF = 0x8769
    ETIQUETA_NOTAS = 0x927C

    # --- TIFF: formatos de struct (sin el orden de bytes, que va
    #     delante) de un entero de 4 bytes (desplazamientos y valores), de
    #     uno de 2 (como el número de entradas de un directorio), de cada
    #     entrada (etiqueta, tipo, cuenta y valor) y de una lista de cuenta
    #     enteros de 2 bytes con signo; bytes de un entero de 2, y posición
    #     del desplazamiento del primer directorio en la cabecera
    FORMATO_ENTERO = "I"
    FORMATO_CORTO = "H"
    FORMATO_ENTRADA = "HHI4s"
    FORMATO_LISTA = "{cuenta}h"
    BYTES_CORTO = 2
    POS_PRIMER_DIRECTORIO = 4
