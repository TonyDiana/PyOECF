# -*- coding: utf-8 *-*
"""
    :Propósito: Resultado de medir una serie (la parte de los RAW del
                análisis) y su paso a datos de JSON y de vuelta: así la
                segunda parte (las exportaciones del revelador) se puede
                hacer otro día, en las mismas teselas, sin releer los RAW
    :Autor:     Tony Diana
    :Versión:   26.10.18
"""

# cSpell:ignore asim, biboecf, kcom, nanmean

__all__ = ["KAN", "ZonaMedida", "BalanceMedido", "Review",
           "review_a_dict", "review_de_dict"]

# --- Bibliotecas estándar Python
from dataclasses import dataclass
from typing import NamedTuple

# --- Bibliotecas externas
import numpy as np

# --- Bibliotecas internas
from bib import std
from .constantes import COM as KCOM
from .secuencia import KS
from .teselas import KTE, Ventana
from .transferencia import Transferencia


#
class KAN(std.EnumMutable):
    """ Constantes del análisis y de sus claves en el JSON. """

    # --- Versión del formato: cambia si cambian las claves. La 2 añade
    #     la curva de transferencia y el ruido aleatorio de la Z-V (en
    #     las de la 1, sin ellos)
    VERSION = 2

    # --- Canales del RAW (los de Teselas.canales) que hacen el rojo, el
    #     verde (la media de los que haya) y el azul del libro
    ROJO = "R0"
    VERDES = ("G1", "G3")
    AZUL = "B2"

    # --- Mapa de teselas en el JSON: una cadena por fila, un carácter por
    #     tesela según su motivo (KTE)
    CARACTERES = {KTE.BUENA: ".", KTE.NO_TARJETA: " ",
                  KTE.RECHAZO_NIVEL: "N", KTE.RECHAZO_DISP: "D",
                  KTE.RECHAZO_ASIM: "A"}

    # --- Claves del JSON
    J_VERSION = "version"
    J_LADO = "lado_tesela"
    J_ALTO = "alto_sensor"
    J_ANCHO = "ancho_sensor"
    J_MAPA = "mapa_teselas"
    J_TELA = "tela"
    J_X = "x"
    J_Y = "y"
    J_ANCHO_VENTANA = "ancho"
    J_ALTO_VENTANA = "alto"
    J_NEGRO = "negro"
    J_ORIGEN_NEGRO = "origen_negro"
    J_RUIDO = "ruido"
    J_ORIGEN_RUIDO = "origen_ruido"
    J_RUIDO_BORDE = "ruido_borde"
    J_RUIDO_TAPADAS = "ruido_tapadas"
    J_DIFIEREN = "ruidos_difieren"
    J_MATRIZ = "matriz_cam_xyz"
    J_ZONAS = "zonas"
    J_CONTROL = "control"
    J_TERCIO_EV = "tercioEV"
    J_ARCHIVO = "archivo"
    J_COPIA = "copia"
    J_NIVEL = "nivel"
    J_DISPERSION = "dispersion"
    J_TELA_NIVEL = "tela_nivel"
    J_TELA_DISP = "tela_disp"
    J_TELA_RECORTADO = "tela_recortado"
    J_DEV = "dev_rechazadas"
    J_BALANCES = "balances"
    J_NOMBRE = "nombre"
    J_KELVIN_CAM = "kelvin_cam"
    J_KELVIN = "kelvin"
    J_MULTIPLICADORES = "multiplicadores"
    J_REVELADOR = "revelador"
    J_CAM = "cam"
    J_FECHA = "fecha_zv"
    J_ISO = "iso"
    J_TV = "tv"
    J_F = "f"
    J_BITS = "bits_raw"
    J_TRANSFERENCIA = "transferencia"
    J_LECTURA = "lectura"
    J_GANANCIA = "ganancia"
    J_PROPORCIONAL = "proporcional"
    J_ALEATORIO = "ruido_aleatorio_zv"


#
# --- Una toma medida: tarjeta y paño por canal del RAW ({canal: valor}).
#     Clase y no tupla: tiene comportamiento propio (sus propiedades); se
#     crea siempre con los nombres de los campos (kw_only)
@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class ZonaMedida:
    """
    Toma medida: su posición (tercioEV), su RAW y su copia, la tarjeta
    por canal (nivel sobre el negro y dispersión), el paño por canal
    (nivel, dispersión y fracción recortada; {} si no hay paño) y la
    desviación de cada tesela rechazada (en zonas).
    """
    tercio_ev: int
    archivo: str
    copia: str | None
    nivel: dict[str, float]
    disp: dict[str, float]
    tela_nivel: dict[str, float]
    tela_disp: dict[str, float]
    tela_recortado: dict[str, float]
    dev: tuple[float, ...]

    #
    @property
    def nivelRGB(self) -> tuple[float, float, float]:
        """ Saber el nivel de la tarjeta en rojo, verde y azul. """
        return _rgb(self.nivel)

    #
    @property
    def dispRGB(self) -> tuple[float, float, float]:
        """ Saber la dispersión de la tarjeta en rojo, verde y azul. """
        return _rgb(self.disp)

    #
    @property
    def telaDispRGB(self) -> tuple[float, float, float] | None:
        """
        Saber la dispersión del paño en rojo, verde y azul (None sin
        paño).
        """
        return _rgb(self.tela_disp) if self.tela_disp else None

    #
    @property
    def telaRecortadoRGB(self) -> tuple[float, float, float] | None:
        """
        Saber la fracción recortada del paño en rojo, verde y azul (None
        sin paño).
        """
        return _rgb(self.tela_recortado) if self.tela_recortado else None


#
# --- Una toma de balance de blancos de la cámara
class BalanceMedido(NamedTuple):
    """
    Toma de balance de la cámara: su RAW, el nombre del balance (como lo
    da biboecf: DAYLIGHT, SHADE…), los Kelvin que guarda la cámara (None
    si no los guarda), los Kelvin que de verdad aplica (los de la luz que
    sus multiplicadores dejan neutra; None sin multiplicadores) y los
    multiplicadores (rojo, verde, azul; el verde a 1).
    """
    archivo: str
    nombre: str | None
    kelvin_cam: int | None
    kelvin: float | None
    multiplicadores: tuple[float, ...] | None

    #
    @property
    def clave(self) -> tuple:
        """
        Saber qué la hace igual a otra (mismo balance, mismos Kelvin):
        de las iguales, el libro solo enseña una.
        """
        return (self.nombre, self.kelvin_cam,
                None if (self.kelvin is None) else round(self.kelvin))


#
# --- El análisis de una serie: lo que se midió en los RAW. Clase y no
#     tupla, como ZonaMedida: tiene comportamiento propio y se crea
#     siempre con los nombres de los campos
@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class Review:
    """
    Análisis de una serie (parte de los RAW): las teselas (lado, tamaño
    del sensor y motivo de cada una), el paño, el negro y el ruido con su
    origen, la matriz de la cámara, las 31 zonas (None si falta), las
    demás Z-V, para la cabecera del libro, la cámara (su nombre), la
    fecha de la Z-V (ISO 8601) y su exposición (ISO, Tv en segundos, f),
    los balances de la cámara, el L* del revelador por zona (las 31, de
    sus exportaciones; () hasta la segunda parte), la profundidad de bits
    de los RAW (None si no se leyó), la curva de transferencia del ruido
    por canal ({canal: Transferencia}; None si no se pudo ajustar) y el
    ruido aleatorio de la tarjeta en la Z-V por canal (dispersión
    relativa, con una Z-V de control; None sin ella).
    """
    lado: int
    alto: int
    ancho: int
    motivos: np.ndarray
    tela: Ventana | str
    negro: tuple[float, ...]
    origen_negro: str
    ruido: tuple[float, ...] | None
    origen_ruido: str | None
    ruido_borde: tuple[float, ...] | None
    ruido_tapadas: tuple[float, ...] | None
    difieren: bool
    matriz: tuple[tuple[float, ...], ...]
    zonas: tuple[ZonaMedida | None, ...]
    control: tuple[ZonaMedida, ...]
    cam: str = ""
    fecha: str | None = None
    iso: float | None = None
    tv: float | None = None
    f: float | None = None
    balances: tuple[BalanceMedido, ...] = ()
    revelador: tuple[float, ...] = ()
    bits: int | None = None
    transferencia: dict[str, Transferencia] | None = None
    aleatorio: dict[str, float] | None = None

    #
    @property
    def balancesDistintos(self) -> list[BalanceMedido]:
        """
        Saber las tomas de balance sin repetir: de las que tienen el
        mismo balance y los mismos Kelvin, la primera.
        """
        vistas: set = set()
        distintos = []
        for balance in self.balances:
            if balance.clave not in vistas:
                vistas.add(balance.clave)
                distintos.append(balance)
        return distintos

    #
    def dev(self, zona: ZonaMedida) -> float:
        """
        Cuánto se aparta una toma de la ZV en la luz que recibió (verde),
        en zonas. En una Z-V de control debería ser casi 0.
        """
        zv = self.zonas[KS.TERCIOS_LADO]
        if (zv is None) or (zv.nivelRGB[1] <= 0) or (zona.nivelRGB[1] <= 0):
            return 0.0
        return float(np.log2(zona.nivelRGB[1] / zv.nivelRGB[1]))

    #
    @property
    def controlesDesviados(self) -> list[ZonaMedida]:
        """
        Saber las Z-V de control que se apartan de la ZV más que
        KCOM.TOLERANCIA_LINEAL: la luz cambió durante la serie. No entran en
        la media de las Z-V.
        """
        return [z for z in self.control
                if abs(self.dev(z)) > KCOM.TOLERANCIA_LINEAL]

    #
    @property
    def ruidoRGB(self) -> tuple[float, float, float] | None:
        """ Saber el ruido de lectura usado en rojo, verde y azul (o None). """
        return None if (self.ruido is None) else _rgb_canales(self.ruido)

    #
    @property
    def ruidoTapadasRGB(self) -> tuple[float, float, float] | None:
        """ Saber el ruido de las tomas tapadas en rojo, verde y azul. """
        return (None if (self.ruido_tapadas is None)
                else _rgb_canales(self.ruido_tapadas))

    #
    @property
    def negroRGB(self) -> tuple[float, float, float]:
        """ Saber el negro restado en rojo, verde y azul. """
        return _rgb_canales(self.negro)

    #
    @property
    def transferenciaRGB(self) -> tuple[Transferencia, Transferencia,
                                        Transferencia] | None:
        """
        Saber la curva de transferencia en rojo, verde y azul (la del verde,
        la media de las de sus canales), o None si falta alguno.
        """
        curvas = self.transferencia
        if ((not curvas) or (KAN.ROJO not in curvas)
                or (KAN.AZUL not in curvas)):
            return None
        verdes = [curvas[v] for v in KAN.VERDES if v in curvas]
        if not verdes:
            return None
        verde = Transferencia(
            lectura=_media([c.lectura for c in verdes]),
            ganancia=_media([c.ganancia for c in verdes]),
            proporcional=_media([c.proporcional for c in verdes]))
        return curvas[KAN.ROJO], verde, curvas[KAN.AZUL]

    #
    @property
    def aleatorioRGB(self) -> tuple[float, float, float] | None:
        """ Saber el ruido aleatorio de la Z-V en rojo, verde y azul. """
        a = self.aleatorio
        if (not a) or (KAN.ROJO not in a) or (KAN.AZUL not in a) or (not any(
                v in a for v in KAN.VERDES)):
            return None
        return _rgb(a)


#
def review_a_dict(review: Review) -> dict:
    """ Análisis como datos de JSON (solo tipos básicos). """
    a = review
    caracteres = KAN.CARACTERES
    tela = a.tela if isinstance(a.tela, str) else {
        KAN.J_X: a.tela.x, KAN.J_Y: a.tela.y,
        KAN.J_ANCHO_VENTANA: a.tela.ancho, KAN.J_ALTO_VENTANA: a.tela.alto}
    return {
        KAN.J_VERSION: KAN.VERSION,
        KAN.J_LADO: a.lado, KAN.J_ALTO: a.alto, KAN.J_ANCHO: a.ancho,
        KAN.J_MAPA: ["".join(caracteres[int(m)] for m in fila)
                     for fila in a.motivos],
        KAN.J_TELA: tela,
        KAN.J_NEGRO: _lista(a.negro), KAN.J_ORIGEN_NEGRO: a.origen_negro,
        KAN.J_RUIDO: _lista(a.ruido), KAN.J_ORIGEN_RUIDO: a.origen_ruido,
        KAN.J_RUIDO_BORDE: _lista(a.ruido_borde),
        KAN.J_RUIDO_TAPADAS: _lista(a.ruido_tapadas),
        KAN.J_DIFIEREN: a.difieren,
        KAN.J_MATRIZ: [list(fila) for fila in a.matriz],
        KAN.J_ZONAS: [_zona_a_dict(z) if z else None for z in a.zonas],
        KAN.J_CONTROL: [_zona_a_dict(z) for z in a.control],
        KAN.J_CAM: a.cam, KAN.J_FECHA: a.fecha, KAN.J_ISO: a.iso,
        KAN.J_TV: a.tv, KAN.J_F: a.f,
        KAN.J_BALANCES: [{KAN.J_ARCHIVO: b.archivo, KAN.J_NOMBRE: b.nombre,
                          KAN.J_KELVIN_CAM: b.kelvin_cam,
                          KAN.J_KELVIN: b.kelvin,
                          KAN.J_MULTIPLICADORES: _lista(b.multiplicadores)}
                         for b in a.balances],
        KAN.J_REVELADOR: _lista(a.revelador) if a.revelador else [],
        KAN.J_BITS: a.bits,
        KAN.J_TRANSFERENCIA: None if (a.transferencia is None) else {
            canal: {KAN.J_LECTURA: _numero(c.lectura),
                    KAN.J_GANANCIA: c.ganancia,
                    KAN.J_PROPORCIONAL: c.proporcional}
            for canal, c in a.transferencia.items()},
        KAN.J_ALEATORIO: a.aleatorio}


#
def review_de_dict(datos: dict) -> Review:
    """ Análisis desde los datos de un JSON (ver review_a_dict). """
    motivo = {c: m for m, c in KAN.CARACTERES.items()}
    tela = datos[KAN.J_TELA]
    return Review(
        lado=datos[KAN.J_LADO],
        alto=datos[KAN.J_ALTO],
        ancho=datos[KAN.J_ANCHO],
        motivos=np.array([[motivo[c] for c in fila]
                          for fila in datos[KAN.J_MAPA]], dtype=np.int8),
        tela=tela if isinstance(tela, str) else Ventana(
            x=tela[KAN.J_X], y=tela[KAN.J_Y], ancho=tela[KAN.J_ANCHO_VENTANA],
            alto=tela[KAN.J_ALTO_VENTANA]),
        negro=_tupla_num(datos[KAN.J_NEGRO]),
        origen_negro=datos[KAN.J_ORIGEN_NEGRO],
        ruido=_tupla(datos[KAN.J_RUIDO]),
        origen_ruido=datos[KAN.J_ORIGEN_RUIDO],
        ruido_borde=_tupla(datos[KAN.J_RUIDO_BORDE]),
        ruido_tapadas=_tupla(datos[KAN.J_RUIDO_TAPADAS]),
        difieren=datos[KAN.J_DIFIEREN],
        matriz=tuple(tuple(fila) for fila in datos[KAN.J_MATRIZ]),
        zonas=tuple(_zona_de_dict(z) if z else None
                    for z in datos[KAN.J_ZONAS]),
        control=tuple(_zona_de_dict(z) for z in datos[KAN.J_CONTROL]),
        cam=datos[KAN.J_CAM],
        fecha=datos[KAN.J_FECHA],
        iso=datos[KAN.J_ISO],
        tv=datos[KAN.J_TV],
        f=datos[KAN.J_F],
        balances=tuple(
            BalanceMedido(
                archivo=b[KAN.J_ARCHIVO],
                nombre=b[KAN.J_NOMBRE],
                kelvin_cam=b[KAN.J_KELVIN_CAM],
                kelvin=b[KAN.J_KELVIN],
                multiplicadores=_tupla(b[KAN.J_MULTIPLICADORES]))
            for b in datos[KAN.J_BALANCES]),
        revelador=_tupla(datos.get(KAN.J_REVELADOR)) or (),
        bits=datos.get(KAN.J_BITS),
        transferencia=None if (datos.get(KAN.J_TRANSFERENCIA) is None) else {
            canal: Transferencia(
                lectura=(np.nan if (c[KAN.J_LECTURA] is None)
                         else c[KAN.J_LECTURA]),
                ganancia=c[KAN.J_GANANCIA],
                proporcional=c[KAN.J_PROPORCIONAL])
            for canal, c in datos[KAN.J_TRANSFERENCIA].items()},
        aleatorio=datos.get(KAN.J_ALEATORIO))


#
# --- Rojo, verde y azul de un valor por canal del RAW (índices 0 a 3; los
#     que no hay, NaN)
def _rgb_canales(valores: tuple[float, ...]) -> tuple[float, float, float]:
    por_nombre = {nombre: valores[int(nombre[1:])]
                  for nombre in (KAN.ROJO, *KAN.VERDES, KAN.AZUL)}
    return _rgb({nombre: valor for nombre, valor in por_nombre.items()
                 if not np.isnan(valor)})


#
# --- Rojo, verde (media de los verdes que haya; sin ninguno, NaN: el
#     ruido de la curva puede no tener verde) y azul de {canal: valor}
def _rgb(valores: dict[str, float]) -> tuple[float, float, float]:
    verdes = [valores[v] for v in KAN.VERDES if v in valores]
    verde = (sum(verdes) / len(verdes)) if verdes else np.nan
    return valores[KAN.ROJO], verde, valores[KAN.AZUL]


#
# --- Media de unos valores sin contar los NaN (NaN si todos lo son)
def _media(valores: list[float]) -> float:
    if all(np.isnan(v) for v in valores):
        return np.nan
    return float(np.nanmean(valores))


#
# --- Tupla de números (o un número) como lista de JSON (NaN, que JSON no
#     admite, como None) y de vuelta
def _lista(valores: tuple[float, ...] | None) -> list | None:
    if valores is None:
        return None
    return [None if np.isnan(v) else float(v) for v in valores]


#
def _numero(valor: float) -> float | None:
    return None if np.isnan(valor) else float(valor)


#
def _tupla(valores: list | None) -> tuple[float, ...] | None:
    return None if (valores is None) else _tupla_num(valores)


#
def _tupla_num(valores: list) -> tuple[float, ...]:
    return tuple(np.nan if (v is None) else float(v) for v in valores)


#
# --- Una toma medida, a datos de JSON y de vuelta
def _zona_a_dict(z: ZonaMedida) -> dict:
    return {KAN.J_TERCIO_EV: z.tercio_ev, KAN.J_ARCHIVO: z.archivo,
            KAN.J_COPIA: z.copia, KAN.J_NIVEL: z.nivel,
            KAN.J_DISPERSION: z.disp,
            KAN.J_TELA_NIVEL: z.tela_nivel,
            KAN.J_TELA_DISP: z.tela_disp,
            KAN.J_TELA_RECORTADO: z.tela_recortado,
            KAN.J_DEV: _lista(z.dev)}


def _zona_de_dict(d: dict) -> ZonaMedida:
    return ZonaMedida(tercio_ev=d[KAN.J_TERCIO_EV],
                      archivo=d[KAN.J_ARCHIVO],
                      copia=d[KAN.J_COPIA],
                      nivel=d[KAN.J_NIVEL],
                      disp=d[KAN.J_DISPERSION],
                      tela_nivel=d[KAN.J_TELA_NIVEL],
                      tela_disp=d[KAN.J_TELA_DISP],
                      tela_recortado=d[KAN.J_TELA_RECORTADO],
                      dev=_tupla(d[KAN.J_DEV]) or ())
