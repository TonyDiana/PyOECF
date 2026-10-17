# -*- coding: utf-8 *-*
"""
    :Propósito: Teselas de una toma (bloques cuadrados del sensor) y lo que
                se mide con ellas: dónde está el paño en la Z-V, qué
                tamaños de lámina caben y el recorte del paño
    :Autor:     Tony Diana
    :Versión:   26.10.14
"""

# cSpell:ignore postprocess, rawpy, teselas

__all__ = ["KTE", "Teselas", "Ventana", "Seleccion", "medir_teselas",
           "buscar_pano", "seleccionar", "porcentaje", "Oscuridad",
           "oscuridad", "Pano",
           "Medida", "medir_toma", "exceso_negro", "restar_exceso",
           "ruido_temporal", "fraccion_recortada", "matriz_color",
           "temperatura",
           "factores", "revelar", "recorte"]

# --- Bibliotecas estándar Python
from collections import deque
from pathlib import Path
from typing import NamedTuple

# --- Bibliotecas externas
import numpy as np
import rawpy

# --- Bibliotecas internas
from bib import clases
from .constantes import COM as KCOM
from .zonas import KP


#
class KTE(clases.EnumMutable):
    """ Constantes de las teselas y del paño. """

    # --- Lado de la tesela, en píxeles: múltiplo de 2 (Bayer) y de 6
    #     (X-Trans), para que todas tengan los mismos colores en las
    #     mismas posiciones (la máscara de colores de una vale para
    #     todas). El verde, de referencia: con él se busca el paño y se
    #     filtran las teselas
    LADO = 48
    VERDE = "G"

    # --- Dispersión relativa: desviación absoluta mediana, escalada para
    #     que valga como una desviación típica, entre la mediana
    ESCALA_DAM = 1.4826

    # --- Teselas oscuras (cartulina negra): nivel por debajo de esta
    #     fracción de la mediana de todas. No cuentan para buscar el paño
    NIVEL_MIN = 0.3

    # --- Paño: sus teselas tienen mucha más dispersión que las de la
    #     tarjeta. El corte entre los dos grupos lo hallan los datos de
    #     cada foto (Otsu sobre el logaritmo de la dispersión, en estas
    #     clases), no un número fijo, que cambiaría con cada cámara. El
    #     histograma va de este percentil al opuesto: una tesela suelta
    #     con una dispersión enorme no aplasta los dos grupos
    CLASES_CORTE = 128
    PERCENTIL_CORTE = 1

    # --- Comprobaciones del paño hallado. Hueco entre grupos: percentil
    #     bajo del paño entre percentil alto de la tarjeta (R7: 3,8; una
    #     serie sin paño: 1,2). Relleno: fracción de su rectángulo que
    #     ocupan sus teselas. Margen: teselas que se quitan por cada lado
    #     (los bordes del paño mezclan paño y tarjeta)
    PERCENTIL_HUECO = 5
    HUECO_MIN = 2.0
    RELLENO_MIN = 0.8
    MARGEN = 1

    # --- Cuadro de la lámina (ancho, alto), en píxeles, y divisores del
    #     recorte: 1 → 100 %, 2 → 50 %, 3 → 33 %, 4 → 25 %. Solo enteros,
    #     para reducir por área (media de cada bloque, sin inventar
    #     recortes en las luces); nunca por encima del 100 %
    CUADRO = (500, 350)
    FACTORES = (1, 2, 3, 4)

    # --- Por qué no se encontró el paño
    SIN_PANO = "SIN_PANO"
    PANO_PEQUENO = "PANO_PEQUENO"

    # --- Teselas buenas de la tarjeta (en la Z-V; valen para toda la
    #     serie). Rareza: una tesela es rara si su dispersión o su
    #     asimetría se aparta de las demás de la misma foto más de estas
    #     desviaciones típicas robustas (mediana y desviación absoluta
    #     mediana): sin número fijo por cámara. Nivel: fuera la que recibe
    #     más de estas zonas de luz distinta de la mediana. Mínimo de
    #     teselas buenas: con menos, no hay tarjeta y no se analiza
    RAREZA = 3
    NIVEL_MAX_ZONAS = 1 / 3
    MIN_TESELAS = 100

    # --- Avisos de las rechazadas, uno por causa (Tony, 2026-10-16),
    #     en fracción de las teselas de tarjeta. Tarjeta sucia: las de
    #     dispersión o las de asimetría pasan de AVISO_SUCIA (con una
    #     tarjeta limpia, por azar, ≈ 0,1-0,3 %). Luz desigual: las de
    #     nivel pasan de AVISO_NIVEL; se dice el lado si al menos
    #     AVISO_LADO de ellas caen en una mitad. El total: revisar desde
    #     AVISO_REVISAR, repetir la serie desde AVISO_REPETIR.
    #     Provisionales: medidos con dos series (R7 2,3 %; D750 8,9 %,
    #     todas las de nivel a la izquierda)
    AVISO_SUCIA = 0.01
    AVISO_NIVEL = 0.03
    AVISO_LADO = 0.8
    AVISO_REVISAR = 0.03
    AVISO_REPETIR = 0.10

    # --- Mitades de la toma donde se agrupan las rechazadas por nivel
    LADO_IZQUIERDA = "IZQUIERDA"
    LADO_DERECHA = "DERECHA"
    LADO_ARRIBA = "ARRIBA"
    LADO_ABAJO = "ABAJO"

    # --- Recortado: un valor llega a esta fracción del máximo de su canal
    #     en la serie (el libro la usa también: su constante UmbralRecorte)
    UMBRAL_RECORTE = 0.995

    # --- Motivo de cada tesela: buena, no es de tarjeta (oscura, paño o
    #     su margen) o el primer filtro que no pasa, en este orden
    BUENA = 0
    NO_TARJETA = -1
    RECHAZO_NIVEL = 1
    RECHAZO_DISPERSION = 2
    RECHAZO_ASIMETRIA = 3

    # --- Negro y ruido de lectura. Borde tapado: la franja izquierda del
    #     sensor (la de arriba sale más ruidosa: quizá no es negro puro),
    #     si tiene al menos estas columnas. Atípicos (una columna
    #     estropeada): fuera los que se apartan más de estas desviaciones
    #     típicas robustas, antes de medir. Si hay borde y tapadas, se
    #     avisa si sus ruidos difieren más de esta fracción
    MIN_COLUMNAS_BORDE = 16
    CORTE_ATIPICOS = 5
    DIFERENCIA_RUIDO = 0.2

    # --- De dónde sale el negro que se resta (de las tapadas si las hay;
    #     si no, estimado en las sombras; si no se puede, el que declara
    #     la cámara) y el ruido (del borde tapado si lo hay; si no, de las
    #     tapadas; si no, de la curva de transferencia; si no, de ninguna
    #     parte)
    ORIGEN_TAPADAS = "TAPADAS"
    ORIGEN_SOMBRAS = "SOMBRAS"
    ORIGEN_DECLARADO = "DECLARADO"
    ORIGEN_BORDE = "BORDE"
    ORIGEN_CURVA = "CURVA"

    # --- Ruido aleatorio con dos tomas iguales: se leen por franjas de
    #     estas filas de teselas (dos RAW enteros en coma flotante no
    #     caben con holgura en un portátil)
    FRANJA_TEMPORAL = 8

    # --- Negro estimado en las sombras: recta entre el nivel de cada zona
    #     (sobre el negro declarado) y su luz (2 elevado a sus EV), en las
    #     zonas de hasta SOMBRAS_HASTA tercios; su corte con luz 0 es lo
    #     que el negro real pasa del declarado. Con menos de
    #     MIN_ZONAS_SOMBRAS zonas, se queda el declarado
    SOMBRAS_HASTA = -3
    MIN_ZONAS_SOMBRAS = 6

    # --- Temperatura de la luz: de cámara a XYZ con la matriz de color
    #     del RAW (rawpy da la de XYZ a cámara; se invierte) y de xy a
    #     kelvin con la fórmula de McCamy: n = (x − X_E) / (Y_E − y) y
    #     K = A·n³ + B·n² + C·n + D. Canales de la matriz: R, G, B
    MCCAMY_X_E = 0.3320
    MCCAMY_Y_E = 0.1858
    MCCAMY = (449.0, 3525.0, 6823.3, 5520.33)
    CANALES_MATRIZ = 3


#
# --- Medidas de las teselas de una toma. Por canal: (canal, filas,
#     columnas); del verde (todos sus píxeles juntos): (filas, columnas)
class Teselas(NamedTuple):
    """
    Por tesela: nivel (mediana sobre el negro) y dispersión relativa de
    cada canal, y nivel, dispersión y asimetría del verde.
    """
    lado: int

    # --- Nombre de cada canal: su color y su índice en el RAW (R0, G1,
    #     B2, G3; en X-Trans, sin G3)
    canales: tuple[str, ...]
    nivel: np.ndarray
    dispersion: np.ndarray

    # --- Verde: nivel, dispersión y asimetría ((media − mediana) /
    #     desviación típica: el ruido es simétrico; un defecto, no)
    nivel_verde: np.ndarray
    dispersion_verde: np.ndarray
    asimetria_verde: np.ndarray


#
# --- Rectángulo en píxeles del sensor
class Ventana(NamedTuple):
    """ Rectángulo en píxeles: esquina superior izquierda, ancho y alto. """
    x: int
    y: int
    ancho: int
    alto: int


#
# --- Teselas de tarjeta elegidas en la Z-V, en filas × columnas
class Seleccion(NamedTuple):
    """ Motivo de cada tesela (KTE): buena, no es de tarjeta o rechazada. """
    motivo: np.ndarray

    #
    @property
    def buenas(self) -> np.ndarray:
        """ Saber qué teselas son buenas (máscara). """
        return self.motivo == KTE.BUENA

    #
    @property
    def tarjeta(self) -> int:
        """ Saber cuántas teselas son de tarjeta (buenas y rechazadas). """
        return int((self.motivo != KTE.NO_TARJETA).sum())

    #
    @property
    def rechazadas(self) -> int:
        """ Saber cuántas teselas de tarjeta rechazaron los filtros. """
        return self.tarjeta - int(self.buenas.sum())

    #
    @property
    def porcentaje(self) -> float:
        """ Saber qué porcentaje de las de tarjeta son rechazadas. """
        return 100 * self.rechazadas / self.tarjeta if self.tarjeta else 0.0

    #
    @property
    def hayTarjeta(self) -> bool:
        """ Saber si hay tarjeta: al menos KTE.MIN_TESELAS buenas. """
        return int(self.buenas.sum()) >= KTE.MIN_TESELAS

    #
    def fraccion(self, motivo: int) -> float:
        """
        Fracción de las teselas de tarjeta rechazadas por este motivo
        (KTE.RECHAZO_*).
        """
        return (int((self.motivo == motivo).sum()) / self.tarjeta
                if self.tarjeta else 0.0)

    #
    @property
    def ladosNivel(self) -> tuple[str, ...]:
        """
        Saber en qué mitades de la toma se agrupan las rechazadas por
        nivel (KTE.LADO_*): la de la izquierda o la de la derecha, y la de
        arriba o la de abajo, si al menos KTE.AVISO_LADO de ellas caen
        allí. Vacío si están repartidas o no hay ninguna.
        """
        filas, columnas = np.nonzero(self.motivo == KTE.RECHAZO_NIVEL)
        if not len(filas):
            return ()
        alto, ancho = self.motivo.shape
        lados = []
        for mitad, primera, segunda in (
                (columnas < ancho / 2, KTE.LADO_IZQUIERDA, KTE.LADO_DERECHA),
                (filas < alto / 2, KTE.LADO_ARRIBA, KTE.LADO_ABAJO)):
            parte = float(mitad.mean())
            if parte >= KTE.AVISO_LADO:
                lados.append(primera)
            elif 1 - parte >= KTE.AVISO_LADO:
                lados.append(segunda)
        return tuple(lados)


#
# --- Negro y ruido de lectura de una serie, por canal del RAW (índices
#     0 a 3; los que no hay, NaN), y de dónde salen
class Oscuridad(NamedTuple):
    """ Negro que se resta y ruido de lectura, por canal, con su origen. """
    negro: tuple[float, ...]
    origen_negro: str

    # --- Ruido usado (None si no hay borde ni tapadas) y los dos medidos,
    #     para el informe; difieren: si hay los dos y no casan
    ruido: tuple[float, ...] | None
    origen_ruido: str | None
    ruido_borde: tuple[float, ...] | None
    ruido_tapadas: tuple[float, ...] | None
    difieren: bool


#
# --- El paño de una toma, por canal (en el orden de Teselas.canales)
class Pano(NamedTuple):
    """
    Paño de una toma, por canal: nivel (mediana sobre el negro),
    dispersión relativa e histograma de sus valores tal como los da el
    RAW (para contar los recortados cuando se sepa el máximo de la
    serie: ver fraccion_recortada).
    """
    nivel: tuple[float, ...]
    dispersion: tuple[float, ...]
    histograma: tuple[np.ndarray, ...]


#
# --- Lo que vale una toma, por canal (en el orden de Teselas.canales)
class Medida(NamedTuple):
    """
    Valor típico (sobre el negro) y dispersión de la tarjeta en una
    toma, por canal; desviación de cada tesela rechazada; y su paño (None
    si no hay).
    """
    canales: tuple[str, ...]
    nivel: tuple[float, ...]
    dispersion: tuple[float, ...]

    # --- Rechazadas (en el orden de np.nonzero de la selección): cuánto
    #     se aparta su verde del de las buenas, en zonas (log2 del
    #     cociente), y su motivo (KTE)
    desviacion_rechazadas: np.ndarray
    motivo_rechazadas: np.ndarray
    pano: Pano | None

    # --- Verde de las buenas (sobre el negro): la referencia de las
    #     rechazadas
    verde: float


#
def medir_toma(archivo: Path, seleccion: Seleccion, negro: tuple[float, ...],
               pano: Ventana | None) -> Medida:
    """
    Valor de una toma por canal: la mediana de sus teselas buenas (las
    elegidas en la Z-V), con el negro restado, y la mediana de sus
    dispersiones; y lo de su paño (la ventana del recorte), si lo hay.
    """
    raw = _leer_raw(archivo)
    teselas = _teselas(raw, negro, KTE.LADO)
    buenas = seleccion.buenas
    medida_pano = None
    if pano is not None:
        trozo = raw.enteros[pano.y:pano.y + pano.alto,
                            pano.x:pano.x + pano.ancho]
        colores = raw.colores[pano.y:pano.y + pano.alto,
                              pano.x:pano.x + pano.ancho]
        niveles, dispersiones, histogramas = [], [], []
        for nombre in teselas.canales:
            indice = int(nombre[1:])
            valores = trozo[colores == indice]
            neto = valores.astype(np.float32) - negro[indice]
            mediana, dispersion = _mediana_dispersion(neto[None, None, :])
            niveles.append(float(mediana[0, 0]))
            dispersiones.append(float(dispersion[0, 0]))
            histogramas.append(np.bincount(valores))
        medida_pano = Pano(tuple(niveles), tuple(dispersiones),
                           tuple(histogramas))
    rechazadas = (seleccion.motivo != KTE.BUENA) & (
        seleccion.motivo != KTE.NO_TARJETA)
    verde_buenas = np.median(teselas.nivel_verde[buenas])
    with np.errstate(divide="ignore", invalid="ignore"):
        desviacion = np.log2(teselas.nivel_verde[rechazadas] / verde_buenas)
    return Medida(teselas.canales,
                  tuple(float(np.median(n[buenas])) for n in teselas.nivel),
                  tuple(float(np.median(d[buenas]))
                        for d in teselas.dispersion),
                  desviacion, seleccion.motivo[rechazadas], medida_pano,
                  float(verde_buenas))


#
def exceso_negro(medidas: list[tuple[int, Medida]]
                 ) -> tuple[float, ...] | None:
    """
    Lo que el negro real pasa del restado, por canal (en el orden de
    Medida.canales), estimado en las sombras de la serie (tercioEV y su
    medida): el corte con luz 0 de la recta entre el nivel de cada zona y
    su luz. None si no hay zonas de sombra bastantes.
    """
    sombras = [(t, m) for t, m in medidas if t <= KTE.SOMBRAS_HASTA]
    if len(sombras) < KTE.MIN_ZONAS_SOMBRAS:
        return None
    luz = np.array([2.0 ** (t / KP.TERCIOS) for t, _ in sombras])
    recta = np.column_stack((np.ones_like(luz), luz))
    niveles = np.array([m.nivel for _, m in sombras])
    corte = np.linalg.lstsq(recta, niveles, rcond=None)[0][0]
    return tuple(float(c) for c in corte)


#
def restar_exceso(medida: Medida, exceso: tuple[float, ...]) -> Medida:
    """
    La medida de una toma con el exceso de negro restado (por canal, en
    el orden de sus canales): los niveles bajan lo mismo; las
    dispersiones relativas suben en proporción (el ruido no cambia; en la
    tarjeta, con su nivel típico); las rechazadas, frente al verde de las
    buenas ya corregido.
    """
    def bajar(niveles: tuple[float, ...], dispersiones: tuple[float, ...]
              ) -> tuple[tuple[float, ...], tuple[float, ...]]:
        nuevos = tuple(n - e for n, e in zip(niveles, exceso))
        relativas = tuple(d * n / m if m > 0 else np.inf
                          for d, n, m in zip(dispersiones, niveles, nuevos))
        return nuevos, relativas

    nivel, dispersion = bajar(medida.nivel, medida.dispersion)
    pano = medida.pano
    if pano is not None:
        pano = Pano(*bajar(pano.nivel, pano.dispersion), pano.histograma)

    # --- Rechazadas: su verde y el de las buenas bajan el exceso del verde
    exceso_verde = float(np.mean([e for c, e in zip(medida.canales, exceso)
                                  if c.startswith(KTE.VERDE)]))
    verde = medida.verde - exceso_verde
    rechazadas = medida.verde * 2.0 ** medida.desviacion_rechazadas
    with np.errstate(divide="ignore", invalid="ignore"):
        desviacion = np.log2((rechazadas - exceso_verde) / verde)
    return medida._replace(nivel=nivel, dispersion=dispersion,
                           desviacion_rechazadas=desviacion, pano=pano,
                           verde=verde)


#
def ruido_temporal(archivo: Path, otro: Path, seleccion: Seleccion,
                   negro: tuple[float, ...]) -> dict[str, float]:
    """
    Ruido aleatorio de la tarjeta por canal ({canal: dispersión
    relativa}, como la de medir_toma), con dos tomas de la misma
    exposición (la Z-V y una de control). En cada tesela buena, la otra
    se iguala en nivel a la primera y se restan: lo fijo (textura de la
    tarjeta, diferencias entre píxeles) se va y queda lo aleatorio de las
    dos, que se divide entre la raíz de 1 + k² (k, el factor de
    igualar). Mediana de las teselas buenas.
    """
    primera, segunda = _leer_raw(archivo), _leer_raw(otro)
    lado = KTE.LADO
    colores = primera.colores
    patron = colores[:lado, :lado].reshape(-1)
    indices = [int(i) for i in np.unique(patron)]
    negro_patron = np.asarray(negro, dtype=np.float32)[patron]
    buenas = seleccion.buenas
    filas, columnas = buenas.shape
    resultados: dict[int, list[np.ndarray]] = {i: [] for i in indices}

    def bloques(enteros: np.ndarray, desde: int, hasta: int) -> np.ndarray:
        trozo = enteros[desde * lado:hasta * lado,
                        :columnas * lado].astype(np.float32)
        return (trozo.reshape(hasta - desde, lado, columnas, lado)
                .transpose(0, 2, 1, 3).reshape(hasta - desde, columnas, -1)
                - negro_patron)

    for desde in range(0, filas, KTE.FRANJA_TEMPORAL):
        hasta = min(filas, desde + KTE.FRANJA_TEMPORAL)
        elegidas = buenas[desde:hasta]
        if not elegidas.any():
            continue
        a = bloques(primera.enteros, desde, hasta)[elegidas]
        b = bloques(segunda.enteros, desde, hasta)[elegidas]
        for i in indices:
            pa, pb = a[:, patron == i], b[:, patron == i]
            nivel_a = np.median(pa, axis=1)
            with np.errstate(divide="ignore", invalid="ignore"):
                k = nivel_a / np.median(pb, axis=1)
                diferencia = pa - k[:, None] * pb
                dam = np.median(np.abs(diferencia - np.median(
                    diferencia, axis=1)[:, None]), axis=1)
                resultados[i].append(KTE.ESCALA_DAM * dam
                                     / np.sqrt(1 + k ** 2) / nivel_a)
    descripcion = primera.descripcion
    return {f"{descripcion[i]}{i}": float(np.median(np.concatenate(r)))
            for i, r in resultados.items() if r}


#
def fraccion_recortada(histograma: np.ndarray, umbral: float) -> float:
    """
    Fracción de los píxeles de un histograma (valores del RAW) que llegan
    al umbral (también en valores del RAW, con el negro incluido).
    """
    total = histograma.sum()
    desde = int(np.ceil(umbral))
    return float(histograma[desde:].sum() / total) if total else 0.0


#
def matriz_color(archivo: Path) -> np.ndarray:
    """ Matriz de cámara (R, G, B) a XYZ de un RAW. """
    with rawpy.imread(str(archivo)) as raw:
        return np.linalg.inv(np.asarray(
            raw.rgb_xyz_matrix)[:KTE.CANALES_MATRIZ])


#
def temperatura(rojo: float, verde: float, azul: float,
                matriz: np.ndarray) -> float:
    """
    Temperatura de color (kelvin) de una luz con esta proporción de rojo,
    verde y azul en la cámara (en una superficie neutra: la tarjeta).
    Fiable solo sin canales recortados y con señal sobre el ruido.
    """
    x_, y_, z_ = matriz @ np.array((rojo, verde, azul))
    suma = x_ + y_ + z_
    x, y = x_ / suma, y_ / suma
    n = (x - KTE.MCCAMY_X_E) / (KTE.MCCAMY_Y_E - y)
    a, b, c, d = KTE.MCCAMY
    return float(a * n ** 3 + b * n ** 2 + c * n + d)


#
def oscuridad(archivo: Path, tapadas: list[Path]) -> Oscuridad:
    """
    Negro y ruido de lectura de una serie: archivo, una toma cualquiera
    (para el negro declarado y el borde tapado); tapadas, las tomas
    tapadas ([] si no hay).
    """
    with rawpy.imread(str(archivo)) as raw:
        declarado = tuple(float(n) for n in raw.black_level_per_channel)
        izquierda = raw.sizes.left_margin
        borde = (_negro_ruido(raw.raw_image[:, :izquierda],
                              raw.raw_colors[:, :izquierda])
                 if izquierda >= KTE.MIN_COLUMNAS_BORDE else None)

    # --- Tapadas: la media de lo que da cada una
    medidas = []
    for tapada in tapadas:
        with rawpy.imread(str(tapada)) as raw:
            medidas.append(_negro_ruido(raw.raw_image_visible,
                                        raw.raw_colors_visible))
    oscuras = (tuple(tuple(np.mean([m[k][i] for m in medidas])
                           for i in range(len(medidas[0][k])))
                     for k in range(2)) if medidas else None)

    ruido_borde = borde[1] if borde else None
    ruido_tapadas = oscuras[1] if oscuras else None
    difieren = bool(
        ruido_borde and ruido_tapadas
        and np.nanmax(np.abs(np.array(ruido_borde) / np.array(ruido_tapadas)
                             - 1)) > KTE.DIFERENCIA_RUIDO)
    if ruido_borde:
        ruido, origen_ruido = ruido_borde, KTE.ORIGEN_BORDE
    elif ruido_tapadas:
        ruido, origen_ruido = ruido_tapadas, KTE.ORIGEN_TAPADAS
    else:
        ruido, origen_ruido = None, None
    return Oscuridad(
        oscuras[0] if oscuras else declarado,
        KTE.ORIGEN_TAPADAS if oscuras else KTE.ORIGEN_DECLARADO,
        ruido, origen_ruido, ruido_borde, ruido_tapadas, difieren)


#
def medir_teselas(archivo: Path, negros: tuple[float, ...] | None = None,
                  lado: int = KTE.LADO) -> Teselas:
    """
    Nivel y dispersión de cada canal en cada tesela de una toma, y lo
    del verde. negros: el negro de cada canal del RAW (None: el que
    declara la cámara).
    """
    return _teselas(_leer_raw(archivo), negros, lado)


#
# --- Lo que se usa de un RAW, leído de una vez
class _Raw(NamedTuple):
    enteros: np.ndarray
    colores: np.ndarray
    declarados: tuple[float, ...]
    descripcion: str


#
def _leer_raw(archivo: Path) -> _Raw:
    with rawpy.imread(str(archivo)) as raw:
        return _Raw(raw.raw_image_visible.copy(),
                    raw.raw_colors_visible.copy(),
                    tuple(float(n) for n in raw.black_level_per_channel),
                    raw.color_desc.decode())


#
# --- Medidas de las teselas de un RAW ya leído (ver medir_teselas)
def _teselas(raw: _Raw, negros: tuple[float, ...] | None,
             lado: int) -> Teselas:
    imagen = raw.enteros.astype(np.float32)
    colores = raw.colores
    descripcion = raw.descripcion
    negro = np.asarray(negros if negros is not None else raw.declarados,
                       dtype=np.float32)

    # --- Cada tesela, en una fila de lado × lado píxeles, sobre su negro;
    #     la máscara de colores de la primera vale para todas
    filas, columnas = imagen.shape[0] // lado, imagen.shape[1] // lado
    patron = colores[:lado, :lado].reshape(-1)
    bloques = (imagen[:filas * lado, :columnas * lado]
               .reshape(filas, lado, columnas, lado)
               .transpose(0, 2, 1, 3).reshape(filas, columnas, -1)
               - negro[patron])

    # --- Por canal (los que hay: X-Trans no tiene el 3) y del verde
    indices = [int(i) for i in np.unique(patron)]
    medidas = [_mediana_dispersion(bloques[..., patron == i])
               for i in indices]
    verdes = [i for i in indices if descripcion[i] == KTE.VERDE]
    pixeles_verdes = bloques[..., np.isin(patron, verdes)]
    nivel_verde, dispersion_verde = _mediana_dispersion(pixeles_verdes)
    with np.errstate(divide="ignore", invalid="ignore"):
        asimetria = ((pixeles_verdes.mean(axis=2) - nivel_verde)
                     / pixeles_verdes.std(axis=2))
    return Teselas(lado, tuple(f"{descripcion[i]}{i}" for i in indices),
                   np.stack([m[0] for m in medidas]),
                   np.stack([m[1] for m in medidas]),
                   nivel_verde, dispersion_verde, asimetria)


#
def buscar_pano(teselas: Teselas) -> Ventana | str:
    """
    Ventana del paño en píxeles o, si no se encuentra, por qué (KTE): los
    dos grupos de teselas no se separan, el paño no es un solo bloque o
    no cabe el cuadro de la lámina.
    """
    claras = (teselas.nivel_verde
              > KTE.NIVEL_MIN * np.median(teselas.nivel_verde))
    logaritmo = np.log2(teselas.dispersion_verde)
    validas = claras & np.isfinite(logaritmo)
    if not validas.any():
        return KTE.SIN_PANO

    # --- Corte entre tarjeta y paño, y hueco entre los dos grupos
    corte = _corte_otsu(logaritmo[validas])
    pano = validas & (logaritmo > corte)
    tarjeta = validas & (logaritmo <= corte)
    if not pano.any() or not tarjeta.any():
        return KTE.SIN_PANO
    hueco = 2 ** (np.percentile(logaritmo[pano], KTE.PERCENTIL_HUECO)
                  - np.percentile(logaritmo[tarjeta],
                                  100 - KTE.PERCENTIL_HUECO))
    if hueco < KTE.HUECO_MIN:
        return KTE.SIN_PANO

    # --- El bloque de paño más grande debe llenar su rectángulo
    bloque = _bloque_mayor(pano)
    filas, columnas = np.nonzero(bloque)
    f0, f1 = filas.min(), filas.max() + 1
    c0, c1 = columnas.min(), columnas.max() + 1
    if bloque.sum() < KTE.RELLENO_MIN * (f1 - f0) * (c1 - c0):
        return KTE.SIN_PANO

    # --- Sin los bordes, y debe caber el cuadro de la lámina
    f0, c0 = f0 + KTE.MARGEN, c0 + KTE.MARGEN
    f1, c1 = f1 - KTE.MARGEN, c1 - KTE.MARGEN
    lado = teselas.lado
    ventana = Ventana(int(c0 * lado), int(f0 * lado),
                      int(max(0, c1 - c0) * lado), int(max(0, f1 - f0) * lado))
    if not factores(ventana):
        return KTE.PANO_PEQUENO
    return ventana


#
def seleccionar(teselas: Teselas, pano: Ventana | None) -> Seleccion:
    """
    Teselas de tarjeta de la Z-V y las que pasan los filtros. De tarjeta:
    las claras, sin el paño ni una tesela más por cada lado (pano es la
    ventana del recorte, ya encogida: se amplía). Filtros, por orden:
    nivel, dispersión y asimetría del verde.
    """
    claras = (teselas.nivel_verde
              > KTE.NIVEL_MIN * np.median(teselas.nivel_verde))
    tarjeta = claras & np.isfinite(teselas.dispersion_verde)
    if pano is not None:
        lado, borde = teselas.lado, 2 * KTE.MARGEN
        tarjeta[max(0, pano.y // lado - borde):
                (pano.y + pano.alto) // lado + borde,
                max(0, pano.x // lado - borde):
                (pano.x + pano.ancho) // lado + borde] = False
    motivo = np.where(tarjeta, KTE.BUENA, KTE.NO_TARJETA).astype(np.int8)
    if not tarjeta.any():
        return Seleccion(motivo)

    # --- Cada filtro marca las que no pasa, si aún son buenas
    nivel = np.log2(teselas.nivel_verde
                    / np.median(teselas.nivel_verde[tarjeta]))
    filtros = ((KTE.RECHAZO_NIVEL, np.abs(nivel) > KTE.NIVEL_MAX_ZONAS),
               (KTE.RECHAZO_DISPERSION,
                _rara(teselas.dispersion_verde, tarjeta, solo_altas=True)),
               (KTE.RECHAZO_ASIMETRIA,
                _rara(teselas.asimetria_verde, tarjeta, solo_altas=False)))
    for codigo, falla in filtros:
        motivo[(motivo == KTE.BUENA) & falla] = codigo
    return Seleccion(motivo)


#
def porcentaje(factor: int) -> int:
    """ Porcentaje de un divisor del recorte: 1 → 100, 2 → 50, 3 → 33… """
    return round(KCOM.CIEN / factor)


#
def factores(ventana: Ventana) -> tuple[int, ...]:
    """ Divisores del recorte (KTE.FACTORES) que caben en la ventana. """
    ancho, alto = KTE.CUADRO
    return tuple(f for f in KTE.FACTORES
                 if ancho * f <= ventana.ancho and alto * f <= ventana.alto)


#
def revelar(archivo: Path) -> np.ndarray:
    """
    Toma revelada en RGB de 8 bits, para verla en pantalla (no para la
    lámina): balance de la cámara, sin aclarar y sin girar, para que sus
    píxeles coincidan con los del sensor.
    """
    with rawpy.imread(str(archivo)) as raw:
        return raw.postprocess(use_camera_wb=True, no_auto_bright=True,
                               output_bps=8, user_flip=0)


#
def recorte(imagen: np.ndarray, ventana: Ventana, factor: int) -> np.ndarray:
    """
    Recorte del centro de la ventana del tamaño del cuadro por factor,
    reducido por área (media de cada bloque de factor × factor): tal
    como sale en el cuadro de la lámina.
    """
    ancho, alto = KTE.CUADRO
    x = ventana.x + (ventana.ancho - ancho * factor) // 2
    y = ventana.y + (ventana.alto - alto * factor) // 2
    trozo = imagen[y:y + alto * factor, x:x + ancho * factor]
    medio = (trozo.reshape(alto, factor, ancho, factor, -1)
             .mean(axis=(1, 3)))
    return np.round(medio).astype(imagen.dtype)


#
# --- Mediana y dispersión relativa de cada tesela (sus píxeles, en el
#     último eje). Sin nivel (todo negro), dispersión infinita
def _mediana_dispersion(pixeles: np.ndarray) -> tuple[np.ndarray,
                                                       np.ndarray]:
    mediana = np.median(pixeles, axis=2)
    dam = np.median(np.abs(pixeles - mediana[..., None]), axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        dispersion = np.where(mediana > 0, KTE.ESCALA_DAM * dam / mediana,
                              np.inf)
    return mediana, dispersion


#
# --- Negro (mediana) y ruido (desviación típica, sin atípicos) de unos
#     píxeles sin luz, por canal del RAW (0 a 3; los que no hay, NaN)
def _negro_ruido(pixeles: np.ndarray, colores: np.ndarray) -> tuple[
        tuple[float, ...], tuple[float, ...]]:
    negros, ruidos = [], []
    for i in range(4):
        valores = pixeles[colores == i].astype(np.float32)
        if not valores.size:
            negros.append(np.nan)
            ruidos.append(np.nan)
            continue
        mediana = float(np.median(valores))
        escala = KTE.ESCALA_DAM * np.median(np.abs(valores - mediana))
        if escala > 0:
            valores = valores[np.abs(valores - mediana)
                              <= KTE.CORTE_ATIPICOS * escala]
        negros.append(mediana)
        ruidos.append(float(valores.std()))
    return tuple(negros), tuple(ruidos)


#
# --- Teselas raras: las que se apartan de las de tarjeta más de RAREZA
#     desviaciones típicas robustas. solo_altas: solo por arriba (la
#     dispersión: una tesela no es mala por ser más lisa)
def _rara(valores: np.ndarray, tarjeta: np.ndarray,
          solo_altas: bool) -> np.ndarray:
    mediana = np.median(valores[tarjeta])
    escala = KTE.ESCALA_DAM * np.median(np.abs(valores[tarjeta] - mediana))
    with np.errstate(divide="ignore", invalid="ignore"):
        distancia = (valores - mediana) / escala
    return distancia > KTE.RAREZA if solo_altas else (
        np.abs(distancia) > KTE.RAREZA)


#
# --- Corte de Otsu: el valor que mejor separa los datos en dos grupos
def _corte_otsu(datos: np.ndarray) -> float:
    rango = (np.percentile(datos, KTE.PERCENTIL_CORTE),
             np.percentile(datos, 100 - KTE.PERCENTIL_CORTE))
    cuenta, bordes = np.histogram(datos, bins=KTE.CLASES_CORTE, range=rango)
    centros = (bordes[:-1] + bordes[1:]) / 2
    peso = np.cumsum(cuenta)
    suma = np.cumsum(cuenta * centros)
    total, suma_total = peso[-1], suma[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        entre = ((suma_total * peso / total - suma) ** 2
                 / (peso * (total - peso)))
    return float(centros[np.nanargmax(entre)])


#
# --- El bloque más grande de teselas marcadas que se tocan por un lado
def _bloque_mayor(marcadas: np.ndarray) -> np.ndarray:
    vistas = np.zeros_like(marcadas)
    mayor = np.zeros_like(marcadas)
    filas, columnas = marcadas.shape
    for inicio in zip(*np.nonzero(marcadas)):
        if vistas[inicio]:
            continue
        bloque = np.zeros_like(marcadas)
        pendientes = deque([inicio])
        vistas[inicio] = True
        while pendientes:
            f, c = pendientes.popleft()
            bloque[f, c] = True
            for vf, vc in ((f - 1, c), (f + 1, c), (f, c - 1), (f, c + 1)):
                if (0 <= vf < filas and 0 <= vc < columnas
                        and marcadas[vf, vc] and not vistas[vf, vc]):
                    vistas[vf, vc] = True
                    pendientes.append((vf, vc))
        if bloque.sum() > mayor.sum():
            mayor = bloque
    return mayor
