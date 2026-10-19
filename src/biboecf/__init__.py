# -*- coding: utf-8 *-*
"""
    :Propósito:
        Este ``__init__`` hará las veces de un **MNS** (*Module Name Server*)
        que permite invocar cualquier elemento de la biblioteca **BibOECF**
        con un simple:

        ``import biboecf``

    :Autor:     Tony Diana
    :Versión:   26.10.18
"""

# cSpell:ignore biboecf, kpsd

__all__ = ["ajustar_transferencia", "BalanceMedido", "buscar_tela", "Cam",
           "escala_mpx", "espacio_icc", "espacio_tiff", "Excel", "Exp",
           "factores", "Ficha", "Incidencia", "incidencias", "KAN", "KC",
           "KCA", "KCOM", "KFI", "KI", "KM", "KP", "KPSD", "KRV", "KS", "KTE",
           "KTR", "KXL", "leer_balance", "leer_cam", "leer_kelvin",
           "lstar_tiff", "medir_teselas", "OECF", "perfil_tiff", "porcentaje",
           "problema_carpeta", "Psd", "PuntoCurva", "recorte", "revelar",
           "Review", "review_a_dict", "review_de_dict", "RUTA_PLANTILLA",
           "RUTA_PROMPT_IA", "Secuencia", "Select", "signal_para_snr",
           "snr_modelo", "Teselas", "texto_zona", "Toma", "Transferencia",
           "Ventana", "zona_tercio", "ZonaMedida"]

#
# --- Lo propio de cada marca: los nombres de los balances de blancos
#
from .marcas import KM, leer_balance, leer_kelvin

#
# --- OECF: la serie de tomas de una carpeta, con lo que se lee de ella
#
from .cam import KC, Cam, leer_cam
from .kernel import Exp, OECF, Toma

#
# --- Protocolo y partes de la serie, y nombres de las zonas
#
from .secuencia import KS, Secuencia
from .zonas import KP, texto_zona, zona_tercio

#
# --- Problemas de la carpeta e incidencias de la serie: códigos, sin
#     frases
#
from .carpeta import KCA, problema_carpeta
from .informe import KI, Incidencia, incidencias

#
# --- Teselas de una toma: el paño de la Z-V, los tamaños de lámina que
#     caben y su recorte
#
from .teselas import (KTE, Select, Teselas, Ventana, buscar_tela, factores,
                      medir_teselas, porcentaje, recorte, revelar)

#
# --- Curva de transferencia del ruido: lectura, fotones y proporcional
#
from .transferencia import (KTR, Transferencia, ajustar_transferencia,
                            escala_mpx, signal_para_snr, snr_modelo)

#
# --- Segunda parte: el L* de las exportaciones del revelador
#
from .revelado import (KRV, espacio_icc, espacio_tiff, lstar_tiff,
                       perfil_tiff)

#
# --- Láminas PSD
#
from .psd import KPSD, Psd

#
# --- Lo medido en los RAW, y su paso a JSON y de vuelta
#
from .review import (KAN, BalanceMedido, Review, ZonaMedida, review_a_dict,
                     review_de_dict)

#
# --- Libro Excel de resultados
#
from .excel import KXL, Excel, PuntoCurva

#
# --- Ficha PDF de la cámara, para el estudiante (la dibuja desde el libro)
#
from .ficha import KFI, Ficha

#
# --- Constantes comunes (los criterios del método) y, aparte, las rutas
#     de la plantilla de las láminas y del prompt de la hoja IA, en los
#     recursos de la biblioteca
#
from .constantes import COM as KCOM
RUTA_PLANTILLA = KCOM.RUTA_PLANTILLA
RUTA_PROMPT_IA = KCOM.RUTA_PROMPT_IA
