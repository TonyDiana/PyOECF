# -*- coding: utf-8 *-*
"""
    :Propósito: Incidencias de una serie ya leída: códigos con sus datos,
                sin frases. Cada interfaz las traduce
    :Autor:     Tony Diana
    :Versión:   26.10.18
"""

# cSpell:ignore asim, kcom, oecf

__all__ = ["KI", "Incidencia", "avisos_rechazadas", "incidencias"]

# --- Bibliotecas estándar Python
from typing import NamedTuple

# --- Bibliotecas internas
from bib import std
from .constantes import COM as KCOM
from .kernel import OECF
from .secuencia import KS
from .teselas import KTE, Select


#
class KI(std.EnumMutable):
    """ Códigos de las incidencias, en el orden en que se informan. """

    # --- ISO
    ISO_DISTINTO = "ISO_DISTINTO"
    """ISO distinto del de la ZV en la serie: impide analizar."""

    # --- Balance personalizado
    MISMO_BALANCE = "MISMO_BALANCE"
    """Las dos primeras son Z-V con el mismo balance de blancos."""

    SIN_BALANCE = "SIN_BALANCE"
    """La 2.ª toma ya es de un lado: no se hizo el balance personalizado."""

    # --- Secuencia (ver OECF.secuencia)
    INICIALES_SOBRAN = "INICIALES_SOBRAN"
    """Hay más Z-V iniciales de las que pide el protocolo."""

    LADOS = "LADOS"
    """No están los dos lados de la serie."""

    SIN_CAMBIO = "SIN_CAMBIO"
    """Falta la Z-V de cambio de lado."""

    CAMBIOS_SOBRAN = "CAMBIOS_SOBRAN"
    """Hay más Z-V de cambio de las que pide el protocolo."""

    SIN_FINAL = "SIN_FINAL"
    """Falta la Z-V final, tras el segundo lado."""

    SALTO = "SALTO"
    """En un lado, el tercioEV no avanza de uno en uno."""

    SOBRANTES = "SOBRANTES"
    """Tomas que no son de ninguna parte de la serie."""

    # --- Tapadas y balances de cámara
    TAPADAS_MAL = "TAPADAS_MAL"
    """No hay las tomas tapadas que pide el protocolo."""

    ISO_TAPADAS = "ISO_TAPADAS"
    """Tapadas con otro ISO que la ZV (solo se avisa)."""

    SIN_BALANCES = "SIN_BALANCES"
    """No hay tomas de balance de cámara."""

    # --- Posiciones de la rejilla y tomas que no caben o se desvían
    SIN_TOMA = "SIN_TOMA"
    """Posición sin toma: impide analizar si es de Z1 a Z9."""

    REPETIDA = "REPETIDA"
    """Posición con más de una toma."""

    FUERA = "FUERA"
    """Tomas que no caben en la rejilla."""

    DESVIADAS = "DESVIADAS"
    """Tomas que se apartan de su tercio más que KP.DEV_MAX."""

    # --- Teselas de la Z-V (tras OECF.Seleccionar)
    SIN_TARJETA = "SIN_TARJETA"
    """Sin tarjeta gris (menos de KTE.MIN_TESELAS buenas): no se
    analiza."""

    RECHAZADAS = "RECHAZADAS"
    """Teselas de tarjeta que rechazan los filtros: cuántas y qué
    porcentaje de las de tarjeta."""

    # --- Avisos de las rechazadas, uno por causa (ver KTE.AVISO_*)
    TARJETA_SUCIA = "TARJETA_SUCIA"
    """Tarjeta sucia o dañada: rechazadas por dispersión o asimetría."""

    LUZ_DESIGUAL = "LUZ_DESIGUAL"
    """Luz desigual: rechazadas por nivel, con sus lados."""

    REVISAR_SERIE = "REVISAR_SERIE"
    """Por el total de rechazadas: revisar la serie."""

    REPETIR_SERIE = "REPETIR_SERIE"
    """Por el total de rechazadas: repetir la serie."""

    # --- Tras medir (OECF.Medir)
    LUZ_CAMBIO = "LUZ_CAMBIO"
    """Z-V de control que se apartan de la ZV más que
    COM.TOLERANCIA_LINEAL: la luz cambió; no entran en la media de las
    Z-V."""


#
# --- Una incidencia: su código y, según el código, sus datos
class Incidencia(NamedTuple):
    """ Incidencia de la serie: código (KI) y datos, sin frases. """
    code: str

    # --- True si impide analizar
    detiene: bool = False

    # --- Tomas a las que se refiere (índices en raws)
    tomas: tuple[int, ...] = ()

    # --- Cuántas hay, si no son tomas, y cuántas se esperaban. En SALTO,
    #     esperado es el tercioEV esperado
    n: int = 0
    esperado: int = 0

    # --- Posición a la que se refiere (tercioEV). En SALTO, la real
    tercioEV: int | None = None

    # --- Un porcentaje, si lo lleva (RECHAZADAS)
    porcentaje: float = 0.0

    # --- Un valor por toma, si lo lleva (LUZ_CAMBIO: cuánto se aparta
    #     cada una de la ZV, en zonas)
    valores: tuple[float, ...] = ()

    # --- Mitades de la toma, si las lleva (LUZ_DESIGUAL: KTE.LADO_*)
    lados: tuple[str, ...] = ()


#
def avisos_rechazadas(select: Select) -> list[Incidencia]:
    """
    Avisos de las teselas rechazadas, uno por causa (ver KTE.AVISO_*):
    tarjeta sucia (el porcentaje mayor de dispersión y asimetría), luz
    desigual (el de nivel y sus lados) y, por el total, revisar o
    repetir la serie. Porcentajes de las teselas de tarjeta.
    """
    avisos = []
    sucia = max(select.part(KTE.RECHAZO_DISP),
                select.part(KTE.RECHAZO_ASIM))
    if sucia > KTE.AVISO_SUCIA:
        avisos.append(Incidencia(code=KI.TARJETA_SUCIA,
                                 porcentaje=KCOM.CIEN * sucia))
    nivel = select.part(KTE.RECHAZO_NIVEL)
    if nivel > KTE.AVISO_NIVEL:
        avisos.append(Incidencia(code=KI.LUZ_DESIGUAL,
                                 porcentaje=KCOM.CIEN * nivel,
                                 lados=select.ladosNivel))
    total = select.porcentaje / KCOM.CIEN
    if total > KTE.AVISO_REPETIR:
        avisos.append(Incidencia(code=KI.REPETIR_SERIE,
                                 porcentaje=select.porcentaje))
    elif total > KTE.AVISO_REVISAR:
        avisos.append(Incidencia(code=KI.REVISAR_SERIE,
                                 porcentaje=select.porcentaje))
    return avisos


#
def incidencias(oecf: OECF) -> list[Incidencia]:
    """ Incidencias de una serie ya leída, en orden ([] si no se leyó). """
    sec = oecf.secuencia
    if sec is None:
        return []
    lista: list[Incidencia] = []

    # --- ISO distinto en la serie: lo primero, porque impide analizar
    if oecf.isoDistintos and (oecf.isoSerie is not None):
        lista.append(Incidencia(code=KI.ISO_DISTINTO, detiene=True,
                                tomas=tuple(oecf.isoDistintos)))

    # --- Sin balance personalizado: si las dos primeras son Z-V, es que
    #     tienen el mismo balance; si no, la 2.ª ya es de un lado
    if oecf.balancePersonalizado is False:
        mismo = (len(sec.iniciales) >= KS.INICIALES)
        lista.append(Incidencia(code=KI.MISMO_BALANCE if mismo
                                else KI.SIN_BALANCE))

    # --- Secuencia
    sobran = len(sec.iniciales) - KS.INICIALES
    if sobran > 0:
        lista.append(Incidencia(code=KI.INICIALES_SOBRAN, n=sobran))
    if len(sec.lados) < KS.LADOS:
        lista.append(Incidencia(code=KI.LADOS, n=len(sec.lados),
                                esperado=KS.LADOS))
    elif not sec.cambios:
        lista.append(Incidencia(code=KI.SIN_CAMBIO))
    sobran = len(sec.cambios) - KS.CAMBIOS
    if sobran > 0:
        lista.append(Incidencia(code=KI.CAMBIOS_SOBRAN, n=sobran))
    if (len(sec.lados) == KS.LADOS) and (not sec.finales):
        lista.append(Incidencia(code=KI.SIN_FINAL))
    lista += [Incidencia(code=KI.SALTO, tomas=(i,), esperado=esperado,
                         tercioEV=tercioEV)
              for i, esperado, tercioEV in sec.saltos]
    if sec.sobrantes:
        lista.append(Incidencia(code=KI.SOBRANTES, tomas=tuple(sec.sobrantes)))

    # --- Tapadas y balances de cámara
    tapadas = len(oecf.tapadas)
    if tapadas != KS.TAPADAS:
        lista.append(Incidencia(code=KI.TAPADAS_MAL, n=tapadas,
                                esperado=KS.TAPADAS))
    if oecf.tapadasOtroISO and (oecf.isoSerie is not None):
        lista.append(Incidencia(code=KI.ISO_TAPADAS,
                                tomas=tuple(oecf.tapadasOtroISO)))
    if not sec.balances:
        lista.append(Incidencia(code=KI.SIN_BALANCES))

    # --- Posiciones vacías y repetidas (fuera de ZV), tomas que no caben
    #     y tomas desviadas
    lista += [Incidencia(code=KI.SIN_TOMA, detiene=oecf.EsNecesaria(t),
                         tercioEV=t)
              for t in oecf.huecos]
    lista += [Incidencia(code=KI.REPETIDA, n=len(idxs), tercioEV=t)
              for t, idxs in oecf.repetidas.items()]
    if oecf.fuera:
        lista.append(Incidencia(code=KI.FUERA, tomas=tuple(oecf.fuera)))
    if oecf.desviadas:
        lista.append(Incidencia(
            code=KI.DESVIADAS,
            tomas=tuple(oecf.desviadas)))

    # --- Teselas de la Z-V, si ya se midieron
    select = oecf.select
    if (select is not None) and (not select.hayTarjeta):
        lista.append(Incidencia(code=KI.SIN_TARJETA, detiene=True))
    elif (select is not None) and select.rechazadas:
        lista.append(Incidencia(code=KI.RECHAZADAS, n=select.rechazadas,
                                esperado=select.tarjeta,
                                porcentaje=select.porcentaje))
        lista += avisos_rechazadas(select)

    # --- Tras medir: la luz cambió durante la serie
    review = oecf.review
    if (review is not None) and review.controlesDesviados:
        nombres = [raw.name for raw in oecf.raws]
        desviados = review.controlesDesviados
        lista.append(Incidencia(
            code=KI.LUZ_CAMBIO, tomas=tuple(nombres.index(z.archivo)
                                            for z in desviados),
            valores=tuple(review.dev(z) for z in desviados)))
    return lista
