# -*- coding: utf-8 *-*
"""
    :Propósito: Rejilla de la serie por zonas y tercios: qué posiciones
                tienen foto y cuáles no, con su resumen, sus incidencias y
                los botones de su pie
    :Autor:     Tony Diana
    :Versión:   26.10.19
"""

# cSpell:ignore biboecf, customtkinter, devs, highlightthickness, idxs, idents
# cSpell:ignore Límpiela

# --- Valenciano
# cSpell:ignore altre, amb, analitzar, baix, Balanç, balanç, Balanços, balanços
# cSpell:ignore blancs, càmera, canvi, canvia, canviar, canvieu, centreu, convé
# cSpell:ignore costat, costats, dalt, defecte, diferent, dreta, durant, enllà
# cSpell:ignore esperat, esperava, esperaven, estes, estranys, Falten, graella
# cSpell:ignore grisa, l'esquerra, llum, l'ordre, mateix, mitjana, Moveu
# cSpell:ignore Netegeu, Només, pels, personalitzat, posició, posicions, preses
# cSpell:ignore primeres, principi, reviseu, Seqüència, seqüència, Sèrie, sèrie
# cSpell:ignore Sobren, sobretot, soroll, tapades, targeta, tenen, teòriques
# cSpell:ignore terç, terços, tessel, tindre, trencada, trobat
# cSpell:ignore anàlisi, definitives, Estes, exportació, exportacions, menys
# cSpell:ignore provar, té

__all__ = ["Rejilla"]

# --- Bibliotecas estándar Python
import re
import tkinter as tk
from pathlib import Path

# --- Bibliotecas externas
import customtkinter as ctk

# --- Bibliotecas internas
import biboecf
from bib import std
from .constantes import K


#
class Rejilla(tk.Canvas):
    """ Rejilla de 11 zonas × 3 tercios con el estado de cada posición. """

    #
    # --- Constantes de la rejilla
    class KR(std.EnumMutable):
        """ Constantes de la rejilla. """

        # --- Geometría: tercios a cada lado de la ZV (los del protocolo,
        #     en biboecf), zonas y tercios
        TERCIOS_LADO = biboecf.KS.TERCIOS_LADO
        ZONAS = (2 * biboecf.KP.ZONA_REF) + 1
        TERCIOS = biboecf.KP.TERCIOS

        # --- Cabeceras de columna y de fila
        CABECERAS = ("0", "1", "2", "3", "4", "V", "6", "7", "8", "9", "X")
        FILAS = ("+0", "+.3", "+.7")

        # --- Z-V de anclaje esperadas en la celda ZV (iniciales, de
        #     cambio de lado y final) y tomas tapadas esperadas: las del
        #     protocolo
        ANCLAS = (biboecf.KS.INICIALES + biboecf.KS.CAMBIOS
                  + biboecf.KS.FINALES)
        TAPADAS = biboecf.KS.TAPADAS

        # --- Pie, debajo de las celdas: un botón bajo la columna Z0, otro
        #     bajo la ZX y el resumen entre los dos, todo centrado en
        #     vertical con el resumen
        COLUMNAS_PIE = (0, ZONAS - 1)

        # --- Medidas (píxeles): celda mínima, hueco, columna de
        #     etiquetas, alto de la fila de cabeceras y de cada línea
        CELDA = 44
        HUECO = 4
        ANCHO_ETIQUETAS = 44
        ALTO_CABECERA = 22
        ALTO_LINEA = 13
        BORDE = 1
        BORDE_ZV = 2
        GUIONES = (4, 3)

        # --- Fuente de los identificadores (tamaño pequeño) y cuántos
        #     caben uno debajo de otro en una celda
        FUENTE = ("TkDefaultFont", 9)
        MAX_LINEAS = 3

        # --- Colores (claro, oscuro). Fondo, texto y acento salen del
        #     tema de customtkinter; éxito y aviso no existen en el tema
        OK = ("#cfe8d2", "#1f4a2a")
        TEXTO_OK = ("#1e5a2b", "#bfe5c6")
        AVISO = ("#f6e2bd", "#5a4212")
        TEXTO_AVISO = ("#8a5300", "#f0c070")

        # --- Textos {idioma: texto}
        TXT_FALTA = {K.ES: "falta", K.EN: "missing",
                     K.CA: "falta"}
        TXT_N_ZV = {K.ES: "{n} Z-V", K.EN: "{n} Z-V",
                    K.CA: "{n} Z-V"}
        TXT_SIN_TOMA = {K.ES: "No hay toma en {zona}.",
                        K.EN: "No shot in {zona}.",
                        K.CA: "No hi ha cap presa en {zona}."}
        TXT_REPETIDA = {K.ES: "Hay {n} tomas en {zona}.",
                        K.EN: "There are {n} shots in {zona}.",
                        K.CA: "Hi ha {n} preses en {zona}."}
        # --- Con número: (singular, plural), ver K.tr_n
        TXT_FUERA = {K.ES: ("Hay {n} toma más allá de las zonas teóricas: "
                            "{idents}.",
                            "Hay {n} tomas más allá de las zonas "
                            "teóricas: {idents}."),
                     K.EN: ("There is {n} shot beyond the theoretical "
                            "zones: {idents}.",
                            "There are {n} shots beyond the theoretical "
                            "zones: {idents}."),
                     K.CA: ("Hi ha {n} presa més enllà de les zones "
                            "teòriques: {idents}.",
                            "Hi ha {n} preses més enllà de les zones "
                            "teòriques: {idents}.")}
        # --- Resumen bajo la rejilla: completa, o cuántas posiciones
        #     faltan (con número: singular y plural, ver K.tr_n)
        TXT_COMPLETA = {K.ES: "Serie completa", K.EN: "Complete series",
                        K.CA: "Sèrie completa"}
        TXT_FALTAN = {K.ES: ("Falta {n} posición", "Faltan {n} posiciones"),
                      K.EN: ("{n} position missing", "{n} positions missing"),
                      K.CA: ("Falta {n} posició", "Falten {n} posicions")}

        # --- Balance de blancos personalizado inicial (toma 2): línea bajo
        #     las posiciones, con sí, no o no se sabe, e incidencia si no
        TXT_BALANCE = {K.ES: "Balance de blancos personalizado: {valor}",
                       K.EN: "Custom white balance: {valor}",
                       K.CA: "Balanç de blancs personalitzat: {valor}"}
        TXT_SI = {K.ES: "sí", K.EN: "yes", K.CA: "sí"}
        TXT_NO = {K.ES: "no", K.EN: "no", K.CA: "no"}
        TXT_NO_SE = {K.ES: "no se sabe", K.EN: "unknown", K.CA: "no se sap"}
        TXT_TAPADAS = {K.ES: "Tomas tapadas: {n} de {esperadas}",
                       K.EN: "Covered shots: {n} of {esperadas}",
                       K.CA: "Preses tapades: {n} de {esperadas}"}
        TXT_TAPADAS_MAL = {
            K.ES: ("Hay {n} toma tapada; se esperaban {esperadas}.",
                   "Hay {n} tomas tapadas; se esperaban {esperadas}."),
            K.EN: ("There is {n} covered shot; {esperadas} expected.",
                   "There are {n} covered shots; {esperadas} expected."),
            K.CA: ("Hi ha {n} presa tapada; se n'esperaven {esperadas}.",
                   "Hi ha {n} preses tapades; se n'esperaven {esperadas}.")}
        TXT_BALANCES = {K.ES: "Balances de cámara: {n}",
                        K.EN: "Camera white balances: {n}",
                        K.CA: "Balanços de càmera: {n}"}
        TXT_SIN_BALANCES = {K.ES: "No hay balances de cámara.",
                            K.EN: "There are no camera white balances.",
                            K.CA: "No hi ha balanços de càmera."}

        # --- Secuencia de tomas (ver OECF.secuencia)
        TXT_INICIALES_SOBRAN = {
            K.ES: ("Sobra {n} Z-V al principio.",
                   "Sobran {n} Z-V al principio."),
            K.EN: ("There is {n} extra Z-V at the start.",
                   "There are {n} extra Z-V at the start."),
            K.CA: ("Sobra {n} Z-V al principi.",
                   "Sobren {n} Z-V al principi.")}
        TXT_SIN_CAMBIO = {K.ES: "Falta la Z-V de cambio de lado.",
                          K.EN: "The side-change Z-V is missing.",
                          K.CA: "Falta la Z-V de canvi de costat."}
        TXT_SIN_FINAL = {K.ES: "Falta la Z-V final.",
                         K.EN: "The final Z-V is missing.",
                         K.CA: "Falta la Z-V final."}

        # --- Paso de la serie: por pasos enteros se analiza sin tercios;
        #     por medios pasos, nunca (Tony, 2026-10-19)
        TXT_PASO_ENTERO = {
            K.ES: "Serie por pasos enteros: se analiza sin tercios.",
            K.EN: "Series in full stops: it is analyzed without thirds.",
            K.CA: "Sèrie per passos sencers: s'analitza sense terços."}
        TXT_MEDIO_PASO = {
            K.ES: "Serie por medios pasos: no se puede analizar. Repítela "
                  "por tercios o por pasos enteros.",
            K.EN: "Series in half stops: it cannot be analyzed. Repeat it "
                  "in thirds or in full stops.",
            K.CA: "Sèrie per mitjos passos: no es pot analitzar. Repeteix-la "
                  "per terços o per passos sencers."}

        # --- ISO distinto del de la ZV: en la serie impide analizar; en
        #     las tapadas, solo se avisa
        TXT_ISO_DISTINTO = {
            K.ES: ("El ISO cambia en {n} toma de la serie: {idents} (se "
                   "esperaba ISO {iso}).",
                   "El ISO cambia en {n} tomas de la serie: {idents} (se "
                   "esperaba ISO {iso})."),
            K.EN: ("The ISO changes in {n} shot of the series: {idents} "
                   "(ISO {iso} expected).",
                   "The ISO changes in {n} shots of the series: {idents} "
                   "(ISO {iso} expected)."),
            K.CA: ("L'ISO canvia en {n} presa de la sèrie: {idents} "
                   "(s'esperava ISO {iso}).",
                   "L'ISO canvia en {n} preses de la sèrie: {idents} "
                   "(s'esperava ISO {iso}).")}
        TXT_TAPADAS_CON_LUZ = {
            K.ES: ("Hay {n} toma tapada que no salió negra: {idents}. Se "
                   "tapó mal y no sirve para el negro.",
                   "Hay {n} tomas tapadas que no salieron negras: {idents}. "
                   "Se taparon mal y no sirven para el negro."),
            K.EN: ("There is {n} covered shot that is not black: {idents}. "
                   "It was badly covered and is not used for the black "
                   "level.",
                   "There are {n} covered shots that are not black: "
                   "{idents}. They were badly covered and are not used for "
                   "the black level."),
            K.CA: ("Hi ha {n} presa tapada que no va sortir negra: "
                   "{idents}. Es va tapar malament i no serveix per al "
                   "negre.",
                   "Hi ha {n} preses tapades que no van sortir negres: "
                   "{idents}. Es van tapar malament i no serveixen per al "
                   "negre.")}
        TXT_ISO_TAPADAS = {
            K.ES: ("Hay {n} toma tapada con otro ISO: {idents} (se "
                   "esperaba ISO {iso}).",
                   "Hay {n} tomas tapadas con otro ISO: {idents} (se "
                   "esperaba ISO {iso})."),
            K.EN: ("There is {n} covered shot with another ISO: {idents} "
                   "(ISO {iso} expected).",
                   "There are {n} covered shots with another ISO: {idents} "
                   "(ISO {iso} expected)."),
            K.CA: ("Hi ha {n} presa tapada amb un altre ISO: {idents} "
                   "(s'esperava ISO {iso}).",
                   "Hi ha {n} preses tapades amb un altre ISO: {idents} "
                   "(s'esperava ISO {iso}).")}
        TXT_CAMBIOS_SOBRAN = {
            K.ES: ("Sobra {n} Z-V en el cambio de lado.",
                   "Sobran {n} Z-V en el cambio de lado."),
            K.EN: ("There is {n} extra Z-V at the side change.",
                   "There are {n} extra Z-V at the side change."),
            K.CA: ("Sobra {n} Z-V en el canvi de costat.",
                   "Sobren {n} Z-V en el canvi de costat.")}
        TXT_LADOS = {K.ES: ("Solo hay {n} lado; se esperaban {esperados}.",
                            "Solo hay {n} lados; se esperaban {esperados}."),
                     K.EN: ("There is only {n} side; {esperados} expected.",
                            "There are only {n} sides; {esperados} expected."),
                     K.CA: ("Només hi ha {n} costat; se n'esperaven "
                            "{esperados}.",
                            "Només hi ha {n} costats; se n'esperaven "
                            "{esperados}.")}
        TXT_SALTO = {K.ES: "Secuencia rota en {ident}: se esperaba {esperada} "
                           "y es {real}.",
                     K.EN: "Sequence broken at {ident}: {esperada} expected, "
                           "{real} found.",
                     K.CA: "Seqüència trencada en {ident}: s'esperava "
                           "{esperada} i és {real}."}
        TXT_SOBRANTES = {
            K.ES: ("Hay {n} toma fuera del orden esperado: {idents}.",
                   "Hay {n} tomas fuera del orden esperado: {idents}."),
            K.EN: ("There is {n} shot out of the expected order: {idents}.",
                   "There are {n} shots out of the expected order: "
                   "{idents}."),
            K.CA: ("Hi ha {n} presa fora de l'ordre esperat: {idents}.",
                   "Hi ha {n} preses fora de l'ordre esperat: {idents}.")}
        TXT_DESVIADAS = {
            K.ES: ("Hay {n} toma que se aparta de su tercio más de "
                   "{umbral} tercios: {idents}.",
                   "Hay {n} tomas que se apartan de su tercio más de "
                   "{umbral} tercios: {idents}."),
            K.EN: ("There is {n} shot more than {umbral} thirds away from "
                   "its third: {idents}.",
                   "There are {n} shots more than {umbral} thirds away "
                   "from their third: {idents}."),
            K.CA: ("Hi ha {n} presa que s'aparta del seu terç més de "
                   "{umbral} terços: {idents}.",
                   "Hi ha {n} preses que s'aparten del seu terç més de "
                   "{umbral} terços: {idents}.")}

        # --- Teselas de la Z-V: sin tarjeta gris (no se analiza) y las de
        #     tarjeta que rechazan los filtros. La caja Lámina usa estos
        #     mismos textos
        TXT_SIN_TARJETA = {
            K.ES: "No se encontró la tarjeta gris: no se puede analizar.",
            K.EN: "The gray card was not found: the series cannot be "
                  "analyzed.",
            K.CA: "No s'ha trobat la targeta grisa: no es pot analitzar."}
        TXT_RECHAZADAS = {
            K.ES: ("Hay {n} tesela de tarjeta fuera por los filtros: el "
                   "{porcentaje} % de las {esperadas}.",
                   "Hay {n} teselas de tarjeta fuera por los filtros: el "
                   "{porcentaje} % de las {esperadas}."),
            K.EN: ("{n} card tile left out by the filters: {porcentaje}% "
                   "of {esperadas}.",
                   "{n} card tiles left out by the filters: {porcentaje}% "
                   "of {esperadas}."),
            K.CA: ("Hi ha {n} tessel·la de targeta fora pels filtres: el "
                   "{porcentaje} % de les {esperadas}.",
                   "Hi ha {n} tessel·les de targeta fora pels filtres: el "
                   "{porcentaje} % de les {esperadas}.")}
        FORMATO_PORCENTAJE = "{:.2f}"

        # --- Avisos de las rechazadas, uno por causa (biboecf.KTE.AVISO_*)
        TXT_TARJETA_SUCIA = {
            K.ES: "El {porcentaje} % de las teselas de tarjeta tiene un "
                  "ruido o unos valores raros: la tarjeta puede tener polvo, "
                  "marcas o un defecto. Límpiela o cámbiela.",
            K.EN: "{porcentaje}% of the card tiles have unusual noise or "
                  "values: the card may have dust, marks or a defect. Clean "
                  "or replace it.",
            K.CA: "El {porcentaje} % de les tessel·les de targeta té un "
                  "soroll o uns valors estranys: la targeta pot tindre pols, "
                  "marques o un defecte. Netegeu-la o canvieu-la."}
        TXT_LUZ_DESIGUAL = {
            K.ES: "El {porcentaje} % de las teselas de tarjeta recibe una "
                  "luz distinta de la del resto: la luz no es uniforme"
                  "{lados}. Mueva la luz o centre la tarjeta.",
            K.EN: "{porcentaje}% of the card tiles get a different light "
                  "from the rest: the light is not even{lados}. Move the "
                  "light or centre the card.",
            K.CA: "El {porcentaje} % de les tessel·les de targeta rep una "
                  "llum diferent de la de la resta: la llum no és uniforme"
                  "{lados}. Moveu la llum o centreu la targeta."}
        TXT_REVISAR_SERIE = {
            K.ES: "En total queda fuera el {porcentaje} % de las teselas de "
                  "tarjeta: revise la luz y la tarjeta.",
            K.EN: "In total, {porcentaje}% of the card tiles are left out: "
                  "check the light and the card.",
            K.CA: "En total queda fora el {porcentaje} % de les tessel·les "
                  "de targeta: reviseu la llum i la targeta."}
        TXT_REPETIR_SERIE = {
            K.ES: "En total queda fuera el {porcentaje} % de las teselas de "
                  "tarjeta: conviene repetir la serie.",
            K.EN: "In total, {porcentaje}% of the card tiles are left out: "
                  "the series should be repeated.",
            K.CA: "En total queda fora el {porcentaje} % de les tessel·les "
                  "de targeta: convé repetir la sèrie."}

        # --- Dónde se agrupa la luz desigual (biboecf.KTE.LADO_*): la
        #     frase que la introduce, cada lado y cómo se unen
        TXT_DONDE = {K.ES: ", sobre todo {donde}",
                     K.EN: ", above all {donde}",
                     K.CA: ", sobretot {donde}"}
        TXT_DONDE_LADO = {
            biboecf.KTE.LADO_IZQUIERDA: {K.ES: "a la izquierda",
                                         K.EN: "on the left",
                                         K.CA: "a l'esquerra"},
            biboecf.KTE.LADO_DERECHA: {K.ES: "a la derecha",
                                       K.EN: "on the right",
                                       K.CA: "a la dreta"},
            biboecf.KTE.LADO_ARRIBA: {K.ES: "arriba", K.EN: "at the top",
                                      K.CA: "dalt"},
            biboecf.KTE.LADO_ABAJO: {K.ES: "abajo", K.EN: "at the bottom",
                                     K.CA: "baix"}}
        TXT_Y = {K.ES: " y ", K.EN: " and ", K.CA: " i "}

        # --- La luz cambió: Z-V de control que se apartan de la ZV (con
        #     lo que se aparta cada una, en zonas)
        TXT_LUZ_CAMBIO = {
            K.ES: ("La luz cambió durante la serie: esta Z-V se aparta de "
                   "la ZV y no entra en la media: {idents}.",
                   "La luz cambió durante la serie: estas Z-V se apartan "
                   "de la ZV y no entran en la media: {idents}."),
            K.EN: ("The light changed during the series: this Z-V departs "
                   "from the ZV and is left out of the average: {idents}.",
                   "The light changed during the series: these Z-V depart "
                   "from the ZV and are left out of the average: "
                   "{idents}."),
            K.CA: ("La llum va canviar durant la sèrie: esta Z-V s'aparta "
                   "de la ZV i no entra en la mitjana: {idents}.",
                   "La llum va canviar durant la sèrie: estes Z-V "
                   "s'aparten de la ZV i no entren en la mitjana: "
                   "{idents}.")}

        # --- Exportaciones del revelador de menos bits que las
        #     definitivas (con sus zonas): solo valen para probar
        TXT_TIFF_8_BITS = {
            K.ES: ("Esta exportación del revelador tiene menos de "
                   "{definitivos} bits: vale para probar, no para el "
                   "análisis definitivo: {zonas}.",
                   "Estas exportaciones del revelador tienen menos de "
                   "{definitivos} bits: valen para probar, no para el "
                   "análisis definitivo: {zonas}."),
            K.EN: ("This export from the raw developer has fewer than "
                   "{definitivos} bits: it is fine for testing, not for "
                   "the final analysis: {zonas}.",
                   "These exports from the raw developer have fewer than "
                   "{definitivos} bits: they are fine for testing, not for "
                   "the final analysis: {zonas}."),
            K.CA: ("Esta exportació del revelador té menys de "
                   "{definitivos} bits: val per a provar, no per a "
                   "l'anàlisi definitiva: {zonas}.",
                   "Estes exportacions del revelador tenen menys de "
                   "{definitivos} bits: valen per a provar, no per a "
                   "l'anàlisi definitiva: {zonas}.")}

        # --- Desvío de una toma: identificador y desvío con signo, en
        #     tercios; el punto decimal se cambia por el del idioma
        FORMATO_DEV = "{ident} ({dev:+.2f})"
        FORMATO_UMBRAL = "{:.2f}"
        PUNTO = "."
        SEP_DECIMAL = {K.ES: ",", K.EN: ".", K.CA: ","}

        # --- Entre los identificadores de una lista
        SEP_IDENTS = ", "
        TXT_SIN_BALANCE = {
            K.ES: "No se hizo el balance de blancos personalizado inicial.",
            K.EN: "The initial custom white balance was not taken.",
            K.CA: "No es va fer el balanç de blancs personalitzat inicial."}
        TXT_MISMO_BALANCE = {
            K.ES: "Las dos primeras Z-V tienen el mismo balance de blancos: "
                  "no se hizo el personalizado.",
            K.EN: "The first two Z-V have the same white balance: the "
                  "custom one was not taken.",
            K.CA: "Les dues primeres Z-V tenen el mateix balanç de blancs: "
                  "no es va fer el personalitzat."}

        # --- Texto de cada incidencia (códigos de biboecf.KI)
        _KI = biboecf.KI
        TEXTOS_INCIDENCIA = {
            _KI.ISO_DISTINTO: TXT_ISO_DISTINTO,
            _KI.MISMO_BALANCE: TXT_MISMO_BALANCE,
            _KI.SIN_BALANCE: TXT_SIN_BALANCE,
            _KI.MEDIO_PASO: TXT_MEDIO_PASO,
            _KI.PASO_ENTERO: TXT_PASO_ENTERO,
            _KI.INICIALES_SOBRAN: TXT_INICIALES_SOBRAN,
            _KI.LADOS: TXT_LADOS,
            _KI.SIN_CAMBIO: TXT_SIN_CAMBIO,
            _KI.CAMBIOS_SOBRAN: TXT_CAMBIOS_SOBRAN,
            _KI.SIN_FINAL: TXT_SIN_FINAL,
            _KI.SALTO: TXT_SALTO,
            _KI.SOBRANTES: TXT_SOBRANTES,
            _KI.TAPADAS_MAL: TXT_TAPADAS_MAL,
            _KI.TAPADAS_CON_LUZ: TXT_TAPADAS_CON_LUZ,
            _KI.ISO_TAPADAS: TXT_ISO_TAPADAS,
            _KI.SIN_BALANCES: TXT_SIN_BALANCES,
            _KI.SIN_TOMA: TXT_SIN_TOMA,
            _KI.REPETIDA: TXT_REPETIDA,
            _KI.FUERA: TXT_FUERA,
            _KI.DESVIADAS: TXT_DESVIADAS,
            _KI.SIN_TARJETA: TXT_SIN_TARJETA,
            _KI.RECHAZADAS: TXT_RECHAZADAS,
            _KI.TARJETA_SUCIA: TXT_TARJETA_SUCIA,
            _KI.LUZ_DESIGUAL: TXT_LUZ_DESIGUAL,
            _KI.REVISAR_SERIE: TXT_REVISAR_SERIE,
            _KI.REPETIR_SERIE: TXT_REPETIR_SERIE,
            _KI.LUZ_CAMBIO: TXT_LUZ_CAMBIO,
            _KI.TIFF_8_BITS: TXT_TIFF_8_BITS}

        # --- Identificador corto: número final del nombre del archivo
        PATRON_IDENT = r"(\d+)$"

    #
    def __init__(self, master: ctk.CTkBaseClass) -> None:
        super().__init__(master, highlightthickness=0,
                         height=self._alto(),
                         bg=self._color(ctk.ThemeManager.theme["CTk"]
                                        ["fg_color"]))
        self.celdas: dict[tuple[int, int], list[str]] = {}

        # --- Pie: (botón izquierdo, resumen, botones derechos, separación
        #     entre estos), o None
        self.pie: tuple[ctk.CTkButton, ctk.CTkLabel,
                        tuple[ctk.CTkButton, ...], int] | None = None
        self.bind("<Configure>", lambda _: self.dibujar())

    #
    # --- Cuenta (función pura)
    #

    #
    @classmethod
    def ident(cls, archivo: Path, archivos: list[Path]) -> str:
        """
        Identificador corto: número final del nombre o, si no tiene, el orden
        en la serie (contando desde 1)
        """
        numero = re.search(cls.KR.PATRON_IDENT, archivo.stem)
        return numero.group(1) if numero else str(archivos.index(archivo) + 1)

    #
    @classmethod
    def pos_zv(cls) -> tuple[int, int]:
        """ Posición de la ZV: (zona, tercio) """
        return divmod(cls.KR.TERCIOS_LADO, cls.KR.TERCIOS)

    #
    @classmethod
    def posiciones(cls) -> list[tuple[int, int]]:
        """ Las 31 posiciones que existen, de Z0 a ZX. """
        return [divmod(i, cls.KR.TERCIOS)
                for i in range((2 * cls.KR.TERCIOS_LADO) + 1)]

    #
    @classmethod
    def resumen(cls, OECF: biboecf.OECF) -> str:
        """
        Línea de debajo de la rejilla: «Serie completa» o cuántas posiciones
        faltan.
        """
        n = len(OECF.huecos)
        if not n:
            return K.tr(cls.KR.TXT_COMPLETA)
        return K.tr_n(cls.KR.TXT_FALTAN, n).format(n=n)

    #
    @classmethod
    def linea_balance(cls, balance: bool | None) -> str:
        """
        Línea del balance de blancos personalizado inicial. balance: True (se
        hizo), False (no) o None (no se sabe)
        """
        valor = {True: cls.KR.TXT_SI, False: cls.KR.TXT_NO,
                 None: cls.KR.TXT_NO_SE}[balance]
        return K.tr(cls.KR.TXT_BALANCE).format(valor=K.tr(valor))

    #
    @classmethod
    def linea_balances(cls, n: int) -> str:
        """ Línea de los balances de cámara: cuántos hay. """
        return K.tr(cls.KR.TXT_BALANCES).format(n=n)

    #
    @classmethod
    def linea_tapadas(cls, n: int) -> str:
        """ Línea de las tomas tapadas: cuántas hay de las esperadas. """
        return K.tr(cls.KR.TXT_TAPADAS).format(n=n,
                                               esperadas=cls.KR.TAPADAS)

    #
    @classmethod
    def incidencias(cls, OECF: biboecf.OECF) -> list[str]:
        """
        Todas las incidencias, una por línea: se muestran aparte, en su propia
        ventana, para que la principal no crezca con ellas. Cuáles son lo
        decide biboecf; aquí solo se traducen.
        """
        return [cls.texto_incidencia(inc, OECF)
                for inc in biboecf.incidencias(OECF)]

    #
    @classmethod
    def texto_incidencia(cls, inc: biboecf.Incidencia,
                         OECF: biboecf.OECF) -> str:
        """
        Texto de una incidencia en el idioma activo. Cada texto usa los datos
        que necesita; los demás se ignoran.
        """
        kr = cls.KR
        raws = OECF.raws
        texto = kr.TEXTOS_INCIDENCIA[inc.codigo]
        n = len(inc.tomas) if inc.tomas else inc.n

        # --- Tomas: su identificador y, en las desviadas y en las de la
        #     luz que cambió, cuánto se apartan
        if inc.codigo == biboecf.KI.DESVIADAS:
            idents = [cls.decimal(kr.FORMATO_DEV.format(
                ident=cls.ident(raws[i], raws), dev=OECF.devs[i]))
                for i in inc.tomas]
        elif inc.valores:
            idents = [cls.decimal(kr.FORMATO_DEV.format(
                ident=cls.ident(raws[i], raws), dev=valor))
                for i, valor in zip(inc.tomas, inc.valores)]
        else:
            idents = [cls.ident(raws[i], raws) for i in inc.tomas]

        plantilla = (K.tr_n(texto, n)
                     if isinstance(texto[K.idioma], tuple) else K.tr(texto))
        return plantilla.format(
            n=n, esperadas=inc.esperado, esperados=inc.esperado,
            idents=kr.SEP_IDENTS.join(idents),
            ident=idents[0] if idents else "",
            iso=(biboecf.OECF.TextoISO(OECF.isoSerie)
                 if (OECF.isoSerie is not None) else ""),
            zona=(biboecf.texto_zona(inc.tercioEV)
                  if (inc.tercioEV is not None) else ""),
            zonas=kr.SEP_IDENTS.join(biboecf.texto_zona(t)
                                     for t in inc.tercioEVs),
            definitivos=biboecf.KRV.BITS_DEFINITIVOS,
            esperada=biboecf.texto_zona(inc.esperado),
            real=(biboecf.texto_zona(inc.tercioEV)
                  if (inc.tercioEV is not None) else ""),
            umbral=cls.decimal(kr.FORMATO_UMBRAL.format(
                biboecf.KP.DEV_MAX)),
            porcentaje=cls.decimal(kr.FORMATO_PORCENTAJE.format(
                inc.porcentaje)),
            lados=(K.tr(kr.TXT_DONDE).format(donde=K.tr(kr.TXT_Y).join(
                K.tr(kr.TXT_DONDE_LADO[lado]) for lado in inc.lados))
                if inc.lados else ""))

    #
    @classmethod
    def decimal(cls, texto: str) -> str:
        """ Texto con el punto decimal cambiado por el del idioma activo. """
        return texto.replace(cls.KR.PUNTO, K.tr(cls.KR.SEP_DECIMAL))

    #
    # --- Dibujo
    #

    #
    def mostrar(self, OECF: biboecf.OECF) -> None:
        """
        Muestra las celdas de una serie: las posiciones de OECF, como (zona,
        tercio), con el identificador corto de cada toma.
        """
        raws = OECF.raws
        self.celdas = {biboecf.zona_tercio(t): [self.ident(raws[i], raws)
                                                for i in idxs]
                       for t, idxs in OECF.celdas.items()}
        self.dibujar()

    #
    def dibujar(self) -> None:
        """ Dibuja cabeceras y celdas con el ancho actual del Canvas. """
        self.delete("all")
        self.configure(bg=self._color(ctk.ThemeManager.theme["CTk"]
                                      ["fg_color"]))
        texto = self._color(ctk.ThemeManager.theme["CTkLabel"]["text_color"])

        kr = self.KR
        ancho = max(kr.CELDA,
                    ((self.winfo_width() - kr.ANCHO_ETIQUETAS) // kr.ZONAS)
                    - kr.HUECO)
        paso_x, paso_y = ancho + kr.HUECO, kr.CELDA + kr.HUECO

        # --- Cabeceras de columna (zonas) y de fila (tercios)
        for zona, cabecera in enumerate(kr.CABECERAS):
            x = kr.ANCHO_ETIQUETAS + (zona * paso_x) + (ancho / 2)
            self.create_text(x, kr.ALTO_CABECERA / 2, text=cabecera,
                             fill=texto)
        for tercio, fila in enumerate(kr.FILAS):
            y = kr.ALTO_CABECERA + (tercio * paso_y) + (kr.CELDA / 2)
            self.create_text(kr.ANCHO_ETIQUETAS / 2, y, text=fila,
                             fill=texto)

        # --- Celdas: las que no existen (X +.3 y X +.7) no se dibujan
        for pos in self.posiciones():
            zona, tercio = pos
            x = kr.ANCHO_ETIQUETAS + (zona * paso_x)
            y = kr.ALTO_CABECERA + (tercio * paso_y)
            self._celda(pos, x, y, ancho)

        # --- Pie (si lo hay), bajo las celdas: los botones, como los de
        #     la ventana, el izquierdo alineado con el borde izquierdo de
        #     la Z0 y los derechos, seguidos, con el derecho de la ZX; el
        #     resumen, centrado en el hueco entre ellos (así no los pisa).
        #     Todo centrado en vertical; su alto es el del más alto.
        #     delete("all") lo quita del Canvas: se vuelve a colocar
        if self.pie is not None:
            izquierdo, resumen, derechos, sep = self.pie
            widgets = (izquierdo, resumen, *derechos)
            fondo = self.cget("bg")
            arriba = kr.ALTO_CABECERA + (kr.TERCIOS * paso_y) + kr.HUECO
            alto_pie = max(w.winfo_reqheight() for w in widgets)
            centro_y = arriba + (alto_pie / 2)
            primera, ultima = kr.COLUMNAS_PIE
            for w in widgets:
                w.configure(bg_color=fondo)
            x_izquierdo = kr.ANCHO_ETIQUETAS + (primera * paso_x)
            self.create_window(x_izquierdo, centro_y, window=izquierdo,
                               anchor="w")
            x = kr.ANCHO_ETIQUETAS + (ultima * paso_x) + ancho
            for w in reversed(derechos):
                self.create_window(x, centro_y, window=w, anchor="e")
                x -= w.winfo_reqwidth() + sep
            fin_izquierdo = x_izquierdo + izquierdo.winfo_reqwidth()
            self.create_window((fin_izquierdo + x + sep) / 2,
                               centro_y, window=resumen, anchor="center")

            # --- El Canvas crece con el pie (solo si cambia: configurar
            #     el alto lo vuelve a dibujar)
            alto = round(arriba + alto_pie)
            if int(self.cget("height")) != alto:
                self.configure(height=alto)

    #
    def poner_pie(self, izquierdo: ctk.CTkButton, resumen: ctk.CTkLabel,
                  derechos: tuple[ctk.CTkButton, ...], sep: int) -> None:
        """
        Coloca el pie: un botón a la izquierda, los de la derecha (en su orden,
        de izquierda a derecha, separados sep píxeles: los de la ventana) y el
        resumen entre ellos. Tienen que ser hijos de la rejilla (Tk no deja
        meter en un Canvas widgets de otro sitio)
        """
        self.pie = (izquierdo, resumen, derechos, sep)
        self.dibujar()

    #
    # --- Una celda: estado según cuántas tomas tenga
    def _celda(self, pos: tuple[int, int], x: float, y: float,
               ancho: float) -> None:
        kr = self.KR
        idents = self.celdas.get(pos, [])
        es_zv = pos == self.pos_zv()
        caja = (x, y, x + ancho, y + kr.CELDA)

        # --- falta: borde discontinuo y texto, sin relleno (se distingue
        #     también por la forma, no solo por el color)
        if not idents:
            aviso = self._color(kr.TEXTO_AVISO)
            self.create_rectangle(*caja, outline=aviso, dash=kr.GUIONES,
                                  width=kr.BORDE)
            self.create_text(x + (ancho / 2), y + (kr.CELDA / 2), fill=aviso,
                             text=K.tr(kr.TXT_FALTA), font=kr.FUENTE)
            return

        # --- repetida (fuera de ZV): relleno de aviso, identificadores
        #     apilados. ZV: borde de acento; en aviso si no son anclas
        correcta = len(idents) == (kr.ANCLAS if es_zv else 1)
        fondo = kr.OK if correcta else kr.AVISO
        color = kr.TEXTO_OK if correcta else kr.TEXTO_AVISO
        borde = (self._color(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
                 if es_zv else self._color(color))
        self.create_rectangle(*caja, fill=self._color(fondo), outline=borde,
                              width=kr.BORDE_ZV if es_zv else kr.BORDE)

        # --- Si no caben, se dice cuántas hay
        lineas = idents if (len(idents) <= kr.MAX_LINEAS) else [
            K.tr(kr.TXT_N_ZV).format(n=len(idents))]
        arriba = y + ((kr.CELDA - (len(lineas) * kr.ALTO_LINEA)) / 2)
        for i, linea in enumerate(lineas):
            self.create_text(x + (ancho / 2),
                             arriba + ((i + 0.5) * kr.ALTO_LINEA),
                             text=linea, fill=self._color(color),
                             font=kr.FUENTE)

    #
    # --- Alto total: cabecera y 3 filas de celdas
    @classmethod
    def _alto(cls) -> int:
        kr = cls.KR
        return kr.ALTO_CABECERA + (kr.TERCIOS * (kr.CELDA + kr.HUECO))

    #
    # --- Color (claro, oscuro) según el modo de customtkinter
    @staticmethod
    def _color(par: tuple[str, str] | list[str]) -> str:
        return par[0] if (ctk.get_appearance_mode() == "Light") else par[1]
