# -*- coding: utf-8 *-*
"""
    :Propósito: Resultado de medir una serie (la parte de los RAW del
                análisis) y su paso a datos de JSON y de vuelta: así la
                segunda parte (las exportaciones del revelador) se puede
                hacer otro día, en las mismas teselas, sin releer los RAW
    :Autor:     Tony Diana
    :Versión:   26.10.15
"""

# cSpell:ignore analisis

__all__ = ["KAN", "ZonaMedida", "BalanceMedido", "Analisis",
           "analisis_a_dict", "analisis_de_dict"]

# --- Bibliotecas estándar Python
from typing import NamedTuple

# --- Bibliotecas externas
import numpy as np

# --- Bibliotecas internas
from bib import clases
from .secuencia import KS
from .teselas import KTE, Ventana
from .transferencia import Transferencia
from .zonas import KP


#
class KAN(clases.EnumMutable):
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
                  KTE.RECHAZO_NIVEL: "N", KTE.RECHAZO_DISPERSION: "D",
                  KTE.RECHAZO_ASIMETRIA: "A"}

    # --- Claves del JSON
    J_VERSION = "version"
    J_LADO = "lado_tesela"
    J_ALTO = "alto_sensor"
    J_ANCHO = "ancho_sensor"
    J_MAPA = "mapa_teselas"
    J_PANO = "pano"
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
    J_MATRIZ = "matriz_camara_xyz"
    J_ZONAS = "zonas"
    J_CONTROL = "control"
    J_TERCIO_EV = "tercioEV"
    J_ARCHIVO = "archivo"
    J_COPIA = "copia"
    J_NIVEL = "nivel"
    J_DISPERSION = "dispersion"
    J_PANO_NIVEL = "pano_nivel"
    J_PANO_DISPERSION = "pano_dispersion"
    J_PANO_RECORTADO = "pano_recortado"
    J_DESVIACION = "desviacion_rechazadas"
    J_BALANCES = "balances"
    J_NOMBRE = "nombre"
    J_KELVIN_CAMARA = "kelvin_camara"
    J_KELVIN = "kelvin"
    J_MULTIPLICADORES = "multiplicadores"
    J_REVELADOR = "revelador"
    J_CAMARA = "camara"
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
# --- Una toma medida: tarjeta y paño por canal del RAW ({canal: valor})
class ZonaMedida(NamedTuple):
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
    dispersion: dict[str, float]
    pano_nivel: dict[str, float]
    pano_dispersion: dict[str, float]
    pano_recortado: dict[str, float]
    desviacion: tuple[float, ...]

    #
    @property
    def nivelRGB(self) -> tuple[float, float, float]:
        """ Saber el nivel de la tarjeta en rojo, verde y azul. """
        return _rgb(self.nivel)

    #
    @property
    def dispersionRGB(self) -> tuple[float, float, float]:
        """ Saber la dispersión de la tarjeta en rojo, verde y azul. """
        return _rgb(self.dispersion)

    #
    @property
    def panoDispersionRGB(self) -> tuple[float, float, float] | None:
        """
        Saber la dispersión del paño en rojo, verde y azul (None sin
        paño).
        """
        return _rgb(self.pano_dispersion) if self.pano_dispersion else None

    #
    @property
    def panoRecortadoRGB(self) -> tuple[float, float, float] | None:
        """
        Saber la fracción recortada del paño en rojo, verde y azul (None
        sin paño).
        """
        return _rgb(self.pano_recortado) if self.pano_recortado else None


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
    kelvin_camara: int | None
    kelvin: float | None
    multiplicadores: tuple[float, ...] | None

    #
    @property
    def clave(self) -> tuple:
        """
        Saber qué la hace igual a otra (mismo balance, mismos Kelvin):
        de las iguales, el libro solo enseña una.
        """
        return (self.nombre, self.kelvin_camara,
                None if self.kelvin is None else round(self.kelvin))


#
# --- El análisis de una serie: lo que se midió en los RAW
class Analisis(NamedTuple):
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
    pano: Ventana | str
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
    camara: str = ""
    fecha: str | None = None
    iso: float | None = None
    tv: float | None = None
    f: float | None = None
    balances: tuple[BalanceMedido, ...] = ()
    revelador: tuple[float | None, ...] = ()
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
    def desvio(self, zona: ZonaMedida) -> float:
        """
        Cuánto se aparta una toma de la ZV en la luz que recibió (verde),
        en zonas. En una Z-V de control debería ser casi 0.
        """
        zv = self.zonas[KS.TERCIOS_LADO]
        if zv is None or zv.nivelRGB[1] <= 0 or zona.nivelRGB[1] <= 0:
            return 0.0
        return float(np.log2(zona.nivelRGB[1] / zv.nivelRGB[1]))

    #
    @property
    def controlesDesviados(self) -> list[ZonaMedida]:
        """
        Saber las Z-V de control que se apartan de la ZV más que
        KP.TOLERANCIA_LINEAL: la luz cambió durante la serie. No entran en
        la media de las Z-V.
        """
        return [z for z in self.control
                if abs(self.desvio(z)) > KP.TOLERANCIA_LINEAL]

    #
    @property
    def ruidoRGB(self) -> tuple[float, float, float] | None:
        """ Saber el ruido de lectura usado en rojo, verde y azul (o None). """
        return _por_canal(self.ruido)

    #
    @property
    def ruidoTapadasRGB(self) -> tuple[float, float, float] | None:
        """ Saber el ruido de las tomas tapadas en rojo, verde y azul. """
        return _por_canal(self.ruido_tapadas)

    #
    @property
    def negroRGB(self) -> tuple[float, float, float]:
        """ Saber el negro restado en rojo, verde y azul. """
        return _por_canal(self.negro)                       # type: ignore

    #
    @property
    def transferenciaRGB(self) -> tuple[Transferencia, Transferencia,
                                        Transferencia] | None:
        """
        Saber la curva de transferencia en rojo, verde y azul (la del verde,
        la media de las de sus canales), o None si falta alguno.
        """
        curvas = self.transferencia
        if not curvas or KAN.ROJO not in curvas or KAN.AZUL not in curvas:
            return None
        verdes = [curvas[v] for v in KAN.VERDES if v in curvas]
        if not verdes:
            return None
        verde = Transferencia(*(float(np.nanmean([c[k] for c in verdes]))
                                if not all(np.isnan(c[k]) for c in verdes)
                                else np.nan for k in range(3)))
        return curvas[KAN.ROJO], verde, curvas[KAN.AZUL]

    #
    @property
    def aleatorioRGB(self) -> tuple[float, float, float] | None:
        """ Saber el ruido aleatorio de la Z-V en rojo, verde y azul. """
        a = self.aleatorio
        if not a or KAN.ROJO not in a or KAN.AZUL not in a or not any(
                v in a for v in KAN.VERDES):
            return None
        return _rgb(a)


#
def analisis_a_dict(analisis: Analisis) -> dict:
    """ Análisis como datos de JSON (solo tipos básicos). """
    a = analisis
    caracteres = KAN.CARACTERES
    pano = a.pano if isinstance(a.pano, str) else {
        KAN.J_X: a.pano.x, KAN.J_Y: a.pano.y,
        KAN.J_ANCHO_VENTANA: a.pano.ancho, KAN.J_ALTO_VENTANA: a.pano.alto}
    return {
        KAN.J_VERSION: KAN.VERSION,
        KAN.J_LADO: a.lado, KAN.J_ALTO: a.alto, KAN.J_ANCHO: a.ancho,
        KAN.J_MAPA: ["".join(caracteres[int(m)] for m in fila)
                     for fila in a.motivos],
        KAN.J_PANO: pano,
        KAN.J_NEGRO: _lista(a.negro), KAN.J_ORIGEN_NEGRO: a.origen_negro,
        KAN.J_RUIDO: _lista(a.ruido), KAN.J_ORIGEN_RUIDO: a.origen_ruido,
        KAN.J_RUIDO_BORDE: _lista(a.ruido_borde),
        KAN.J_RUIDO_TAPADAS: _lista(a.ruido_tapadas),
        KAN.J_DIFIEREN: a.difieren,
        KAN.J_MATRIZ: [list(fila) for fila in a.matriz],
        KAN.J_ZONAS: [_zona_a_dict(z) if z else None for z in a.zonas],
        KAN.J_CONTROL: [_zona_a_dict(z) for z in a.control],
        KAN.J_CAMARA: a.camara, KAN.J_FECHA: a.fecha, KAN.J_ISO: a.iso,
        KAN.J_TV: a.tv, KAN.J_F: a.f,
        KAN.J_BALANCES: [{KAN.J_ARCHIVO: b.archivo, KAN.J_NOMBRE: b.nombre,
                          KAN.J_KELVIN_CAMARA: b.kelvin_camara,
                          KAN.J_KELVIN: b.kelvin,
                          KAN.J_MULTIPLICADORES: _lista(b.multiplicadores)}
                         for b in a.balances],
        KAN.J_REVELADOR: _lista(a.revelador) if a.revelador else [],
        KAN.J_BITS: a.bits,
        KAN.J_TRANSFERENCIA: None if a.transferencia is None else {
            canal: {KAN.J_LECTURA: _numero(c.lectura),
                    KAN.J_GANANCIA: c.ganancia,
                    KAN.J_PROPORCIONAL: c.proporcional}
            for canal, c in a.transferencia.items()},
        KAN.J_ALEATORIO: a.aleatorio}


#
def analisis_de_dict(datos: dict) -> Analisis:
    """ Análisis desde los datos de un JSON (ver analisis_a_dict). """
    motivo = {c: m for m, c in KAN.CARACTERES.items()}
    pano = datos[KAN.J_PANO]
    return Analisis(
        datos[KAN.J_LADO], datos[KAN.J_ALTO], datos[KAN.J_ANCHO],
        np.array([[motivo[c] for c in fila] for fila in datos[KAN.J_MAPA]],
                 dtype=np.int8),
        pano if isinstance(pano, str) else Ventana(
            pano[KAN.J_X], pano[KAN.J_Y], pano[KAN.J_ANCHO_VENTANA],
            pano[KAN.J_ALTO_VENTANA]),
        _tupla(datos[KAN.J_NEGRO]), datos[KAN.J_ORIGEN_NEGRO],
        _tupla(datos[KAN.J_RUIDO]), datos[KAN.J_ORIGEN_RUIDO],
        _tupla(datos[KAN.J_RUIDO_BORDE]), _tupla(datos[KAN.J_RUIDO_TAPADAS]),
        datos[KAN.J_DIFIEREN],
        tuple(tuple(fila) for fila in datos[KAN.J_MATRIZ]),
        tuple(_zona_de_dict(z) if z else None for z in datos[KAN.J_ZONAS]),
        tuple(_zona_de_dict(z) for z in datos[KAN.J_CONTROL]),
        datos[KAN.J_CAMARA], datos[KAN.J_FECHA], datos[KAN.J_ISO],
        datos[KAN.J_TV], datos[KAN.J_F],
        tuple(BalanceMedido(b[KAN.J_ARCHIVO], b[KAN.J_NOMBRE],
                            b[KAN.J_KELVIN_CAMARA], b[KAN.J_KELVIN],
                            _tupla(b[KAN.J_MULTIPLICADORES]))
              for b in datos[KAN.J_BALANCES]),
        _tupla(datos.get(KAN.J_REVELADOR)) or (), datos.get(KAN.J_BITS),
        None if datos.get(KAN.J_TRANSFERENCIA) is None else {
            canal: Transferencia(
                np.nan if c[KAN.J_LECTURA] is None else c[KAN.J_LECTURA],
                c[KAN.J_GANANCIA], c[KAN.J_PROPORCIONAL])
            for canal, c in datos[KAN.J_TRANSFERENCIA].items()},
        datos.get(KAN.J_ALEATORIO))


#
# --- Rojo, verde y azul de un valor por canal del RAW (índices 0 a 3; los
#     que no hay, NaN), o None
def _por_canal(valores: tuple[float, ...] | None
               ) -> tuple[float, float, float] | None:
    if valores is None:
        return None
    por_nombre = {nombre: valores[int(nombre[1:])]
                  for nombre in (KAN.ROJO, *KAN.VERDES, KAN.AZUL)}
    return _rgb({nombre: valor for nombre, valor in por_nombre.items()
                 if not np.isnan(valor)})


#
# --- Rojo, verde (media de los verdes que haya; sin ninguno, NaN: el
#     ruido de la curva puede no tener verde) y azul de {canal: valor}
def _rgb(valores: dict[str, float]) -> tuple[float, float, float]:
    verdes = [valores[v] for v in KAN.VERDES if v in valores]
    verde = sum(verdes) / len(verdes) if verdes else np.nan
    return valores[KAN.ROJO], verde, valores[KAN.AZUL]


#
# --- Tupla de números (o un número) como lista de JSON (NaN, que JSON no
#     admite, como None) y de vuelta
def _lista(valores: tuple[float, ...] | None) -> list | None:
    if valores is None:
        return None
    return [None if np.isnan(v) else float(v) for v in valores]


def _numero(valor: float) -> float | None:
    return None if np.isnan(valor) else float(valor)


def _tupla(valores: list | None) -> tuple[float, ...] | None:
    if valores is None:
        return None
    return tuple(np.nan if v is None else float(v) for v in valores)


#
# --- Una toma medida, a datos de JSON y de vuelta
def _zona_a_dict(z: ZonaMedida) -> dict:
    return {KAN.J_TERCIO_EV: z.tercio_ev, KAN.J_ARCHIVO: z.archivo,
            KAN.J_COPIA: z.copia, KAN.J_NIVEL: z.nivel,
            KAN.J_DISPERSION: z.dispersion,
            KAN.J_PANO_NIVEL: z.pano_nivel,
            KAN.J_PANO_DISPERSION: z.pano_dispersion,
            KAN.J_PANO_RECORTADO: z.pano_recortado,
            KAN.J_DESVIACION: _lista(z.desviacion)}


def _zona_de_dict(d: dict) -> ZonaMedida:
    return ZonaMedida(d[KAN.J_TERCIO_EV], d[KAN.J_ARCHIVO], d[KAN.J_COPIA],
                      d[KAN.J_NIVEL], d[KAN.J_DISPERSION],
                      d[KAN.J_PANO_NIVEL],
                      d[KAN.J_PANO_DISPERSION], d[KAN.J_PANO_RECORTADO],
                      _tupla(d[KAN.J_DESVIACION]) or ())
