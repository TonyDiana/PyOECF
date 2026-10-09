# -*- coding: utf-8 *-*
"""
    :Propósito: Rejilla de la serie por zonas y tercios: qué posiciones
                tienen foto y cuáles no, con su resumen, sus incidencias y
                los botones de su pie
    :Autor:     Tony Diana
    :Versión:   26.10.09
"""

# cSpell:ignore analisis, biboecf, customtkinter, exito, idents

# --- Valenciano
# cSpell:ignore Balanços, canvi, costat, costats, enllà, esperat, esperava
# cSpell:ignore esperaven, Falten, graella, Només, posició, posicions, preses
# cSpell:ignore principi, seqüència, Seqüència, Sèrie, Sobren, tapades
# cSpell:ignore teòriques, trencada

__all__ = ["Rejilla"]

# --- Bibliotecas estándar Python
import re
import tkinter as tk
from pathlib import Path

# --- Bibliotecas externas
import customtkinter as ctk

# --- Bibliotecas internas
from bib import biboecf, std
from .constantes import K


#
class Rejilla(tk.Canvas):
    """ Rejilla de 11 zonas × 3 tercios con el estado de cada posición. """

    # --- Constantes de la rejilla
    class KR(std.EnumMutable):
        """ Constantes de la rejilla. """

        # --- Geometría: tercios a cada lado de la ZV (los del protocolo,
        #     en biboecf), zonas y tercios
        tercios_lado = biboecf.KS.tercios_lado
        zonas = 11
        tercios = 3

        # --- Cabeceras de columna y de fila
        cabeceras = ("0", "1", "2", "3", "4", "V", "6", "7", "8", "9", "X")
        filas = ("+0", "+.3", "+.7")

        # --- Z-V de anclaje esperadas en la celda ZV (iniciales y de
        #     cambio de lado) y tomas tapadas esperadas: las del protocolo
        anclas = biboecf.KS.iniciales + biboecf.KS.cambios
        tapadas = biboecf.KS.tapadas

        # --- Pie, debajo de las celdas: un botón bajo la columna Z0, otro
        #     bajo la ZX y el resumen entre los dos, todo centrado en
        #     vertical con el resumen
        columnas_pie = (0, zonas - 1)

        # --- Medidas (píxeles): celda mínima, hueco, columna de
        #     etiquetas, alto de la fila de cabeceras y de cada línea
        celda = 44
        hueco = 4
        ancho_etiquetas = 44
        alto_cabecera = 22
        alto_linea = 13
        borde = 1
        borde_zv = 2
        guiones = (4, 3)

        # --- Fuente de los identificadores (tamaño pequeño: hasta 3 líneas)
        fuente = ("TkDefaultFont", 9)

        # --- Colores (claro, oscuro). Fondo, texto y acento salen del
        #     tema de customtkinter; éxito y aviso no existen en el tema
        exito = ("#cfe8d2", "#1f4a2a")
        texto_exito = ("#1e5a2b", "#bfe5c6")
        aviso = ("#f6e2bd", "#5a4212")
        texto_aviso = ("#8a5300", "#f0c070")

        # --- Textos {idioma: texto}
        txt_falta = {K.es: "falta", K.en: "missing",
                     K.ca: "falta"}
        txt_n_zv = {K.es: "{n} Z-V", K.en: "{n} Z-V",
                    K.ca: "{n} Z-V"}
        txt_sin_toma = {K.es: "No hay toma en {zona}.",
                        K.en: "No shot in {zona}.",
                        K.ca: "No hi ha cap presa en {zona}."}
        txt_repetida = {K.es: "Hay {n} tomas en {zona}.",
                        K.en: "There are {n} shots in {zona}.",
                        K.ca: "Hi ha {n} preses en {zona}."}
        # --- Con número: (singular, plural), ver K.tr_n
        txt_fuera = {K.es: ("Hay {n} toma más allá de las zonas teóricas.",
                            "Hay {n} tomas más allá de las zonas "
                            "teóricas."),
                     K.en: ("There is {n} shot beyond the theoretical "
                            "zones.",
                            "There are {n} shots beyond the theoretical "
                            "zones."),
                     K.ca: ("Hi ha {n} presa més enllà de les zones "
                            "teòriques.",
                            "Hi ha {n} preses més enllà de les zones "
                            "teòriques.")}
        # --- Resumen bajo la rejilla: completa, o cuántas posiciones
        #     faltan (con número: singular y plural, ver K.tr_n)
        txt_completa = {K.es: "Serie completa", K.en: "Complete series",
                        K.ca: "Sèrie completa"}
        txt_faltan = {K.es: ("Falta {n} posición", "Faltan {n} posiciones"),
                      K.en: ("{n} position missing", "{n} positions missing"),
                      K.ca: ("Falta {n} posició", "Falten {n} posicions")}

        # --- Balance de blancos personalizado inicial (toma 2): línea bajo
        #     las posiciones, con sí, no o no se sabe, e incidencia si no
        txt_balance = {K.es: "Balance de blancos personalizado: {valor}",
                       K.en: "Custom white balance: {valor}",
                       K.ca: "Balanç de blancs personalitzat: {valor}"}
        txt_si = {K.es: "sí", K.en: "yes", K.ca: "sí"}
        txt_no = {K.es: "no", K.en: "no", K.ca: "no"}
        txt_no_se = {K.es: "no se sabe", K.en: "unknown", K.ca: "no se sap"}
        txt_tapadas = {K.es: "Tomas tapadas: {n} de {esperadas}",
                       K.en: "Covered shots: {n} of {esperadas}",
                       K.ca: "Preses tapades: {n} de {esperadas}"}
        txt_tapadas_mal = {
            K.es: ("Hay {n} toma tapada; se esperaban {esperadas}.",
                   "Hay {n} tomas tapadas; se esperaban {esperadas}."),
            K.en: ("There is {n} covered shot; {esperadas} expected.",
                   "There are {n} covered shots; {esperadas} expected."),
            K.ca: ("Hi ha {n} presa tapada; se n'esperaven {esperadas}.",
                   "Hi ha {n} preses tapades; se n'esperaven {esperadas}.")}
        txt_balances = {K.es: "Balances de cámara: {n}",
                        K.en: "Camera white balances: {n}",
                        K.ca: "Balanços de càmera: {n}"}
        txt_sin_balances = {K.es: "No hay balances de cámara.",
                            K.en: "There are no camera white balances.",
                            K.ca: "No hi ha balanços de càmera."}

        # --- Secuencia de tomas (ver OECF.secuencia)
        txt_iniciales_sobran = {
            K.es: ("Sobra {n} Z-V al principio.",
                   "Sobran {n} Z-V al principio."),
            K.en: ("There is {n} extra Z-V at the start.",
                   "There are {n} extra Z-V at the start."),
            K.ca: ("Sobra {n} Z-V al principi.",
                   "Sobren {n} Z-V al principi.")}
        txt_sin_cambio = {K.es: "Falta la Z-V de cambio de lado.",
                          K.en: "The side-change Z-V is missing.",
                          K.ca: "Falta la Z-V de canvi de costat."}
        txt_cambios_sobran = {
            K.es: ("Sobra {n} Z-V en el cambio de lado.",
                   "Sobran {n} Z-V en el cambio de lado."),
            K.en: ("There is {n} extra Z-V at the side change.",
                   "There are {n} extra Z-V at the side change."),
            K.ca: ("Sobra {n} Z-V en el canvi de costat.",
                   "Sobren {n} Z-V en el canvi de costat.")}
        txt_lados = {K.es: ("Solo hay {n} lado; se esperaban {esperados}.",
                            "Solo hay {n} lados; se esperaban {esperados}."),
                     K.en: ("There is only {n} side; {esperados} expected.",
                            "There are only {n} sides; {esperados} expected."),
                     K.ca: ("Només hi ha {n} costat; se n'esperaven "
                            "{esperados}.",
                            "Només hi ha {n} costats; se n'esperaven "
                            "{esperados}.")}
        txt_salto = {K.es: "Secuencia rota en {ident}: se esperaba {esperada} "
                           "y es {real}.",
                     K.en: "Sequence broken at {ident}: {esperada} expected, "
                           "{real} found.",
                     K.ca: "Seqüència trencada en {ident}: s'esperava "
                           "{esperada} i és {real}."}
        txt_sobrantes = {
            K.es: ("Hay {n} toma fuera del orden esperado: {idents}.",
                   "Hay {n} tomas fuera del orden esperado: {idents}."),
            K.en: ("There is {n} shot out of the expected order: {idents}.",
                   "There are {n} shots out of the expected order: "
                   "{idents}."),
            K.ca: ("Hi ha {n} presa fora de l'ordre esperat: {idents}.",
                   "Hi ha {n} preses fora de l'ordre esperat: {idents}.")}

        # --- Entre los identificadores de una lista
        sep_idents = ", "
        txt_sin_balance = {
            K.es: "No se hizo el balance de blancos personalizado inicial.",
            K.en: "The initial custom white balance was not taken.",
            K.ca: "No es va fer el balanç de blancs personalitzat inicial."}
        txt_mismo_balance = {
            K.es: "Las dos primeras Z-V tienen el mismo balance de blancos: "
                  "no se hizo el personalizado.",
            K.en: "The first two Z-V have the same white balance: the "
                  "custom one was not taken.",
            K.ca: "Les dues primeres Z-V tenen el mateix balanç de blancs: "
                  "no es va fer el personalitzat."}

        # --- Identificador corto: número final del nombre del archivo
        patron_ident = r"(\d+)$"

    #
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, highlightthickness=0,
                         height=self._alto(),
                         bg=self._color(ctk.ThemeManager.theme["CTk"]
                                        ["fg_color"]))
        self.celdas: dict[tuple[int, int], list[str]] = {}

        # --- Pie: (botón izquierdo, resumen, botón derecho), o None
        self.pie: tuple[ctk.CTkButton, ctk.CTkLabel,
                        ctk.CTkButton] | None = None
        self.bind("<Configure>", lambda _: self.dibujar())

    #
    # --- Cuenta (función pura)
    #

    # --- Identificador corto: número final del nombre o, si no tiene,
    #     el orden en la serie (contando desde 1)
    @classmethod
    def ident(cls, archivo: Path, archivos: list[Path]) -> str:
        numero = re.search(cls.KR.patron_ident, archivo.stem)
        return numero.group(1) if numero else str(archivos.index(archivo) + 1)

    # --- Posición de la ZV: (zona, tercio)
    @classmethod
    def pos_zv(cls) -> tuple[int, int]:
        return divmod(cls.KR.tercios_lado, cls.KR.tercios)

    # --- Las 31 posiciones que existen, de Z0 a ZX
    @classmethod
    def posiciones(cls) -> list[tuple[int, int]]:
        return [divmod(i, cls.KR.tercios)
                for i in range(2 * cls.KR.tercios_lado + 1)]

    # --- Línea de debajo de la rejilla: «Serie completa» o cuántas
    #     posiciones faltan
    @classmethod
    def resumen(cls, OECF: biboecf.OECF) -> str:
        n = len(OECF.vacias)
        if not n:
            return K.tr(cls.KR.txt_completa)
        return K.tr_n(cls.KR.txt_faltan, n).format(n=n)

    # --- Línea del balance de blancos personalizado inicial. balance:
    #     True (se hizo), False (no) o None (no se sabe)
    @classmethod
    def linea_balance(cls, balance: bool | None) -> str:
        valor = {True: cls.KR.txt_si, False: cls.KR.txt_no,
                 None: cls.KR.txt_no_se}[balance]
        return K.tr(cls.KR.txt_balance).format(valor=K.tr(valor))

    # --- Línea de los balances de cámara: cuántos hay
    @classmethod
    def linea_balances(cls, n: int) -> str:
        return K.tr(cls.KR.txt_balances).format(n=n)

    # --- Línea de las tomas tapadas: cuántas hay de las esperadas
    @classmethod
    def linea_tapadas(cls, n: int) -> str:
        return K.tr(cls.KR.txt_tapadas).format(n=n,
                                               esperadas=cls.KR.tapadas)

    # --- Todas las incidencias, una por línea: se muestran aparte, en
    #     su propia ventana, para que la principal no crezca con ellas
    @classmethod
    def incidencias(cls, OECF: biboecf.OECF) -> list[str]:
        balance = OECF.balancePersonalizado
        sec: biboecf.Secuencia = OECF.secuencia                 # type: ignore
        tapadas = len(OECF.tapadas)
        incidencias = []

        # --- Sin balance personalizado: si las dos primeras son Z-V, es
        #     que tienen el mismo balance; si no, la 2.ª ya es de un lado
        if balance is False:
            mismo = len(sec.iniciales) >= biboecf.KS.iniciales
            incidencias.append(K.tr(cls.KR.txt_mismo_balance if mismo
                                    else cls.KR.txt_sin_balance))
        incidencias += cls.incidencias_secuencia(sec, OECF.raws)
        if tapadas != cls.KR.tapadas:
            incidencias.append(K.tr_n(cls.KR.txt_tapadas_mal, tapadas).format(
                n=tapadas, esperadas=cls.KR.tapadas))
        if not sec.balances:
            incidencias.append(K.tr(cls.KR.txt_sin_balances))

        incidencias += [K.tr(cls.KR.txt_sin_toma).format(
            zona=biboecf.texto_zona(t)) for t in OECF.vacias]

        # --- Repetidas (fuera de ZV)
        incidencias += [K.tr(cls.KR.txt_repetida).format(
            n=len(indices), zona=biboecf.texto_zona(t))
            for t, indices in OECF.repetidas.items()]

        n = len(OECF.fuera)
        if n:
            incidencias.append(K.tr_n(cls.KR.txt_fuera, n).format(n=n))
        return incidencias

    # --- Incidencias de la secuencia de tomas, en su orden. archivos: los
    #     de la serie, en el orden en que se leyó
    @classmethod
    def incidencias_secuencia(cls, sec: biboecf.Secuencia,
                              archivos: list[Path]) -> list[str]:
        ks = biboecf.KS
        incidencias = []

        sobran = len(sec.iniciales) - ks.iniciales
        if sobran > 0:
            incidencias.append(K.tr_n(cls.KR.txt_iniciales_sobran,
                                      sobran).format(n=sobran))
        if len(sec.lados) < ks.lados:
            incidencias.append(K.tr_n(cls.KR.txt_lados, len(sec.lados))
                               .format(n=len(sec.lados), esperados=ks.lados))
        elif not sec.cambios:
            incidencias.append(K.tr(cls.KR.txt_sin_cambio))
        sobran = len(sec.cambios) - ks.cambios
        if sobran > 0:
            incidencias.append(K.tr_n(cls.KR.txt_cambios_sobran,
                                      sobran).format(n=sobran))

        incidencias += [K.tr(cls.KR.txt_salto).format(
            ident=cls.ident(archivos[i], archivos),
            esperada=biboecf.texto_zona(esperado),
            real=biboecf.texto_zona(tercioEV))
            for i, esperado, tercioEV in sec.saltos]

        if sec.sobrantes:
            idents = cls.KR.sep_idents.join(
                cls.ident(archivos[i], archivos) for i in sec.sobrantes)
            incidencias.append(K.tr_n(cls.KR.txt_sobrantes,
                                      len(sec.sobrantes)).format(
                                          n=len(sec.sobrantes), idents=idents))
        return incidencias

    #
    # --- Dibujo
    #

    # --- Muestra las celdas de una serie: las posiciones de OECF, como
    #     (zona, tercio), con el identificador corto de cada toma
    def mostrar(self, OECF: biboecf.OECF) -> None:
        raws = OECF.raws
        self.celdas = {biboecf.zona_tercio(t): [self.ident(raws[i], raws)
                                               for i in indices]
                       for t, indices in OECF.celdas.items()}
        self.dibujar()

    # --- Dibuja cabeceras y celdas con el ancho actual del Canvas
    def dibujar(self) -> None:
        self.delete("all")
        self.configure(bg=self._color(ctk.ThemeManager.theme["CTk"]
                                      ["fg_color"]))
        texto = self._color(ctk.ThemeManager.theme["CTkLabel"]["text_color"])

        kr = self.KR
        ancho = max(kr.celda,
                    (self.winfo_width() - kr.ancho_etiquetas) // kr.zonas
                    - kr.hueco)
        paso_x, paso_y = ancho + kr.hueco, kr.celda + kr.hueco

        # --- Cabeceras de columna (zonas) y de fila (tercios)
        for zona, cabecera in enumerate(kr.cabeceras):
            x = kr.ancho_etiquetas + zona * paso_x + ancho / 2
            self.create_text(x, kr.alto_cabecera / 2, text=cabecera,
                             fill=texto)
        for tercio, fila in enumerate(kr.filas):
            y = kr.alto_cabecera + tercio * paso_y + kr.celda / 2
            self.create_text(kr.ancho_etiquetas / 2, y, text=fila,
                             fill=texto)

        # --- Celdas: las que no existen (X +.3 y X +.7) no se dibujan
        for posicion in self.posiciones():
            zona, tercio = posicion
            x = kr.ancho_etiquetas + zona * paso_x
            y = kr.alto_cabecera + tercio * paso_y
            self._celda(posicion, x, y, ancho)

        # --- Pie (si lo hay), bajo las celdas: los botones, como los de
        #     la ventana, alineados con el borde izquierdo de la Z0 y el
        #     derecho de la ZX, y el resumen en medio, todo centrado en
        #     vertical. Su alto es el del más alto. delete("all") lo quita
        #     del Canvas: se vuelve a colocar
        if self.pie is not None:
            izquierdo, resumen, derecho = self.pie
            fondo = self.cget("bg")
            arriba = kr.alto_cabecera + kr.tercios * paso_y + kr.hueco
            alto_pie = max(w.winfo_reqheight() for w in self.pie)
            centro_y = arriba + alto_pie / 2
            primera, ultima = kr.columnas_pie
            for w in self.pie:
                w.configure(bg_color=fondo)
            self.create_window(kr.ancho_etiquetas + primera * paso_x,
                               centro_y, window=izquierdo, anchor="w")
            self.create_window(kr.ancho_etiquetas + ultima * paso_x + ancho,
                               centro_y, window=derecho, anchor="e")
            self.create_window(
                kr.ancho_etiquetas + (kr.zonas * paso_x - kr.hueco) / 2,
                centro_y, window=resumen, anchor="center")

            # --- El Canvas crece con el pie (solo si cambia: configurar
            #     el alto lo vuelve a dibujar)
            alto = round(arriba + alto_pie)
            if int(self.cget("height")) != alto:
                self.configure(height=alto)

    # --- Coloca el pie: dos botones y el resumen entre ellos. Tienen que
    #     ser hijos de la rejilla (Tk no deja meter en un Canvas widgets
    #     de otro sitio)
    def poner_pie(self, izquierdo: ctk.CTkButton, resumen: ctk.CTkLabel,
                  derecho: ctk.CTkButton) -> None:
        self.pie = (izquierdo, resumen, derecho)
        self.dibujar()

    # --- Una celda: estado según cuántas tomas tenga
    def _celda(self, posicion: tuple[int, int], x: float, y: float,
               ancho: float) -> None:
        kr = self.KR
        idents = self.celdas.get(posicion, [])
        es_zv = posicion == self.pos_zv()
        caja = (x, y, x + ancho, y + kr.celda)

        # --- falta: borde discontinuo y texto, sin relleno (se distingue
        #     también por la forma, no solo por el color)
        if not idents:
            aviso = self._color(kr.texto_aviso)
            self.create_rectangle(*caja, outline=aviso, dash=kr.guiones,
                                  width=kr.borde)
            self.create_text(x + ancho / 2, y + kr.celda / 2, fill=aviso,
                             text=K.tr(kr.txt_falta), font=kr.fuente)
            return

        # --- repetida (fuera de ZV): relleno de aviso, identificadores
        #     apilados. ZV: borde de acento; en aviso si no son 3
        correcta = len(idents) == (kr.anclas if es_zv else 1)
        fondo = kr.exito if correcta else kr.aviso
        color = kr.texto_exito if correcta else kr.texto_aviso
        borde = (self._color(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
                 if es_zv else self._color(color))
        self.create_rectangle(*caja, fill=self._color(fondo), outline=borde,
                              width=kr.borde_zv if es_zv else kr.borde)

        # --- Más de 3 no caben: se dice cuántas hay
        lineas = idents if len(idents) <= kr.anclas else [
            K.tr(kr.txt_n_zv).format(n=len(idents))]
        arriba = y + (kr.celda - len(lineas) * kr.alto_linea) / 2
        for i, linea in enumerate(lineas):
            self.create_text(x + ancho / 2,
                             arriba + (i + 0.5) * kr.alto_linea,
                             text=linea, fill=self._color(color),
                             font=kr.fuente)

    # --- Alto total: cabecera y 3 filas de celdas
    @classmethod
    def _alto(cls) -> int:
        kr = cls.KR
        return kr.alto_cabecera + kr.tercios * (kr.celda + kr.hueco)

    # --- Color (claro, oscuro) según el modo de customtkinter
    @staticmethod
    def _color(par: tuple[str, str] | list[str]) -> str:
        return par[0] if ctk.get_appearance_mode() == "Light" else par[1]
