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
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import FuncFormatter

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
    #     las dos gráficas: (izquierda, abajo, ancho, alto)
    APARTADO_LATITUD = 0.875
    SUBRAYA = 0.008
    ESCALA = (0.06, 0.725, 0.88, 0.1)
    CIFRAS_Y = 0.62
    CIFRAS_ALTO = 0.085
    CIFRAS_ANCHO = 0.43
    CIFRAS_PASO = 0.45
    APARTADO_CURVA = 0.585
    GRAF_CURVA = (0.1, 0.33, 0.84, 0.225)
    APARTADO_DIFERENCIA = 0.275
    GRAF_DIFERENCIA = (0.1, 0.06, 0.84, 0.185)

    # --- Escala de zonas: alto de los tramos (apreciable, recomendado) y
    #     su grosor, y dónde van los nombres de las zonas
    TRAMO_APRECIABLE = (1.45, 2.5)
    TRAMO_RECOMENDADO = (1.2, 4)
    PATA_TRAMO = 0.1
    NOMBRES_Y = -0.35
    ESCALA_Y = (-0.6, 1.65)

    # --- Página 2: secciones y tablas (alto de fila; separación entre
    #     secciones; de la sección a su nota y a su tabla)
    APARTADO_RECOMENDACIONES = 0.875
    ALTO_FILA = 0.021
    ENTRE_APARTADOS = 0.04
    A_LA_NOTA = 0.03
    A_LA_TABLA = 0.05
    ANCHOS_RECOMENDACIONES = (1, 1.3, 1.3, 1, 1)
    ANCHOS_RUIDO = (2.4, 1, 1, 1)
    ANCHOS_BALANCES = (1.6, 1, 1)

    # --- Gráficas: grosor de las líneas, tamaño de los puntos y ancho de
    #     las barras (en zonas)
    LINEA = 1.5
    LINEA_OBJETIVO = 1.2
    PUNTO = 3.5
    BARRA = 0.13

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
        enteras: L* esperado y del revelador, entrada y salida), ruido de
        lectura y negro, y balances de blancos (sin tomas de balance, lo
        dice).
        """
        t, d = self.__textos, self.__datos
        fig = self.pagina(2)
        y = KFI.APARTADO_RECOMENDACIONES
        self.apartado(fig, y, t[KXL.T_RECOMENDACIONES])
        self.nota(fig, y - KFI.A_LA_NOTA, t[KFI.T_NOTA_RECOMENDACIONES])
        enteras = [p for p in puntos
                   if (p.tercio_ev % k[KXL.C_TERCIO_POR_ZONA]) == 0]
        filas = [(p.nombre, self.numero(p.esperado, 1),
                  self.numero(p.revelador, 1), self.numero(p.entrada, 0),
                  self.numero(p.salida, 0)) for p in enteras]
        y = self.tabla(fig, y - KFI.A_LA_TABLA, tuple(t[c] for c in (
            KXL.T_CAB_ZONA, KXL.T_CAB_L_ESPERADO, KXL.T_CAB_L_REVELADOR,
            KXL.T_CAB_ENTRADA, KXL.T_CAB_SALIDA)), filas,
            KFI.ANCHOS_RECOMENDACIONES)
        if all(p.revelador is None for p in enteras):
            self.nota(fig, y - KFI.A_LA_NOTA, t[KFI.T_SIN_FASE_2])
            y -= KFI.A_LA_NOTA

        # --- Ruido de lectura y negro
        y -= KFI.ENTRE_APARTADOS
        self.apartado(fig, y, t[KXL.T_RUIDO_NEGRO])
        y = self.tabla(fig, y - KFI.A_LA_NOTA, ("",) + tuple(
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
        self.nota(fig, y - KFI.A_LA_NOTA, t[KXL.T_NOTA_BALANCES])
        self.tabla(fig, y - KFI.A_LA_TABLA, tuple(t[c] for c in (
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
        exp = " · ".join((
            f"{t[KXL.T_ISO]} {OECF.TextoISO(d.iso)}" if d.iso else "",
            OECF.TextoTV(d.tv) if d.tv else "",
            f"{t[KXL.T_F]}{OECF.TextoF(d.f)}" if d.f else ""))
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
    def nota(self, fig: Figure, y: float, texto: str) -> None:
        """ Nota en gris bajo una sección. """
        fig.text(KFI.IZQUIERDA, y, texto, fontsize=KFI.LETRA_NOTA,
                 color=KFI.GRIS, wrap=True)

    #
    def escala(self, fig: Figure, k: dict, puntos: list[PuntoCurva],
               limites: dict | None) -> None:
        """
        Escala de las zonas enteras, cada una en su gris (el de su L*
        esperado en sRGB, con un borde para que el blanco se vea) y, con
        paño, los tramos de la latitud apreciable y recomendada.
        """
        t = self.__textos
        ax = fig.add_axes(KFI.ESCALA)
        zona_zv = k[KXL.C_ZONA_ZV]
        for p in puntos:
            if p.tercio_ev % k[KXL.C_TERCIO_POR_ZONA]:
                continue
            zona = zona_zv + (p.tercio_ev / k[KXL.C_TERCIO_POR_ZONA])
            gris = self.__excel.curva(p.luz_esperada, k) / k[
                KXL.C_ESCALA_CURVA]
            ax.add_patch(Rectangle((zona - 0.5, 0), 1, 1,
                                   facecolor=(gris,) * 3,
                                   edgecolor=KFI.BORDE, linewidth=0.5))
            ax.text(zona, KFI.NOMBRES_Y, p.nombre, ha="center", va="center",
                    color=KFI.TINTA)
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
                ax.text(-0.45, alto, t[clave], ha="left", va="center",
                        fontsize=KFI.LETRA_NOTA, color=color)
        # --- De Z0 a ZX: la ZV está en medio
        ax.set_xlim(-0.5, (2 * zona_zv) + 0.5)
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
            boxstyle="round,pad=0,rounding_size=0.008",
            facecolor=KFI.VERDE_CLARO, edgecolor=KFI.BORDE, linewidth=0.8))
        arriba = KFI.CIFRAS_Y + KFI.CIFRAS_ALTO
        fig.text(x + 0.02, arriba - 0.02, rotulo, color=KFI.GRIS)
        cifra = (t[KFI.T_CIFRA_ZONAS].format(
            zonas=self.__excel.tercios_texto(ancho))
            if isinstance(ancho, float) else ancho)
        fig.text(x + 0.02, KFI.CIFRAS_Y + 0.025, cifra,
                 fontsize=KFI.LETRA_CIFRA, weight="bold", color=KFI.TINTA)
        if isinstance(sombra, float) and isinstance(luz, float):
            fig.text(x + KFI.CIFRAS_ANCHO - 0.02, KFI.CIFRAS_Y + 0.028,
                     t[KFI.T_DESDE_HASTA].format(
                         desde=self.nombre(sombra, k),
                         hasta=self.nombre(luz, k)),
                     fontsize=KFI.LETRA_SUBTITULO, color=KFI.GRIS,
                     ha="right", va="center")

    #
    def graf_curva(self, fig: Figure, k: dict,
                   puntos: list[PuntoCurva]) -> None:
        """
        Curva tonal en L*: esperado (gris grueso, detrás), objetivo
        (discontinuo), sensor (delante, para que se vea aunque coincida
        con el esperado) y revelador (si lo hay).
        """
        t = self.__textos
        ax = fig.add_axes(KFI.GRAF_CURVA)
        x = self.zonas(puntos, k)
        ax.plot(x, [p.esperado for p in puntos], color=KXL.COLOR_ESPERADO,
                linewidth=KXL.ANCHO_ESPERADO + 1,
                alpha=KXL.TRANSPARENCIA_ESPERADO / KXL.CIEN,
                label=t[KXL.T_CAB_ESPERADO], zorder=1)
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
        Diferencia en L* (menos el esperado): barras del sensor y, si lo
        hay, del revelador, cada serie siempre en su color (el signo se
        lee en el eje); sin dato, hueco. La leyenda, encima, fuera de las
        barras.
        """
        t = self.__textos
        ax = fig.add_axes(KFI.GRAF_DIFERENCIA)
        x = self.zonas(puntos, k)
        hay_revelador = any(p.revelador is not None for p in puntos)
        desplaza = (KFI.BARRA / 2) if hay_revelador else 0
        ax.bar([v - desplaza for v in x],
               [math.nan if (p.sensor is None) else (p.sensor - p.esperado)
                for p in puntos], width=KFI.BARRA, color=KXL.COLOR_SENSOR,
               label=t[KXL.T_S_SENSOR])
        if hay_revelador:
            ax.bar([v + desplaza for v in x],
                   [math.nan if (p.revelador is None)
                    else (p.revelador - p.esperado) for p in puntos],
                   width=KFI.BARRA, color=KFI.REVELADOR,
                   label=t[KXL.T_S_REVELADOR])
        ax.axhline(0, color=KFI.CERO, linewidth=0.8)
        self.ejes(ax, k, t[KXL.T_EJE_DIF_LSTAR])
        ax.legend(loc="lower right", bbox_to_anchor=(1, 1), ncol=2,
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
