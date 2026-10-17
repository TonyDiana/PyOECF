# -*- coding: utf-8 *-*
"""
    :Propósito: Datos que se piden al usuario: declaración de los campos
                (sin textos: cada interfaz los traduce por su nombre) y
                su validación, que devuelve códigos de problema
    :Autor:     Tony Diana
    :Versión:   26.10.12
"""

# cSpell:ignore bicubica, bilineal, pano

__all__ = ["KCA", "Campo", "campos", "problema_carpeta", "validar"]

# --- Bibliotecas estándar Python
from pathlib import Path
from typing import NamedTuple

# --- Bibliotecas internas
from bib import clases
from .kernel import OECF


#
class KCA(clases.EnumMutable):
    """ Constantes de los campos. """

    # --- Nombres de los campos: son también la clave para traducirlos.
    #     Solo los decididos; la salida va siempre a la carpeta OECF de la
    #     serie y la cámara se lee, no se pide
    CARPETA_SERIE = "carpeta_serie"
    METODO_REDUCCION = "metodo_reduccion_pano"

    # --- Tipos de campo
    TIPO_RUTA = "ruta"
    TIPO_OPCION = "opcion"

    # --- Reducción del recorte del paño para la lámina al 50 %: area es
    #     la media de cada bloque de píxeles (conserva la luz y no inventa
    #     recortes en las luces); bicubica realza los bordes
    METODO_AREA = "area"
    METODOS = (METODO_AREA, "bilineal", "bicubica")

    # --- Problemas de un campo, en el orden en que se comprueban
    NO_EXISTE = "NO_EXISTE"
    NO_LEGIBLE = "NO_LEGIBLE"
    SIN_RAW = "SIN_RAW"
    NO_ESCRIBIBLE = "NO_ESCRIBIBLE"
    NO_ADMITIDO = "NO_ADMITIDO"


#
# --- Un campo que se pide al usuario
class Campo(NamedTuple):
    """ Campo que se pide al usuario, sin textos. """
    nombre: str
    tipo: str

    # --- Valor por defecto (None si es obligatorio y no tiene)
    defecto: object
    obligatorio: bool

    # --- True: va en «Mostrar ajustes avanzados»
    avanzado: bool

    # --- Valores admitidos, en los de tipo opción
    opciones: tuple[str, ...] = ()


#
def campos() -> tuple[Campo, ...]:
    """ Campos que se piden al usuario, en el orden en que se muestran. """
    return (
        Campo(KCA.CARPETA_SERIE, KCA.TIPO_RUTA, None, True, False),
        Campo(KCA.METODO_REDUCCION, KCA.TIPO_OPCION, KCA.METODO_AREA, False,
              True, KCA.METODOS))


#
def problema_carpeta(oecf: OECF) -> str | None:
    """
    Problema de la carpeta de una serie (KCA), o None si sirve: debe
    existir, poder leerse, tener RAW y poder escribirse (para la carpeta
    OECF, donde van los resultados).
    """
    if not oecf.esCarpeta:
        return KCA.NO_EXISTE
    if not oecf.esLegible:
        return KCA.NO_LEGIBLE
    if not oecf.raws:
        return KCA.SIN_RAW
    if not oecf.esEscribible:
        return KCA.NO_ESCRIBIBLE
    return None


#
def validar(valores: dict[str, object]) -> dict[str, str]:
    """
    Problemas de los valores de los campos: {nombre: código (KCA)}. Si
    está vacío, todo sirve. Un campo que falta toma su defecto.
    """
    problemas: dict[str, str] = {}
    for campo in campos():
        valor = valores.get(campo.nombre, campo.defecto)

        if campo.tipo == KCA.TIPO_RUTA:
            problema = (problema_carpeta(OECF(Path(str(valor))))
                        if valor is not None else KCA.NO_EXISTE)
        else:
            problema = (None if valor in campo.opciones
                        else KCA.NO_ADMITIDO)

        if problema:
            problemas[campo.nombre] = problema
    return problemas
