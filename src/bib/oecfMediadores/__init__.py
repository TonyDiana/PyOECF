# -*- coding: utf-8 *-*
"""
    :Propósito: Los mediadores: lo que comparten PyOECF y FE a través del
                JSON del estudio. Ofrece lo común (claves de los grupos,
                versión del formato, textos y utilidades de «common») y el
                Mediador que usa FE para leer el estudio
    :Autor:     Tony Diana
    :Versión:   26.10.26
"""

# cSpell:ignore kmed, kres

__all__ = ["estado_version", "ident_toma", "KES", "KFR", "KI", "KMA", "KMED",
           "KP", "KRES", "MARCADORES_INCIDENCIA", "marcadores_incidencia",
           "Mediador", "partes_version", "texto_iso", "texto_zona",
           "TEXTOS_INCIDENCIA_ES", "TEXTOS_LADO", "TXT_DONDE", "TXT_Y",
           "version_formato", "zona_tercio"]

# --- Paquete propio
from .common import (KES, KFR, KI, KMA, KMED, KP, KRES, MARCADORES_INCIDENCIA,
                     TEXTOS_INCIDENCIA_ES, TEXTOS_LADO, TXT_DONDE, TXT_Y,
                     estado_version, ident_toma, marcadores_incidencia,
                     partes_version, texto_iso, texto_zona, version_formato,
                     zona_tercio)
from .fe_mediator import Mediador
