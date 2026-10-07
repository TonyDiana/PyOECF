# -*- coding: utf-8 *-*
"""
    :Propósito: Busca los RAW de la carpeta de una serie y los ordena.
                De momento, por nombre; el orden definitivo es por
                (fecha, número del nombre)
    :Autor:     Tony Diana
    :Versión:   26.10.06
"""

# cSpell:ignore

__all__ = ["KS", "Secuencia", "balance_personalizado", "buscar_raw",
           "secuencia"]

# --- Bibliotecas estándar Python
from pathlib import Path
from typing import Callable, NamedTuple

# --- Bibliotecas internas
from bib import std
from ..raw import KT


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
#     que se analizó) y los saltos de cada lado: (índice, k esperado, k)
class Secuencia(NamedTuple):
    iniciales: list[int]
    lados: list[list[int]]
    cambios: list[int]
    balances: list[int]
    sobrantes: list[int]
    saltos: list[tuple[int, int, int]]


# --- RAW de la carpeta, ordenados por nombre (lista vacía si no hay)
def buscar_raw(carpeta: Path) -> list[Path]:
    return sorted(p for p in carpeta.iterdir()
                  if p.is_file() and p.suffix.lower() in KT.extensiones)


# --- ¿Se hizo el balance de blancos personalizado inicial? En la
#     secuencia, la toma 1 es la Z-V (la referencia: k = 0) y la 2 es la
#     Z-V con el balance personalizado, con la misma exposición. Si la
#     segunda ya es de un lado (un tercio más o menos), se empezó sin él.
#     None si no se puede saber. ks: k de cada toma, en su orden (None si
#     no se pudo leer). No sirve comparar el balance de las dos tomas: en
#     series reales la Z-V inicial ya lleva a veces el personalizado
def balance_personalizado(ks: list[int | None]) -> bool | None:
    if len(ks) < 2 or ks[1] is None:
        return None
    if ks[1] == 0:
        return True
    if abs(ks[1]) == 1:
        return False
    return None


# --- Reparte la serie en sus partes. Las tomas se agrupan en rachas
#     seguidas de k = 0 (Z-V) o de k del mismo signo (un lado). Los dos
#     lados son las dos rachas más largas de signo contrario (la primera
#     si empatan): así, un intento suelto o una serie repetida no se
#     toman por un lado. Las Z-V del principio son las iniciales; las
#     de entre los dos lados, las de cambio; las de justo después del
#     segundo lado, los balances de cámara. En cada lado, k debe avanzar
#     de uno en uno desde ±1: lo que no, es un salto (repetida, saltada o
#     fuera de orden), y lo que pasa de ±tercios_lado sobra. Las tapadas
#     y las que no se pudieron leer no cuentan
def secuencia(ks: list[int | None], tapadas: list[bool]) -> Secuencia:
    tomas = [(i, k) for i, (k, tapada) in enumerate(zip(ks, tapadas))
             if k is not None and not tapada]

    # --- Rachas: (signo: 0, 1 o -1, índices de sus tomas)
    rachas: list[tuple[int, list[int]]] = []
    for i, k in tomas:
        signo = (k > 0) - (k < 0)
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
        lado = [i for i in indices if abs(ks[i]) <= KS.tercios_lado]
        lados.append(lado)
        usadas.update(lado)
        anterior = 0
        for i in lado:
            esperado = anterior + signo
            if ks[i] != esperado:
                saltos.append((i, esperado, ks[i]))             # type: ignore
            anterior = ks[i]                                    # type: ignore

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
