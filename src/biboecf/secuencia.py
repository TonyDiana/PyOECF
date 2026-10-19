# -*- coding: utf-8 *-*
"""
    :Propósito: El protocolo de la serie (KS) y su reparto en partes:
                iniciales, lados, cambio, balances de cámara, sobrantes y
                saltos. También, si se hizo el balance personalizado
    :Autor:     Tony Diana
    :Versión:   26.10.18
"""

# cSpell:ignore

__all__ = ["KS", "Secuencia", "balance_personalizado", "secuencia"]

# --- Bibliotecas estándar Python
from typing import NamedTuple

# --- Bibliotecas internas
from bib import std


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
    """Z-V final: tras el segundo lado, marca el fin de la serie."""

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
    tercioEV).
    """
    iniciales: list[int]
    lados: list[list[int]]
    cambios: list[int]
    finales: list[int]
    tapadas: list[int]
    balances: list[int]
    sobrantes: list[int]
    saltos: list[tuple[int, int, int]]


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
def secuencia(tercioEVs: list[int | None], oscuras: list[bool]) -> Secuencia:
    """
    Reparte la serie en sus partes. Las tomas se agrupan en rachas
    seguidas de tercioEV = 0 (Z-V) o de tercioEV del mismo signo (un
    lado). Si algo se repitió, la buena es la última vez. Los dos lados
    son la última pareja de lados de signo contrario seguidos, con o sin
    Z-V de cambio entre ellos, y con al menos KS.MIN_LADO tomas cada uno.
    Si no hay ninguna, los dos más largos de signo contrario (los últimos
    si empatan). Las Z-V del principio son las iniciales; las de entre los
    dos lados, las de cambio; la primera Z-V justo después del segundo
    lado, la final, que marca el fin de la serie. Las tapadas son las
    oscuras (a 1/160 y casi negras) que van detrás de la final: sin final,
    no se buscan, y las oscuras de antes son tomas normales. Los balances
    de cámara, la racha de Z-V más larga de las demás, sin la final ni las
    tapadas, con al menos KS.MIN_BALANCES tomas (la última si empatan),
    esté donde esté. En cada lado, el tercioEV debe avanzar de uno en uno
    desde ±1: lo que no, es un salto (repetida, saltada o fuera de orden),
    y lo que pasa de ±KS.TERCIOS_LADO sobra. Las que no se pudieron leer
    no cuentan.
    """
    # --- Las tomas leídas: {índice: tercioEV}, en su orden
    tomas: dict[int, int] = {i: tercioEV
                             for i, tercioEV in enumerate(tercioEVs)
                             if tercioEV is not None}

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

    # --- Lados, recortando lo que pasa de ±KS.TERCIOS_LADO, y sus saltos
    lados: list[list[int]] = []
    saltos: list[tuple[int, int, int]] = []
    usadas = set()
    for n in elegidas:
        signo, tomas_racha = rachas[n]
        lado = [i for i in tomas_racha if abs(tomas[i]) <= KS.TERCIOS_LADO]
        lados.append(lado)
        usadas.update(lado)
        anterior = 0
        for i in lado:
            esperado = anterior + signo
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

    # --- Z-V final: la primera de la racha de Z-V justo después del
    #     segundo lado. Las tapadas, las oscuras que vayan detrás
    tras_lados = (elegidas[-1] + 1) if dos_lados else len(rachas)
    hay_final = ((tras_lados < len(rachas))
                 and (rachas[tras_lados][0] == 0))
    finales = [rachas[tras_lados][1][0]] if hay_final else []
    tapadas = ([i for i, oscura in enumerate(oscuras)
                if oscura and (i > finales[0])] if finales else [])

    # --- Balances de cámara: de las demás rachas de Z-V, sin la final ni
    #     las tapadas, la más larga (la última si empatan)
    quitar = set(finales) | set(tapadas)
    otras = [[i for i in tomas_racha if i not in quitar]
             for n, (s, tomas_racha) in enumerate(rachas)
             if (s == 0) and (n != 0) and (n not in entre)]
    otras = [tomas_racha for tomas_racha in otras
             if len(tomas_racha) >= KS.MIN_BALANCES]
    balances = (max(reversed(otras), key=len) if otras else [])
    usadas.update(iniciales, cambios, finales, tapadas, balances)

    sobrantes = [i for i in tomas if i not in usadas]
    return Secuencia(
        iniciales=iniciales,
        lados=lados,
        cambios=cambios,
        finales=finales,
        tapadas=tapadas,
        balances=balances,
        sobrantes=sobrantes,
        saltos=saltos)


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
