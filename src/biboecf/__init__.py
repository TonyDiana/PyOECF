# -*- coding: utf-8 *-*
"""
    :Propósito:
        Este ``__init__`` hará las veces de un **MNS** (*Module Name Server*)
        que permite invocar cualquier elemento de la biblioteca **BibOECF**
        con un simple:

        ``import biboecf``

    :Autor:     Tony Diana
    :Versión:   26.10.15
"""

# cSpell:ignore biboecf

__all__ = ["Analisis", "analisis_a_dict", "analisis_de_dict", "buscar_pano",
           "Cam", "Campo", "campos", "Exp", "factores", "Incidencia",
           "incidencias", "KAN", "KCA", "KI", "KLA", "KLI", "KM", "KP",
           "KRV", "KS", "KTE", "Lamina", "Libro", "lstar_tiff",
           "KFI", "Ficha", "PuntoCurva",
           "medir_teselas", "OECF", "perfil_tiff", "espacio_tiff",
           "espacio_icc", "porcentaje",
           "problema_carpeta", "recorte", "revelar", "RUTA_PLANTILLA",
           "RUTA_PROMPT_IA",
           "Secuencia", "Teselas", "texto_zona", "Toma", "validar",
           "Ventana", "zona_tercio", "ZonaMedida", "KTR", "Transferencia",
           "ajustar_transferencia", "snr_modelo", "senal_para_snr",
           "escala_mpx"]

#
# --- Lo propio de cada marca: los nombres de los balances de blancos
#
from .marcas import KM

#
# --- Plantilla de las láminas y prompt de la hoja IA: sus rutas, en los
#     recursos de la biblioteca
#
from .constantes import COM as _COM
RUTA_PLANTILLA = _COM.RUTA_PLANTILLA
RUTA_PROMPT_IA = _COM.RUTA_PROMPT_IA

#
# --- OECF: la serie de tomas de una carpeta, con lo que se lee de ella
#
from .cam import Cam
from .kernel import Exp, OECF, Toma

#
# --- Protocolo y partes de la serie, y nombres de las zonas
#
from .secuencia import KS, Secuencia
from .zonas import KP, texto_zona, zona_tercio

#
# --- Datos que se piden (campos) e incidencias de la serie: códigos, sin
#     frases
#
from .campos import KCA, Campo, campos, problema_carpeta, validar
from .informe import KI, Incidencia, incidencias

#
# --- Teselas de una toma: el paño de la Z-V, los tamaños de lámina que
#     caben y su recorte
#
from .teselas import (KTE, Teselas, Ventana, buscar_pano, factores,
                          medir_teselas, porcentaje, recorte, revelar)

#
# --- Curva de transferencia del ruido: lectura, fotones y proporcional
#
from .transferencia import (KTR, Transferencia, ajustar_transferencia,
                                escala_mpx, senal_para_snr, snr_modelo)

#
# --- Segunda parte: el L* de las exportaciones del revelador
#
from .revelado import (KRV, espacio_icc, espacio_tiff, lstar_tiff,
                           perfil_tiff)

#
# --- Láminas PSD
#
from .lamina import KLA, Lamina

#
# --- Lo medido en los RAW, y su paso a JSON y de vuelta
#
from .analisis import (KAN, Analisis, ZonaMedida, analisis_a_dict,
                           analisis_de_dict)

#
# --- Libro Excel de resultados
#
from .libro import KLI, Libro, PuntoCurva

#
# --- Ficha PDF de la cámara, para el estudiante (la dibuja desde el libro)
#
from .ficha import KFI, Ficha
