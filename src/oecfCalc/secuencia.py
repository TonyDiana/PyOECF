# -*- coding: utf-8 *-*
"""
    :Propósito: El protocolo de la serie (KS) y su reparto en partes:
                iniciales, lados, cambio, final, tapadas, balances de
                cámara, marcadores y bloques de la secuencia de ISO,
                sobrantes y saltos, y la ZV. También, si se hizo el
                balance personalizado
    :Autor:     Tony Diana
    :Versión:   26.11.10
"""

# cSpell:ignore leidas, oecf

__all__ = ["KS", "BloqueISO", "Secuencia", "balance_personalizado",
           "z2_medible", "repartir_secuencia"]

# --- Bibliotecas estándar Python
from typing import NamedTuple

# --- Bibliotecas internas
from bib import std
from bib.oecfMediadores import KP


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

    MARCADORES = 2
    """Marcadores de la secuencia de ISO: el inicial y el final."""

    ZONAS_Z2 = 3
    """Zonas de la Z2 por debajo de la Z-V en la secuencia de ISO."""

    TERCIOS_Z2 = -ZONAS_Z2 * KP.TERCIOS
    """tercioEV de la Z2 de la secuencia de ISO."""

    MARGEN_Z2 = 1
    """Tercios que la Z2 de un ISO puede apartarse de TERCIOS_Z2 (en el
    ISO más alto, por el tiempo más corto de la cámara): se mide como
    estimación. Más, no se mide (Tony, 2026-11-10)."""


#
# --- Un bloque de la secuencia de ISO
class BloqueISO(NamedTuple):
    """
    Tomas de un ISO en la secuencia de ISO (índices; None si falta): su
    Z-V (tercioEV 0) y su Z2 (la de tercioEV negativo, que debería ser
    -9 pero puede quedarse corta por el tiempo más corto de la cámara)
    """
    z2: int | None
    zv: int | None


#
# --- Partes de una serie
class Secuencia(NamedTuple):
    """
    Partes de una serie: índices de sus tomas (en el orden de la lista que
    se repartió) y los saltos de cada lado: (índice, tercioEV esperado,
    tercioEV). zv: la ZV de la serie, la última de cambio o, si no hay,
    la última inicial (None si no hay ninguna: Tony, 2026-10-19). paso:
    tercios de cada paso de los lados, 1 (por tercios) o KP.TERCIOS (por
    pasos enteros, sin tercios: Tony, 2026-10-19). marcadores: los de la
    secuencia de ISO, 0, 1 (sin el final) o KS.MARCADORES. bloques: los
    de la secuencia de ISO, {ISO: bloque}, de menor a mayor ISO.
    """
    iniciales: list[int]
    lados: list[list[int]]
    cambios: list[int]
    finales: list[int]
    tapadas: list[int]
    balances: list[int]
    marcadores: list[int]
    bloques: dict[int, BloqueISO]
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
def z2_medible(tercio_z2: int | None, hay_zv: bool) -> bool:
    """
    ¿Se puede medir un ISO de la secuencia de ISO? Sí, si tiene Z-V y Z2
    y su Z2 (tercio_z2, su tercioEV) está a KS.MARGEN_Z2 tercios de
    KS.TERCIOS_Z2 como mucho. Si no está justo en KS.TERCIOS_Z2, es una
    estimación
    """
    return (hay_zv and (tercio_z2 is not None)
            and (abs(tercio_z2 - KS.TERCIOS_Z2) <= KS.MARGEN_Z2))


#
def repartir_secuencia(tercioEVs: list[int | None], de_tapada: list[bool],
                       WBs: list[tuple[float, ...] | None],
                       isos: list[float | None],
                       oscuras: list[bool]) -> Secuencia:
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
    hay tapadas, y sobran (Tony, 2026-10-19). Secuencia de ISO: tras las
    tapadas (o tras el segundo lado, si no las hay), el marcador inicial
    es la primera toma oscura con tercioEV 0 o con la exposición de las
    tapadas (se acepta ese error: Tony, 2026-11-10), y el final, la
    última oscura tras él con lo mismo; entre los dos (o tras el inicial,
    sin final), los bloques por ISO: su Z-V, la última con tercioEV 0, y
    su Z2, la última con tercioEV negativo. Balances de cámara, con al
    menos KS.MIN_BALANCES tomas y antes del marcador inicial: con
    tapadas, las Z-V que van detrás de la última; sin ellas, las Z-V tras
    el segundo lado desde la primera con un balance distinto del de la
    serie (Tony, 2026-10-19). La serie
    va por pasos enteros si todas las tomas de los lados caen en una zona
    entera; si no, por tercios. En cada lado, el tercioEV debe avanzar de
    paso en paso desde ±1 paso: lo que no, es un salto (repetida, saltada
    o fuera de orden), y lo que pasa de ±KS.TERCIOS_LADO sobra. Las que no
    se pudieron leer no cuentan. de_tapada (si tiene la exposición de las
    tapadas), WBs, isos y oscuras (si salió casi negra): de cada toma, en
    el orden de tercioEVs.
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
    #     seguidas: una tapada posterior, separada de ellas por otras
    #     tomas (p. ej. un marcador de la secuencia de ISO tomado con los
    #     valores de las tapadas), no es una tapada y no desplaza los
    #     balances de cámara
    tapadas: list[int] = []
    if finales:
        for i in (i for i in leidas if i > finales[-1]):
            if not de_tapada[i]:
                break
            tapadas.append(i)

    # --- Secuencia de ISO. Marcador inicial: tras las tapadas (o tras el
    #     segundo lado, si no las hay), la primera toma oscura con
    #     tercioEV 0 o con la exposición de las tapadas (se acepta ese
    #     error: Tony, 2026-11-10). Final: la última oscura tras él con
    #     tercioEV 0 o con esa exposición
    desde = tapadas[-1] if tapadas else ultima_lado
    marcadores: list[int] = []
    if desde is not None:
        marcadores = [i for i in leidas if (i > desde) and oscuras[i]
                      and (de_tapada[i] or (tercioEVs[i] == 0))][:1]
    if marcadores:
        final = next((i for i in reversed(leidas)
                      if (i > marcadores[0]) and oscuras[i]
                      and (de_tapada[i] or (tercioEVs[i] == 0))), None)
        if final is not None:
            marcadores.append(final)

    # --- Bloques: las tomas entre los marcadores (o tras el inicial, sin
    #     final), por su ISO. Si algo se repitió, la buena es la última
    bloques: dict[int, BloqueISO] = {}
    if marcadores:
        hasta = (marcadores[-1] if (len(marcadores) == KS.MARCADORES)
                 else len(tercioEVs))
        por_iso: dict[int, list[int]] = {}
        for i in leidas:
            if marcadores[0] < i < hasta:
                iso = round(isos[i])                            # type: ignore
                por_iso.setdefault(iso, []).append(i)
        for iso in sorted(por_iso):
            grupo = por_iso[iso]
            bloques[iso] = BloqueISO(
                z2=next((i for i in reversed(grupo) if tercioEVs[i] < 0),
                        None),                                  # type: ignore
                zv=next((i for i in reversed(grupo) if tercioEVs[i] == 0),
                        None))
    limite = marcadores[0] if marcadores else len(tercioEVs)

    # --- Balances de cámara, antes del marcador inicial: con tapadas, las
    #     Z-V tras la última; sin ellas, las Z-V tras el segundo lado desde
    #     la primera con otro balance que el de la serie
    tras = [i for i in tras if i < limite]
    if tapadas:
        balances = [i for i in tras if i > tapadas[-1]]
    else:
        desde = next((n for n, i in enumerate(tras)
                      if WBs[i] != wb_serie), len(tras))
        balances = tras[desde:]
    if len(balances) < KS.MIN_BALANCES:
        balances = []
    usadas.update(iniciales, cambios, finales, tapadas, balances,
                  marcadores)
    usadas.update(i for bloque in bloques.values()
                  for i in (bloque.z2, bloque.zv) if i is not None)

    sobrantes = [i for i in leidas if i not in usadas]
    return Secuencia(
        iniciales=iniciales,
        lados=lados,
        cambios=cambios,
        finales=finales,
        tapadas=tapadas,
        balances=balances,
        marcadores=marcadores,
        bloques=bloques,
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
