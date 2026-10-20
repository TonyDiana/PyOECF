# -*- coding: utf-8 *-*
"""
    :Propósito: El protocolo de la serie (KS) y su reparto en partes:
                iniciales, lados, cambio, final, tapadas, balances de
                cámara, sobrantes y saltos, y la ZV. También, si se hizo
                el balance personalizado
    :Autor:     Tony Diana
    :Versión:   26.10.19
"""

# cSpell:ignore

__all__ = ["KS", "Secuencia", "balance_personalizado", "secuencia"]

# --- Bibliotecas estándar Python
from typing import NamedTuple

# --- Bibliotecas internas
from bib import std
from .zonas import KP


#
# --- Constantes de la secuencia de tomas
class KS(std.EnumMutable):
    """ Tomas que pide el protocolo en cada parte de la serie. """

    INICIALES = 2
    """Z-V iniciales: con balance arbitrario y con el personalizado."""

    TERCIOS_LADO = 15
    """Tomas de cada lado, de 1/3 en 1/3."""

    LADOS = 2
    """Lados de la serie: uno por encima de la Z-V y otro por debajo."""

    CAMBIOS = 1
    """Z-V de cambio de lado."""

    FINALES = 1
    """Z-V final: tras el segundo lado, con el balance de la serie y con
    las tapadas detrás; marca el fin de la serie."""

    TAPADAS = 2
    """Tomas tapadas (solo tras la Z-V final)."""

    MIN_LADO = TERCIOS_LADO // 2
    """Una racha solo cuenta como lado si tiene al menos estas tomas (la
    mitad de un lado): así, una toma suelta no es un lado."""

    MIN_BALANCES = 2
    """Una racha de Z-V solo cuenta como balances de cámara si tiene al
    menos estas tomas: así, una Z-V suelta no es un balance."""


#
# --- Partes de una serie
class Secuencia(NamedTuple):
    """
    Partes de una serie: índices de sus tomas (en el orden de la lista que
    se repartió) y los saltos de cada lado: (índice, tercioEV esperado,
    tercioEV). zv: la ZV de la serie, la última de cambio o, si no hay,
    la última inicial (None si no hay ninguna: Tony, 2026-10-19). paso:
    tercios de cada paso de los lados, 1 (por tercios) o KP.TERCIOS (por
    pasos enteros, sin tercios: Tony, 2026-10-19).
    """
    iniciales: list[int]
    lados: list[list[int]]
    cambios: list[int]
    finales: list[int]
    tapadas: list[int]
    balances: list[int]
    sobrantes: list[int]
    saltos: list[tuple[int, int, int]]
    zv: int | None
    paso: int


#
def balance_personalizado(tercioEVs: list[int | None],
                          balances: list[tuple[float, ...] | None]
                          ) -> bool | None:
    """
    ¿Se hizo el balance de blancos personalizado inicial? Las dos primeras
    tomas deben ser Z-V (tercioEV = 0) con balances distintos: la 1.ª con
    el que tenga la cámara y la 2.ª con el personalizado. False si la 2.ª
    ya es de un lado (un tercio más o menos) o si las dos tienen el mismo
    balance; None si no se puede saber. tercioEVs: el de cada toma, en su
    orden (None si no se pudo leer). balances: balance de blancos de las
    dos primeras (None si no se pudo leer).
    """
    if (len(tercioEVs) < KS.INICIALES) or (tercioEVs[1] is None):
        return None
    if tercioEVs[1] != 0:
        return False if (abs(tercioEVs[1]) == 1) else None
    if None in balances:
        return None
    return balances[0] != balances[1]


#
def secuencia(tercioEVs: list[int | None], de_tapada: list[bool],
              WBs: list[tuple[float, ...] | None]) -> Secuencia:
    """
    Reparte la serie en sus partes. Las tomas se agrupan en rachas
    seguidas de tercioEV = 0 (Z-V) o de tercioEV del mismo signo (un
    lado). Si algo se repitió, la buena es la última vez. Los dos lados
    son la última pareja de lados de signo contrario seguidos, con o sin
    Z-V de cambio entre ellos, y con al menos KS.MIN_LADO tomas cada uno.
    Si no hay ninguna, los dos más largos de signo contrario (los últimos
    si empatan). Las Z-V del principio son las iniciales; las de entre los
    dos lados, las de cambio. La ZV de la serie es la última de cambio o,
    si no hay, la última inicial, y su balance (WBs) es el de la serie.
    Las tomas con la exposición de las tapadas (f/11 y 1/160) nunca van a
    los lados ni a ninguna zona. Final: las Z-V justo después del segundo
    lado con el balance de la serie, solo si detrás de la última va una
    con la exposición de las tapadas; marca el fin de la serie. Las
    tapadas son las que la tienen y van detrás de la final: sin final no
    hay tapadas, y sobran (Tony, 2026-10-19). Balances de cámara, con al
    menos KS.MIN_BALANCES tomas: con tapadas, las Z-V que van detrás de
    la última; sin ellas, las Z-V tras el segundo lado desde la primera
    con un balance distinto del de la serie (Tony, 2026-10-19). La serie
    va por pasos enteros si todas las tomas de los lados caen en una zona
    entera; si no, por tercios. En cada lado, el tercioEV debe avanzar de
    paso en paso desde ±1 paso: lo que no, es un salto (repetida, saltada
    o fuera de orden), y lo que pasa de ±KS.TERCIOS_LADO sobra. Las que no
    se pudieron leer no cuentan. de_tapada (si tiene la exposición de las
    tapadas) y WBs: de cada toma, en el orden de tercioEVs.
    """
    # --- Las tomas leídas, en su orden; y, sin las de la exposición de
    #     las tapadas, {índice: tercioEV}
    leidas = [i for i, tercioEV in enumerate(tercioEVs)
              if tercioEV is not None]
    tomas: dict[int, int] = {i: tercioEVs[i] for i in leidas
                             if not de_tapada[i]}           # type: ignore

    # --- Rachas: (signo: 0, 1 o -1, índices de sus tomas)
    rachas: list[tuple[int, list[int]]] = []
    for i, tercioEV in tomas.items():
        signo = (tercioEV > 0) - (tercioEV < 0)
        if rachas and (rachas[-1][0] == signo):
            rachas[-1][1].append(i)
        else:
            rachas.append((signo, [i]))

    # --- Los dos lados (posiciones en rachas): la última pareja de
    #     lados de signo contrario, seguidos o con una racha de Z-V en
    #     medio, los dos con al menos KS.MIN_LADO tomas
    elegidas: list[int] = []
    for n, (signo, tomas_racha) in enumerate(rachas):
        if (not signo) or (len(tomas_racha) < KS.MIN_LADO):
            continue
        for m in (n + 1, n + 2):
            if m >= len(rachas):
                break
            seguidas = (m == (n + 1)) or (rachas[n + 1][0] == 0)
            if (seguidas and (rachas[m][0] == -signo)
                    and (len(rachas[m][1]) >= KS.MIN_LADO)):
                elegidas = [n, m]
                break

    # --- Sin pareja: el lado más largo y el más largo de signo contrario
    #     (los últimos si empatan)
    if not elegidas:
        candidatas = [n for n, (s, _) in enumerate(rachas) if s]
        if candidatas:
            primera = _mas_larga(candidatas, rachas)
            elegidas = [primera]
            contrarias = [n for n in candidatas
                          if rachas[n][0] == -rachas[primera][0]]
            if contrarias:
                elegidas.append(_mas_larga(contrarias, rachas))
            elegidas.sort()

    # --- Lados, recortando lo que pasa de ±KS.TERCIOS_LADO
    lados: list[list[int]] = []
    usadas = set()
    for n in elegidas:
        lado = [i for i in rachas[n][1] if abs(tomas[i]) <= KS.TERCIOS_LADO]
        lados.append(lado)
        usadas.update(lado)

    # --- Paso: enteros si todas las tomas de los lados caen en una zona
    #     entera; si no, tercios. Saltos: lo que no avanza de paso en paso
    de_lados = [tomas[i] for lado in lados for i in lado]
    paso = (KP.TERCIOS
            if (de_lados and all((t % KP.TERCIOS) == 0 for t in de_lados))
            else 1)
    saltos: list[tuple[int, int, int]] = []
    for n, lado in zip(elegidas, lados):
        signo = rachas[n][0]
        anterior = 0
        for i in lado:
            esperado = anterior + (signo * paso)
            if tomas[i] != esperado:
                saltos.append((i, esperado, tomas[i]))
            anterior = tomas[i]

    # --- Z-V iniciales (la racha del principio, si es de Z-V) y de
    #     cambio (entre los lados)
    iniciales = rachas[0][1] if (rachas and (rachas[0][0] == 0)) else []
    dos_lados = (len(elegidas) == KS.LADOS)
    entre = (range(elegidas[0] + 1, elegidas[1]) if dos_lados
             else range(0))
    cambios = [i for n in entre if rachas[n][0] == 0 for i in rachas[n][1]]

    # --- ZV: la última de cambio o, si no hay, la última inicial. Su
    #     balance es el de la serie
    zv = cambios[-1] if cambios else (iniciales[-1] if iniciales else None)
    wb_serie = WBs[zv] if (zv is not None) else None

    # --- Z-V tras el segundo lado, en su orden (ninguna sin dos lados)
    ultima_lado = lados[-1][-1] if (dos_lados and lados[-1]) else None
    tras = ([i for i, tercioEV in tomas.items()
             if (i > ultima_lado) and (tercioEV == 0)]
            if (ultima_lado is not None) else [])

    # --- Final: las Z-V seguidas justo después del segundo lado con el
    #     balance de la serie, si detrás de la última va una con la
    #     exposición de las tapadas. Las tapadas, las que la tengan y
    #     vayan detrás
    finales: list[int] = []
    if ultima_lado is not None:
        for i in leidas:
            if i <= ultima_lado:
                continue
            if de_tapada[i] or (tomas[i] != 0) or (WBs[i] != wb_serie):
                break
            finales.append(i)
    if finales:
        siguiente = next((i for i in leidas if i > finales[-1]), None)
        if (siguiente is None) or (not de_tapada[siguiente]):
            finales = []
    tapadas = ([i for i in leidas if de_tapada[i] and (i > finales[-1])]
               if finales else [])

    # --- Balances de cámara: con tapadas, las Z-V tras la última; sin
    #     ellas, las Z-V tras el segundo lado desde la primera con otro
    #     balance que el de la serie
    if tapadas:
        balances = [i for i in tras if i > tapadas[-1]]
    else:
        desde = next((n for n, i in enumerate(tras)
                      if WBs[i] != wb_serie), len(tras))
        balances = tras[desde:]
    if len(balances) < KS.MIN_BALANCES:
        balances = []
    usadas.update(iniciales, cambios, finales, tapadas, balances)

    sobrantes = [i for i in leidas if i not in usadas]
    return Secuencia(
        iniciales=iniciales,
        lados=lados,
        cambios=cambios,
        finales=finales,
        tapadas=tapadas,
        balances=balances,
        sobrantes=sobrantes,
        saltos=saltos,
        zv=zv,
        paso=paso)


#
# --- De estas posiciones en rachas, la de la racha con más tomas (la
#     última si empatan)
def _mas_larga(posiciones: list[int],
               rachas: list[tuple[int, list[int]]]) -> int:
    mejor = posiciones[0]
    for n in posiciones:
        if len(rachas[n][1]) >= len(rachas[mejor][1]):
            mejor = n
    return mejor
