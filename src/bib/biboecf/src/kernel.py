# -*- coding: utf-8 *-*
"""
    :Propósito: El objeto OECF, entrada de la biblioteca BibOECF: la serie
                de tomas de una carpeta
    :Autor:     Tony Diana
    :Versión:   26.10.09
"""

# cSpell:ignore biboecf, imread, kcom, rawpy, whitebalance

__all__ = ["Exp", "Toma", "OECF"]

# --- Bibliotecas estándar Python
import math
import shutil
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

# --- Bibliotecas externas
import rawpy

# --- Bibliotecas internas
from bib import std
from .cam import Cam, leer_cam
from .constantes import COM as KCOM
from .secuencia import KS, Secuencia, balance_personalizado, secuencia
from .zonas import KP, calcular_tercioEV, exp_relativa, zona_tercio


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
    """
    exp: Exp | None
    fecha: datetime | None
    WB: tuple[float, ...] | None
    tapada: bool


#
class OECF(object):
    """ Serie de tomas de una carpeta. Al crearlo lee de una vez la cámara
        y los datos de la serie, y los ofrece. Cada carpeta tiene su
        objeto, así que puede haber varios a la vez. """

    __slots__ = ["__balancePersonalizado", "__cam", "__celdas", "__copias",
                 "__enRejilla", "__esCarpeta", "__fuera", "__partes",
                 "__path", "__raws", "__secuencia", "__tapadas",
                 "__tercioEVs", "__tomas", "__WBs", "__zonas"]

    #
    # --- Constantes de la toma
    class KT(std.EnumMutable):
        """ Constantes de la lectura de una toma. """

        # --- Unidad del tiempo de exposición al mostrarlo
        segundos = "s"

        # --- Decimales del diafragma: rawpy lo da en coma flotante de 32
        #     bits
        decimales_f = 1

        # --- Tomas tapadas (tapa puesta y visor cubierto): se disparan a
        #     este tiempo y quedan casi en negro. Brillo: media del RAW
        #     sobre el nivel de negro, en tanto por uno del rango útil. En
        #     series reales, una tapada da 0.0003 y una toma normal, de
        #     0.02 a 0.06
        tv_tapada = 1 / 160
        brillo_tapada = 0.005

        # --- Copias de la serie: carpeta dentro de la de la serie y
        #     nombres de cada copia (llevan la extensión de su RAW). Zonas:
        #     Z00 a Z10, con -3 y -7 en los tercios (Z05 es la ZV);
        #     tapadas: DARK-1, DARK-2; balances de cámara: WB-01, WB-02…
        carpeta = "OECF"
        prefijo_zona = "Z"
        cifras_zona = 2
        tercios_zona = ("", "-3", "-7")
        prefijo_tapada = "DARK-"
        prefijo_balance = "WB-"
        cifras_balance = 2

        # --- Parte de la serie de cada toma (ver la property partes). La
        #     de los lados lleva su número: lado1, lado2
        parte_inicial = "inicial"
        parte_lado = "lado"
        parte_cambio = "cambio"
        parte_tapada = "tapada"
        parte_balance = "balance"
        parte_sobrante = "sobrante"

        # --- Para analizar, de Z1 a Z9 (con sus tercios) cada posición
        #     debe tener una toma, ni falta ni repetida; la ZV, al menos una
        zona_min_analisis = 1
        zona_max_analisis = 9

    #
    # --- Si la carpeta no existe o no tiene RAW, no falla.
    #
    def __init__(self, path: Path) -> None:
        self.__path = path
        self.__esCarpeta = path.is_dir()

        # --- Leer los RAW, en orden ([] si no hay)
        self.__raws: list[Path] = (self.__buscar_raw() if self.esCarpeta
                                   else [])

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
        self.__secuencia: Secuencia | None = None
        self.__tapadas: list[Path] = []
        self.__WBs: list[Path] = []
        self.__zonas: dict[int, Path | None] = {}
        self.__balancePersonalizado: bool | None = None
        self.__partes: list[str | None] = []
        self.__enRejilla: list[bool] = []
        self.__celdas: dict[int, list[int]] = {}
        self.__fuera: list[int] = []
        if self.raws and self.esRead:
            self.__repartir()

        # --- Copias en la carpeta OECF: las hace Copiar ({} hasta entonces)
        self.__copias: dict[Path, Path] = {}

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
    def raws(self) -> list[Path]:
        """ RAW's de la carpeta, ordenados ([] si no hay). """
        return self.__raws

    #
    @property
    def primera(self) -> str:
        """ Nombre del primer RAW de la carpeta. """
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
        En la ZV, la Z-V del balance personalizado o, si no hay, la
        primera; en las demás, la última que se hizo.
        """
        return self.__zonas

    #
    @property
    def tapadas(self) -> list[Path]:
        """ Saber los RAW de las tomas tapadas, en orden de disparo. """
        return self.__tapadas

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
        inicial, lado1, cambio, lado2, tapada, balance o sobrante (None si
        no se pudo leer; [] hasta leer la serie).
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
    def vacias(self) -> list[int]:
        """
        Saber las posiciones de la rejilla sin ninguna toma (sus tercioEV,
        de la más oscura a la más clara).
        """
        return [t for t in range(-KS.tercios_lado, KS.tercios_lado + 1)
                if t not in self.celdas]

    #
    @property
    def repetidas(self) -> dict[int, list[int]]:
        """
        Saber las posiciones con más de una toma, sin contar la ZV, donde
        se esperan varias: {tercioEV: [índices en raws]}.
        """
        return {t: tomas for t, tomas in sorted(self.celdas.items())
                if t != 0 and len(tomas) > 1}

    #
    @property
    def esAnalizable(self) -> bool:
        """
        Saber si la serie se puede analizar: de Z1 a Z9, cada posición con
        una toma, ni falta ni repetida; en la ZV, al menos una.
        """
        if not self.celdas:
            return False
        kt = self.KT
        desde = (kt.zona_min_analisis - KP.zona_ref) * KP.tercios
        hasta = (kt.zona_max_analisis - KP.zona_ref) * KP.tercios
        for tercioEV in range(desde, hasta + 1):
            n = len(self.celdas.get(tercioEV, []))
            if n == 0 or (n > 1 and tercioEV != 0):
                return False
        return True

    #
    @property
    def carpeta(self) -> Path:
        """
        Saber la carpeta de las copias de la serie: OECF, dentro de la de
        la serie.
        """
        return self.path / self.KT.carpeta

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
    def Leer(self) -> Iterator[int]:
        """
        Lee las tomas que faltan, una cada vez y abriendo cada RAW una sola
        vez (la primera ya se leyó al crear el objeto). Tras cada una dice
        cuántas lleva: se pueden ir pidiendo con next() para mostrar el
        progreso sin congelarse, o leerlas todas seguidas con un for. Si
        ya están todas, no lee nada.
        """
        # --- Al leer la última, se reparte la serie ANTES de su yield:
        #     quien lee con next() deja de pedir cuando ya están todas, y
        #     lo que fuera detrás del último yield no se ejecutaría nunca
        for raw in self.raws[len(self.tomas):]:
            self.__tomas.append(self.__leer_toma(raw))
            if self.esRead:
                self.__repartir()
            yield len(self.tomas)

    #
    def Copiar(self) -> Path | None:
        """
        Copia a la carpeta OECF las tomas que sirven, con su nombre: una
        por zona, las tapadas y los balances de cámara. Solo el RAW, copia
        exacta: los originales no se tocan. Antes borra la carpeta OECF
        anterior, si la hay. Devuelve la carpeta, o None si la serie aún
        no está leída o no se pudo copiar.
        """
        self.__copias = {}
        if not self.raws or not self.esRead:
            return None
        kt = self.KT

        # --- Nombre de cada copia, sin extensión: {RAW: nombre}
        nombres: dict[Path, str] = {}
        for tercioEV, raw in self.zonas.items():
            if raw is not None:
                ev, tercio = zona_tercio(tercioEV)
                nombres[raw] = (f"{kt.prefijo_zona}{ev:0{kt.cifras_zona}d}"
                                f"{kt.tercios_zona[tercio]}")
        for n, raw in enumerate(self.tapadas, 1):
            nombres[raw] = f"{kt.prefijo_tapada}{n}"
        for n, raw in enumerate(self.WBs, 1):
            nombres[raw] = f"{kt.prefijo_balance}{n:0{kt.cifras_balance}d}"

        # --- Las copias se apuntan solo si se hicieron todas
        copias = {raw: self.carpeta / f"{nombre}{raw.suffix}"
                  for raw, nombre in nombres.items()}
        try:
            if self.carpeta.is_dir():
                shutil.rmtree(self.carpeta)
            self.carpeta.mkdir()
            for raw, copia in copias.items():
                shutil.copy2(raw, copia)
        except OSError:
            return None
        self.__copias = copias
        return self.carpeta

    #
    @staticmethod
    def TextoF(diafragma: float) -> str:
        """ Diafragma como texto, sin ceros sobrantes: 9, 5.6. """
        return f"{round(diafragma, OECF.KT.decimales_f):g}"

    #
    @staticmethod
    def TextoTV(segundos: float) -> str:
        """ Tiempo como lo marca la cámara: 1/125 s, o 2 s si pasa del
            segundo. """
        if segundos < 1:
            return f"1/{round(1 / segundos)} {OECF.KT.segundos}"
        return f"{segundos:g} {OECF.KT.segundos}"

    #
    @staticmethod
    def TextoISO(iso: float) -> str:
        """ ISO como texto, en número entero: 100. """
        return str(round(iso))

    # endregion Métodos públicos

    #
    # --- Métodos privados
    #
    # region Métodos privados

    # --- RAW de la carpeta, ordenados por nombre (lista vacía si no hay).
    #     El orden definitivo será por fecha de disparo
    def __buscar_raw(self) -> list[Path]:
        return sorted(p for p in self.path.iterdir()
                      if p.is_file() and p.suffix.lower() in KCOM.extensiones)

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
                exp = Exp(float(otros.aperture), float(otros.shutter_speed),
                          float(otros.iso_speed))
                wb = tuple(float(m) for m in raw.camera_whitebalance)

                # --- Brillo: media del RAW sobre el nivel de negro, en tanto
                #     por uno del rango útil
                tapada = False
                if math.isclose(exp.tv, OECF.KT.tv_tapada,
                                rel_tol=KCOM.margenTV):
                    negro = sum(raw.black_level_per_channel) / len(
                        raw.black_level_per_channel)
                    brillo = ((raw.raw_image_visible.mean() - negro)
                              / (raw.white_level - negro))
                    tapada = bool(brillo < OECF.KT.brillo_tapada)

                return Toma(exp, otros.timestamp, wb, tapada)
        except (rawpy.LibRawError, OSError):                    # type: ignore
            return Toma(None, None, None, False)

    #
    # --- Reparte la serie ya leída: el tercioEV de cada toma respecto a la
    #     primera que se pudo leer (la Z-V), sus partes según el protocolo,
    #     las tapadas, los WB y una toma por zona (ver la property zonas).
    #     La Z-V de cambio de lado y las sobrantes no van a ninguna zona
    def __repartir(self) -> None:
        relativas = [exp_relativa(t.exp.tv, t.exp.f, t.exp.iso) if t.exp
                     else None for t in self.tomas]
        reads = [e for e in relativas if e is not None]
        self.__tercioEVs = [calcular_tercioEV(e, reads[0]) if e is not None
                            else None for e in relativas]

        tapadas = [t.tapada for t in self.tomas]
        partes = self.__secuencia = secuencia(self.tercioEVs, tapadas)
        self.__tapadas = [r for r, t in zip(self.raws, tapadas) if t]
        self.__WBs = [self.raws[i] for i in partes.balances]

        # --- Las 31 zonas, vacías; la ZV y, después, los lados en orden de
        #     disparo: si una zona se repite, queda la última
        zonas: dict[int, Path | None] = {
            tercioEV: None
            for tercioEV in range(-KS.tercios_lado, KS.tercios_lado + 1)}
        iniciales = partes.iniciales
        if iniciales:
            zv = (iniciales[KS.iniciales - 1]
                  if len(iniciales) >= KS.iniciales else iniciales[0])
            zonas[0] = self.raws[zv]
        for lado in partes.lados:
            for i in lado:
                zonas[self.tercioEVs[i]] = self.raws[i]         # type: ignore
        self.__zonas = zonas

        # --- Balance personalizado: el de las Z-V iniciales del protocolo
        self.__balancePersonalizado = balance_personalizado(
            self.tercioEVs, [t.WB for t in self.tomas[:KS.iniciales]])

        # --- Parte de cada toma. Si una toma está en varias, gana la
        #     última de esta lista
        kt = self.KT
        nombres: dict[int, str] = {i: kt.parte_inicial
                                   for i in partes.iniciales}
        for n, lado in enumerate(partes.lados, 1):
            nombres.update({i: f"{kt.parte_lado}{n}" for i in lado})
        nombres.update({i: kt.parte_cambio for i in partes.cambios})
        nombres.update({i: kt.parte_tapada
                        for i, t in enumerate(tapadas) if t})
        nombres.update({i: kt.parte_balance for i in partes.balances})
        nombres.update({i: kt.parte_sobrante for i in partes.sobrantes})
        self.__partes = [nombres.get(i) for i in range(len(self.tomas))]

        # --- A la rejilla, todas menos tapadas, balances de cámara y Z-V
        #     iniciales de más; en cada posición, sus tomas en orden de
        #     disparo, y fuera, las que no caben o no se leyeron
        de_mas = set(partes.iniciales[KS.iniciales:])
        quitar = set(partes.balances) | de_mas
        self.__enRejilla = [not (t or i in quitar)
                            for i, t in enumerate(tapadas)]
        celdas: dict[int, list[int]] = {}
        fuera: list[int] = []
        for i, (tercioEV, va) in enumerate(zip(self.tercioEVs,
                                               self.enRejilla)):
            if not va:
                continue
            if tercioEV is None or abs(tercioEV) > KS.tercios_lado:
                fuera.append(i)
            else:
                celdas.setdefault(tercioEV, []).append(i)
        self.__celdas = celdas
        self.__fuera = fuera

    # endregion Métodos privados
