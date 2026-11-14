# -*- coding: utf-8 *-*
"""
    :Propósito: Resultado de medir una serie (la parte de los RAW del
                análisis) y su paso a datos de JSON y de vuelta: así la
                segunda parte (las exportaciones del revelador) se puede
                hacer otro día, en las mismas teselas, sin releer los RAW
    :Autor:     Tony Diana
    :Versión:   26.11.10
"""

# cSpell:ignore asim, kcom, nanmean

__all__ = ["KAN", "ZonaMedida", "BalanceMedido", "MedidaISO", "FilaISO",
           "textura", "Review", "review_a_dict", "review_de_dict"]

# --- Bibliotecas estándar Python
import math
from dataclasses import dataclass
from typing import NamedTuple

# --- Bibliotecas externas
import numpy as np

# --- Bibliotecas internas
from bib import std
from bib.oecfMediadores import KP
from kernel import COM as KCOM
from .pixeles import Pixeles
from .secuencia import KS, z2_medible
from .teselas import KTE, Ventana
from .transferencia import Transferencia


#
class KAN(std.EnumMutable):
    """ Constantes del análisis y de sus claves en el JSON. """

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

    # --- Claves del JSON (el bloque «medida» de estudio.json), en
    #     camelCase. Lo que es de la serie (cámara, fecha, exposición y
    #     bits de la ZV, la copia de cada toma, el nombre, los Kelvin y los
    #     multiplicadores de la cámara en cada balance) y el L* del
    #     revelador no se guardan aquí: cada dato, en un solo sitio (Tony,
    #     2026-10-21). Los repone quien lee (ver estudio.leer_review). La
    #     tela es siempre {x, y, ancho, alto} o null, y si es null,
    #     telaMotivo dice por qué (KTE): un tipo por clave
    J_LADO = "ladoTesela"
    J_ALTO = "altoSensor"
    J_ANCHO = "anchoSensor"
    J_MAPA = "mapaTeselas"
    J_TELA = "tela"
    J_TELA_MOTIVO = "telaMotivo"

    # --- Tamaño de la segunda lámina elegido en la caja Lámina (factor de
    #     KTE.FACTORES): lo graba Generar y lo lee Analizar revelado, que
    #     es quien hace las láminas, con las exportaciones del revelador.
    #     No es del análisis: no está en Review, lo leen y graban aparte
    #     (exportar.jsonSave). Ausente en los JSON 1.0 (Tony, 2026-11-13)
    J_FACTOR_LAMINA = "factorLamina"

    # --- Versión del análisis (oecf.versionAnalisis del JSON): SÚBELA
    #     SOLO SI CAMBIA CÓMO SE MIDEN LOS RAW (criterio de textura,
    #     umbrales, teselas…): un análisis guardado con una anterior se
    #     vuelve a medir. Un cambio de textos o de claves no la toca (ver
    #     oecfMediadores.KES, las tres versiones). Tony, 2026-11-13.
    #     1.1: el límite de sombras de la latitud de texturas sale del
    #     contraste de la trama del paño en las exportaciones del
    #     revelador, no de la textura/ruido de los RAW (2026-11-13)
    VERSION_ANALISIS = "1.1"
    J_X = "x"
    J_Y = "y"
    J_ANCHO_VENTANA = "ancho"
    J_ALTO_VENTANA = "alto"
    J_NEGRO = "negro"
    J_ORIGEN_NEGRO = "origenNegro"
    J_RUIDO = "ruido"
    J_ORIGEN_RUIDO = "origenRuido"
    J_RUIDO_BORDE = "ruidoBorde"
    J_RUIDO_TAPADAS = "ruidoTapadas"
    J_DIFIEREN = "ruidosDifieren"
    J_MATRIZ = "matrizCamXYZ"
    J_ZONAS = "zonas"
    J_CONTROL = "control"
    J_TERCIO_EV = "tercioEV"
    J_ARCHIVO = "archivo"
    J_ISO = "iso"
    J_ISOS = "secuenciaISO"
    J_NIVEL = "nivel"
    J_DISPERSION = "dispersion"
    J_DISP_PANTALLA = "dispPantalla"
    J_TELA_NIVEL = "telaNivel"
    J_TELA_DISP = "telaDisp"
    J_TELA_DISP_PANTALLA = "telaDispPantalla"
    J_TELA_RECORTADO = "telaRecortado"
    J_DEV = "devRechazadas"
    J_BALANCES = "balances"
    J_KELVIN = "kelvin"
    J_TRANSFERENCIA = "transferencia"
    J_LECTURA = "lectura"
    J_GANANCIA = "ganancia"
    J_PROPORCIONAL = "proporcional"
    J_ALEATORIO = "ruidoAleatorioZV"
    J_PIXELES = "pixeles"
    J_CALIENTES = "calientes"
    J_CONFIRMADOS = "confirmados"
    J_MUERTOS = "muertos"
    J_MEGAPIXELES = "megapixeles"
    J_Z2 = "z2"
    J_ZV = "zv"


#
# --- Una toma medida: tarjeta y paño por canal del RAW ({canal: valor}).
#     Clase y no tupla: tiene comportamiento propio (sus propiedades); se
#     crea siempre con los nombres de los campos (kw_only)
@dataclass(frozen=True, slots=True, kw_only=True, eq=False)
class ZonaMedida:
    """
    Toma medida: su posición (tercioEV), su RAW y su copia, la tarjeta
    por canal (nivel sobre el negro y dispersión), el paño por canal
    (nivel, dispersión y fracción recortada; {} si no hay paño), la
    desviación de cada tesela rechazada (en zonas) y las dispersiones de
    la tarjeta y del paño a escala de pantalla (ver
    teselas.bloque_pantalla; {} si no se midieron)
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
    disp_pantalla: dict[str, float]
    tela_disp_pantalla: dict[str, float]

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
    def dispPantallaRGB(self) -> tuple[float, float, float] | None:
        """
        Saber la dispersión de la tarjeta a escala de pantalla en rojo,
        verde y azul (None si no se midió)
        """
        return _rgb(self.disp_pantalla) if self.disp_pantalla else None

    #
    @property
    def telaDispPantallaRGB(self) -> tuple[float, float, float] | None:
        """
        Saber la dispersión del paño a escala de pantalla en rojo, verde y
        azul (None sin paño o si no se midió)
        """
        return (_rgb(self.tela_disp_pantalla) if self.tela_disp_pantalla
                else None)

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
    da leer.marcas: DAYLIGHT, SHADE…), los Kelvin que guarda la cámara (None
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
# --- Un ISO de la secuencia de ISO, medido
class MedidaISO(NamedTuple):
    """
    Un ISO de la secuencia de ISO: el ISO, el negro restado por canal (el
    que declara su RAW: las tapadas son del ISO de la serie), el ruido de
    lectura del borde oscuro de su RAW (None si no hay borde) y su Z-V y
    su Z2 medidas (None si falta)
    """
    iso: int
    negro: tuple[float, ...]
    ruido_borde: tuple[float, ...] | None
    z2: ZonaMedida | None
    zv: ZonaMedida | None


#
# --- Lo que se enseña de un ISO de la secuencia de ISO (en verde)
class FilaISO(NamedTuple):
    """
    Un ISO de la secuencia de ISO, en verde: el ISO, el tercioEV de su
    Z2 (None si falta), si se mide (con Z-V y Z2, y la Z2 a KS.MARGEN_Z2
    tercios de KS.TERCIOS_Z2 como mucho) y si es una estimación (la Z2 no
    está justo en KS.TERCIOS_Z2); y, si se mide (si no, None): cuánto se
    aparta su Z-V de la del ISO inicial (en zonas), el ruido de lectura
    (del borde oscuro; None si no hay), el ruido de la tarjeta en la Z-V
    y en la Z2 (dispersión relativa), la textura del paño en la Z2 (sin
    el ruido de la tarjeta; None sin paño), textura/ruido en la Z2, el
    nivel de la tarjeta en la Z-V y en la Z2 (sobre el negro) y si los
    ruidos y la textura son a escala de pantalla (si no, por píxel: JSON
    anteriores)
    """
    iso: int
    tercio_z2: int | None
    medible: bool
    estimada: bool
    desviacion: float | None
    lectura: float | None
    ruido_zv: float | None
    ruido_z2: float | None
    textura_z2: float | None
    textura_ruido: float | None
    nivel_zv: float | None
    nivel_z2: float | None
    es_pantalla: bool


#
def textura(tela_disp: float, tarjeta_disp: float) -> float:
    """
    Textura del paño: su dispersión sin el ruido de la tarjeta (las dos,
    dispersiones relativas de la misma toma), la raíz de la diferencia de
    sus cuadrados (0 si la del paño no llega)
    """
    return math.sqrt(max(0.0, (tela_disp ** 2) - (tarjeta_disp ** 2)))


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
    fecha de la Z-V (ISO 8601) y su exposición (f, Tv en segundos, ISO),
    los balances de la cámara, el L* del revelador por zona (las 31, de
    sus exportaciones; () hasta la segunda parte), el contraste de la
    trama del paño por zona en esas exportaciones (las 31, en L*; NaN sin
    él; () hasta la segunda parte), la profundidad de bits
    de los RAW (None si no se leyó), la curva de transferencia del ruido
    por canal ({canal: Transferencia}; None si no se pudo ajustar) y el
    ruido aleatorio de la tarjeta en la Z-V por canal (dispersión
    relativa, con una Z-V de control; None sin ella), los píxeles
    defectuosos del sensor (None si no se contaron) y la secuencia de ISO
    medida, de menor a mayor ISO (() si no la hay).
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
    f: float | None = None
    tv: float | None = None
    iso: float | None = None
    balances: tuple[BalanceMedido, ...] = ()
    revelador: tuple[float, ...] = ()
    contraste: tuple[float, ...] = ()
    bits: int | None = None
    transferencia: dict[str, Transferencia] | None = None
    aleatorio: dict[str, float] | None = None
    pixeles: Pixeles | None = None
    isos: tuple[MedidaISO, ...] = ()

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
        return sorted(distintos, key=_por_kelvin)

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
    def sombrasAlzadas(self) -> float | None:
        """
        Saber cuánto más claras salen las sombras de lo que dice su tiempo
        de exposición, en zonas (verde, en la zona más oscura): el corte
        con luz 0 de la recta nivel/luz de las sombras, sobre su nivel.
        None si no hay zonas de sombra bastantes o el corte no es positivo.
        """
        sombras = [z for z in self.zonas
                   if (z is not None) and (z.nivelRGB[1] > 0)
                   and (z.tercio_ev <= KTE.SOMBRAS_HASTA)]
        if len(sombras) < KTE.MIN_ZONAS_SOMBRAS:
            return None
        luz = np.array([2.0 ** (z.tercio_ev / KP.TERCIOS) for z in sombras])
        nivel = np.array([z.nivelRGB[1] for z in sombras])
        recta = np.column_stack((np.ones_like(luz), luz))
        corte = np.linalg.lstsq(recta, nivel, rcond=None)[0][0]
        oscura = nivel[np.argmin(luz)]
        if (corte <= 0) or (corte >= oscura):
            return None
        return float(np.log2(oscura / (oscura - corte)))

    #
    @property
    def ruidoRGB(self) -> tuple[float, float, float] | None:
        """ Saber el ruido de lectura usado en rojo, verde y azul (o None). """
        return None if (self.ruido is None) else _rgb_canales(self.ruido)

    #
    @property
    def ruidoBordeRGB(self) -> tuple[float, float, float] | None:
        """
        Saber el ruido de la franja oscura del sensor en rojo, verde y
        azul (None si el sensor no la tiene).
        """
        return (None if (self.ruido_borde is None)
                else _rgb_canales(self.ruido_borde))

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
    def filasISO(self) -> list[FilaISO]:
        """
        Saber lo que se enseña de cada ISO de la secuencia de ISO, de menor
        a mayor ISO ([] si no la hay). La desviación, frente a la Z-V del
        primer ISO que la tenga (el inicial)
        """
        verde = 1
        base = next((m.zv.nivelRGB[verde] for m in self.isos
                     if (m.zv is not None) and (m.zv.nivelRGB[verde] > 0)),
                    None)
        filas = []
        for m in self.isos:
            tercio = m.z2.tercio_ev if m.z2 else None
            if not z2_medible(tercio, m.zv is not None):
                filas.append(FilaISO(
                    iso=m.iso, tercio_z2=tercio, medible=False,
                    estimada=False, desviacion=None, lectura=None,
                    ruido_zv=None, ruido_z2=None, textura_z2=None,
                    textura_ruido=None, nivel_zv=None, nivel_z2=None,
                    es_pantalla=False))
                continue
            zv, z2 = m.zv, m.z2
            nivel = zv.nivelRGB[verde]                       # type: ignore

            # --- La textura y el ruido, a escala de pantalla si se
            #     midieron (si no, JSON anteriores: por píxel)
            pantalla = ((zv.dispPantallaRGB is not None)     # type: ignore
                        and (z2.dispPantallaRGB is not None)  # type: ignore
                        and (z2.telaDispPantallaRGB is not None
                             or not z2.telaDispRGB))         # type: ignore
            if pantalla:
                ruido_zv = zv.dispPantallaRGB[verde]         # type: ignore
                ruido_z2 = z2.dispPantallaRGB[verde]         # type: ignore
                tela = z2.telaDispPantallaRGB                # type: ignore
            else:
                ruido_zv = zv.dispRGB[verde]                 # type: ignore
                ruido_z2 = z2.dispRGB[verde]                 # type: ignore
                tela = z2.telaDispRGB                        # type: ignore
            tx = (textura(tela[verde], ruido_z2)
                  if (tela is not None) else None)
            filas.append(FilaISO(
                iso=m.iso,
                tercio_z2=tercio,
                medible=True,
                estimada=(tercio != KS.TERCIOS_Z2),
                desviacion=(float(np.log2(nivel / base))
                            if (base and (nivel > 0)) else None),
                lectura=(None if (m.ruido_borde is None)
                         else _rgb_canales(m.ruido_borde)[verde]),
                ruido_zv=ruido_zv,
                ruido_z2=ruido_z2,
                textura_z2=tx,
                textura_ruido=((tx / ruido_z2)
                               if ((tx is not None) and (ruido_z2 > 0))
                               else None),
                nivel_zv=nivel,
                nivel_z2=z2.nivelRGB[verde],                 # type: ignore
                es_pantalla=pantalla))
        return filas

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
    """
    Análisis como datos de JSON (solo tipos básicos), sin lo que es de la
    serie ni el revelador (ver KAN, claves del JSON)
    """
    a = review
    caracteres = KAN.CARACTERES
    tela, motivo = ((None, a.tela) if isinstance(a.tela, str) else (
        {KAN.J_X: a.tela.x, KAN.J_Y: a.tela.y,
         KAN.J_ANCHO_VENTANA: a.tela.ancho, KAN.J_ALTO_VENTANA: a.tela.alto},
        None))
    return {
        KAN.J_LADO: a.lado, KAN.J_ALTO: a.alto, KAN.J_ANCHO: a.ancho,
        KAN.J_MAPA: ["".join(caracteres[int(m)] for m in fila)
                     for fila in a.motivos],
        KAN.J_TELA: tela,
        KAN.J_TELA_MOTIVO: motivo,
        KAN.J_NEGRO: _lista(a.negro), KAN.J_ORIGEN_NEGRO: a.origen_negro,
        KAN.J_RUIDO: _lista(a.ruido), KAN.J_ORIGEN_RUIDO: a.origen_ruido,
        KAN.J_RUIDO_BORDE: _lista(a.ruido_borde),
        KAN.J_RUIDO_TAPADAS: _lista(a.ruido_tapadas),
        KAN.J_DIFIEREN: a.difieren,
        KAN.J_MATRIZ: [list(fila) for fila in a.matriz],
        KAN.J_ZONAS: [_zona_a_dict(z) if z else None for z in a.zonas],
        KAN.J_CONTROL: [_zona_a_dict(z) for z in a.control],
        KAN.J_BALANCES: [{KAN.J_ARCHIVO: b.archivo, KAN.J_KELVIN: b.kelvin}
                         for b in a.balances],
        KAN.J_TRANSFERENCIA: None if (a.transferencia is None) else {
            canal: {KAN.J_LECTURA: _numero(c.lectura),
                    KAN.J_GANANCIA: c.ganancia,
                    KAN.J_PROPORCIONAL: c.proporcional}
            for canal, c in a.transferencia.items()},
        KAN.J_ALEATORIO: a.aleatorio,
        KAN.J_PIXELES: None if (a.pixeles is None) else {
            KAN.J_CALIENTES: a.pixeles.calientes,
            KAN.J_CONFIRMADOS: a.pixeles.confirmados,
            KAN.J_MUERTOS: a.pixeles.muertos,
            KAN.J_MEGAPIXELES: a.pixeles.megapixeles},
        KAN.J_ISOS: [_iso_a_dict(m) for m in a.isos]}


#
def review_de_dict(datos: dict) -> Review:
    """
    Análisis desde los datos de un JSON (ver review_a_dict). Lo que es de
    la serie y el revelador quedan vacíos (cam "", fecha, f, tv, iso y
    bits None, revelador (), copia de cada toma None y, en los balances,
    nombre, kelvin_cam y multiplicadores None): los repone quien lee (ver
    estudio.leer_review)
    """
    motivo = {c: m for m, c in KAN.CARACTERES.items()}
    tela = datos[KAN.J_TELA]
    return Review(
        lado=datos[KAN.J_LADO],
        alto=datos[KAN.J_ALTO],
        ancho=datos[KAN.J_ANCHO],
        motivos=np.array([[motivo[c] for c in fila]
                          for fila in datos[KAN.J_MAPA]], dtype=np.int8),
        tela=datos[KAN.J_TELA_MOTIVO] if (tela is None) else Ventana(
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
        balances=tuple(
            BalanceMedido(archivo=b[KAN.J_ARCHIVO], nombre=None,
                          kelvin_cam=None, kelvin=b[KAN.J_KELVIN],
                          multiplicadores=None)
            for b in datos[KAN.J_BALANCES]),
        transferencia=None if (datos.get(KAN.J_TRANSFERENCIA) is None) else {
            canal: Transferencia(
                lectura=(np.nan if (c[KAN.J_LECTURA] is None)
                         else c[KAN.J_LECTURA]),
                ganancia=c[KAN.J_GANANCIA],
                proporcional=c[KAN.J_PROPORCIONAL])
            for canal, c in datos[KAN.J_TRANSFERENCIA].items()},
        aleatorio=datos.get(KAN.J_ALEATORIO),
        pixeles=None if (datos.get(KAN.J_PIXELES) is None) else Pixeles(
            calientes=datos[KAN.J_PIXELES][KAN.J_CALIENTES],
            confirmados=datos[KAN.J_PIXELES][KAN.J_CONFIRMADOS],
            muertos=datos[KAN.J_PIXELES][KAN.J_MUERTOS],
            megapixeles=datos[KAN.J_PIXELES][KAN.J_MEGAPIXELES]),
        isos=tuple(_iso_de_dict(d) for d in (datos.get(KAN.J_ISOS) or [])))


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
# --- Orden de los balances: por Kelvin anotado, de menor a mayor; los que
#     la cámara no anota, al final
def _por_kelvin(balance: BalanceMedido) -> tuple[bool, int]:
    return (balance.kelvin_cam is None), (balance.kelvin_cam or 0)


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
            KAN.J_NIVEL: z.nivel, KAN.J_DISPERSION: z.disp,
            KAN.J_TELA_NIVEL: z.tela_nivel,
            KAN.J_TELA_DISP: z.tela_disp,
            KAN.J_TELA_RECORTADO: z.tela_recortado,
            KAN.J_DEV: _lista(z.dev),
            KAN.J_DISP_PANTALLA: z.disp_pantalla,
            KAN.J_TELA_DISP_PANTALLA: z.tela_disp_pantalla}


def _zona_de_dict(d: dict) -> ZonaMedida:
    return ZonaMedida(tercio_ev=d[KAN.J_TERCIO_EV],
                      archivo=d[KAN.J_ARCHIVO],
                      copia=None,
                      nivel=d[KAN.J_NIVEL],
                      disp=d[KAN.J_DISPERSION],
                      tela_nivel=d[KAN.J_TELA_NIVEL],
                      tela_disp=d[KAN.J_TELA_DISP],
                      tela_recortado=d[KAN.J_TELA_RECORTADO],
                      dev=_tupla(d[KAN.J_DEV]) or (),
                      # --- JSON anteriores, sin la escala de pantalla
                      disp_pantalla=d.get(KAN.J_DISP_PANTALLA) or {},
                      tela_disp_pantalla=(
                          d.get(KAN.J_TELA_DISP_PANTALLA) or {}))


#
# --- Un ISO de la secuencia de ISO, a datos de JSON y de vuelta
def _iso_a_dict(m: MedidaISO) -> dict:
    return {KAN.J_ISO: m.iso, KAN.J_NEGRO: _lista(m.negro),
            KAN.J_RUIDO_BORDE: _lista(m.ruido_borde),
            KAN.J_Z2: _zona_a_dict(m.z2) if m.z2 else None,
            KAN.J_ZV: _zona_a_dict(m.zv) if m.zv else None}


def _iso_de_dict(d: dict) -> MedidaISO:
    return MedidaISO(iso=d[KAN.J_ISO],
                     negro=_tupla_num(d[KAN.J_NEGRO]),
                     ruido_borde=_tupla(d[KAN.J_RUIDO_BORDE]),
                     z2=_zona_de_dict(d[KAN.J_Z2]) if d[KAN.J_Z2] else None,
                     zv=_zona_de_dict(d[KAN.J_ZV]) if d[KAN.J_ZV] else None)
