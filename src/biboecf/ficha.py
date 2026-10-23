# -*- coding: utf-8 *-*
"""
    :Propósito: Ficha PDF de la cámara para el estudiante (dos páginas A4,
                con matplotlib): latitud de texturas, curva tonal y
                diferencia en L*, recomendaciones para la curva del
                revelador, ruido de lectura y negro, y balances de blancos.
                Lo calcula el libro (Excel): la ficha solo lo dibuja. Sin
                los datos del estudiante (ni sus decisiones ni el L* que
                escribe a mano). Sin textos propios: los recibe ya
                traducidos
    :Autor:     Tony Diana
    :Versión:   26.10.18
"""

# cSpell:ignore axhline, backend, backends, boxstyle, capstyle, dejavu
# cSpell:ignore edgecolor, facecolor, figsize, fontsize, frameon, graf
# cSpell:ignore labelcolor, linestyle, linewidth, lstar, markersize
# cSpell:ignore matplotlib, ncol, xlim, xtick, xticks, ylabel, ylim, ytick
# cSpell:ignore zorder

__all__ = ["KFI", "Ficha"]

# --- Bibliotecas estándar Python
import math
from datetime import datetime
from pathlib import Path

# --- Bibliotecas externas
import matplotlib
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.text import Text
from matplotlib.ticker import FuncFormatter
from matplotlib.transforms import Bbox

# --- Bibliotecas internas
from bib import std
from .kernel import OECF
from .excel import KXL, Excel, PuntoCurva
from .teselas import Ventana


#
class KFI(std.EnumMutable):
    """ Diseño de la ficha: página, colores, posiciones y textos. """

    # --- Motor de dibujo de matplotlib: solo a archivo, sin ventanas. Sin
    #     fijarlo, el depurador de VS Code lo engancha a Tk en modo
    #     interactivo y el programa puede no cerrarse (2026-10-19)
    MOTOR = "Agg"

    # --- Página A4 vertical, en pulgadas, y márgenes laterales (fracción)
    PAGINA = (8.27, 11.69)
    IZQUIERDA = 0.06
    DERECHA = 0.94
    PAGINAS = 2

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

    # --- Página 1: latitud (sección, nota, escala de zonas y cifras) y
    #     las dos gráficas: (izquierda, abajo, ancho, alto). La escala va
    #     de margen a margen, como la raya de las secciones; las
    #     gráficas dejan sitio a la izquierda para el nombre del eje
    APARTADO_LATITUD = 0.875
    SUBRAYA = 0.008
    ESCALA = (IZQUIERDA, 0.725, DERECHA - IZQUIERDA, 0.1)
    CIFRAS_Y = 0.62
    CIFRAS_ALTO = 0.085
    CIFRAS_ANCHO = 0.43
    CIFRAS_PASO = 0.45
    APARTADO_CURVA = 0.585
    GRAF_IZQUIERDA = 0.1
    GRAF_CURVA = (GRAF_IZQUIERDA, 0.33, DERECHA - GRAF_IZQUIERDA, 0.225)
    APARTADO_DIFERENCIA = 0.275
    GRAF_DIFERENCIA = (GRAF_IZQUIERDA, 0.06, DERECHA - GRAF_IZQUIERDA,
                       0.185)

    # --- Recuadros de las cifras: margen interior, altura de la cifra
    #     grande y de «de Zx a Zy» sobre su base, y radio de las esquinas
    CIFRAS_MARGEN = 0.02
    CIFRAS_NUMERO_Y = 0.025
    CIFRAS_DESDE_Y = 0.028
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
    TRAMO_APRECIABLE = (1.45, 2.5)
    TRAMO_RECOMENDADO = (1.2, 4)
    PATA_TRAMO = 0.1
    DIENTE_ZONA = 0.3
    DIENTE_TERCIO = 0.15
    LINEA_DIENTE = 0.8
    LINEA_TIRA = 0.5
    NOMBRES_Y = -0.62
    MARCO_ZV = "round,pad=0.25"
    ESCALA_Y = (-0.95, 1.65)

    # --- Página 2: secciones y tablas (alto de fila; separación entre
    #     secciones; de la sección a lo alto de su nota y a su tabla (con
    #     nota o sin ella); hueco mínimo de la nota a la tabla, si la nota
    #     es tan larga que la empuja, y de una tabla a la nota de debajo)
    APARTADO_RECOMENDACIONES = 0.875
    ALTO_FILA = 0.021
    ENTRE_APARTADOS = 0.04
    A_LA_NOTA = 0.014
    A_LA_TABLA = 0.05
    A_LA_TABLA_SIN_NOTA = 0.03
    NOTA_A_TABLA = 0.008
    TABLA_A_NOTA = 0.012
    ANCHOS_RECOMENDACIONES = (1, 1.3, 1.3, 1, 1)
    ANCHOS_RUIDO = (2.4, 1, 1, 1)
    ANCHOS_BALANCES = (1.6, 1, 1)

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
    SIN_DATO = "—"

    # --- Textos (claves; los traduce la aplicación)
    T_TITULO_FICHA = "titulo_ficha"
    T_SUBTITULO_FICHA = "subtitulo_ficha"
    T_FORMATO_FECHA_FICHA = "formato_fecha_ficha"
    T_SEPARADOR_DECIMAL = "separador_decimal"
    T_NOTA_TEXTURAS_FICHA = "nota_texturas_ficha"
    T_CIFRA_ZONAS = "cifra_zonas"
    T_DESDE_HASTA = "desde_hasta"
    T_NOTA_RECOMENDACIONES = "nota_recomendaciones"
    T_SIN_FASE_2 = "sin_fase_2"
    T_RUIDO_FICHA = "ruido_ficha"
    T_NEGRO_FICHA = "negro_ficha"
    T_PIE_FICHA = "pie_ficha"
    T_PAGINA = "pagina"


# --- Ver KFI.MOTOR
matplotlib.use(KFI.MOTOR)


#
class Ficha(object):
    """
    Ficha PDF de una serie, desde su libro ya calculado: se crea con la
    ruta, los textos ya traducidos ({clave de KXL o KFI: texto}) y el
    Excel; escribir() la graba.
    """

    __slots__ = ["__datos", "__excel", "__ruta", "__textos"]

    #
    def __init__(self, ruta: Path, textos: dict[str, str],
                 excel: Excel) -> None:

        # --- Variables de instancia
        self.__ruta: Path = ruta
        self.__textos: dict[str, str] = textos
        self.__excel: Excel = excel
        self.__datos = excel.review

    #
    # --- Métodos públicos
    #
    # region Métodos públicos

    #
    def escribir(self) -> None:
        """
        Escribe las dos páginas: la latitud y las gráficas; las
        recomendaciones, el ruido y los balances.
        """
        k = self.__excel.valores_constantes()
        puntos = self.__excel.puntos_curva(k)
        estilo = {"font.family": KFI.FUENTE, "font.size": KFI.LETRA,
                  "axes.edgecolor": KFI.EJES, "axes.labelcolor": KFI.GRIS,
                  "xtick.color": KFI.GRIS, "ytick.color": KFI.GRIS}
        # --- type: ignore: rc_context pide sus propios nombres de clave
        #     (RcKeyType); un diccionario de cadenas funciona igual
        with (matplotlib.rc_context(estilo),                 # type: ignore
              PdfPages(self.__ruta) as pdf):
            pdf.savefig(self.pagina_curva(k, puntos))
            pdf.savefig(self.pagina_datos(k, puntos))

    #
    def pagina_curva(self, k: dict, puntos: list[PuntoCurva]) -> Figure:
        """
        Página 1: la latitud de texturas (escala de zonas en su gris, con
        los tramos apreciable y recomendado, y las dos cifras) y las
        gráficas de la curva tonal y de la diferencia en L*.
        """
        t = self.__textos
        fig = self.pagina(1)
        limites = self.__excel.limites_texturas(k, self.__excel.texturas(k))
        self.apartado(fig, KFI.APARTADO_LATITUD, t[KXL.T_TEXTURAS])
        sin_tela = not isinstance(self.__datos.tela, Ventana)
        self.nota(fig, KFI.APARTADO_LATITUD - KFI.A_LA_NOTA,
                  t[KXL.T_SIN_TELA] if sin_tela
                  else t[KFI.T_NOTA_TEXTURAS_FICHA])
        self.escala(fig, k, puntos, None if sin_tela else limites)
        for i, (clave, valores) in enumerate(limites.items()):
            self.cifra(fig, KFI.IZQUIERDA + (i * KFI.CIFRAS_PASO), k,
                       t[clave], valores)
        self.apartado(fig, KFI.APARTADO_CURVA,
                      self.titulo_graf(KXL.T_G_CURVA))
        self.graf_curva(fig, k, puntos)
        self.apartado(fig, KFI.APARTADO_DIFERENCIA,
                      self.titulo_graf(KXL.T_G_DIFERENCIA))
        self.graf_diferencia(fig, k, puntos)
        return fig

    #
    def pagina_datos(self, k: dict, puntos: list[PuntoCurva]) -> Figure:
        """
        Página 2: recomendaciones para la curva del revelador (las zonas
        enteras: L* objetivo y del revelador, entrada y salida), ruido de
        lectura y negro, y balances de blancos (sin tomas de balance, lo
        dice).
        """
        t, d = self.__textos, self.__datos
        fig = self.pagina(2)
        y = KFI.APARTADO_RECOMENDACIONES
        self.apartado(fig, y, t[KXL.T_RECOMENDACIONES])
        fin = self.nota(fig, y - KFI.A_LA_NOTA,
                        t[KFI.T_NOTA_RECOMENDACIONES])
        enteras = [p for p in puntos
                   if (p.tercio_ev % k[KXL.C_TERCIO_POR_ZONA]) == 0]
        filas = [(p.nombre, self.numero(p.objetivo, 1),
                  self.numero(p.revelador, 1), self.numero(p.entrada, 0),
                  self.numero(p.salida, 0)) for p in enteras]
        y = self.tabla(fig, self.bajo_nota(y, fin), tuple(t[c] for c in (
            KXL.T_CAB_ZONA, KXL.T_CAB_L_OBJETIVO, KXL.T_CAB_L_REVELADOR,
            KXL.T_CAB_ENTRADA, KXL.T_CAB_SALIDA)), filas,
            KFI.ANCHOS_RECOMENDACIONES)
        if all(p.revelador is None for p in enteras):
            y = self.nota(fig, y - KFI.TABLA_A_NOTA, t[KFI.T_SIN_FASE_2])

        # --- Ruido de lectura y negro
        y -= KFI.ENTRE_APARTADOS
        self.apartado(fig, y, t[KXL.T_RUIDO_NEGRO])
        y = self.tabla(fig, y - KFI.A_LA_TABLA_SIN_NOTA, ("",) + tuple(
            t[c] for c in KXL.T_CANALES), [
            (t[KFI.T_RUIDO_FICHA],) + self.canales(d.ruidoRGB, 2),
            (t[KFI.T_NEGRO_FICHA],) + self.canales(d.negroRGB, 0)],
            KFI.ANCHOS_RUIDO)

        # --- Balances de blancos
        y -= KFI.ENTRE_APARTADOS
        self.apartado(fig, y, t[KXL.T_BALANCES])
        if not d.balancesDistintos:
            self.nota(fig, y - KFI.A_LA_NOTA, t[KXL.T_SIN_BALANCES])
            return fig
        fin = self.nota(fig, y - KFI.A_LA_NOTA, t[KXL.T_NOTA_BALANCES])
        self.tabla(fig, self.bajo_nota(y, fin), tuple(t[c] for c in (
            KXL.T_CAB_BALANCE, KXL.T_CAB_KELVIN_ANOTADO,
            KXL.T_CAB_KELVIN_MEDIDO)), [
            (self.__excel.nombre_balance(b.nombre),
             self.numero(b.kelvin_cam, 0), self.numero(b.kelvin, 0))
            for b in d.balancesDistintos], KFI.ANCHOS_BALANCES)
        return fig

    # endregion Métodos públicos

    #
    # --- Piezas de las páginas
    #
    # region Piezas

    #
    def pagina(self, numero: int) -> Figure:
        """
        Página nueva con su cabecera (cámara, fecha, bits y exposición de
        la Z-V, sobre una banda verde) y su pie (con su número).
        """
        t, d = self.__textos, self.__datos
        fig = Figure(figsize=KFI.PAGINA)
        fig.patches.append(Rectangle(
            (0, KFI.BANDA_ABAJO), 1, 1 - KFI.BANDA_ABAJO,
            transform=fig.transFigure, color=KFI.VERDE, zorder=0))
        fig.text(KFI.IZQUIERDA, KFI.TITULO_Y,
                 t[KFI.T_TITULO_FICHA].format(cam=d.cam),
                 fontsize=KFI.LETRA_TITULO, weight="bold", color="white",
                 va="center")
        fecha = (datetime.fromisoformat(d.fecha).strftime(
            t[KFI.T_FORMATO_FECHA_FICHA]) if d.fecha else KFI.SIN_DATO)
        exp = (OECF.TextoExp(d.f, d.tv, d.iso, tuple(
            t[c] for c in KXL.ROTULOS_EXP)) or KFI.SIN_DATO)
        fig.text(KFI.IZQUIERDA, KFI.SUBTITULO_Y,
                 t[KFI.T_SUBTITULO_FICHA].format(
                     fecha=fecha, bits=d.bits or KFI.SIN_DATO,
                     exp=exp),
                 fontsize=KFI.LETRA_SUBTITULO, color="white", va="center")
        fig.text(KFI.IZQUIERDA, KFI.PIE_Y, t[KFI.T_PIE_FICHA],
                 fontsize=KFI.LETRA_PIE, color=KFI.GRIS)
        fig.text(KFI.DERECHA, KFI.PIE_Y, t[KFI.T_PAGINA].format(
            pagina=numero, paginas=KFI.PAGINAS), fontsize=KFI.LETRA_PIE,
            color=KFI.GRIS, ha="right")
        return fig

    #
    def apartado(self, fig: Figure, y: float, texto: str) -> None:
        """ Título de una sección, en verde, con una raya debajo. """
        fig.text(KFI.IZQUIERDA, y, texto, fontsize=KFI.LETRA_APARTADO,
                 weight="bold", color=KFI.VERDE)
        raya = y - KFI.SUBRAYA
        fig.lines.append(Line2D([KFI.IZQUIERDA, KFI.DERECHA], [raya, raya],
                                transform=fig.transFigure, color=KFI.BORDE,
                                linewidth=1))

    #
    def nota(self, fig: Figure, y: float, texto: str) -> float:
        """
        Nota en gris, desde y (lo alto de su primera línea) hacia abajo,
        partida en líneas que no pasan de la raya de las secciones (de
        KFI.IZQUIERDA a KFI.DERECHA). Devuelve dónde acaba.
        """
        nota = fig.text(KFI.IZQUIERDA, y, "\n".join(self.partir(
            fig, texto, KFI.LETRA_NOTA)), fontsize=KFI.LETRA_NOTA,
            color=KFI.GRIS, va="top")
        return self.caja(fig, nota).y0

    #
    def partir(self, fig: Figure, texto: str, letra: float) -> list[str]:
        """
        Líneas de un texto, palabra a palabra, sin pasar del ancho entre
        márgenes con ese tamaño de letra (lo mide como lo dibujará).
        """
        ancho = KFI.DERECHA - KFI.IZQUIERDA
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
        return min(y - KFI.A_LA_TABLA, fin - KFI.NOTA_A_TABLA)

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
        ax = fig.add_axes(KFI.ESCALA)
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
                KFI.ALTO_ZONA if entera else KFI.ALTO_TERCIO,
                facecolor=(gris,) * 3, edgecolor=KFI.MARCO_TIRA,
                linewidth=KFI.LINEA_TIRA))
            ax.plot([zona, zona],
                    [0, -(KFI.DIENTE_ZONA if entera else KFI.DIENTE_TERCIO)],
                    color=KFI.TINTA if entera else KFI.GRIS,
                    linewidth=KFI.LINEA_DIENTE)
            if not entera:
                continue
            zv = (p.tercio_ev == 0)
            ax.text(zona, KFI.NOMBRES_Y, p.nombre, ha="center", va="center",
                    color="white" if zv else KFI.TINTA,
                    weight="bold" if zv else "normal",
                    bbox=({"boxstyle": KFI.MARCO_ZV, "facecolor": KFI.TINTA,
                           "edgecolor": "none"} if zv else None))
        if limites is not None:
            for clave, (alto, grueso), color in (
                    (KXL.T_APRECIABLE, KFI.TRAMO_APRECIABLE, KFI.VERDE),
                    (KXL.T_RECOMENDADA, KFI.TRAMO_RECOMENDADO,
                     KFI.VERDE_OSCURO)):
                sombra, luz, _ = limites[clave]
                if not (isinstance(sombra, float) and isinstance(luz, float)):
                    continue
                ax.plot([sombra, luz], [alto, alto], color=color,
                        linewidth=grueso, solid_capstyle="butt")
                for x in (sombra, luz):
                    ax.plot([x, x], [alto - KFI.PATA_TRAMO,
                                     alto + KFI.PATA_TRAMO], color=color,
                            linewidth=KFI.LINEA)
                ax.text(izquierda, alto, t[clave], ha="left", va="center",
                        fontsize=KFI.LETRA_NOTA, color=color)
        # --- De Z0 a ZX (la ZV está en medio), justo lo que ocupa la tira
        ax.set_xlim(izquierda, derecha)
        ax.set_ylim(*KFI.ESCALA_Y)
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
            (x, KFI.CIFRAS_Y), KFI.CIFRAS_ANCHO, KFI.CIFRAS_ALTO,
            transform=fig.transFigure,
            boxstyle=f"round,pad=0,rounding_size={KFI.CIFRAS_REDONDEO}",
            facecolor=KFI.VERDE_CLARO, edgecolor=KFI.BORDE, linewidth=0.8))
        arriba = KFI.CIFRAS_Y + KFI.CIFRAS_ALTO
        fig.text(x + KFI.CIFRAS_MARGEN, arriba - KFI.CIFRAS_MARGEN, rotulo,
                 color=KFI.GRIS)
        cifra = (t[KFI.T_CIFRA_ZONAS].format(
            zonas=self.__excel.tercios_texto(ancho))
            if isinstance(ancho, float) else ancho)
        fig.text(x + KFI.CIFRAS_MARGEN, KFI.CIFRAS_Y + KFI.CIFRAS_NUMERO_Y,
                 cifra, fontsize=KFI.LETRA_CIFRA, weight="bold",
                 color=KFI.TINTA)
        if isinstance(sombra, float) and isinstance(luz, float):
            fig.text((x + KFI.CIFRAS_ANCHO) - KFI.CIFRAS_MARGEN,
                     KFI.CIFRAS_Y + KFI.CIFRAS_DESDE_Y,
                     t[KFI.T_DESDE_HASTA].format(
                         desde=self.nombre(sombra, k),
                         hasta=self.nombre(luz, k)),
                     fontsize=KFI.LETRA_SUBTITULO, color=KFI.GRIS,
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
        ax = fig.add_axes(KFI.GRAF_CURVA)
        x = self.zonas(puntos, k)
        ax.plot(x, [p.esperado for p in puntos], color=KXL.COLOR_ESPERADO,
                linewidth=KFI.LINEA_ESPERADO, alpha=KFI.OPACIDAD_ESPERADO,
                solid_capstyle="butt", label=t[KXL.T_CAB_ESPERADO],
                zorder=1)
        ax.plot(x, [p.objetivo for p in puntos], color=KXL.COLOR_OBJETIVO,
                linewidth=KFI.LINEA_OBJETIVO, linestyle="--",
                label=t[KXL.T_CAB_L_OBJETIVO], zorder=2)
        if any(p.revelador is not None for p in puntos):
            ax.plot(x, [math.nan if (p.revelador is None) else p.revelador
                        for p in puntos], color=KFI.REVELADOR,
                    linewidth=KFI.LINEA, marker="o", markersize=KFI.PUNTO,
                    label=t[KXL.T_S_REVELADOR], zorder=3)
        ax.plot(x, [math.nan if (p.sensor is None) else p.sensor
                    for p in puntos], color=KXL.COLOR_SENSOR,
                linewidth=KFI.LINEA, label=t[KXL.T_S_SENSOR], zorder=4)
        self.ejes(ax, k, t[KXL.T_EJE_LSTAR])
        ax.set_ylim(*KXL.EJE_LSTAR[:2])
        ax.legend(loc="upper left", frameon=False, fontsize=KFI.LETRA_NOTA)

    #
    def graf_diferencia(self, fig: Figure, k: dict,
                        puntos: list[PuntoCurva]) -> None:
        """
        Diferencia en L* del revelador con el objetivo: cuánto se separa
        el revelado de la escala que se busca, lo que el estudiante
        corrige (el signo se lee en el eje); sin dato, hueco. La leyenda,
        encima, fuera de las barras. Sin revelador, lo dice.
        """
        t = self.__textos
        ax = fig.add_axes(KFI.GRAF_DIFERENCIA)
        ax.axhline(0, color=KFI.CERO, linewidth=0.8)
        self.ejes(ax, k, t[KXL.T_EJE_DIF_LSTAR])
        if all(p.revelador is None for p in puntos):
            ax.text(0.5, 0.5, t[KFI.T_SIN_FASE_2], transform=ax.transAxes,
                    ha="center", va="center", color=KFI.GRIS,
                    fontsize=KFI.LETRA_NOTA)
            return
        ax.bar(self.zonas(puntos, k),
               [math.nan if (p.revelador is None)
                else (p.revelador - p.objetivo) for p in puntos],
               width=KFI.BARRA, color=KFI.REVELADOR,
               label=t[KXL.T_S_REVELADOR])
        ax.legend(loc="lower right", bbox_to_anchor=(1, 1),
                  frameon=False, fontsize=KFI.LETRA_NOTA)

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
        ax.grid(axis="y", color=KFI.REJILLA, linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)

    #
    def tabla(self, fig: Figure, y: float, cabeceras: tuple[str, ...],
              filas: list[tuple], anchos: tuple[float, ...]) -> float:
        """
        Tabla como las del libro (cabecera verde, filas alternas), a todo
        el ancho, desde y hacia abajo. Devuelve dónde acaba.
        """
        ancho = KFI.DERECHA - KFI.IZQUIERDA
        total = sum(anchos)
        bordes = [KFI.IZQUIERDA]
        for a in anchos:
            bordes.append(bordes[-1] + ((ancho * a) / total))
        alto = KFI.ALTO_FILA
        for f, fila in enumerate([cabeceras] + list(filas)):
            abajo = y - (alto * (f + 1))
            cabecera = (f == 0)
            fondo = (KFI.VERDE if cabecera
                     else (KFI.VERDE_CLARO if (f % 2) else "white"))
            for i, texto in enumerate(fila):
                fig.patches.append(Rectangle(
                    (bordes[i], abajo), bordes[i + 1] - bordes[i], alto,
                    transform=fig.transFigure, facecolor=fondo,
                    edgecolor="white" if cabecera else KFI.BORDE,
                    linewidth=0.5))
                fig.text((bordes[i] + bordes[i + 1]) / 2, abajo + (alto / 2),
                         str(texto).replace("\n", " "),
                         color="white" if cabecera else KFI.TINTA,
                         weight="bold" if cabecera else "normal",
                         fontsize=KFI.LETRA_NOTA, ha="center", va="center")
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
    def numero(self, valor: float | int | None, decimales: int) -> str:
        """
        Número con el separador decimal del idioma; sin él (o no finito),
        una raya.
        """
        if (valor is None) or (not math.isfinite(valor)):
            return KFI.SIN_DATO
        texto = f"{valor:.{decimales}f}"
        return texto.replace(".", self.__textos[KFI.T_SEPARADOR_DECIMAL])

    #
    def marca_eje(self, valor: float, _pos: int) -> str:
        """ Marca de un eje: sin decimales si es entera. """
        return self.numero(valor, 0 if float(valor).is_integer() else 1)

    #
    def canales(self, valores: tuple | None, decimales: int) -> tuple:
        """ Rojo, verde y azul como texto (sin ellos, rayas). """
        if not valores:
            return (KFI.SIN_DATO,) * KXL.CANALES
        return tuple(self.numero(v, decimales) for v in valores)

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
