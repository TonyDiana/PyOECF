# -*- coding: utf-8 *-*
"""
    :Propósito: El objeto OECF, entrada de la biblioteca BibOECF: la serie
                de tomas de una carpeta
    :Autor:     Tony Diana
    :Versión:   26.10.19
"""

# cSpell:ignore biboecf, devs, imread, kcom, rawpy, reescalados, whitebalance

__all__ = ["Exp", "Toma", "OECF"]

# --- Bibliotecas estándar Python
import math
import os
import re
import shutil
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

# --- Bibliotecas externas
import numpy as np
import rawpy

# --- Bibliotecas internas
from bib import std
from .cam import Cam, leer_cam
from .constantes import COM as KCOM
from .marcas import KM, leer_balance, leer_kelvin
from .secuencia import KS, Secuencia, balance_personalizado, secuencia
from .review import Review, BalanceMedido, ZonaMedida
from .teselas import (KTE, Select, Ventana, buscar_tela, exceso_negro,
                      part_recortada, matriz_color, medir_teselas,
                      medir_toma, oscuridad, restar_exceso, ruido_temporal,
                      seleccionar, temperatura)
from .transferencia import ajustar_transferencia
from .zonas import (KP, calcular_tercio_exacto, exp_relativa,
                    texto_zona, zona_tercio)


#
class Exp(NamedTuple):
    """ Exposición de una toma. El orden es siempre f, Tv e ISO. """
    f: float
    tv: float
    iso: float


#
class Toma(NamedTuple):
    """
    Datos de una toma, leídos de su RAW de una sola vez. Cada dato es None
    si no se pudo leer. La ruta no va aquí: la toma i es la de raws[i].
    WB: multiplicadores del balance de blancos (todas las marcas);
    nombreWB: su nombre, en inglés y mayúsculas (SUNNY, DAYLIGHT,
    5600K…). bits: profundidad de bits del RAW (12, 14…). kelvin:
    temperatura de color con que se hizo (Canon y Sony, en todas las
    tomas; Nikon y Fujifilm, solo con el balance por Kelvin). tapada:
    con la exposición de las tapadas (f/11 y 1/160); es una tapada solo
    si va tras la Z-V final (ver secuencia). oscura: tapada y casi negra
    (si no, se tapó mal).
    """
    exp: Exp | None
    fecha: datetime | None
    WB: tuple[float, ...] | None
    tapada: bool
    oscura: bool
    nombreWB: str | None
    bits: int | None
    kelvin: int | None


#
class OECF(object):
    """ Serie de tomas de una carpeta. Al crearlo lee de una vez la cámara
        y los datos de la serie, y los ofrece. Cada carpeta tiene su
        objeto, así que puede haber varios a la vez. """

    __slots__ = ["__review", "__balancePersonalizado", "__cam", "__carpeta",
                 "__celdas", "__copias", "__desviadas", "__devs",
                 "__errorCopia",
                 "__enRejilla", "__esCarpeta", "__fuera",
                 "__isoDistintos", "__isoSerie", "__medioPaso", "__tela",
                 "__partes",
                 "__path", "__puedeLeer", "__raws", "__secuencia",
                 "__select",
                 "__tapadas", "__tapadasConLuz", "__tapadasOtroISO",
                 "__tercioEVs", "__tomas", "__wbCtrl", "__WBs",
                 "__zonas", "__zvs"]

    #
    # --- Constantes de la toma
    class KT(std.EnumMutable):
        """ Constantes de la lectura de una toma. """

        # --- Unidad del tiempo de exposición al mostrarlo, y separador
        #     entre los trozos de un texto de una línea (f, Tv e ISO de la
        #     exposición; también lo usa la aplicación en sus resúmenes)
        SEGUNDOS = "s"
        SEPARADOR = " · "

        # --- Decimales del diafragma: rawpy lo da en coma flotante de 32
        #     bits
        DECIMALES_F = 1

        # --- Tomas tapadas (tapa puesta y visor cubierto): siempre a f/11
        #     y 1/160, con el ISO de la serie; esa exposición las
        #     identifica (Tony, 2026-10-19), con margen en el diafragma
        #     (f/11 real es 11,31 y hay cámaras que guardan este).
        #     Deben quedar casi en negro: si no, se tapó mal (no sirven
        #     para el negro y se avisa). Brillo: media del RAW sobre el
        #     nivel de negro, en tanto por uno del rango útil. En series
        #     reales, una tapada da 0.0003 y una toma normal, de 0.02 a
        #     0.06
        F_TAPADA = 11
        MARGEN_F_TAPADA = 0.05
        TV_TAPADA = 1 / 160
        BRILLO_TAPADA = 0.005

        # --- Balance de blancos: canal verde (R, G, B, G2), con el que se
        #     dividen los multiplicadores, y sus decimales
        CANAL_VERDE = 1
        DECIMALES_WB = 4

        # --- Copias de la serie: carpeta dentro de la de la serie, con el
        #     JSON en su raíz y una subcarpeta por papel, y nombres de cada
        #     copia (llevan la extensión de su RAW). ZONAS: Z00 a Z10, con
        #     -3 y -7 en los tercios (Z05 es la ZV), y las exportaciones
        #     del revelador (TIFF), junto a su RAW. CTRL: balances de
        #     cámara, WB-01, WB-02… con el nombre del balance si la cámara
        #     lo guarda (WB-03-INCANDESCENT, WB-07-NATURAL-AUTO): en
        #     mayúsculas y con un guion en lugar de lo que no sea letra o
        #     número; el de Kelvin a mano, con sus K (WB-01-KELVIN-5600K);
        #     de los repetidos (mismo nombre y multiplicadores), solo el
        #     último. También las tapadas, DARK-1, DARK-2; la toma del
        #     balance personalizado, WB-CTRL; las Z-V de control, ZV-INI,
        #     ZV-MEDIO (cambio de lado) y ZV-FIN (de cada una, la última),
        #     y las incidencias. ANALISIS: el libro, la ficha y las
        #     láminas. JSON y ZONAS bastan para rehacer el análisis: es lo
        #     que se lleva FE (Tony, 2026-10-19)
        CARPETA = "OECF"
        CARPETA_ZONAS = "ZONAS"
        CARPETA_CTRL = "CTRL"
        CARPETA_ANALISIS = "ANALISIS"
        CIFRAS_ZONA = 2
        TERCIOS_ZONA = ("", "-3", "-7")
        NOMBRE_TAPADA = "DARK"
        """ Nombre de las copias de las tomas tapadas (sin su número). """
        PREFIJO_TAPADA = f"{NOMBRE_TAPADA}-"
        PREFIJO_BALANCE = "WB-"
        CIFRAS_BALANCE = 2
        NOMBRE_WB_CTRL = f"{PREFIJO_BALANCE}{CARPETA_CTRL}"
        ZV_INI = "INI"
        """ Papel de la Z-V inicial (ver zvs). """
        ZV_MEDIO = "MEDIO"
        """ Papel de la Z-V del cambio de lado (ver zvs). """
        ZV_FIN = "FIN"
        """ Papel de la Z-V final (ver zvs). """
        SEP_NOMBRE = "-"
        REGEX_RARO = r"[^A-Z0-9]+"

        # --- Parte de la serie de cada toma (ver la property partes). La
        #     de los lados lleva su número: lado1, lado2
        PARTE_INICIAL = "inicial"
        PARTE_LADO = "lado"
        PARTE_CAMBIO = "cambio"
        PARTE_FINAL = "final"
        PARTE_TAPADA = "tapada"
        """ Parte de la serie de las tomas tapadas (ver partes). """
        PARTE_BALANCE = "balance"
        PARTE_SOBRANTE = "sobrante"

        # --- Z-V iniciales de más: las repetidas (todas menos la del
        #     balance personalizado y la última). No van a la rejilla ni
        #     se miden: vale la última (Tony, 2026-10-19); el JSON lo dice
        PARTE_CONTROL = "control"

        # --- Para analizar, de Z1 a Z9 (con sus tercios) ninguna zona
        #     puede quedar sin toma. Las repetidas no impiden analizar
        ZONA_MIN_REVIEW = 1
        ZONA_MAX_REVIEW = 9

        # --- Serie por medios pasos (nunca se analiza: Tony, 2026-10-19):
        #     medio paso es 1,5 tercios, y una de cada dos tomas de los
        #     lados se aparta medio tercio del suyo (DESVIO_MEDIO, con
        #     MARGEN_MEDIO). Lo es si son al menos PARTE_MEDIOS de las
        #     tomas de los lados
        DESVIO_MEDIO = 0.5
        MARGEN_MEDIO = 0.1
        PARTE_MEDIOS = 1 / 3

    #
    # --- Si la carpeta no existe o no tiene RAW, no falla. buscar: si se
    #     buscan sus RAW (no, al restaurar una serie preparada: ver
    #     Restaurar)
    #
    def __init__(self, path: Path, buscar: bool = True) -> None:
        self.__path = path
        self.__esCarpeta = path.is_dir()

        # --- Carpeta de las copias: OECF, dentro de la de la serie (al
        #     restaurar, la elegida: ver Restaurar)
        self.__carpeta: Path = path / self.KT.CARPETA

        # --- Leer los RAW, en orden ([] si no hay o si no hay permiso
        #     para leer la carpeta)
        self.__puedeLeer: bool = self.esCarpeta
        self.__raws: list[Path] = []
        if buscar and self.esCarpeta:
            try:
                self.__raws = self.__buscar_raw()
            except OSError:
                self.__puedeLeer = False

        # --- Cámara: marca y modelo de la primera toma (None si no hay RAW
        #     o no se leen)
        self.__cam: Cam | None = (leer_cam(self.raws[0]) if self.raws
                                  else None)

        # --- Tomas leídas, en el orden de raws. Ahora, solo la primera,
        #     la Z-V: referencia de la serie ([] si no hay RAW)
        self.__tomas: list[Toma] = ([self.__leer_toma(self.raws[0])]
                                    if self.raws else [])

        # --- Reparto de la serie: se calcula al terminar de leerla (vacío
        #     hasta entonces). Si solo hay una toma, ya está leída
        self.__tercioEVs: list[int | None] = []
        self.__devs: list[float | None] = []
        self.__secuencia: Secuencia | None = None
        self.__tapadas: list[Path] = []
        self.__WBs: list[Path] = []
        self.__zonas: dict[int, Path | None] = {}
        self.__zvs: dict[str, Path] = {}
        self.__wbCtrl: Path | None = None
        self.__balancePersonalizado: bool | None = None
        self.__partes: list[str | None] = []
        self.__enRejilla: list[bool] = []
        self.__celdas: dict[int, list[int]] = {}
        self.__fuera: list[int] = []
        self.__desviadas: list[int] = []
        self.__medioPaso: bool = False
        self.__isoSerie: float | None = None
        self.__isoDistintos: list[int] = []
        self.__tapadasOtroISO: list[int] = []
        self.__tapadasConLuz: list[int] = []
        if self.raws and self.esRead:
            self.__repartir()

        # --- Copias en la carpeta OECF: las hace Copiar ({} hasta entonces)
        self.__copias: dict[Path, Path] = {}
        self.__errorCopia: OSError | None = None

        # --- Teselas de la Z-V: las calcula Seleccionar (None hasta
        #     entonces). Paño: su ventana o por qué no se encontró (KTE)
        self.__tela: Ventana | str | None = None
        self.__select: Select | None = None

        # --- Lo medido en los RAW: lo calcula Medir (None hasta entonces)
        self.__review: Review | None = None

    #
    # --- Propiedades públicas
    #
    # region Propiedades públicas

    #
    @property
    def path(self) -> Path:
        """ Carpeta de la serie. """
        return self.__path

    #
    @property
    def esCarpeta(self) -> bool:
        """ Saber si la carpeta existe. """
        return self.__esCarpeta

    #
    @property
    def puedeLeer(self) -> bool:
        """ Saber si la carpeta existe y hay permiso para leerla. """
        return self.__puedeLeer

    #
    @property
    def puedeEscribir(self) -> bool:
        """
        Saber si hay permiso para escribir en la carpeta (para la carpeta
        OECF). En Windows no siempre se sabe de antemano: si falla al
        copiar, copias queda vacío.
        """
        return self.esCarpeta and os.access(self.path, os.W_OK)

    #
    @property
    def raws(self) -> list[Path]:
        """
        RAW's de la carpeta ([] si no hay). Ordenados por nombre hasta
        leer la serie; después, por fecha de disparo (a igual fecha, por
        nombre; los que no tienen fecha, al final).
        """
        return self.__raws

    #
    @property
    def primera(self) -> str:
        """ Nombre del primer RAW de la carpeta (ver raws). """
        return self.__raws[0].name if self.__raws else ""

    #
    @property
    def cam(self) -> Cam | None:
        """ Saber la cámara: marca y modelo (None si no se leyó). """
        return self.__cam

    #
    @property
    def tomas(self) -> list[Toma]:
        """ Saber las tomas leídas, en el orden de raws ([] si ninguna). """
        return self.__tomas

    #
    @property
    def tercioEVs(self) -> list[int | None]:
        """
        Saber el tercioEV de cada toma: tercios de paso respecto a la Z-V,
        en el orden de raws (None si no se pudo leer; [] hasta leer la
        serie).
        """
        return self.__tercioEVs

    #
    @property
    def devs(self) -> list[float | None]:
        """
        Saber el desvío de cada toma, en tercios: su posición exacta menos
        su tercioEV (None si no se leyó). Es el desvío de los tiempos que
        rotula la cámara, no el del obturador, que solo se ve en el RAW.
        """
        return self.__devs

    #
    @property
    def secuencia(self) -> Secuencia | None:
        """
        Saber las partes de la serie según el protocolo: iniciales, lados,
        cambio, balances, sobrantes y saltos (None hasta leer la serie).
        """
        return self.__secuencia

    #
    @property
    def zonas(self) -> dict[int, Path | None]:
        """
        Saber el RAW de cada zona, de la más oscura a la más clara: las 31,
        con su tercioEV como clave (None si no hay toma; {} hasta leer la
        serie).
        En la ZV, la del cambio de lado o, si no hay, la inicial (ver
        zvs); en las demás, la última que se hizo.
        """
        return self.__zonas

    #
    @property
    def zvs(self) -> dict[str, Path]:
        """
        Saber el RAW de cada Z-V de control, por su papel (KT.ZV_INI,
        KT.ZV_MEDIO, KT.ZV_FIN), solo las que hay: de cada una, la última
        que se hizo (si se repite, es que el estudiante no estaba seguro:
        Tony, 2026-10-19). La inicial, sin la toma del balance
        personalizado (ver wbCtrl). {} hasta leer la serie.
        """
        return self.__zvs

    #
    @property
    def wbCtrl(self) -> Path | None:
        """
        Saber el RAW de la toma del balance personalizado: la primera, si
        la serie empieza con dos Z-V (solo tarjeta, con otro encuadre).
        None si no la hay o hasta leer la serie.
        """
        return self.__wbCtrl

    #
    @property
    def tapadas(self) -> list[Path]:
        """
        Saber los RAW de las tomas tapadas, en orden de disparo: las que
        salieron casi negras (las demás, ver tapadasConLuz).
        """
        return self.__tapadas

    #
    @property
    def tapadasConLuz(self) -> list[int]:
        """
        Saber las tomas tapadas que no salieron casi negras (índices en
        raws): se taparon mal; no sirven para el negro ni se copian.
        """
        return self.__tapadasConLuz

    #
    @property
    def WBs(self) -> list[Path]:
        """
        Saber los RAW de los balances de cámara (WB), en orden de disparo.
        """
        return self.__WBs

    #
    @property
    def balancePersonalizado(self) -> bool | None:
        """
        Saber si se hizo el balance de blancos personalizado inicial: las
        dos primeras tomas, Z-V con balances distintos. None si no se
        puede saber o hasta leer la serie.
        """
        return self.__balancePersonalizado

    #
    @property
    def partes(self) -> list[str | None]:
        """
        Saber la parte de la serie de cada toma, en el orden de raws:
        inicial, control (las Z-V iniciales de más), lado1, cambio, lado2,
        final, tapada, balance o sobrante (None si no se pudo leer; [] hasta
        leer la serie).
        """
        return self.__partes

    #
    @property
    def enRejilla(self) -> list[bool]:
        """
        Saber qué tomas van a la rejilla, en el orden de raws: todas menos
        las tapadas, los balances de cámara y las Z-V iniciales de más
        ([] hasta leer la serie).
        """
        return self.__enRejilla

    #
    @property
    def celdas(self) -> dict[int, list[int]]:
        """
        Saber las tomas de cada posición de la rejilla: {tercioEV: [índices
        en raws]}, solo las posiciones con alguna toma ({} hasta leer la
        serie).
        """
        return self.__celdas

    #
    @property
    def fuera(self) -> list[int]:
        """
        Saber las tomas de la rejilla que no caben en ninguna posición:
        más allá de Z0 o ZX, o que no se pudieron leer (índices en raws).
        """
        return self.__fuera

    #
    @property
    def huecos(self) -> list[int]:
        """
        Saber las posiciones de la rejilla sin ninguna toma (sus tercioEV,
        de la más oscura a la más clara).
        """
        return [t for t in range(-KS.TERCIOS_LADO, KS.TERCIOS_LADO + 1)
                if t not in self.celdas]

    #
    @property
    def repetidas(self) -> dict[int, list[int]]:
        """
        Saber las posiciones con más de una toma, sin contar la ZV, donde
        se esperan varias: {tercioEV: [índices en raws]}.
        """
        return {t: tomas for t, tomas in sorted(self.celdas.items())
                if (t != 0) and (len(tomas) > 1)}

    #
    @property
    def isoSerie(self) -> float | None:
        """
        Saber el ISO de la serie: el de la ZV (None si no se leyó o hasta
        leer la serie).
        """
        return self.__isoSerie

    #
    @property
    def isoDistintos(self) -> list[int]:
        """
        Saber las tomas de la serie (iniciales, lados, cambio y final) con
        un ISO distinto del de la ZV (índices en raws). Si hay alguna, no
        se puede analizar.
        """
        return self.__isoDistintos

    #
    @property
    def tapadasOtroISO(self) -> list[int]:
        """
        Saber las tomas tapadas con un ISO distinto del de la ZV (índices
        en raws). No impiden analizar.
        """
        return self.__tapadasOtroISO

    #
    @property
    def desviadas(self) -> list[int]:
        """
        Saber las tomas de la rejilla cuyo desvío pasa de KP.DEV_MAX
        (índices en raws). No impiden analizar.
        """
        return self.__desviadas

    #
    @property
    def tela(self) -> Ventana | str | None:
        """
        Saber la ventana del paño en la Z-V o, si no se encontró, por qué
        (KTE). None hasta Seleccionar.
        """
        return self.__tela

    #
    @property
    def select(self) -> Select | None:
        """
        Saber las teselas de tarjeta de la Z-V: buenas y rechazadas, con
        su motivo (valen para toda la serie). None hasta Seleccionar.
        """
        return self.__select

    #
    @property
    def exportaciones(self) -> dict[int, Path]:
        """
        Saber las exportaciones del revelador: las TIFF con el nombre de
        una zona (ver NombreZona), junto a su RAW en la subcarpeta ZONAS
        o, si se guardaron solas con el JSON, en la carpeta (Tony,
        2026-10-19); si una está en las dos, la de ZONAS. {tercioEV:
        ruta}. No hace falta haber leído la serie.
        """
        por_nombre: dict[str, Path] = {}
        for donde in (self.carpeta, self.carpeta / self.KT.CARPETA_ZONAS):
            if donde.is_dir():
                por_nombre.update({
                    p.stem.upper(): p for p in donde.iterdir()
                    if p.suffix.lower() in KCOM.EXTENSIONES_TIFF})
        exportaciones = {}
        for tercioEV in range(-KS.TERCIOS_LADO, KS.TERCIOS_LADO + 1):
            ruta = por_nombre.get(self.NombreZona(tercioEV).upper())
            if ruta is not None:
                exportaciones[tercioEV] = ruta
        return exportaciones

    #
    @property
    def review(self) -> Review | None:
        """
        Saber lo medido en los RAW de la serie: teselas, paño, negro,
        ruido y cada zona (ver Review). None hasta Medir.
        """
        return self.__review

    #
    @property
    def esAnalizable(self) -> bool:
        """
        Saber si la serie se puede analizar: de Z1 a Z9, ninguna zona sin
        toma (las de zonas, que son las que se copian; por pasos enteros,
        solo las enteras), el mismo ISO en toda la serie y que no sea por
        medios pasos. Las repetidas no lo impiden.
        """
        if (not self.zonas) or self.isoDistintos or self.medioPaso:
            return False
        return all(self.zonas[t] is not None for t in self.zonas
                   if self.EsNecesaria(t))

    #
    @property
    def paso(self) -> int:
        """
        Saber los tercios de cada paso de los lados: 1 (por tercios) o
        KP.TERCIOS (por pasos enteros, sin tercios). 1 hasta leer la serie.
        """
        return self.secuencia.paso if self.secuencia else 1

    #
    @property
    def medioPaso(self) -> bool:
        """
        Saber si la serie se hizo por medios pasos: no se puede analizar
        (Tony, 2026-10-19). False hasta leer la serie.
        """
        return self.__medioPaso

    #
    @property
    def carpeta(self) -> Path:
        """
        Saber la carpeta de las copias de la serie: OECF, dentro de la de
        la serie (con el JSON en su raíz). En una serie restaurada, la que
        se eligió, se llame como se llame (ver Restaurar).
        """
        return self.__carpeta

    #
    @property
    def copiasEnSitio(self) -> bool:
        """
        Saber si están todas las copias (las RAW de ZONAS y CTRL): sin
        ellas no se puede medir. En una serie restaurada pueden faltar si
        solo se guardó el JSON con las exportaciones del revelador (Tony,
        2026-10-19).
        """
        return bool(self.copias) and all(copia.is_file()
                                          for copia in self.copias.values())

    #
    @property
    def carpetaCtrl(self) -> Path:
        """
        Saber la subcarpeta de control de la carpeta OECF: CTRL, con los
        balances de cámara, las tapadas, las Z-V de control y las
        incidencias.
        """
        return self.carpeta / self.KT.CARPETA_CTRL

    #
    @property
    def carpetaAnalisis(self) -> Path:
        """
        Saber la subcarpeta de la carpeta OECF con lo que escribe el
        análisis: ANALISIS, con el libro, la ficha y las láminas.
        """
        return self.carpeta / self.KT.CARPETA_ANALISIS

    #
    @property
    def copias(self) -> dict[Path, Path]:
        """
        Saber la copia de cada RAW que se copió a la carpeta OECF:
        {original: copia} ({} hasta copiar o si la copia falló).
        """
        return self.__copias

    #
    @property
    def zonasCopia(self) -> dict[int, Path | None]:
        """
        Saber la copia de cada zona, en la subcarpeta ZONAS: las mismas
        claves que zonas, con la copia en vez del RAW ({} hasta copiar o
        si la copia falló). Con las zonas se trabaja siempre en sus
        copias (Tony, 2026-10-19).
        """
        if not self.copias:
            return {}
        return {tercioEV: (self.copias.get(raw) if (raw is not None)
                           else None)
                for tercioEV, raw in self.zonas.items()}

    #
    @property
    def errorCopia(self) -> OSError | None:
        """
        Saber el error del sistema que paró la última copia (None si no
        hubo): borrar la carpeta OECF anterior, crearla o copiar un RAW.
        """
        return self.__errorCopia

    #
    @property
    def esRead(self) -> bool:
        """ Saber si ya están leídas todas las tomas de la serie. """
        return len(self.tomas) == len(self.raws)

    #
    @property
    def ZV(self) -> Exp | None:
        """
        Saber la exposición de la Z-V, la referencia de la serie
        (None si no se leyó).
        """
        return self.tomas[0].exp if self.tomas else None

    #
    @property
    def bits(self) -> int | None:
        """
        Saber la profundidad de bits de los RAW de la serie: la de la Z-V
        (12, 14…; None si no se leyó).
        """
        return self.tomas[0].bits if self.tomas else None

    #
    @property
    def fecha(self) -> datetime | None:
        """ Saber la fecha y hora de disparo de la Z-V (None si no se leyó).
        """
        return self.tomas[0].fecha if self.tomas else None

    # endregion Propiedades públicas

    #
    # --- Métodos públicos
    #
    # region Métodos públicos

    #
    def EsNecesaria(self, tercioEV: int) -> bool:
        """
        Saber si una posición (tercioEV) es necesaria para analizar: de
        Z1 a Z9, con sus tercios (por pasos enteros, sin ellos).
        """
        kt = self.KT
        desde = (kt.ZONA_MIN_REVIEW - KP.ZONA_REF) * KP.TERCIOS
        hasta = (kt.ZONA_MAX_REVIEW - KP.ZONA_REF) * KP.TERCIOS
        return (desde <= tercioEV <= hasta) and ((tercioEV % self.paso) == 0)

    #
    def RellenarTercios(self, rutas: dict[int, Path | None]
                        ) -> dict[int, Path]:
        """
        Rutas por tercioEV (zonasCopia, exportaciones…) sin las vacías y,
        en una serie por pasos enteros, cada tercio sin ruta con la de su
        zona entera (Z03-3 y Z03-7, la de Z03), si la hay: así la lámina
        tiene todos sus cuadros (Tony, 2026-10-19). Por tercios, como
        vienen.
        """
        llenas = {t: ruta for t, ruta in rutas.items() if ruta is not None}
        if self.paso != KP.TERCIOS:
            return llenas
        for tercioEV in range(-KS.TERCIOS_LADO, KS.TERCIOS_LADO + 1):
            entera = tercioEV - zona_tercio(tercioEV)[1]
            if (tercioEV not in llenas) and (entera in llenas):
                llenas[tercioEV] = llenas[entera]
        return dict(sorted(llenas.items()))

    #
    def Leer(self) -> Iterator[int]:
        """
        Lee las tomas que faltan, una cada vez y abriendo cada RAW una sola
        vez (la primera ya se leyó al crear el objeto). Tras cada una dice
        cuántas lleva: se pueden ir pidiendo con next() para mostrar el
        progreso sin congelarse, o leerlas todas seguidas con un for. Si
        ya están todas, no lee nada. Al terminar, ordena raws y tomas por
        fecha de disparo y reparte la serie.
        """
        # --- Al leer la última, se ordena y se reparte la serie ANTES de
        #     su yield: quien lee con next() deja de pedir cuando ya están
        #     todas, y lo que fuera detrás del último yield no se
        #     ejecutaría nunca
        for raw in self.raws[len(self.tomas):]:
            self.__tomas.append(self.__leer_toma(raw))
            if self.esRead:
                self.__ordenar()
                self.__repartir()
            yield len(self.tomas)

    #
    def Seleccionar(self) -> None:
        """
        Mide las teselas de la Z-V: busca el paño y elige las teselas
        buenas de la tarjeta (ver tela y select), en su copia. Sin Z-V
        copiada, sin paño ni tarjeta.
        """
        zv = self.zonasCopia.get(0)
        if zv is None:
            self.__tela = KTE.SIN_TELA
            self.__select = None
            return
        teselas = medir_teselas(zv)
        self.__tela = buscar_tela(teselas)
        self.__select = seleccionar(
            teselas, self.__tela if isinstance(self.__tela, Ventana)
            else None)

    #
    def Medir(self) -> Iterator[tuple[int, int]]:
        """
        Mide la serie en las copias, una toma cada vez: las 31 zonas y
        las demás Z-V de control (ver zvs), en las teselas buenas de la
        Z-V (antes, Seleccionar, si no se hizo). Dice cuántas lleva y
        cuántas son (para el progreso), empezando por (0, total) antes de
        medir nada (ver Copiar), y después tras cada una. Al terminar, el
        resultado en review.
        """
        if self.select is None:
            self.Seleccionar()
        select, zv, tela_zv = self.select, self.zonas.get(0), self.tela
        if (select is None) or (zv is None) or (tela_zv is None):
            return
        tela = tela_zv if isinstance(tela_zv, Ventana) else None

        # --- Z-V de control: las demás de zvs (inicial, cambio y final; de
        #     cada una, la última). La del balance personalizado no: solo
        #     tarjeta y con otro encuadre (sus teselas caerían en otro
        #     sitio)
        otras = [raw for raw in self.zvs.values() if raw != zv]
        tomas = [(t, raw) for t, raw in sorted(self.zonas.items())
                 if raw is not None] + [(0, raw) for raw in otras]

        # --- Primero, cuántas son; luego, el negro, el ruido y la matriz
        #     de la Z-V (que también tardan) y cada toma
        yield 0, len(tomas)
        zv_copia = self.__copia(zv)
        oscuro = oscuridad(zv_copia,
                           [self.__copia(raw) for raw in self.tapadas])
        matriz = matriz_color(zv_copia)

        # --- Cada toma: la tarjeta, su paño (con su histograma, para
        #     contar los recortados al final) y la temperatura
        medidas = []
        for hechas, (tercio_ev, raw) in enumerate(tomas, 1):
            medidas.append((tercio_ev, raw, medir_toma(
                self.__copia(raw), select, oscuro.negro, tela)))
            if hechas < len(tomas):
                yield hechas, len(tomas)

        # --- Sin tapadas, el negro declarado puede quedarse corto: lo que
        #     le falta se estima en las sombras de la serie y se resta
        if oscuro.origen_negro == KTE.ORIGEN_DECLARADO:
            exceso = exceso_negro([(t, m) for t, _, m
                                   in medidas[:len(medidas) - len(otras)]])
            if exceso is not None:
                negro = list(oscuro.negro)
                for c, e in zip(medidas[0][2].canales, exceso):
                    negro[int(c[1:])] += e
                oscuro = oscuro._replace(negro=tuple(negro),
                                         origen_negro=KTE.ORIGEN_SOMBRAS)
                medidas = [(t, raw, restar_exceso(m, exceso))
                           for t, raw, m in medidas]

        # --- Recortados en el paño: los que llegan a UMBRAL_RECORTE del
        #     máximo de la tarjeta de su canal en la serie
        topes = {c: max(m.nivel[i] for _, _, m in medidas)
                 for i, c in enumerate(medidas[0][2].canales)}
        zonas: dict[int, ZonaMedida] = {}
        control: list[ZonaMedida] = []
        for n, (tercio_ev, raw, m) in enumerate(medidas):
            nivel = dict(zip(m.canales, m.nivel))

            recortado = {} if (m.tela is None) else {
                c: part_recortada(h, oscuro.negro[int(c[1:])]
                                  +
                                  (KCOM.UMBRAL_RECORTE * topes[c]))

                for c, h in zip(m.canales, m.tela.histograma)}

            copia = self.copias.get(raw)
            zona = ZonaMedida(
                tercio_ev=tercio_ev,
                archivo=raw.name,
                copia=copia.name if copia else None,
                nivel=nivel,
                disp=dict(zip(m.canales, m.disp)),
                tela_nivel={} if (m.tela is None) else dict(
                    zip(m.canales, m.tela.nivel)),
                tela_disp={} if (m.tela is None) else dict(
                    zip(m.canales, m.tela.disp)),
                tela_recortado=recortado,
                dev=tuple(float(x) for x in m.dev_rechazadas))
            if n < (len(medidas) - len(otras)):
                zonas[tercio_ev] = zona
            else:
                control.append(zona)

        # --- Curva de transferencia del ruido, con las zonas. Si el ruido
        #     de lectura no se midió (sin borde ni tapadas), sale de ella
        curvas = ajustar_transferencia(list(zonas.values()))
        if oscuro.ruido is None:
            lecturas = [math.nan] * len(oscuro.negro)
            for canal, curva in curvas.items():
                lecturas[int(canal[1:])] = curva.lectura
            if not all(math.isnan(x) for x in lecturas):
                oscuro = oscuro._replace(ruido=tuple(lecturas),
                                         origen_ruido=KTE.ORIGEN_CURVA)

        # --- Ruido aleatorio en la Z-V, con la primera Z-V de control de
        #     su misma luz (la que no se desvía: ver
        #     Review.controlesDesviados)
        zona_zv = zonas.get(0)
        pareja = next((
            raw for raw, z in zip(otras, control)
            if zona_zv and (zona_zv.nivelRGB[1] > 0) and (z.nivelRGB[1] > 0)
            and (abs(math.log2(z.nivelRGB[1] / zona_zv.nivelRGB[1]))
                 <= KCOM.TOLERANCIA_LINEAL)), None)
        aleatorio = (ruido_temporal(zv_copia, self.__copia(pareja), select,
                                    oscuro.negro)
                     if pareja else None)

        # --- Tomas de balance de la cámara: los Kelvin que guarda y los
        #     que de verdad aplica (la luz que sus multiplicadores dejan
        #     neutra: la inversa de cada uno). Las copiadas: sin repetidos
        balances = []
        for i in self.__balances_sin_repetir():
            raw, toma = self.raws[i], self.tomas[i]
            wb = toma.WB
            kelvin: float | None = None
            if wb:
                rojo, verde, azul = (1 / x for x in wb[:KCOM.CANALES_RGB])
                kelvin = temperatura(rojo, verde, azul, matriz)
            balances.append(BalanceMedido(
                archivo=raw.name,
                nombre=toma.nombreWB,
                kelvin_cam=toma.kelvin,
                kelvin=kelvin,
                multiplicadores=tuple(float(x) for x in wb) if wb else None))

        alto, ancho = self.__medida(zv_copia)
        exp_zv = self.ZV
        self.__review = Review(
            lado=KTE.LADO,
            alto=alto,
            ancho=ancho,
            motivos=select.motivo,
            tela=tela_zv,
            negro=oscuro.negro,
            origen_negro=oscuro.origen_negro,
            ruido=oscuro.ruido,
            origen_ruido=oscuro.origen_ruido,
            ruido_borde=oscuro.ruido_borde,
            ruido_tapadas=oscuro.ruido_tapadas,
            difieren=oscuro.difieren,
            matriz=tuple(tuple(float(x) for x in fila) for fila in matriz),
            zonas=tuple(zonas.get(t) for t in sorted(self.zonas)),
            control=tuple(control),
            cam=self.cam.nombre if self.cam else "",
            fecha=self.fecha.isoformat() if self.fecha else None,
            f=exp_zv.f if exp_zv else None,
            tv=exp_zv.tv if exp_zv else None,
            iso=exp_zv.iso if exp_zv else None,
            balances=tuple(balances),
            bits=self.bits,
            transferencia=curvas or None,
            aleatorio=aleatorio)
        yield len(tomas), len(tomas)

    #
    @classmethod
    def Restaurar(cls, carpeta: Path, archivos: list[str],
                  tomas: list[Toma], copias: dict[str, str],
                  cam: Cam | None = None) -> "OECF":
        """
        Serie ya preparada, sin leer ningún RAW (los originales pueden no
        estar: Tony, 2026-10-19): carpeta, la de sus copias (la OECF, o la
        que se guardó con su JSON, se llame como se llame); archivos y
        tomas, los de cada toma en orden de disparo (los nombres de los
        originales y sus datos, como los dejó Leer); copias, {archivo:
        copia}, la copia relativa a la carpeta de la serie (la que
        contiene a carpeta). El primer componente de esa ruta es el nombre
        que tenía la carpeta al grabar el JSON y no se usa: el resto se
        cuelga de carpeta, se llame como se llame (Tony, 2026-10-22). Se
        reparte como al leerla, así que zonas,
        zvs, tapadas… salen igual. La cámara, de la primera copia que
        esté o, si no hay ninguna, cam. Puede faltar alguna copia (ver
        copiasEnSitio).
        """
        path = carpeta.parent
        oecf = cls(path, buscar=False)
        oecf.__carpeta = carpeta
        oecf.__raws = [path / archivo for archivo in archivos]
        oecf.__tomas = list(tomas)
        oecf.__copias = {path / archivo: carpeta.joinpath(
                             *Path(copia).parts[1:])
                         for archivo, copia in copias.items()}
        primera = next((copia for copia in oecf.__copias.values()
                        if copia.is_file()), None)
        oecf.__cam = leer_cam(primera) if primera else cam
        if oecf.raws:
            oecf.__repartir()
        return oecf

    #
    @staticmethod
    def NombreZona(tercioEV: int) -> str:
        """
        Nombre de la copia de una zona, sin extensión: Z00, Z00-3, Z00-7,
        … Z05 (la ZV) … Z10. Las exportaciones del revelador se llaman
        igual.
        """
        kt = OECF.KT
        ev, tercio = zona_tercio(tercioEV)
        return (f"{KP.PREFIJO}{ev:0{kt.CIFRAS_ZONA}d}"
                f"{kt.TERCIOS_ZONA[tercio]}")

    #
    def Copiar(self) -> Iterator[tuple[int, int]]:
        """
        Copia a la carpeta OECF las tomas que sirven, con su nombre y
        cada una en la subcarpeta de su papel: una por zona (ZONAS), y
        los balances de cámara sin repetidos, las tapadas, la toma del
        balance personalizado y las Z-V de control (CTRL; la ZV va
        también en ZONAS, como su zona). Solo el RAW, copia exacta: los
        originales no se tocan. Antes vacía la carpeta OECF anterior, si
        la hay, salvo las exportaciones del revelador y las subcarpetas
        del usuario (ver Vaciar). Copia una cada vez y dice cuántas lleva y
        cuántas son, (hechas, total), empezando por (0, total): se pueden
        ir pidiendo con next() para mostrar el progreso sin congelarse, o
        copiarlas todas seguidas con un for. Al terminar, copias dice la
        copia de cada RAW (la de la ZV, la de ZONAS); si la serie aún no
        está leída o algo falla, se para y copias queda vacío (y, si fue
        el sistema, errorCopia dice por qué).
        """
        self.__copias = {}
        self.__errorCopia = None
        if (not self.raws) or (not self.esRead):
            return
        kt = self.KT

        # --- Ruta de cada copia, sin extensión: (RAW, subcarpeta/nombre).
        #     La ZV sale dos veces: primero en ZONAS, que es la que apunta
        #     copias
        zonas = self.carpeta / kt.CARPETA_ZONAS
        ctrl = self.carpetaCtrl
        nombres: list[tuple[Path, Path]] = []
        for tercioEV, raw in self.zonas.items():
            if raw is not None:
                nombres.append((raw, zonas / self.NombreZona(tercioEV)))
        for papel, raw in self.zvs.items():
            nombres.append((raw, ctrl / f"{texto_zona(0)}"
                                        f"{kt.SEP_NOMBRE}{papel}"))
        if self.wbCtrl is not None:
            nombres.append((self.wbCtrl, ctrl / kt.NOMBRE_WB_CTRL))
        for n, raw in enumerate(self.tapadas, 1):
            nombres.append((raw, ctrl / f"{kt.PREFIJO_TAPADA}{n}"))
        for n, i in enumerate(self.__balances_sin_repetir(), 1):
            nombres.append((self.raws[i],
                            ctrl / self.__nombre_balance(n, i)))

        destinos = [(raw, ruta.with_name(f"{ruta.name}{raw.suffix}"))
                    for raw, ruta in nombres]
        copias: dict[Path, Path] = {}
        for raw, copia in destinos:
            copias.setdefault(raw, copia)
        total = len(destinos)
        try:
            if self.carpeta.is_dir():
                self.Vaciar()
            else:
                self.carpeta.mkdir()
            # --- CTRL y ANALISIS, siempre: en ellas escriben las
            #     incidencias y el análisis
            for subcarpeta in ({copia.parent for _, copia in destinos}
                               | {self.carpetaCtrl, self.carpetaAnalisis}):
                subcarpeta.mkdir(exist_ok=True)
        except OSError as e:
            self.__errorCopia = e
            return
        yield 0, total

        # --- Las copias se apuntan solo si se hicieron todas, y ANTES del
        #     último yield (ver Leer)
        for hechas, (raw, copia) in enumerate(destinos, 1):
            try:
                shutil.copy2(raw, copia)
            except OSError as e:
                self.__errorCopia = e
                return
            if hechas == total:
                self.__copias = copias
            yield hechas, total

    #
    def Vaciar(self) -> None:
        """
        Vacía la carpeta OECF para prepararla de nuevo: borra lo que hizo
        el programa (copias, JSON, incidencias, libro, ficha, láminas),
        también dentro de sus subcarpetas (ZONAS, CTRL y ANALISIS, que
        borra si quedan vacías), y conserva las TIFF (las exportaciones del
        revelador: Tony, 2026-10-16) y las demás subcarpetas (son del
        usuario).
        """
        kt = self.KT
        propias = {kt.CARPETA_ZONAS, kt.CARPETA_CTRL, kt.CARPETA_ANALISIS}
        for ruta in self.carpeta.iterdir():
            if not ruta.is_dir():
                self.__borrar(ruta)
            elif ruta.name in propias:
                for archivo in ruta.iterdir():
                    if not archivo.is_dir():
                        self.__borrar(archivo)
                if not any(ruta.iterdir()):
                    ruta.rmdir()

    #
    @staticmethod
    def TextoF(diafragma: float) -> str:
        """ Diafragma como texto, sin ceros sobrantes: 9, 5.6. """
        return f"{round(diafragma, OECF.KT.DECIMALES_F):g}"

    #
    @staticmethod
    def TextoTV(segundos: float) -> str:
        """ Tiempo como lo marca la cámara: 1/125 s, o 2 s si pasa del
            segundo. """
        if segundos < 1:
            return f"1/{round(1 / segundos)} {OECF.KT.SEGUNDOS}"
        return f"{segundos:g} {OECF.KT.SEGUNDOS}"

    #
    @staticmethod
    def TextoISO(iso: float) -> str:
        """ ISO como texto, en número entero: 100. """
        return str(round(iso))

    #
    @staticmethod
    def TextoExp(f: float | None, tv: float | None, iso: float | None,
                 rotulos: tuple[str, ...]) -> str:
        """
        Exposición en un solo texto, como la marca la cámara: «f/9 · Tv
        1/125 s · ISO 100». rotulos: los de f, Tv e ISO, en ese orden y
        ya traducidos (KXL.ROTULOS_EXP). Lo que falta no sale.
        """
        rotulo_f, rotulo_tv, rotulo_iso = rotulos
        trozos = (
            (f"{rotulo_f}{OECF.TextoF(f)}" if (f is not None) else ""),
            (f"{rotulo_tv} {OECF.TextoTV(tv)}" if (tv is not None) else ""),
            (f"{rotulo_iso} {OECF.TextoISO(iso)}"
             if (iso is not None) else ""))
        return OECF.KT.SEPARADOR.join(t for t in trozos if t)

    # endregion Métodos públicos

    #
    # --- Métodos privados
    #
    # region Métodos privados

    # --- Copia de un RAW de la serie (o el propio RAW, si no se copió)
    def __copia(self, raw: Path) -> Path:
        return self.copias.get(raw, raw)

    #
    # --- Borra un archivo que hizo el programa: no las TIFF, que son las
    #     exportaciones del revelador (ver Vaciar)
    @staticmethod
    def __borrar(archivo: Path) -> None:
        if archivo.suffix.lower() not in KCOM.EXTENSIONES_TIFF:
            archivo.unlink()

    #
    # --- Balances de cámara que se copian, en orden de disparo
    #     (índices de raws): de los repetidos (mismo nombre y mismos
    #     multiplicadores), solo el último (Tony, 2026-10-19)
    def __balances_sin_repetir(self) -> list[int]:
        ultimo: dict[tuple[str | None, tuple[float, ...] | None], int] = {}
        for i in self.secuencia.balances:                       # type: ignore
            toma = self.tomas[i]
            ultimo[(toma.nombreWB, toma.WB)] = i
        return sorted(ultimo.values())

    #
    # --- Nombre de la copia del balance de cámara n.º n (la toma i), sin
    #     extensión: WB-01, con el nombre del balance si lo hay
    #     (WB-03-INCANDESCENT) y, si es de Kelvin a mano, sus K
    #     (WB-01-KELVIN-5600K)
    def __nombre_balance(self, n: int, i: int) -> str:
        kt = self.KT
        toma = self.tomas[i]
        nombre = f"{kt.PREFIJO_BALANCE}{n:0{kt.CIFRAS_BALANCE}d}"
        if toma.nombreWB:
            limpio = re.sub(kt.REGEX_RARO, kt.SEP_NOMBRE,
                            toma.nombreWB.upper()).strip(kt.SEP_NOMBRE)
            nombre = f"{nombre}{kt.SEP_NOMBRE}{limpio}"
            if (toma.nombreWB == KM.B_KELVIN) and (toma.kelvin is not None):
                nombre = (f"{nombre}{kt.SEP_NOMBRE}{toma.kelvin}"
                          f"{KM.UNIDAD_KELVIN}")
        return nombre

    #
    # --- RAW de la carpeta, ordenados por nombre (lista vacía si no hay).
    #     El definitivo, por fecha, lo pone __ordenar al leer la serie
    def __buscar_raw(self) -> list[Path]:
        return sorted(p for p in self.path.iterdir()
                      if p.is_file()
                      and (p.suffix.lower() in KCOM.EXTENSIONES))

    #
    # --- Con la serie leída, ordena raws y tomas por fecha de disparo: el
    #     nombre puede engañar (el contador de la cámara da la vuelta en
    #     9999, archivos renombrados, dos tarjetas). Ver __clave_orden
    def __ordenar(self) -> None:
        pares = sorted(zip(self.raws, self.tomas), key=OECF.__clave_orden)
        self.__raws = [raw for raw, _ in pares]
        self.__tomas = [toma for _, toma in pares]

    #
    # --- Clave del orden de una toma: primero las que tienen fecha, por
    #     fecha; a igual fecha (resolución de 1 s), por nombre
    @staticmethod
    def __clave_orden(par: tuple[Path, Toma]) -> tuple[bool, datetime, str]:
        raw, toma = par
        return toma.fecha is None, toma.fecha or datetime.min, raw.name

    #
    # --- Medida visible del sensor: alto y ancho (los de las teselas)
    @staticmethod
    def __medida(archivo: Path) -> tuple[int, int]:
        with rawpy.imread(str(archivo)) as raw:
            return raw.sizes.height, raw.sizes.width

    #
    # --- Lee una toma abriendo su RAW una sola vez: exposición, fecha de
    #     disparo y balance de blancos y, solo si es al tiempo de las
    #     tapadas, si está tapada (mirar la imagen es lo lento). Si el RAW
    #     no se puede leer, todo None y no tapada
    @staticmethod
    def __leer_toma(archivo: Path) -> Toma:
        try:
            with rawpy.imread(str(archivo)) as raw:
                otros = raw.other
                exp = Exp(
                    f=float(otros.aperture),
                    tv=float(otros.shutter_speed),
                    iso=float(otros.iso_speed))
                # --- Balance de blancos: multiplicadores con el verde a 1,
                #     para comparar marcas (Canon los da en bruto)
                bruto = [float(m) for m in raw.camera_whitebalance]
                verde = bruto[OECF.KT.CANAL_VERDE] or 1
                wb = tuple(round(m / verde, OECF.KT.DECIMALES_WB)
                           for m in bruto)

                # --- Tapada: por su exposición. Y, solo entonces, su
                #     brillo: media del RAW sobre el nivel de negro, en
                #     tanto por uno del rango útil
                tapada = (math.isclose(exp.tv, OECF.KT.TV_TAPADA,
                                       rel_tol=KCOM.MARGEN_TV)
                          and math.isclose(exp.f, OECF.KT.F_TAPADA,
                                           rel_tol=OECF.KT.MARGEN_F_TAPADA))
                oscura = False
                if tapada:
                    negro = sum(raw.black_level_per_channel) / len(
                        raw.black_level_per_channel)
                    brillo = ((raw.raw_image_visible.mean() - negro)
                              / (raw.white_level - negro))
                    oscura = bool(brillo < OECF.KT.BRILLO_TAPADA)

                fecha = otros.timestamp

                # --- Profundidad de bits: los que hacen falta para el
                #     nivel de blanco (16383 → 14), menos los últimos que
                #     no usa ningún valor: algunas cámaras (Sony) guardan
                #     12 bits reescalados a 14, todos múltiplos de 4
                usados = int(np.bitwise_or.reduce(
                    raw.raw_image_visible, axis=None))
                sobran = (((usados & -usados).bit_length() - 1)
                          if usados else 0)
                bits = int(raw.white_level).bit_length() - sobran
        except (rawpy.LibRawError, OSError):                    # type: ignore
            return Toma(
                exp=None,
                fecha=None,
                WB=None,
                tapada=False,
                oscura=False,
                nombreWB=None,
                bits=None,
                kelvin=None)
        return Toma(
            exp=exp,
            fecha=fecha,
            WB=wb,
            tapada=tapada,
            oscura=oscura,
            nombreWB=leer_balance(archivo),
            bits=bits,
            kelvin=leer_kelvin(archivo))

    #
    # --- Reparte la serie ya leída: el tercioEV de cada toma respecto a la
    #     primera que se pudo leer (la Z-V), sus partes según el protocolo,
    #     las tapadas, los WB, las Z-V de control (ver zvs y wbCtrl) y una
    #     toma por zona (ver la property zonas). Las sobrantes no van a
    #     ninguna zona
    def __repartir(self) -> None:
        relativas = [exp_relativa(t.exp.tv, t.exp.f, t.exp.iso) if t.exp
                     else None for t in self.tomas]
        reads = [e for e in relativas if e is not None]
        exactos = [calcular_tercio_exacto(e, reads[0]) if (e is not None)
                   else None for e in relativas]
        self.__tercioEVs = [round(x) if (x is not None) else None
                            for x in exactos]
        self.__devs = [(x - t)
                       if ((x is not None) and (t is not None)) else None
                       for x, t in zip(exactos, self.tercioEVs)]

        partes = self.__secuencia = secuencia(
            self.tercioEVs, [t.tapada for t in self.tomas],
            [t.WB for t in self.tomas])
        self.__tapadas = [self.raws[i] for i in partes.tapadas
                          if self.tomas[i].oscura]
        self.__tapadasConLuz = [i for i in partes.tapadas
                                if not self.tomas[i].oscura]
        self.__WBs = [self.raws[i] for i in partes.balances]

        # --- Z-V de control, de cada una la última (índices en raws). Si
        #     la serie empieza con dos Z-V, la primera es la del balance
        #     personalizado y la inicial es la última de las demás
        kt = self.KT
        iniciales = partes.iniciales
        wb_ctrl = iniciales[0] if (len(iniciales) >= KS.INICIALES) else None
        ini = iniciales[-1] if iniciales else None
        papeles = {kt.ZV_INI: ini,
                   kt.ZV_MEDIO: partes.cambios[-1] if partes.cambios else None,
                   kt.ZV_FIN: partes.finales[-1] if partes.finales else None}
        self.__zvs = {papel: self.raws[i] for papel, i in papeles.items()
                      if i is not None}
        self.__wbCtrl = self.raws[wb_ctrl] if (wb_ctrl is not None) else None

        # --- Las 31 zonas, vacías; la ZV (ver Secuencia) y, después, los
        #     lados en orden de disparo: si una zona se repite, queda la
        #     última
        zonas: dict[int, Path | None] = {
            tercioEV: None
            for tercioEV in range(-KS.TERCIOS_LADO, KS.TERCIOS_LADO + 1)}
        zv = partes.zv
        if zv is not None:
            zonas[0] = self.raws[zv]
        for lado in partes.lados:
            for i in lado:
                zonas[self.tercioEVs[i]] = self.raws[i]         # type: ignore
        self.__zonas = zonas

        # --- Balance personalizado: el de las Z-V iniciales del protocolo
        self.__balancePersonalizado = balance_personalizado(
            self.tercioEVs, [t.WB for t in self.tomas[:KS.INICIALES]])

        # --- Parte de cada toma. Si una toma está en varias, gana la
        #     última de esta lista. Iniciales de más: las repetidas (todas
        #     menos la del balance personalizado y la última)
        de_mas = set(iniciales) - {wb_ctrl, ini}
        nombres: dict[int, str] = {
            i: kt.PARTE_CONTROL if (i in de_mas) else kt.PARTE_INICIAL
            for i in partes.iniciales}
        for n, lado in enumerate(partes.lados, 1):
            nombres.update({i: f"{kt.PARTE_LADO}{n}" for i in lado})
        nombres.update({i: kt.PARTE_CAMBIO for i in partes.cambios})
        nombres.update({i: kt.PARTE_FINAL for i in partes.finales})
        nombres.update({i: kt.PARTE_TAPADA for i in partes.tapadas})
        nombres.update({i: kt.PARTE_BALANCE for i in partes.balances})
        nombres.update({i: kt.PARTE_SOBRANTE for i in partes.sobrantes})
        self.__partes = [nombres.get(i) for i in range(len(self.tomas))]

        # --- A la rejilla, todas menos tapadas, balances de cámara y Z-V
        #     iniciales de más; en cada posición, sus tomas en orden de
        #     disparo, y fuera, las que no caben o no se leyeron
        quitar = set(partes.balances) | set(partes.tapadas) | de_mas
        self.__enRejilla = [i not in quitar for i in range(len(self.tomas))]
        celdas: dict[int, list[int]] = {}
        fuera: list[int] = []
        for i, (tercioEV, va) in enumerate(zip(self.tercioEVs,
                                               self.enRejilla)):
            if not va:
                continue
            if (tercioEV is None) or (abs(tercioEV) > KS.TERCIOS_LADO):
                fuera.append(i)
            else:
                celdas.setdefault(tercioEV, []).append(i)
        self.__celdas = celdas
        self.__fuera = fuera

        # --- Desviadas: las de la rejilla que se apartan de su tercio
        self.__desviadas = [i for i, (d, va) in enumerate(
            zip(self.devs, self.enRejilla))
            if va and (d is not None) and (abs(d) > KP.DEV_MAX)]

        # --- Por medios pasos: en los lados, al menos PARTE_MEDIOS de las
        #     tomas se apartan medio tercio del suyo
        de_lados = [self.devs[i] for lado in partes.lados for i in lado]
        medias = [d for d in de_lados if (d is not None) and (
            abs(abs(d) - kt.DESVIO_MEDIO) <= kt.MARGEN_MEDIO)]
        self.__medioPaso = bool(de_lados) and (
            len(medias) >= (kt.PARTE_MEDIOS * len(de_lados)))

        # --- ISO: el de la ZV. Las tomas de la serie con otro ISO impiden
        #     analizar; las tapadas con otro, solo se avisan
        exp_zv = self.tomas[zv].exp if (zv is not None) else None
        iso = self.__isoSerie = exp_zv.iso if exp_zv else None
        serie = sorted(set(partes.iniciales) | set(partes.cambios)
                       | set(partes.finales)
                       | {i for lado in partes.lados for i in lado})
        self.__isoDistintos = [i for i in serie if (iso is not None)
                               and self.__otro_iso(i, iso)]
        self.__tapadasOtroISO = [i for i in partes.tapadas if (iso is not None)
                                 and self.__otro_iso(i, iso)]

    #
    # --- ¿La toma i tiene un ISO distinto de iso? (No, si no se leyó)
    def __otro_iso(self, i: int, iso: float) -> bool:
        exp = self.tomas[i].exp
        return (exp is not None) and (round(exp.iso) != round(iso))

    # endregion Métodos privados
