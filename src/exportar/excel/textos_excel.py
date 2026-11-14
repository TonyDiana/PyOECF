# -*- coding: utf-8 *-*
"""
    :Propósito: Textos del libro Excel de resultados y del PDF de
                la cámara, en los tres idiomas.
                oecfCalc no traduce: el libro los recibe ya traducidos, en
                el idioma de la ventana (textos_excel)
    :Autor:     Tony Diana
    :Versión:   26.10.17
"""

# cSpell:ignore ASIM, CIELAB, Colorimetría, colours, DESV, KPDF
# cSpell:ignore Lightroom, LSTAR, MULT, neighbouring, Preajuste, SRGB, Srgb
# cSpell:ignore teclearlo, unclipped, viñeteo

# --- Valenciano
# cSpell:ignore acceptades, admet, així, Aleatori, aleatori, Altes, altre
# cSpell:ignore altres, amb, amunt, Anàlisi, analitza, analitzar, anotat
# cSpell:ignore anteriors, Arxiu, asimetria, asimètrica, assolit, auditoria
# cSpell:ignore baix, baixar, Balanç, balanç, Balanços, balanços, blanc, blancs
# cSpell:ignore Blau, blau, brillant, Càlcul, càlculs, calent, càmera, càmeres
# cSpell:ignore canvie, casen, caure, cel, cinquena, Colorimetria, comencen
# cSpell:ignore comparació, comparant, Compleix, complet, Comprovació, compta
# cSpell:ignore comptar, compte, compten, Concepte, còpia, còpies, Corba, corba
# cSpell:ignore corbes, criteri, Dades, dades, dalt, damunt, d'Anàlisi, Davall
# cSpell:ignore davall, decisió, declarat, defecte, defineix, deixen, dels
# cSpell:ignore d'enginyeria, d'entrada, desplaçament, destí, Desviació
# cSpell:ignore desviacions, dia, dibuixar, Diferència, diferència, diferent
# cSpell:ignore Dispersió, dispersió, disseny, divideix, d'on, Drap, drap, d'un
# cSpell:ignore d'uns, eixe, Eixida, eixida, Els, els, Enginyeria, Ennuvolat
# cSpell:ignore És, és, escrit, Escriu, espai, Esperat, esperat, està, estimat
# cSpell:ignore estimats, exportacions, exposició, fallada, filtres, finestra
# cSpell:ignore Fins, Flaix, fórmules, fosc, fosques, Fracció, fracció, Generat
# cSpell:ignore gràfic, Gràfics, gràfics, Grandària, grisa, Guany, guany
# cSpell:ignore iguals, importants, impreses, ixen, l'aigua, làmina, l'arrel
# cSpell:ignore l'editor, l'eixida, l'entrada, l'escala, linealitat, llegir
# cSpell:ignore llegit, llevat, llibre, Llig, Lligen, llindar, llindars, llisa
# cSpell:ignore llista, Llum, llum, lluminositat, Llums, llums, l'objectiu
# cSpell:ignore locar, l'ordre, l'última, Luminància, luminància, mà, mana
# cSpell:ignore mateixa, Màxim, màxim, màxima, megapíxels, més, Mesurada
# cSpell:ignore mesurada, mesurat, mesures, mètode, Mínim, mitjana, mitjos
# cSpell:ignore Motiu, motiu, multiplicadors, Negre, negre, neutre, nivell
# cSpell:ignore nivells, Nom, nom, Només, només, normalitzada, normalitzat
# cSpell:ignore Objectiu, objectiu, Obtingut, obtingut, Ombra, ombra, Ombres
# cSpell:ignore ombres, orde, ordre, passa, passar, Passos, pegat, Percentatge
# cSpell:ignore perquè, Personalitzat, personalitzat, píxels, poc, Poden, Poseu
# cSpell:ignore Posició, potència, Preajust, pren, Preses, preses, Profunditat
# cSpell:ignore pròpies, propòsit, prou, pròxim, punt, puntes, punts, qual
# cSpell:ignore qualitat, Quan, Què, què, Quocient, ratlla, Rebutjades
# cSpell:ignore rebutjades, recomana, Recomanacions, Recomanada, recomanada
# cSpell:ignore recomanades, Recompte, Referència, referència, referències
# cSpell:ignore Relació, repartixen, resolució, respecte, resultat, retall
# cSpell:ignore Retallat, retallat, retallats, Rètol, revelat, robustes, Roig
# cSpell:ignore roig, roïna, s'aparten, s'aprecia, s'aprecie, saturació
# cSpell:ignore saturat, seguits, senceres, Senyal, senyal, Sèrie, sèrie
# cSpell:ignore s'estima, seu, seua, seus, s'ha, simètric, Sòl, sòl, sòls, Són
# cSpell:ignore són, Soroll, soroll, Sostre, sostre, suau, suggerida
# cSpell:ignore Suggeriment, suggeriment, Suggerit, suggerit, Tapades, tapades
# cSpell:ignore targeta, taronja, teclejar, teòric, terç, Terços, terços
# cSpell:ignore Tessel, tessel, teu, teua, teues, típiques, tota, traça
# cSpell:ignore transferència, Tria, triades, Tungstè, Últim, últim, Unitat
# cSpell:ignore units, usen, useu, utilitzable, valors, vegades, Vegeu, veïnes
# cSpell:ignore veïns, Verd, verd, veritat, vinyetatge, volta, Vora, vora
# cSpell:ignore xicotet

__all__ = ["textos_excel"]

# --- Bibliotecas internas
from kernel import K
from leer import KM
from ..pdf import KPDF
from .excel import KXL

# --- Atajos: las claves son constantes del libro y del PDF
_L = KXL
_F = KPDF


#
# --- Texto aún sin traducir: el español en los tres idiomas, hasta que
#     llegue la traducción (PENDIENTE DE DEEPSEEK; Tony, 2026-11-10)
def _solo_es(texto: str) -> dict[str, str]:
    return {K.ES: texto, K.EN: texto, K.CA: texto}


#
# --- {clave: {idioma: texto}}
TEXTOS = {
    # --- Nombres de las hojas
    _L.T_HOJA_RESUMEN: {K.ES: "Análisis", K.EN: "Analysis",
                        K.CA: "Anàlisi"},
    _L.T_HOJA_GRAF: {K.ES: "Gráficos", K.EN: "Charts",
                     K.CA: "Gràfics"},
    _L.T_HOJA_DATOS: {K.ES: "Datos", K.EN: "Data", K.CA: "Dades"},
    _L.T_HOJA_CONSTANTES: {K.ES: "Constantes", K.EN: "Constants",
                           K.CA: "Constants"},
    _L.T_HOJA_CALCULO: {K.ES: "Cálculo", K.EN: "Calculation",
                        K.CA: "Càlcul"},
    _L.T_HOJA_RECHAZADAS: {K.ES: "Rechazadas", K.EN: "Rejected",
                           K.CA: "Rebutjades"},
    _L.T_HOJA_IA: {K.ES: "IA", K.EN: "IA", K.CA: "IA"},
    _L.T_HOJA_ISO: {K.ES: "ISO", K.EN: "ISO", K.CA: "ISO"},

    # --- Hoja ISO y página de la secuencia de ISO en el PDF. EN y CA, de
    #     Claude a petición de Tony (2026-11-13)
    _L.T_TITULO_ISO: {K.ES: "Secuencia de ISO", K.EN: "ISO sequence",
                      K.CA: "Seqüència d'ISO"},
    _L.T_NOTA_ISO: {
        K.ES: "Una ZV y una Z2 por ISO, tomadas entre los dos marcadores, "
              "tras los balances de blancos. Todo en el canal verde. "
              "Desviación: cuánto se aparta la ZV de cada ISO de la del ISO "
              "inicial, en zonas. Ruido de lectura: el del borde oscuro del "
              "sensor, en niveles. Ruido: dispersión relativa de la tarjeta "
              "gris. Textura: la del paño en la Z2, sin el ruido de la "
              "tarjeta. Ruido y textura, a escala de pantalla (la foto "
              "entera en una pantalla Full HD). Umbral: textura/ruido de "
              "{umbral} ({rose_textura}, en Constantes). La textura se ve "
              "desde el 100 % del umbral, es justa desde el {justa} % "
              "({textura_justa}) y por debajo se pierde.",
        K.EN: "One ZV and one Z2 per ISO, taken between the two markers, "
              "after the white balances. All in the green channel. "
              "Deviation: how far the ZV of each ISO is from that of the "
              "initial ISO, in zones. Read noise: that of the dark edge of "
              "the sensor, in levels. Noise: relative dispersion of the grey "
              "card. Texture: that of the cloth in Z2, without the card's "
              "noise. Noise and texture, at screen scale (the whole photo on "
              "a Full HD screen). Threshold: texture/noise of {umbral} "
              "({rose_textura}, in Constants). The texture is visible from "
              "100 % of the threshold, borderline from {justa} % "
              "({textura_justa}) and lost below that.",
        K.CA: "Una ZV i una Z2 per ISO, preses entre els dos marcadors, "
              "després dels balanços de blancs. Tot en el canal verd. "
              "Desviació: quant s'aparta la ZV de cada ISO de la de l'ISO "
              "inicial, en zones. Soroll de lectura: el de la vora fosca del "
              "sensor, en nivells. Soroll: dispersió relativa de la targeta "
              "grisa. Textura: la del drap en la Z2, sense el soroll de la "
              "targeta. Soroll i textura, a escala de pantalla (la foto "
              "sencera en una pantalla Full HD). Llindar: textura/soroll de "
              "{umbral} ({rose_textura}, en Constants). La textura es veu "
              "des del 100 % del llindar, és justa des del {justa} % "
              "({textura_justa}) i per davall es perd."},
    _L.T_CAB_ISO: {K.ES: "ISO", K.EN: "ISO", K.CA: "ISO"},
    _L.T_CAB_Z2: {K.ES: "Z2", K.EN: "Z2", K.CA: "Z2"},
    _L.T_CAB_DESVIACION_ISO: {K.ES: "Desviación ZV (zonas)",
                              K.EN: "ZV deviation (zones)",
                              K.CA: "Desviació ZV (zones)"},
    _L.T_CAB_LECTURA_ISO: {K.ES: "Ruido de lectura", K.EN: "Read noise",
                           K.CA: "Soroll de lectura"},
    _L.T_CAB_RUIDO_ZV: {K.ES: "Ruido ZV", K.EN: "ZV noise",
                        K.CA: "Soroll ZV"},
    _L.T_CAB_RUIDO_Z2: {K.ES: "Ruido Z2", K.EN: "Z2 noise",
                        K.CA: "Soroll Z2"},
    _L.T_CAB_TEXTURA_Z2: {K.ES: "Textura Z2", K.EN: "Z2 texture",
                          K.CA: "Textura Z2"},
    _L.T_CAB_TEXTURA_RUIDO_Z2: {K.ES: "Textura/ruido Z2",
                                K.EN: "Z2 texture/noise",
                                K.CA: "Textura/soroll Z2"},
    _L.T_CAB_PORCENTAJE_UMBRAL: {K.ES: "% del umbral",
                                 K.EN: "% of threshold",
                                 K.CA: "% del llindar"},
    _L.T_CAB_SE_APRECIA: {K.ES: "Textura en sombras (Z2)",
                          K.EN: "Shadow texture (Z2)",
                          K.CA: "Textura en ombres (Z2)"},
    _L.T_CAB_NOTA_ISO: {K.ES: "Nota", K.EN: "Note", K.CA: "Nota"},
    _L.T_ISO_ESTIMADO: {K.ES: "Estimación: la Z2 solo llegó a {zona}",
                        K.EN: "Estimate: Z2 only reached {zona}",
                        K.CA: "Estimació: la Z2 només va arribar a {zona}"},
    _L.T_ISO_SIN_MEDIR: {K.ES: "No se puede medir",
                         K.EN: "Cannot be measured",
                         K.CA: "No es pot mesurar"},
    _L.T_NOTA_ISO_PDF: {
        K.ES: "Qué pasa al subir el ISO, con una ZV y una Z2 por ISO. "
              "Exposición: si la imagen sale igual, más clara o más oscura "
              "que al ISO inicial. Textura en sombras: si se ve la textura "
              "del paño en la Z2 (verde, se ve; amarillo, justa; rojo, se "
              "pierde). Sombras con textura desde: dónde colocar las "
              "sombras importantes a ese ISO (≈, estimado solo con su ZV y "
              "su Z2); «Ninguna»: ni en la ZV llega la textura a la del ISO "
              "inicial. Los números, en la hoja ISO del libro.",
        K.EN: "What happens when raising the ISO, with one ZV and one Z2 per "
              "ISO. Exposure: whether the image comes out the same, lighter "
              "or darker than at the initial ISO. Shadow texture: whether "
              "the cloth's texture is visible in Z2 (green, visible; yellow, "
              "borderline; red, lost). Shadows with texture from: where to "
              "place the important shadows at that ISO (≈, estimated only "
              "from its ZV and Z2); «None»: not even in ZV does the texture "
              "reach that of the initial ISO. The figures, in the ISO sheet "
              "of the workbook.",
        K.CA: "Què passa en pujar l'ISO, amb una ZV i una Z2 per ISO. "
              "Exposició: si la imatge ix igual, més clara o més fosca que "
              "a l'ISO inicial. Textura en ombres: si es veu la textura del "
              "drap en la Z2 (verd, es veu; groc, justa; roig, es perd). "
              "Ombres amb textura des de: on col·locar les ombres "
              "importants a eixe ISO (≈, estimat només amb la seua ZV i la "
              "seua Z2); «Cap»: ni en la ZV arriba la textura a la de l'ISO "
              "inicial. Els números, en el full ISO del llibre."},
    _L.T_CAB_EXPOSICION_ISO: {K.ES: "Exposición", K.EN: "Exposure",
                              K.CA: "Exposició"},
    _L.T_EXPOSICION_IGUAL: {K.ES: "Igual", K.EN: "Same", K.CA: "Igual"},
    _L.T_EXPOSICION_CLARA: {K.ES: "+{cuanto} zona", K.EN: "+{cuanto} zone",
                            K.CA: "+{cuanto} zona"},
    _L.T_EXPOSICION_OSCURA: {K.ES: "−{cuanto} zona", K.EN: "−{cuanto} zone",
                             K.CA: "−{cuanto} zona"},
    _L.T_TEXTURA_ISO[0]: {K.ES: "Se pierde", K.EN: "Lost",
                          K.CA: "Es perd"},
    _L.T_TEXTURA_ISO[1]: {K.ES: "Justa", K.EN: "Borderline",
                          K.CA: "Justa"},
    _L.T_TEXTURA_ISO[2]: {K.ES: "Se ve", K.EN: "Visible", K.CA: "Es veu"},
    _L.T_CAB_SOMBRAS_ISO: {K.ES: "Sombras con textura desde",
                           K.EN: "Shadows with texture from",
                           K.CA: "Ombres amb textura des de"},
    _L.T_SOMBRAS_ISO: {K.ES: "≈{zona}", K.EN: "≈{zona}", K.CA: "≈{zona}"},
    _L.T_SOMBRAS_NINGUNA: {K.ES: "Ninguna", K.EN: "None", K.CA: "Cap"},
    _L.T_ISO_HASTA: {
        K.ES: "Hasta ISO {hasta}, las sombras de la Z2 conservan la "
              "textura. A partir de ISO {desde}, coloca las sombras "
              "importantes más arriba.",
        K.EN: "Up to ISO {hasta}, the Z2 shadows keep their texture. From "
              "ISO {desde} on, place the important shadows higher.",
        K.CA: "Fins a ISO {hasta}, les ombres de la Z2 conserven la "
              "textura. A partir d'ISO {desde}, col·loca les ombres "
              "importants més amunt."},
    _L.T_ISO_TODOS: {
        K.ES: "En todos los ISO medidos, las sombras de la Z2 conservan la "
              "textura.",
        K.EN: "At every ISO measured, the Z2 shadows keep their texture.",
        K.CA: "En tots els ISO mesurats, les ombres de la Z2 conserven la "
              "textura."},
    _L.T_ISO_NINGUNO: {
        K.ES: "Ni siquiera a ISO {iso} conservan la textura las sombras de "
              "la Z2: coloca las sombras importantes más arriba.",
        K.EN: "Not even at ISO {iso} do the Z2 shadows keep their texture: "
              "place the important shadows higher.",
        K.CA: "Ni tan sols a ISO {iso} conserven la textura les ombres de "
              "la Z2: col·loca les ombres importants més amunt."},

    # --- Hoja Constantes
    _L.T_TITULO_CONSTANTES: {K.ES: "Constantes del método",
                             K.EN: "Method constants",
                             K.CA: "Constants del mètode"},
    _L.T_NOTA_CONSTANTES: {
        K.ES: "Cada constante tiene un nombre. Las fórmulas del libro usan "
              "el nombre, no la celda ni el número.",
        K.EN: "Each constant has a name. The workbook formulas use the "
              "name, not the cell or the number.",
        K.CA: "Cada constant té un nom. Les fórmules del llibre usen el "
              "nom, no la cel·la ni el número."},
    _L.T_CAB_NOMBRE: {K.ES: "Nombre", K.EN: "Name", K.CA: "Nom"},
    _L.T_CAB_VALOR: {K.ES: "Valor", K.EN: "Value", K.CA: "Valor"},
    _L.T_CAB_UNIDAD: {K.ES: "Unidad", K.EN: "Unit", K.CA: "Unitat"},
    _L.T_CAB_QUE_ES: {K.ES: "Qué es", K.EN: "What it is",
                      K.CA: "Què és"},

    # --- Unidades
    _L.U_ZONA: {K.ES: "zona", K.EN: "zone", K.CA: "zona"},
    _L.U_ZONAS: {K.ES: "zonas", K.EN: "zones", K.CA: "zones"},
    _L.U_TERCIOS: {K.ES: "tercios", K.EN: "thirds", K.CA: "terços"},
    _L.U_VECES: {K.ES: "veces", K.EN: "times", K.CA: "vegades"},
    _L.U_LSTAR: {K.ES: "L*", K.EN: "L*", K.CA: "L*"},
    _L.U_PART: {K.ES: "fracción", K.EN: "fraction", K.CA: "fracció"},
    _L.U_NUMERO: {K.ES: "número", K.EN: "number", K.CA: "número"},
    _L.U_TEXTO: {K.ES: "texto", K.EN: "text", K.CA: "text"},
    _L.U_MPX: {K.ES: "megapíxeles", K.EN: "megapixels",
               K.CA: "megapíxels"},

    # --- Qué es cada constante (la clave es su nombre)
    _L.C_ZONA_ZV: {K.ES: "Zona de la Z-V (la quinta).",
                   K.EN: "Zone of the Z-V (the fifth).",
                   K.CA: "Zona de la Z-V (la cinquena)."},
    _L.C_TERCIO_POR_ZONA: {K.ES: "Tercios en que se divide una zona.",
                           K.EN: "Thirds into which a zone is divided.",
                           K.CA: "Terços en què es divideix una zona."},
    _L.C_FACTOR_ZONA: {K.ES: "Luz por zona: una zona es el doble de luz.",
                       K.EN: "Light per zone: one zone is twice the light.",
                       K.CA: "Llum per zona: una zona és el doble de "
                             "llum."},
    _L.C_LZV: {K.ES: "L* del gris neutro en la ZV. Entero, para teclearlo "
                     "en el selector Lab.",
               K.EN: "L* of the neutral grey in the ZV. Whole number, to "
                     "type it in the Lab picker.",
               K.CA: "L* del gris neutre en la ZV. Enter, per a teclejar-lo "
                     "en el selector Lab."},
    _L.C_L_POR_ZONA: {K.ES: "Objetivo de la escala perceptual: L* que sube "
                            "cada zona.",
                      K.EN: "Target of the perceptual scale: L* added by "
                            "each zone.",
                      K.CA: "Objectiu de l'escala perceptual: L* que puja "
                            "cada zona."},
    _L.C_RATIO_SR: {K.ES: "Relación señal/ruido que define el suelo "
                    "(normalizada a {mpx_referencia}). 1 = señal "
                    "igual al ruido: el criterio de ingeniería.",
                    K.EN: "Signal-to-noise ratio that defines the floor "
                    "(normalized to {mpx_referencia}). 1 = signal "
                    "equal to noise: the engineering criterion.",
                    K.CA: "Relació senyal/soroll que defineix el sòl "
                    "(normalitzada a {mpx_referencia}). 1 = senyal "
                    "igual al soroll: el criteri d'enginyeria."},
    _L.C_SNR_MINIMA: {K.ES: "Relación señal/ruido mínima sugerida para una "
                            "zona utilizable («aceptable»), normalizada a "
                            "{mpx_referencia}. Ver la nota.",
                      K.EN: "Suggested minimum signal-to-noise ratio for a "
                            "usable zone (“acceptable”), normalized to "
                            "{mpx_referencia}. See the note.",
                      K.CA: "Relació senyal/soroll mínima suggerida per a "
                            "una zona utilitzable («acceptable»), "
                            "normalitzada a {mpx_referencia}. Vegeu la nota."},
    _L.C_SNR_EXCELENTE: {K.ES: "Relación señal/ruido «excelente» (ISO "
                               "12232), normalizada a {mpx_referencia}.",
                         K.EN: "“Excellent” signal-to-noise ratio (ISO "
                               "12232), normalized to {mpx_referencia}.",
                         K.CA: "Relació senyal/soroll «excel·lent» (ISO "
                               "12232), normalitzada a {mpx_referencia}."},
    _L.C_MPX_REFERENCIA: {
        K.ES: "Tamaño de referencia de la señal/ruido comparable: la de un "
              "píxel se multiplica por la raíz de (megapíxeles del sensor "
              "/ {mpx_referencia}). 8 Mpx, como DxOMark (una copia de unos "
              "30 × 20 cm a 300 ppp).",
        K.EN: "Reference size of the comparable signal/noise: a pixel's "
              "is multiplied by the square root of (sensor megapixels / "
              "{mpx_referencia}). 8 Mpx, as DxOMark (a print of about "
              "30 × 20 cm at 300 ppi).",
        K.CA: "Grandària de referència del senyal/soroll comparable: el "
              "d'un píxel es multiplica per l'arrel de (megapíxels del "
              "sensor / {mpx_referencia}). 8 Mpx, com DxOMark (una còpia "
              "d'uns 30 × 20 cm a 300 ppp)."},
    _L.C_TOLERANCIA_LINEAL: {
        K.ES: "Desviación máxima para decir que un punto es lineal.",
        K.EN: "Maximum deviation to call a point linear.",
        K.CA: "Desviació màxima per a dir que un punt és lineal."},
    _L.C_UMBRAL_RECORTE: {
        K.ES: "Fracción del máximo de un canal desde la que un valor se "
              "considera recortado.",
        K.EN: "Fraction of a channel's maximum from which a value is "
              "considered clipped.",
        K.CA: "Fracció del màxim d'un canal des de la qual un valor es "
              "considera retallat."},
    _L.C_PANO_MINIMO: {
        K.ES: "Textura/ruido mínima del paño en la ZV. Por debajo, el paño "
              "es demasiado suave y la latitud de texturas en las sombras "
              "puede salir corta: se avisa.",
        K.EN: "Minimum texture/noise of the cloth at ZV. Below it, the "
              "cloth is too smooth and the texture latitude in the shadows "
              "may come out short: a warning is given.",
        K.CA: "Textura/soroll mínima del drap en la ZV. Per davall, el drap "
              "és massa suau i la latitud de textures en les ombres pot "
              "eixir curta: s'avisa."},
    _L.C_ROSE_TEXTURA: {
        K.ES: "Secuencia de ISO: textura/ruido desde la que se aprecia la "
              "textura del paño en la Z2 de cada ISO: la textura del paño "
              "(su dispersión sin el ruido de la tarjeta) entre el ruido de "
              "la tarjeta, medidas como se verían con la foto entera en una "
              "pantalla Full HD (cada bloque de píxeles del sensor que ocupa "
              "un píxel de la pantalla, en uno). Del criterio de Rose (Rose "
              "1948; Burgess 1999). La latitud de texturas ya no lo usa: ver "
              "{contraste_sombras}.",
        K.EN: "ISO sequence: texture/noise from which the cloth's texture is "
              "visible in each ISO's Z2: the cloth's texture (its dispersion "
              "without the card's noise) divided by the card's noise, "
              "measured as they would look with the whole photo on a Full HD "
              "screen (each block of sensor pixels that fills one screen "
              "pixel, as one). From the Rose criterion (Rose 1948; Burgess "
              "1999). The texture latitude no longer uses it: see "
              "{contraste_sombras}.",
        K.CA: "Seqüència d'ISO: textura/soroll des de la qual s'aprecia la "
              "textura del drap en la Z2 de cada ISO: la textura del drap "
              "(la seua dispersió sense el soroll de la targeta) entre el "
              "soroll de la targeta, mesurades com es veurien amb la foto "
              "sencera en una pantalla Full HD (cada bloc de píxels del "
              "sensor que ocupa un píxel de la pantalla, en un). Del criteri "
              "de Rose (Rose 1948; Burgess 1999). La latitud de textures ja "
              "no l'usa: vegeu {contraste_sombras}."},
    _L.C_TEXTURA_JUSTA: {
        K.ES: "Fracción del umbral de sombras desde la que la textura de la "
              "Z2 de un ISO es justa; por debajo, se pierde.",
        K.EN: "Fraction of the shadow threshold from which the texture of "
              "an ISO's Z2 is borderline; below it, it is lost.",
        K.CA: "Fracció del llindar d'ombres des de la qual la textura de "
              "la Z2 d'un ISO és justa; per davall, es perd."},
    _L.C_TEXTURA_CONSERVADA: {
        K.ES: "Fracción de la textura del paño en la ZV que debe conservar "
              "una zona de luces para que se aprecie su textura.",
        K.EN: "Fraction of the cloth's texture at ZV that a highlight zone "
              "must keep for its texture to be visible.",
        K.CA: "Fracció de la textura del drap en la ZV que ha de conservar "
              "una zona de llums perquè s'aprecie la seua textura."},
    _L.C_TELA_RECORTADO_APRECIABLE: {
        K.ES: "Fracción del paño recortado que admite como mucho la zona de "
              "luces apreciable.",
        K.EN: "Largest clipped fraction of the cloth allowed in the "
              "visible highlight zone.",
        K.CA: "Fracció del drap retallat que admet com a molt la zona de "
              "llums apreciable."},
    _L.C_TELA_RECORTADO_MAX: {
        K.ES: "Fracción del paño recortado que admite como mucho la zona de "
              "luces recomendada.",
        K.EN: "Largest clipped fraction of the cloth allowed in the "
              "recommended highlight zone.",
        K.CA: "Fracció del drap retallat que admet com a molt la zona de "
              "llums recomanada."},
    _L.C_CONTRASTE_SOMBRAS: {
        K.ES: "Fracción del contraste de la trama del paño en la ZV desde la "
              "que la textura de una zona de sombras es aprovechable (las "
              "sombras recomendadas). El contraste: la diferencia de L* "
              "entre lo más claro y lo más oscuro del paño (percentiles 95 y "
              "5), en las exportaciones del revelador, es decir, lo que se "
              "ve al revelar. Relativo a la ZV para no depender del paño. "
              "Ajustado a ojo en 8 series (error de un tercio como mucho).",
        K.EN: "Fraction of the cloth weave's contrast at ZV from which the "
              "texture of a shadow zone is usable (the recommended shadows). "
              "The contrast: the L* difference between the lightest and the "
              "darkest of the cloth (95th and 5th percentiles), in the "
              "developer exports, that is, what is seen after developing. "
              "Relative to ZV so as not to depend on the cloth. Fitted by eye "
              "on 8 series (an error of one third at most).",
        K.CA: "Fracció del contrast de la trama del drap en la ZV des de la "
              "qual la textura d'una zona d'ombres és aprofitable (les ombres "
              "recomanades). El contrast: la diferència de L* entre el més "
              "clar i el més fosc del drap (percentils 95 i 5), en les "
              "exportacions del revelador, és a dir, el que es veu en "
              "revelar. Relatiu a la ZV per no dependre del drap. Ajustat a "
              "ull en 8 sèries (un error d'un terç com a molt)."},
    _L.C_MARGEN_SOMBRAS: {
        K.ES: "Tercios por debajo de las sombras recomendadas donde empiezan "
              "las apreciables: la resolución de la serie.",
        K.EN: "Thirds below the recommended shadows where the visible ones "
              "begin: the resolution of the series.",
        K.CA: "Terços per davall de les ombres recomanades on comencen les "
              "apreciables: la resolució de la sèrie."},
    _L.C_ANCHO_ZONA: {
        K.ES: "Lo que suma una zona al contar una latitud: cuentan las dos "
              "puntas (de Z3 a Z8 son 6 zonas, no 5).",
        K.EN: "What one zone adds when counting a latitude: both ends count "
              "(from Z3 to Z8 there are 6 zones, not 5).",
        K.CA: "El que suma una zona en comptar una latitud: compten les dues "
              "puntes (de Z3 a Z8 són 6 zones, no 5)."},
    _L.C_LAB_ESCALA: {K.ES: "Constante de CIELAB: factor de la raíz cúbica.",
                      K.EN: "CIELAB constant: factor of the cube root.",
                      K.CA: "Constant de CIELAB: factor de l'arrel "
                            "cúbica."},
    _L.C_LAB_DESPLAZA: {K.ES: "Constante de CIELAB: desplazamiento.",
                        K.EN: "CIELAB constant: offset.",
                        K.CA: "Constant de CIELAB: desplaçament."},
    _L.C_LAB_UMBRAL: {K.ES: "Constante de CIELAB: luminancia por debajo de "
                            "la cual L* es lineal.",
                      K.EN: "CIELAB constant: luminance below which L* is "
                            "linear.",
                      K.CA: "Constant de CIELAB: luminància per davall de "
                            "la qual L* és lineal."},
    _L.C_LAB_PENDIENTE: {K.ES: "Constante de CIELAB: pendiente del tramo "
                               "lineal.",
                         K.EN: "CIELAB constant: slope of the linear part.",
                         K.CA: "Constant de CIELAB: pendent del tram "
                               "lineal."},
    _L.C_SRGB_UMBRAL: {K.ES: "Constante de sRGB: luz por debajo de la cual "
                             "la curva es lineal.",
                       K.EN: "sRGB constant: light below which the curve is "
                             "linear.",
                       K.CA: "Constant de sRGB: llum per davall de la qual "
                             "la corba és lineal."},
    _L.C_SRGB_PENDIENTE: {K.ES: "Constante de sRGB: pendiente del tramo "
                                "lineal.",
                          K.EN: "sRGB constant: slope of the linear part.",
                          K.CA: "Constant de sRGB: pendent del tram "
                                "lineal."},
    _L.C_SRGB_ESCALA: {K.ES: "Constante de sRGB: factor de la potencia.",
                       K.EN: "sRGB constant: factor of the power.",
                       K.CA: "Constant de sRGB: factor de la potència."},
    _L.C_SRGB_GAMMA: {K.ES: "Constante de sRGB: exponente de la curva.",
                      K.EN: "sRGB constant: exponent of the curve.",
                      K.CA: "Constant de sRGB: exponent de la corba."},
    _L.C_SRGB_DESPLAZA: {K.ES: "Constante de sRGB: desplazamiento.",
                         K.EN: "sRGB constant: offset.",
                         K.CA: "Constant de sRGB: desplaçament."},
    _L.C_ESCALA_CURVA: {K.ES: "Valor máximo de la escala de entrada y "
                              "salida de la curva de Lightroom.",
                        K.EN: "Maximum value of the input and output scale "
                              "of the Lightroom curve.",
                        K.CA: "Valor màxim de l'escala d'entrada i eixida "
                              "de la corba de Lightroom."},
    _L.C_TEXTO_RECORTADO: {K.ES: "Marca de recortado.",
                           K.EN: "Clipped mark.",
                           K.CA: "Marca de retallat."},
    _L.C_TEXTO_NO_RECORTADO: {K.ES: "Marca de no recortado.",
                              K.EN: "Not clipped mark.",
                              K.CA: "Marca de no retallat."},
    _L.C_TEXTO_NINGUNO: {K.ES: "Cuando no hay ningún punto lineal.",
                         K.EN: "When there is no linear point.",
                         K.CA: "Quan no hi ha cap punt lineal."},
    _L.C_TEXTO_NO_ALCANZADO: {
        K.ES: "Cuando ningún valor llega al umbral o al recorte.",
        K.EN: "When no value reaches the threshold or clipping.",
        K.CA: "Quan cap valor arriba al llindar o al retall."},
    _L.C_TEXTO_SIN_REVELADO: {
        K.ES: "Cuando las sombras de la latitud de texturas aún no se pueden "
              "medir: faltan las exportaciones del revelador (se miden al "
              "analizar el revelado).",
        K.EN: "When the shadows of the texture latitude cannot be measured "
              "yet: the developer exports are missing (they are measured "
              "when analyzing the development).",
        K.CA: "Quan les ombres de la latitud de textures encara no es poden "
              "mesurar: falten les exportacions del revelador (es mesuren en "
              "analitzar el revelat)."},
    _L.C_TEXTO_SATURADO: {
        K.ES: "Marca de señal/ruido sin medir porque el canal está "
              "saturado (dispersión 0): no es un dato que falte.",
        K.EN: "Mark of a signal/noise not measured because the channel is "
              "saturated (dispersion 0): not missing data.",
        K.CA: "Marca de senyal/soroll sense mesurar perquè el canal està "
              "saturat (dispersió 0): no és una dada que falte."},
    _L.C_TEXTO_PUNTO: {K.ES: "Marca de las zonas que son puntos de la "
                             "curva.",
                       K.EN: "Mark of the zones that are curve points.",
                       K.CA: "Marca de les zones que són punts de la "
                             "corba."},
    _L.C_LUZ_POR_TERCIO: {K.ES: "Cociente de luz entre dos tercios "
                                "seguidos. Se calcula con las constantes "
                                "anteriores.",
                          K.EN: "Light ratio between two consecutive "
                                "thirds. Calculated from the constants "
                                "above.",
                          K.CA: "Quocient de llum entre dos terços "
                                "seguits. Es calcula amb les constants "
                                "anteriors."},
    _L.C_LUZ_ZV: {K.ES: "Luminancia relativa de la ZV, calculada a partir "
                        "de su L*.",
                  K.EN: "Relative luminance of the ZV, calculated from its "
                        "L*.",
                  K.CA: "Luminància relativa de la ZV, calculada a partir "
                        "de la seua L*."},

    # --- Valores de las constantes de texto (las fórmulas los usan)
    _L.V_RECORTADO: {K.ES: "SÍ", K.EN: "YES", K.CA: "SÍ"},
    _L.V_NO_RECORTADO: {K.ES: "NO", K.EN: "NO", K.CA: "NO"},
    _L.V_NINGUNO: {K.ES: "ninguno", K.EN: "none", K.CA: "cap"},
    _L.V_NO_ALCANZADO: {K.ES: "no alcanzado", K.EN: "not reached",
                        K.CA: "no assolit"},
    _L.V_SIN_REVELADO: {K.ES: "sin revelado", K.EN: "no development",
                        K.CA: "sense revelat"},
    _L.V_SATURADO: {K.ES: "saturado", K.EN: "saturated",
                    K.CA: "saturat"},
    _L.V_PUNTO: {K.ES: "●", K.EN: "●", K.CA: "●"},

    # --- Nota de {snr_minima} (su valor va entre «antes» y «después»)
    _L.T_NOTA_SNR_ANTES: {K.ES: "Nota sobre {snr_minima}: ",
                          K.EN: "Note on {snr_minima}: ",
                          K.CA: "Nota sobre {snr_minima}: "},
    _L.T_NOTA_SNR_TRAS: {K.ES: " es una sugerencia, no un resultado.",
                         K.EN: " is a suggestion, not a result.",
                         K.CA: " és un suggeriment, no un resultat."},
    _L.T_NOTA_SNR_ISO: {
        K.ES: "Viene de ISO 12232: 10:1 es calidad «aceptable» y 40:1, "
              "«excelente», medidas sobre copias impresas.",
        K.EN: "It comes from ISO 12232: 10:1 is “acceptable” quality and "
              "40:1, “excellent”, measured on printed copies.",
        K.CA: "Ve de la ISO 12232: 10:1 és qualitat «acceptable» i 40:1, "
              "«excel·lent», mesures sobre còpies impreses."},
    _L.T_NOTA_SNR_USUARIO: {
        K.ES: "Es el criterio del método; para estudiar otro, use una "
              "copia del libro.",
        K.EN: "It is the method's criterion; to study another one, use a "
              "copy of the workbook.",
        K.CA: "És el criteri del mètode; per a estudiar-ne un altre, useu "
              "una còpia del llibre."},

    # --- Hoja Datos
    _L.T_TITULO_DATOS: {K.ES: "Datos de la serie", K.EN: "Series data",
                        K.CA: "Dades de la sèrie"},
    _L.T_NOTA_DATOS: {
        K.ES: "Lo leído de los RAW, en orden de zonas. Sin cálculos salvo "
              "la media de las Z-V y los tercios estimados del L* del "
              "revelador.",
        K.EN: "What was read from the RAW files, in zone order. No "
              "calculations except the Z-V average and the estimated "
              "thirds of the developer L*.",
        K.CA: "El que s'ha llegit dels RAW, en ordre de zones. Sense "
              "càlculs llevat de la mitjana de les Z-V i dels terços "
              "estimats del L* del revelador."},
    _L.T_SERIE_ZONAS: {K.ES: "Serie por zonas", K.EN: "Series by zone",
                       K.CA: "Sèrie per zones"},
    _L.T_CAB_ZONA: {K.ES: "Zona", K.EN: "Zone", K.CA: "Zona"},
    _L.T_CAB_TERCIOS: {K.ES: "Tercios", K.EN: "Thirds", K.CA: "Terços"},
    _L.T_CAB_ARCHIVO: {K.ES: "Archivo", K.EN: "File", K.CA: "Arxiu"},
    _L.T_CAB_ROJO: {K.ES: "Rojo", K.EN: "Red", K.CA: "Roig"},
    _L.T_CAB_VERDE: {K.ES: "Verde", K.EN: "Green", K.CA: "Verd"},
    _L.T_CAB_AZUL: {K.ES: "Azul", K.EN: "Blue", K.CA: "Blau"},
    _L.T_CAB_DISP_ROJO: {K.ES: "Dispersión rojo", K.EN: "Red dispersion",
                         K.CA: "Dispersió roig"},
    _L.T_CAB_DISP_VERDE: {K.ES: "Dispersión verde",
                          K.EN: "Green dispersion",
                          K.CA: "Dispersió verd"},
    _L.T_CAB_DISP_AZUL: {K.ES: "Dispersión azul", K.EN: "Blue dispersion",
                         K.CA: "Dispersió blau"},
    _L.T_CONTROL: {K.ES: "Z-V de control (las demás Z-V de la serie)",
                   K.EN: "Control Z-V (the other Z-V of the series)",
                   K.CA: "Z-V de control (les altres Z-V de la sèrie)"},
    _L.T_MEDIA_ZV: {K.ES: "Z-V (media de todas)", K.EN: "Z-V (average of "
                    "all)", K.CA: "Z-V (mitjana de totes)"},
    _L.T_MEDIA: {K.ES: "media", K.EN: "average", K.CA: "mitjana"},
    _L.T_RUIDO: {K.ES: "Ruido de lectura (niveles)",
                 K.EN: "Read noise (levels)",
                 K.CA: "Soroll de lectura (nivells)"},
    _L.T_CAB_ORIGEN: {K.ES: "Origen", K.EN: "Source", K.CA: "Origen"},
    _L.T_ORIGEN_BORDE: {K.ES: "Ruido: franja oscura del sensor",
                        K.EN: "Noise: dark strip of the sensor",
                        K.CA: "Soroll: franja fosca del sensor"},
    _L.T_SIN_BORDE: {K.ES: "Ruido: sensor sin franja oscura",
                     K.EN: "Noise: sensor without dark strip",
                     K.CA: "Soroll: sensor sense franja fosca"},
    _L.T_REVELADOR: {K.ES: "L* del revelador, por zona",
                     K.EN: "Developer L*, by zone",
                     K.CA: "L* del revelador, per zona"},
    _L.T_NOTA_REVELADOR: {
        K.ES: "Lee el L* leído de Análisis (a mano o de las exportaciones "
              "del revelador). Un tercio sin él se estima entre las dos "
              "zonas enteras vecinas. Al lado, el contraste de la trama del "
              "paño medido en cada exportación (en blanco sin ella).",
        K.EN: "Reads the L* read from Analysis (by hand or from the "
              "developer exports). A third without it is estimated between "
              "the two neighbouring whole zones. Next to it, the cloth "
              "weave's contrast measured in each export (blank without it).",
        K.CA: "Llig el L* llegit d'Anàlisi (a mà o de les exportacions del "
              "revelador). Un terç sense ell s'estima entre les dues zones "
              "senceres veïnes. Al costat, el contrast de la trama del drap "
              "mesurat en cada exportació (en blanc sense ella)."},
    _L.T_CAB_REVELADOR: {K.ES: "L* del revelador", K.EN: "Developer L*",
                         K.CA: "L* del revelador"},
    _L.T_CAB_CONTRASTE: {K.ES: "Contraste del paño (L*)",
                         K.EN: "Cloth contrast (L*)",
                         K.CA: "Contrast del drap (L*)"},

    # --- Hoja Cálculo
    _L.T_TITULO_CALCULO: {K.ES: "Cálculo", K.EN: "Calculation",
                          K.CA: "Càlcul"},
    _L.T_NOTA_CALCULO: {
        K.ES: "Lee de Datos y de Constantes. No guarda datos propios.",
        K.EN: "Reads from Data and Constants. Stores no data of its own.",
        K.CA: "Llig de Dades i de Constants. No guarda dades pròpies."},
    _L.T_POR_CANAL: {K.ES: "1. Por canal", K.EN: "1. By channel",
                     K.CA: "1. Per canal"},
    _L.T_NOTA_POR_CANAL: {
        K.ES: "Una fila por canal. Zonas, salvo el máximo y la Z-V "
              "(niveles) y la latitud (número de zonas).",
        K.EN: "One row per channel. Zones, except the maximum and the Z-V "
              "(levels) and the latitude (number of zones).",
        K.CA: "Una fila per canal. Zones, llevat del màxim i la Z-V "
              "(nivells) i la latitud (nombre de zones)."},
    _L.T_NOTA_LATITUD: {
        K.ES: "Los tres suelos salen de la curva de transferencia (Datos), "
              "con la señal/ruido normalizada a {mpx_referencia}: dónde "
              "llega a {ratio_sr}, {snr_minima} y {snr_excelente}. Pueden "
              "caer por debajo de Z0: el modelo los extrapola. Latitud "
              "sugerida = último punto lineal − suelo sugerido "
              "({snr_minima}) + {ancho_zona}: cuenta las zonas que caben, "
              "con las dos puntas. Es asimétrica a propósito: arriba manda "
              "la linealidad y abajo la señal/ruido.",
        K.EN: "The three floors come from the transfer curve (Data), with "
              "the signal/noise normalized to {mpx_referencia}: where it "
              "reaches {ratio_sr}, {snr_minima} and {snr_excelente}. They "
              "may fall below Z0: the model extrapolates them. Suggested "
              "latitude = last linear point − suggested floor "
              "({snr_minima}) + {ancho_zona}: it counts the zones that fit, "
              "both ends included. It is asymmetric on purpose: linearity "
              "rules at the top and signal/noise at the bottom.",
        K.CA: "Els tres sòls ixen de la corba de transferència (Dades), "
              "amb el senyal/soroll normalitzat a {mpx_referencia}: on "
              "arriba a {ratio_sr}, {snr_minima} i {snr_excelente}. Poden "
              "caure per davall de Z0: el model els extrapola. Latitud "
              "suggerida = últim punt lineal − sòl suggerit ({snr_minima}) "
              "+ {ancho_zona}: compta les zones que hi caben, amb les dues "
              "puntes. És asimètrica a propòsit: dalt mana la linealitat i "
              "baix el senyal/soroll."},
    _L.T_CAB_CANAL: {K.ES: "Canal", K.EN: "Channel", K.CA: "Canal"},
    _L.T_CAB_ZV_MEDIA: {K.ES: "Z-V (media)", K.EN: "Z-V (average)",
                        K.CA: "Z-V (mitjana)"},
    _L.T_CAB_MAX: {K.ES: "Máximo", K.EN: "Maximum", K.CA: "Màxim"},
    _L.T_CAB_TECHO: {K.ES: "Techo", K.EN: "Ceiling", K.CA: "Sostre"},
    _L.T_CAB_SUELO: {K.ES: "Suelo ({ratio_sr})",
                     K.EN: "Floor ({ratio_sr})",
                     K.CA: "Sòl ({ratio_sr})"},
    _L.T_CAB_RANGO: {K.ES: "Rango", K.EN: "Range", K.CA: "Rang"},
    _L.T_CAB_LINEAL: {K.ES: "Último punto lineal", K.EN: "Last linear point",
                      K.CA: "Últim punt lineal"},
    _L.T_CAB_RECORTADO: {K.ES: "Primer punto recortado",
                         K.EN: "First clipped point",
                         K.CA: "Primer punt retallat"},
    _L.T_CAB_SUELO_SNR: {K.ES: "Suelo sugerido ({snr_minima})",
                         K.EN: "Suggested floor ({snr_minima})",
                         K.CA: "Sòl suggerit ({snr_minima})"},
    _L.T_CAB_SUELO_EXCELENTE: {K.ES: "Suelo excelente ({snr_excelente})",
                               K.EN: "Excellent floor ({snr_excelente})",
                               K.CA: "Sòl excel·lent ({snr_excelente})"},
    _L.T_CAB_LATITUD: {K.ES: "Latitud sugerida", K.EN: "Suggested latitude",
                       K.CA: "Latitud suggerida"},
    _L.T_POR_TERCIO: {K.ES: "2. Por tercio de zona", K.EN: "2. By third of "
                      "a zone", K.CA: "2. Per terç de zona"},
    _L.T_NOTA_POR_TERCIO: {
        K.ES: "Una fila por zona, en el orden de Datos. Techo, suelo y los "
              "umbrales de señal/ruido son referencias para dibujar los "
              "gráficos. Señal/ruido: la de un píxel; «8 Mpx», normalizada "
              "a {mpx_referencia} (comparable entre cámaras); el modelo, la "
              "de la curva de transferencia.",
        K.EN: "One row per zone, in the order of Data. Ceiling, floor and "
              "the signal/noise thresholds are references to draw the "
              "charts. Signal/noise: a pixel's; “8 Mpx”, normalized to "
              "{mpx_referencia} (comparable between cameras); the model, the "
              "transfer curve's.",
        K.CA: "Una fila per zona, en l'ordre de Dades. Sostre, sòl i els "
              "llindars de senyal/soroll són referències per a dibuixar "
              "els gràfics. Senyal/soroll: el d'un píxel; «8 Mpx», "
              "normalitzat a {mpx_referencia} (comparable entre càmeres); el "
              "model, el de la corba de transferència."},
    _L.T_CAB_ESPERADO: {K.ES: "Esperado", K.EN: "Expected",
                        K.CA: "Esperat"},
    _L.T_CAB_OBTENIDO_ROJO: {K.ES: "Obtenido rojo", K.EN: "Obtained red",
                             K.CA: "Obtingut roig"},
    _L.T_CAB_OBTENIDO_VERDE: {K.ES: "Obtenido verde", K.EN: "Obtained green",
                              K.CA: "Obtingut verd"},
    _L.T_CAB_OBTENIDO_AZUL: {K.ES: "Obtenido azul", K.EN: "Obtained blue",
                             K.CA: "Obtingut blau"},
    _L.T_CAB_DESV_ROJO: {K.ES: "Desviación rojo", K.EN: "Red deviation",
                         K.CA: "Desviació roig"},
    _L.T_CAB_DESV_VERDE: {K.ES: "Desviación verde", K.EN: "Green deviation",
                          K.CA: "Desviació verd"},
    _L.T_CAB_DESV_AZUL: {K.ES: "Desviación azul", K.EN: "Blue deviation",
                         K.CA: "Desviació blau"},
    _L.T_CAB_REC_ROJO: {K.ES: "Recortado rojo", K.EN: "Red clipped",
                        K.CA: "Retallat roig"},
    _L.T_CAB_REC_VERDE: {K.ES: "Recortado verde", K.EN: "Green clipped",
                         K.CA: "Retallat verd"},
    _L.T_CAB_REC_AZUL: {K.ES: "Recortado azul", K.EN: "Blue clipped",
                        K.CA: "Retallat blau"},
    _L.T_CAB_SNR_ROJO: {K.ES: "Señal/ruido rojo", K.EN: "Red signal/noise",
                        K.CA: "Senyal/soroll roig"},
    _L.T_CAB_SNR_VERDE: {K.ES: "Señal/ruido verde",
                         K.EN: "Green signal/noise",
                         K.CA: "Senyal/soroll verd"},
    _L.T_CAB_SNR_AZUL: {K.ES: "Señal/ruido azul", K.EN: "Blue signal/noise",
                        K.CA: "Senyal/soroll blau"},
    _L.T_CAB_FALTA_VERDE: {K.ES: "Falta (verde)", K.EN: "Shortfall (green)",
                           K.CA: "Falta (verd)"},
    _L.T_CAB_TECHO_VERDE: {K.ES: "Techo (verde)", K.EN: "Ceiling (green)",
                           K.CA: "Sostre (verd)"},
    _L.T_CAB_SUELO_VERDE: {K.ES: "Suelo (verde)", K.EN: "Floor (green)",
                           K.CA: "Sòl (verd)"},
    _L.T_CAB_SNR_SUGERIDA: {K.ES: "Señal/ruido sugerida",
                            K.EN: "Suggested signal/noise",
                            K.CA: "Senyal/soroll suggerida"},
    _L.T_CAB_SNR8_ROJO: {K.ES: "Señal/ruido rojo (8 Mpx)",
                         K.EN: "Red signal/noise (8 Mpx)",
                         K.CA: "Senyal/soroll roig (8 Mpx)"},
    _L.T_CAB_SNR8_VERDE: {K.ES: "Señal/ruido verde (8 Mpx)",
                          K.EN: "Green signal/noise (8 Mpx)",
                          K.CA: "Senyal/soroll verd (8 Mpx)"},
    _L.T_CAB_SNR8_AZUL: {K.ES: "Señal/ruido azul (8 Mpx)",
                         K.EN: "Blue signal/noise (8 Mpx)",
                         K.CA: "Senyal/soroll blau (8 Mpx)"},
    _L.T_CAB_SNR_MODELO: {K.ES: "Modelo verde (8 Mpx)",
                          K.EN: "Green model (8 Mpx)",
                          K.CA: "Model verd (8 Mpx)"},
    _L.T_CAB_SNR_EXCELENTE: {K.ES: "Señal/ruido excelente",
                             K.EN: "Excellent signal/noise",
                             K.CA: "Senyal/soroll excel·lent"},
    _L.T_CAB_SNR_ING: {K.ES: "Señal/ruido de ingeniería",
                       K.EN: "Engineering signal/noise",
                       K.CA: "Senyal/soroll d'enginyeria"},
    _L.T_CURVA: {K.ES: "3. Curva tonal por zona (L*)",
                 K.EN: "3. Tone curve by zone (L*)",
                 K.CA: "3. Corba tonal per zona (L*)"},
    _L.T_NOTA_CURVA_ANTES: {
        K.ES: "Esperado: ZV en L* 50, un paso de luz por zona (la escena; "
              "el sensor se compara con él). Objetivo: 10 L* por zona, ZX "
              "en 100 (el destino del revelado; el revelador se compara con "
              "él). Sensor: de los datos de la serie. Revelador: de Datos "
              "(el L* leído o, en un tercio sin él, estimado). Entrada (el "
              "revelador) y salida (el objetivo) de la curva de Lightroom "
              "(0 a 255). Comprobación: el parche ZV debe leer ",
        K.EN: "Expected: ZV at L* 50, one light step per zone (the scene; "
              "the sensor is compared with it). Target: 10 L* per zone, ZX "
              "at 100 (where the development should land; the developer is "
              "compared with it). Sensor: from the series data. Developer: "
              "from Data (the L* read or, in a third without it, "
              "estimated). Lightroom curve input (the developer) and output "
              "(the target), 0 to 255. Check: the ZV patch must read ",
        K.CA: "Esperat: ZV en L* 50, un pas de llum per zona (l'escena; el "
              "sensor es compara amb ell). Objectiu: 10 L* per zona, ZX en "
              "100 (el destí del revelat; el revelador es compara amb ell). "
              "Sensor: de les dades de la sèrie. Revelador: de Dades (el L* "
              "llegit o, en un terç sense ell, estimat). Entrada (el "
              "revelador) i eixida (l'objectiu) de la corba de Lightroom (0 "
              "a 255). Comprovació: el pegat ZV ha de llegir "},
    _L.T_NOTA_CURVA_MEDIO: {K.ES: " % en Revelar (", K.EN: "% in Develop (",
                            K.CA: " % en Revelar ("},
    _L.T_NOTA_CURVA_TRAS: {K.ES: ").", K.EN: ").", K.CA: ")."},
    _L.T_CAB_LUZ_ESPERADA: {K.ES: "Luz esperada", K.EN: "Expected light",
                            K.CA: "Llum esperada"},
    _L.T_CAB_L_ESPERADO: {K.ES: "Esperado (L*)", K.EN: "Expected (L*)",
                          K.CA: "Esperat (L*)"},
    _L.T_CAB_L_OBJETIVO: {K.ES: "Objetivo (L*)", K.EN: "Target (L*)",
                          K.CA: "Objectiu (L*)"},
    _L.T_CAB_LUZ_SENSOR: {K.ES: "Luz del sensor", K.EN: "Sensor light",
                          K.CA: "Llum del sensor"},
    _L.T_CAB_L_SENSOR: {K.ES: "Sensor (L*)", K.EN: "Sensor (L*)",
                        K.CA: "Sensor (L*)"},
    # --- Diferencias: cada una, con lo que resta (el sensor, el esperado;
    #     el revelador, el objetivo), en la segunda línea
    _L.T_CAB_DIF_SENSOR: {K.ES: "Dif. sensor\n(− esperado)",
                          K.EN: "Sensor diff.\n(− expected)",
                          K.CA: "Dif. sensor\n(− esperat)"},
    _L.T_CAB_L_REVELADOR: {K.ES: "Revelador (L*)", K.EN: "Developer (L*)",
                           K.CA: "Revelador (L*)"},
    _L.T_CAB_LUZ_REVELADOR: {K.ES: "Luz del revelador",
                             K.EN: "Developer light",
                             K.CA: "Llum del revelador"},
    _L.T_CAB_DIF_REVELADOR: {K.ES: "Dif. revelador\n(− objetivo)",
                             K.EN: "Developer diff.\n(− target)",
                             K.CA: "Dif. revelador\n(− objectiu)"},
    _L.T_CAB_FALTA: {K.ES: "Falta", K.EN: "Shortfall", K.CA: "Falta"},
    _L.T_CAB_SOBRA: {K.ES: "Sobra", K.EN: "Excess", K.CA: "Sobra"},
    # --- Tu curva (bloque 3 de Cálculo, a la derecha)
    _L.T_CAB_TU_DESDE_ENTRADA: {K.ES: "Desde\n(entrada)",
                                K.EN: "From\n(input)",
                                K.CA: "Des de\n(entrada)"},
    _L.T_CAB_TU_DESDE_SALIDA: {K.ES: "Desde\n(salida)",
                               K.EN: "From\n(output)",
                               K.CA: "Des de\n(eixida)"},
    _L.T_CAB_TU_HASTA_ENTRADA: {K.ES: "Hasta\n(entrada)",
                                K.EN: "To\n(input)",
                                K.CA: "Fins a\n(entrada)"},
    _L.T_CAB_TU_HASTA_SALIDA: {K.ES: "Hasta\n(salida)",
                               K.EN: "To\n(output)",
                               K.CA: "Fins a\n(eixida)"},
    _L.T_CAB_TU_SALIDA: {K.ES: "Tu salida\n(0-255)",
                         K.EN: "Your output\n(0-255)",
                         K.CA: "La teua eixida\n(0-255)"},
    _L.T_CAB_TU_L: {K.ES: "Tu curva (L*)", K.EN: "Your curve (L*)",
                    K.CA: "La teua corba (L*)"},
    _L.T_CAB_TU_DIF: {K.ES: "Dif. tu curva\n(− objetivo)",
                      K.EN: "Your curve diff.\n(− target)",
                      K.CA: "Dif. la teua corba\n(− objectiu)"},
    _L.T_CAB_TU_PUNTO_ENTRADA: {K.ES: "Tu punto\n(entrada)",
                                K.EN: "Your point\n(input)",
                                K.CA: "El teu punt\n(entrada)"},
    _L.T_CAB_TU_PUNTO_SALIDA: {K.ES: "Tu punto\n(salida)",
                               K.EN: "Your point\n(output)",
                               K.CA: "El teu punt\n(eixida)"},
    # --- Entrada y salida: el rango, siempre en la segunda línea (así las
    #     dos cabeceras quedan alineadas)
    _L.T_CAB_ENTRADA: {K.ES: "Entrada\n(0-255)", K.EN: "Input\n(0-255)",
                       K.CA: "Entrada\n(0-255)"},
    _L.T_CAB_SALIDA: {K.ES: "Salida\n(0-255)", K.EN: "Output\n(0-255)",
                      K.CA: "Eixida\n(0-255)"},
    _L.T_CAB_PUNTO: {K.ES: "Punto de la curva", K.EN: "Curve point",
                     K.CA: "Punt de la corba"},

    # --- Hoja Análisis
    _L.T_TITULO_RESUMEN: {K.ES: "Análisis de cámara",
                          K.EN: "Camera analysis",
                          K.CA: "Anàlisi de càmera"},
    _L.T_MARCA_MODELO: {K.ES: "Marca y modelo", K.EN: "Make and model",
                        K.CA: "Marca i model"},
    _L.T_FECHA: {K.ES: "Fecha", K.EN: "Date", K.CA: "Data"},
    _L.T_BITS: {K.ES: "Profundidad RAW", K.EN: "RAW bit depth",
                K.CA: "Profunditat RAW"},
    _L.T_FORMATO_FECHA: {K.ES: "[$-C0A]d\\-mmm\\-yyyy;@",
                         K.EN: "[$-409]d\\-mmm\\-yyyy;@",
                         K.CA: "[$-403]d\\-mmm\\-yyyy;@"},
    _L.T_ZV: {K.ES: "ZV", K.EN: "ZV", K.CA: "ZV"},
    _L.T_ISO: {K.ES: "ISO", K.EN: "ISO", K.CA: "ISO"},
    _L.T_TV: {K.ES: "Tv", K.EN: "Tv", K.CA: "Tv"},
    _L.T_F: {K.ES: "f/", K.EN: "f/", K.CA: "f/"},
    _L.T_SUGERENCIA: {K.ES: "Sugerencia de revelado para contraste CIELab",
                      K.EN: "Development suggestion for CIELab contrast",
                      K.CA: "Suggeriment de revelat per a contrast "
                            "CIELab"},
    _L.T_REFERENCIA: {
        K.ES: "Referencia: ISO/CIE 11664-4:2019, Colorimetría, parte 4: "
              "espacio de color CIE 1976 L*a*b*.",
        K.EN: "Reference: ISO/CIE 11664-4:2019, Colorimetry, part 4: CIE "
              "1976 L*a*b* colour space.",
        K.CA: "Referència: ISO/CIE 11664-4:2019, Colorimetria, part 4: "
              "espai de color CIE 1976 L*a*b*."},
    _L.T_ES_SUGERENCIA: {
        K.ES: "Es una sugerencia: la decisión se toma comparando con la "
              "lámina impresa.",
        K.EN: "It is a suggestion: the decision is made by comparing with "
              "the printed sheet.",
        K.CA: "És un suggeriment: la decisió es pren comparant amb la "
              "làmina impresa."},
    _L.T_SUGERIDO: {
        K.ES: "Sugerido: punto de la curva de tonos de Lightroom (curva de "
              "puntos RGB), con entrada y salida de 0 a 255. Entrada = L* "
              "del revelador y salida = L* objetivo (10 L* por zona). Ponga "
              "Perfeccionar "
              "saturación a 0 para que la curva cambie solo la luminosidad. "
              "La curva admite 16 puntos: use las zonas enteras.",
        K.EN: "Suggested: point of the Lightroom tone curve (RGB point "
              "curve), with input and output from 0 to 255. Input = "
              "developer L* and output = target L* (10 L* per zone). Set "
              "Refine Saturation "
              "to 0 so the curve only changes lightness. The curve accepts "
              "16 points: use the whole zones.",
        K.CA: "Suggerit: punt de la corba de tons de Lightroom (corba de "
              "punts RGB), amb entrada i eixida de 0 a 255. Entrada = L* "
              "del revelador i eixida = L* objectiu (10 L* per zona). Poseu "
              "Perfeccionar "
              "saturació a 0 perquè la corba canvie només la lluminositat. "
              "La corba admet 16 punts: useu les zones senceres."},
    _L.T_DIF_MEDIA_SENSOR: {K.ES: "Diferencia media del sensor (− esperado)",
                            K.EN: "Sensor average difference (− expected)",
                            K.CA: "Diferència mitjana del sensor (− esperat)"},
    _L.T_DIF_MEDIA_REVELADOR: {
        K.ES: "Diferencia media del revelador (− objetivo)",
        K.EN: "Developer average difference (− target)",
        K.CA: "Diferència mitjana del revelador (− objectiu)"},
    _L.T_DIF_MEDIA_TU: {
        K.ES: "Diferencia media con tu curva (− objetivo)",
        K.EN: "Average difference with your curve (− target)",
        K.CA: "Diferència mitjana amb la teua corba (− objectiu)"},
    _L.T_SIN_REVELADOR: {
        K.ES: "Sin L* leído (a mano o de las exportaciones del revelador): "
              "su diferencia, la entrada y la salida salen en blanco. El "
              "sensor, casi 0 en los medios, es el resultado: no un fallo.",
        K.EN: "Without L* read (by hand or from the developer exports): its "
              "difference, the input and the output are blank. The sensor, "
              "almost 0 in the middle tones, is the result: not a fault.",
        K.CA: "Sense L* llegit (a mà o de les exportacions del revelador): "
              "la seua diferència, l'entrada i l'eixida ixen en blanc. El "
              "sensor, quasi 0 en els mitjos, és el resultat: no una "
              "fallada."},
    _L.T_CAB_L_APUNTADO: {K.ES: "L* leído", K.EN: "L* read",
                          K.CA: "L* llegit"},
    _L.T_ESTIMADO: {
        K.ES: "En color: estimado entre las dos zonas enteras vecinas, "
              "porque ese tercio no tiene L* leído.",
        K.EN: "In colour: estimated between the two neighbouring whole "
              "zones, because that third has no L* read.",
        K.CA: "En color: estimat entre les dues zones senceres veïnes, "
              "perquè eixe terç no té L* llegit."},
    _L.T_BALANCES: {K.ES: "Balances de blancos", K.EN: "White balances",
                    K.CA: "Balanços de blancs"},
    _L.T_NOTA_BALANCES: {
        K.ES: "Kelvin anotado: el que la cámara guarda en el RAW. Kelvin "
              "medido: el de la luz que sus multiplicadores dejan neutra, "
              "el que de verdad aplica. Los balances iguales, una sola vez.",
        K.EN: "Recorded Kelvin: the one the camera stores in the RAW. "
              "Measured Kelvin: that of the light its multipliers make "
              "neutral, the one really applied. Identical balances, only "
              "once.",
        K.CA: "Kelvin anotat: el que la càmera guarda en el RAW. Kelvin "
              "mesurat: el de la llum que els seus multiplicadors deixen "
              "neutra, el que de veritat aplica. Els balanços iguals, una "
              "sola volta."},
    _L.T_SIN_BALANCES: {K.ES: "Sin tomas de balance de la cámara.",
                        K.EN: "No camera white balance shots.",
                        K.CA: "Sense preses de balanç de la càmera."},
    _L.T_CAB_BALANCE: {K.ES: "Balance", K.EN: "Balance", K.CA: "Balanç"},
    _L.T_CAB_KELVIN_ANOTADO: {K.ES: "Kelvin anotado",
                              K.EN: "Recorded Kelvin",
                              K.CA: "Kelvin anotat"},
    _L.T_CAB_KELVIN_MEDIDO: {K.ES: "Kelvin medido", K.EN: "Measured Kelvin",
                             K.CA: "Kelvin mesurat"},
    _L.T_CAB_MULT_ROJO: {K.ES: "Multiplicador rojo",
                         K.EN: "Red multiplier",
                         K.CA: "Multiplicador roig"},
    _L.T_CAB_MULT_AZUL: {K.ES: "Multiplicador azul",
                         K.EN: "Blue multiplier",
                         K.CA: "Multiplicador blau"},

    # --- Ruido y negro
    _L.T_COMPARAR_TAPADAS: {
        K.ES: "Ruido: superficie real del sensor (tapadas)",
        K.EN: "Noise: actual sensor surface (covered)",
        K.CA: "Soroll: superfície real del sensor (tapades)"},
    _L.T_NEGRO_TAPADAS: {K.ES: "Negro digital (tapadas)",
                         K.EN: "Digital black (covered)",
                         K.CA: "Negre digital (tapades)"},
    _L.T_NEGRO_SOMBRAS: {K.ES: "Negro digital (estimado en las sombras)",
                         K.EN: "Digital black (estimated from shadows)",
                         K.CA: "Negre digital (estimat en les ombres)"},
    _L.T_NEGRO_DECLARADO: {K.ES: "Negro digital (declarado)",
                           K.EN: "Digital black (declared)",
                           K.CA: "Negre digital (declarat)"},

    # --- Ruido aceptable por color (Análisis y PDF)
    _L.T_RUIDO_COLOR: {K.ES: "Ruido aceptable por color",
                       K.EN: "Acceptable noise per color",
                       K.CA: "Soroll acceptable per color"},
    # --- Lo mismo con el ISO de la serie (Tony, 2026-11-13). EN y CA, de
    #     Claude a petición de Tony
    _L.T_RUIDO_COLOR_ISO: {K.ES: "Ruido aceptable por color a ISO {iso}",
                           K.EN: "Acceptable noise per color at ISO {iso}",
                           K.CA: "Soroll acceptable per color a ISO {iso}"},
    _L.T_RUIDO_COLOR_NOTA: {K.ES: "Señal/ruido ≥ {umbral}",
                            K.EN: "Signal/noise ≥ {umbral}",
                            K.CA: "Senyal/soroll ≥ {umbral}"},
    _L.T_RUIDO_COLOR_TODO: {
        K.ES: "{canal}: ruido aceptable en todo el rango.",
        K.EN: "{canal}: acceptable noise across the whole range.",
        K.CA: "{canal}: soroll acceptable en tot el rang."},
    _L.T_RUIDO_COLOR_DESDE: {K.ES: "{canal}: aceptable desde {zona}.",
                             K.EN: "{canal}: acceptable from {zona}.",
                             K.CA: "{canal}: acceptable des de {zona}."},
    _L.T_RUIDO_COLOR_NUNCA: {
        K.ES: "{canal}: en ninguna zona medida el ruido llega a ser "
              "aceptable.",
        K.EN: "{canal}: noise is not acceptable in any measured zone.",
        K.CA: "{canal}: en cap zona mesurada el soroll arriba a ser "
              "acceptable."},

    # --- Píxeles defectuosos (Datos, Análisis y PDF)
    _L.T_PIXELES: {K.ES: "Píxeles defectuosos", K.EN: "Defective pixels",
                   K.CA: "Píxels defectuosos"},
    _L.T_PIXELES_CALIENTES: {
        K.ES: "Calientes: {n} ({por_mpx} por Mpx)",
        K.EN: "Hot: {n} ({por_mpx} per Mpx)",
        K.CA: "Calents: {n} ({por_mpx} per Mpx)"},
    _L.T_PIXELES_MUERTOS: {
        K.ES: "Muertos: {n} ({por_mpx} por Mpx)",
        K.EN: "Dead: {n} ({por_mpx} per Mpx)",
        K.CA: "Morts: {n} ({por_mpx} per Mpx)"},
    _L.T_PIXELES_SIN_CALIENTES: {K.ES: "Calientes: ninguno",
                                 K.EN: "Hot: none",
                                 K.CA: "Calents: cap"},
    _L.T_PIXELES_SIN_MUERTOS: {K.ES: "Muertos: ninguno",
                               K.EN: "Dead: none",
                               K.CA: "Morts: cap"},
    _L.T_PIXELES_NINGUNO: {
        K.ES: "No hay píxeles defectuosos: ni calientes ni muertos.",
        K.EN: "There are no defective pixels: neither hot nor dead.",
        K.CA: "No hi ha píxels defectuosos: ni calents ni morts."},
    _L.T_PIXELES_SIN_TAPADAS: {
        K.ES: "Sin tomas tapadas no se pueden contar los píxeles calientes.",
        K.EN: "Without covered shots, hot pixels cannot be counted.",
        K.CA: "Sense preses tapades no es poden comptar els píxels "
              "calents."},
    _L.T_RUIDOS_DIFIEREN: {
        K.ES: "El ruido de la franja oscura del sensor y el de la superficie "
              "real (tapadas) no casan: se apartan más del {porcentaje} %.",
        K.EN: "The noise of the sensor's dark strip and that of the actual "
              "surface (covered) do not match: they differ by more than "
              "{porcentaje}%.",
        K.CA: "El soroll de la franja fosca del sensor i el de la "
              "superfície real (tapades) no casen: s'aparten més del "
              "{porcentaje} %."},
    _L.T_SIN_RUIDO_SUELO: {
        K.ES: "Sin franja oscura, tomas tapadas ni zonas bastantes para la "
              "curva de transferencia: no hay ruido de lectura ni suelos.",
        K.EN: "No dark strip, covered shots or enough zones for the "
              "transfer curve: there is no read noise and no floors.",
        K.CA: "Sense franja fosca, preses tapades ni zones prou per a la "
              "corba de transferència: no hi ha soroll de lectura ni "
              "sòls."},
    _L.T_TRANSFERENCIA: {K.ES: "Curva de transferencia del ruido",
                         K.EN: "Noise transfer curve",
                         K.CA: "Corba de transferència del soroll"},
    _L.T_NOTA_TRANSFERENCIA: {
        K.ES: "Ajustada con las zonas sin recorte: ruido² = lectura² + "
              "señal / ganancia + (proporcional × señal)². Aleatorio: de "
              "la Z-V y una de control (misma exposición); fijo: lo que "
              "queda de la dispersión media de las Z-V.",
        K.EN: "Fitted with the unclipped zones: noise² = read² + signal / "
              "gain + (proportional × signal)². Random: from the Z-V and "
              "a control one (same exposure); fixed: what remains of the "
              "average Z-V dispersion.",
        K.CA: "Ajustada amb les zones sense retall: soroll² = lectura² + "
              "senyal / guany + (proporcional × senyal)². Aleatori: de la "
              "Z-V i una de control (mateixa exposició); fix: el que "
              "queda de la dispersió mitjana de les Z-V."},
    _L.T_LECTURA: {K.ES: "Ruido de lectura (niveles)",
                   K.EN: "Read noise (levels)",
                   K.CA: "Soroll de lectura (nivells)"},
    _L.T_GANANCIA: {K.ES: "Ganancia (e⁻ por nivel)",
                    K.EN: "Gain (e⁻ per level)",
                    K.CA: "Guany (e⁻ per nivell)"},
    _L.T_PROPORCIONAL: {K.ES: "Proporcional a la señal",
                        K.EN: "Proportional to signal",
                        K.CA: "Proporcional al senyal"},
    _L.T_ALEATORIO_ZV: {K.ES: "Z-V: aleatorio (dispersión)",
                        K.EN: "Z-V: random (dispersion)",
                        K.CA: "Z-V: aleatori (dispersió)"},
    _L.T_FIJO_ZV: {K.ES: "Z-V: fijo (dispersión)",
                   K.EN: "Z-V: fixed (dispersion)",
                   K.CA: "Z-V: fix (dispersió)"},
    _L.T_MPX_SENSOR: {K.ES: "Sensor (megapíxeles)",
                      K.EN: "Sensor (megapixels)",
                      K.CA: "Sensor (megapíxels)"},

    # --- Hoja Rechazadas
    _L.T_TITULO_RECHAZADAS: {K.ES: "Teselas rechazadas",
                             K.EN: "Rejected tiles",
                             K.CA: "Tessel·les rebutjades"},
    _L.T_NOTA_RECHAZADAS: {
        K.ES: "Teselas de tarjeta gris que los filtros dejan fuera, elegidas "
              "en la Z-V (valen para toda la serie). Solo cuentan las de "
              "tarjeta: no el paño, su margen ni las oscuras. Los filtros "
              "van en orden (nivel, dispersión, asimetría): cada tesela "
              "cuenta solo en el primero que no pasa.",
        K.EN: "Grey card tiles left out by the filters, chosen in the Z-V "
              "(valid for the whole series). Only card tiles count: not the "
              "fabric, its margin or the dark ones. The filters go in "
              "order (level, dispersion, asymmetry): each tile counts only "
              "in the first one it fails.",
        K.CA: "Tessel·les de targeta grisa que els filtres deixen fora, "
              "triades en la Z-V (valen per a tota la sèrie). Només compten "
              "les de targeta: no el drap, el seu marge ni les fosques. "
              "Els filtres van en orde (nivell, dispersió, asimetria): cada "
              "tessel·la compta només en el primer que no passa."},
    _L.T_RECUENTO: {K.ES: "Recuento", K.EN: "Count", K.CA: "Recompte"},
    _L.T_CAB_CONCEPTO: {K.ES: "Concepto", K.EN: "Item", K.CA: "Concepte"},
    _L.T_TESELAS_TARJETA: {K.ES: "Teselas de tarjeta",
                           K.EN: "Card tiles",
                           K.CA: "Tessel·les de targeta"},
    _L.T_TESELAS_RECHAZADAS: {K.ES: "Rechazadas", K.EN: "Rejected",
                              K.CA: "Rebutjades"},
    _L.T_PORCENTAJE: {K.ES: "Porcentaje de las de tarjeta",
                      K.EN: "Percentage of the card tiles",
                      K.CA: "Percentatge de les de targeta"},
    _L.T_POR_MOTIVO: {K.ES: "Rechazadas por {motivo}",
                      K.EN: "Rejected by {motivo}",
                      K.CA: "Rebutjades per {motivo}"},
    _L.T_MOTIVO_NIVEL: {K.ES: "nivel", K.EN: "level", K.CA: "nivell"},
    _L.T_MOTIVO_DISP: {K.ES: "dispersión", K.EN: "dispersion",
                             K.CA: "dispersió"},
    _L.T_MOTIVO_ASIM: {K.ES: "asimetría", K.EN: "asymmetry",
                       K.CA: "asimetria"},
    _L.T_EXPLICA_NIVEL: {
        K.ES: "La tesela recibe más de {nivel} de zona de luz distinta que "
              "la mediana de la tarjeta: luz desigual (viñeteo, una sombra, "
              "un reflejo) o una mancha en la tarjeta.",
        K.EN: "The tile receives more than {nivel} of a zone of light "
              "different from the card's median: uneven light (vignetting, "
              "a shadow, a reflection) or a stain on the card.",
        K.CA: "La tessel·la rep més de {nivel} de zona de llum diferent de "
              "la mediana de la targeta: llum desigual (vinyetatge, una "
              "ombra, un reflex) o una taca en la targeta."},
    _L.T_EXPLICA_DISP: {
        K.ES: "Su dispersión (el ruido dentro de la tesela, de {lado} × "
              "{lado} píxeles) supera a la de las demás en más de {rareza} "
              "desviaciones típicas robustas: polvo, un arañazo, una fibra "
              "o un borde dentro de la tesela. Solo por arriba: una tesela "
              "más lisa no es mala.",
        K.EN: "Its dispersion (the noise inside the tile, {lado} × {lado} "
              "pixels) exceeds the others' by more than {rareza} robust "
              "standard deviations: dust, a scratch, a fibre or an edge "
              "inside the tile. Only upwards: a smoother tile is not bad.",
        K.CA: "La seua dispersió (el soroll dins de la tessel·la, de {lado} "
              "× {lado} píxels) supera la de les altres en més de {rareza} "
              "desviacions típiques robustes: pols, una ratlla, una fibra o "
              "una vora dins de la tessel·la. Només per dalt: una tessel·la "
              "més llisa no és roïna."},
    _L.T_EXPLICA_ASIM: {
        K.ES: "Sus valores no se reparten igual por encima y por debajo de "
              "su mediana (más de {rareza} desviaciones típicas robustas "
              "que las demás). El ruido es simétrico; un defecto pequeño "
              "(una mota, un punto brillante o un píxel caliente) no.",
        K.EN: "Its values are not spread equally above and below its median "
              "(more than {rareza} robust standard deviations from the "
              "others). Noise is symmetric; a small defect (a speck, a "
              "bright dot or a hot pixel) is not.",
        K.CA: "Els seus valors no es repartixen igual per damunt i per davall "
              "de la seua mediana (més de {rareza} desviacions típiques "
              "robustes que les altres). El soroll és simètric; un defecte "
              "xicotet (una mota, un punt brillant o un píxel calent) no."},
    _L.T_G_RECHAZADAS: {
        K.ES: "Desviación de las rechazadas respecto a las aceptadas",
        K.EN: "Deviation of the rejected tiles from the accepted ones",
        K.CA: "Desviació de les rebutjades respecte a les acceptades"},
    _L.T_DATOS_GRAF: {K.ES: "Datos del gráfico (verde, por motivo)",
                      K.EN: "Chart data (green, by reason)",
                      K.CA: "Dades del gràfic (verd, per motiu)"},
    _L.T_CAB_POS: {K.ES: "Posición (zonas)", K.EN: "Position (zones)",
                   K.CA: "Posició (zones)"},
    _L.T_CAB_MOTIVO: {K.ES: "Motivo", K.EN: "Reason", K.CA: "Motiu"},
    _L.T_CAB_DEV: {K.ES: "Desviación (zonas)",
                   K.EN: "Deviation (zones)",
                   K.CA: "Desviació (zones)"},

    # --- Hoja Gráficos
    _L.T_TITULO_GRAF: {K.ES: "Gráficos", K.EN: "Charts",
                       K.CA: "Gràfics"},
    _L.T_NOTA_GRAF: {
        K.ES: "Leen de Cálculo. Datos de la serie de la {cam}. La 3 aplica "
              "al revelado los puntos de tus decisiones propias (Análisis), "
              "unidos en recta: Lightroom traza una curva suave, así que "
              "entre punto y punto puede dar algo distinto.",
        K.EN: "They read from Calculation. Data of the {cam} series. Chart "
              "3 applies the points of your own decisions (Analysis) to the "
              "development, joined by straight lines: Lightroom draws a "
              "smooth curve, so between points it may give something "
              "slightly different.",
        K.CA: "Lligen de Càlcul. Dades de la sèrie de la {cam}. La 3 aplica "
              "al revelat els punts de les teues decisions pròpies "
              "(Anàlisi), units en recta: Lightroom traça una corba suau, "
              "així que entre punt i punt pot donar una cosa un poc "
              "diferent."},
    _L.T_G_ESPERADO: {K.ES: "Esperado y obtenido",
                      K.EN: "Expected and obtained",
                      K.CA: "Esperat i obtingut"},
    _L.T_G_DESV_LINEAL: {K.ES: "Desviación, tramo lineal",
                         K.EN: "Deviation, linear range",
                         K.CA: "Desviació, tram lineal"},
    _L.T_G_DESV_COMPLETA: {K.ES: "Desviación, rango completo",
                           K.EN: "Deviation, full range",
                           K.CA: "Desviació, rang complet"},
    _L.T_G_SNR: {K.ES: "Relación señal/ruido por zona (8 Mpx)",
                 K.EN: "Signal-to-noise ratio by zone (8 Mpx)",
                 K.CA: "Relació senyal/soroll per zona (8 Mpx)"},
    _L.T_G_CURVA: {K.ES: "Curva tonal en L*", K.EN: "Tone curve in L*",
                   K.CA: "Corba tonal en L*"},
    _L.T_G_DIFERENCIA: {K.ES: "Diferencia en L* (− objetivo)",
                        K.EN: "L* difference (− target)",
                        K.CA: "Diferència en L* (− objectiu)"},
    _L.T_G_TU_CURVA: {K.ES: "Tu curva y el objetivo",
                      K.EN: "Your curve and the target",
                      K.CA: "La teua corba i l'objectiu"},
    _L.T_G_BALANCES: {K.ES: "Balances de blancos: Kelvin anotado y medido",
                      K.EN: "White balances: recorded and measured Kelvin",
                      K.CA: "Balanços de blancs: Kelvin anotat i mesurat"},
    _L.T_AUDITORIA: {K.ES: "Gráficas de auditoría (el sensor)",
                     K.EN: "Audit charts (the sensor)",
                     K.CA: "Gràfics d'auditoria (el sensor)"},
    _L.T_EJE_ZONA: {K.ES: "Zona", K.EN: "Zone", K.CA: "Zona"},
    _L.T_EJE_SIGNAL: {K.ES: "Señal en zonas equivalentes",
                      K.EN: "Signal in equivalent zones",
                      K.CA: "Senyal en zones equivalents"},
    _L.T_EJE_PASOS: {K.ES: "Pasos respecto a Z-V",
                     K.EN: "Steps from Z-V",
                     K.CA: "Passos respecte a la Z-V"},
    _L.T_EJE_DEV: {K.ES: "Desviación (zonas)",
                   K.EN: "Deviation (zones)",
                   K.CA: "Desviació (zones)"},
    _L.T_EJE_SNR: {K.ES: "Señal/ruido (veces, escala logarítmica)",
                   K.EN: "Signal/noise (times, log scale)",
                   K.CA: "Senyal/soroll (vegades, escala logarítmica)"},
    _L.T_EJE_LSTAR: {K.ES: "L*", K.EN: "L*", K.CA: "L*"},
    _L.T_EJE_DIF_LSTAR: {K.ES: "Diferencia de L*", K.EN: "L* difference",
                         K.CA: "Diferència de L*"},
    _L.T_EJE_KELVIN: {K.ES: "Kelvin", K.EN: "Kelvin", K.CA: "Kelvin"},
    _L.T_S_MIN: {K.ES: "Mínimo sugerido", K.EN: "Suggested minimum",
                 K.CA: "Mínim suggerit"},
    _L.T_S_EXCELENTE: {K.ES: "Excelente", K.EN: "Excellent",
                       K.CA: "Excel·lent"},
    _L.T_S_ING: {K.ES: "Ingeniería", K.EN: "Engineering",
                 K.CA: "Enginyeria"},
    _L.T_S_MODELO: {K.ES: "Modelo (verde)", K.EN: "Model (green)",
                    K.CA: "Model (verd)"},
    _L.T_S_SENSOR: {K.ES: "Sensor", K.EN: "Sensor", K.CA: "Sensor"},
    _L.T_S_REVELADOR: {K.ES: "Revelador", K.EN: "Developer",
                       K.CA: "Revelador"},
    _L.T_S_TU_CURVA: {K.ES: "Con tu curva", K.EN: "With your curve",
                      K.CA: "Amb la teua corba"},

    # --- Leyenda de los colores del texto
    _L.T_LEYENDA: {K.ES: "Colores del texto", K.EN: "Text colours",
                   K.CA: "Colors del text"},
    _L.T_LEYENDA_DATO: {K.ES: "Dato: azul. Lo leído de los RAW.",
                        K.EN: "Data: blue. What was read from the RAW "
                              "files.",
                        K.CA: "Dada: blau. El que s'ha llegit dels RAW."},
    _L.T_LEYENDA_LITERAL: {K.ES: "Literal: naranja oscuro. Lo escrito por "
                                 "diseño.",
                           K.EN: "Literal: dark orange. What is written by "
                                 "design.",
                           K.CA: "Literal: taronja fosc. El que s'ha escrit "
                                 "per disseny."},
    _L.T_LEYENDA_FORMULA: {K.ES: "Fórmula: negro. Lo que se calcula.",
                           K.EN: "Formula: black. What is calculated.",
                           K.CA: "Fórmula: negre. El que es calcula."},
    _L.T_LEYENDA_ROTULO: {K.ES: "Rótulo o nota: gris.",
                          K.EN: "Label or note: grey.",
                          K.CA: "Rètol o nota: gris."},

    # --- Paño por zona (Datos)
    _L.T_TELA: {K.ES: "Paño por zona", K.EN: "Cloth by zone",
                K.CA: "Drap per zona"},
    _L.T_NOTA_TELA: {
        K.ES: "Lo leído en la ventana del paño de cada toma: dispersión "
              "(relativa) y fracción de sus píxeles recortados, por canal. "
              "Al final, las dispersiones del verde del paño y de la "
              "tarjeta, por píxel, con las que se mide la latitud de "
              "texturas. En blanco si no hay paño.",
        K.EN: "What was read in the cloth window of each shot: dispersion "
              "(relative) and fraction of its clipped pixels, by channel. "
              "Last, the green dispersions of the cloth and the card, per "
              "pixel, used to measure the texture latitude. Blank if there "
              "is no cloth.",
        K.CA: "El que s'ha llegit en la finestra del drap de cada presa: "
              "dispersió (relativa) i fracció dels seus píxels retallats, "
              "per canal. Al final, les dispersions del verd del drap i de "
              "la targeta, per píxel, amb què es mesura la latitud de "
              "textures. En blanc si no hi ha drap."},
    _L.T_CAB_TELA_REC_ROJO: {K.ES: "Recortado rojo", K.EN: "Red clipped",
                             K.CA: "Retallat roig"},
    _L.T_CAB_TELA_REC_VERDE: {K.ES: "Recortado verde", K.EN: "Green clipped",
                              K.CA: "Retallat verd"},
    _L.T_CAB_TELA_REC_AZUL: {K.ES: "Recortado azul", K.EN: "Blue clipped",
                             K.CA: "Retallat blau"},
    _L.T_CAB_TELA_PANTALLA: {K.ES: "Paño verde", K.EN: "Green cloth",
                             K.CA: "Drap verd"},
    _L.T_CAB_TARJETA_PANTALLA: {K.ES: "Tarjeta verde", K.EN: "Green card",
                                K.CA: "Targeta verda"},

    # --- Latitud de texturas (Cálculo, bloque 4, y Análisis)
    _L.T_TEXTURAS: {K.ES: "Latitud de texturas", K.EN: "Texture latitude",
                    K.CA: "Latitud de textures"},
    _L.T_POR_TEXTURA: {K.ES: "4. Latitud de texturas (verde)",
                       K.EN: "4. Texture latitude (green)",
                       K.CA: "4. Latitud de textures (verd)"},
    _L.T_NOTA_TEXTURAS: {
        K.ES: "Sombras, en las exportaciones del revelador: recomendadas, la "
              "primera zona cuyo contraste de la trama del paño llega a "
              "{contraste_sombras} del de la ZV y no vuelve a bajar hasta "
              "ella; apreciables, {margen_sombras} tercios más abajo; sin "
              "exportaciones, {texto_sin_revelado}. Luces, en el canal verde "
              "de los RAW: la última zona, desde la ZV, que conserva "
              "{textura_conservada} de la textura de la ZV sin pasar de "
              "{tela_recortado_apreciable} de paño recortado; recomendadas, "
              "la última sin pasar de {tela_recortado_max} de paño "
              "recortado.",
        K.EN: "Shadows, in the developer exports: recommended, the first "
              "zone whose cloth weave contrast reaches {contraste_sombras} of "
              "the ZV's and does not drop again up to it; visible, "
              "{margen_sombras} thirds lower; without exports, "
              "{texto_sin_revelado}. Highlights, in the green channel of the "
              "RAW files: the last zone, from ZV, that keeps "
              "{textura_conservada} of the ZV texture without exceeding "
              "{tela_recortado_apreciable} of clipped cloth; recommended, "
              "the last one not exceeding {tela_recortado_max} of clipped "
              "cloth.",
        K.CA: "Ombres, en les exportacions del revelador: recomanades, la "
              "primera zona el contrast de la trama del drap de la qual "
              "arriba a {contraste_sombras} del de la ZV i no torna a baixar "
              "fins a ella; apreciables, {margen_sombras} terços més avall; "
              "sense exportacions, {texto_sin_revelado}. Llums, en el canal "
              "verd dels RAW: l'última zona, des de la ZV, que conserva "
              "{textura_conservada} de la textura de la ZV sense passar de "
              "{tela_recortado_apreciable} de drap retallat; recomanades, "
              "l'última sense passar de {tela_recortado_max} de drap "
              "retallat."},
    _L.T_CAB_TEXTURA: {K.ES: "Textura del paño", K.EN: "Cloth texture",
                       K.CA: "Textura del drap"},
    _L.T_CAB_TEXTURA_RUIDO: {K.ES: "Textura/ruido", K.EN: "Texture/noise",
                             K.CA: "Textura/soroll"},
    _L.T_CAB_CONSERVADA: {K.ES: "Textura conservada", K.EN: "Texture kept",
                          K.CA: "Textura conservada"},
    _L.T_CAB_TELA_RECORTADO: {K.ES: "Paño recortado", K.EN: "Cloth clipped",
                              K.CA: "Drap retallat"},
    _L.T_CAB_CUMPLE_SOMBRAS: {K.ES: "Cumple sombras",
                              K.EN: "Meets shadows",
                              K.CA: "Compleix ombres"},
    _L.T_CAB_CUMPLE_LUCES: {K.ES: "Cumple luces", K.EN: "Meets highlights",
                            K.CA: "Compleix llums"},
    _L.T_CAB_SIN_RECORTE: {K.ES: "Cumple recorte", K.EN: "Meets clipping",
                           K.CA: "Compleix retall"},
    _L.T_CAB_CONTRASTE_ZV: {K.ES: "Contraste / ZV", K.EN: "Contrast / ZV",
                            K.CA: "Contrast / ZV"},
    _L.T_CAB_SOMBRAS: {K.ES: "Sombras", K.EN: "Shadows", K.CA: "Ombres"},
    _L.T_CAB_LUCES: {K.ES: "Altas luces", K.EN: "Highlights",
                     K.CA: "Altes llums"},
    _L.T_CAB_LATITUD_TEXTURAS: {K.ES: "Latitud (zonas)",
                                K.EN: "Latitude (zones)",
                                K.CA: "Latitud (zones)"},
    _L.T_APRECIABLE: {K.ES: "Apreciable", K.EN: "Visible",
                      K.CA: "Apreciable"},
    _L.T_RECOMENDADA: {K.ES: "Recomendada", K.EN: "Recommended",
                       K.CA: "Recomanada"},
    _L.T_NOTA_TEXTURAS_RESUMEN: {
        K.ES: "Medida en el paño. Sombras, en las exportaciones del "
              "revelador (lo que ves al revelar): recomendada desde donde "
              "el contraste de su trama llega al {umbral} % del de la ZV; "
              "apreciable, {margen} tercio más abajo. Luces, en el canal "
              "verde de los RAW: apreciable hasta donde conserva el "
              "{conservada} % de su textura, sin pasar del "
              "{recortado_apreciable} % del paño recortado; recomendada, sin "
              "pasar del {recortado} %.",
        K.EN: "Measured on the cloth. Shadows, in the developer exports "
              "(what you see after developing): recommended from where its "
              "weave contrast reaches {umbral} % of the ZV's; visible, "
              "{margen} third lower. Highlights, in the green channel of the "
              "RAW files: visible up to where it keeps {conservada} % of its "
              "texture, not exceeding {recortado_apreciable} % of clipped "
              "cloth; recommended, not exceeding {recortado} %.",
        K.CA: "Mesurada en el drap. Ombres, en les exportacions del revelador "
              "(el que veus en revelar): recomanada des d'on el contrast de "
              "la seua trama arriba al {umbral} % del de la ZV; apreciable, "
              "{margen} terç més avall. Llums, en el canal verd dels RAW: "
              "apreciable fins on conserva el {conservada} % de la seua "
              "textura, sense passar del {recortado_apreciable} % del drap "
              "retallat; recomanada, sense passar del {recortado} %."},
    _L.T_DECISIONES: {K.ES: "Decisiones propias", K.EN: "Own decisions",
                      K.CA: "Decisions pròpies"},
    _L.T_RECOMENDACIONES: {K.ES: "Recomendaciones",
                           K.EN: "Recommendations",
                           K.CA: "Recomanacions"},
    _L.T_VALIDA_ZONA: {
        K.ES: "Elige la zona de la lista (Z0, Z0 1/3… ZX), o — para que el "
              "punto no cuente.",
        K.EN: "Choose the zone from the list (Z0, Z0 1/3… ZX), or — so the "
              "point does not count.",
        K.CA: "Tria la zona de la llista (Z0, Z0 1/3… ZX), o — perquè el "
              "punt no compte."},
    _L.T_VALIDA_CURVA: {
        K.ES: "Escribe un número entero de 0 a {tope}.",
        K.EN: "Type a whole number from 0 to {tope}.",
        K.CA: "Escriu un nombre enter de 0 a {tope}."},
    _L.T_SIN_TELA: {
        K.ES: "Sin paño: no se puede medir la latitud de texturas.",
        K.EN: "No cloth: the texture latitude cannot be measured.",
        K.CA: "Sense drap: no es pot mesurar la latitud de textures."},
    _L.T_POCA_TEXTURA: {
        K.ES: "El paño tiene poca textura (en la Z-V, {textura} veces el "
              "ruido; hacen falta {minimo}): la latitud de texturas en las "
              "sombras puede salir corta o no medirse. Use un paño con la "
              "trama más marcada y revise la luz y el diafragma.",
        K.EN: "The cloth has little texture (in Z-V, {textura} times the "
              "noise; {minimo} are needed): texture latitude in the shadows "
              "may come out short or not be measurable. Use a cloth with a "
              "more marked weave and check the light and the aperture.",
        K.CA: "El drap té poca textura (en la Z-V, {textura} vegades el "
              "soroll; calen {minimo}): la latitud de textures en les ombres "
              "pot eixir curta o no mesurar-se. Useu un drap amb la trama "
              "més marcada i reviseu la llum i el diafragma."},

    # --- PDF de la cámara (exportar.Pdf; usa también textos del
    #     libro)
    _F.T_TITULO_PDF: {K.ES: "Tu cámara: {cam}",
                      K.EN: "Your camera: {cam}",
                      K.CA: "La teua càmera: {cam}"},
    _F.T_SUBTITULO_PDF: {
        K.ES: "Serie del {fecha} · RAW {bits} bits · ZV: {exp}",
        K.EN: "Series of {fecha} · RAW {bits} bits · ZV: {exp}",
        K.CA: "Sèrie del {fecha} · RAW {bits} bits · ZV: {exp}"},
    _F.T_FORMATO_FECHA_PDF: {K.ES: "%d/%m/%Y", K.EN: "%Y-%m-%d",
                             K.CA: "%d/%m/%Y"},
    _F.T_SEPARADOR_DECIMAL: {K.ES: ",", K.EN: ".", K.CA: ","},
    _F.T_NOTA_TEXTURAS_PDF: {
        K.ES: "Dónde se aprecia la textura (medida en el paño, canal verde) "
              "y dónde se recomienda colocar las texturas importantes.",
        K.EN: "Where texture is visible (measured on the cloth, green "
              "channel) and where important textures are best placed.",
        K.CA: "On s'aprecia la textura (mesurada en el drap, canal verd) i "
              "on es recomana col·locar les textures importants."},
    _F.T_CIFRA_ZONAS: {K.ES: "{zonas} zonas", K.EN: "{zonas} zones",
                       K.CA: "{zonas} zones"},
    _F.T_DESDE_HASTA: {K.ES: "de {desde}\na {hasta}",
                       K.EN: "from {desde}\nto {hasta}",
                       K.CA: "de {desde}\na {hasta}"},
    _F.T_NOTA_RECOMENDACIONES: {
        K.ES: "Puntos de la curva (escala 0–255 del editor de curvas): "
              "lleva cada entrada a su salida, que es el objetivo (10 L* "
              "por zona). Son una sugerencia: la decisión es tuya.",
        K.EN: "Curve points (0–255 scale of the curve editor): take each "
              "input to its output, which is the target (10 L* per zone). "
              "They are a suggestion: the decision is yours.",
        K.CA: "Punts de la corba (escala 0–255 de l'editor de corbes): porta "
              "cada entrada a la seua eixida, que és l'objectiu (10 L* per "
              "zona). Són un suggeriment: la decisió és teua."},
    _F.T_SIN_FASE_2: {
        K.ES: "Falta la fase 2: exporta las TIFF del revelador y analiza "
              "el revelado para completar la entrada.",
        K.EN: "Phase 2 is missing: export the developer's TIFF files and "
              "analyze the development to complete the input.",
        K.CA: "Falta la fase 2: exporta les TIFF del revelador i analitza "
              "el revelat per a completar l'entrada."},
    _F.T_PIE_PDF: {K.ES: f"Generado con {K.NOMBRE} {K.version}",
                   K.EN: f"Generated with {K.NOMBRE} {K.version}",
                   K.CA: f"Generat amb {K.NOMBRE} {K.version}"},
    _F.T_PAGINA: {K.ES: "{pagina} / {paginas}", K.EN: "{pagina} / {paginas}",
                  K.CA: "{pagina} / {paginas}"},
}


# --- Análisis: la serie (cabecera), la latitud por canal y los avisos
TEXTOS.update({
    _L.T_ANALIZABLE: {K.ES: "Se puede analizar", K.EN: "Can be analyzed",
                      K.CA: "Es pot analitzar"},
    _L.T_AVISOS: {K.ES: "Avisos", K.EN: "Warnings", K.CA: "Avisos"},
    _L.T_BALANCE_PERSONALIZADO: {K.ES: "Balance personalizado",
                                 K.EN: "Custom balance",
                                 K.CA: "Balanç personalitzat"},
    _L.T_FILA_LATITUD: {K.ES: "Latitud sugerida", K.EN: "Suggested latitude",
                        K.CA: "Latitud suggerida"},
    _L.T_FILA_LINEAL_HASTA: {K.ES: "Lineal hasta la zona",
                             K.EN: "Linear up to zone",
                             K.CA: "Lineal fins a la zona"},
    _L.T_FILA_RANGO: {K.ES: "Rango (techo − suelo)",
                      K.EN: "Range (ceiling − floor)",
                      K.CA: "Rang (sostre − sòl)"},
    _L.T_FILA_SE_RECORTA: {K.ES: "Se recorta en la zona",
                           K.EN: "Clips at zone",
                           K.CA: "Es retalla en la zona"},
    _L.T_FILA_SOMBRA_ACEPTABLE: {K.ES: "Sombra aceptable desde la zona",
                                 K.EN: "Acceptable shadow from zone",
                                 K.CA: "Ombra acceptable des de la zona"},
    _L.T_FILA_SOMBRA_EXCELENTE: {K.ES: "Sombra excelente desde la zona",
                                 K.EN: "Excellent shadow from zone",
                                 K.CA: "Ombra excel·lent des de la zona"},
    _L.T_FILA_SUELO: {K.ES: "Suelo teórico", K.EN: "Theoretical floor",
                      K.CA: "Sòl teòric"},
    _L.T_FILA_TECHO: {K.ES: "Techo teórico", K.EN: "Theoretical ceiling",
                      K.CA: "Sostre teòric"},
    _L.T_LATITUD_CANAL: {K.ES: "Latitud por canal (en zonas)",
                         K.EN: "Latitude per channel (in zones)",
                         K.CA: "Latitud per canal (en zones)"},
    _L.T_NO: {K.ES: "No", K.EN: "No", K.CA: "No"},
    _L.T_SI: {K.ES: "Sí", K.EN: "Yes", K.CA: "Sí"},
    _L.T_SIN_AVISOS: {K.ES: "Sin avisos", K.EN: "No warnings",
                      K.CA: "Sense avisos"},
    _L.T_TOMAS: {K.ES: "Tomas", K.EN: "Shots", K.CA: "Preses"}})


# --- Nombres de los balances de la cámara (los de leer.marcas), traducidos
_M = KM
TEXTOS[_L.T_PRESET] = {K.ES: "Preajuste {n}", K.EN: "Preset {n}",
                       K.CA: "Preajust {n}"}
TEXTOS.update({_L.PREFIJO_BALANCE + nombre: texto for nombre, texto in (
    (_M.B_AUTO, {K.ES: "Auto", K.EN: "Auto", K.CA: "Auto"}),
    (_M.B_DAYLIGHT, {K.ES: "Luz día", K.EN: "Daylight",
                     K.CA: "Llum de dia"}),
    (_M.B_CLOUDY, {K.ES: "Nublado", K.EN: "Cloudy", K.CA: "Ennuvolat"}),
    (_M.B_SHADE, {K.ES: "Sombra", K.EN: "Shade", K.CA: "Ombra"}),
    (_M.B_TUNGSTEN, {K.ES: "Tungsteno", K.EN: "Tungsten",
                     K.CA: "Tungstè"}),
    (_M.B_INCANDESCENT, {K.ES: "Incandescente", K.EN: "Incandescent",
                         K.CA: "Incandescent"}),
    (_M.B_FLUORESCENT, {K.ES: "Fluorescente", K.EN: "Fluorescent",
                        K.CA: "Fluorescent"}),
    (_M.B_FLASH, {K.ES: "Flash", K.EN: "Flash", K.CA: "Flaix"}),
    (_M.B_CUSTOM, {K.ES: "Personalizado", K.EN: "Custom",
                   K.CA: "Personalitzat"}),
    (_M.B_KELVIN, {K.ES: "Kelvin", K.EN: "Kelvin", K.CA: "Kelvin"}),
    (_M.B_UNDERWATER, {K.ES: "Bajo el agua", K.EN: "Underwater",
                       K.CA: "Davall de l'aigua"}))})


#
def textos_excel() -> dict[str, str]:
    """ Textos del libro en el idioma activo: {clave: texto}. """
    return {clave: K.tr(texto) for clave, texto in TEXTOS.items()}
