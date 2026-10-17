# -*- coding: utf-8 *-*
"""
    :Propósito: Incidencias de una serie ya leída: códigos con sus datos,
                sin frases. Cada interfaz las traduce
    :Autor:     Tony Diana
    :Versión:   26.10.12
"""

# cSpell:ignore

__all__ = ["KI", "Incidencia", "avisos_rechazadas", "incidencias"]

# --- Bibliotecas estándar Python
from typing import NamedTuple

# --- Bibliotecas internas
from bib import clases
from .constantes import COM as KCOM
from .kernel import OECF
from .secuencia import KS
from .teselas import KTE, Seleccion


#
class KI(clases.EnumMutable):
    """ Códigos de las incidencias, en el orden en que se informan. """

    # --- ISO distinto del de la ZV en la serie: impide analizar
    ISO_DISTINTO = "ISO_DISTINTO"

    # --- Balance personalizado: las dos primeras son Z-V con el mismo
    #     balance, o la 2.ª ya es de un lado
    MISMO_BALANCE = "MISMO_BALANCE"
    SIN_BALANCE = "SIN_BALANCE"

    # --- Secuencia (ver OECF.secuencia)
    INICIALES_SOBRAN = "INICIALES_SOBRAN"
    LADOS = "LADOS"
    SIN_CAMBIO = "SIN_CAMBIO"
    CAMBIOS_SOBRAN = "CAMBIOS_SOBRAN"
    SIN_FINAL = "SIN_FINAL"
    SALTO = "SALTO"
    SOBRANTES = "SOBRANTES"

    # --- Tapadas y balances de cámara
    TAPADAS_MAL = "TAPADAS_MAL"
    ISO_TAPADAS = "ISO_TAPADAS"
    SIN_BALANCES = "SIN_BALANCES"

    # --- Posiciones de la rejilla y tomas que no caben o se desvían. Una
    #     posición sin toma impide analizar si es de Z1 a Z9
    SIN_TOMA = "SIN_TOMA"
    REPETIDA = "REPETIDA"
    FUERA = "FUERA"
    DESVIADAS = "DESVIADAS"

    # --- Teselas de la Z-V (tras OECF.Seleccionar): sin tarjeta gris no
    #     se analiza; las de tarjeta que rechazan los filtros, cuántas y
    #     qué porcentaje de las de tarjeta
    SIN_TARJETA = "SIN_TARJETA"
    RECHAZADAS = "RECHAZADAS"

    # --- Avisos de las rechazadas, uno por causa (ver KTE.AVISO_*):
    #     tarjeta sucia o dañada (dispersión o asimetría), luz desigual
    #     (nivel, con sus lados) y, por el total, revisar o repetir
    TARJETA_SUCIA = "TARJETA_SUCIA"
    LUZ_DESIGUAL = "LUZ_DESIGUAL"
    REVISAR_SERIE = "REVISAR_SERIE"
    REPETIR_SERIE = "REPETIR_SERIE"

    # --- Tras medir (OECF.Medir): Z-V de control que se apartan de la
    #     ZV más que la tolerancia de linealidad (la luz cambió); no
    #     entran en la media de las Z-V
    LUZ_CAMBIO = "LUZ_CAMBIO"


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

    # --- Un porcentaje, si lo lleva (RECHAZADAS)
    porcentaje: float = 0.0

    # --- Un valor por toma, si lo lleva (LUZ_CAMBIO: cuánto se aparta
    #     cada una de la ZV, en zonas)
    valores: tuple[float, ...] = ()

    # --- Mitades de la toma, si las lleva (LUZ_DESIGUAL: KTE.LADO_*)
    lados: tuple[str, ...] = ()


#
def avisos_rechazadas(seleccion: Seleccion) -> list[Incidencia]:
    """
    Avisos de las teselas rechazadas, uno por causa (ver KTE.AVISO_*):
    tarjeta sucia (el porcentaje mayor de dispersión y asimetría), luz
    desigual (el de nivel y sus lados) y, por el total, revisar o
    repetir la serie. Porcentajes de las teselas de tarjeta.
    """
    avisos = []
    sucia = max(seleccion.fraccion(KTE.RECHAZO_DISPERSION),
                seleccion.fraccion(KTE.RECHAZO_ASIMETRIA))
    if sucia > KTE.AVISO_SUCIA:
        avisos.append(Incidencia(KI.TARJETA_SUCIA,
                                 porcentaje=KCOM.CIEN * sucia))
    nivel = seleccion.fraccion(KTE.RECHAZO_NIVEL)
    if nivel > KTE.AVISO_NIVEL:
        avisos.append(Incidencia(KI.LUZ_DESIGUAL,
                                 porcentaje=KCOM.CIEN * nivel,
                                 lados=seleccion.ladosNivel))
    total = seleccion.porcentaje / KCOM.CIEN
    if total > KTE.AVISO_REPETIR:
        avisos.append(Incidencia(KI.REPETIR_SERIE,
                                 porcentaje=seleccion.porcentaje))
    elif total > KTE.AVISO_REVISAR:
        avisos.append(Incidencia(KI.REVISAR_SERIE,
                                 porcentaje=seleccion.porcentaje))
    return avisos


#
def incidencias(oecf: OECF) -> list[Incidencia]:
    """ Incidencias de una serie ya leída, en orden ([] si no se leyó). """
    sec = oecf.secuencia
    if sec is None:
        return []
    lista: list[Incidencia] = []

    # --- ISO distinto en la serie: lo primero, porque impide analizar
    if oecf.isoDistintos and oecf.isoSerie is not None:
        lista.append(Incidencia(KI.ISO_DISTINTO, detiene=True,
                                tomas=tuple(oecf.isoDistintos)))

    # --- Sin balance personalizado: si las dos primeras son Z-V, es que
    #     tienen el mismo balance; si no, la 2.ª ya es de un lado
    if oecf.balancePersonalizado is False:
        mismo = len(sec.iniciales) >= KS.INICIALES
        lista.append(Incidencia(KI.MISMO_BALANCE if mismo
                                else KI.SIN_BALANCE))

    # --- Secuencia
    sobran = len(sec.iniciales) - KS.INICIALES
    if sobran > 0:
        lista.append(Incidencia(KI.INICIALES_SOBRAN, n=sobran))
    if len(sec.lados) < KS.LADOS:
        lista.append(Incidencia(KI.LADOS, n=len(sec.lados),
                                esperado=KS.LADOS))
    elif not sec.cambios:
        lista.append(Incidencia(KI.SIN_CAMBIO))
    sobran = len(sec.cambios) - KS.CAMBIOS
    if sobran > 0:
        lista.append(Incidencia(KI.CAMBIOS_SOBRAN, n=sobran))
    if len(sec.lados) == KS.LADOS and not sec.finales:
        lista.append(Incidencia(KI.SIN_FINAL))
    lista += [Incidencia(KI.SALTO, tomas=(i,), esperado=esperado,
                         tercioEV=tercioEV)
              for i, esperado, tercioEV in sec.saltos]
    if sec.sobrantes:
        lista.append(Incidencia(KI.SOBRANTES, tomas=tuple(sec.sobrantes)))

    # --- Tapadas y balances de cámara
    tapadas = len(oecf.tapadas)
    if tapadas != KS.TAPADAS:
        lista.append(Incidencia(KI.TAPADAS_MAL, n=tapadas,
                                esperado=KS.TAPADAS))
    if oecf.tapadasOtroISO and oecf.isoSerie is not None:
        lista.append(Incidencia(KI.ISO_TAPADAS,
                                tomas=tuple(oecf.tapadasOtroISO)))
    if not sec.balances:
        lista.append(Incidencia(KI.SIN_BALANCES))

    # --- Posiciones vacías y repetidas (fuera de ZV), tomas que no caben
    #     y tomas desviadas
    lista += [Incidencia(KI.SIN_TOMA, detiene=oecf.EsNecesaria(t),
                         tercioEV=t)
              for t in oecf.vacias]
    lista += [Incidencia(KI.REPETIDA, n=len(indices), tercioEV=t)
              for t, indices in oecf.repetidas.items()]
    if oecf.fuera:
        lista.append(Incidencia(KI.FUERA, tomas=tuple(oecf.fuera)))
    if oecf.desviadas:
        lista.append(Incidencia(KI.DESVIADAS, tomas=tuple(oecf.desviadas)))

    # --- Teselas de la Z-V, si ya se midieron
    seleccion = oecf.seleccion
    if seleccion is not None and not seleccion.hayTarjeta:
        lista.append(Incidencia(KI.SIN_TARJETA, detiene=True))
    elif seleccion is not None and seleccion.rechazadas:
        lista.append(Incidencia(KI.RECHAZADAS, n=seleccion.rechazadas,
                                esperado=seleccion.tarjeta,
                                porcentaje=seleccion.porcentaje))
        lista += avisos_rechazadas(seleccion)

    # --- Tras medir: la luz cambió durante la serie
    analisis = oecf.analisis
    if analisis is not None and analisis.controlesDesviados:
        nombres = [raw.name for raw in oecf.raws]
        desviados = analisis.controlesDesviados
        lista.append(Incidencia(
            KI.LUZ_CAMBIO, tomas=tuple(nombres.index(z.archivo)
                                       for z in desviados),
            valores=tuple(analisis.desvio(z) for z in desviados)))
    return lista
