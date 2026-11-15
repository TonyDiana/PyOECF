# -*- coding: utf-8 *-*
"""
    :Propósito: PDF de la cámara para el estudiante (dos páginas A4,
                con matplotlib; una tercera solo si la secuencia de ISO
                no cabe en la segunda): latitud de texturas, curva tonal
                y diferencia en L*, recomendaciones para la curva del
                revelador, balances de blancos con los Kelvin que poner
                en la cámara, ruido aceptable por color, píxeles
                defectuosos y la secuencia de ISO.
                Lo calcula el libro (Excel): el PDF solo lo dibuja. Sin
                los datos del estudiante (ni sus decisiones ni el L* que
                escribe a mano). Sin textos propios: los recibe ya
                traducidos
    :Autor:     Tony Diana
    :Versión:   26.11.10
"""

# cSpell:ignore axhline, backend, backends, boxstyle, capstyle
# cSpell:ignore dejavu, edgecolor, facecolor, figsize, fontsize, frameon, graf
# cSpell:ignore kpdf, labelcolor, linestyle, linewidth, lstar, markersize
# cSpell:ignore matplotlib, ncol, oecf, rotulos, xlim, xtick, xticks, ylabel
# cSpell:ignore ylim, ytick, zorder

__all__ = ["KPDF", "Pdf"]

# --- Bibliotecas estándar Python
import math
from datetime import datetime
from pathlib import Path

# --- Bibliotecas externas
import matplotlib
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import to_hex, to_rgb
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.text import Text
from matplotlib.ticker import FuncFormatter
from matplotlib.transforms import Bbox

# --- Bibliotecas internas
from bib import std
from bib.oecfMediadores import KP
from oecfCalc import BalanceMedido, KNE, OECF, rangos_neutros, Ventana
from .excel import KXL, Excel, PuntoCurva


#
class KPDF(std.EnumMutable):
    """ Diseño del PDF: página, colores, posiciones y textos. """

    # --- Motor de dibujo de matplotlib: solo a archivo, sin ventanas. Sin
    #     fijarlo, el depurador de VS Code lo engancha a Tk en modo
    #     interactivo y el programa puede no cerrarse (2026-10-19)
    MOTOR = "Agg"

    # --- Página A4 vertical, en pulgadas, y márgenes laterales (fracción)
    PAGINA = (8.27, 11.69)
    IZQUIERDA = 0.06
    DERECHA = 0.94
    PAGINAS = 2
    """ Páginas de siempre; con secuencia de ISO, una más (la última). """

    # --- Colores: los del libro (cabecera, filas alternas y bordes) y
    #     los de sus series; el verde oscuro de la latitud recomendada,
    #     la tinta del texto y la rejilla de las gráficas
    VERDE = KXL.CABECERA_FONDO
    VERDE_CLARO = KXL.BANDA
    BORDE = KXL.BORDE_TABLA
    VERDE_OSCURO = "#2E5E1A"
    TINTA = "#262626"
    GRIS = KXL.COLOR_ROTULO
    REJILLA = "#E6E6E6"
    EJES = "#BFBFBF"
    CERO = "#7F7F7F"
    REVELADOR = KXL.COLORES_CANALES[2]

    # --- Bordes de los pasos de la escala de zonas: gris, el de la línea
    #     del cero (el verde claro de los bordes se confundía con los
    #     grises claros y el blanco, de la Z7 en adelante)
    MARCO_TIRA = CERO

    # --- Letra: la de matplotlib (DejaVu Sans, va con él en cualquier
    #     sistema) y sus tamaños
    FUENTE = "DejaVu Sans"
    LETRA = 9
    LETRA_TITULO = 20
    LETRA_SUBTITULO = 10
    LETRA_APARTADO = 12.5
    LETRA_NOTA = 8.5
    LETRA_CIFRA = 20
    LETRA_PIE = 7.5

    # --- Cabecera (banda verde arriba) y pie: alturas en fracción
    BANDA_ABAJO = 0.915
    TITULO_Y = 0.962
    SUBTITULO_Y = 0.931
    PIE_Y = 0.025

    # --- Página 1: latitud (sección, nota, escala de zonas y cifras), las
    #     dos gráficas una al lado de otra con su título cada una
    #     (izquierda, abajo, ancho, alto; los títulos, de dónde a dónde
    #     van con su raya) y, debajo, las recomendaciones. La escala va de
    #     margen a margen, como la raya de las secciones; las gráficas
    #     dejan sitio a la izquierda para el nombre del eje (Tony,
    #     2026-11-13: todo más compacto, para que el PDF salga en dos
    #     páginas)
    APARTADO_LATITUD = 0.88
    SUBRAYA = 0.008
    ESCALA = (IZQUIERDA, 0.745, DERECHA - IZQUIERDA, 0.095)
    CIFRAS_Y = 0.672
    CIFRAS_ALTO = 0.065
    CIFRAS_ANCHO = 0.43
    CIFRAS_PASO = 0.45
    APARTADO_CURVA = 0.64
    TITULO_CURVA = (IZQUIERDA, 0.48)
    GRAF_CURVA = (0.1, 0.385, 0.38, 0.23)
    TITULO_DIFERENCIA = (0.535, DERECHA)
    GRAF_DIFERENCIA = (0.585, 0.385, DERECHA - 0.585, 0.23)
    APARTADO_RECOMENDACIONES = 0.335

    # --- Recuadros de las cifras: margen interior, altura de la cifra
    #     grande y de «de Zx a Zy» sobre su base, y radio de las esquinas
    CIFRAS_MARGEN = 0.02
    CIFRAS_NUMERO_Y = 0.013
    CIFRAS_DESDE_Y = 0.016
    CIFRAS_REDONDEO = 0.008

    # --- Escala de zonas (en peine): tira de grises, un paso por tercio,
    #     cada uno con su borde; alto de los pasos de zona entera y de los
    #     de tercio (dos tercios), desde 0. Debajo, el peine (diente largo en
    #     cada zona entera, corto en cada tercio: la mitad) y los nombres
    #     de las zonas enteras, con la ZV destacada (recuadro oscuro, letra
    #     blanca). Encima, los tramos: alto (apreciable, recomendado) y su
    #     grosor
    ALTO_ZONA = 1
    ALTO_TERCIO = 2 / 3
    TRAMO_APRECIABLE = (1.85, 2.5)
    TRAMO_RECOMENDADO = (1.4, 4)
    PATA_TRAMO = 0.1
    DIENTE_ZONA = 0.3
    DIENTE_TERCIO = 0.15
    LINEA_DIENTE = 0.8
    LINEA_TIRA = 0.5
    NOMBRES_Y = -0.62
    MARCO_ZV = "round,pad=0.25"
    ESCALA_Y = (-0.95, 2.0)

    # --- Página 2 (y la 3, si la secuencia de ISO no cabe en la 2):
    #     secciones y tablas (dónde empieza la primera; alto de fila;
    #     separación entre secciones; de la sección a lo alto de su nota
    #     y a su tabla (con nota o sin ella); hueco mínimo de la nota a la
    #     tabla, si la nota es tan larga que la empuja, y de una tabla a
    #     la nota de debajo). Nada se pinta por debajo de LIMITE_ABAJO
    APARTADO_PAGINA = 0.875
    LIMITE_ABAJO = 0.05
    ALTO_FILA = 0.019
    ENTRE_APARTADOS = 0.032
    A_LA_NOTA = 0.014
    A_LA_TABLA = 0.05
    A_LA_TABLA_SIN_NOTA = 0.03
    NOTA_A_TABLA = 0.008
    TABLA_A_NOTA = 0.012
    ENTRE_NOTAS = 0.006
    ANCHOS_RECOMENDACIONES = (1, 1.3, 1.3, 1, 1)

    # --- Balances de blancos: columnas (nombre; Kelvin anotado y su color;
    #     color del Kelvin medido y su número: los dos colores quedan juntos
    #     en el centro, para compararlos), cuáles son las de color y las
    #     cabeceras unidas sobre dos columnas (primera columna, cuántas).
    #     La tabla ocupa la mitad izquierda: hasta BALANCES_ANCHO del
    #     ancho entre márgenes (Tony, 2026-11-13)
    BALANCES_ANCHO = 0.5
    ANCHOS_BALANCES = (1.2, 0.8, 0.4, 0.4, 0.8)
    COL_COLOR_ANOTADO = 2
    COL_COLOR_MEDIDO = 3
    UNIONES_BALANCES = ((1, 2), (3, 2))

    # --- Color de la luz según su temperatura, para ver qué es frío y qué
    #     cálido: (Kelvin, color), de menor a mayor. Aproximado y algo más
    #     marcado que el real, para que se note; entre dos, se interpola.
    #     Sin Kelvin, gris
    ESCALA_KELVIN = ((2500, "#FF8A1F"), (3200, "#FFA94D"),
                     (4000, "#FFC58A"), (5000, "#FFE3C4"),
                     (5600, "#F6F0E4"), (6500, "#DCE7FF"),
                     (7500, "#BCD3FF"), (10000, "#9DBFFF"))
    COLOR_SIN_KELVIN = "#BFBFBF"

    # --- Ruido aceptable por color: una tabla de tres filas (canal y zona
    #     desde la que su ruido es aceptable) a la izquierda, hasta esta
    #     fracción del ancho entre márgenes y con estos anchos de columna
    #     (Tony, 2026-11-13: sustituye a las franjas por tercio). Los dos
    #     colores fuertes son también los del semáforo de la secuencia de
    #     ISO; los tenues, los de las celdas de las tablas (bien, aviso,
    #     mal). El canal, el color suyo aclarado esta fracción hacia el
    #     blanco
    RUIDO_TABLA_ANCHO = 0.5
    ANCHOS_RUIDO = (0.8, 1.2)
    RUIDO_BIEN = "#5FA777"
    RUIDO_MAL = "#D9534F"
    TINTE_BIEN = "#CDE7D3"
    TINTE_AVISO = "#FBE3B0"
    TINTE_MAL = "#F3C6C2"
    TINTES_RUIDO = {KXL.RUIDO_TODO: TINTE_BIEN, KXL.RUIDO_DESDE: TINTE_AVISO,
                    KXL.RUIDO_NINGUNO: TINTE_MAL}
    CANAL_ACLARADO = 0.7

    # --- Tablas de la derecha, junto a las de la izquierda (píxeles
    #     defectuosos junto al ruido, Kelvin neutros junto a los
    #     balances): desde esta fracción del ancho entre márgenes, con
    #     estos anchos de columna (Tony, 2026-11-13)
    TABLAS_DERECHA_DESDE = 0.54
    ANCHOS_PIXELES = (1.5, 0.9, 0.9)
    ANCHOS_NEUTRAS = (1.0, 0.7, 1.25, 1.25)

    # --- Gráficas: grosor de las líneas, tamaño de los puntos y ancho de
    #     las barras (en zonas). El esperado, una banda gris ancha y casi
    #     opaca: el sensor va encima, casi igual, y no debe taparlo
    LINEA = 1.5
    LINEA_OBJETIVO = 1.2
    LINEA_ESPERADO = 7
    OPACIDAD_ESPERADO = 0.75
    PUNTO = 3.5
    BARRA = 0.26

    # --- Sin dato en una tabla
    SIN_DATO = KXL.SIN_DATO

    # --- Página de la secuencia de ISO: una columna por ISO (la primera,
    #     los rótulos, más ancha), porcentajes con un decimal y, debajo,
    #     una nota por ISO estimado o sin medir y la conclusión. Fondo de
    #     la textura en sombras, en el orden de KXL.T_TEXTURA_ISO (se
    #     pierde, justa, se ve)
    TEXTURA_JUSTA = "#F0C05A"
    SEMAFORO_ISO = (RUIDO_MAL, TEXTURA_JUSTA, RUIDO_BIEN)
    ANCHO_ROTULO_ISO = 2.6
    ANCHO_COLUMNA_ISO = 1
    FORMATO_PORCENTAJE = "{} %"
    FORMATO_NOTA_ISO = "{rotulo} {iso}: {nota}"

    # --- Las filas de la tabla que llevan semáforo (de arriba abajo: el
    #     tiempo, el señal/ruido en la ZV y en la Z2, la textura en la Z2 y
    #     desde qué zona hay textura, contadas sin la cabecera; Tony,
    #     2026-11-13)
    FILA_SR_ZV = 1
    FILA_SR_Z2 = 2
    FILA_TEXTURA_ISO = 3

    # --- Textos (claves; los traduce la aplicación)
    T_TITULO_PDF = "titulo_pdf"
    T_SUBTITULO_PDF = "subtitulo_pdf"
    T_FORMATO_FECHA_PDF = "formato_fecha_pdf"
    T_SEPARADOR_DECIMAL = KXL.T_SEPARADOR_DECIMAL
    T_NOTA_TEXTURAS_PDF = "nota_texturas_pdf"
    T_CIFRA_ZONAS = "cifra_zonas"
    T_DESDE_HASTA = "desde_hasta"
    T_NOTA_RECOMENDACIONES = "nota_recomendaciones"
    T_SIN_FASE_2 = "sin_fase_2"
    T_PIE_PDF = "pie_pdf"
    T_PAGINA = "pagina"
    T_AVISO_EXPOSICION_ISO = "aviso_exposicion_iso"
    T_CAB_CANTIDAD = "cab_cantidad_pixeles"
    T_CAB_EN_CAMARA = KXL.T_CAB_EN_CAMARA
    T_CAB_KELVIN_LUZ = KXL.T_CAB_KELVIN_LUZ
    T_CAB_LUZ = KXL.T_CAB_LUZ
    T_CAB_LUZ_MIRED = KXL.T_CAB_LUZ_MIRED
    T_CAB_POR_MPX = "cab_por_mpx"
    T_CAB_RUIDO_DESDE = "cab_ruido_desde"
    T_CAB_SR_Z2 = "cab_sr_z2"
    T_CAB_SR_ZV = "cab_sr_zv"
    T_CAB_TV_ISO = "cab_tv_iso"
    # --- Las luces de los Kelvin neutros: su texto lleva el código que
    #     les da el cálculo (oecfCalc.KNE), que es el que leen también el
    #     libro y el JSON
    T_LUZ_CALIDA = KNE.LUZ_CALIDA
    T_LUZ_FLASH = KNE.LUZ_FLASH
    T_LUZ_LED_FRIO = KNE.LUZ_LED_FRIO
    T_LUZ_SOL = KNE.LUZ_SOL
    T_NOTA_NEUTRAS = KXL.T_NOTA_NEUTRAS
    T_SIN_DATOS_NEUTRA = KXL.T_SIN_DATOS_NEUTRA


# --- Ver KPDF.MOTOR
matplotlib.use(KPDF.MOTOR)


#
class Pdf(object):
    """
    PDF de una serie, desde su libro ya calculado: se crea con la
    ruta, los textos ya traducidos ({clave de KXL o KPDF: texto}), el
    Excel y el nombre del estudiante (el de la carpeta de la serie; ""
    si no hay); escribir() la graba.
    """

    __slots__ = ["__datos", "__estudiante", "__excel", "__iso_aparte",
                 "__ruta", "__textos"]

    #
    def __init__(self, ruta: Path, textos: dict[str, str],
                 excel: Excel, estudiante: str) -> None:

        # --- Variables de instancia
        self.__ruta: Path = ruta
        self.__textos: dict[str, str] = textos
        self.__excel: Excel = excel
        self.__datos = excel.review
        self.__estudiante: str = estudiante

        # --- True si la secuencia de ISO no cabe en la página 2 y va en una
        #     tercera (se decide al escribir)
        self.__iso_aparte: bool = False

    #
    # --- Métodos públicos
    #
    # region Métodos públicos

    #
    def escribir(self) -> None:
        """
        Escribe las dos páginas: la latitud, las gráficas y las
        recomendaciones; los balances, el ruido aceptable, los píxeles
        defectuosos y, si cabe debajo, la secuencia de ISO (si no, en una
        tercera página).
        """
        k = self.__excel.valores_constantes()
        puntos = self.__excel.puntos_curva(k)
        estilo = {"font.family": KPDF.FUENTE, "font.size": KPDF.LETRA,
                  "axes.edgecolor": KPDF.EJES, "axes.labelcolor": KPDF.GRIS,
                  "xtick.color": KPDF.GRIS, "ytick.color": KPDF.GRIS}
        # --- type: ignore: rc_context pide sus propios nombres de clave
        #     (RcKeyType); un diccionario de cadenas funciona igual
        with (matplotlib.rc_context(estilo),                 # type: ignore
              PdfPages(self.__ruta) as pdf):
            self.__iso_aparte = self.iso_no_cabe(k, puntos)
            pdf.savefig(self.pagina_curva(k, puntos))
            pdf.savefig(self.pagina_datos(k, puntos)[0])
            if self.__iso_aparte:
                pdf.savefig(self.pagina_iso(k))

    #
    def paginas(self) -> int:
        """ Cuántas páginas tiene: una más si la secuencia de ISO no cabe
            en la segunda. """
        return KPDF.PAGINAS + (1 if self.__iso_aparte else 0)

    #
    def iso_no_cabe(self, k: dict, puntos: list[PuntoCurva]) -> bool:
        """
        Saber si hay secuencia de ISO y no cabe debajo de lo que lleva la
        página 2: se dibuja la página 2 y la sección de ISO en páginas de
        prueba, que se tiran, y se mide dónde acaba (sin pasar de
        KPDF.LIMITE_ABAJO).
        """
        if not self.__datos.isos:
            return False
        fin = self.pagina_datos(k, puntos)[1] - KPDF.ENTRE_APARTADOS
        prueba = Figure(figsize=KPDF.PAGINA)
        return self.seccion_iso(prueba, fin, k) < KPDF.LIMITE_ABAJO

    #
    def pagina_curva(self, k: dict, puntos: list[PuntoCurva]) -> Figure:
        """
        Página 1: la latitud de texturas (escala de zonas en su gris, con
        los tramos apreciable y recomendado, y las dos cifras), las
        gráficas de la curva tonal y de la diferencia en L*, una al lado
        de la otra, y las recomendaciones para la curva del revelador.
        """
        t = self.__textos
        fig = self.pagina(1)
        limites = self.__excel.limites_texturas(k, self.__excel.texturas(k))
        self.apartado(fig, KPDF.APARTADO_LATITUD, t[KXL.T_TEXTURAS])
        sin_tela = not isinstance(self.__datos.tela, Ventana)
        self.nota(fig, KPDF.APARTADO_LATITUD - KPDF.A_LA_NOTA,
                  t[KXL.T_SIN_TELA] if sin_tela
                  else t[KPDF.T_NOTA_TEXTURAS_PDF])
        self.escala(fig, k, puntos, None if sin_tela else limites)
        for i, (clave, valores) in enumerate(limites.items()):
            self.cifra(fig, KPDF.IZQUIERDA + (i * KPDF.CIFRAS_PASO), k,
                       t[clave], valores)
        self.apartado(fig, KPDF.APARTADO_CURVA,
                      self.titulo_graf(KXL.T_G_CURVA),
                      desde=KPDF.TITULO_CURVA[0], hasta=KPDF.TITULO_CURVA[1])
        self.graf_curva(fig, k, puntos)
        self.apartado(fig, KPDF.APARTADO_CURVA,
                      self.titulo_graf(KXL.T_G_DIFERENCIA),
                      desde=KPDF.TITULO_DIFERENCIA[0],
                      hasta=KPDF.TITULO_DIFERENCIA[1])
        self.graf_diferencia(fig, k, puntos)
        self.recomendaciones(fig, KPDF.APARTADO_RECOMENDACIONES, k, puntos)
        return fig

    #
    def recomendaciones(self, fig: Figure, y: float, k: dict,
                        puntos: list[PuntoCurva]) -> float:
        """
        Recomendaciones para la curva del revelador, desde y (el título)
        hacia abajo: una tabla con las zonas enteras (L* objetivo y del
        revelador, entrada y salida). Devuelve dónde acaba.
        """
        t = self.__textos
        self.apartado(fig, y, t[KXL.T_RECOMENDACIONES])
        fin = self.nota(fig, y - KPDF.A_LA_NOTA,
                        t[KPDF.T_NOTA_RECOMENDACIONES])
        enteras = [p for p in puntos
                   if (p.tercio_ev % k[KXL.C_TERCIO_POR_ZONA]) == 0]
        filas = [(p.nombre, self.numero(p.objetivo, 1),
                  self.numero(p.revelador, 1), self.numero(p.entrada, 0),
                  self.numero(p.salida, 0)) for p in enteras]
        y = self.tabla(fig, self.bajo_nota(y, fin), tuple(t[c] for c in (
            KXL.T_CAB_ZONA, KXL.T_CAB_L_OBJETIVO, KXL.T_CAB_L_REVELADOR,
            KXL.T_CAB_ENTRADA, KXL.T_CAB_SALIDA)), filas,
            KPDF.ANCHOS_RECOMENDACIONES)
        if all(p.revelador is None for p in enteras):
            y = self.nota(fig, y - KPDF.TABLA_A_NOTA, t[KPDF.T_SIN_FASE_2])
        return y

    #
    def pagina_datos(self, k: dict,
                     puntos: list[PuntoCurva]) -> tuple[Figure, float]:
        """
        Página 2: balances de blancos (sin tomas de balance, lo dice) con
        los Kelvin que poner en la cámara con cada luz, y debajo el ruido
        aceptable por color con los píxeles defectuosos y, si cabe, la
        secuencia de ISO. Devuelve la página y dónde acaba lo de antes de
        la secuencia de ISO.
        """
        fig = self.pagina(2)
        y = self.balances(fig, KPDF.APARTADO_PAGINA)
        y = self.ruido_y_pixeles(fig, y - KPDF.ENTRE_APARTADOS, k)
        if self.__datos.isos and (not self.__iso_aparte):
            self.seccion_iso(fig, y - KPDF.ENTRE_APARTADOS, k)
        return fig, y

    #
    def balances(self, fig: Figure, y: float) -> float:
        """
        Balances de blancos, desde y (el título) hacia abajo: la tabla de
        las tomas a la izquierda y, a su derecha, los Kelvin que poner en
        la cámara con cada luz habitual. Sin tomas de balance, lo dice.
        Devuelve dónde acaba.
        """
        t, d = self.__textos, self.__datos
        self.apartado(fig, y, t[KXL.T_BALANCES])
        if not d.balancesDistintos:
            return self.nota(fig, y - KPDF.A_LA_NOTA, t[KXL.T_SIN_BALANCES])
        fin = self.nota(fig, y - KPDF.A_LA_NOTA, t[KXL.T_NOTA_BALANCES])

        # --- Cada Kelvin en dos columnas: el anotado, número y color; el
        #     medido, color y número. Las de color, sin texto
        colores = {}
        for fila, b in enumerate(d.balancesDistintos):
            colores[(fila, KPDF.COL_COLOR_ANOTADO)] = self.color_kelvin(
                b.kelvin_cam)
            colores[(fila, KPDF.COL_COLOR_MEDIDO)] = self.color_kelvin(
                b.kelvin)
        arriba = self.bajo_nota(y, fin)
        y_tabla = self.tabla(fig, arriba, (
            t[KXL.T_CAB_BALANCE], t[KXL.T_CAB_KELVIN_ANOTADO], "",
            t[KXL.T_CAB_KELVIN_MEDIDO], ""), [
            (self.__excel.nombre_balance(b.nombre),
             self.numero(b.kelvin_cam, 0), "", "",
             self.numero(b.kelvin, 0))
            for b in d.balancesDistintos], KPDF.ANCHOS_BALANCES,
            colores, KPDF.UNIONES_BALANCES, derecha=KPDF.IZQUIERDA + (
                KPDF.BALANCES_ANCHO * (KPDF.DERECHA - KPDF.IZQUIERDA)))

        # --- A la derecha, qué Kelvin poner en la cámara con cada luz
        #     habitual
        return min(y_tabla,
                   self.kelvin_neutros(fig, arriba, d.balancesDistintos))

    #
    def ruido_y_pixeles(self, fig: Figure, y: float, k: dict) -> float:
        """
        Ruido aceptable por color, desde y (el título) hacia abajo: en el
        título, al final de la línea, el umbral; debajo, por canal, la zona
        desde la que es aceptable (a la izquierda) y los píxeles
        defectuosos (a la derecha). Devuelve dónde acaba.
        """
        t = self.__textos
        self.apartado(fig, y, self.__excel.titulo_ruido_color(),
                      t[KXL.T_RUIDO_COLOR_NOTA].format(
                          umbral=k[KXL.C_SNR_MINIMA]))
        arriba = y - KPDF.A_LA_TABLA_SIN_NOTA
        return min(self.tabla_ruido(fig, arriba, k),
                   self.tabla_pixeles(fig, arriba))

    #
    def kelvin_neutros(self, fig: Figure, y: float,
                       balances: list[BalanceMedido]) -> float:
        """
        A la derecha de la tabla de balances, desde y hacia abajo: una
        tabla con una fila por luz habitual (KNE.LUCES_NEUTRAS: su Kelvin,
        el rango que cubre la tolerancia en mired y el rango de Kelvin que
        poner en la cámara para que salga neutra con ella; «≈» si es una
        estimación, o «sin datos») y debajo una nota que explica el mired.
        Devuelve dónde acaba (y, si no hay nada que decir).
        """
        t = self.__textos
        rangos = rangos_neutros(balances)
        if not rangos:
            return y
        mired = KNE.TOLERANCIA_MIRED
        filas = self.__excel.filas_neutros(rangos)
        colores = {(i, 1): self.color_kelvin(r.kelvin)
                   for i, r in enumerate(rangos)}
        izquierda = self.columna_derecha()
        y = self.tabla(fig, y, (
            t[KPDF.T_CAB_LUZ], t[KPDF.T_CAB_KELVIN_LUZ],
            t[KPDF.T_CAB_LUZ_MIRED].format(mired=mired),
            t[KPDF.T_CAB_EN_CAMARA]), filas, KPDF.ANCHOS_NEUTRAS, colores,
            izquierda=izquierda)
        return self.nota(fig, y - KPDF.TABLA_A_NOTA,
                         t[KPDF.T_NOTA_NEUTRAS].format(mired=mired),
                         izquierda=izquierda)

    #
    def pagina_iso(self, k: dict) -> Figure:
        """
        Página de la secuencia de ISO (la última), para el estudiante, si
        no cabe en la página 2: solo su sección (ver seccion_iso).
        """
        fig = self.pagina(self.paginas())
        self.seccion_iso(fig, KPDF.APARTADO_PAGINA, k)
        return fig

    #
    def seccion_iso(self, fig: Figure, y: float, k: dict) -> float:
        """
        Sección de la secuencia de ISO, desde y (el título) hacia abajo:
        su nota y una tabla con una columna por ISO bajo una banda «ISO»:
        el tiempo de la ZV, el señal/ruido en la ZV y en la Z2, la textura
        en la Z2 y desde qué zona hay textura. Los de ruido y textura,
        en semáforo y con su número o texto; los números de cada ISO, en
        la hoja ISO del libro. Debajo, un aviso por exposición que se
        aparta del ISO inicial y una nota por ISO estimado o sin medir.
        Devuelve dónde acaba.
        """
        t, excel = self.__textos, self.__excel
        filas_iso = self.__datos.filasISO
        umbral = excel.umbral_iso(k)
        self.apartado(fig, y, t[KXL.T_TITULO_ISO])
        fin = self.nota(fig, y - KPDF.A_LA_NOTA,
                        excel.rotulo_sombra(t[KXL.T_NOTA_ISO_PDF]))
        diafragma = excel.diafragma_iso()
        rotulo_tv = (t[KPDF.T_CAB_TV_ISO].format(f=diafragma) if diafragma
                     else t[KXL.T_TV])
        filas = [
            (rotulo_tv, *(excel.tv_iso(f) or KPDF.SIN_DATO
                          for f in filas_iso)),
            (t[KPDF.T_CAB_SR_ZV],
             *(excel.senal_ruido_iso(f.ruido_zv) or KPDF.SIN_DATO
               for f in filas_iso)),
            (excel.rotulo_sombra(t[KPDF.T_CAB_SR_Z2]),
             *(excel.senal_ruido_iso(f.ruido_z2) or KPDF.SIN_DATO
               for f in filas_iso)),
            (excel.rotulo_sombra(t[KXL.T_CAB_SE_APRECIA]),
             *(excel.aprecia_iso(f, k, umbral) or KPDF.SIN_DATO
               for f in filas_iso)),
            (t[KXL.T_CAB_SOMBRAS_ISO],
             *(excel.sombras_iso(f, k, umbral) or KPDF.SIN_DATO
               for f in filas_iso))]
        colores = {}
        for i, f in enumerate(filas_iso):
            for fila, nivel in (
                    (KPDF.FILA_SR_ZV, excel.nivel_ruido_iso(f.ruido_zv, k)),
                    (KPDF.FILA_SR_Z2, excel.nivel_ruido_iso(f.ruido_z2, k)),
                    (KPDF.FILA_TEXTURA_ISO,
                     excel.nivel_textura_iso(f, k, umbral))):
                if nivel is not None:
                    colores[(fila, i + 1)] = KPDF.SEMAFORO_ISO[nivel]
        y = self.tabla(
            fig, self.bajo_nota(y, fin),
            ("", *(str(f.iso) for f in filas_iso)), filas,
            (KPDF.ANCHO_ROTULO_ISO,
             *((KPDF.ANCHO_COLUMNA_ISO,) * len(filas_iso))), colores,
            banda=(t[KXL.T_CAB_ISO], 1, len(filas_iso)))
        for f in filas_iso:
            exposicion = excel.exposicion_iso(f, k)
            if exposicion and (exposicion != t[KXL.T_EXPOSICION_IGUAL]):
                y = self.nota(fig, y - KPDF.TABLA_A_NOTA,
                              t[KPDF.T_AVISO_EXPOSICION_ISO].format(
                                  rotulo=t[KXL.T_CAB_ISO], iso=f.iso,
                                  desvio=exposicion), KXL.COLOR_NEGATIVO)
        for f in filas_iso:
            nota = excel.nota_iso(f)
            if nota:
                y = self.nota(fig, y - KPDF.TABLA_A_NOTA,
                              KPDF.FORMATO_NOTA_ISO.format(
                                  rotulo=t[KXL.T_CAB_ISO], iso=f.iso,
                                  nota=nota))
        return y

    # endregion Métodos públicos

    #
    # --- Piezas de las páginas
    #
    # region Piezas

    #
    def pagina(self, numero: int) -> Figure:
        """
        Página nueva con su cabecera (cámara, fecha, bits y exposición de
        la Z-V, sobre una banda verde, y a la derecha el nombre del
        estudiante, sin traducir) y su pie (con su número).
        """
        t, d = self.__textos, self.__datos
        fig = Figure(figsize=KPDF.PAGINA)
        fig.patches.append(Rectangle(
            (0, KPDF.BANDA_ABAJO), 1, 1 - KPDF.BANDA_ABAJO,
            transform=fig.transFigure, color=KPDF.VERDE, zorder=0))
        fig.text(KPDF.IZQUIERDA, KPDF.TITULO_Y,
                 t[KPDF.T_TITULO_PDF].format(cam=d.cam),
                 fontsize=KPDF.LETRA_TITULO, weight="bold", color="white",
                 va="center")
        if self.__estudiante:
            fig.text(KPDF.DERECHA, KPDF.TITULO_Y, self.__estudiante,
                     fontsize=KPDF.LETRA_TITULO, weight="bold",
                     color="white", va="center", ha="right")
        fecha = (datetime.fromisoformat(d.fecha).strftime(
            t[KPDF.T_FORMATO_FECHA_PDF]) if d.fecha else KPDF.SIN_DATO)
        exp = (OECF.TextoExp(d.f, d.tv, d.iso, tuple(
            t[c] for c in KXL.ROTULOS_EXP)) or KPDF.SIN_DATO)
        fig.text(KPDF.IZQUIERDA, KPDF.SUBTITULO_Y,
                 t[KPDF.T_SUBTITULO_PDF].format(
                     fecha=fecha, bits=d.bits or KPDF.SIN_DATO,
                     exp=exp),
                 fontsize=KPDF.LETRA_SUBTITULO, color="white", va="center")
        fig.text(KPDF.IZQUIERDA, KPDF.PIE_Y, t[KPDF.T_PIE_PDF],
                 fontsize=KPDF.LETRA_PIE, color=KPDF.GRIS)
        fig.text(KPDF.DERECHA, KPDF.PIE_Y, t[KPDF.T_PAGINA].format(
            pagina=numero, paginas=self.paginas()), fontsize=KPDF.LETRA_PIE,
            color=KPDF.GRIS, ha="right")
        return fig

    #
    def apartado(self, fig: Figure, y: float, texto: str,
                 derecha: str = "", desde: float = KPDF.IZQUIERDA,
                 hasta: float = KPDF.DERECHA) -> None:
        """ Título de una sección, en verde, con una raya debajo (entre
            desde y hasta: de margen a margen, si no se dice) y, si se da,
            un texto en gris al final de su línea (a la derecha). """
        fig.text(desde, y, texto, fontsize=KPDF.LETRA_APARTADO,
                 weight="bold", color=KPDF.VERDE)
        if derecha:
            fig.text(hasta, y, derecha, fontsize=KPDF.LETRA_NOTA,
                     color=KPDF.GRIS, ha="right")
        raya = y - KPDF.SUBRAYA
        fig.lines.append(Line2D([desde, hasta], [raya, raya],
                                transform=fig.transFigure, color=KPDF.BORDE,
                                linewidth=1))

    #
    def nota(self, fig: Figure, y: float, texto: str,
             color: str = KPDF.GRIS, izquierda: float = KPDF.IZQUIERDA,
             derecha: float = KPDF.DERECHA) -> float:
        """
        Nota en gris (o en este color), desde y (lo alto de su primera
        línea) hacia abajo, partida en líneas que no pasan de la raya de
        las secciones (de KPDF.IZQUIERDA a KPDF.DERECHA, si no se dice).
        Devuelve dónde acaba.
        """
        nota = fig.text(izquierda, y, "\n".join(self.partir(
            fig, texto, KPDF.LETRA_NOTA, derecha - izquierda)),
            fontsize=KPDF.LETRA_NOTA, color=color, va="top")
        return self.caja(fig, nota).y0

    #
    def partir(self, fig: Figure, texto: str, letra: float,
               ancho: float = KPDF.DERECHA - KPDF.IZQUIERDA) -> list[str]:
        """
        Líneas de un texto, palabra a palabra, sin pasar del ancho (el de
        entre márgenes, si no se dice) con ese tamaño de letra (lo mide
        como lo dibujará).
        """
        medida = fig.text(0, 0, "", fontsize=letra)
        lineas: list[str] = []
        linea = ""
        for palabra in texto.split():
            prueba = f"{linea} {palabra}" if linea else palabra
            medida.set_text(prueba)
            if linea and (self.caja(fig, medida).width > ancho):
                lineas.append(linea)
                linea = palabra
            else:
                linea = prueba
        lineas.append(linea)
        medida.remove()
        return lineas

    #
    @staticmethod
    def caja(fig: Figure, texto: Text) -> Bbox:
        """
        Caja que ocupa un texto, en fracción de la página. Lo mide con el
        lienzo de Agg de la página (se lo pone la primera vez).
        """
        lienzo = (fig.canvas if isinstance(fig.canvas, FigureCanvasAgg)
                  else FigureCanvasAgg(fig))
        return texto.get_window_extent(lienzo.get_renderer()).transformed(
            fig.transFigure.inverted())

    #
    @staticmethod
    def bajo_nota(y: float, fin: float) -> float:
        """
        Dónde empieza la tabla de una sección con nota: a su distancia de
        siempre o, si la nota es tan larga que llega, más abajo.
        """
        return min(y - KPDF.A_LA_TABLA, fin - KPDF.NOTA_A_TABLA)

    #
    def escala(self, fig: Figure, k: dict, puntos: list[PuntoCurva],
               limites: dict | None) -> None:
        """
        Escala de zonas en peine: una tira con un paso por tercio, cada uno
        en su gris (el de su L* objetivo en sRGB) y con un borde gris para
        que el blanco se vea; los de zona entera, altos, y los de tercio,
        a media altura. Debajo, el peine (diente largo en las zonas
        enteras, corto en los tercios) y los nombres de las zonas enteras,
        con la ZV destacada. Con paño, encima, los tramos de la latitud
        apreciable y recomendada.
        """
        t = self.__textos
        ax = fig.add_axes(KPDF.ESCALA)
        zona_zv = k[KXL.C_ZONA_ZV]
        por_zona = k[KXL.C_TERCIO_POR_ZONA]
        paso = 1 / por_zona
        izquierda = -(paso / 2)
        derecha = (2 * zona_zv) + (paso / 2)
        for p in puntos:
            zona = zona_zv + (p.tercio_ev / por_zona)
            # --- El gris del objetivo: su sRGB, la salida de la curva
            gris = p.salida / k[KXL.C_ESCALA_CURVA]
            entera = ((p.tercio_ev % por_zona) == 0)
            ax.add_patch(Rectangle(
                (zona - (paso / 2), 0), paso,
                KPDF.ALTO_ZONA if entera else KPDF.ALTO_TERCIO,
                facecolor=(gris,) * 3, edgecolor=KPDF.MARCO_TIRA,
                linewidth=KPDF.LINEA_TIRA))
            ax.plot([zona, zona],
                    [0, -(KPDF.DIENTE_ZONA if entera else KPDF.DIENTE_TERCIO)],
                    color=KPDF.TINTA if entera else KPDF.GRIS,
                    linewidth=KPDF.LINEA_DIENTE)
            if not entera:
                continue
            zv = (p.tercio_ev == 0)
            ax.text(zona, KPDF.NOMBRES_Y, p.nombre, ha="center", va="center",
                    color="white" if zv else KPDF.TINTA,
                    weight="bold" if zv else "normal",
                    bbox=({"boxstyle": KPDF.MARCO_ZV, "facecolor": KPDF.TINTA,
                           "edgecolor": "none"} if zv else None))
        if limites is not None:
            for clave, (alto, grueso), color in (
                    (KXL.T_APRECIABLE, KPDF.TRAMO_APRECIABLE, KPDF.VERDE),
                    (KXL.T_RECOMENDADA, KPDF.TRAMO_RECOMENDADO,
                     KPDF.VERDE_OSCURO)):
                sombra, luz, _ = limites[clave]
                if not (isinstance(sombra, float) and isinstance(luz, float)):
                    continue
                ax.plot([sombra, luz], [alto, alto], color=color,
                        linewidth=grueso, solid_capstyle="butt")
                for x in (sombra, luz):
                    ax.plot([x, x], [alto - KPDF.PATA_TRAMO,
                                     alto + KPDF.PATA_TRAMO], color=color,
                            linewidth=KPDF.LINEA)
                ax.text(izquierda, alto, t[clave], ha="left", va="center",
                        fontsize=KPDF.LETRA_NOTA, color=color)
        # --- De Z0 a ZX (la ZV está en medio), justo lo que ocupa la tira
        ax.set_xlim(izquierda, derecha)
        ax.set_ylim(*KPDF.ESCALA_Y)
        ax.axis("off")

    #
    def cifra(self, fig: Figure, x: float, k: dict, rotulo: str,
              valores: tuple) -> None:
        """
        Recuadro con una latitud (apreciable o recomendada): sus zonas en
        grande y, al lado, de qué zona a qué zona.
        """
        t = self.__textos
        sombra, luz, ancho = valores
        fig.patches.append(FancyBboxPatch(
            (x, KPDF.CIFRAS_Y), KPDF.CIFRAS_ANCHO, KPDF.CIFRAS_ALTO,
            transform=fig.transFigure,
            boxstyle=f"round,pad=0,rounding_size={KPDF.CIFRAS_REDONDEO}",
            facecolor=KPDF.VERDE_CLARO, edgecolor=KPDF.BORDE, linewidth=0.8))
        arriba = KPDF.CIFRAS_Y + KPDF.CIFRAS_ALTO
        fig.text(x + KPDF.CIFRAS_MARGEN, arriba - KPDF.CIFRAS_MARGEN, rotulo,
                 color=KPDF.GRIS)
        cifra = (t[KPDF.T_CIFRA_ZONAS].format(
            zonas=self.__excel.tercios_texto(ancho))
            if isinstance(ancho, float) else ancho)
        fig.text(x + KPDF.CIFRAS_MARGEN, KPDF.CIFRAS_Y + KPDF.CIFRAS_NUMERO_Y,
                 cifra, fontsize=KPDF.LETRA_CIFRA, weight="bold",
                 color=KPDF.TINTA)
        if isinstance(sombra, float) and isinstance(luz, float):
            fig.text((x + KPDF.CIFRAS_ANCHO) - KPDF.CIFRAS_MARGEN,
                     KPDF.CIFRAS_Y + KPDF.CIFRAS_DESDE_Y,
                     t[KPDF.T_DESDE_HASTA].format(
                         desde=self.nombre(sombra, k),
                         hasta=self.nombre(luz, k)),
                     fontsize=KPDF.LETRA_SUBTITULO, color=KPDF.GRIS,
                     ha="right", va="center")

    #
    def graf_curva(self, fig: Figure, k: dict,
                   puntos: list[PuntoCurva]) -> None:
        """
        Curva tonal en L*: esperado (banda gris ancha, detrás), objetivo
        (discontinuo), sensor (delante, fino, dentro de la banda: casi
        coincide con el esperado) y revelador (si lo hay).
        """
        t = self.__textos
        ax = fig.add_axes(KPDF.GRAF_CURVA)
        x = self.zonas(puntos, k)
        ax.plot(x, [p.esperado for p in puntos], color=KXL.COLOR_ESPERADO,
                linewidth=KPDF.LINEA_ESPERADO, alpha=KPDF.OPACIDAD_ESPERADO,
                solid_capstyle="butt", label=t[KXL.T_CAB_ESPERADO],
                zorder=1)
        ax.plot(x, [p.objetivo for p in puntos], color=KXL.COLOR_OBJETIVO,
                linewidth=KPDF.LINEA_OBJETIVO, linestyle="--",
                label=t[KXL.T_CAB_L_OBJETIVO], zorder=2)
        if any(p.revelador is not None for p in puntos):
            ax.plot(x, [math.nan if (p.revelador is None) else p.revelador
                        for p in puntos], color=KPDF.REVELADOR,
                    linewidth=KPDF.LINEA, marker="o", markersize=KPDF.PUNTO,
                    label=t[KXL.T_S_REVELADOR], zorder=3)
        ax.plot(x, [math.nan if (p.sensor is None) else p.sensor
                    for p in puntos], color=KXL.COLOR_SENSOR,
                linewidth=KPDF.LINEA, label=t[KXL.T_S_SENSOR], zorder=4)
        self.ejes(ax, k, t[KXL.T_EJE_LSTAR])
        ax.set_ylim(*KXL.EJE_LSTAR[:2])
        ax.legend(loc="upper left", frameon=False, fontsize=KPDF.LETRA_NOTA)

    #
    def graf_diferencia(self, fig: Figure, k: dict,
                        puntos: list[PuntoCurva]) -> None:
        """
        Diferencia en L* del revelador con el objetivo: cuánto se separa
        el revelado de la escala que se busca, lo que el estudiante
        corrige (el signo se lee en el eje); sin dato, hueco. La leyenda,
        dentro, arriba a la izquierda. Sin revelador, lo dice.
        """
        t = self.__textos
        ax = fig.add_axes(KPDF.GRAF_DIFERENCIA)
        ax.axhline(0, color=KPDF.CERO, linewidth=0.8)
        self.ejes(ax, k, t[KXL.T_EJE_DIF_LSTAR])
        if all(p.revelador is None for p in puntos):
            ax.text(0.5, 0.5, t[KPDF.T_SIN_FASE_2], transform=ax.transAxes,
                    ha="center", va="center", color=KPDF.GRIS,
                    fontsize=KPDF.LETRA_NOTA)
            return
        ax.bar(self.zonas(puntos, k),
               [math.nan if (p.revelador is None)
                else (p.revelador - p.objetivo) for p in puntos],
               width=KPDF.BARRA, color=KPDF.REVELADOR,
               label=t[KXL.T_S_REVELADOR])
        ax.legend(loc="upper left", frameon=False, fontsize=KPDF.LETRA_NOTA)

    #
    def ejes(self, ax: Axes, k: dict, nombre_y: str) -> None:
        """
        Ejes de una gráfica: las zonas enteras abajo (con su nombre), el
        nombre del eje y, sus números con el separador del idioma, la
        rejilla horizontal y sin marco arriba ni a la derecha.
        """
        zona_zv = k[KXL.C_ZONA_ZV]
        por_zona = k[KXL.C_TERCIO_POR_ZONA]
        enteras = range(0, (2 * zona_zv) + 1)
        ax.set_xticks(list(enteras), [
            Excel.nombre_zona(round((z - zona_zv) * por_zona))
            for z in enteras])
        ax.set_ylabel(nombre_y)
        ax.yaxis.set_major_formatter(FuncFormatter(self.marca_eje))
        ax.grid(axis="y", color=KPDF.REJILLA, linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    #
    def tabla_ruido(self, fig: Figure, y: float, k: dict) -> float:
        """
        Ruido aceptable por color, desde y hacia abajo: una tabla de tres
        filas (rojo, verde y azul) con la zona desde la que el ruido de
        cada canal es aceptable, en la mitad izquierda de la página (hasta
        KPDF.RUIDO_TABLA_ANCHO). El canal, con su color aclarado; la zona,
        en verde si lo es en todo el rango, en ámbar si desde una zona y en
        rojo si en ninguna. Devuelve dónde acaba.
        """
        t, excel = self.__textos, self.__excel
        filas, colores = [], {}
        for j, (clave, suelo) in enumerate(zip(KXL.T_CANALES,
                                               excel.suelos_ruido(k))):
            zona, estado = excel.zona_ruido(suelo)
            filas.append((t[clave], zona))
            colores[(j, 0)] = self.aclarar(KXL.COLORES_CANALES[j])
            colores[(j, 1)] = KPDF.TINTES_RUIDO.get(
                estado, KPDF.COLOR_SIN_KELVIN)
        derecha = KPDF.IZQUIERDA + (
            KPDF.RUIDO_TABLA_ANCHO * (KPDF.DERECHA - KPDF.IZQUIERDA))
        return self.tabla(fig, y, (
            t[KXL.T_CAB_CANAL], t[KPDF.T_CAB_RUIDO_DESDE]), filas,
            KPDF.ANCHOS_RUIDO, colores, derecha=derecha)

    #
    def tabla_pixeles(self, fig: Figure, y: float) -> float:
        """
        Píxeles defectuosos, a la derecha de la tabla del ruido (desde
        KPDF.TABLAS_DERECHA_DESDE), desde y hacia abajo: una fila por tipo
        (calientes y muertos) con cuántos y cuántos por megapíxel, en verde
        si no hay ninguno y en ámbar si hay. Sin tapadas no se pueden
        contar los calientes: lo dice una nota debajo. Devuelve dónde
        acaba (y, si no se contaron píxeles).
        """
        t = self.__textos
        filas = self.__excel.filas_pixeles()
        if not filas:
            return y
        colores = {}
        for i, (_, _, _, ninguno) in enumerate(filas):
            colores[(i, 1)] = colores[(i, 2)] = (
                KPDF.COLOR_SIN_KELVIN if (ninguno is None)
                else (KPDF.TINTE_BIEN if ninguno else KPDF.TINTE_AVISO))
        izquierda = self.columna_derecha()
        y = self.tabla(fig, y, (
            t[KXL.T_PIXELES], t[KPDF.T_CAB_CANTIDAD],
            t[KPDF.T_CAB_POR_MPX]), [fila[:3] for fila in filas],
            KPDF.ANCHOS_PIXELES, colores, izquierda=izquierda)
        if self.__datos.pixeles.calientes is None:               # type: ignore
            y = self.nota(fig, y - KPDF.TABLA_A_NOTA,
                          t[KXL.T_PIXELES_SIN_TAPADAS], izquierda=izquierda)
        return y

    #
    @staticmethod
    def columna_derecha() -> float:
        """ Dónde empiezan las tablas de la derecha (ver
            KPDF.TABLAS_DERECHA_DESDE). """
        return KPDF.IZQUIERDA + (KPDF.TABLAS_DERECHA_DESDE
                                 * (KPDF.DERECHA - KPDF.IZQUIERDA))

    #
    @staticmethod
    def aclarar(color: str) -> str:
        """ Color más claro: el suyo mezclado con blanco (KPDF.CANAL_ACLARADO
            hacia el blanco). """
        return to_hex([c + ((1 - c) * KPDF.CANAL_ACLARADO)
                       for c in to_rgb(color)])

    #
    def tabla(self, fig: Figure, y: float, cabeceras: tuple[str, ...],
              filas: list[tuple], anchos: tuple[float, ...],
              colores: dict[tuple[int, int], str] | None = None,
              uniones: tuple[tuple[int, int], ...] = (),
              izquierda: float = KPDF.IZQUIERDA,
              derecha: float = KPDF.DERECHA,
              banda: tuple[str, int, int] | None = None) -> float:
        """
        Tabla como las del libro (cabecera verde, filas alternas), entre
        izquierda y derecha (a todo el ancho entre márgenes, si no se
        dice), desde y hacia abajo. Devuelve dónde acaba. colores: el
        fondo propio de algunas celdas, {(fila, columna): color}, con la
        fila contada sin la cabecera. uniones: celdas de la cabecera que
        ocupan varias columnas, (primera columna, cuántas); su texto es el
        de la primera. banda: una fila verde sobre la cabecera, solo sobre
        algunas columnas (texto, primera columna, cuántas)
        """
        ancho = derecha - izquierda
        total = sum(anchos)
        bordes = [izquierda]
        for a in anchos:
            bordes.append(bordes[-1] + ((ancho * a) / total))
        alto = KPDF.ALTO_FILA
        if banda is not None:
            texto_banda, primera, n_banda = banda
            desde, hasta = bordes[primera], bordes[primera + n_banda]
            fig.patches.append(Rectangle(
                (desde, y - alto), hasta - desde, alto,
                transform=fig.transFigure, facecolor=KPDF.VERDE,
                edgecolor="white", linewidth=0.5))
            fig.text((desde + hasta) / 2, y - (alto / 2), texto_banda,
                     color="white", weight="bold", fontsize=KPDF.LETRA_NOTA,
                     ha="center", va="center")
            y -= alto
        cuantas = dict(uniones)
        cubiertas = {c for primera, n in uniones
                     for c in range(primera + 1, primera + n)}
        for f, fila in enumerate([cabeceras] + list(filas)):
            abajo = y - (alto * (f + 1))
            cabecera = (f == 0)
            fondo = (KPDF.VERDE if cabecera
                     else (KPDF.VERDE_CLARO if (f % 2) else "white"))
            for i, texto in enumerate(fila):
                if cabecera and (i in cubiertas):
                    continue
                izquierda = bordes[i]
                derecha = bordes[i + (cuantas.get(i, 1) if cabecera else 1)]
                propio = (None if (cabecera or (colores is None))
                          else colores.get((f - 1, i)))
                fig.patches.append(Rectangle(
                    (izquierda, abajo), derecha - izquierda, alto,
                    transform=fig.transFigure, facecolor=propio or fondo,
                    edgecolor="white" if cabecera else KPDF.BORDE,
                    linewidth=0.5))
                fig.text((izquierda + derecha) / 2, abajo + (alto / 2),
                         str(texto).replace("\n", " "),
                         color="white" if cabecera else KPDF.TINTA,
                         weight="bold" if cabecera else "normal",
                         fontsize=KPDF.LETRA_NOTA, ha="center", va="center")
        return y - (alto * (len(filas) + 1))

    # endregion Piezas

    #
    # --- Números y nombres
    #
    # region Números

    #
    def titulo_graf(self, clave: str) -> str:
        """ Título de una gráfica, con su número del libro. """
        return KXL.FORMATO_TITULO_GRAF.format(
            numero=KXL.ORDEN_GRAF.index(clave) + 1,
            titulo=self.__textos[clave])

    #
    @staticmethod
    def color_kelvin(kelvin: float | None) -> str:
        """
        Color (aproximado) de la luz de esa temperatura, interpolado entre
        los de KPDF.ESCALA_KELVIN; gris si no hay Kelvin.
        """
        if (kelvin is None) or (not math.isfinite(kelvin)):
            return KPDF.COLOR_SIN_KELVIN
        escala = KPDF.ESCALA_KELVIN
        if kelvin <= escala[0][0]:
            return escala[0][1]
        for (k0, c0), (k1, c1) in zip(escala, escala[1:]):
            if kelvin <= k1:
                t = (kelvin - k0) / (k1 - k0)
                return to_hex([a + ((b - a) * t)
                               for a, b in zip(to_rgb(c0), to_rgb(c1))])
        return escala[-1][1]

    #
    def numero(self, valor: float | int | None, decimales: int) -> str:
        """
        Número con el separador decimal del idioma; sin él (o no finito),
        una raya.
        """
        if (valor is None) or (not math.isfinite(valor)):
            return KPDF.SIN_DATO
        texto = f"{valor:.{decimales}f}"
        return texto.replace(".", self.__textos[KPDF.T_SEPARADOR_DECIMAL])

    #
    def porcentaje(self, valor: float | None) -> str:
        """
        Fracción como porcentaje con un decimal (con el separador del
        idioma); sin ella, una raya.
        """
        if valor is None:
            return KPDF.SIN_DATO
        return KPDF.FORMATO_PORCENTAJE.format(
            self.numero(valor * KXL.CIEN, 1))

    #
    def marca_eje(self, valor: float, _pos: int) -> str:
        """ Marca de un eje: sin decimales si es entera. """
        return self.numero(valor, 0 if float(valor).is_integer() else 1)

    #
    @staticmethod
    def zonas(puntos: list[PuntoCurva], k: dict) -> list[float]:
        """ Posición de cada punto en zonas (Z0 = 0). """
        return [k[KXL.C_ZONA_ZV] + (p.tercio_ev / k[KXL.C_TERCIO_POR_ZONA])
                for p in puntos]

    #
    @staticmethod
    def nombre(zona: float, k: dict) -> str:
        """ Nombre de la zona de una posición (en tercios): Z2 1/3… """
        return Excel.nombre_zona(round((zona - k[KXL.C_ZONA_ZV])
                                       * k[KXL.C_TERCIO_POR_ZONA]))

    # endregion Números
