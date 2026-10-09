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
from bib import std


#
# --- Constantes de la secuencia de tomas
class KS(std.EnumMutable):
    """ Tomas que pide el protocolo en cada parte de la serie. """

    # --- Z-V iniciales: con balance arbitrario y con el personalizado
    iniciales = 2

    # --- Tomas de cada lado, de 1/3 en 1/3, y lados
    tercios_lado = 15
    lados = 2

    # --- Z-V de cambio de lado y tomas tapadas
    cambios = 1
    tapadas = 2


#
# --- Partes de una serie: índices de sus tomas (en el orden de la lista
#     que se repartió) y los saltos de cada lado: (índice, tercioEV
#     esperado, tercioEV)
class Secuencia(NamedTuple):
    iniciales: list[int]
    lados: list[list[int]]
    cambios: list[int]
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
    if len(tercioEVs) < KS.iniciales or tercioEVs[1] is None:
        return None
    if tercioEVs[1] != 0:
        return False if abs(tercioEVs[1]) == 1 else None
    if None in balances:
        return None
    return balances[0] != balances[1]


# --- Reparte la serie en sus partes. Las tomas se agrupan en rachas
#     seguidas de tercioEV = 0 (Z-V) o de tercioEV del mismo signo (un
#     lado). Los dos lados son las dos rachas más largas de signo
#     contrario (la primera si empatan): así, un intento suelto o una
#     serie repetida no se toman por un lado. Las Z-V del principio son
#     las iniciales; las de entre los dos lados, las de cambio; las de
#     justo después del segundo lado, los balances de cámara. En cada
#     lado, el tercioEV debe avanzar de uno en uno desde ±1: lo que no,
#     es un salto (repetida, saltada o fuera de orden), y lo que pasa de
#     ±tercios_lado sobra. Las tapadas y las que no se pudieron leer no
#     cuentan
def secuencia(tercioEVs: list[int | None], tapadas: list[bool]) -> Secuencia:
    tomas = [(i, tercioEV) for i, (tercioEV, tapada)
             in enumerate(zip(tercioEVs, tapadas))
             if tercioEV is not None and not tapada]

    # --- Rachas: (signo: 0, 1 o -1, índices de sus tomas)
    rachas: list[tuple[int, list[int]]] = []
    for i, tercioEV in tomas:
        signo = (tercioEV > 0) - (tercioEV < 0)
        if rachas and rachas[-1][0] == signo:
            rachas[-1][1].append(i)
        else:
            rachas.append((signo, [i]))

    # --- Los dos lados, en su orden en la serie (posiciones en rachas)
    def mas_larga(signos: set[int]) -> int | None:
        candidatas = [n for n, (s, _) in enumerate(rachas) if s in signos]
        return max(candidatas, key=lambda n: len(rachas[n][1]),
                   default=None)

    primera = mas_larga({1, -1})
    elegidas = [] if primera is None else [primera]
    if primera is not None:
        segunda = mas_larga({-rachas[primera][0]})
        if segunda is not None:
            elegidas.append(segunda)
    elegidas.sort()

    # --- Lados, recortando lo que pasa de ±tercios_lado, y sus saltos
    lados: list[list[int]] = []
    saltos: list[tuple[int, int, int]] = []
    usadas = set()
    for n in elegidas:
        signo, indices = rachas[n]
        lado = [i for i in indices if abs(tercioEVs[i]) <= KS.tercios_lado]
        lados.append(lado)
        usadas.update(lado)
        anterior = 0
        for i in lado:
            esperado = anterior + signo
            if tercioEVs[i] != esperado:
                saltos.append((i, esperado, tercioEVs[i]))      # type: ignore
            anterior = tercioEVs[i]                             # type: ignore

    # --- Z-V: iniciales (racha del principio), de cambio (entre los
    #     lados) y balances (racha justo después del segundo lado)
    def ceros(desde: int, hasta: int) -> list[int]:
        return [i for s, indices in rachas[desde:hasta] if s == 0
                for i in indices]

    iniciales = ceros(0, 1)
    cambios = (ceros(elegidas[0] + 1, elegidas[1])
               if len(elegidas) == KS.lados else [])
    ultima = elegidas[-1] if elegidas else 0
    balances = ceros(ultima + 1, ultima + 2) if elegidas else []
    usadas.update(iniciales, cambios, balances)

    sobrantes = [i for i, _ in tomas if i not in usadas]
    return Secuencia(iniciales, lados, cambios, balances, sobrantes, saltos)
