# -*- coding: utf-8 *-*
"""
    :Propósito: TEMPORAL. Rejilla de la serie por zonas y tercios (pieza 2):
                qué posiciones tienen foto y cuáles no. Cuenta y dibujo en
                el mismo módulo hasta decidir la estructura
    :Autor:     Tony Diana
    :Versión:   26.10.06
"""

# cSpell:ignore customtkinter, idents
# --- Valenciano
# cSpell:ignore anàlisi, buit, corba, esperaven, graella, posicions, preses
# cSpell:ignore Sèrie, Balanços, canvi, costat, costats, esperava, Només
# cSpell:ignore principi, seqüència, Seqüència, Sobren, tapades, trencada
# cSpell:ignore enllà, esperat, teòriques

__all__ = ["Rejilla"]

# --- Bibliotecas estándar Python
import re
import tkinter as tk
from pathlib import Path

# --- Bibliotecas externas
import customtkinter as ctk

# --- Bibliotecas internas
from bib import biboecf, std
from ..constantes import K


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
        posiciones = 31

        # --- Cabeceras de columna y de fila
        cabeceras = ("0", "1", "2", "3", "4", "V", "6", "7", "8", "9", "X")
        filas = ("+0", "+1/3", "+2/3")

        # --- Z-V de anclaje esperadas en la celda ZV (iniciales y de
        #     cambio de lado) y tomas tapadas esperadas: las del protocolo
        anclas = biboecf.KS.iniciales + biboecf.KS.cambios
        tapadas = biboecf.KS.tapadas

        # --- Hueco de ZX 2/3 (no existe): ahí va el botón de incidencias
        pos_boton = (zonas - 1, tercios - 1)

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
        txt_contador = {K.es: "{n} de {total} posiciones",
                        K.en: "{n} of {total} positions",
                        K.ca: "{n} de {total} posicions"}
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
        txt_completa = {K.es: "Serie completa en las {total} posiciones.",
                        K.en: "Series complete in all {total} positions.",
                        K.ca: "Sèrie completa en les {total} posicions."}
        txt_hueco = {K.es: "El análisis continúa, con un hueco en la curva.",
                     K.en: "The analysis goes on, with a gap in the curve.",
                     K.ca: "L'anàlisi continua, amb un buit en la corba."}

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

        # --- Secuencia de tomas (ver biboecf.secuencia)
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

        # --- Identificador corto: número final del nombre del archivo
        patron_ident = r"(\d+)$"

    #
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, highlightthickness=0,
                         height=self._alto())
        self.celdas: dict[tuple[int, int], list[str]] = {}
        self.boton: tk.Misc | None = None
        self.bind("<Configure>", lambda _: self.dibujar())

    #
    # --- Cuenta (función pura)
    #

    # --- Reparte las tomas en celdas {(zona, tercio): [identificadores]}
    #     y devuelve también las que caen fuera. ks: k de cada archivo
    #     (None si no se pudo leer)
    @classmethod
    def repartir(cls, archivos: list[Path], ks: list[int | None]
                 ) -> tuple[dict[tuple[int, int], list[str]], list[str]]:
        celdas: dict[tuple[int, int], list[str]] = {}
        fuera = []
        for archivo, k in zip(archivos, ks):
            ident = cls.ident(archivo, archivos)
            if k is None or abs(k) > cls.KR.tercios_lado:
                fuera.append(ident)
                continue
            posicion = divmod(cls.KR.tercios_lado + k, cls.KR.tercios)
            celdas.setdefault(posicion, []).append(ident)
        return celdas, fuera

    # --- Archivos y k sin las tomas que no van a la rejilla (tapadas y
    #     balances de cámara): quitar dice cuáles
    @staticmethod
    def sin(archivos: list[Path], ks: list[int | None],
            quitar: list[bool]) -> tuple[list[Path], list[int | None]]:
        quedan = [(a, k) for a, k, q in zip(archivos, ks, quitar) if not q]
        return [a for a, _ in quedan], [k for _, k in quedan]

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

    # --- Nombre de la zona de una posición: Z8 1/3
    @classmethod
    def nombre(cls, posicion: tuple[int, int]) -> str:
        zona, tercio = posicion
        return biboecf.texto_zona(zona * cls.KR.tercios + tercio
                                  - cls.KR.tercios_lado)

    # --- Posiciones sin ninguna toma
    @classmethod
    def vacias(cls, celdas: dict[tuple[int, int], list[str]]
               ) -> list[tuple[int, int]]:
        return [p for p in cls.posiciones() if not celdas.get(p)]

    # --- Líneas de debajo de la rejilla: contador y conclusión
    @classmethod
    def resumen(cls, celdas: dict[tuple[int, int], list[str]]) -> list[str]:
        vacias = cls.vacias(celdas)
        conclusion = cls.KR.txt_hueco if vacias else cls.KR.txt_completa
        return [K.tr(cls.KR.txt_contador).format(
                    n=cls.KR.posiciones - len(vacias),
                    total=cls.KR.posiciones),
                K.tr(conclusion).format(total=cls.KR.posiciones)]

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
    def incidencias(cls, celdas: dict[tuple[int, int], list[str]],
                    fuera: list[str], balance: bool | None,
                    tapadas: int, sec: biboecf.Secuencia,
                    archivos: list[Path]) -> list[str]:
        incidencias = []
        if balance is False:
            incidencias.append(K.tr(cls.KR.txt_sin_balance))
        incidencias += cls.incidencias_secuencia(sec, archivos)
        if tapadas != cls.KR.tapadas:
            incidencias.append(K.tr_n(cls.KR.txt_tapadas_mal, tapadas).format(
                n=tapadas, esperadas=cls.KR.tapadas))
        if not sec.balances:
            incidencias.append(K.tr(cls.KR.txt_sin_balances))

        incidencias += [K.tr(cls.KR.txt_sin_toma).format(zona=cls.nombre(p))
                        for p in cls.vacias(celdas)]

        # --- Repetidas (fuera de ZV)
        incidencias += [K.tr(cls.KR.txt_repetida).format(
            n=len(celdas[p]), zona=cls.nombre(p))
            for p in cls.posiciones() if p != cls.pos_zv()
            and len(celdas.get(p, [])) > 1]

        if fuera:
            incidencias.append(K.tr_n(cls.KR.txt_fuera, len(fuera)).format(
                n=len(fuera)))
        return incidencias

    # --- Incidencias de la secuencia de tomas, en su orden. archivos: los
    #     de la serie, en el orden en que se analizó
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
            real=biboecf.texto_zona(k)) for i, esperado, k in sec.saltos]

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

    # --- Muestra unas celdas nuevas
    def mostrar(self, celdas: dict[tuple[int, int], list[str]]) -> None:
        self.celdas = celdas
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

        # --- Celdas: las que no existen (X +1/3 y X +2/3) no se dibujan
        for posicion in self.posiciones():
            zona, tercio = posicion
            x = kr.ancho_etiquetas + zona * paso_x
            y = kr.alto_cabecera + tercio * paso_y
            self._celda(posicion, x, y, ancho)

        # --- Botón (si lo hay) en su hueco, del tamaño de una celda.
        #     delete("all") lo quita del Canvas: se vuelve a colocar
        if self.boton is not None:
            zona, tercio = kr.pos_boton
            self.boton.configure(width=ancho, height=kr.celda)
            self.create_window(kr.ancho_etiquetas + zona * paso_x,
                               kr.alto_cabecera + tercio * paso_y,
                               window=self.boton, anchor="nw")

    # --- Coloca un botón en el hueco de ZX 2/3. Tiene que ser hijo de
    #     la rejilla (Tk no deja meter en un Canvas widgets de otro sitio)
    def poner_boton(self, boton: tk.Misc) -> None:
        self.boton = boton
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
