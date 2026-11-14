# -*- coding: utf-8 *-*
"""
    :Propósito: Mediador entre PyOECF y FE: quien lo usa le da la carpeta
                del estudio y la versión del formato que sabe leer; el
                mediador lo lee, comprueba la versión y entrega los datos.
                Solo depende de std y de la librería estándar: nunca de
                otros paquetes de PyOECF
    :Autor:     Tony Diana
    :Versión:   26.10.23
"""

# cSpell:ignore codificacion, kmed, oecf

__all__ = ["Mediador"]

# --- Bibliotecas estándar Python
import copy
import json
from pathlib import Path

# --- Bibliotecas internas
from .common import (KES, KMED, estado_version, partes_version,
                     version_formato)


#
class Mediador(object):
    """
    Lee el JSON del estudio para quien no lleva el código de PyOECF (FE).

    El constructor solo guarda la ruta y la versión: no abre nada. El
    JSON (``KES.ARCHIVO``, dentro de la carpeta) se lee la primera vez que se
    pide el ``estado`` o un dato, y no se vuelve a leer. Los datos que entrega
    nunca llevan ``medida``.

    Reglas de versión (ver ``KES``): un MAYOR superior al que sabe leer
    quien llama es ``KMED.VERSION_NUEVA``; uno inferior, ``VERSION_ANTIGUA``;
    el mismo MAYOR con otro MENOR se acepta, ignorando las claves que no se
    conozcan.
    """

    __slots__ = ["__path", "__version", "__estado", "__datos"]

    #
    def __init__(self, path: str | Path, version: str) -> None:
        """
        Guarda la carpeta del estudio (el JSON es ``KES.ARCHIVO`` dentro de
        ella) y la versión del formato que sabe leer quien llama
        (MAYOR.MENOR, p. ej. «1.0»). No abre ningún archivo. Lanza
        ValueError si la versión no son números separados por puntos.
        """
        partes_version(version)
        self.__path = Path(path) / KES.ARCHIVO
        self.__version = version
        self.__estado: str | None = None
        self.__datos: dict | None = None

    #
    @property
    def path(self) -> Path:
        """ Ruta del JSON, como Path. """
        return self.__path

    #
    @property
    def version(self) -> str:
        """ Versión del formato que sabe leer quien llama. """
        return self.__version

    #
    @property
    def estado(self) -> str:
        """
        Estado de la lectura (un ``KMED.*``). Lee el archivo la primera vez
        que se pide.
        """
        self.__cargar()
        return self.__estado or KMED.ILEGIBLE

    #
    def dict_estudio(self) -> dict | None:
        """
        Copia de los datos del estudio, sin ``medida``, lista para guardar
        (quien la modifique no cambia al mediador). None si el estado no es
        ``KMED.OK``.
        """
        self.__cargar()
        if self.__datos is None:
            return None
        return copy.deepcopy(self.__datos)

    #
    @property
    def info(self) -> dict | None:
        """ Grupo ``info`` (programa, fecha, carpeta, cámara). Solo
        lectura. """
        return self.__grupo(KES.INFO)                           # type: ignore

    #
    @property
    def serie(self) -> dict | None:
        """ Grupo ``serie`` (iso, balance, tomas…). Solo lectura. """
        return self.__grupo(KES.SERIE)                          # type: ignore

    #
    @property
    def incidencias(self) -> list | None:
        """ Grupo ``incidencias`` (lista de incidencias). Solo lectura. """
        return self.__grupo(KES.INCIDENCIAS)                    # type: ignore

    #
    @property
    def revelado(self) -> dict | None:
        """
        Grupo ``revelado``. None si el estado no es OK o si aún no se ha
        analizado el revelado. Solo lectura.
        """
        return self.__grupo(KES.REVELADO)                       # type: ignore

    #
    @property
    def resultados(self) -> dict | None:
        """
        Grupo ``resultados`` (canales, constantes, linealidad, curva…). None
        si el estado no es OK o si aún no se han generado. Solo lectura.
        """
        return self.__grupo(KES.RESULTADOS)                     # type: ignore

    #
    def __grupo(self, clave: str) -> dict | list | None:
        """ Un grupo de primer nivel, o None si no hay datos válidos. """
        self.__cargar()
        if self.__datos is None:
            return None
        return self.__datos.get(clave)

    #
    def __cargar(self) -> None:
        """
        Lee el JSON una sola vez y fija el estado. Si es OK, guarda los
        datos sin ``medida``; si no, no guarda nada.
        """
        if self.__estado is not None:
            return

        # --- ¿Existe y es un archivo?
        if not self.__path.exists():
            self.__estado = KMED.NO_EXISTE
            return
        if not self.__path.is_file():
            self.__estado = KMED.ILEGIBLE
            return

        # --- Leerlo y comparar la versión; un MENOR distinto se acepta
        try:
            datos = json.loads(
                self.__path.read_text(encoding=KES.CODIFICACION))
            estado = estado_version(
                version_formato(datos), self.__version, True)
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            # JSON mal formado, no se puede leer, o sin versión del formato
            # válida (oecf.versionFormato, u oecf.version en los 1.x)
            self.__estado = KMED.ILEGIBLE
            return
        if estado != KMED.OK:
            self.__estado = estado
            return

        # --- Válido: sin medida, que es interna de PyOECF
        self.__datos = {clave: valor for clave, valor in datos.items()
                        if clave != KES.MEDIDA}
        self.__estado = KMED.OK
