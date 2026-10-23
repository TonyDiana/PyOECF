# -*- coding: utf-8 *-*
"""
    :Propósito: Incidencias de una serie ya leída: códigos con sus datos,
                sin frases. Cada interfaz las traduce
    :Autor:     Tony Diana
    :Versión:   26.10.19
"""

# cSpell:ignore asim, kcom, oecf

__all__ = ["KI", "Incidencia", "avisos_rechazadas", "incidencias"]

# --- Bibliotecas estándar Python
from typing import NamedTuple

# --- Bibliotecas internas
from bib import std
from .constantes import COM as KCOM
from .kernel import OECF
from .revelado import KRV, bits_tiff
from .secuencia import KS
from .teselas import KTE, Select
from .zonas import KP


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
    MEDIO_PASO = "MEDIO_PASO"
    """Serie por medios pasos: impide analizar."""

    PASO_ENTERO = "PASO_ENTERO"
    """Serie por pasos enteros, sin tercios: se analiza sin ellos."""

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

    TAPADAS_CON_LUZ = "TAPADAS_CON_LUZ"
    """Tapadas que no salieron casi negras: se taparon mal (no sirven
    para el negro)."""

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

    # --- Exportaciones del revelador (OECF.exportaciones)
    TIFF_8_BITS = "TIFF_8_BITS"
    """Exportaciones del revelador con menos de KRV.BITS_DEFINITIVOS bits
    por canal (sus posiciones, en tercioEVs): valen para probar el flujo,
    no para el análisis definitivo. Solo se avisa (Tony, 2026-10-21)."""


#
# --- Una incidencia: su código y, según el código, sus datos
class Incidencia(NamedTuple):
    """ Incidencia de la serie: código (KI) y datos, sin frases. """
    codigo: str

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

    # --- Posiciones a las que se refiere, si son varias (TIFF_8_BITS)
    tercioEVs: tuple[int, ...] = ()

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
        avisos.append(Incidencia(codigo=KI.TARJETA_SUCIA,
                                 porcentaje=KCOM.CIEN * sucia))
    nivel = select.part(KTE.RECHAZO_NIVEL)
    if nivel > KTE.AVISO_NIVEL:
        avisos.append(Incidencia(codigo=KI.LUZ_DESIGUAL,
                                 porcentaje=KCOM.CIEN * nivel,
                                 lados=select.ladosNivel))
    total = select.porcentaje / KCOM.CIEN
    if total > KTE.AVISO_REPETIR:
        avisos.append(Incidencia(codigo=KI.REPETIR_SERIE,
                                 porcentaje=select.porcentaje))
    elif total > KTE.AVISO_REVISAR:
        avisos.append(Incidencia(codigo=KI.REVISAR_SERIE,
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
        lista.append(Incidencia(codigo=KI.ISO_DISTINTO, detiene=True,
                                tomas=tuple(oecf.isoDistintos)))

    # --- Sin balance personalizado: si las dos primeras son Z-V, es que
    #     tienen el mismo balance; si no, la 2.ª ya es de un lado
    if oecf.balancePersonalizado is False:
        mismo = (len(sec.iniciales) >= KS.INICIALES)
        lista.append(Incidencia(codigo=KI.MISMO_BALANCE if mismo
                                else KI.SIN_BALANCE))

    # --- Secuencia. Por medios pasos, jamás; por pasos enteros, sí (Tony,
    #     2026-10-19)
    if oecf.medioPaso:
        lista.append(Incidencia(codigo=KI.MEDIO_PASO, detiene=True))
    elif sec.paso == KP.TERCIOS:
        lista.append(Incidencia(codigo=KI.PASO_ENTERO))
    sobran = len(sec.iniciales) - KS.INICIALES
    if sobran > 0:
        lista.append(Incidencia(codigo=KI.INICIALES_SOBRAN, n=sobran))
    if len(sec.lados) < KS.LADOS:
        lista.append(Incidencia(codigo=KI.LADOS, n=len(sec.lados),
                                esperado=KS.LADOS))
    elif not sec.cambios:
        lista.append(Incidencia(codigo=KI.SIN_CAMBIO))
    sobran = len(sec.cambios) - KS.CAMBIOS
    if sobran > 0:
        lista.append(Incidencia(codigo=KI.CAMBIOS_SOBRAN, n=sobran))
    if (len(sec.lados) == KS.LADOS) and (not sec.finales):
        lista.append(Incidencia(codigo=KI.SIN_FINAL))
    lista += [Incidencia(codigo=KI.SALTO, tomas=(i,), esperado=esperado,
                         tercioEV=tercioEV)
              for i, esperado, tercioEV in sec.saltos]
    if sec.sobrantes:
        lista.append(Incidencia(codigo=KI.SOBRANTES,
                                tomas=tuple(sec.sobrantes)))

    # --- Tapadas y balances de cámara
    tapadas = len(oecf.tapadas)
    if tapadas != KS.TAPADAS:
        lista.append(Incidencia(codigo=KI.TAPADAS_MAL, n=tapadas,
                                esperado=KS.TAPADAS))
    if oecf.tapadasConLuz:
        lista.append(Incidencia(codigo=KI.TAPADAS_CON_LUZ,
                                tomas=tuple(oecf.tapadasConLuz)))
    if oecf.tapadasOtroISO and (oecf.isoSerie is not None):
        lista.append(Incidencia(codigo=KI.ISO_TAPADAS,
                                tomas=tuple(oecf.tapadasOtroISO)))
    if not sec.balances:
        lista.append(Incidencia(codigo=KI.SIN_BALANCES))

    # --- Posiciones vacías y repetidas (fuera de ZV), tomas que no caben
    #     y tomas desviadas. Por pasos enteros, los tercios no son huecos
    lista += [Incidencia(codigo=KI.SIN_TOMA, detiene=oecf.EsNecesaria(t),
                         tercioEV=t)
              for t in oecf.huecos if (t % sec.paso) == 0]
    lista += [Incidencia(codigo=KI.REPETIDA, n=len(idxs), tercioEV=t)
              for t, idxs in oecf.repetidas.items()]
    if oecf.fuera:
        lista.append(Incidencia(codigo=KI.FUERA, tomas=tuple(oecf.fuera)))
    if oecf.desviadas:
        lista.append(Incidencia(
            codigo=KI.DESVIADAS,
            tomas=tuple(oecf.desviadas)))

    # --- Teselas de la Z-V, si ya se midieron
    select = oecf.select
    if (select is not None) and (not select.hayTarjeta):
        lista.append(Incidencia(codigo=KI.SIN_TARJETA, detiene=True))
    elif (select is not None) and select.rechazadas:
        lista.append(Incidencia(codigo=KI.RECHAZADAS, n=select.rechazadas,
                                esperado=select.tarjeta,
                                porcentaje=select.porcentaje))
        lista += avisos_rechazadas(select)

    # --- Tras medir: la luz cambió durante la serie
    review = oecf.review
    if (review is not None) and review.controlesDesviados:
        nombres = [raw.name for raw in oecf.raws]
        desviados = review.controlesDesviados
        lista.append(Incidencia(
            codigo=KI.LUZ_CAMBIO, tomas=tuple(nombres.index(z.archivo)
                                              for z in desviados),
            valores=tuple(review.dev(z) for z in desviados)))

    # --- Exportaciones del revelador con menos bits que las definitivas
    pocos = []
    for tercio_ev, ruta in sorted(oecf.exportaciones.items()):
        bits = bits_tiff(ruta)
        if (bits is not None) and (bits < KRV.BITS_DEFINITIVOS):
            pocos.append(tercio_ev)
    if pocos:
        lista.append(Incidencia(codigo=KI.TIFF_8_BITS, n=len(pocos),
                                tercioEVs=tuple(pocos)))
    return lista
