# -*- coding: utf-8 *-*
"""
    :Propósito: Incidencias de una serie ya leída: códigos con sus datos,
                sin frases. Cada interfaz las traduce
    :Autor:     Tony Diana
    :Versión:   26.10.24
"""

# cSpell:ignore asim, codigo, devs, idxs, kcom, oecf

__all__ = ["Incidencia", "incidencia_a_dict", "avisos_rechazadas",
           "calcular_incidencias"]

# --- Bibliotecas estándar Python
from pathlib import Path
from typing import NamedTuple

# --- Bibliotecas internas
from bib.oecfMediadores import KFR, KI, KP
from kernel import COM as KCOM
from .oecf import OECF
from .secuencia import KS, tercios_sombra, z2_medible
from .teselas import KTE, Select


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
    #     cada una de la ZV, en zonas; DESVIADAS: su desvío, en tercios)
    valores: tuple[float, ...] = ()

    # --- Mitades de la toma, si las lleva (LUZ_DESIGUAL: KTE.LADO_*)
    lados: tuple[str, ...] = ()


#
def incidencia_a_dict(incidencia: Incidencia, raws: list[Path]) -> dict:
    """
    La incidencia como se graba en el JSON (grupo incidencias): sus campos,
    con las tomas por el nombre de su archivo en vez de su índice en raws.
    Es lo que recibe common.marcadores_incidencia
    """
    return {
        KFR.J_CODIGO: incidencia.codigo,
        KFR.J_DETIENE: incidencia.detiene,
        KFR.J_TOMAS: tuple(raws[t].name for t in incidencia.tomas),
        KFR.J_N: incidencia.n,
        KFR.J_ESPERADO: incidencia.esperado,
        KFR.J_TERCIO_EV: incidencia.tercioEV,
        KFR.J_TERCIO_EVS: incidencia.tercioEVs,
        KFR.J_PORCENTAJE: incidencia.porcentaje,
        KFR.J_VALORES: incidencia.valores,
        KFR.J_LADOS: incidencia.lados}


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
def calcular_incidencias(oecf: OECF) -> list[Incidencia]:
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

    # --- Secuencia de ISO: marcadores con la exposición de las tapadas
    #     (se aceptan: Tony, 2026-11-10), sin marcador final, ISO cuya
    #     Z2 no está justo en su sitio (estimación; sus Z2) e ISO que no
    #     se pueden medir (de cada uno, su Z-V o, sin ella, su Z2)
    con_tapada = [i for i in sec.marcadores if oecf.tomas[i].tapada]
    if con_tapada:
        lista.append(Incidencia(codigo=KI.MARCADOR_TAPADAS,
                                tomas=tuple(con_tapada)))
    if len(sec.marcadores) == 1:
        lista.append(Incidencia(codigo=KI.SIN_MARCADOR_FINAL))
    estimados: list[int] = []
    sin_medir: list[int] = []
    for bloque in sec.bloques.values():
        if (bloque.zv is None) and (bloque.z2 is None):
            continue
        tercio = (oecf.tercioEVs[bloque.z2] if (bloque.z2 is not None)
                  else None)
        if not z2_medible(tercio, bloque.zv is not None):
            sin_medir.append(bloque.zv if (bloque.zv is not None)
                             else bloque.z2)                    # type: ignore
        elif tercio != tercios_sombra(tercio):
            estimados.append(bloque.z2)                         # type: ignore
    if estimados:
        lista.append(Incidencia(codigo=KI.ISO_ESTIMADO,
                                tomas=tuple(estimados)))
    if sin_medir:
        lista.append(Incidencia(codigo=KI.ISO_SIN_MEDIR,
                                tomas=tuple(sin_medir)))

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
        # --- Una desviada siempre tiene su desvío (así se eligen), aunque
        #     devs admite None
        lista.append(Incidencia(
            codigo=KI.DESVIADAS,
            tomas=tuple(oecf.desviadas),
            valores=tuple(oecf.devs[i]                          # type: ignore
                          for i in oecf.desviadas)))

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

    # --- Con negro medido (tapadas): las sombras salen más claras de lo que
    #     dice su tiempo de exposición (antiparpadeo, obturador, luz que
    #     parpadea)
    if (review is not None) and (review.origen_negro == KTE.ORIGEN_TAPADAS):
        alzadas = review.sombrasAlzadas
        if (alzadas is not None) and (alzadas > KCOM.TOLERANCIA_LINEAL):
            lista.append(Incidencia(
                codigo=KI.SOMBRAS_ALZADAS,
                porcentaje=KCOM.CIEN * ((2.0 ** alzadas) - 1)))
    return lista
