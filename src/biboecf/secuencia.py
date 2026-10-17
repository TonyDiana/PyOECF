# -*- coding: utf-8 *-*
"""
    :Propósito: El protocolo de la serie (KS) y su reparto en partes:
                iniciales, lados, cambio, balances de cámara, sobrantes y
                saltos. También, si se hizo el balance personalizado
    :Autor:     Tony Diana
    :Versión:   26.10.06
"""

# cSpell:ignore

__all__ = ["KS", "Secuencia", "balance_personalizado", "secuencia"]

# --- Bibliotecas estándar Python
from typing import NamedTuple

# --- Bibliotecas internas
from bib import clases


#
# --- Constantes de la secuencia de tomas
class KS(clases.EnumMutable):
    """ Tomas que pide el protocolo en cada parte de la serie. """

    # --- Z-V iniciales: con balance arbitrario y con el personalizado
    INICIALES = 2

    # --- Tomas de cada lado, de 1/3 en 1/3, y lados
    TERCIOS_LADO = 15
    LADOS = 2

    # --- Z-V de cambio de lado, Z-V final (tras el segundo lado: marca
    #     el fin de la serie) y tomas tapadas (solo tras la final)
    CAMBIOS = 1
    FINALES = 1
    TAPADAS = 2

    # --- Una racha solo cuenta como lado si tiene al menos estas tomas
    #     (la mitad de un lado): así, una toma suelta no es un lado
    MINIMO_LADO = TERCIOS_LADO // 2

    # --- Una racha de Z-V solo cuenta como balances de cámara si tiene al
    #     menos estas tomas: así, una Z-V suelta no es un balance
    MINIMO_BALANCES = 2


#
# --- Partes de una serie: índices de sus tomas (en el orden de la lista
#     que se repartió) y los saltos de cada lado: (índice, tercioEV
#     esperado, tercioEV)
class Secuencia(NamedTuple):
    iniciales: list[int]
    lados: list[list[int]]
    cambios: list[int]
    finales: list[int]
    tapadas: list[int]
    balances: list[int]
    sobrantes: list[int]
    saltos: list[tuple[int, int, int]]


# --- ¿Se hizo el balance de blancos personalizado inicial? Las dos
#     primeras tomas deben ser Z-V (tercioEV = 0) con balances
#     distintos: la 1.ª con el que tenga la cámara y la 2.ª con el
#     personalizado. False si la 2.ª ya es de un lado (un tercio más o
#     menos) o si las dos tienen el mismo balance; None si no se puede
#     saber. tercioEVs: el de cada toma, en su orden (None si no se pudo
#     leer). balances: balance de blancos de las dos primeras (None si no
#     se pudo leer)
def balance_personalizado(tercioEVs: list[int | None],
                          balances: list[tuple[float, ...] | None]
                          ) -> bool | None:
    if len(tercioEVs) < KS.INICIALES or tercioEVs[1] is None:
        return None
    if tercioEVs[1] != 0:
        return False if abs(tercioEVs[1]) == 1 else None
    if None in balances:
        return None
    return balances[0] != balances[1]


# --- Reparte la serie en sus partes. Las tomas se agrupan en rachas
#     seguidas de tercioEV = 0 (Z-V) o de tercioEV del mismo signo (un
#     lado). Si algo se repitió, la buena es la última vez. Los dos
#     lados son la última pareja de lados de signo contrario seguidos,
#     con o sin Z-V de cambio entre ellos, y con al menos minimo_lado
#     tomas cada uno. Si no hay ninguna, los dos más largos de signo
#     contrario (los últimos si empatan). Las Z-V del principio son las
#     iniciales; las de entre los dos lados, las de cambio; la primera
#     Z-V justo después del segundo lado, la final, que marca el fin de
#     la serie. Las tapadas son las oscuras (a 1/160 y casi negras) que
#     van detrás de la final: sin final, no se buscan, y las oscuras de
#     antes son tomas normales. Los balances de cámara, la racha de Z-V
#     más larga de las demás, sin la final ni las tapadas, con al menos
#     minimo_balances tomas (la última si empatan), esté donde esté. En
#     cada lado, el tercioEV debe avanzar de uno en uno desde ±1: lo que
#     no, es un salto (repetida, saltada o fuera de orden), y lo que pasa
#     de ±tercios_lado sobra. Las que no se pudieron leer no cuentan
def secuencia(tercioEVs: list[int | None], oscuras: list[bool]) -> Secuencia:
    tomas = [(i, tercioEV) for i, tercioEV in enumerate(tercioEVs)
             if tercioEV is not None]

    # --- Rachas: (signo: 0, 1 o -1, índices de sus tomas)
    rachas: list[tuple[int, list[int]]] = []
    for i, tercioEV in tomas:
        signo = (tercioEV > 0) - (tercioEV < 0)
        if rachas and rachas[-1][0] == signo:
            rachas[-1][1].append(i)
        else:
            rachas.append((signo, [i]))

    # --- Los dos lados (posiciones en rachas): la última pareja de
    #     lados de signo contrario, seguidos o con una racha de Z-V en
    #     medio, los dos con al menos minimo_lado tomas
    elegidas: list[int] = []
    for n, (signo, indices) in enumerate(rachas):
        if not signo or len(indices) < KS.MINIMO_LADO:
            continue
        for m in (n + 1, n + 2):
            if m >= len(rachas):
                break
            seguidas = m == n + 1 or rachas[n + 1][0] == 0
            if (seguidas and rachas[m][0] == -signo
                    and len(rachas[m][1]) >= KS.MINIMO_LADO):
                elegidas = [n, m]
                break

    # --- Sin pareja: el lado más largo y el más largo de signo contrario
    #     (los últimos si empatan)
    if not elegidas:
        candidatas = [n for n, (s, _) in enumerate(rachas) if s]
        if candidatas:
            primera = max(reversed(candidatas),
                          key=lambda n: len(rachas[n][1]))
            elegidas = [primera]
            contrarias = [n for n in candidatas
                          if rachas[n][0] == -rachas[primera][0]]
            if contrarias:
                elegidas.append(max(reversed(contrarias),
                                    key=lambda n: len(rachas[n][1])))
            elegidas.sort()

    # --- Lados, recortando lo que pasa de ±tercios_lado, y sus saltos
    lados: list[list[int]] = []
    saltos: list[tuple[int, int, int]] = []
    usadas = set()
    for n in elegidas:
        signo, indices = rachas[n]
        lado = [i for i in indices if abs(tercioEVs[i]) <= KS.TERCIOS_LADO]
        lados.append(lado)
        usadas.update(lado)
        anterior = 0
        for i in lado:
            esperado = anterior + signo
            if tercioEVs[i] != esperado:
                saltos.append((i, esperado, tercioEVs[i]))      # type: ignore
            anterior = tercioEVs[i]                             # type: ignore

    # --- Z-V iniciales (la racha del principio, si es de Z-V) y de
    #     cambio (entre los lados)
    iniciales = rachas[0][1] if rachas and rachas[0][0] == 0 else []
    dos_lados = len(elegidas) == KS.LADOS
    entre = (range(elegidas[0] + 1, elegidas[1]) if dos_lados
             else range(0))
    cambios = [i for n in entre if rachas[n][0] == 0 for i in rachas[n][1]]

    # --- Z-V final: la primera de la racha de Z-V justo después del
    #     segundo lado. Las tapadas, las oscuras que vayan detrás
    tras_lados = elegidas[-1] + 1 if dos_lados else len(rachas)
    hay_final = tras_lados < len(rachas) and rachas[tras_lados][0] == 0
    finales = [rachas[tras_lados][1][0]] if hay_final else []
    tapadas = ([i for i, oscura in enumerate(oscuras)
                if oscura and i > finales[0]] if finales else [])

    # --- Balances de cámara: de las demás rachas de Z-V, sin la final ni
    #     las tapadas, la más larga (la última si empatan)
    quitar = set(finales) | set(tapadas)
    otras = [[i for i in indices if i not in quitar]
             for n, (s, indices) in enumerate(rachas)
             if s == 0 and n != 0 and n not in entre]
    otras = [indices for indices in otras
             if len(indices) >= KS.MINIMO_BALANCES]
    balances = (max(reversed(otras), key=len) if otras else [])
    usadas.update(iniciales, cambios, finales, tapadas, balances)

    sobrantes = [i for i, _ in tomas if i not in usadas]
    return Secuencia(iniciales, lados, cambios, finales, tapadas, balances,
                     sobrantes, saltos)
