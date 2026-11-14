# -*- coding: utf-8 *-*
"""
    :Propósito: Libro Excel de resultados de una serie (pieza D), escrito
                desde cero con XlsxWriter: cada valor calculado va con su
                fórmula y su resultado (así se ve en la Vista protegida de
                Excel). Sin textos propios: los recibe ya traducidos
    :Autor:     Tony Diana
    :Versión:   26.10.25
"""

# cSpell:ignore asim, averageifs, Calibri, CIELAB, COUNTIF, countifs
# cSpell:ignore desp, desv, desviacion, dif, disp, dvi, graf, grafs, gridlines
# cSpell:ignore iferror, ISNUMBER, kcom, kres, kte, ktr, kxl, Lightroom, lstar
# cSpell:ignore lzv, maxifs, minifs, mpx, mult, oecf, preajuste, preajustes
# cSpell:ignore rci, recalculan, Relacion, rotulos, rowcol, srgb, valign
# cSpell:ignore vcenter, Verdana, xlsxwriter

__all__ = ["KXL", "Excel", "PuntoCurva", "DatosSerie"]

# --- Bibliotecas estándar Python
import math
import re
from datetime import datetime
from functools import partial
from pathlib import Path
from typing import Any, NamedTuple, cast

# --- Bibliotecas externas
import xlsxwriter
from xlsxwriter.chart import Chart
from xlsxwriter.format import Format
from xlsxwriter.utility import xl_range_abs, xl_rowcol_to_cell
from xlsxwriter.worksheet import Worksheet

# --- Bibliotecas internas
from bib import std
from bib.oecfMediadores import KP, KRES, texto_iso, zona_tercio
from kernel import COM as KCOM, K
from oecfCalc import (escala_mpx, Exp, FilaISO, KS, KTE, KTR, OECF, Review,
                      signal_para_snr, snr_modelo, tercios_sombra,
                      textura as calcular_textura, ZonaMedida)


# --- Un tramo de la latitud de texturas: sombra, luz y ancho, en zonas (o
#     el texto de C_TEXTO_NO_ALCANZADO si no se alcanza)
Tramo = tuple[float | str, float | str, float | str]


#
class KXL(std.EnumMutable):
    """ Diseño del libro: fuentes, colores, medidas, nombres y textos. """

    # --- Fuente de todas las hojas salvo Análisis, y sus tamaños
    FUENTE = "Arial"
    LETRA = 10
    LETRA_TITULO = 14
    LETRA_APARTADO = 11

    # --- Colores del texto: dato (lo leído de los RAW), literal (lo
    #     escrito por diseño), fórmula y rótulo o nota
    COLOR_DATO = "#0000FF"
    COLOR_LITERAL = "#C55A11"
    COLOR_FORMULA = "#000000"
    COLOR_ROTULO = "#595959"
    """Color del texto de rótulos y notas (también en el PDF)."""

    # --- Tablas: cabecera, filas alternas y bordes finos, en la gama de
    #     verdes del libro (Tony, 2026-10-15; antes, azules). La cabecera,
    #     lo bastante oscura para que se lea el blanco
    CABECERA_FONDO = "#548235"
    """Fondo de la cabecera de las tablas (también en el PDF)."""
    CABECERA_TEXTO = "#FFFFFF"
    BANDA = "#E2EFDA"
    """Fondo de las filas alternas de las tablas (también en el PDF)."""
    BORDE_TABLA = "#A9D08E"
    """Color de los bordes finos de las tablas (también en el PDF)."""
    FINO = 1
    MEDIO = 2

    # --- Marco «tarjeta»: anillo gris alrededor (fila 1, última fila,
    #     columna A y última columna), tarjeta con borde medio y una fila
    #     y una columna de relleno por dentro. El contenido, desde C3.
    #     Anchos: los del cuadro de diálogo de Excel (el archivo guarda
    #     unos 0,71 más: 8,43 → 9,14)
    ANILLO = "#BFBFBF"
    ANCHO_ANILLO = 8.43
    ANCHO_RELLENO = 2.14
    FILA_INICIO = 2
    COLUMNA_INICIO = 2
    ULTIMA_COLUMNA_EXCEL = 16383

    # --- Para pasar fracciones a porcentaje (el de kernel)
    CIEN = KCOM.CIEN
    """Para pasar fracciones a porcentaje: el COM.CIEN de kernel."""

    # --- Formatos de número y comilla de las cadenas en las fórmulas
    NUM_ENTERO = "0"
    NUM_UNO = "0.0"
    NUM_DOS = "0.00"
    NUM_TRES = "0.000"
    NUM_CUATRO = "0.0000"
    NUM_PORCENTAJE = "0.00%"
    COMILLA = '"'

    # --- Nombre de las zonas en el libro (Z0, Z0 1/3, Z0 2/3, … ZV, ZX):
    #     el del fotómetro, con los tercios en fracción
    TERCIOS_EXCEL = ("", " 1/3", " 2/3")

    # --- Sin dato en un texto (también en las tablas del PDF)
    SIN_DATO = "—"

    # --- Alto de las cabeceras que se parten en dos líneas
    ALTO_CABECERA = 30

    # --- Notas y textos largos: se parten en líneas dentro de las columnas
    #     de su tabla, sin pasar de ANCHO_NOTA (en caracteres de Excel:
    #     unos 1200 px), y la fila crece según las líneas. ANCHO_LETRA:
    #     lo que ocupa de media una letra del texto frente al carácter de
    #     Excel (el «0»), con algo de holgura; ALTO_LINEA, en puntos
    ANCHO_NOTA = 165
    ANCHO_LETRA = 0.95
    ALTO_LINEA = 12.75
    COLUMNAS_ROTULO = 3

    # --- Canales del libro (rojo, verde, azul) y columna del primer valor
    #     de una toma en Datos, tras zona, tercios y archivo
    CANALES = KCOM.CANALES_RGB
    """Canales del libro (rojo, verde, azul): COM.CANALES_RGB."""
    COL_VALORES = 3

    # --- Tabla del paño en Datos: tras la dispersión y el recortado por
    #     canal, las dispersiones del verde con las que se mide la textura
    #     (por píxel; ver Excel.disp_textura): paño y tarjeta
    COL_TELA_PIXEL = COL_VALORES + (2 * CANALES)
    COL_TARJETA_PIXEL = COL_TELA_PIXEL + 1

    # --- Columna del L* del revelador en su tabla de Datos, tras zona y
    #     tercios, y la del contraste de la trama del paño (Tony,
    #     2026-11-13)
    COL_REVELADOR = 2
    COL_CONTRASTE = 3

    # --- Hojas, en su orden (claves de sus nombres en los textos)
    T_HOJA_RESUMEN = "hoja_resumen"
    T_HOJA_GRAF = "hoja_graf"
    T_HOJA_DATOS = "hoja_datos"
    T_HOJA_CONSTANTES = "hoja_constantes"
    T_HOJA_CALCULO = "hoja_calculo"
    T_HOJA_RECHAZADAS = "hoja_rechazadas"
    T_HOJA_IA = "hoja_ia"
    T_HOJA_ISO = "hoja_iso"
    """ Hoja de la secuencia de ISO: solo si la serie la tiene. """
    HOJAS = (T_HOJA_RESUMEN, T_HOJA_GRAF, T_HOJA_ISO, T_HOJA_DATOS,
             T_HOJA_CONSTANTES, T_HOJA_CALCULO, T_HOJA_RECHAZADAS,
             T_HOJA_IA)

    # --- Hojas que se generan ocultas: el estudiante trabaja en Análisis
    #     y Gráficos
    HOJAS_OCULTAS = (T_HOJA_DATOS, T_HOJA_CONSTANTES, T_HOJA_CALCULO,
                     T_HOJA_RECHAZADAS, T_HOJA_IA)

    # --- Sin dato en una columna que dibuja una gráfica: NA() (la
    #     gráfica no lo dibuja; "" se dibujaría a 0) y su resultado
    FORMULA_NA = "NA()"
    RESULTADO_NA = "#N/A"

    # --- Constantes del método: nombres definidos en el libro (no se
    #     traducen: las fórmulas los usan)
    C_ZONA_ZV = "ZonaZV"
    """Nombre definido de la zona de la ZV (su valor, en CONSTANTES;
    su descripción, en los textos)."""
    C_TERCIO_POR_ZONA = "TercioPorZona"
    """Nombre definido de los tercios por zona."""
    C_FACTOR_ZONA = "FactorZona"
    C_LZV = "LZV"
    C_L_POR_ZONA = "LPorZona"
    C_RATIO_SR = "RelacionSR"
    C_SNR_MINIMA = "SNRMinima"
    C_SNR_EXCELENTE = "SNRExcelente"
    C_MPX_REFERENCIA = "MpxReferencia"
    C_TOLERANCIA_LINEAL = "ToleranciaLineal"
    C_UMBRAL_RECORTE = "UmbralRecorte"
    C_ROSE_TEXTURA = "RoseTextura"
    """Nombre definido de la textura/ruido, por píxel, desde la que se
    aprecia la textura en las sombras (criterio de Rose)."""
    C_TEXTURA_JUSTA = "TexturaJusta"
    """Nombre definido de la fracción del umbral de sombras desde la que
    la textura de la Z2 de un ISO es justa (por debajo, se pierde)."""
    C_TEXTURA_CONSERVADA = "TexturaConservada"
    C_TELA_RECORTADO_APRECIABLE = "TelaRecortadoApreciable"
    """Nombre definido de la fracción del paño recortado que admite como
    mucho la zona de luces apreciable."""
    C_TELA_RECORTADO_MAX = "TelaRecortadoMax"
    C_CONTRASTE_SOMBRAS = "ContrasteSombras"
    """Nombre definido de la fracción del contraste de la trama del paño
    en la ZV (en L*, en las exportaciones del revelador) desde la que la
    textura de una zona de sombras es recomendada (Tony, 2026-11-13)."""
    C_MARGEN_SOMBRAS = "MargenSombras"
    C_ANCHO_ZONA = "AnchoZona"
    C_LAB_ESCALA = "LabEscala"
    C_LAB_DESPLAZA = "LabDesplaza"
    C_LAB_UMBRAL = "LabUmbral"
    C_LAB_PENDIENTE = "LabPendiente"
    C_SRGB_UMBRAL = "SrgbUmbral"
    C_SRGB_PENDIENTE = "SrgbPendiente"
    C_SRGB_ESCALA = "SrgbEscala"
    C_SRGB_GAMMA = "SrgbGamma"
    C_SRGB_DESPLAZA = "SrgbDesplaza"
    C_ESCALA_CURVA = "EscalaCurva"
    """Nombre definido de la escala de la entrada y la salida de la
    curva."""
    C_TEXTO_RECORTADO = "TextoRecortado"
    C_TEXTO_NO_RECORTADO = "TextoNoRecortado"
    C_TEXTO_NINGUNO = "TextoNinguno"
    C_TEXTO_NO_ALCANZADO = "TextoNoAlcanzado"
    C_TEXTO_SIN_REVELADO = "TextoSinRevelado"
    C_TEXTO_SATURADO = "TextoSaturado"
    C_TEXTO_PUNTO = "TextoPunto"
    C_LUZ_POR_TERCIO = "LuzPorTercio"
    C_LUZ_ZV = "LuzZV"

    # --- Unidades (claves de sus textos)
    U_ZONA = "unidad_zona"
    U_ZONAS = "unidad_zonas"
    U_TERCIOS = "unidad_tercios"
    U_VECES = "unidad_veces"
    U_LSTAR = "unidad_lstar"
    U_PART = "unidad_part"
    U_NUMERO = "unidad_numero"
    U_TEXTO = "unidad_texto"
    U_MPX = "unidad_mpx"

    # --- Valores de las constantes de texto: claves de sus textos (las
    #     fórmulas comparan con ellos, así que van traducidos)
    V_RECORTADO = "valor_recortado"
    V_NO_RECORTADO = "valor_no_recortado"
    V_NINGUNO = "valor_ninguno"
    V_NO_ALCANZADO = "valor_no_alcanzado"
    V_SIN_REVELADO = "valor_sin_revelado"
    V_SATURADO = "valor_saturado"
    V_PUNTO = "valor_punto"

    # --- Cada constante: nombre, valor (str: clave del texto que hace de
    #     valor, ya traducido) y unidad. Su descripción, en los textos con
    #     el nombre como clave. Las derivadas van aparte, con fórmula
    CONSTANTES = (
        (C_ZONA_ZV, 5, U_ZONA),
        (C_TERCIO_POR_ZONA, 3, U_TERCIOS),
        (C_FACTOR_ZONA, 2, U_VECES),
        (C_LZV, 50, U_LSTAR),
        (C_L_POR_ZONA, 10, U_LSTAR),
        (C_RATIO_SR, 1, U_VECES),
        (C_SNR_MINIMA, 10, U_VECES),
        (C_SNR_EXCELENTE, 40, U_VECES),
        (C_MPX_REFERENCIA, 8, U_MPX),
        (C_TOLERANCIA_LINEAL, KCOM.TOLERANCIA_LINEAL, U_ZONAS),
        (C_UMBRAL_RECORTE, KCOM.UMBRAL_RECORTE, U_PART),
        (C_ROSE_TEXTURA, 1.3, U_VECES),
        (C_TEXTURA_JUSTA, 0.75, U_PART),
        (C_TEXTURA_CONSERVADA, 0.5, U_PART),
        (C_TELA_RECORTADO_APRECIABLE, 0.1, U_PART),
        (C_TELA_RECORTADO_MAX, 0.01, U_PART),
        (C_CONTRASTE_SOMBRAS, 0.4, U_PART),
        (C_MARGEN_SOMBRAS, 1, U_TERCIOS),
        (C_ANCHO_ZONA, 1, U_ZONAS),
        (C_LAB_ESCALA, KCOM.LAB_ESCALA, U_NUMERO),
        (C_LAB_DESPLAZA, KCOM.LAB_DESPLAZA, U_NUMERO),
        (C_LAB_UMBRAL, KCOM.LAB_UMBRAL, U_PART),
        (C_LAB_PENDIENTE, KCOM.LAB_PENDIENTE, U_NUMERO),
        (C_SRGB_UMBRAL, KCOM.SRGB_UMBRAL_LUZ, U_PART),
        (C_SRGB_PENDIENTE, KCOM.SRGB_PENDIENTE, U_NUMERO),
        (C_SRGB_ESCALA, KCOM.SRGB_ESCALA, U_NUMERO),
        (C_SRGB_GAMMA, KCOM.SRGB_GAMMA, U_NUMERO),
        (C_SRGB_DESPLAZA, KCOM.SRGB_DESPLAZA, U_NUMERO),
        (C_ESCALA_CURVA, 255, U_NUMERO),
        (C_TEXTO_RECORTADO, V_RECORTADO, U_TEXTO),
        (C_TEXTO_NO_RECORTADO, V_NO_RECORTADO, U_TEXTO),
        (C_TEXTO_NINGUNO, V_NINGUNO, U_TEXTO),
        (C_TEXTO_NO_ALCANZADO, V_NO_ALCANZADO, U_TEXTO),
        (C_TEXTO_SIN_REVELADO, V_SIN_REVELADO, U_TEXTO),
        (C_TEXTO_SATURADO, V_SATURADO, U_TEXTO),
        (C_TEXTO_PUNTO, V_PUNTO, U_TEXTO))
    """Constantes del método: (nombre, valor, unidad). Un valor de texto
    es la clave del texto que hace de valor; la descripción, en los
    textos con el nombre como clave."""
    DERIVADAS = (
        (C_LUZ_POR_TERCIO, f"={C_FACTOR_ZONA}^(1/{C_TERCIO_POR_ZONA})",
         U_VECES),
        (C_LUZ_ZV, f"=IF({C_LZV}>{C_LAB_UMBRAL}*{C_LAB_PENDIENTE},"
         f"(({C_LZV}+{C_LAB_DESPLAZA})/{C_LAB_ESCALA})^3,"
         f"{C_LZV}/{C_LAB_PENDIENTE})", U_PART))

    # --- Hoja Constantes: anchos (C a F; la de la unidad, oculta, como en
    #     el libro de Tony) y textos
    ANCHOS_CONSTANTES = (20.71, 12.71, None, 100.71)
    T_TITULO_CONSTANTES = "titulo_constantes"
    T_NOTA_CONSTANTES = "nota_constantes"
    T_CAB_NOMBRE = "cab_nombre"
    T_CAB_VALOR = "cab_valor"
    T_CAB_UNIDAD = "cab_unidad"
    T_CAB_QUE_ES = "cab_que_es"

    # --- Nota de C_SNR_MINIMA: su primera línea lleva el valor de la
    #     constante, por fórmula (si se cambia, el texto no se desfasa)
    T_NOTA_SNR_ANTES = "nota_snr_antes"
    T_NOTA_SNR_TRAS = "nota_snr_tras"
    T_NOTA_SNR_ISO = "nota_snr_iso"
    T_NOTA_SNR_USUARIO = "nota_snr_usuario"

    # --- Hoja Datos: anchos (C a M), Z-V de control que caben y textos
    ANCHOS_DATOS = (12.0, 9.0, 16.0, 14.0, 14.0, 14.0, 14.0, 14.0, 14.0,
                    14.0, 14.0)
    CONTROLES = 3
    T_TITULO_DATOS = "titulo_datos"
    T_NOTA_DATOS = "nota_datos"
    T_SERIE_ZONAS = "serie_zonas"
    T_CAB_ZONA = "cab_zona"
    T_CAB_TERCIOS = "cab_tercios"
    T_CAB_ARCHIVO = "cab_archivo"
    T_CAB_ROJO = "cab_rojo"
    T_CAB_VERDE = "cab_verde"
    T_CAB_AZUL = "cab_azul"
    T_CAB_DISP_ROJO = "cab_disp_rojo"
    T_CAB_DISP_VERDE = "cab_disp_verde"
    T_CAB_DISP_AZUL = "cab_disp_azul"

    # --- Balances de blancos de la cámara: textos, y prefijo de la clave
    #     del nombre traducido de cada balance (el de leer.marcas: DAYLIGHT…;
    #     si no hay traducción, tal cual)
    T_BALANCES = "balances"
    T_NOTA_BALANCES = "nota_balances"
    T_SIN_BALANCES = "sin_balances"
    T_CAB_BALANCE = "cab_balance"
    T_CAB_KELVIN_ANOTADO = "cab_kelvin_anotado"
    T_CAB_KELVIN_MEDIDO = "cab_kelvin_medido"
    T_CAB_MULT_ROJO = "cab_mult_rojo"
    T_CAB_MULT_AZUL = "cab_mult_azul"
    PREFIJO_BALANCE = "balance_"

    # --- Preajustes de balance con número (Nikon: PRESET1, PRESET2…):
    #     su patrón y la clave de su nombre traducido («Preajuste {n}»)
    REGEX_PRESET = r"PRESET(\d+)"
    T_PRESET = "balance_preset"
    T_CONTROL = "control"
    T_MEDIA_ZV = "media_zv"
    T_MEDIA = "media"
    T_RUIDO = "ruido"
    T_CAB_ORIGEN = "cab_origen"
    T_ORIGEN_BORDE = "origen_borde"
    T_REVELADOR = "revelador"
    T_TELA = "tela"
    T_NOTA_TELA = "nota_tela"
    T_CAB_TELA_REC_ROJO = "cab_tela_rec_rojo"
    T_CAB_TELA_REC_VERDE = "cab_tela_rec_verde"
    T_CAB_TELA_REC_AZUL = "cab_tela_rec_azul"
    T_CAB_TELA_PIXEL = "cab_tela_pixel"
    T_CAB_TARJETA_PIXEL = "cab_tarjeta_pixel"
    T_NOTA_REVELADOR = "nota_revelador"
    T_CAB_REVELADOR = "cab_revelador"
    T_CAB_CONTRASTE = "cab_contraste"

    # --- Ruido y negro (Datos): la franja oscura del sensor, la comparación
    #     con las tapadas, el negro restado (según su origen, oecfCalc.KTE) y
    #     sus avisos
    T_COMPARAR_TAPADAS = "comparar_tapadas"
    T_NEGRO_TAPADAS = "negro_tapadas"
    T_NEGRO_SOMBRAS = "negro_sombras"
    T_NEGRO_DECLARADO = "negro_declarado"
    ORIGEN_NEGRO = {KTE.ORIGEN_TAPADAS: T_NEGRO_TAPADAS,
                    KTE.ORIGEN_SOMBRAS: T_NEGRO_SOMBRAS,
                    KTE.ORIGEN_DECLARADO: T_NEGRO_DECLARADO}
    T_RUIDOS_DIFIEREN = "ruidos_difieren"
    T_SIN_RUIDO_SUELO = "sin_ruido_suelo"
    T_SIN_BORDE = "sin_borde"

    # --- Ruido aceptable por color (Análisis y PDF): título, nota con el
    #     umbral y la frase de cada canal según su suelo sugerido
    T_RUIDO_COLOR = "ruido_color"
    T_RUIDO_COLOR_ISO = "ruido_color_iso"
    T_RUIDO_COLOR_NOTA = "ruido_color_nota"
    T_RUIDO_COLOR_TODO = "ruido_color_todo"
    T_RUIDO_COLOR_DESDE = "ruido_color_desde"
    T_RUIDO_COLOR_NUNCA = "ruido_color_nunca"
    T_RUIDO_COLOR_NINGUNA = "ruido_color_ninguna"

    # --- Estado del ruido de un canal (Excel.zona_ruido): aceptable en
    #     todo el rango, desde una zona o en ninguna
    RUIDO_TODO = 0
    RUIDO_DESDE = 1
    RUIDO_NINGUNO = 2

    # --- Píxeles defectuosos (Datos, Análisis y PDF): título, calientes y
    #     muertos (cuántos y por megapíxel) y el aviso de que sin tapadas no
    #     se cuentan los calientes
    T_PIXELES = "pixeles"
    T_PIXELES_CALIENTES = "pixeles_calientes"
    T_PIXELES_MUERTOS = "pixeles_muertos"
    T_PIXELES_SIN_TAPADAS = "pixeles_sin_tapadas"
    T_PIXELES_SIN_CALIENTES = "pixeles_sin_calientes"
    T_PIXELES_SIN_MUERTOS = "pixeles_sin_muertos"
    T_PIXELES_NINGUNO = "pixeles_ninguno"
    T_PIXELES_TIPO_CALIENTES = "pixeles_tipo_calientes"
    T_PIXELES_TIPO_MUERTOS = "pixeles_tipo_muertos"
    DECIMALES_MPX = 1
    ZONA_SOMBRA_TEXTO = "Z2"
    """Cómo dicen «la Z2» los textos de la secuencia de ISO: se cambia por
    la zona de la toma de sombras (ver Excel.rotulo_sombra)."""
    SEPARADOR_ZONAS = "/"
    """Une las zonas de la toma de sombras de la secuencia de ISO, si es
    la Z2 en unos ISO y la Z3 en otros."""
    SENAL_RUIDO_DECIMAL = 10
    """Por debajo de este señal/ruido, el PDF lo escribe con un decimal."""
    SIN_NUMERO = "—"
    """Lo que se escribe en una celda de la que no hay número."""
    """Decimales de los píxeles por megapíxel."""
    MARGEN_TERCIO = 1e-9
    """Margen al llevar un suelo a su tercio (evita que un suelo que cae
    justo en un tercio pase al siguiente por los decimales)."""

    # --- Curva de transferencia del ruido (Datos): sección, nota y cada
    #     fila (lectura, ganancia, proporcional, aleatorio y fijo de la
    #     Z-V) y los megapíxeles del sensor
    T_TRANSFERENCIA = "transferencia"
    T_NOTA_TRANSFERENCIA = "nota_transferencia"
    T_LECTURA = "lectura"
    T_GANANCIA = "ganancia"
    T_PROPORCIONAL = "proporcional"
    T_ALEATORIO_ZV = "aleatorio_zv"
    T_FIJO_ZV = "fijo_zv"
    T_MPX_SENSOR = "mpx_sensor"

    # --- Filas de la hoja Datos que leen otras hojas (claves de
    #     Excel.filas: se calculan al escribirla)
    F_ZONAS = "zonas"
    F_CONTROL = "control"
    F_MEDIA = "media"
    F_RUIDO = "ruido"
    F_REVELADOR = "revelador"
    F_BALANCES = "balances"
    F_RUIDO_TAPADAS = "ruido_tapadas"
    F_NEGRO = "negro"
    F_LECTURA = "lectura"
    F_GANANCIA = "ganancia"
    F_PROPORCIONAL = "proporcional"
    F_ALEATORIO = "aleatorio"
    F_FIJO = "fijo"
    F_MPX = "mpx"
    F_TELA = "tela"

    # --- Hoja Cálculo: anchos (C a AA), altos de las cabeceras y formatos
    ANCHOS_CALCULO = (12.0,) * 28
    ALTO_CABECERA_ALTA = 42
    NUM_SIGNO_TRES = "+0.000;-0.000;0.000"
    NUM_SIGNO_UNO = "+0.0;-0.0;0.0"
    T_TITULO_CALCULO = "titulo_calculo"
    T_NOTA_CALCULO = "nota_calculo"
    T_POR_CANAL = "por_canal"
    T_NOTA_POR_CANAL = "nota_por_canal"
    T_NOTA_LATITUD = "nota_latitud"
    T_CAB_CANAL = "cab_canal"
    T_CAB_ZV_MEDIA = "cab_zv_media"
    T_CAB_MAX = "cab_max"
    T_CAB_TECHO = "cab_techo"
    T_CAB_SUELO = "cab_suelo"
    T_CAB_RANGO = "cab_rango"
    T_CAB_LINEAL = "cab_lineal"
    T_CAB_RECORTADO = "cab_recortado"
    T_CAB_SUELO_SNR = "cab_suelo_snr"
    T_CAB_SUELO_EXCELENTE = "cab_suelo_excelente"
    T_CAB_LATITUD = "cab_latitud"
    T_POR_TERCIO = "por_tercio"
    T_NOTA_POR_TERCIO = "nota_por_tercio"
    T_CAB_ESPERADO = "cab_esperado"
    T_CAB_OBTENIDO_ROJO = "cab_obtenido_rojo"
    T_CAB_OBTENIDO_VERDE = "cab_obtenido_verde"
    T_CAB_OBTENIDO_AZUL = "cab_obtenido_azul"
    T_CAB_DESV_ROJO = "cab_desv_rojo"
    T_CAB_DESV_VERDE = "cab_desv_verde"
    T_CAB_DESV_AZUL = "cab_desv_azul"
    T_CAB_REC_ROJO = "cab_rec_rojo"
    T_CAB_REC_VERDE = "cab_rec_verde"
    T_CAB_REC_AZUL = "cab_rec_azul"
    T_CAB_SNR_ROJO = "cab_snr_rojo"
    T_CAB_SNR_VERDE = "cab_snr_verde"
    T_CAB_SNR_AZUL = "cab_snr_azul"
    T_CAB_FALTA_VERDE = "cab_falta_verde"
    T_CAB_TECHO_VERDE = "cab_techo_verde"
    T_CAB_SUELO_VERDE = "cab_suelo_verde"
    T_CAB_SNR_SUGERIDA = "cab_snr_sugerida"
    T_CAB_SNR8_ROJO = "cab_snr8_rojo"
    T_CAB_SNR8_VERDE = "cab_snr8_verde"
    T_CAB_SNR8_AZUL = "cab_snr8_azul"
    T_CAB_SNR_MODELO = "cab_snr_modelo"
    T_CAB_SNR_EXCELENTE = "cab_snr_excelente"
    T_CAB_SNR_ING = "cab_snr_ing"
    T_CURVA = "curva"
    T_NOTA_CURVA_ANTES = "nota_curva_antes"
    T_NOTA_CURVA_MEDIO = "nota_curva_medio"
    T_NOTA_CURVA_TRAS = "nota_curva_tras"
    T_CAB_LUZ_ESPERADA = "cab_luz_esperada"
    T_CAB_L_ESPERADO = "cab_l_esperado"
    T_CAB_L_OBJETIVO = "cab_l_objetivo"
    T_CAB_LUZ_SENSOR = "cab_luz_sensor"
    T_CAB_L_SENSOR = "cab_l_sensor"
    T_CAB_DIF_SENSOR = "cab_dif_sensor"
    T_CAB_L_REVELADOR = "cab_l_revelador"
    T_CAB_LUZ_REVELADOR = "cab_luz_revelador"
    T_CAB_DIF_REVELADOR = "cab_dif_revelador"
    T_CAB_FALTA = "cab_falta"
    T_CAB_SOBRA = "cab_sobra"
    T_CAB_ENTRADA = "cab_entrada"
    T_CAB_SALIDA = "cab_salida"
    T_CAB_PUNTO = "cab_punto"
    T_CANALES = (T_CAB_ROJO, T_CAB_VERDE, T_CAB_AZUL)

    # --- Claves de zonas_canal (por zona y canal). Las de canales (por
    #     canal: lo que da el bloque 1 de Cálculo) son KRES.R_*
    Z_ESPERADO = "esperado"
    Z_OBTENIDO = "obtenido"
    Z_DEV = "dev"
    Z_RECORTADO = KRES.J_RECORTADO

    # --- Las constantes que usó el análisis, en los resultados del JSON:
    #     cada una, con su nombre en el libro y su clave en el JSON
    CONSTANTES_JSON = ((C_ANCHO_ZONA, KRES.CONST_ANCHO_ZONA),
                       (C_FACTOR_ZONA, KRES.CONST_FACTOR_ZONA),
                       (C_L_POR_ZONA, KRES.CONST_L_POR_ZONA),
                       (C_LZV, KRES.CONST_LZV),
                       (C_SNR_EXCELENTE, KRES.CONST_SNR_EXCELENTE),
                       (C_SNR_MINIMA, KRES.CONST_SNR_MINIMA),
                       (C_TERCIO_POR_ZONA, KRES.CONST_TERCIO_POR_ZONA),
                       (C_TOLERANCIA_LINEAL, KRES.CONST_TOLERANCIA_LINEAL),
                       (C_UMBRAL_RECORTE, KRES.CONST_UMBRAL_RECORTE),
                       (C_ZONA_ZV, KRES.CONST_ZONA_ZV))

    # --- Bloque 4 de Cálculo: latitud de texturas (verde). Arriba, los
    #     límites (sombras, altas luces y latitud, apreciable y
    #     recomendada); debajo, una fila por zona. Columnas de la tabla
    #     por zona (desde la de la zona) y de los límites (desde la del
    #     rótulo)
    T_TEXTURAS = "texturas"
    T_POR_TEXTURA = "por_textura"
    T_NOTA_TEXTURAS = "nota_texturas"
    T_CAB_TEXTURA = "cab_textura"
    T_CAB_TEXTURA_RUIDO = "cab_textura_ruido"
    T_CAB_CONSERVADA = "cab_conservada"
    T_CAB_TELA_RECORTADO = "cab_tela_recortado"
    T_CAB_CUMPLE_SOMBRAS = "cab_cumple_sombras"
    T_CAB_CUMPLE_LUCES = "cab_cumple_luces"
    T_CAB_SIN_RECORTE = "cab_sin_recorte"
    T_CAB_CONTRASTE_ZV = "cab_contraste_zv"
    T_CAB_SOMBRAS = "cab_sombras"
    T_CAB_LUCES = "cab_luces"
    T_CAB_LATITUD_TEXTURAS = "cab_latitud_texturas"
    T_APRECIABLE = "apreciable"
    T_RECOMENDADA = "recomendada"
    TEXTURA_ESPERADO = 2
    TEXTURA_TEXTURA = 3
    TEXTURA_RUIDO = 4
    TEXTURA_CONSERVADA = 5
    TEXTURA_RECORTADO = 6
    TEXTURA_SOMBRAS = 7
    TEXTURA_LUCES = 8
    TEXTURA_SIN_RECORTE = 9
    TEXTURA_CONTRASTE = 10
    TEXTURA_FRACCION = 11
    LIMITE_SOMBRAS = 1
    LIMITE_LUCES = 2
    LIMITE_LATITUD = 3

    # --- Columnas del bloque 3 de Cálculo que leen Análisis y Datos
    #     (desde la de la zona)
    CURVA_L_ESPERADO = 3
    CURVA_L_OBJETIVO = 4
    CURVA_L_REVELADOR = 8
    CURVA_DIF_SENSOR = 7
    CURVA_DIF_REVELADOR = 10
    CURVA_ENTRADA = 13
    CURVA_SALIDA = 14
    CURVA_PUNTO = 15

    # --- Tu curva (bloque 3 de Cálculo, a la derecha): la entrada de cada
    #     zona pasada por los puntos de las decisiones propias, en recta
    #     entre el de abajo y el de arriba (con (0, 0) y (C_ESCALA_CURVA,
    #     C_ESCALA_CURVA) en los extremos, como en Lightroom). Columnas
    #     (desde la de la zona): los dos puntos del tramo, la salida, el
    #     L*, su diferencia con el objetivo y falta y sobra (barras de la
    #     gráfica); y la tabla de los puntos (entrada y salida), una fila
    #     por punto, desde la Z0
    TU_DESDE_ENTRADA = 16
    TU_DESDE_SALIDA = 17
    TU_HASTA_ENTRADA = 18
    TU_HASTA_SALIDA = 19
    TU_SALIDA = 20
    TU_L = 21
    TU_DIF = 22
    TU_FALTA = 23
    TU_SOBRA = 24
    TU_PUNTOS_ENTRADA = 26
    TU_PUNTOS_SALIDA = 27
    T_CAB_TU_DESDE_ENTRADA = "cab_tu_desde_entrada"
    T_CAB_TU_DESDE_SALIDA = "cab_tu_desde_salida"
    T_CAB_TU_HASTA_ENTRADA = "cab_tu_hasta_entrada"
    T_CAB_TU_HASTA_SALIDA = "cab_tu_hasta_salida"
    T_CAB_TU_SALIDA = "cab_tu_salida"
    T_CAB_TU_L = "cab_tu_l"
    T_CAB_TU_DIF = "cab_tu_dif"
    T_CAB_TU_PUNTO_ENTRADA = "cab_tu_punto_entrada"
    T_CAB_TU_PUNTO_SALIDA = "cab_tu_punto_salida"

    # --- Filas de Cálculo que leen otras hojas (claves de Excel.filas)
    F_CANALES = "canales"
    F_TERCIOS = "tercios"
    F_CURVA = "curva"
    F_LIMITES = "limites"

    # --- Hoja Análisis: su propio estilo (el de Tony): Verdana, anillo
    #     más claro y otros anchos (del cuadro de diálogo de Excel). Dos
    #     tarjetas, una al lado de la otra: la izquierda (cabecera, ruido
    #     y negro, balances) y la derecha (sugerencia y tabla por zona).
    #     Entre las dos, relleno, anillo y relleno
    FUENTE_RESUMEN = "Verdana"
    LETRA_RESUMEN = 11
    LETRA_RESUMEN_TITULO = 16
    LETRA_RESUMEN_TABLA = 10
    LETRA_RESUMEN_NOTA = 9
    ANILLO_RESUMEN = "#D9D9D9"
    ANCHO_ANILLO_RESUMEN = 9.0
    ANCHO_RELLENO_RESUMEN = 1.86
    ANCHOS_RESUMEN = (22.57, 9.29) + ((12.29,) * 5)
    ANCHOS_RESUMEN_DERECHA = (10.71,) + ((12.29,) * 6)
    ENTRE_TARJETAS = 3

    # --- Tarjeta izquierda: las tablas con los tres canales (rótulo y un
    #     valor por canal) ocupan el ancho de su barra, así que el rótulo
    #     lleva las columnas que no usan los canales. En los balances, el
    #     recuadro de la nota ocupa las primeras
    COLUMNAS_ROTULO_RESUMEN = len(ANCHOS_RESUMEN) - CANALES
    COLUMNAS_NOTA_BALANCES = 2

    # --- Cabecera de la tarjeta izquierda: columnas del dato de cámara,
    #     fecha y bits (tras su rótulo) y de la caja de la exposición de la
    #     Z-V (rótulo y dato, las últimas)
    COLUMNAS_DATO_RESUMEN = 3
    COLUMNAS_CAJA_ZV = 2

    # --- Latitud por canal (Análisis): una fila por cifra, con su rótulo y
    #     la columna que ocupa en el bloque 1 de Cálculo (contada desde la
    #     del canal)
    COL_B1_TECHO = 3
    COL_B1_SUELO = 4
    COL_B1_RANGO = 5
    COL_B1_LINEAL = 6
    COL_B1_RECORTADO = 7
    COL_B1_SUELO_SUGERIDO = 8
    COL_B1_SUELO_EXCELENTE = 9
    COL_B1_LATITUD = 10
    T_LATITUD_CANAL = "latitud_canal"
    T_FILA_LATITUD = "fila_latitud"
    T_FILA_SOMBRA_ACEPTABLE = "fila_sombra_aceptable"
    T_FILA_LINEAL_HASTA = "fila_lineal_hasta"
    T_FILA_SE_RECORTA = "fila_se_recorta"
    T_FILA_SOMBRA_EXCELENTE = "fila_sombra_excelente"
    T_FILA_TECHO = "fila_techo"
    T_FILA_SUELO = "fila_suelo"
    T_FILA_RANGO = "fila_rango"
    FILAS_LATITUD_CANAL = (
        (T_FILA_LATITUD, COL_B1_LATITUD),
        (T_FILA_SOMBRA_ACEPTABLE, COL_B1_SUELO_SUGERIDO),
        (T_FILA_LINEAL_HASTA, COL_B1_LINEAL),
        (T_FILA_SE_RECORTA, COL_B1_RECORTADO),
        (T_FILA_SOMBRA_EXCELENTE, COL_B1_SUELO_EXCELENTE),
        (T_FILA_TECHO, COL_B1_TECHO),
        (T_FILA_SUELO, COL_B1_SUELO),
        (T_FILA_RANGO, COL_B1_RANGO))

    # --- La serie (cabecera de Análisis) y los avisos (su sección)
    T_TOMAS = "tomas"
    T_ANALIZABLE = "analizable"
    T_BALANCE_PERSONALIZADO = "balance_personalizado"
    T_SI = "si"
    T_NO = "no"
    T_AVISOS = "avisos"
    T_SIN_AVISOS = "sin_avisos"

    # --- Rejilla de Análisis: todas las filas del mismo alto (el de Excel
    #     por defecto), porque las dos tarjetas comparten filas; lo que
    #     necesita más ocupa varias combinadas: el título, las cabeceras
    #     (dos filas; tres, las altas) y las notas y los rótulos largos,
    #     según sus líneas. Alto de una línea (puntos) de las notas
    #     (Verdana 9) y de las tablas (Verdana 10), y cuánto más ancha es
    #     la letra de las tablas que la de Excel
    ALTO_REJILLA = 15
    FILAS_TITULO_RESUMEN = 2
    FILAS_CABECERA = 2
    FILAS_CABECERA_ALTA = 3
    ALTO_LINEA_NOTA = 11.25
    ALTO_LINEA_TABLA = 12.75
    ESCALA_LETRA_TABLA = 1.1

    # --- Decisiones propias (tarjeta derecha): filas en blanco para los
    #     puntos de la curva que elige el estudiante, en dos lados (desde
    #     la primera columna y desde la quinta: zona, entrada y salida)
    FILAS_DECISIONES = 5
    LADOS_DECISIONES = (0, 4)
    F_DECISIONES = "decisiones"
    SIN_ZONA = "—"
    """Zona de una decisión propia que no cuenta (el punto no se usa)."""
    T_DECISIONES = "decisiones"
    T_RECOMENDACIONES = "recomendaciones"
    T_VALIDA_ZONA = "valida_zona"
    T_VALIDA_CURVA = "valida_curva"

    # --- Tarjeta derecha: separador de las partes del texto de la
    #     sugerencia (el sugerido, la referencia y que es una sugerencia)
    #     y columnas del rótulo de las diferencias medias
    SEPARADOR_NOTAS = " "
    COLUMNAS_ROTULO_MEDIA = 5

    # --- L* leído (Análisis): lo escribe el estudiante (las zonas
    #     enteras) o el programa con las TIFF (las 31). Fila de su Z0
    #     (clave de Excel.filas), su columna (tras la de la zona) y color
    #     de lo estimado (los tercios sin L* leído, entre las dos zonas
    #     enteras vecinas)
    F_APUNTADO = "apuntado"
    COL_APUNTADO = 1
    COLOR_ESTIMADO = "#C2185B"
    T_CAB_L_APUNTADO = "cab_l_apuntado"
    T_ESTIMADO = "estimado"
    NUM_LSTAR = '0.0" L*"'
    NUM_BITS = '0" bits"'
    T_TITULO_RESUMEN = "titulo_resumen"
    T_MARCA_MODELO = "marca_modelo"
    T_FECHA = "fecha"
    T_BITS = "bits"
    T_FORMATO_FECHA = "formato_fecha"
    T_ZV = "zv"
    T_ISO = "iso"
    T_TV = "tv"
    T_F = "f"
    ROTULOS_EXP = (T_F, T_TV, T_ISO)
    """Rótulos de la exposición, en el orden de OECF.TextoExp."""
    T_SUGERENCIA = "sugerencia"
    T_REFERENCIA = "referencia"
    T_ES_SUGERENCIA = "es_sugerencia"
    T_SUGERIDO = "sugerido"
    T_DIF_MEDIA_SENSOR = "dif_media_sensor"
    T_DIF_MEDIA_REVELADOR = "dif_media_revelador"
    T_DIF_MEDIA_TU = "dif_media_tu"
    T_SIN_REVELADOR = "sin_revelador"
    T_NOTA_TEXTURAS_RESUMEN = "nota_texturas_resumen"
    T_SIN_TELA = "sin_tela"
    T_SEPARADOR_DECIMAL = "separador_decimal"

    # --- Zonas de la latitud de texturas en Análisis: en tercios (8 1/3)
    NUM_TERCIOS = "# ?/3"

    # --- Hoja Gráficos: seis huecos (dos columnas × tres filas) de 6
    #     columnas × 18 filas con borde gris, separados por una columna y
    #     una fila; cada gráfica, a 3 px de la esquina de su hueco
    ANCHOS_GRAF = ((15.0,) * 6) + (3.0,) + ((15.0,) * 6)
    COLUMNAS_HUECO = 6
    FILAS_HUECO = 18
    FILA_HUECOS = 5
    BORDE_HUECO = "#7F7F7F"
    MEDIDA_GRAF = (654, 354)
    MARGEN_GRAF = 3

    # --- Colores y trazos de las gráficas: canales, esperado (gris
    #     grueso, algo transparente), objetivo, sensor y barras lilas
    COLORES_CANALES = ("#C0392B", "#2E8B57", "#1F5FA8")
    """Colores de las series de cada canal: rojo, verde y azul."""
    FORMA_REDONDA = "circle"
    """Forma de los marcadores si no se dice otra."""
    FORMAS_CANALES = ("square", FORMA_REDONDA, "triangle")
    """Formas de los marcadores de cada canal (rojo, verde y azul): distintas
    para leer las series aunque se solapen."""
    COLOR_ESPERADO = "#808080"
    """Color de la serie del esperado."""
    TRANSPARENCIA_ESPERADO = 60
    """Transparencia de la serie del esperado, en porcentaje."""
    ANCHO_ESPERADO = 3
    """Grosor de la línea del esperado (más gruesa que las demás)."""
    COLOR_OBJETIVO = "#7B3FA0"
    """Color de la serie del objetivo."""
    COLOR_SENSOR = "#E08A1E"
    """Color de la serie del sensor."""
    COLOR_BARRAS = "#B39DDB"
    ANCHO_BARRAS = 3
    COLOR_NEGATIVO = "#C0392B"
    MEDIDA_MARCADOR = 4
    GIRO_ZONAS = -45
    LETRA_ZONAS = 8

    # --- Ejes: (mínimo, máximo, paso, formato de los números; si no, los
    #     ejes copian el de las celdas, con decimales de sobra). El
    #     segundo eje de la de esperado y obtenido, en pasos respecto a
    #     la Z-V: el primero menos C_ZONA_ZV
    EJE_ZONAS = (-4, 10, 1, "0")
    EJE_DESV_LINEAL = (-0.2, 0.2, 0.05, "+0.00;-0.00;0")
    EJE_DESV_COMPLETA = (-1.5, 0.5, 0.5, "+0.0;-0.0;0")
    EJE_SNR = (1, 1000, None, "0")
    BASE_EJE_SNR = 10
    EJE_LSTAR = (0, 100, 20, "0")
    """Eje de L*: mínimo, máximo, paso y formato de número."""
    EJE_DIF_LSTAR = (-25, 25, 5, "+0;-0;0")
    EJE_KELVIN = (2000, 10000, 1000, "0")

    # --- Textos de Gráficos
    T_TITULO_GRAF = "titulo_graf"
    T_NOTA_GRAF = "nota_graf"
    T_G_ESPERADO = "g_esperado"
    T_G_DESV_LINEAL = "g_desv_lineal"
    T_G_DESV_COMPLETA = "g_desv_completa"
    T_G_SNR = "g_snr"
    T_G_CURVA = "g_curva"
    T_G_DIFERENCIA = "g_diferencia"
    T_G_TU_CURVA = "g_tu_curva"
    T_G_BALANCES = "g_balances"
    T_S_TU_CURVA = "s_tu_curva"
    T_EJE_KELVIN = "eje_kelvin"

    # --- Orden de las gráficas en la hoja (de izquierda a derecha y de
    #     arriba abajo): primero lo que más interesa al estudiante (Tony).
    #     Su número en el título sale de aquí. Las de auditoría (el
    #     sensor), al final de Cálculo, sin número, una al lado de otra
    ORDEN_GRAF = (T_G_CURVA, T_G_DIFERENCIA, T_G_TU_CURVA,
                  T_G_DESV_LINEAL, T_G_BALANCES, T_G_SNR)
    """Orden de las gráficas en la hoja; da su número en el título."""
    GRAF_AUDITORIA = (T_G_ESPERADO, T_G_DESV_COMPLETA)
    F_AUDITORIA = "auditoria"
    COLUMNAS_AUDITORIA = 8
    T_AUDITORIA = "auditoria"
    FORMATO_TITULO_GRAF = "{numero}. {titulo}"
    """Título numerado de una gráfica: «número. título»."""
    T_EJE_ZONA = "eje_zona"
    T_EJE_SIGNAL = "eje_signal"
    T_EJE_PASOS = "eje_pasos"
    T_EJE_DEV = "eje_dev"
    T_EJE_SNR = "eje_snr"
    T_EJE_LSTAR = "eje_lstar"
    T_EJE_DIF_LSTAR = "eje_dif_lstar"
    T_S_MIN = "s_min"
    T_S_EXCELENTE = "s_excelente"
    T_S_ING = "s_ing"
    T_S_MODELO = "s_modelo"
    T_S_SENSOR = "s_sensor"
    T_S_REVELADOR = "s_revelador"

    # --- Hoja Rechazadas: anchos (C a I), colores de cada motivo en el
    #     gráfico, eje de las zonas y textos
    ANCHOS_RECHAZADAS = (24.0, 12.0, 16.0, 14.0, 12.0, 12.0, 12.0)

    # --- Hoja IA: las instrucciones para revisarlo con una IA (de su
    #     archivo, K.ruta_prompt_ia), una línea por fila. Las de
    #     título, en negrita
    ANCHO_IA = 100.0
    MARCA_TITULO_IA = "#"
    T_MOTIVO_NIVEL = "motivo_nivel"
    T_MOTIVO_DISP = "motivo_disp"
    T_MOTIVO_ASIM = "motivo_asim"
    MOTIVOS = ((KTE.RECHAZO_NIVEL, T_MOTIVO_NIVEL, "#E08A1E"),
               (KTE.RECHAZO_DISP, T_MOTIVO_DISP, "#1F5FA8"),
               (KTE.RECHAZO_ASIM, T_MOTIVO_ASIM, "#7B3FA0"))
    EJE_POS = (0, 10, 1, "0")

    # --- Qué significa cada motivo (junto a su recuento): claves de sus
    #     textos, que llevan los umbrales de oecfCalc.KTE
    T_EXPLICA_NIVEL = "explica_nivel"
    T_EXPLICA_DISP = "explica_disp"
    T_EXPLICA_ASIM = "explica_asim"
    EXPLICA_MOTIVO = {KTE.RECHAZO_NIVEL: T_EXPLICA_NIVEL,
                      KTE.RECHAZO_DISP: T_EXPLICA_DISP,
                      KTE.RECHAZO_ASIM: T_EXPLICA_ASIM}
    NUM_DEV = "+0.00;-0.00;0"
    T_TITULO_RECHAZADAS = "titulo_rechazadas"
    T_NOTA_RECHAZADAS = "nota_rechazadas"
    T_RECUENTO = "recuento"
    T_CAB_CONCEPTO = "cab_concepto"
    T_TESELAS_TARJETA = "teselas_tarjeta"
    T_TESELAS_RECHAZADAS = "teselas_rechazadas"
    T_PORCENTAJE = "porcentaje"
    T_POR_MOTIVO = "por_motivo"
    T_G_RECHAZADAS = "g_rechazadas"
    T_DATOS_GRAF = "datos_graf"
    T_CAB_POS = "cab_pos"
    T_CAB_MOTIVO = "cab_motivo"
    T_CAB_DEV = "cab_dev"

    # --- Hoja ISO (secuencia de ISO, en verde): anchos de sus columnas
    #     (ISO, Z2, desviación, lectura, ruido en Z-V y Z2, textura,
    #     textura/ruido, % del umbral, textura en sombras, sombras con
    #     textura desde y nota) y textos
    ANCHOS_ISO = (8.0, 8.0, 13.0, 13.0, 11.0, 11.0, 11.0, 13.0, 11.0, 15.0,
                  15.0, 30.0)
    T_TITULO_ISO = "titulo_iso"
    T_NOTA_ISO = "nota_iso"
    T_CAB_ISO = "cab_iso"
    T_CAB_Z2 = "cab_z2"
    T_CAB_DESVIACION_ISO = "cab_desviacion_iso"
    T_CAB_LECTURA_ISO = "cab_lectura_iso"
    T_CAB_RUIDO_ZV = "cab_ruido_zv"
    T_CAB_RUIDO_Z2 = "cab_ruido_z2"
    T_CAB_TEXTURA_Z2 = "cab_textura_z2"
    T_CAB_TEXTURA_RUIDO_Z2 = "cab_textura_ruido_z2"
    T_CAB_PORCENTAJE_UMBRAL = "cab_porcentaje_umbral"
    T_CAB_SE_APRECIA = "cab_se_aprecia"
    T_CAB_NOTA_ISO = "cab_nota_iso"
    T_ISO_ESTIMADO = "iso_estimado"
    T_ISO_SIN_MEDIR = "iso_sin_medir"

    # --- Secuencia de ISO para el estudiante (PDF): exposición, textura
    #     en sombras (semáforo: se pierde, justa, se ve; en ese orden, el
    #     de NivelTextura) y la conclusión
    T_NOTA_ISO_PDF = "nota_iso_pdf"
    T_CAB_EXPOSICION_ISO = "cab_exposicion_iso"
    T_EXPOSICION_IGUAL = "exposicion_igual"
    T_EXPOSICION_CLARA = "exposicion_clara"
    T_EXPOSICION_OSCURA = "exposicion_oscura"
    T_TEXTURA_ISO = ("textura_se_pierde", "textura_justa", "textura_se_ve")
    T_CAB_SOMBRAS_ISO = "cab_sombras_iso"
    T_SOMBRAS_ISO = "sombras_iso"
    T_SOMBRAS_NINGUNA = "sombras_ninguna"

    # --- Leyenda de los colores del texto
    T_LEYENDA = "leyenda"
    T_LEYENDA_DATO = "leyenda_dato"
    T_LEYENDA_LITERAL = "leyenda_literal"
    T_LEYENDA_FORMULA = "leyenda_formula"
    T_LEYENDA_ROTULO = "leyenda_rotulo"


#
class PuntoCurva(NamedTuple):
    """
    Una zona de la curva tonal en L*: su posición (tercioEV) y su nombre,
    la luz y el L* esperados, el objetivo, la luz y el L* del sensor y
    del revelador (None sin dato) y la entrada y la salida de la curva de
    Lightroom (de 0 a C_ESCALA_CURVA; la entrada, None sin revelador).
    """
    tercio_ev: int
    nombre: str
    luz_esperada: float
    esperado: float
    objetivo: float
    luz_sensor: float | None
    sensor: float | None
    luz_revelador: float | None
    revelador: float | None
    entrada: int | None
    salida: int


#
class DatosSerie(NamedTuple):
    """
    Lo de la serie que el libro enseña en Análisis y que no sale de lo
    medido: los avisos (las incidencias, ya con su frase en el idioma del
    libro), si se puede analizar, si hay balance personalizado, cuántas
    tomas tiene y, de la secuencia de ISO, la exposición de la ZV de cada
    ISO (la del PDF; vacía sin secuencia).
    """
    avisos: tuple[str, ...]
    esAnalizable: bool
    esBalancePersonalizado: bool
    tomas: int
    expISO: tuple[Exp, ...] = ()


#
class Excel(object):
    """
    Libro Excel de una serie. Se crea con la ruta, los textos ya
    traducidos ({clave de KXL: texto}), lo medido en los RAW (Review) y
    lo de la serie que enseña Análisis (DatosSerie); escribir() lo graba.
    """

    __slots__ = ["__datos", "__filas", "__formatos", "__hojas", "__excel",
                 "__revelador", "__serie", "__textos"]

    #
    def __init__(self, ruta: Path, textos: dict[str, str],
                 datos: Review, serie: DatosSerie) -> None:

        # --- Variables de instancia. filas: dónde quedó cada bloque de
        #     Datos (KXL.F_*), para las fórmulas de las demás hojas
        self.__textos: dict[str, str] = self.con_nombres(textos)
        self.__datos: Review = datos
        self.__serie: DatosSerie = serie
        # --- use_future_functions: MAXIFS y MINIFS (tu curva) llevan el
        #     prefijo que Excel pide a las funciones nuevas
        self.__excel = xlsxwriter.Workbook(
            str(ruta), {"use_future_functions": True})
        self.__formatos: dict[tuple, Format] = {}
        self.__hojas: dict[str, Worksheet] = {}
        self.__filas: dict[str, int] = {}

        # --- L* del revelador por zona, como sale en Datos: el leído y,
        #     en los tercios sin él, el estimado (None: sin dato)
        self.__revelador: list[float | None] = self.revelador_estimado()

        # --- Fuente por defecto de todas las celdas
        self.__excel.formats[0].set_font_name(KXL.FUENTE)
        self.__excel.formats[0].set_font_size(KXL.LETRA)

        # --- Las hojas, en su orden, antes de escribir ninguna: las
        #     fórmulas de unas leen de otras. La de la secuencia de ISO,
        #     solo si la serie la tiene
        for clave in KXL.HOJAS:
            if (clave == KXL.T_HOJA_ISO) and (not datos.isos):
                continue
            self.__hojas[clave] = self.__excel.add_worksheet(textos[clave])

    #
    # --- Métodos públicos
    #
    # region Métodos públicos

    #
    @property
    def review(self) -> Review:
        """ Saber lo medido en los RAW con que se hace el libro. """
        return self.__datos

    #
    def escribir(self) -> None:
        """ Escribe todas las hojas y graba el libro. """
        self.hoja_constantes()
        self.hoja_datos()
        self.hoja_calculo()
        self.hoja_resumen()
        self.bloque_tu_curva()
        self.revelador_datos()
        self.hoja_graf()
        self.hoja_rechazadas()
        self.hoja_ia()
        if KXL.T_HOJA_ISO in self.__hojas:
            self.hoja_iso()
        for clave in KXL.HOJAS_OCULTAS:
            self.__hojas[clave].hide()
        self.__excel.close()

    #
    def hoja_datos(self) -> None:
        """
        Hoja Datos: lo leído de los RAW, sin cálculos salvo la media de
        las Z-V. La serie por zonas, las demás Z-V, su media, el ruido de
        lectura y la tabla del L* medido (vacía: la rellena el usuario).
        """
        t, d = self.__textos, self.__datos
        hoja = self.__hojas[KXL.T_HOJA_DATOS]
        fila, col = KXL.FILA_INICIO, KXL.COLUMNA_INICIO
        canales = (t[KXL.T_CAB_ROJO], t[KXL.T_CAB_VERDE], t[KXL.T_CAB_AZUL])
        cabecera = ((t[KXL.T_CAB_ZONA], t[KXL.T_CAB_TERCIOS],
                     t[KXL.T_CAB_ARCHIVO]) + canales
                    + (t[KXL.T_CAB_DISP_ROJO], t[KXL.T_CAB_DISP_VERDE],
                       t[KXL.T_CAB_DISP_AZUL]))
        self.titulo(hoja, fila, col, t[KXL.T_TITULO_DATOS],
                    t[KXL.T_NOTA_DATOS],
                    KXL.ANCHOS_DATOS)

        # --- Serie por zonas: una fila por zona, de Z0 a ZX
        fila += 3
        hoja.write(fila, col, t[KXL.T_SERIE_ZONAS], self.apartado())
        fila += 1
        self.cabecera(hoja, fila, col, cabecera)
        hoja.set_row(fila, KXL.ALTO_CABECERA)
        self.__filas[KXL.F_ZONAS] = fila + 1
        for i, toma in enumerate(d.zonas):
            fila += 1
            self.fila_serie(hoja, fila, col, i - KS.TERCIOS_LADO, toma,
                            (i % 2) == 0)

        # --- Las demás Z-V de la serie (huecos vacíos si hay menos)
        fila += 2
        hoja.write(fila, col, t[KXL.T_CONTROL], self.apartado())
        fila += 1
        self.cabecera(hoja, fila, col, cabecera)
        hoja.set_row(fila, KXL.ALTO_CABECERA)
        self.__filas[KXL.F_CONTROL] = fila + 1
        control = d.control[:KXL.CONTROLES]
        for i in range(KXL.CONTROLES):
            fila += 1
            toma = control[i] if (i < len(control)) else None
            self.fila_serie(hoja, fila, col, 0, toma, (i % 2) == 0)

        # --- Media de todas las Z-V: la de la serie y las de control
        fila += 2
        hoja.write(fila, col, t[KXL.T_MEDIA_ZV], self.apartado())
        fila += 1
        self.__filas[KXL.F_MEDIA] = fila
        literal = self.celda(KXL.COLOR_LITERAL, True, "center")
        hoja.write(fila, col, self.nombre_zona(0), literal)
        hoja.write_blank(fila, col + 1, None, literal)
        hoja.write(fila, col + 2, t[KXL.T_MEDIA],
                   self.celda(KXL.COLOR_ROTULO, True, "center"))
        # --- Solo entran las Z-V de control cuyo verde se aparta de la
        #     ZV como mucho C_TOLERANCIA_LINEAL (si no, la luz cambió): una
        #     fórmula matricial, que lee la constante
        fila_zv = self.__filas[KXL.F_ZONAS] + KS.TERCIOS_LADO
        desde = self.__filas[KXL.F_CONTROL]
        hasta = desde + KXL.CONTROLES - 1
        c_verde = col + KXL.COL_VALORES + 1
        verdes = (f"{xl_rowcol_to_cell(desde, c_verde, False, True)}:"
                  f"{xl_rowcol_to_cell(hasta, c_verde, False, True)}")
        verde_zv = xl_rowcol_to_cell(fila_zv, c_verde, False, True)
        entra = (f"IF(ISNUMBER({verdes}),IF(ABS(LOG({verdes}/{verde_zv},"
                 f"{KXL.C_FACTOR_ZONA}))<={KXL.C_TOLERANCIA_LINEAL},1,0),0)")
        zv = d.zonas[KS.TERCIOS_LADO]
        desviados = d.controlesDesviados
        valores = [v for v in ([zv] + [z for z in control
                                       if z not in desviados])
                   if v is not None]
        for j in range(2 * KXL.CANALES):
            c = col + KXL.COL_VALORES + j
            celdas = (f"{xl_rowcol_to_cell(desde, c)}:"
                      f"{xl_rowcol_to_cell(hasta, c)}")
            cifras = [(v.nivelRGB + v.dispRGB)[j] for v in valores]
            self.formula_matriz(
                hoja, fila, c, fila, c,
                f"{{=({xl_rowcol_to_cell(fila_zv, c)}+SUM({entra}*"
                f"IF(ISNUMBER({celdas}),{celdas},0)))/(1+SUM({entra}))}}",
                self.celda(KXL.COLOR_FORMULA, True, "center",
                           KXL.NUM_UNO if (j < KXL.CANALES)
                           else KXL.NUM_TRES),
                (sum(cifras) / len(cifras)) if cifras else "")
        disp_zv = [(sum(v.dispRGB[j] for v in valores)
                   / len(valores)) if valores else None
                   for j in range(KXL.CANALES)]

        # --- Ruido de lectura por canal: el de la franja oscura del sensor
        #     (sin ella, el rótulo lo dice y los números quedan en blanco),
        #     el de la superficie real con las tomas tapadas (en blanco si
        #     no hay) y el negro restado, con su origen
        fila += 2
        hoja.write(fila, col, t[KXL.T_RUIDO], self.apartado())
        fila += 1
        self.cabecera(hoja, fila, col, (t[KXL.T_CAB_ORIGEN], "", "")
                      + canales)
        filas_ruido = [
            (KXL.F_RUIDO,
             t[KXL.T_ORIGEN_BORDE if d.ruidoBordeRGB else KXL.T_SIN_BORDE],
             d.ruidoBordeRGB, KXL.NUM_DOS),
            (KXL.F_RUIDO_TAPADAS, t[KXL.T_COMPARAR_TAPADAS],
             d.ruidoTapadasRGB, KXL.NUM_DOS),
            (KXL.F_NEGRO, t[KXL.ORIGEN_NEGRO[d.origen_negro]],
             d.negroRGB, KXL.NUM_ENTERO)]
        for i, (clave, texto, valores, numero) in enumerate(filas_ruido):
            fila += 1
            banda = (i % 2) == 0
            self.__filas[clave] = fila
            literal_i = self.celda(KXL.COLOR_LITERAL, banda, "center")
            self.rotulo_fila(hoja, fila, col, texto, literal_i)
            self.fila_canales(hoja, fila, col, valores, banda, numero)

        # --- Avisos del ruido (antes bajo el bloque de Análisis): sin
        #     ruido de lectura, y franja y tapadas que no casan
        avisos = []
        if d.ruidoRGB is None:
            avisos.append(t[KXL.T_SIN_RUIDO_SUELO])
        if d.difieren:
            avisos.append(t[KXL.T_RUIDOS_DIFIEREN].format(
                porcentaje=round(KTE.DIFERENCIA_RUIDO * KXL.CIEN)))
        for aviso in avisos:
            fila += 1
            self.nota(hoja, fila, col, aviso, KXL.ANCHOS_DATOS)

        # --- Píxeles defectuosos: calientes (con las tapadas) y muertos,
        #     por megapíxel
        lineas = self.lineas_pixeles()
        if lineas:
            fila += 2
            hoja.write(fila, col, t[KXL.T_PIXELES], self.apartado())
            for i, linea in enumerate(lineas):
                fila += 1
                hoja.merge_range(
                    fila, col, fila, col + KXL.COL_VALORES + KXL.CANALES - 1,
                    linea, self.celda(KXL.COLOR_LITERAL, (i % 2) == 0,
                                      "left"))

        # --- Curva de transferencia del ruido (de las zonas): lectura,
        #     ganancia y parte proporcional por canal; el ruido aleatorio
        #     de la Z-V (con una de control) y, por fórmula, lo fijo (lo
        #     que queda de la dispersión media de las Z-V); y los
        #     megapíxeles del sensor (para normalizar la señal/ruido)
        fila += 2
        hoja.write(fila, col, t[KXL.T_TRANSFERENCIA], self.apartado())
        self.nota(hoja, fila + 1, col, t[KXL.T_NOTA_TRANSFERENCIA],
                  KXL.ANCHOS_DATOS)
        fila += 2
        self.cabecera(hoja, fila, col, (t[KXL.T_CAB_CONCEPTO], "", "")
                      + canales)
        curvas = d.transferenciaRGB
        aleatorio = d.aleatorioRGB
        filas_curva = (
            (KXL.F_LECTURA, KXL.T_LECTURA, KXL.NUM_DOS,
             tuple(c.lectura for c in curvas) if curvas else None),
            (KXL.F_GANANCIA, KXL.T_GANANCIA, KXL.NUM_TRES,
             tuple(c.ganancia for c in curvas) if curvas else None),
            (KXL.F_PROPORCIONAL, KXL.T_PROPORCIONAL, KXL.NUM_PORCENTAJE,
             tuple(c.proporcional for c in curvas) if curvas else None),
            (KXL.F_ALEATORIO, KXL.T_ALEATORIO_ZV, KXL.NUM_CUATRO,
             aleatorio))
        for i, (clave, texto, numero, valores_curva) in enumerate(
                filas_curva):
            fila += 1
            banda = (i % 2) == 0
            self.__filas[clave] = fila
            literal_i = self.celda(KXL.COLOR_LITERAL, banda, "center")
            self.rotulo_fila(hoja, fila, col, t[texto], literal_i)
            self.fila_canales(hoja, fila, col, valores_curva, banda, numero)

        # --- Lo fijo de la Z-V: raíz de (dispersión media² − aleatorio²)
        fila += 1
        banda = (len(filas_curva) % 2) == 0
        self.__filas[KXL.F_FIJO] = fila
        literal_i = self.celda(KXL.COLOR_LITERAL, banda, "center")
        self.rotulo_fila(hoja, fila, col, t[KXL.T_FIJO_ZV], literal_i)
        formula_i = self.celda(KXL.COLOR_FORMULA, banda, "center",
                               KXL.NUM_CUATRO)
        for j in range(KXL.CANALES):
            c = col + KXL.COL_VALORES + j
            total = xl_rowcol_to_cell(self.__filas[KXL.F_MEDIA],
                                      c + KXL.CANALES)
            azar = xl_rowcol_to_cell(self.__filas[KXL.F_ALEATORIO], c)
            dz = disp_zv[j]
            self.formula(
                hoja, fila, c, f'=IF(AND(ISNUMBER({total}),ISNUMBER({azar})),'
                f'SQRT(MAX(0,{total}^2-{azar}^2)),"")', formula_i,
                math.sqrt(max(0.0, (dz ** 2) - (aleatorio[j] ** 2)))
                if (aleatorio and (dz is not None)) else "")

        # --- Megapíxeles del sensor (un solo valor, en la primera columna)
        fila += 1
        banda = ((len(filas_curva) + 1) % 2) == 0
        self.__filas[KXL.F_MPX] = fila
        literal_i = self.celda(KXL.COLOR_LITERAL, banda, "center")
        self.rotulo_fila(hoja, fila, col, t[KXL.T_MPX_SENSOR], literal_i)
        hoja.write_number(fila, col + KXL.COL_VALORES,
                          d.alto * d.ancho / KTR.PX_MPX,
                          self.celda(KXL.COLOR_DATO, banda, "center",
                                     KXL.NUM_UNO))

        # --- Balances de blancos de la cámara (sin repetir los iguales):
        #     balance, archivo, Kelvin de la cámara y reales y los
        #     multiplicadores rojo y azul (el verde es 1)
        fila += 2
        hoja.write(fila, col, t[KXL.T_BALANCES], self.apartado())
        self.nota(hoja, fila + 1, col, t[KXL.T_NOTA_BALANCES],
                  KXL.ANCHOS_DATOS)
        fila += 2
        self.cabecera(hoja, fila, col, (
            t[KXL.T_CAB_BALANCE], "", t[KXL.T_CAB_ARCHIVO],
            t[KXL.T_CAB_KELVIN_ANOTADO], t[KXL.T_CAB_KELVIN_MEDIDO],
            t[KXL.T_CAB_MULT_ROJO], t[KXL.T_CAB_MULT_AZUL]))
        hoja.set_row(fila, KXL.ALTO_CABECERA)
        self.__filas[KXL.F_BALANCES] = fila + 1
        balances = d.balancesDistintos
        if not balances:
            fila += 1
            hoja.write(fila, col, t[KXL.T_SIN_BALANCES], literal)
        for i, balance in enumerate(balances):
            fila += 1
            banda = (i % 2) == 0
            dato = self.celda(KXL.COLOR_DATO, banda, "center")
            hoja.write(fila, col, self.nombre_balance(balance.nombre), dato)
            hoja.write_blank(fila, col + 1, None, dato)
            hoja.write(fila, col + 2, balance.archivo, dato)
            valores = ((balance.kelvin_cam, KXL.NUM_ENTERO),
                       (balance.kelvin, KXL.NUM_ENTERO),
                       (balance.multiplicadores[0]
                        if balance.multiplicadores else None, KXL.NUM_TRES),
                       (balance.multiplicadores[2]
                        if balance.multiplicadores else None, KXL.NUM_TRES))
            for j, (valor, numero) in enumerate(valores):
                formato = self.celda(KXL.COLOR_DATO, banda, "center", numero)
                if valor is None:
                    hoja.write_blank(fila, col + KXL.COL_VALORES + j, None,
                                     formato)
                else:
                    hoja.write_number(fila, col + KXL.COL_VALORES + j, valor,
                                      formato)

        # --- Paño por zona: dispersión y fracción recortada de cada canal
        #     (en blanco sin paño). Lo lee la latitud de texturas
        fila += 2
        hoja.write(fila, col, t[KXL.T_TELA], self.apartado())
        self.nota(hoja, fila + 1, col, t[KXL.T_NOTA_TELA],
                  KXL.ANCHOS_DATOS)
        fila += 2
        self.cabecera(hoja, fila, col, (
            t[KXL.T_CAB_ZONA], t[KXL.T_CAB_TERCIOS], t[KXL.T_CAB_ARCHIVO],
            t[KXL.T_CAB_DISP_ROJO], t[KXL.T_CAB_DISP_VERDE],
            t[KXL.T_CAB_DISP_AZUL], t[KXL.T_CAB_TELA_REC_ROJO],
            t[KXL.T_CAB_TELA_REC_VERDE], t[KXL.T_CAB_TELA_REC_AZUL],
            t[KXL.T_CAB_TELA_PIXEL], t[KXL.T_CAB_TARJETA_PIXEL]))
        hoja.set_row(fila, KXL.ALTO_CABECERA)
        self.__filas[KXL.F_TELA] = fila + 1
        for i, toma in enumerate(d.zonas):
            fila += 1
            banda = (i % 2) == 0
            self.zona_y_tercios(hoja, fila, col, i - KS.TERCIOS_LADO, banda)
            dato = self.celda(KXL.COLOR_DATO, banda, "center")
            archivo = col + KXL.COL_VALORES - 1
            if toma is None:
                hoja.write_blank(fila, archivo, None, dato)
            else:
                hoja.write(fila, archivo, toma.archivo, dato)
            for desp, valores, numero in (
                    (0, toma.telaDispRGB if toma else None,
                     KXL.NUM_TRES),
                    (KXL.CANALES, toma.telaRecortadoRGB if toma else None,
                     KXL.NUM_PORCENTAJE)):
                self.fila_canales(hoja, fila, col + desp, valores, banda,
                                  numero)
            formato = self.celda(KXL.COLOR_DATO, banda, "center",
                                 KXL.NUM_TRES)
            for c, valor in zip((KXL.COL_TELA_PIXEL,
                                 KXL.COL_TARJETA_PIXEL),
                                self.disp_textura(toma)):
                if (valor is None) or (not math.isfinite(valor)):
                    hoja.write_blank(fila, col + c, None, formato)
                else:
                    hoja.write_number(fila, col + c, valor, formato)

        # --- L* del revelador por zona: lee el L* leído de Análisis y
        #     estima los tercios que no lo tienen. Sus fórmulas, en
        #     revelador_datos (leen de Cálculo y de Análisis)
        fila += 2
        hoja.write(fila, col, t[KXL.T_REVELADOR], self.apartado())
        self.nota(hoja, fila + 1, col, t[KXL.T_NOTA_REVELADOR],
                  KXL.ANCHOS_DATOS)
        fila += 2
        self.cabecera(hoja, fila, col, (t[KXL.T_CAB_ZONA],
                                        t[KXL.T_CAB_TERCIOS],
                                        t[KXL.T_CAB_REVELADOR],
                                        t[KXL.T_CAB_CONTRASTE]))
        self.__filas[KXL.F_REVELADOR] = fila + 1
        contrastes = self.contrastes()
        for i in range((2 * KS.TERCIOS_LADO) + 1):
            fila += 1
            banda = (i % 2) == 0
            tercio_ev = i - KS.TERCIOS_LADO
            self.zona_y_tercios(hoja, fila, col, tercio_ev, banda)

            # --- El contraste de la trama del paño: un dato medido en
            #     las exportaciones (en blanco sin él)
            formato = self.celda(KXL.COLOR_DATO, banda, "center",
                                 KXL.NUM_UNO)
            if contrastes[i] is None:
                hoja.write_blank(fila, col + KXL.COL_CONTRASTE, None,
                                 formato)
            else:
                hoja.write_number(fila, col + KXL.COL_CONTRASTE,
                                  contrastes[i], formato)

        self.marco(hoja, ((fila, KXL.ANCHOS_DATOS),))

    #
    def hoja_constantes(self) -> None:
        """
        Hoja Constantes: cada constante del método con su nombre definido
        en el libro, las derivadas (con fórmula), la nota de C_SNR_MINIMA y
        la leyenda de los colores.
        """
        t = self.__textos
        hoja = self.__hojas[KXL.T_HOJA_CONSTANTES]
        nombre_hoja = t[KXL.T_HOJA_CONSTANTES]
        fila, col = KXL.FILA_INICIO, KXL.COLUMNA_INICIO

        self.titulo(hoja, fila, col, t[KXL.T_TITULO_CONSTANTES],
                    t[KXL.T_NOTA_CONSTANTES],
                    KXL.ANCHOS_CONSTANTES)
        fila += 3
        self.cabecera(hoja, fila, col, (t[KXL.T_CAB_NOMBRE],
                                        t[KXL.T_CAB_VALOR],
                                        t[KXL.T_CAB_UNIDAD],
                                        t[KXL.T_CAB_QUE_ES]))

        # --- Una fila por constante, por orden alfabético; las derivadas,
        #     con su fórmula y su valor calculado (si no, el archivo
        #     guarda 0 y un visor que no recalcula lo muestra). «Qué es»,
        #     partido en líneas
        k = self.valores_constantes()
        ancho_que_es = KXL.ANCHOS_CONSTANTES[3]
        for i, (nombre, valor, unidad) in enumerate(sorted(
                KXL.CONSTANTES + KXL.DERIVADAS,
                key=lambda constante: constante[0].casefold())):
            fila += 1
            banda = (i % 2) == 0
            es_formula = isinstance(valor, str) and valor.startswith("=")
            hoja.write(fila, col, nombre,
                       self.celda(KXL.COLOR_LITERAL, banda, "left"))
            if es_formula:
                self.formula(
                    hoja, fila, col + 1, str(valor),
                    self.celda(KXL.COLOR_FORMULA, banda, "center",
                               KXL.NUM_CUATRO), k[nombre])
            else:
                hoja.write(fila, col + 1,
                           t[valor] if isinstance(valor, str) else valor,
                           self.celda(KXL.COLOR_LITERAL, banda, "center"))
            hoja.write(fila, col + 2, t[unidad],
                       self.celda(KXL.COLOR_ROTULO, banda, "center"))
            hoja.write(fila, col + 3, t[nombre],
                       self.celda(KXL.COLOR_ROTULO, banda, "left",
                                  text_wrap=True, valign="top"))
            lineas = self.lineas(t[nombre], ancho_que_es)
            if lineas > 1:
                hoja.set_row(fila, KXL.ALTO_LINEA * lineas)
            self.__excel.define_name(
                nombre, f"='{nombre_hoja}'!"
                f"{xl_rowcol_to_cell(fila, col + 1, True, True)}")

        # --- Nota de C_SNR_MINIMA: la primera línea, con su valor por fórmula
        fila += 2
        snr = KXL.C_SNR_MINIMA
        valor_snr = self.valores_constantes()[snr]
        antes, tras = t[KXL.T_NOTA_SNR_ANTES], t[KXL.T_NOTA_SNR_TRAS]
        self.nota(hoja, fila, col, f"{antes}{valor_snr}{tras}",
                  KXL.ANCHOS_CONSTANTES,
                  self.formato(font_color=KXL.COLOR_ROTULO, bold=True,
                               text_wrap=True, valign="top"),
                  f"={self.cadena(antes)}&{snr}&{self.cadena(tras)}")
        for clave in (KXL.T_NOTA_SNR_ISO, KXL.T_NOTA_SNR_USUARIO):
            fila += 1
            self.nota(hoja, fila, col, t[clave], KXL.ANCHOS_CONSTANTES)

        # --- Leyenda: cada tipo de texto en su color
        fila += 2
        hoja.write(fila, col, t[KXL.T_LEYENDA], self.apartado())
        for clave, color in ((KXL.T_LEYENDA_DATO, KXL.COLOR_DATO),
                             (KXL.T_LEYENDA_LITERAL, KXL.COLOR_LITERAL),
                             (KXL.T_LEYENDA_FORMULA, KXL.COLOR_FORMULA),
                             (KXL.T_LEYENDA_ROTULO, KXL.COLOR_ROTULO)):
            fila += 1
            hoja.write(fila, col, t[clave], self.texto(color, negrita=True))

        self.marco(hoja, ((fila, KXL.ANCHOS_CONSTANTES),))

    #
    def hoja_calculo(self) -> None:
        """
        Hoja Cálculo: lee de Datos y de Constantes. Bloque 1, por canal
        (techo, suelo, linealidad, recorte y latitud); bloque 2, por
        zona (obtenido, desviación, recorte y señal/ruido); bloque 3, la
        curva tonal (esperado, sensor y revelador). Cada fórmula, con su
        resultado; si falta un dato, en blanco.
        """
        t, d, f = self.__textos, self.__datos, self.__filas
        hoja = self.__hojas[KXL.T_HOJA_CALCULO]
        fila, col = KXL.FILA_INICIO, KXL.COLUMNA_INICIO
        k = self.valores_constantes()
        n = (2 * KS.TERCIOS_LADO) + 1
        cols_datos = [KXL.COLUMNA_INICIO + KXL.COL_VALORES + j
                      for j in range(2 * KXL.CANALES)]
        medias = self.medias_zv()
        topes = self.topes()
        disp = [z.dispRGB if z else None for z in d.zonas]
        self.titulo(hoja, fila, col, t[KXL.T_TITULO_CALCULO],
                    t[KXL.T_NOTA_CALCULO],
                    KXL.ANCHOS_CALCULO)

        # --- Posiciones de los bloques (los tres se leen entre sí)
        fila_b1 = fila + 6
        fila_b2 = fila_b1 + KXL.CANALES + 4
        fila_b3 = fila_b2 + n + 4
        f[KXL.F_CANALES], f[KXL.F_TERCIOS], f[KXL.F_CURVA] = (
            fila_b1, fila_b2, fila_b3)
        celda = xl_rowcol_to_cell

        rango = partial(Excel.rango_columna, fila_b2, n)

        # --- Bloque 2 primero en Python (zonas_canal): lo usa el bloque 1
        #     (sus resultados, de canales)
        por_zona = self.zonas_canal(k)
        esperado, obtenido, dev, recortado = (
            por_zona[clave] for clave in (KXL.Z_ESPERADO, KXL.Z_OBTENIDO,
                                          KXL.Z_DEV, KXL.Z_RECORTADO))
        resultados = self.canales(k)
        snr = [[None if (q is None) else ((1 / q[j]) if (q[j] > 0)
                                          else t[KXL.V_SATURADO])
                for q in disp] for j in range(KXL.CANALES)]

        # --- Bloque 1: por canal (sección, nota y cabecera, como el 2)
        fila = fila_b1 - 3
        hoja.write(fila, col, t[KXL.T_POR_CANAL], self.apartado())
        self.nota(hoja, fila + 1, col, t[KXL.T_NOTA_POR_CANAL],
                  KXL.ANCHOS_CALCULO)
        self.cabecera(hoja, fila_b1 - 1, col, tuple(t[c] for c in (
            KXL.T_CAB_CANAL, KXL.T_CAB_ZV_MEDIA, KXL.T_CAB_MAX,
            KXL.T_CAB_TECHO, KXL.T_CAB_SUELO, KXL.T_CAB_RANGO,
            KXL.T_CAB_LINEAL, KXL.T_CAB_RECORTADO, KXL.T_CAB_SUELO_SNR,
            KXL.T_CAB_SUELO_EXCELENTE, KXL.T_CAB_LATITUD)))
        hoja.set_row(fila_b1 - 1, KXL.ALTO_CABECERA_ALTA)
        c_desv = col + 6
        c_rec = col + 9
        # --- Columnas del bloque 1 (KXL.COL_B1_*, las mismas que lee
        #     Análisis)
        c_b1_techo = col + KXL.COL_B1_TECHO
        c_b1_suelo = col + KXL.COL_B1_SUELO
        c_b1_rango = col + KXL.COL_B1_RANGO
        c_b1_lineal = col + KXL.COL_B1_LINEAL
        c_b1_recortado = col + KXL.COL_B1_RECORTADO
        c_b1_sugerido = col + KXL.COL_B1_SUELO_SUGERIDO
        c_b1_excelente = col + KXL.COL_B1_SUELO_EXCELENTE
        c_b1_latitud = col + KXL.COL_B1_LATITUD
        for j in range(KXL.CANALES):
            r = fila_b1 + j
            banda = (j % 2) == 0
            uno = self.celda(KXL.COLOR_FORMULA, banda, "center",
                             KXL.NUM_UNO)
            dos = self.celda(KXL.COLOR_FORMULA, banda, "center",
                             KXL.NUM_DOS)
            hoja.write(r, col, t[KXL.T_CANALES[j]],
                       self.celda(KXL.COLOR_LITERAL, banda, "center"))
            media = self.ref(KXL.T_HOJA_DATOS, f[KXL.F_MEDIA],
                             cols_datos[j])
            canal = resultados[j]
            self.formula(hoja, r, col + 1, f"={media}", uno,
                         canal[KRES.R_MEDIA_ZV])
            columna = self.ref(KXL.T_HOJA_DATOS, f[KXL.F_ZONAS],
                               cols_datos[j], True, False)
            hasta = celda(f[KXL.F_ZONAS] + n - 1, cols_datos[j], True)
            self.formula(hoja, r, col + 2, f"=MAX({columna}:{hasta})", uno,
                         canal[KRES.R_MAX])
            dz, ez = celda(r, col + 1), celda(r, col + 2)
            self.formula(
                hoja,
                r, c_b1_techo, f'=IF(AND(N({dz})>0,N({ez})>0),{KXL.C_ZONA_ZV}'
                f'+LOG({ez}/{dz},{KXL.C_FACTOR_ZONA}),"")', dos,
                canal[KRES.R_TECHO])
            # --- Suelo: donde la señal/ruido (normalizada) llega a
            #     C_RATIO_SR, según la curva de transferencia
            self.formula(hoja, r, c_b1_suelo,
                         self.suelo_snr(KXL.C_RATIO_SR, j, dz), dos,
                         canal[KRES.R_SUELO])
            fz, gz = celda(r, c_b1_techo), celda(r, c_b1_suelo)
            self.formula(
                hoja, r, c_b1_rango,
                f'=IF(AND(ISNUMBER({fz}),ISNUMBER({gz})),'
                f'{fz}-{gz},"")', dos, canal[KRES.R_RANGO])

            # --- Último punto lineal y primer recortado: fórmulas
            #     matriciales (sin literales ni trucos)
            dv, rc = rango(c_desv + j), rango(c_rec + j)
            es = rango(col + 2)
            cond = (f"IF(ISNUMBER({dv}),IF(ABS({dv})<="
                    f"{KXL.C_TOLERANCIA_LINEAL},IF({rc}="
                    f"{KXL.C_TEXTO_NO_RECORTADO},1,0),0),0)")
            self.formula_matriz(
                hoja, r, c_b1_lineal, r, c_b1_lineal,
                f"{{=IF(SUM({cond})=0,{KXL.C_TEXTO_NINGUNO},"
                f"MAX(IF({cond}=1,{es})))}}", dos,
                canal[KRES.R_FIN_LINEAL])
            self.formula(
                hoja, r, c_b1_recortado,
                f"=IF(COUNTIF({rc},{KXL.C_TEXTO_RECORTADO})=0,"
                f"{KXL.C_TEXTO_NO_ALCANZADO},INDEX({es},MATCH("
                f"{KXL.C_TEXTO_RECORTADO},{rc},0)))", dos,
                canal[KRES.R_PRIMER_RECORTADO])
            # --- Suelos sugeridos, aceptable (C_SNR_MINIMA) y excelente
            #     (C_SNR_EXCELENTE), como el suelo; y la latitud, con el
            #     aceptable
            for c_dest, umbral, clave in (
                    (c_b1_sugerido, KXL.C_SNR_MINIMA, KRES.R_SUELO_SUGERIDO),
                    (c_b1_excelente, KXL.C_SNR_EXCELENTE,
                     KRES.R_SUELO_EXCELENTE)):
                self.formula(hoja, r, c_dest,
                             self.suelo_snr(umbral, j, dz), dos,
                             canal[clave])
            iz, kz = celda(r, c_b1_lineal), celda(r, c_b1_sugerido)
            self.formula(
                hoja, r, c_b1_latitud,
                f"=IF(AND(ISNUMBER({iz}),ISNUMBER({kz})),"
                f"{iz}-{kz}+{KXL.C_ANCHO_ZONA},"
                f"{KXL.C_TEXTO_NO_ALCANZADO})", dos,
                canal[KRES.R_LATITUD])
        # --- Debajo, de qué suelo sale la latitud y por qué es asimétrica
        self.nota(hoja, fila_b1 + KXL.CANALES, col, t[KXL.T_NOTA_LATITUD],
                  KXL.ANCHOS_CALCULO)
        techo_verde = celda(fila_b1 + 1, c_b1_techo, True, True)
        suelo_verde = celda(fila_b1 + 1, c_b1_suelo, True, True)

        # --- Bloque 2: por tercio de zona
        fila = fila_b2 - 3
        hoja.write(fila, col, t[KXL.T_POR_TERCIO], self.apartado())
        self.nota(hoja, fila + 1, col, t[KXL.T_NOTA_POR_TERCIO],
                  KXL.ANCHOS_CALCULO)
        self.cabecera(hoja, fila_b2 - 1, col, tuple(t[c] for c in (
            KXL.T_CAB_ZONA, KXL.T_CAB_TERCIOS, KXL.T_CAB_ESPERADO,
            KXL.T_CAB_OBTENIDO_ROJO, KXL.T_CAB_OBTENIDO_VERDE,
            KXL.T_CAB_OBTENIDO_AZUL, KXL.T_CAB_DESV_ROJO,
            KXL.T_CAB_DESV_VERDE, KXL.T_CAB_DESV_AZUL, KXL.T_CAB_REC_ROJO,
            KXL.T_CAB_REC_VERDE, KXL.T_CAB_REC_AZUL, KXL.T_CAB_SNR_ROJO,
            KXL.T_CAB_SNR_VERDE, KXL.T_CAB_SNR_AZUL, KXL.T_CAB_FALTA_VERDE,
            KXL.T_CAB_TECHO_VERDE, KXL.T_CAB_SUELO_VERDE,
            KXL.T_CAB_SNR_SUGERIDA, KXL.T_CAB_SNR8_ROJO, KXL.T_CAB_SNR8_VERDE,
            KXL.T_CAB_SNR8_AZUL, KXL.T_CAB_SNR_MODELO,
            KXL.T_CAB_SNR_EXCELENTE, KXL.T_CAB_SNR_ING)))
        hoja.set_row(fila_b2 - 1, KXL.ALTO_CABECERA)
        techo_v = self.valor(hoja, fila_b1 + 1, c_b1_techo)
        suelo_v = self.valor(hoja, fila_b1 + 1, c_b1_suelo)

        # --- Para la señal/ruido normalizada y el modelo (verde): los
        #     megapíxeles del sensor, la curva del verde, su Z-V media y
        #     su máximo (por encima, el modelo no vale: recorte)
        mpx = self.ref(KXL.T_HOJA_DATOS, f[KXL.F_MPX],
                       KXL.COLUMNA_INICIO + KXL.COL_VALORES, True, True)
        normalizar = f"SQRT({mpx}/{KXL.C_MPX_REFERENCIA})"
        escala = escala_mpx(d.alto, d.ancho, k[KXL.C_MPX_REFERENCIA])
        curvas = d.transferenciaRGB
        c_verde = KXL.COLUMNA_INICIO + KXL.COL_VALORES + 1
        lectura_v, ganancia_v, proporcional_v = (
            self.ref(KXL.T_HOJA_DATOS, f[clave], c_verde, True, True)
            for clave in (KXL.F_LECTURA, KXL.F_GANANCIA, KXL.F_PROPORCIONAL))
        media_v = self.ref(KXL.T_HOJA_DATOS, f[KXL.F_MEDIA], c_verde, True,
                           True)
        tope_v = celda(fila_b1 + 1, col + 2, True, True)
        for i in range(n):
            r, dz = fila_b2 + i, f[KXL.F_ZONAS] + i
            banda = (i % 2) == 0

            fmt = partial(self.fmt_formula, banda)

            self.formula(hoja, r, col, "=" + self.ref(KXL.T_HOJA_DATOS, dz,
                                                      col), fmt(),
                         self.nombre_zona(i - KS.TERCIOS_LADO))
            self.formula(hoja, r, col + 1, "=" + self.ref(
                KXL.T_HOJA_DATOS, dz, col + 1), fmt(KXL.NUM_ENTERO),
                i - KS.TERCIOS_LADO)
            self.formula(
                hoja, r, col + 2, f"={KXL.C_ZONA_ZV}+{celda(r, col + 1)}/"
                f"{KXL.C_TERCIO_POR_ZONA}", fmt(KXL.NUM_DOS),
                esperado[i])
            for j in range(KXL.CANALES):
                valor = self.ref(KXL.T_HOJA_DATOS, dz, cols_datos[j])
                media = self.ref(KXL.T_HOJA_DATOS, f[KXL.F_MEDIA],
                                 cols_datos[j], True, False)
                oz = celda(r, col + 3 + j)
                self.formula(
                    hoja,
                    r, col + 3 + j, f'=IF(N({valor})>0,{KXL.C_ZONA_ZV}+LOG('
                    f'{valor}/{media},{KXL.C_FACTOR_ZONA}),'
                    f'"")', fmt(KXL.NUM_DOS),
                    self.en_blanco(obtenido[j][i]))
                self.formula(
                    hoja, r, col + 6 + j, f'=IF(ISNUMBER({oz}),{oz}-'
                    f'{celda(r, col + 2, False, True)},"")',
                    fmt(KXL.NUM_SIGNO_TRES), self.en_blanco(dev[j][i]))
                tope = celda(fila_b1 + j, col + 2, True, True)
                self.formula(
                    hoja, r, col + 9 + j, f'=IF(ISNUMBER({valor}),IF({valor}>='
                    f'{KXL.C_UMBRAL_RECORTE}*{tope},'
                    f'{KXL.C_TEXTO_RECORTADO},'
                    f'{KXL.C_TEXTO_NO_RECORTADO}),"")',
                    fmt(), self.en_blanco(recortado[j][i]))
                ref_disp = self.ref(KXL.T_HOJA_DATOS, dz,
                                    cols_datos[KXL.CANALES + j])
                self.formula(
                    hoja, r, col + 12 + j, f'=IF(ISNUMBER({ref_disp}),IF('
                    f'{ref_disp}>0,1/{ref_disp},'
                    f'{KXL.C_TEXTO_SATURADO}),"")',
                    fmt(KXL.NUM_UNO), self.en_blanco(snr[j][i]))
            verde = celda(r, col + 4)
            self.formula(
                hoja, r, col + 15, f'=IF(ISNUMBER({verde}),MAX(0,'
                f'{celda(r, col + 2, False, True)}-{verde}),"")',
                fmt(KXL.NUM_TRES), self.en_blanco(
                    None if (obtenido[1][i] is None)
                    else max(0.0, esperado[i] - obtenido[1][i])))
            self.formula(hoja, r, col + 16, f"={techo_verde}",
                         fmt(KXL.NUM_DOS), techo_v)
            self.formula(hoja, r, col + 17, f"={suelo_verde}",
                         fmt(KXL.NUM_DOS), suelo_v)
            self.formula(hoja, r, col + 18, f"={KXL.C_SNR_MINIMA}",
                         fmt(KXL.NUM_ENTERO), k[KXL.C_SNR_MINIMA])

            # --- Señal/ruido normalizada a C_MPX_REFERENCIA (NA() sin dato:
            #     la gráfica no lo dibuja)
            for j in range(KXL.CANALES):
                pixel = celda(r, col + 12 + j)
                snr_ji = snr[j][i]
                self.formula(
                    hoja, r, col + 19 + j, f"=IF(ISNUMBER({pixel}),{pixel}*"
                    f"{normalizar},{KXL.FORMULA_NA})",
                    fmt(KXL.NUM_UNO), (snr_ji * escala)
                    if isinstance(snr_ji, float) else KXL.RESULTADO_NA)

            # --- Modelo (verde): la señal/ruido de la curva en la señal
            #     esperada de la zona, normalizada; hasta el máximo
            signal = (f"({media_v}*{KXL.C_FACTOR_ZONA}^({celda(r, col + 1)}"
                      f"/{KXL.C_TERCIO_POR_ZONA}))")
            signal_v = medias[1] * (k[KXL.C_FACTOR_ZONA] ** (
                ((i - KS.TERCIOS_LADO) / k[KXL.C_TERCIO_POR_ZONA])))
            self.formula(
                hoja,
                r, col + 22, f"=IF(AND(N({ganancia_v})>0,N({media_v})>0),"
                f"IF({signal}<={tope_v},{signal}/SQRT(N("
                f"{lectura_v})^2+{signal}/{ganancia_v}+(N("
                f"{proporcional_v})*{signal})^2)*{normalizar},"
                f"{KXL.FORMULA_NA}),{KXL.FORMULA_NA})",
                fmt(KXL.NUM_UNO), (snr_modelo(curvas[1], signal_v) * escala)
                if (curvas and (medias[1] > 0) and (signal_v <= topes[1]))
                else KXL.RESULTADO_NA)

            # --- Umbrales excelente y de ingeniería (el aceptable, arriba)
            for desp, umbral in ((23, KXL.C_SNR_EXCELENTE),
                                 (24, KXL.C_RATIO_SR)):
                self.formula(hoja, r, col + desp, f"={umbral}",
                             fmt(KXL.NUM_ENTERO), k[umbral])

        # --- Bloque 3: curva tonal (esperado, sensor y revelador)
        self.bloque_curva(hoja, fila_b3, col, k)

        # --- Bloque 4: latitud de texturas (verde)
        ultima = self.bloque_texturas(hoja, fila_b3 + n + 4, col, k)

        # --- Gráficas de auditoría (el sensor): su título y su sitio; las
        #     pone hoja_graf
        fila_auditoria = ultima + 3
        hoja.write(fila_auditoria, col, t[KXL.T_AUDITORIA], self.apartado())
        f[KXL.F_AUDITORIA] = fila_auditoria + 2
        ultima = f[KXL.F_AUDITORIA] + KXL.FILAS_HUECO
        self.marco(hoja, ((ultima, KXL.ANCHOS_CALCULO),))

    #
    def bloque_texturas(self, hoja: Worksheet, fila_b4: int, col: int,
                        k: dict) -> int:
        """
        Bloque 4 de Cálculo: latitud de texturas. Arriba, los límites
        (apreciable y recomendada: sombras, luces y latitud; los lee
        Análisis); debajo, una fila por zona con la textura del paño (de
        Datos), su relación con el ruido de la tarjeta, la conservada
        frente a la ZV, el paño recortado, si cumple cada criterio, y el
        contraste de la trama del paño en las exportaciones (de Datos) con
        su fracción del de la ZV, que decide las sombras (ver texturas y
        limites_texturas). Devuelve su última fila.
        """
        t, f = self.__textos, self.__filas
        n = (2 * KS.TERCIOS_LADO) + 1
        zv = KS.TERCIOS_LADO
        celda = xl_rowcol_to_cell
        por_zona = self.texturas(k)
        limites = self.limites_texturas(k, por_zona)
        verde = KXL.COLUMNA_INICIO + KXL.COL_VALORES + 1
        fila_t = fila_b4 + 5

        # --- Sección, nota y cabecera de los límites
        hoja.write(fila_b4 - 3, col, t[KXL.T_POR_TEXTURA], self.apartado())
        self.nota(hoja, fila_b4 - 2, col, t[KXL.T_NOTA_TEXTURAS],
                  KXL.ANCHOS_CALCULO)
        self.cabecera(hoja, fila_b4 - 1, col, (
            "", t[KXL.T_CAB_SOMBRAS], t[KXL.T_CAB_LUCES],
            t[KXL.T_CAB_LATITUD_TEXTURAS]))
        f[KXL.F_LIMITES] = fila_b4

        # --- Rangos de la tabla por zona: el lado de las sombras (de Z0 a
        #     la ZV) y el de las luces (de la ZV a ZX)
        columnas = {clave: col + desp for clave, desp in (
            (KXL.T_CAB_ESPERADO, KXL.TEXTURA_ESPERADO),
            (KXL.T_CAB_TEXTURA_RUIDO, KXL.TEXTURA_RUIDO),
            (KXL.T_CAB_CONSERVADA, KXL.TEXTURA_CONSERVADA),
            (KXL.T_CAB_TELA_RECORTADO, KXL.TEXTURA_RECORTADO),
            (KXL.T_CAB_CUMPLE_SOMBRAS, KXL.TEXTURA_SOMBRAS),
            (KXL.T_CAB_CUMPLE_LUCES, KXL.TEXTURA_LUCES),
            (KXL.T_CAB_SIN_RECORTE, KXL.TEXTURA_SIN_RECORTE),
            (KXL.T_CAB_CONTRASTE_ZV, KXL.TEXTURA_FRACCION))}
        bajo = {clave: f"{celda(fila_t, c, True, True)}:"
                f"{celda(fila_t + zv, c, True, True)}"
                for clave, c in columnas.items()}
        alto = {clave: f"{celda(fila_t + zv, c, True, True)}:"
                f"{celda(fila_t + n - 1, c, True, True)}"
                for clave, c in columnas.items()}

        # --- Límites: apreciable y recomendada
        no = KXL.C_TEXTO_NO_ALCANZADO
        sin_revelado = KXL.C_TEXTO_SIN_REVELADO
        tercio = KXL.C_TERCIO_POR_ZONA
        cumple, es, fr = (bajo[KXL.T_CAB_CUMPLE_SOMBRAS],
                          bajo[KXL.T_CAB_ESPERADO],
                          bajo[KXL.T_CAB_CONTRASTE_ZV])
        # --- Solo cuentan los tercios con dato: el criterio por
        #     ISNUMBER de su valor (matriciales)
        ok = f"{cumple}*ISNUMBER({fr})"
        # --- Sombras recomendadas (Tony, 2026-11-13): la primera zona que
        #     cumple (la fracción del contraste de la ZV, en la tabla por
        #     zona); sin ningún contraste (antes de la segunda fase), sin
        #     revelado; sin paño, no alcanzado. Las apreciables, en su
        #     fila, C_MARGEN_SOMBRAS tercios más abajo
        if isinstance(self.__datos.tela, str):
            sombra_rec = f"={no}"
        else:
            sombra_rec = (f"{{=IF(COUNT({fr})=0,{sin_revelado},IF(SUM("
                          f"{ok})=0,{no},INDEX({es},MATCH(1,{ok},0))))}}")
        c_sombra_rec = celda(fila_b4 + list(limites).index(KXL.T_RECOMENDADA),
                             col + KXL.LIMITE_SOMBRAS)
        luces = (f"{alto[KXL.T_CAB_CUMPLE_LUCES]}*ISNUMBER("
                 f"{alto[KXL.T_CAB_CONSERVADA]})")
        cortes = (f"{alto[KXL.T_CAB_SIN_RECORTE]}*ISNUMBER("
                  f"{alto[KXL.T_CAB_TELA_RECORTADO]})")
        es_alto = alto[KXL.T_CAB_ESPERADO]
        for i, (clave, valores) in enumerate(limites.items()):
            r = fila_b4 + i
            banda = (i % 2) == 0
            dos = self.celda(KXL.COLOR_FORMULA, banda, "center", KXL.NUM_DOS)
            hoja.write(r, col, t[clave],
                       self.celda(KXL.COLOR_LITERAL, banda, "center"))
            c_luz = celda(fila_b4, col + KXL.LIMITE_LUCES)
            if clave == KXL.T_APRECIABLE:
                formulas = (f"=IF(ISNUMBER({c_sombra_rec}),{c_sombra_rec}-"
                            f"{KXL.C_MARGEN_SOMBRAS}/{tercio},"
                            f"{c_sombra_rec})",
                            f"{{=IF(SUM({luces})=0,{no},"
                            f"MAX(IF({luces}=1,{es_alto})))}}")
            else:
                tope = f"MAX(IF({cortes}=1,{es_alto}))"
                formulas = (sombra_rec,
                            f"{{=IF(SUM({cortes})=0,{no},IF(ISNUMBER("
                            f"{c_luz}),MIN({c_luz},{tope}),{tope}))}}")
            for j, formula in enumerate(formulas):
                c = col + KXL.LIMITE_SOMBRAS + j
                if formula.startswith("{"):
                    self.formula_matriz(hoja, r, c, r, c, formula, dos,
                                        valores[j])
                else:
                    self.formula(hoja, r, c, formula, dos, valores[j])
            luz_r, sombra_r = (celda(r, col + KXL.LIMITE_LUCES),
                               celda(r, col + KXL.LIMITE_SOMBRAS))
            self.formula(
                hoja, r, col + KXL.LIMITE_LATITUD,
                f"=IF({sombra_r}={sin_revelado},{sin_revelado},"
                f"IF(AND(ISNUMBER({luz_r}),ISNUMBER({sombra_r})),"
                f"{luz_r}-{sombra_r}+{KXL.C_ANCHO_ZONA},{no}))", dos,
                valores[2])

        # --- Tabla por zona
        self.cabecera(hoja, fila_t - 1, col, tuple(t[c] for c in (
            KXL.T_CAB_ZONA, KXL.T_CAB_TERCIOS, KXL.T_CAB_ESPERADO,
            KXL.T_CAB_TEXTURA, KXL.T_CAB_TEXTURA_RUIDO, KXL.T_CAB_CONSERVADA,
            KXL.T_CAB_TELA_RECORTADO, KXL.T_CAB_CUMPLE_SOMBRAS,
            KXL.T_CAB_CUMPLE_LUCES, KXL.T_CAB_SIN_RECORTE,
            KXL.T_CAB_CONTRASTE, KXL.T_CAB_CONTRASTE_ZV)))
        hoja.set_row(fila_t - 1, KXL.ALTO_CABECERA_ALTA)
        textura_zv = celda(fila_t + zv, col + KXL.TEXTURA_TEXTURA, True, True)
        contraste_zv = celda(fila_t + zv, col + KXL.TEXTURA_CONTRASTE, True,
                             True)
        for i in range(n):
            r, dz, pz = fila_t + i, f[KXL.F_ZONAS] + i, f[KXL.F_TELA] + i
            banda = (i % 2) == 0
            self.formula(hoja, r, col, "=" + self.ref(KXL.T_HOJA_DATOS, dz,
                                                      col),
                         self.celda(KXL.COLOR_FORMULA, banda, "center"),
                         self.nombre_zona(i - zv))
            self.formula(hoja, r, col + 1, "=" + self.ref(
                KXL.T_HOJA_DATOS, dz, col + 1), self.celda(
                KXL.COLOR_FORMULA, banda, "center", KXL.NUM_ENTERO), i - zv)
            self.formula(
                hoja, r, col + KXL.TEXTURA_ESPERADO,
                f"={KXL.C_ZONA_ZV}+{celda(r, col + 1)}/{tercio}",
                self.celda(KXL.COLOR_FORMULA, banda, "center", KXL.NUM_DOS),
                por_zona[KXL.T_CAB_ESPERADO][i])
            # --- La textura, con las dispersiones del verde por píxel
            #     (tabla del paño de Datos; ver disp_textura)
            tela = self.ref(KXL.T_HOJA_DATOS, pz,
                            KXL.COLUMNA_INICIO + KXL.COL_TELA_PIXEL)
            tarjeta = self.ref(KXL.T_HOJA_DATOS, pz,
                               KXL.COLUMNA_INICIO + KXL.COL_TARJETA_PIXEL)
            recorte = self.ref(KXL.T_HOJA_DATOS, pz, verde + KXL.CANALES)
            # --- El contraste de la trama del paño (tabla del revelador de
            #     Datos) y su fracción del de la ZV (Tony, 2026-11-13)
            contraste = self.ref(KXL.T_HOJA_DATOS, f[KXL.F_REVELADOR] + i,
                                 KXL.COLUMNA_INICIO + KXL.COL_CONTRASTE)
            tx = celda(r, col + KXL.TEXTURA_TEXTURA)
            cv = celda(r, col + KXL.TEXTURA_CONSERVADA)
            rp = celda(r, col + KXL.TEXTURA_RECORTADO)
            ct = celda(r, col + KXL.TEXTURA_CONTRASTE)
            fc = celda(r, col + KXL.TEXTURA_FRACCION)
            cols_num = (
                (KXL.TEXTURA_TEXTURA, KXL.T_CAB_TEXTURA, KXL.NUM_CUATRO,
                 f'=IF(AND(ISNUMBER({tela}),ISNUMBER({tarjeta})),SQRT(MAX(0,'
                 f'{tela}^2-{tarjeta}^2)),"")'),
                (KXL.TEXTURA_RUIDO, KXL.T_CAB_TEXTURA_RUIDO, KXL.NUM_DOS,
                 f'=IF(AND(ISNUMBER({tx}),N({tarjeta})>0),{tx}/{tarjeta},"")'),
                (KXL.TEXTURA_CONSERVADA, KXL.T_CAB_CONSERVADA,
                 KXL.NUM_PORCENTAJE,
                 f'=IF(AND(ISNUMBER({tx}),N({textura_zv})>0),'
                 f'{tx}/{textura_zv},"")'),
                (KXL.TEXTURA_RECORTADO, KXL.T_CAB_TELA_RECORTADO,
                 KXL.NUM_PORCENTAJE, f'=IF(ISNUMBER({recorte}),{recorte},"")'),
                (KXL.TEXTURA_CONTRASTE, KXL.T_CAB_CONTRASTE, KXL.NUM_UNO,
                 f'=IF(ISNUMBER({contraste}),{contraste},"")'),
                (KXL.TEXTURA_FRACCION, KXL.T_CAB_CONTRASTE_ZV,
                 KXL.NUM_PORCENTAJE,
                 f'=IF(AND(ISNUMBER({ct}),N({contraste_zv})>0),'
                 f'{ct}/{contraste_zv},"")'))
            for desp, clave, numero, formula in cols_num:
                self.formula(
                    hoja, r, col + desp, formula,
                    self.celda(KXL.COLOR_FORMULA, banda, "center", numero),
                    self.en_blanco(por_zona[clave][i]))

            # --- Criterios: sombras, de la ZV hacia abajo (lee la fila de
            #     debajo); luces, de la ZV hacia arriba (lee la de encima)
            criterios = []
            #     Sin dato, pasa lo que viene del lado de la ZV
            if i <= zv:
                sigue = ("TRUE" if (i == zv) else
                         celda(r + 1, col + KXL.TEXTURA_SOMBRAS))
                criterios.append((KXL.TEXTURA_SOMBRAS,
                                  KXL.T_CAB_CUMPLE_SOMBRAS,
                                  f"=IF(ISNUMBER({fc}),AND({fc}>="
                                  f"{KXL.C_CONTRASTE_SOMBRAS},{sigue}),"
                                  f"{sigue})"))
            if i >= zv:
                for desp, clave, dato, cond in (
                        (KXL.TEXTURA_LUCES, KXL.T_CAB_CUMPLE_LUCES, cv,
                         f"{cv}>={KXL.C_TEXTURA_CONSERVADA},N({rp})<="
                         f"{KXL.C_TELA_RECORTADO_APRECIABLE}"),
                        (KXL.TEXTURA_SIN_RECORTE, KXL.T_CAB_SIN_RECORTE, rp,
                         f"{rp}<={KXL.C_TELA_RECORTADO_MAX}")):
                    antes = ("TRUE" if (i == zv) else
                             celda(r - 1, col + desp))
                    criterios.append((desp, clave,
                                      f"=IF(ISNUMBER({dato}),AND("
                                      f"{cond},{antes}),{antes})"))
            formato = self.celda(KXL.COLOR_FORMULA, banda, "center")
            for desp in (KXL.TEXTURA_SOMBRAS, KXL.TEXTURA_LUCES,
                         KXL.TEXTURA_SIN_RECORTE):
                hoja.write_blank(r, col + desp, None, formato)
            for desp, clave, formula in criterios:
                self.formula(hoja, r, col + desp, formula, formato,
                             bool(por_zona[clave][i]))
        return fila_t + n - 1

    #
    def bloque_curva(self, hoja: Worksheet, fila_b3: int, col: int,
                     k: dict) -> None:
        """
        Bloque 3 de Cálculo, la curva tonal en L*: por zona, la luz y el
        L* esperados, el objetivo, el sensor (de los datos de la serie)
        y el revelador (de su tabla en Datos), sus diferencias (el sensor,
        con el esperado; el revelador, con el objetivo), falta y sobra
        del revelador hasta el objetivo (para las barras de la gráfica),
        entrada (el revelador) y salida (el objetivo) de la curva de
        Lightroom y si es punto de la curva.
        Los resultados, de puntos_curva.
        """
        t, f = self.__textos, self.__filas
        n = (2 * KS.TERCIOS_LADO) + 1
        celda = xl_rowcol_to_cell
        c_verde = KXL.COLUMNA_INICIO + KXL.COL_VALORES + 1
        c_rev = KXL.COLUMNA_INICIO + KXL.COL_REVELADOR
        puntos = self.puntos_curva(k)
        hoja.write(fila_b3 - 3, col, t[KXL.T_CURVA], self.apartado())
        self.cabecera(hoja, fila_b3 - 1, col, tuple(t[c] for c in (
            KXL.T_CAB_ZONA, KXL.T_CAB_TERCIOS, KXL.T_CAB_LUZ_ESPERADA,
            KXL.T_CAB_L_ESPERADO, KXL.T_CAB_L_OBJETIVO, KXL.T_CAB_LUZ_SENSOR,
            KXL.T_CAB_L_SENSOR, KXL.T_CAB_DIF_SENSOR, KXL.T_CAB_L_REVELADOR,
            KXL.T_CAB_LUZ_REVELADOR, KXL.T_CAB_DIF_REVELADOR, KXL.T_CAB_FALTA,
            KXL.T_CAB_SOBRA, KXL.T_CAB_ENTRADA, KXL.T_CAB_SALIDA,
            KXL.T_CAB_PUNTO)))
        hoja.set_row(fila_b3 - 1, KXL.ALTO_CABECERA_ALTA)
        salida_zv = None
        for i in range(n):
            r, dz = fila_b3 + i, f[KXL.F_ZONAS] + i
            tercio_ev = i - KS.TERCIOS_LADO
            banda = (i % 2) == 0
            p = puntos[i]

            fmt = partial(self.fmt_formula, banda)

            c = partial(Excel.celda_desp, r, col)

            self.formula(hoja, r, col, "=" + self.ref(KXL.T_HOJA_DATOS, dz,
                                                      col), fmt(),
                         self.nombre_zona(tercio_ev))
            self.formula(hoja, r, col + 1, "=" + self.ref(
                KXL.T_HOJA_DATOS, dz, col + 1), fmt(KXL.NUM_ENTERO),
                tercio_ev)

            # --- Esperado: un paso de luz por zona desde la ZV, hasta el
            #     blanco de pantalla; objetivo: 10 L* por zona
            self.formula(
                hoja,
                r, col + 2, f"=MIN(1,{KXL.C_LUZ_ZV}*{KXL.C_FACTOR_ZONA}^("
                f"{c(1)}/{KXL.C_TERCIO_POR_ZONA}))",
                fmt(KXL.NUM_CUATRO), p.luz_esperada)
            self.formula(hoja, r, col + 3, f"={self.formula_lab(c(2))}",
                         fmt(KXL.NUM_UNO), p.esperado)
            self.formula(
                hoja,
                r, col + 4, f"={KXL.C_L_POR_ZONA}*({KXL.C_ZONA_ZV}+{c(1)}/"
                f"{KXL.C_TERCIO_POR_ZONA})", fmt(KXL.NUM_UNO),
                p.objetivo)

            # --- Sensor: el verde de la zona entre el de la ZV (media)
            verde = self.ref(KXL.T_HOJA_DATOS, dz, c_verde)
            media = self.ref(KXL.T_HOJA_DATOS, f[KXL.F_MEDIA], c_verde,
                             True, True)
            self.formula(
                hoja,
                r, col + 5, f'=IF(N({verde})>0,MIN(1,{KXL.C_LUZ_ZV}*{verde}'
                f'/{media}),"")', fmt(KXL.NUM_CUATRO),
                self.en_blanco(p.luz_sensor))
            self.formula(
                hoja,
                r, col + 6, f'=IF(ISNUMBER({c(5)}),{self.formula_lab(c(5))},'
                f'"")', fmt(KXL.NUM_UNO), self.en_blanco(p.sensor))
            self.formula(
                hoja, r, col + KXL.CURVA_DIF_SENSOR,
                f'=IF(ISNUMBER({c(6)}),{c(6)}-{c(3)},"")',
                fmt(KXL.NUM_SIGNO_UNO),
                self.en_blanco(None if (p.sensor is None)
                               else (p.sensor - p.esperado)))

            # --- Revelador: de su tabla en Datos (leído o estimado). Sin
            #     dato, NA() en lo que dibujan la curva tonal y la
            #     diferencia en L*
            revelador = self.ref(KXL.T_HOJA_DATOS, f[KXL.F_REVELADOR] + i,
                                 c_rev)
            l_obj, l_rev, luz_rev = p.objetivo, p.revelador, p.luz_revelador
            self.formula(
                hoja, r, col + 8, f'=IF(ISNUMBER({revelador}),{revelador},'
                f'{KXL.FORMULA_NA})',
                fmt(KXL.NUM_UNO), KXL.RESULTADO_NA if (l_rev is None)
                else l_rev)
            self.formula(
                hoja, r, col + 9,
                f'=IF(ISNUMBER({c(8)}),{self.formula_luz(c(8))},"")',
                fmt(KXL.NUM_CUATRO), self.en_blanco(luz_rev))
            self.formula(
                hoja, r, col + KXL.CURVA_DIF_REVELADOR,
                f'=IF(ISNUMBER({c(8)}),{c(8)}-{c(4)},{KXL.FORMULA_NA})',
                fmt(KXL.NUM_SIGNO_UNO),
                KXL.RESULTADO_NA if (l_rev is None) else (l_rev - l_obj))
            self.formula(
                hoja,
                r, col + 11, f'=IF(ISNUMBER({c(8)}),MAX(0,{c(4)}-{c(8)}),"")',
                fmt(KXL.NUM_UNO),
                "" if (l_rev is None) else max(0.0, l_obj - l_rev))
            self.formula(
                hoja,
                r, col + 12, f'=IF(ISNUMBER({c(8)}),MAX(0,{c(8)}-{c(4)}),"")',
                fmt(KXL.NUM_UNO),
                "" if (l_rev is None) else max(0.0, l_rev - l_obj))
            self.formula(
                hoja, r, col + KXL.CURVA_ENTRADA,
                f'=IF(ISNUMBER({c(9)}),{self.formula_curva(c(9))},"")',
                fmt(KXL.NUM_ENTERO),
                self.en_blanco(p.entrada))
            salida = p.salida
            self.formula(
                hoja, r, col + KXL.CURVA_SALIDA,
                f'=IF(ISNUMBER({c(8)}),'
                f'{self.formula_curva(self.formula_luz(c(4)))},"")',
                fmt(KXL.NUM_ENTERO), "" if (l_rev is None) else salida)
            if tercio_ev == 0:
                salida_zv = (celda(r, col + 2), salida)
            self.formula(
                hoja, r, col + KXL.CURVA_PUNTO,
                f'=IF(MOD({c(1)},{KXL.C_TERCIO_POR_ZONA})=0,'
                f'{KXL.C_TEXTO_PUNTO},"")', fmt(),
                t[KXL.V_PUNTO] if ((tercio_ev % k[KXL.C_TERCIO_POR_ZONA]) == 0)
                else "")

        # --- Nota, con la lectura que debe dar el parche ZV en Revelar
        #     calculada (si cambia C_LZV, no se desfasa)
        luz_zv, valor_zv = salida_zv                            # type: ignore
        porcentaje = (KXL.CIEN * valor_zv) / k[KXL.C_ESCALA_CURVA]
        cien = KXL.CIEN
        self.nota(
            hoja, fila_b3 - 2, col,
            f"{t[KXL.T_NOTA_CURVA_ANTES]}{porcentaje:.1f}"
            f"{t[KXL.T_NOTA_CURVA_MEDIO]}{valor_zv}"
            f"{t[KXL.T_NOTA_CURVA_TRAS]}", KXL.ANCHOS_CALCULO,
            formula=f"={self.cadena(t[KXL.T_NOTA_CURVA_ANTES])}&FIXED("
            f"{self.formula_curva(luz_zv)}/{KXL.C_ESCALA_CURVA}*"
            f"{cien},1)&{self.cadena(t[KXL.T_NOTA_CURVA_MEDIO])}&"
            f"{self.formula_curva(luz_zv)}&"
            f"{self.cadena(t[KXL.T_NOTA_CURVA_TRAS])}")

    #
    def hoja_resumen(self) -> None:
        """
        Hoja Análisis, con el estilo de Tony, en dos tarjetas sobre una
        rejilla de filas iguales (KXL.ALTO_REJILLA): lo alto ocupa varias
        filas combinadas, así una tarjeta no estira las filas de la otra.
        Izquierda: cabecera (cámara, fecha, bits, exposición de la Z-V y
        serie), latitud de texturas, latitud por canal, ruido de lectura y
        negro, balances de blancos y avisos. Derecha: sugerencia de
        revelado, diferencias medias, las decisiones propias del
        estudiante y las recomendaciones (la tabla
        por zona: L* leído, diferencias del sensor y del revelador,
        entrada, salida y punto de la curva).
        """
        # --- Cada tarjeta, por su cuenta (la rejilla las independiza)
        hoja = self.__hojas[KXL.T_HOJA_RESUMEN]
        fila_balances = self.resumen_izquierda(hoja)
        ultima_derecha = self.resumen_derecha(hoja)
        ultima_balances = self.resumen_balances(hoja, fila_balances)
        ultima_izquierda = self.resumen_avisos(hoja, ultima_balances + 2)
        self.marco(hoja, ((ultima_izquierda, KXL.ANCHOS_RESUMEN),
                          (ultima_derecha, KXL.ANCHOS_RESUMEN_DERECHA)),
                   KXL.ANILLO_RESUMEN, KXL.ANCHO_ANILLO_RESUMEN,
                   KXL.ANCHO_RELLENO_RESUMEN, KXL.ALTO_REJILLA)

    #
    def resumen_izquierda(self, hoja: Worksheet) -> int:
        """
        Tarjeta izquierda de Análisis: título, cámara, fecha, bits y
        exposición de la Z-V, y la serie (tomas, si se puede analizar y si
        hay balance personalizado); latitud de texturas; latitud por
        canal; y ruido de lectura y negro, con sus avisos. Devuelve la
        fila donde puede ir el título de los balances (ver
        resumen_balances); tras ellos, los avisos (ver resumen_avisos).
        """
        t, d, f = self.__textos, self.__datos, self.__filas
        col = KXL.COLUMNA_INICIO
        ultima = col + len(KXL.ANCHOS_RESUMEN) - 1
        n_rotulo = KXL.COLUMNAS_ROTULO_RESUMEN
        rotulo = self.fmt_resumen(bold=True, align="right", valign="top")
        nota = self.nota_resumen(KXL.COLOR_ROTULO)

        # --- Cabecera: título, cámara, fecha, profundidad de bits de los
        #     RAW y exposición de la Z-V
        fila = KXL.FILA_INICIO
        hoja.merge_range(fila, col, fila + KXL.FILAS_TITULO_RESUMEN - 1,
                         ultima, t[KXL.T_TITULO_RESUMEN],
                         self.fondo_resumen(KXL.LETRA_RESUMEN_TITULO,
                                            align="center", valign="vcenter"))
        fila += KXL.FILAS_TITULO_RESUMEN + 1

        # --- A la izquierda, cámara, fecha y bits: el rótulo y, a su
        #     derecha, el dato centrado
        primera = fila
        ultimo_dato = col + KXL.COLUMNAS_DATO_RESUMEN
        centro = self.fmt_resumen(align="center", valign="top")
        hoja.write(fila, col, t[KXL.T_MARCA_MODELO], rotulo)
        hoja.merge_range(fila, col + 1, fila, ultimo_dato, d.cam, centro)
        fila += 1
        hoja.write(fila, col, t[KXL.T_FECHA], rotulo)
        fecha = self.fmt_resumen(align="center", valign="top",
                                 num_format=t[KXL.T_FORMATO_FECHA])
        hoja.merge_range(fila, col + 1, fila, ultimo_dato, "", fecha)
        if d.fecha:
            hoja.write_datetime(fila, col + 1,
                                datetime.fromisoformat(d.fecha), fecha)
        fila += 1
        hoja.write(fila, col, t[KXL.T_BITS], rotulo)
        bits = self.fmt_resumen(align="center", valign="top",
                                num_format=KXL.NUM_BITS)
        hoja.merge_range(fila, col + 1, fila, ultimo_dato, "", bits)
        if d.bits:
            hoja.write_number(fila, col + 1, d.bits, bits)

        # --- A la derecha, en una caja, la exposición de la Z-V, en el
        #     orden de KXL.ROTULOS_EXP: f, Tv e ISO (el de la pantalla y el
        #     PDF)
        caja = ultima - KXL.COLUMNAS_CAJA_ZV + 1
        hoja.merge_range(primera, caja, primera, ultima, t[KXL.T_ZV],
                         self.cabecera_resumen())
        for i, (clave, dato) in enumerate(zip(KXL.ROTULOS_EXP, (
                OECF.TextoF(d.f) if d.f else "",
                OECF.TextoTV(d.tv) if d.tv else "",
                OECF.TextoISO(d.iso) if d.iso else ""), strict=True)):
            hoja.write(primera + 1 + i, caja, t[clave],
                       self.celda_resumen(False, "right", bold=True))
            hoja.write(primera + 1 + i, caja + 1, dato,
                       self.celda_resumen(False, "left"))
        fila = primera + len(KXL.ROTULOS_EXP)

        # --- La serie, bajo la caja: el dato (cuántas tomas tiene, si se
        #     puede analizar y si hay balance personalizado; lo que enseña
        #     FotoEstación) y, a su derecha, su rótulo
        serie = self.__serie
        rotulo_serie = self.fmt_resumen(bold=True, align="left",
                                        valign="top")
        for clave, dato in (
                (KXL.T_TOMAS, serie.tomas),
                (KXL.T_ANALIZABLE, self.si_no(serie.esAnalizable)),
                (KXL.T_BALANCE_PERSONALIZADO,
                 self.si_no(serie.esBalancePersonalizado))):
            fila += 1
            hoja.write(fila, col + 1, dato, centro)
            hoja.merge_range(fila, col + 2, fila, col + 4, t[clave],
                             rotulo_serie)

        # --- Latitud de texturas (de Cálculo, bloque 4): barra, cabecera,
        #     apreciable y recomendada (sombras, luces y latitud, en
        #     tercios) y la nota con los criterios (o que no hay paño)
        fila += 2
        self.barra_resumen(hoja, fila, col, ultima, t[KXL.T_TEXTURAS])
        fila = self.cabecera_tarjeta(
            hoja, fila + 2, col, (("", n_rotulo),
                                  (t[KXL.T_CAB_SOMBRAS], 1),
                                  (t[KXL.T_CAB_LUCES], 1),
                                  (t[KXL.T_CAB_LATITUD_TEXTURAS], 1)),
            KXL.FILAS_CABECERA)
        k = self.valores_constantes()
        limites = self.limites_texturas(k, self.texturas(k))
        for i, (clave, valores) in enumerate(limites.items()):
            fila += 1
            banda = (i % 2) == 0
            hoja.merge_range(fila, col, fila, col + n_rotulo - 1,
                             t[clave], self.celda_resumen(banda, "left"))
            numero = self.celda_resumen(banda, "center", KXL.NUM_TERCIOS)
            for j in range(len(valores)):
                origen = self.ref(KXL.T_HOJA_CALCULO, f[KXL.F_LIMITES] + i,
                                  col + KXL.LIMITE_SOMBRAS + j)
                self.formula(hoja, fila, col + n_rotulo + j,
                             f"={origen}", numero, valores[j])
        if isinstance(d.tela, str):
            nota_texturas = t[KXL.T_SIN_TELA]
        else:
            nota_texturas = t[KXL.T_NOTA_TEXTURAS_RESUMEN].format(
                umbral=round(k[KXL.C_CONTRASTE_SOMBRAS] * KXL.CIEN),
                conservada=round(k[KXL.C_TEXTURA_CONSERVADA] * KXL.CIEN),
                recortado_apreciable=round(
                    k[KXL.C_TELA_RECORTADO_APRECIABLE] * KXL.CIEN),
                recortado=round(k[KXL.C_TELA_RECORTADO_MAX] * KXL.CIEN),
                margen=k[KXL.C_MARGEN_SOMBRAS])
        fila = self.nota_tarjeta(hoja, fila + 1, col, ultima, nota_texturas,
                                 KXL.ANCHOS_RESUMEN, nota)

        # --- Latitud por canal (de Cálculo, bloque 1)
        fila = self.resumen_latitud(hoja, fila + 2)

        # --- Ruido aceptable por color (de Cálculo, bloque 1: el suelo
        #     sugerido): barra, nota con el umbral y una frase por canal.
        #     El ruido de lectura y el negro, solo en Datos
        fila += 2
        self.barra_resumen(hoja, fila, col, ultima,
                           self.titulo_ruido_color())
        fila = self.nota_tarjeta(
            hoja, fila + 1, col, ultima,
            t[KXL.T_RUIDO_COLOR_NOTA].format(umbral=k[KXL.C_SNR_MINIMA]),
            KXL.ANCHOS_RESUMEN, nota)
        for i, frase in enumerate(self.frases_ruido(k)):
            fila += 1
            hoja.merge_range(fila, col, fila, ultima, frase,
                             self.celda_resumen((i % 2) == 0, "left"))

        # --- Píxeles defectuosos (de Datos), debajo del ruido
        lineas = self.lineas_pixeles()
        if lineas:
            fila += 2
            self.barra_resumen(hoja, fila, col, ultima, t[KXL.T_PIXELES])
            for i, linea in enumerate(lineas):
                fila += 1
                hoja.merge_range(fila, col, fila, ultima, linea,
                                 self.celda_resumen((i % 2) == 0, "left"))

        # --- Balances de blancos (de Datos): los escribe resumen_balances,
        #     desde la fila donde irá su título
        return fila + 2

    #
    def resumen_latitud(self, hoja: Worksheet, fila: int) -> int:
        """
        Latitud por canal de la tarjeta izquierda de Análisis (de Cálculo,
        bloque 1): la barra en fila, la cabecera (rojo, verde y azul) y una
        fila por cifra, todo en zonas. Devuelve su última fila.
        """
        t, f = self.__textos, self.__filas
        calculo = self.__hojas[KXL.T_HOJA_CALCULO]
        col = KXL.COLUMNA_INICIO
        ultima = col + len(KXL.ANCHOS_RESUMEN) - 1
        n_rotulo = KXL.COLUMNAS_ROTULO_RESUMEN
        self.barra_resumen(hoja, fila, col, ultima, t[KXL.T_LATITUD_CANAL])
        fila = self.cabecera_tarjeta(
            hoja, fila + 2, col, (("", n_rotulo),)
            + tuple((t[clave], 1) for clave in KXL.T_CANALES),
            KXL.FILAS_CABECERA)
        for i, (clave, desplazamiento) in enumerate(
                KXL.FILAS_LATITUD_CANAL):
            fila += 1
            banda = (i % 2) == 0
            hoja.merge_range(fila, col, fila, col + n_rotulo - 1,
                             t[clave], self.celda_resumen(banda, "left"))
            numero = self.celda_resumen(banda, "center", KXL.NUM_DOS)
            for j in range(KXL.CANALES):
                fila_calculo = f[KXL.F_CANALES] + j
                origen = self.ref(KXL.T_HOJA_CALCULO, fila_calculo,
                                  col + desplazamiento)
                self.formula(
                    hoja, fila, col + n_rotulo + j,
                    f'=IF({origen}="","",{origen})', numero,
                    self.valor(calculo, fila_calculo, col + desplazamiento))
        return fila

    #
    def resumen_balances(self, hoja: Worksheet, fila: int) -> int:
        """
        Balances de blancos de la tarjeta izquierda de Análisis (de
        Datos), desde fila: a la izquierda, el título y, debajo, la nota
        en un recuadro; a la derecha, la tabla (el nombre del balance y sus
        Kelvin anotado y medido), con su cabecera a la altura del título.
        Devuelve su última fila.
        """
        t, d, f = self.__textos, self.__datos, self.__filas
        col = KXL.COLUMNA_INICIO
        ultima = col + len(KXL.ANCHOS_RESUMEN) - 1
        col_tabla = col + KXL.COLUMNAS_NOTA_BALANCES
        col_kelvin = ultima - 1

        # --- Título y cabecera de la tabla, en las mismas filas
        arriba = fila + KXL.FILAS_CABECERA_ALTA - 1
        hoja.merge_range(fila, col, arriba, col_kelvin - 1, t[KXL.T_BALANCES],
                         self.fondo_resumen(align="center",
                                            valign="vcenter"))
        fila = self.cabecera_tarjeta(
            hoja, fila, col_kelvin, ((t[KXL.T_CAB_KELVIN_ANOTADO], 1),
                                     (t[KXL.T_CAB_KELVIN_MEDIDO], 1)),
            KXL.FILAS_CABECERA_ALTA)

        # --- La tabla: un balance por fila
        balances = d.balancesDistintos
        for i, balance in enumerate(balances):
            fila += 1
            banda = (i % 2) == 0
            texto = self.celda_resumen(banda, "left")
            numero = self.celda_resumen(banda, "center", KXL.NUM_ENTERO)
            origen = f[KXL.F_BALANCES] + i
            hoja.merge_range(fila, col_tabla, fila, col_kelvin - 1, "", texto)
            self.formula(
                hoja,
                fila, col_tabla, "=" + self.ref(KXL.T_HOJA_DATOS, origen, col),
                texto, self.nombre_balance(balance.nombre))
            for j, valor_k in enumerate((balance.kelvin_cam,
                                         balance.kelvin)):
                celda_datos = self.ref(KXL.T_HOJA_DATOS, origen,
                                       col + KXL.COL_VALORES + j)
                self.formula(
                    hoja, fila, col_kelvin + j,
                    f'=IF(ISNUMBER({celda_datos}),{celda_datos},"")',
                    numero, self.en_blanco(valor_k))

        # --- La nota, en un recuadro a la izquierda de la tabla: de su
        #     altura, o de la que pidan sus líneas si es mayor
        nota = t[KXL.T_NOTA_BALANCES]
        ancho = sum(KXL.ANCHOS_RESUMEN[:KXL.COLUMNAS_NOTA_BALANCES])
        filas = max(len(balances),
                    self.filas_texto(nota, ancho, KXL.ALTO_LINEA_NOTA))
        fin_nota = arriba + filas
        hoja.merge_range(
            arriba + 1, col, fin_nota, col_tabla - 1, nota,
            self.fmt_resumen(KXL.LETRA_RESUMEN_NOTA,
                             font_color=KXL.COLOR_ROTULO, text_wrap=True,
                             align="center", valign="vcenter",
                             border=KXL.FINO, border_color=KXL.BORDE_TABLA))
        return max(fila, fin_nota)

    #
    def resumen_avisos(self, hoja: Worksheet, fila: int) -> int:
        """
        Avisos de la tarjeta izquierda de Análisis (las incidencias de la
        serie): la barra en fila y una frase por aviso, o que no hay.
        Devuelve su última fila.
        """
        t = self.__textos
        col = KXL.COLUMNA_INICIO
        ultima = col + len(KXL.ANCHOS_RESUMEN) - 1
        nota = self.nota_resumen(KXL.COLOR_ROTULO)
        self.barra_resumen(hoja, fila, col, ultima, t[KXL.T_AVISOS])
        for aviso in (self.__serie.avisos or (t[KXL.T_SIN_AVISOS],)):
            fila = self.nota_tarjeta(hoja, fila + 1, col, ultima, aviso,
                                     KXL.ANCHOS_RESUMEN, nota)
        return fila

    #
    def resumen_derecha(self, hoja: Worksheet) -> int:
        """
        Tarjeta derecha de Análisis: sugerencia de revelado (un solo
        texto), qué es lo estimado, las diferencias medias (sensor y
        revelador), el aviso si no hay L* leído, las decisiones propias
        (los puntos de la curva que elige el estudiante: zona de la lista,
        entrada y salida de 0 a C_ESCALA_CURVA) y las recomendaciones: la
        tabla por zona, con el L* leído (lo escribe el estudiante o el
        programa con las TIFF) y lo demás, de Cálculo. Lo estimado
        (tercios sin L* leído), en su color. Devuelve su última fila.
        """
        t, f = self.__textos, self.__filas
        hoja_calculo = self.__hojas[KXL.T_HOJA_CALCULO]
        col = self.columna_derecha()
        ultima = col + len(KXL.ANCHOS_RESUMEN_DERECHA) - 1
        col_calculo = KXL.COLUMNA_INICIO
        b3 = f[KXL.F_CURVA]
        n = (2 * KS.TERCIOS_LADO) + 1
        celda = xl_rowcol_to_cell
        nota = self.nota_resumen(KXL.COLOR_ROTULO)

        # --- Sugerencia de revelado: barra y su texto, en un bloque
        fila = KXL.FILA_INICIO
        self.barra_resumen(hoja, fila, col, ultima, t[KXL.T_SUGERENCIA])
        fila = self.nota_tarjeta(
            hoja, fila + 1, col, ultima, KXL.SEPARADOR_NOTAS.join(
                t[clave] for clave in (KXL.T_SUGERIDO, KXL.T_REFERENCIA,
                                       KXL.T_ES_SUGERENCIA)),
            KXL.ANCHOS_RESUMEN_DERECHA, nota)

        # --- Qué es lo estimado, en su color
        fila = self.nota_tarjeta(hoja, fila + 1, col, ultima,
                                 t[KXL.T_ESTIMADO],
                                 KXL.ANCHOS_RESUMEN_DERECHA,
                                 self.nota_resumen(KXL.COLOR_ESTIMADO))

        # --- Diferencias medias (sensor, revelador y con tu curva: esta,
        #     de unas columnas de Cálculo que se escriben después, en
        #     blanco hasta que el estudiante pone sus puntos) y, sin
        #     revelador, la nota que lo explica (sus filas, aunque salga
        #     vacía)
        rotulo = self.fmt_resumen(bold=True, align="right", valign="top")
        valor_media = self.fmt_resumen(align="left", valign="top",
                                       num_format=KXL.NUM_LSTAR)
        col_media = col + KXL.COLUMNAS_ROTULO_MEDIA
        medias = []
        for desp, clave in ((KXL.CURVA_DIF_SENSOR, KXL.T_DIF_MEDIA_SENSOR),
                            (KXL.CURVA_DIF_REVELADOR,
                             KXL.T_DIF_MEDIA_REVELADOR),
                            (KXL.TU_DIF, KXL.T_DIF_MEDIA_TU)):
            fila += 1
            primera = self.ref(KXL.T_HOJA_CALCULO, b3, col_calculo + desp,
                               True, True)
            columna = (f"{primera}:"
                       f"{celda(b3 + n - 1, col_calculo + desp, True, True)}")
            cifras = [v for v in (self.valor(hoja_calculo, b3 + i,
                                             col_calculo + desp)
                                  for i in range(n))
                      if isinstance(v, (int, float))]
            hoja.merge_range(fila, col, fila, col_media - 1, t[clave], rotulo)
            hoja.merge_range(fila, col_media, fila, ultima, "", valor_media)
            self.formula_matriz(
                hoja, fila, col_media, fila, col_media,
                f'{{=IF(COUNT({columna})=0,"",SUM(IF(ISNUMBER({columna}),'
                f'ABS({columna}),0))/COUNT({columna}))}}', valor_media,
                (sum(abs(x) for x in cifras) / len(cifras)) if cifras
                else "")
            medias.append(columna)
        aviso = self.cadena(t[KXL.T_SIN_REVELADOR])
        sin_revelador = not any(v is not None for v in self.__revelador)
        fila = self.nota_tarjeta(
            hoja, fila + 2, col, ultima,
            t[KXL.T_SIN_REVELADOR] if sin_revelador else "",
            KXL.ANCHOS_RESUMEN_DERECHA, nota,
            f'=IF(COUNT({medias[1]})=0,{aviso},"")', t[KXL.T_SIN_REVELADOR])

        # --- Decisiones propias: barra, cabecera doble (zona, entrada y
        #     salida, en cada lado) y sus filas, de un lado y luego del
        #     otro: por defecto, las zonas enteras desde la Z0 y la salida
        #     recomendada de cada una, como valores (en azul: el
        #     estudiante los cambia libremente; KXL.SIN_ZONA, el punto no
        #     cuenta). La entrada (fórmula) y las validaciones, al final,
        #     cuando se sabe dónde está la tabla
        fila += 2
        self.barra_resumen(hoja, fila, col, ultima, t[KXL.T_DECISIONES])
        punto = ((t[KXL.T_CAB_ZONA], 1), (t[KXL.T_CAB_ENTRADA], 1),
                 (t[KXL.T_CAB_SALIDA], 1))
        for lado in KXL.LADOS_DECISIONES:
            fin_cabecera = self.cabecera_tarjeta(hoja, fila + 1, col + lado,
                                                 punto, KXL.FILAS_CABECERA)
        primera_propia = fin_cabecera + 1
        self.__filas[KXL.F_DECISIONES] = primera_propia
        fila = fin_cabecera
        k = self.valores_constantes()
        puntos = self.puntos_curva(k)
        por_zona = k[KXL.C_TERCIO_POR_ZONA]
        for i in range(KXL.FILAS_DECISIONES):
            fila += 1
            banda = (i % 2) == 0
            dato = self.celda_resumen(banda, "center",
                                      font_color=KXL.COLOR_DATO)
            numero = self.celda_resumen(banda, "center", KXL.NUM_ENTERO,
                                        font_color=KXL.COLOR_DATO)
            for n_lado, lado in enumerate(KXL.LADOS_DECISIONES):
                zona = (n_lado * KXL.FILAS_DECISIONES) + i
                p = puntos[KS.TERCIOS_LADO
                           + ((zona - k[KXL.C_ZONA_ZV]) * por_zona)]
                hoja.write_string(fila, col + lado, p.nombre, dato)
                hoja.write_blank(fila, col + lado + 1, None, numero)
                hoja.write_number(fila, col + lado + 2, p.salida, numero)
        ultima_propia = fila

        # --- Recomendaciones, justo debajo: barra y la tabla por zona
        #     (zona, L* leído y, de Cálculo, las diferencias, la entrada,
        #     la salida y el punto de la curva)
        fila += 3
        self.barra_resumen(hoja, fila - 1, col, ultima,
                           t[KXL.T_RECOMENDACIONES])
        fila = self.cabecera_tarjeta(
            hoja, fila, col, tuple((t[clave], 1) for clave in (
                KXL.T_CAB_ZONA, KXL.T_CAB_L_APUNTADO, KXL.T_CAB_DIF_SENSOR,
                KXL.T_CAB_DIF_REVELADOR, KXL.T_CAB_ENTRADA, KXL.T_CAB_SALIDA,
                KXL.T_CAB_PUNTO)), KXL.FILAS_CABECERA_ALTA)
        f[KXL.F_APUNTADO] = fila + 1
        col_apuntado = col + KXL.COL_APUNTADO
        cols_num = ((KXL.CURVA_DIF_SENSOR, KXL.NUM_SIGNO_UNO),
                    (KXL.CURVA_DIF_REVELADOR, KXL.NUM_SIGNO_UNO),
                    (KXL.CURVA_ENTRADA, KXL.NUM_ENTERO),
                    (KXL.CURVA_SALIDA, KXL.NUM_ENTERO))
        estimables = (KXL.CURVA_DIF_REVELADOR, KXL.CURVA_ENTRADA)
        cols_estimadas = [col_apuntado + 1 + j
                          for j, (desp, _) in enumerate(cols_num)
                          if desp in estimables]
        col_punto = col_apuntado + 1 + len(cols_num)
        medido = self.revelador_medido()
        por_zona = self.valores_constantes()[KXL.C_TERCIO_POR_ZONA]
        for i in range(n):
            fila += 1
            banda = (i % 2) == 0

            # --- Las zonas enteras (los puntos de la curva), en negrita
            entera = ((i - KS.TERCIOS_LADO) % por_zona) == 0
            self.formula(
                hoja, fila, col, "=" + self.ref(KXL.T_HOJA_CALCULO, b3 + i,
                                                col_calculo),
                self.celda_resumen(banda, "right", bold=entera),
                self.nombre_zona(i - KS.TERCIOS_LADO))
            apuntado = self.celda_resumen(banda, "center", KXL.NUM_UNO,
                                          font_color=KXL.COLOR_DATO,
                                          bold=entera)
            medido_i = medido[i]
            if medido_i is None:
                hoja.write_blank(fila, col_apuntado, None, apuntado)
            else:
                hoja.write_number(fila, col_apuntado, medido_i, apuntado)
            for j, (desp, numero) in enumerate(cols_num):
                origen = self.ref(KXL.T_HOJA_CALCULO, b3 + i,
                                  col_calculo + desp)
                resultado = self.valor(hoja_calculo, b3 + i,
                                       col_calculo + desp)
                self.formula(
                    hoja, fila, col_apuntado + 1 + j,
                    f'=IF(ISNUMBER({origen}),{origen},"")',
                    self.celda_resumen(banda, "center", numero,
                                       bold=entera),
                    resultado if isinstance(resultado, (int, float))
                    else "")
            origen = self.ref(KXL.T_HOJA_CALCULO, b3 + i,
                              col_calculo + KXL.CURVA_PUNTO)
            self.formula(
                hoja, fila, col_punto, f'=IF({origen}="","",{origen})',
                self.celda_resumen(banda, "center", bold=entera),
                self.valor(hoja_calculo, b3 + i,
                           col_calculo + KXL.CURVA_PUNTO))

        # --- Lo estimado, en su color: hay valor sin L* leído
        primera = f[KXL.F_APUNTADO]
        apuntado_fila = celda(primera, col_apuntado, False, True)
        estimado = self.__excel.add_format(
            {"font_color": KXL.COLOR_ESTIMADO})
        for c in cols_estimadas:
            hoja.conditional_format(
                primera, c, fila, c,
                {"type": "formula",
                 "criteria": f'=AND({apuntado_fila}="",'
                 f'ISNUMBER({celda(primera, c)}))',
                 "format": estimado})

        # --- Decisiones propias: la zona, desplegable (KXL.SIN_ZONA y las
        #     de la tabla); la entrada, la de esa zona en la tabla (fórmula:
        #     el estudiante solo elige la zona y su salida; con SIN_ZONA, en
        #     blanco); la salida, entero de 0 a C_ESCALA_CURVA
        rango_zonas = (f"{celda(primera, col, True, True)}:"
                       f"{celda(fila, col, True, True)}")
        col_entrada = (col_apuntado + 1
                       + [desp for desp, _ in cols_num].index(
                           KXL.CURVA_ENTRADA))
        rango_entradas = (f"{celda(primera, col_entrada, True, True)}:"
                          f"{celda(fila, col_entrada, True, True)}")
        for i, r in enumerate(range(primera_propia, ultima_propia + 1)):
            formato = self.celda_resumen(
                (i % 2) == 0, "center", KXL.NUM_ENTERO,
                font_color=KXL.COLOR_FORMULA)
            for lado in KXL.LADOS_DECISIONES:
                zona = celda(r, col + lado)
                self.formula(
                    hoja, r, col + lado + 1,
                    f'=IF({zona}="","",IFERROR(INDEX({rango_entradas},'
                    f'MATCH({zona},{rango_zonas},0)),""))', formato, "")
        lista_zonas = [KXL.SIN_ZONA] + [
            self.nombre_zona(i - KS.TERCIOS_LADO)
            for i in range((2 * KS.TERCIOS_LADO) + 1)]
        for lado in KXL.LADOS_DECISIONES:
            hoja.data_validation(
                primera_propia, col + lado, ultima_propia, col + lado,
                {"validate": "list", "source": lista_zonas,
                 "error_title": t[KXL.T_DECISIONES],
                 "error_message": t[KXL.T_VALIDA_ZONA]})
            hoja.data_validation(
                primera_propia, col + lado + 2, ultima_propia,
                col + lado + 2,
                {"validate": "integer", "criteria": "between",
                 "minimum": 0, "maximum": f"={KXL.C_ESCALA_CURVA}",
                 "error_title": t[KXL.T_DECISIONES],
                 "error_message": t[KXL.T_VALIDA_CURVA].format(
                     tope=self.valores_constantes()[KXL.C_ESCALA_CURVA])})
        return fila

    #
    def bloque_tu_curva(self) -> None:
        """
        Tu curva, a la derecha del bloque 3 de Cálculo: los puntos de las
        decisiones propias de Análisis (los que tienen entrada y salida),
        en su tabla, y, por zona, la entrada del revelador pasada por
        ellos en recta entre el de abajo y el de arriba ((0, 0) y
        (C_ESCALA_CURVA, C_ESCALA_CURVA) en los extremos): la salida, su
        L*, la diferencia con el objetivo y falta y sobra. Sin puntos o
        sin revelador, en blanco (NA() en lo que dibuja la gráfica). Va
        después de Análisis, cuando se sabe dónde están las decisiones.
        """
        t, f = self.__textos, self.__filas
        hoja = self.__hojas[KXL.T_HOJA_CALCULO]
        col, b3 = KXL.COLUMNA_INICIO, f[KXL.F_CURVA]
        n = (2 * KS.TERCIOS_LADO) + 1
        self.cabecera(hoja, b3 - 1, col + KXL.TU_DESDE_ENTRADA, tuple(
            t[c] for c in (KXL.T_CAB_TU_DESDE_ENTRADA,
                           KXL.T_CAB_TU_DESDE_SALIDA,
                           KXL.T_CAB_TU_HASTA_ENTRADA,
                           KXL.T_CAB_TU_HASTA_SALIDA, KXL.T_CAB_TU_SALIDA,
                           KXL.T_CAB_TU_L, KXL.T_CAB_TU_DIF, KXL.T_CAB_FALTA,
                           KXL.T_CAB_SOBRA)))
        self.cabecera(hoja, b3 - 1, col + KXL.TU_PUNTOS_ENTRADA, (
            t[KXL.T_CAB_TU_PUNTO_ENTRADA], t[KXL.T_CAB_TU_PUNTO_SALIDA]))

        # --- Los puntos: cada fila de las decisiones, de un lado y luego
        #     del otro; solo con entrada y salida
        filas_puntos = KXL.FILAS_DECISIONES * len(KXL.LADOS_DECISIONES)
        col_decisiones = self.columna_derecha()
        for j in range(filas_puntos):
            r = b3 + j
            fmt = partial(self.fmt_formula, (j % 2) == 0)
            lado = KXL.LADOS_DECISIONES[j // KXL.FILAS_DECISIONES]
            fila_decision = f[KXL.F_DECISIONES] + (j % KXL.FILAS_DECISIONES)
            entrada, salida = (
                self.ref(KXL.T_HOJA_RESUMEN, fila_decision,
                         col_decisiones + lado + desp) for desp in (1, 2))
            completo = f"AND(ISNUMBER({entrada}),ISNUMBER({salida}))"
            for desp, valor in ((KXL.TU_PUNTOS_ENTRADA, entrada),
                                (KXL.TU_PUNTOS_SALIDA, salida)):
                self.formula(hoja, r, col + desp,
                             f'=IF({completo},{valor},"")',
                             fmt(KXL.NUM_ENTERO), "")
        entradas, salidas = (
            xl_range_abs(b3, col + desp, (b3 + filas_puntos) - 1, col + desp)
            for desp in (KXL.TU_PUNTOS_ENTRADA, KXL.TU_PUNTOS_SALIDA))

        # --- Por zona: el tramo (desde y hasta: entrada y salida), la
        #     salida en recta, su L*, la diferencia y falta y sobra
        tope = KXL.C_ESCALA_CURVA
        for i in range(n):
            r = b3 + i
            fmt = partial(self.fmt_formula, (i % 2) == 0)
            c = partial(Excel.celda_desp, r, col)
            x = c(KXL.CURVA_ENTRADA)
            de, ds, he, hs = (c(d) for d in (
                KXL.TU_DESDE_ENTRADA, KXL.TU_DESDE_SALIDA,
                KXL.TU_HASTA_ENTRADA, KXL.TU_HASTA_SALIDA))
            ts, tl, obj = (c(KXL.TU_SALIDA), c(KXL.TU_L),
                           c(KXL.CURVA_L_OBJETIVO))
            hay = f"AND(ISNUMBER({x}),COUNT({entradas})>0)"
            formulas = (
                (KXL.TU_DESDE_ENTRADA,
                 f'=IF({hay},MAXIFS({entradas},{entradas},"<="&{x}),"")',
                 KXL.NUM_ENTERO, ""),
                (KXL.TU_DESDE_SALIDA,
                 f'=IF(ISNUMBER({de}),IF(COUNTIFS({entradas},{de})>0,'
                 f'AVERAGEIFS({salidas},{entradas},{de}),{de}),"")',
                 KXL.NUM_ENTERO, ""),
                (KXL.TU_HASTA_ENTRADA,
                 f'=IF({hay},IF(COUNTIFS({entradas},">="&{x})=0,{tope},'
                 f'MINIFS({entradas},{entradas},">="&{x})),"")',
                 KXL.NUM_ENTERO, ""),
                (KXL.TU_HASTA_SALIDA,
                 f'=IF(ISNUMBER({he}),IF(COUNTIFS({entradas},{he})>0,'
                 f'AVERAGEIFS({salidas},{entradas},{he}),{he}),"")',
                 KXL.NUM_ENTERO, ""),
                (KXL.TU_SALIDA,
                 f'=IF(ISNUMBER({de}),IF({he}={de},{ds},'
                 f'{ds}+((({hs}-{ds})*({x}-{de}))/({he}-{de}))),"")',
                 KXL.NUM_UNO, ""),
                (KXL.TU_L,
                 f'=IF(ISNUMBER({ts}),'
                 f'{self.formula_lab(self.formula_luz_curva(ts))},'
                 f'{KXL.FORMULA_NA})', KXL.NUM_UNO, KXL.RESULTADO_NA),
                (KXL.TU_DIF,
                 f'=IF(ISNUMBER({tl}),{tl}-{obj},{KXL.FORMULA_NA})',
                 KXL.NUM_SIGNO_UNO, KXL.RESULTADO_NA),
                (KXL.TU_FALTA,
                 f'=IF(ISNUMBER({tl}),MAX(0,{obj}-{tl}),"")',
                 KXL.NUM_UNO, ""),
                (KXL.TU_SOBRA,
                 f'=IF(ISNUMBER({tl}),MAX(0,{tl}-{obj}),"")',
                 KXL.NUM_UNO, ""))
            for desp, texto, numero, valor in formulas:
                self.formula(hoja, r, col + desp, texto, fmt(numero), valor)

    #
    def revelador_datos(self) -> None:
        """
        L* del revelador en Datos: el L* leído de Análisis y, en un
        tercio sin él, el estimado: la diferencia con el esperado de
        Cálculo (L* leído menos esperado) de las dos zonas enteras
        vecinas, repartida en recta y sumada al esperado del tercio, sin
        salirse de los L* de esas dos zonas (MEDIAN). Si falta una de las
        dos, en blanco. Va después de Cálculo y Análisis.
        """
        f = self.__filas
        hoja = self.__hojas[KXL.T_HOJA_DATOS]
        col = KXL.COLUMNA_INICIO
        col_apuntado = self.columna_derecha() + KXL.COL_APUNTADO
        col_esperado = col + KXL.CURVA_L_ESPERADO
        por_zona = self.valores_constantes()[KXL.C_TERCIO_POR_ZONA]
        for i, valor in enumerate(self.__revelador):
            tercio = (i - KS.TERCIOS_LADO) % por_zona
            apuntado = self.ref(KXL.T_HOJA_RESUMEN, f[KXL.F_APUNTADO] + i,
                                col_apuntado)
            formula = f'=IF(ISNUMBER({apuntado}),{apuntado},"")'
            if tercio:
                antes, tras = i - tercio, i - tercio + por_zona
                apuntado_a, apuntado_d = (
                    self.ref(KXL.T_HOJA_RESUMEN, f[KXL.F_APUNTADO] + z,
                             col_apuntado) for z in (antes, tras))
                esp_i, esp_a, esp_d = (
                    self.ref(KXL.T_HOJA_CALCULO, f[KXL.F_CURVA] + z,
                             col_esperado) for z in (i, antes, tras))
                dif_a = f"({apuntado_a}-{esp_a})"
                dif_d = f"({apuntado_d}-{esp_d})"
                formula = (f'=IF(ISNUMBER({apuntado}),{apuntado},'
                           f'IF(AND(ISNUMBER({apuntado_a}),'
                           f'ISNUMBER({apuntado_d})),'
                           f'MEDIAN({apuntado_a},{apuntado_d},{esp_i}+{dif_a}+'
                           f'({dif_d}-{dif_a})*{tercio}/'
                           f'{KXL.C_TERCIO_POR_ZONA}),""))')
            self.formula(
                hoja, f[KXL.F_REVELADOR] + i, col + KXL.COL_REVELADOR, formula,
                self.celda(KXL.COLOR_FORMULA, (i % 2) == 0, "center",
                           KXL.NUM_UNO), self.en_blanco(valor))

    #
    def hoja_graf(self) -> None:
        """
        Hoja Gráficos: seis gráficas que leen de Cálculo (y Datos), en el
        orden de KXL.ORDEN_GRAF (que les da su número): la curva tonal en
        L*, la diferencia en L* con el objetivo, tu curva (las decisiones
        propias), la desviación del tramo lineal, los balances de blancos
        y la señal/ruido. Las de auditoría (KXL.GRAF_AUDITORIA: esperado y
        obtenido, con un segundo eje en pasos respecto a la Z-V, y la
        desviación de todo el rango), sin número, al final de Cálculo. La
        serie del revelador, siempre: el L* leído puede llegar después (a
        mano); sin él, Cálculo da NA() y la gráfica no lo dibuja.
        """
        t, d, f = self.__textos, self.__datos, self.__filas
        hoja = self.__hojas[KXL.T_HOJA_GRAF]
        col, n = KXL.COLUMNA_INICIO, (2 * KS.TERCIOS_LADO) + 1
        b2, b3 = f[KXL.F_TERCIOS], f[KXL.F_CURVA]
        self.titulo(hoja, KXL.FILA_INICIO, col, t[KXL.T_TITULO_GRAF],
                    t[KXL.T_NOTA_GRAF].format(cam=d.cam),
                    KXL.ANCHOS_GRAF)
        canales = KXL.T_CANALES

        rango = partial(Excel.rango_graf, t[KXL.T_HOJA_CALCULO], col, n)

        linea = Excel.linea_graf

        marcador = Excel.marcador_graf

        graf = partial(self.nueva_graf, t)

        zonas_b2, zonas_b3 = rango(b2, 0), rango(b3, 0)
        grafs: dict[str, Chart] = {}

        # --- Esperado y obtenido, con barras lilas del verde hasta el
        #     esperado y un segundo eje en pasos respecto a la Z-V
        g = graf("line", KXL.T_G_ESPERADO, KXL.EJE_ZONAS,
                 KXL.T_EJE_SIGNAL)
        g.add_series({"name": t[KXL.T_CAB_ESPERADO], "categories": zonas_b2,
                      "values": rango(b2, 2),
                      "line": {**linea(KXL.COLOR_ESPERADO,
                                       KXL.ANCHO_ESPERADO),
                               "transparency": KXL.TRANSPARENCIA_ESPERADO}})
        for j in range(KXL.CANALES):
            serie = {"name": t[canales[j]], "categories": zonas_b2,
                     "values": rango(b2, 3 + j), "line": {"none": True},
                     "marker": marcador(KXL.COLORES_CANALES[j],
                                        KXL.FORMAS_CANALES[j])}
            if j == 1:
                serie["y_error_bars"] = {
                    "type": "custom", "direction": "plus",
                    "plus_values": rango(b2, 15), "end_style": 0,
                    "line": linea(KXL.COLOR_BARRAS, KXL.ANCHO_BARRAS)}
            g.add_series(serie)
        g.add_series({"name": t[KXL.T_CAB_TECHO_VERDE],
                      "categories": zonas_b2, "values": rango(b2, 16),
                      "line": linea(KXL.COLORES_CANALES[1], trazo="dash")})
        g.add_series({"name": t[KXL.T_CAB_SUELO_VERDE],
                      "categories": zonas_b2, "values": rango(b2, 17),
                      "line": linea(KXL.COLORES_CANALES[1],
                                    trazo="round_dot")})
        g.add_series({"categories": zonas_b2, "values": rango(b2, 2),
                      "y2_axis": True, "line": {"none": True}})
        piso, tope, paso, formato_num = KXL.EJE_ZONAS
        zona_zv = self.valores_constantes()[KXL.C_ZONA_ZV]
        g.set_y2_axis({"name": t[KXL.T_EJE_PASOS], "min": piso - zona_zv,
                       "max": tope - zona_zv, "major_unit": paso,
                       "num_format": formato_num})
        g.set_legend({"position": "bottom",
                      "delete_series": [KXL.CANALES + 3]})
        grafs[KXL.T_G_ESPERADO] = g

        # --- Desviación por canal: tramo lineal y rango completo
        for titulo, eje in ((KXL.T_G_DESV_LINEAL, KXL.EJE_DESV_LINEAL),
                            (KXL.T_G_DESV_COMPLETA, KXL.EJE_DESV_COMPLETA)):
            g = graf("line", titulo, eje, KXL.T_EJE_DEV)
            for j in range(KXL.CANALES):
                g.add_series({"name": t[canales[j]], "categories": zonas_b2,
                              "values": rango(b2, 6 + j),
                              "line": linea(KXL.COLORES_CANALES[j])})
            grafs[titulo] = g

        # --- Señal/ruido por canal, normalizada a C_MPX_REFERENCIA (en
        #     escala logarítmica), el modelo del verde y los tres umbrales:
        #     ingeniería, mínimo sugerido y excelente
        g = graf("line", KXL.T_G_SNR, KXL.EJE_SNR, KXL.T_EJE_SNR,
                 KXL.BASE_EJE_SNR)
        for j in range(KXL.CANALES):
            g.add_series({"name": t[canales[j]], "categories": zonas_b2,
                          "values": rango(b2, 19 + j), "line": {"none": True},
                          "marker": marcador(KXL.COLORES_CANALES[j],
                                             KXL.FORMAS_CANALES[j])})
        g.add_series({"name": t[KXL.T_S_MODELO], "categories": zonas_b2,
                      "values": rango(b2, 22),
                      "line": linea(KXL.COLORES_CANALES[1], trazo="dash")})
        for nombre, desp, trazo in ((KXL.T_S_ING, 24, "round_dot"),
                                    (KXL.T_S_MIN, 18, "dash"),
                                    (KXL.T_S_EXCELENTE, 23, "long_dash")):
            g.add_series({"name": t[nombre], "categories": zonas_b2,
                          "values": rango(b2, desp),
                          "line": linea(KXL.COLOR_ESPERADO, trazo=trazo)})
        grafs[KXL.T_G_SNR] = g

        # --- Curva tonal en L*: esperado, objetivo, sensor y
        #     revelador, con barras lilas hasta el objetivo
        g = graf("line", KXL.T_G_CURVA, KXL.EJE_LSTAR, KXL.T_EJE_LSTAR)
        g.add_series({"name": t[KXL.T_CAB_ESPERADO], "categories": zonas_b3,
                      "values": rango(b3, 3),
                      "line": {**linea(KXL.COLOR_ESPERADO,
                                       KXL.ANCHO_ESPERADO),
                               "transparency": KXL.TRANSPARENCIA_ESPERADO}})
        g.add_series({"name": t[KXL.T_CAB_L_OBJETIVO],
                      "categories": zonas_b3, "values": rango(b3, 4),
                      "line": linea(KXL.COLOR_OBJETIVO, trazo="dash")})
        g.add_series({"name": t[KXL.T_S_SENSOR], "categories": zonas_b3,
                      "values": rango(b3, 6),
                      "line": linea(KXL.COLOR_SENSOR)})
        g.add_series({
            "name": t[KXL.T_S_REVELADOR], "categories": zonas_b3,
            "values": rango(b3, 8),
            "line": linea(KXL.COLORES_CANALES[2]),
            "marker": marcador(KXL.COLORES_CANALES[2]),
            "y_error_bars": {
                "type": "custom", "plus_values": rango(b3, 11),
                "minus_values": rango(b3, 12), "end_style": 0,
                "line": linea(KXL.COLOR_BARRAS, KXL.ANCHO_BARRAS)}})
        grafs[KXL.T_G_CURVA] = g

        # --- Diferencia en L*: cuánto se separa el revelado del objetivo
        #     (lo que el estudiante corrige); las negativas, en rojo. La
        #     del sensor (con el esperado) queda en Cálculo
        g = graf("column", KXL.T_G_DIFERENCIA, KXL.EJE_DIF_LSTAR,
                 KXL.T_EJE_DIF_LSTAR)
        g.add_series({"name": t[KXL.T_S_REVELADOR], "categories": zonas_b3,
                      "values": rango(b3, KXL.CURVA_DIF_REVELADOR),
                      "fill": {"color": KXL.COLORES_CANALES[2]},
                      "invert_if_negative": True,
                      "invert_if_negative_color": KXL.COLOR_NEGATIVO})
        grafs[KXL.T_G_DIFERENCIA] = g

        # --- Tu curva: el revelado con los puntos de las decisiones
        #     propias, con barras lilas hasta el objetivo; el objetivo y,
        #     fino y gris, el revelado sin ellos
        g = graf("line", KXL.T_G_TU_CURVA, KXL.EJE_LSTAR, KXL.T_EJE_LSTAR)
        g.add_series({"name": t[KXL.T_CAB_L_OBJETIVO],
                      "categories": zonas_b3,
                      "values": rango(b3, KXL.CURVA_L_OBJETIVO),
                      "line": linea(KXL.COLOR_OBJETIVO, trazo="dash")})
        g.add_series({"name": t[KXL.T_S_REVELADOR], "categories": zonas_b3,
                      "values": rango(b3, KXL.CURVA_L_REVELADOR),
                      "line": linea(KXL.COLOR_ESPERADO)})
        g.add_series({
            "name": t[KXL.T_S_TU_CURVA], "categories": zonas_b3,
            "values": rango(b3, KXL.TU_L),
            "line": linea(KXL.COLORES_CANALES[2]),
            "marker": marcador(KXL.COLORES_CANALES[2]),
            "y_error_bars": {
                "type": "custom", "plus_values": rango(b3, KXL.TU_FALTA),
                "minus_values": rango(b3, KXL.TU_SOBRA), "end_style": 0,
                "line": linea(KXL.COLOR_BARRAS, KXL.ANCHO_BARRAS)}})
        grafs[KXL.T_G_TU_CURVA] = g

        # --- Balances de blancos (de Datos): por balance, los Kelvin que
        #     anota la cámara y los que de verdad aplica. Sin balances, la
        #     fila que lo dice (la gráfica sale vacía)
        nb = max(1, len(d.balancesDistintos))
        balances = partial(Excel.rango_graf, t[KXL.T_HOJA_DATOS], col, nb,
                           f[KXL.F_BALANCES])
        g = graf("column", KXL.T_G_BALANCES, KXL.EJE_KELVIN,
                 KXL.T_EJE_KELVIN)
        g.set_x_axis({"name": t[KXL.T_CAB_BALANCE]})
        for desp, clave, color in (
                (KXL.COL_VALORES, KXL.T_CAB_KELVIN_ANOTADO,
                 KXL.COLOR_ESPERADO),
                (KXL.COL_VALORES + 1, KXL.T_CAB_KELVIN_MEDIDO,
                 KXL.COLORES_CANALES[2])):
            g.add_series({"name": t[clave], "categories": balances(0),
                          "values": balances(desp),
                          "fill": {"color": color}})
        grafs[KXL.T_G_BALANCES] = g

        # --- Los huecos, con su borde, y cada gráfica en el suyo
        gris = KXL.BORDE_HUECO
        ultima_fila = 0
        for i, clave in enumerate(KXL.ORDEN_GRAF):
            g = grafs[clave]
            fila0 = KXL.FILA_HUECOS + ((i // 2) * (KXL.FILAS_HUECO + 1))
            col0 = col + ((i % 2) * (KXL.COLUMNAS_HUECO + 1))
            fila1 = fila0 + KXL.FILAS_HUECO - 1
            col1 = col0 + KXL.COLUMNAS_HUECO - 1
            for r in range(fila0, fila1 + 1):
                for c in range(col0, col1 + 1):
                    bordes: dict = {}
                    if r == fila0:
                        bordes.update(top=KXL.FINO, top_color=gris)
                    if r == fila1:
                        bordes.update(bottom=KXL.FINO, bottom_color=gris)
                    if c == col0:
                        bordes.update(left=KXL.FINO, left_color=gris)
                    if c == col1:
                        bordes.update(right=KXL.FINO, right_color=gris)
                    if bordes:
                        hoja.write_blank(r, c, None, self.formato(**bordes))
            hoja.insert_chart(fila0, col0, g,
                              {"x_offset": KXL.MARGEN_GRAF,
                               "y_offset": KXL.MARGEN_GRAF})
            ultima_fila = max(ultima_fila, fila1)
        self.marco(hoja, ((ultima_fila, KXL.ANCHOS_GRAF),))

        # --- Las de auditoría, al final de Cálculo, una al lado de otra
        hoja_calculo = self.__hojas[KXL.T_HOJA_CALCULO]
        for i, clave in enumerate(KXL.GRAF_AUDITORIA):
            hoja_calculo.insert_chart(
                f[KXL.F_AUDITORIA], col + (i * KXL.COLUMNAS_AUDITORIA),
                grafs[clave], {"x_offset": KXL.MARGEN_GRAF,
                               "y_offset": KXL.MARGEN_GRAF})

    #
    def hoja_rechazadas(self) -> None:
        """
        Hoja Rechazadas: las teselas de tarjeta gris que los filtros dejan
        fuera (en la Z-V; valen para toda la serie). Recuento (de
        tarjeta, rechazadas, porcentaje y por motivo), gráfico de
        dispersión (por zona, cuánto se aparta cada rechazada de las
        buenas en el verde, en zonas; una serie por motivo) y, debajo,
        sus datos, agrupados por motivo.
        """
        t, d = self.__textos, self.__datos
        hoja = self.__hojas[KXL.T_HOJA_RECHAZADAS]
        fila, col = KXL.FILA_INICIO, KXL.COLUMNA_INICIO
        self.titulo(hoja, fila, col, t[KXL.T_TITULO_RECHAZADAS],
                    t[KXL.T_NOTA_RECHAZADAS],
                    KXL.ANCHOS_RECHAZADAS)
        motivos = d.motivos.ravel()
        tarjeta = int((motivos != KTE.NO_TARJETA).sum())
        es_rechazada = (motivos != KTE.NO_TARJETA) & (motivos != KTE.BUENA)
        rechazadas = int(es_rechazada.sum())

        # --- Recuento
        fila += 3
        hoja.write(fila, col, t[KXL.T_RECUENTO], self.apartado())
        #     Junto a cada motivo, qué significa (en las columnas que
        #     quedan, partido en líneas)
        fila += 1
        ultima = col + len(KXL.ANCHOS_RECHAZADAS) - 1
        ancho_explica = sum(KXL.ANCHOS_RECHAZADAS[2:])
        self.cabecera(hoja, fila, col, (t[KXL.T_CAB_CONCEPTO],
                                        t[KXL.T_CAB_VALOR]))
        hoja.merge_range(fila, col + 2, fila, ultima, t[KXL.T_CAB_QUE_ES],
                         self.fmt_cabecera())
        umbrales = dict(nivel=self.tercios_texto(KTE.NIVEL_MAX_ZONAS),
                        rareza=KTE.RAREZA, lado=KTE.LADO)
        recuento = [(t[KXL.T_TESELAS_TARJETA], tarjeta, KXL.NUM_ENTERO, ""),
                    (t[KXL.T_TESELAS_RECHAZADAS], rechazadas,
                     KXL.NUM_ENTERO, ""),
                    (t[KXL.T_PORCENTAJE], (KXL.CIEN * rechazadas / tarjeta)
                     if tarjeta else 0.0, KXL.NUM_UNO, "")]
        recuento += [(t[KXL.T_POR_MOTIVO].format(motivo=t[clave]),
                      int((motivos == code).sum()), KXL.NUM_ENTERO,
                      t[KXL.EXPLICA_MOTIVO[code]].format(**umbrales))
                     for code, clave, _ in KXL.MOTIVOS]
        for i, (texto, valor, numero, explica) in enumerate(recuento):
            fila += 1
            banda = (i % 2) == 0
            hoja.write(fila, col, texto,
                       self.celda(KXL.COLOR_ROTULO, banda, "left",
                                  valign="top"))
            hoja.write_number(fila, col + 1, valor,
                              self.celda(KXL.COLOR_DATO, banda, "center",
                                         numero, valign="top"))
            hoja.merge_range(fila, col + 2, fila, ultima, explica,
                             self.celda(KXL.COLOR_ROTULO, banda, "left",
                                        text_wrap=True, valign="top"))
            if explica:
                hoja.set_row(fila, KXL.ALTO_LINEA
                             * self.lineas(explica, ancho_explica))

        # --- Hueco del gráfico; los datos, debajo
        fila_graf = fila + 2
        fila = fila_graf + KXL.FILAS_HUECO + 1
        hoja.write(fila, col, t[KXL.T_DATOS_GRAF], self.apartado())
        fila += 1
        self.cabecera(hoja, fila, col, (t[KXL.T_CAB_ZONA],
                                        t[KXL.T_CAB_POS],
                                        t[KXL.T_CAB_MOTIVO],
                                        t[KXL.T_CAB_DEV]))
        hoja.set_row(fila, KXL.ALTO_CABECERA)
        motivo_rechazada = motivos[es_rechazada]
        zona_zv = self.valores_constantes()[KXL.C_ZONA_ZV]
        tercios = self.valores_constantes()[KXL.C_TERCIO_POR_ZONA]
        series = []
        banda = True
        for code, clave, color in KXL.MOTIVOS:
            desde = fila + 1
            for i, zona in enumerate(d.zonas):
                if zona is None:
                    continue
                tercio_ev = i - KS.TERCIOS_LADO
                for dev, motivo in zip(zona.dev, motivo_rechazada):
                    if ((motivo != code) or (dev is None)
                            or (not math.isfinite(dev))):
                        continue
                    fila += 1
                    banda = not banda
                    hoja.write(fila, col, self.nombre_zona(tercio_ev),
                               self.celda(KXL.COLOR_LITERAL, banda,
                                          "center"))
                    hoja.write_number(fila, col + 1,
                                      zona_zv + (tercio_ev / tercios),
                                      self.celda(KXL.COLOR_DATO, banda,
                                                 "center", KXL.NUM_DOS))
                    hoja.write(fila, col + 2, t[clave],
                               self.celda(KXL.COLOR_DATO, banda, "center"))
                    hoja.write_number(fila, col + 3, dev,
                                      self.celda(KXL.COLOR_DATO, banda,
                                                 "center",
                                                 KXL.NUM_DEV))
            if fila >= desde:
                series.append((t[clave], color, desde, fila))

        # --- El gráfico de dispersión, una serie por motivo
        g = cast(Chart, self.__excel.add_chart({"type": "scatter"}))
        g.set_title({"name": t[KXL.T_G_RECHAZADAS]})
        piso, tope, paso, formato_num = KXL.EJE_POS
        g.set_x_axis({"name": t[KXL.T_EJE_ZONA], "min": piso,
                      "max": tope, "major_unit": paso,
                      "num_format": formato_num})
        g.set_y_axis({"name": t[KXL.T_EJE_DEV],
                      "num_format": KXL.NUM_DEV})
        g.set_legend({"position": "bottom"})
        g.set_size({"width": KXL.MEDIDA_GRAF[0],
                    "height": KXL.MEDIDA_GRAF[1]})
        nombre = t[KXL.T_HOJA_RECHAZADAS]
        for texto, color, desde, hasta in series:
            g.add_series({
                "name": texto,
                "categories": f"='{nombre}'!" + xl_range_abs(
                    desde, col + 1, hasta, col + 1),
                "values": f"='{nombre}'!" + xl_range_abs(
                    desde, col + 3, hasta, col + 3),
                "marker": {"type": "circle", "size": KXL.MEDIDA_MARCADOR,
                           "fill": {"color": color},
                           "border": {"color": color}}})
        hoja.insert_chart(fila_graf, col, g,
                          {"x_offset": KXL.MARGEN_GRAF,
                           "y_offset": KXL.MARGEN_GRAF})
        self.marco(hoja, ((fila, KXL.ANCHOS_RECHAZADAS),))

    #
    def hoja_ia(self) -> None:
        """
        Hoja IA: las instrucciones para revisar el libro con una IA, de
        su archivo (siempre en español), una línea por fila: la IA las lee
        en las celdas. Las líneas de título, en negrita. Si el archivo no
        se puede leer, la hoja sale vacía
        """
        hoja = self.__hojas[KXL.T_HOJA_IA]
        col = KXL.COLUMNA_INICIO
        hoja.set_column(col, col, KXL.ANCHO_IA)
        normal = self.formato(text_wrap=True, valign="top")
        titulo = self.formato(text_wrap=True, valign="top", bold=True)
        try:
            lineas = self.con_nombre(K.ruta_prompt_ia.read_text(
                encoding="utf-8")).splitlines()
        except OSError:
            lineas = []
        for i, linea in enumerate(lineas):
            if linea.strip():
                hoja.write_string(KXL.FILA_INICIO + i, col, linea,
                                  titulo if linea.startswith(
                                      KXL.MARCA_TITULO_IA) else normal)
        hoja.hide_gridlines(2)

    #
    def hoja_iso(self) -> None:
        """
        Hoja ISO: la secuencia de ISO, una fila por ISO (ver
        Review.filasISO), en verde: su Z2, cuánto se aparta su Z-V de la
        del ISO inicial, el ruido de lectura, el ruido de la tarjeta en la
        Z-V y en la Z2, la textura del paño en la Z2, textura/ruido, qué
        parte del umbral de sombras es (ver umbral_iso), cómo es la
        textura (se ve, justa o se pierde) y una nota (estimación o sin
        medir)
        """
        t = self.__textos
        hoja = self.__hojas[KXL.T_HOJA_ISO]
        fila, col = KXL.FILA_INICIO, KXL.COLUMNA_INICIO
        k = self.valores_constantes()
        umbral = self.umbral_iso(k)
        self.titulo(hoja, fila, col, t[KXL.T_TITULO_ISO],
                    Excel.con_nombre(
                        self.rotulo_sombra(t[KXL.T_NOTA_ISO])).format(
                        umbral=(KXL.SIN_DATO if umbral is None
                                else self.numero_texto(umbral, 1)),
                        justa=round(k[KXL.C_TEXTURA_JUSTA] * KXL.CIEN)),
                    KXL.ANCHOS_ISO)
        fila += 3
        self.cabecera(hoja, fila, col, tuple(
            self.rotulo_sombra(t[c]) for c in (
            KXL.T_CAB_ISO, KXL.T_CAB_Z2, KXL.T_CAB_DESVIACION_ISO,
            KXL.T_CAB_LECTURA_ISO, KXL.T_CAB_RUIDO_ZV, KXL.T_CAB_RUIDO_Z2,
            KXL.T_CAB_TEXTURA_Z2, KXL.T_CAB_TEXTURA_RUIDO_Z2,
            KXL.T_CAB_PORCENTAJE_UMBRAL, KXL.T_CAB_SE_APRECIA,
            KXL.T_CAB_SOMBRAS_ISO, KXL.T_CAB_NOTA_ISO)))
        hoja.set_row(fila, KXL.ALTO_CABECERA)
        for n, f in enumerate(self.__datos.filasISO):
            fila += 1
            banda = (n % 2) == 0
            valores = (
                (f.iso, KXL.NUM_ENTERO), (self.zona_z2(f), None),
                (f.desviacion, KXL.NUM_DEV), (f.lectura, KXL.NUM_DOS),
                (f.ruido_zv, KXL.NUM_PORCENTAJE),
                (f.ruido_z2, KXL.NUM_PORCENTAJE),
                (f.textura_z2, KXL.NUM_PORCENTAJE),
                (f.textura_ruido, KXL.NUM_DOS),
                (self.parte_umbral(f, umbral), KXL.NUM_PORCENTAJE),
                (self.aprecia_iso(f, k, umbral), None),
                (self.sombras_iso(f, k, umbral) or None, None))
            for i, (valor, numero) in enumerate(valores):
                formato = self.celda(KXL.COLOR_DATO, banda, "center", numero)
                if valor is None:
                    hoja.write_blank(fila, col + i, None, formato)
                elif numero is None:
                    hoja.write_string(fila, col + i, valor, formato)
                else:
                    hoja.write_number(fila, col + i, valor, formato)
            hoja.write_string(fila, col + len(valores), self.nota_iso(f),
                              self.celda(KXL.COLOR_ROTULO, banda, "left"))
        self.marco(hoja, ((fila, KXL.ANCHOS_ISO),))

    #
    def zona_z2(self, f: FilaISO) -> str:
        """ Nombre de la zona de la Z2 de un ISO ("" si no la tiene). """
        return "" if (f.tercio_z2 is None) else self.nombre_zona(f.tercio_z2)

    #
    def zona_sombra_iso(self) -> str:
        """
        Nombre de la zona de la toma de sombras de la secuencia de ISO: Z2,
        Z3 o Z2/Z3 si hay ISO de las dos (la Z2 si no hay ninguno
        medible).
        """
        sitios = sorted({tercios_sombra(f.tercio_z2)
                         for f in self.__datos.filasISO if f.medible}
                        - {None})
        return KXL.SEPARADOR_ZONAS.join(
            self.nombre_zona(sitio) for sitio in (sitios or [KS.TERCIOS_Z2]))

    #
    def rotulo_sombra(self, texto: str) -> str:
        """
        Un texto de la secuencia de ISO (antes de rellenarlo) con la «Z2»
        cambiada por la zona de la toma de sombras, si es la Z3 o hay de
        las dos (Z2/Z3).
        """
        return texto.replace(KXL.ZONA_SOMBRA_TEXTO, self.zona_sombra_iso())

    #
    def nota_iso(self, f: FilaISO) -> str:
        """
        Nota de un ISO de la secuencia de ISO: que no se puede medir, que
        es una estimación (con la zona a la que llegó su Z2) o nada
        """
        t = self.__textos
        if not f.medible:
            return t[KXL.T_ISO_SIN_MEDIR]
        if f.estimada:
            return self.rotulo_sombra(t[KXL.T_ISO_ESTIMADO]).format(
                zona=self.zona_z2(f))
        return ""

    #
    def umbral_iso(self, k: dict) -> float | None:
        """
        Umbral de la textura en la Z2 de cada ISO: el de las sombras de la
        serie (ver umbral_sombras)
        """
        return self.umbral_sombras(k)

    #
    @staticmethod
    def parte_umbral(f: FilaISO, umbral: float | None) -> float | None:
        """
        Qué parte del umbral (ver umbral_iso) es la textura/ruido de la Z2
        de un ISO: 1 = justo el umbral (None sin dato)
        """
        if (f.textura_ruido is None) or (not umbral):
            return None
        return f.textura_ruido / umbral

    #
    def nivel_textura_iso(self, f: FilaISO, k: dict,
                          umbral: float | None) -> int | None:
        """
        Cómo es la textura de la Z2 de un ISO, con el orden de
        KXL.T_TEXTURA_ISO: 0 se pierde (por debajo de C_TEXTURA_JUSTA del
        umbral), 1 justa (hasta el umbral), 2 se ve (None sin dato)
        """
        parte = self.parte_umbral(f, umbral)
        if parte is None:
            return None
        if parte >= 1:
            return 2
        return 1 if (parte >= k[KXL.C_TEXTURA_JUSTA]) else 0

    #
    @staticmethod
    def zona_sombras_iso(f: FilaISO, k: dict,
                         umbral: float | None) -> float | None:
        """
        Estimación de la zona desde la que hay textura en las sombras de un
        ISO (en zonas, sin redondear; None sin dato, math.inf si no llega
        nunca), solo con su Z-V y su Z2. Modelo del ruido de la tarjeta
        (en niveles): ruido² = lectura² + señal·x + (p·señal)², con la
        lectura del borde y x y p sacadas de los dos puntos; la textura
        del paño, la misma fracción de la señal que en la Z2. La zona es
        donde textura/ruido llega al umbral (ver umbral_iso)
        """
        datos = (f.nivel_zv, f.nivel_z2, f.ruido_zv, f.ruido_z2,
                 f.textura_z2)
        if (not umbral) or any(d is None for d in datos):
            return None
        s1, s2, n1, n2, t = datos                           # type: ignore
        if (s1 <= 0) or (s2 <= 0) or (s1 == s2) or (t <= 0):
            return None
        # --- La lectura del borde es por píxel: a escala de pantalla no
        #     vale, y el modelo se ajusta solo con los dos puntos
        lectura2 = 0.0 if f.es_pantalla else ((f.lectura or 0.0) ** 2)

        # --- Los dos puntos: ruido² − lectura² = señal·x + señal²·p²
        y1 = ((n1 * s1) ** 2) - lectura2
        y2 = ((n2 * s2) ** 2) - lectura2
        det = (s1 * (s2 ** 2)) - (s2 * (s1 ** 2))
        x = ((y1 * (s2 ** 2)) - (y2 * (s1 ** 2))) / det
        p2 = ((s1 * y2) - (s2 * y1)) / det
        #     Sin sentido físico (x o p² negativos): solo fotones, con
        #     el punto de la Z2 (el que manda en las sombras)
        if (x <= 0) or (p2 < 0):
            p2 = 0.0
            x = max(y2, 0.0) / s2
            if x <= 0:
                return None

        # --- Señal a la que textura/ruido llega al umbral: la raíz
        #     positiva de ((t/umbral)² − p²)·S² − x·S − lectura² = 0
        a = ((t / umbral) ** 2) - p2
        if a <= 0:
            return math.inf
        signal = (x + math.sqrt((x ** 2) + (4 * a * lectura2))) / (2 * a)
        return k[KXL.C_ZONA_ZV] + math.log(signal / s1,
                                           k[KXL.C_FACTOR_ZONA])

    #
    def sombras_iso(self, f: FilaISO, k: dict, umbral: float | None) -> str:
        """
        Desde qué zona colocar las sombras con textura en un ISO, en texto:
        la estimación de zona_sombras_iso al tercio más próximo, más
        C_MARGEN_SOMBRAS tercios (como la recomendada de la latitud), con
        «≈»; sin pasar por debajo de Z0. Por encima de la Z-V, «ninguna»
        ("" sin dato)
        """
        t = self.__textos
        zona = self.zona_sombras_iso(f, k, umbral)
        if zona is None:
            return ""
        if not math.isfinite(zona):
            return t[KXL.T_SOMBRAS_NINGUNA]

        # --- Al tercio más próximo (el medio, hacia arriba, como en
        #     limites_texturas) y el margen de la recomendada
        tercio = k[KXL.C_TERCIO_POR_ZONA]
        tercio_ev = (math.floor(((zona - k[KXL.C_ZONA_ZV]) * tercio) + 0.5)
                     + k[KXL.C_MARGEN_SOMBRAS])
        if tercio_ev > 0:
            return t[KXL.T_SOMBRAS_NINGUNA]
        tercio_ev = max(tercio_ev, -KS.TERCIOS_LADO)
        return t[KXL.T_SOMBRAS_ISO].format(zona=self.nombre_zona(tercio_ev))

    #
    def aprecia_iso(self, f: FilaISO, k: dict, umbral: float | None) -> str:
        """
        Cómo es la textura de la Z2 de un ISO, en texto: se ve, justa o se
        pierde (ver nivel_textura_iso; "" sin dato)
        """
        nivel = self.nivel_textura_iso(f, k, umbral)
        return ("" if (nivel is None)
                else self.__textos[KXL.T_TEXTURA_ISO[nivel]])

    #
    def exposicion_iso(self, f: FilaISO, k: dict) -> str:
        """
        Cómo sale la exposición de un ISO frente a la del ISO inicial, al
        tercio de zona: igual, o cuánto más clara u oscura ("" sin dato)
        """
        if f.desviacion is None:
            return ""
        tercios = round(f.desviacion * k[KXL.C_TERCIO_POR_ZONA])
        if tercios == 0:
            return self.__textos[KXL.T_EXPOSICION_IGUAL]
        entera, tercio = divmod(abs(tercios), k[KXL.C_TERCIO_POR_ZONA])
        cuanto = (f"{entera if entera else ''}"
                  f"{KXL.TERCIOS_EXCEL[tercio]}").strip()
        clave = (KXL.T_EXPOSICION_CLARA if (tercios > 0)
                 else KXL.T_EXPOSICION_OSCURA)
        return self.__textos[clave].format(cuanto=cuanto)

    #
    def tv_iso(self, f: FilaISO) -> str:
        """
        Tiempo de exposición de la ZV de un ISO de la secuencia, como lo
        marca la cámara (1/20 s); "" sin dato.
        """
        exp = next((e for e in self.__serie.expISO
                    if (e.iso is not None) and (round(e.iso) == f.iso)), None)
        if (exp is None) or (exp.tv is None):
            return ""
        return OECF.TextoTV(exp.tv)

    #
    def diafragma_iso(self) -> str:
        """
        Diafragma de la secuencia de ISO, si es el mismo en todas sus tomas
        (22); "" si cambia o no hay dato.
        """
        diafragmas = {e.f for e in self.__serie.expISO if e.f is not None}
        return OECF.TextoF(diafragmas.pop()) if (len(diafragmas) == 1) else ""

    #
    def senal_ruido_iso(self, ruido: float | None) -> str:
        """
        Señal/ruido de la tarjeta en una toma de la secuencia de ISO, desde
        su ruido (dispersión relativa), en número entero, o con un decimal
        si es menor de KXL.SENAL_RUIDO_DECIMAL (para que un 9,9 no salga
        como un 10 en rojo); "" sin dato.
        """
        if (ruido is None) or (ruido <= 0):
            return ""
        senal = 1 / ruido
        return self.numero_texto(
            senal, 1 if (senal < KXL.SENAL_RUIDO_DECIMAL) else 0)

    #
    @staticmethod
    def nivel_ruido_iso(ruido: float | None, k: dict) -> int | None:
        """
        Cómo es el ruido de una toma de la secuencia de ISO, con el orden
        de los colores del PDF (KPDF.SEMAFORO_ISO): 0 mal (señal/ruido por
        debajo de C_SNR_MINIMA), 1 justo (hasta C_SNR_EXCELENTE), 2 bien;
        None sin dato.
        """
        if (ruido is None) or (ruido <= 0):
            return None
        senal = 1 / ruido
        if senal < k[KXL.C_SNR_MINIMA]:
            return 0
        return 1 if (senal < k[KXL.C_SNR_EXCELENTE]) else 2

    #
    def zonas_canal(self, k: dict) -> dict[str, list]:
        """
        Por zona y canal, lo que calcula el bloque 2 de Cálculo y usan el
        1 y canales: el esperado (en zonas), el obtenido (zona
        equivalente), la desviación y si está recortado (los textos de
        C_TEXTO_RECORTADO y C_TEXTO_NO_RECORTADO; None sin toma).
        """
        t, d = self.__textos, self.__datos
        n = (2 * KS.TERCIOS_LADO) + 1
        medias = self.medias_zv()
        zonas = [z.nivelRGB if z else None for z in d.zonas]
        esperado = [k[KXL.C_ZONA_ZV] + ((i - KS.TERCIOS_LADO)
                    / k[KXL.C_TERCIO_POR_ZONA]) for i in range(n)]
        topes = self.topes()
        obtenido = [[(k[KXL.C_ZONA_ZV] + math.log(z[j] / medias[j],
                                                  k[KXL.C_FACTOR_ZONA]))
                     if (z and (z[j] > 0)) else None for z in zonas]
                    for j in range(KXL.CANALES)]
        dev = [[(o - e) if (o is not None) else None
                for o, e in zip(obtenido[j], esperado)]
               for j in range(KXL.CANALES)]
        recortado = [[None if (z is None) else (
            t[KXL.V_RECORTADO]
            if (z[j] >= (k[KXL.C_UMBRAL_RECORTE] * topes[j]))
            else t[KXL.V_NO_RECORTADO]) for z in zonas]
            for j in range(KXL.CANALES)]
        return {KXL.Z_ESPERADO: esperado, KXL.Z_OBTENIDO: obtenido,
                KXL.Z_DEV: dev, KXL.Z_RECORTADO: recortado}

    #
    def topes(self) -> list[float]:
        """ Máximo de cada canal en la serie (rojo, verde, azul). """
        zonas = [z.nivelRGB for z in self.__datos.zonas if z]
        return [max((z[j] for z in zonas), default=0.0)
                for j in range(KXL.CANALES)]

    #
    def canales(self, k: dict) -> list[dict[str, object]]:
        """
        Por canal (rojo, verde, azul), lo que da el bloque 1 de Cálculo:
        Z-V media, máximo, techo, suelo (C_RATIO_SR), rango, último punto
        lineal, primer punto recortado, suelos sugerido (C_SNR_MINIMA) y
        excelente (C_SNR_EXCELENTE) y la latitud sugerida (KRES.R_*). Lo que
        no se alcanza o falta, con el mismo texto o vacío que en el
        libro.
        """
        t = self.__textos
        medias, topes = self.medias_zv(), self.topes()
        por_zona = self.zonas_canal(k)
        esperado = por_zona[KXL.Z_ESPERADO]
        resultados = []
        for j in range(KXL.CANALES):
            techo = ((k[KXL.C_ZONA_ZV] + math.log(topes[j] / medias[j],
                                                  k[KXL.C_FACTOR_ZONA]))
                     if ((topes[j] > 0) and (medias[j] > 0)) else "")
            suelo = self.valor_suelo(KXL.C_RATIO_SR, j, k)
            lineales = [e for e, dvi, rci in zip(
                esperado, por_zona[KXL.Z_DEV][j],
                por_zona[KXL.Z_RECORTADO][j])
                if (dvi is not None)
                and (abs(dvi) <= k[KXL.C_TOLERANCIA_LINEAL])
                and (rci == t[KXL.V_NO_RECORTADO])]
            primeros = [e for e, rci in zip(esperado,
                                            por_zona[KXL.Z_RECORTADO][j])
                        if rci == t[KXL.V_RECORTADO]]
            sugerido = self.valor_suelo(KXL.C_SNR_MINIMA, j, k)
            resultados.append({
                KRES.R_MEDIA_ZV: medias[j], KRES.R_MAX: topes[j],
                KRES.R_TECHO: techo, KRES.R_SUELO: suelo,
                KRES.R_RANGO: ((techo - suelo) if (isinstance(techo, float)
                              and isinstance(suelo, float)) else ""),
                KRES.R_FIN_LINEAL: (max(lineales) if lineales
                                    else t[KXL.V_NINGUNO]),
                KRES.R_PRIMER_RECORTADO: (primeros[0] if primeros
                                          else t[KXL.V_NO_ALCANZADO]),
                KRES.R_SUELO_SUGERIDO: sugerido,
                KRES.R_SUELO_EXCELENTE: self.valor_suelo(KXL.C_SNR_EXCELENTE,
                                                         j, k),
                KRES.R_LATITUD: (self.latitud(max(lineales), sugerido, k)
                                 if lineales else t[KXL.V_NO_ALCANZADO])})
        return resultados

    #
    def resultados(self) -> dict:
        """
        Resultados del análisis para el JSON (los que lee FotoEstación,
        que no lleva el código de PyOECF): por canal (canales), la latitud de
        texturas, la curva zona a zona, las diferencias medias, la
        linealidad por tercio y las constantes que usó el análisis. Sin
        textos: lo que no es un número va como None, y en cada canal sus
        estados (KRES.EST_*) dicen por qué (no alcanzado, ninguno, sin
        dato).
        """
        k = self.valores_constantes()

        canales = {}
        for clave, canal in zip(KRES.CANALES_JSON, self.canales(k)):
            cifras: dict[str, object] = {
                nombre: self.numero_json(valor)
                for nombre, valor in canal.items()}
            cifras[KRES.J_ESTADOS] = {nombre: self.estado_json(canal[nombre])
                                      for nombre in KRES.ESTADOS_JSON}
            canales[clave] = cifras
        por_zona = self.zonas_canal(k)
        linealidad = []
        for i in range(len(por_zona[KXL.Z_ESPERADO])):
            tercio: dict[str, object] = {KRES.J_TERCIO: i - KS.TERCIOS_LADO}
            for j, clave in enumerate(KRES.CANALES_JSON):
                tercio[clave] = {
                    KRES.J_DESVIACION: self.numero_json(
                        por_zona[KXL.Z_DEV][j][i]),
                    KRES.J_RECORTADO: self.recortado_json(
                        por_zona[KXL.Z_RECORTADO][j][i])}
            linealidad.append(tercio)
        constantes = {clave: k[nombre]
                      for nombre, clave in KXL.CONSTANTES_JSON}
        limites = self.limites_texturas(k, self.texturas(k))
        sin_tela = isinstance(self.__datos.tela, str)
        texturas = None if sin_tela else {
            clave: dict(zip(KRES.TEXTURAS_JSON,
                            (self.numero_json(v) for v in valores)))
            for clave, valores in limites.items()}
        puntos = self.puntos_curva(k)
        curva = [{KRES.J_ZONA: p.nombre, KRES.J_TERCIO: p.tercio_ev,
                  KRES.J_ESPERADO: p.esperado, KRES.J_OBJETIVO: p.objetivo,
                  KRES.J_SENSOR: p.sensor, KRES.J_REVELADOR: p.revelador,
                  KRES.J_ENTRADA: p.entrada, KRES.J_SALIDA: p.salida,
                  KRES.J_PUNTO: (p.tercio_ev % k[KXL.C_TERCIO_POR_ZONA]) == 0}
                 for p in puntos]
        sensor = [abs(p.sensor - p.esperado) for p in puntos
                  if p.sensor is not None]
        revelador = [abs(p.revelador - p.objetivo) for p in puntos
                     if p.revelador is not None]
        medias = {KRES.J_SENSOR: self.media(sensor),
                  KRES.J_REVELADOR: self.media(revelador)}
        return {KRES.J_CANALES: canales, KRES.J_TEXTURAS: texturas,
                KRES.J_CURVA: curva, KRES.J_DIFERENCIAS: medias,
                KRES.J_LINEALIDAD: linealidad, KRES.J_CONSTANTES: constantes}

    #
    @staticmethod
    def media(valores: list[float]) -> float | None:
        """ Media de unos valores, o None si no hay ninguno. """
        return (sum(valores) / len(valores)) if valores else None

    #
    @staticmethod
    def numero_json(valor: object) -> float | None:
        """ Un resultado para el JSON: el número, o None si no lo es. """
        if isinstance(valor, (int, float)) and (not isinstance(valor, bool)):
            return float(valor) if math.isfinite(valor) else None
        return None

    #
    def estado_json(self, valor: object) -> str:
        """
        Estado de una cifra de los canales para el JSON (KRES.EST_*): ok si
        es un número; si no, noAlcanzado, ninguno o sinDato (sin curva o
        sin dato).
        """
        t = self.__textos
        if self.numero_json(valor) is not None:
            return KRES.EST_OK
        if valor == t[KXL.V_NO_ALCANZADO]:
            return KRES.EST_NO_ALCANZADO
        if valor == t[KXL.V_NINGUNO]:
            return KRES.EST_NINGUNO
        return KRES.EST_SIN_DATO

    #
    def recortado_json(self, valor: object) -> bool | None:
        """
        Si una zona está recortada, para el JSON: True, False o None sin
        toma.
        """
        t = self.__textos
        if valor == t[KXL.V_RECORTADO]:
            return True
        if valor == t[KXL.V_NO_RECORTADO]:
            return False
        return None

    #
    def puntos_curva(self, k: dict) -> list[PuntoCurva]:
        """
        La curva tonal en L*, zona a zona (de Z0 a ZX): lo que escribe el
        bloque 3 de Cálculo y dibuja el PDF. Esperado: un paso de
        luz por zona desde la ZV, hasta el blanco; objetivo: C_L_POR_ZONA por
        zona, el destino del revelado (la salida de la curva); sensor: el
        verde de la zona entre el de la ZV (media); revelador: el de Datos
        (leído o estimado).
        """
        medias = self.medias_zv()
        lzv = self.lab_a_luz(k[KXL.C_LZV], k)
        puntos = []
        for i, zona in enumerate(self.__datos.zonas):
            tercio_ev = i - KS.TERCIOS_LADO
            luz_esp = self.luz_esperada(tercio_ev, k)
            luz_sen = (min(1.0, lzv * zona.nivelRGB[1] / medias[1])
                       if (zona and (zona.nivelRGB[1] > 0)) else None)
            l_rev = self.__revelador[i]
            luz_rev = None if (l_rev is None) else self.lab_a_luz(l_rev, k)
            objetivo = k[KXL.C_L_POR_ZONA] * (
                k[KXL.C_ZONA_ZV] + (tercio_ev / k[KXL.C_TERCIO_POR_ZONA]))
            puntos.append(PuntoCurva(
                tercio_ev=tercio_ev,
                nombre=self.nombre_zona(tercio_ev),
                luz_esperada=luz_esp,
                esperado=self.luz_a_lab(luz_esp, k),
                objetivo=objetivo,
                luz_sensor=luz_sen,
                sensor=None if (luz_sen is None)
                else self.luz_a_lab(luz_sen, k),
                luz_revelador=luz_rev,
                revelador=l_rev,
                entrada=None if (luz_rev is None) else self.curva(luz_rev, k),
                salida=self.curva(self.lab_a_luz(objetivo, k), k)))
        return puntos

    #
    def medias_zv(self) -> list[float]:
        """ Media de las Z-V (la de la serie y las de control) por canal. """
        d = self.__datos
        zv = d.zonas[KS.TERCIOS_LADO]
        desviados = d.controlesDesviados
        valores = [v.nivelRGB for v in [zv] + list(d.control[:KXL.CONTROLES])
                   if (v is not None) and (v not in desviados)]
        return [(sum(v[j] for v in valores) / len(valores)) if valores else 0.0
                for j in range(KXL.CANALES)]

    #
    @staticmethod
    def con_nombre(texto: str) -> str:
        """
        El texto con los nombres de las constantes del libro puestos: cada
        hueco {nombre} (el de KXL.C_NOMBRE en minúsculas, sin «C_») se
        cambia por su nombre definido ({snr_minima} → el valor de
        KXL.C_SNR_MINIMA). Así cada nombre solo se escribe en KXL.
        """
        for atributo in dir(KXL):
            nombre = getattr(KXL, atributo)
            if atributo.startswith("C_") and isinstance(nombre, str):
                texto = texto.replace(f"{{{atributo[2:].lower()}}}", nombre)
        return texto

    #
    @staticmethod
    def con_nombres(textos: dict[str, str]) -> dict[str, str]:
        """ Cada texto con los nombres de las constantes puestos (ver
            con_nombre). """
        return {clave: Excel.con_nombre(texto)
                for clave, texto in textos.items()}

    #
    def valores_constantes(self) -> dict[str, Any]:
        """
        Valor de cada constante del libro: {nombre: valor} (números y
        claves de texto).
        """
        k: dict[str, Any] = {nombre: valor
                             for nombre, valor, _ in KXL.CONSTANTES}
        k[KXL.C_LUZ_POR_TERCIO] = (k[KXL.C_FACTOR_ZONA]
                                   ** (1 / k[KXL.C_TERCIO_POR_ZONA]))
        k[KXL.C_LUZ_ZV] = self.lab_a_luz(k[KXL.C_LZV], k)
        return k

    #
    def texturas(self, k: dict) -> dict[str, list]:
        """
        Latitud de texturas del verde, por zona (de Z0 a ZX): esperado,
        textura del paño (su dispersión sin el ruido de la tarjeta),
        textura/ruido, textura conservada (frente a la de la ZV), paño
        recortado, contraste de la trama del paño en las exportaciones del
        revelador (en L*) y su fracción del de la ZV, y si cumple cada
        criterio (sombras: fracción del contraste de C_CONTRASTE_SOMBRAS en
        adelante hasta la ZV; luces: desde la ZV, textura conservada de
        C_TEXTURA_CONSERVADA y paño recortado de C_TELA_RECORTADO_MAX como
        mucho). None: sin dato o fuera de su lado.
        """
        n = (2 * KS.TERCIOS_LADO) + 1
        zv = KS.TERCIOS_LADO
        verde = 1
        esperado = [k[KXL.C_ZONA_ZV] + ((i - zv) / k[KXL.C_TERCIO_POR_ZONA])
                    for i in range(n)]
        textura, ruido, recortado = [], [], []
        for z in self.__datos.zonas:
            tela, tarjeta = self.disp_textura(z)
            if ((tela is None) or (tarjeta is None)
                    or (not math.isfinite(tarjeta))
                    or (not math.isfinite(tela))):
                textura.append(None)
                ruido.append(None)
            else:
                tx = calcular_textura(tela, tarjeta)
                textura.append(tx)
                ruido.append((tx / tarjeta) if (tarjeta > 0) else None)
            recorte = z.telaRecortadoRGB if z else None
            recortado.append(recorte[verde] if (recorte
                             and math.isfinite(recorte[verde])) else None)
        base = textura[zv]
        conservada = [(tx / base) if ((tx is not None) and base) else None
                      for tx in textura]

        # --- Contraste de la trama del paño en las exportaciones y su
        #     fracción del de la ZV (Tony, 2026-11-13)
        contraste = self.contrastes()
        contraste_zv = contraste[zv]
        fraccion = [(c / contraste_zv) if ((c is not None) and contraste_zv)
                    else None for c in contraste]

        # --- Sombras, de la ZV hacia abajo; luces, de la ZV hacia arriba.
        #     Un tercio sin dato no corta la cadena: deja pasar lo que
        #     viene del lado de la ZV
        sombras: list = [None] * n
        luces: list = [None] * n
        sin_recorte: list = [None] * n
        umbral = k[KXL.C_CONTRASTE_SOMBRAS]
        for i in range(zv, -1, -1):
            sigue = True if (i == zv) else sombras[i + 1]
            sombras[i] = (sigue if (fraccion[i] is None)
                          else ((fraccion[i] >= umbral) and sigue))
        for i in range(zv, n):
            luz = True if (i == zv) else luces[i - 1]
            corte = True if (i == zv) else sin_recorte[i - 1]
            # --- Apreciable: conserva su textura y no pasa del recorte
            #     de C_TELA_RECORTADO_APRECIABLE (sin dato de recorte,
            #     cuenta como 0, igual que N() en el libro)
            recorte_i = recortado[i] if (recortado[i] is not None) else 0.0
            luces[i] = (luz if (conservada[i] is None) else
                        ((conservada[i] >= k[KXL.C_TEXTURA_CONSERVADA])
                         and (recorte_i
                              <= k[KXL.C_TELA_RECORTADO_APRECIABLE])
                         and luz))
            sin_recorte[i] = (
                corte if (recortado[i] is None) else
                ((recortado[i] <= k[KXL.C_TELA_RECORTADO_MAX]) and corte))
        return {KXL.T_CAB_ESPERADO: esperado, KXL.T_CAB_TEXTURA: textura,
                KXL.T_CAB_TEXTURA_RUIDO: ruido,
                KXL.T_CAB_CONSERVADA: conservada,
                KXL.T_CAB_TELA_RECORTADO: recortado,
                KXL.T_CAB_CUMPLE_SOMBRAS: sombras,
                KXL.T_CAB_CUMPLE_LUCES: luces,
                KXL.T_CAB_SIN_RECORTE: sin_recorte,
                KXL.T_CAB_CONTRASTE: contraste,
                KXL.T_CAB_CONTRASTE_ZV: fraccion}

    #
    def titulo_ruido_color(self) -> str:
        """
        Título del ruido aceptable por color (Análisis y PDF), con el ISO
        de la serie, al que se refiere (Tony, 2026-11-13); sin ISO leído,
        sin él
        """
        t, iso = self.__textos, self.__datos.iso
        if iso is None:
            return t[KXL.T_RUIDO_COLOR]
        return t[KXL.T_RUIDO_COLOR_ISO].format(iso=texto_iso(iso))

    #
    def contrastes(self) -> list[float | None]:
        """
        Contraste de la trama del paño en las exportaciones del revelador,
        por zona (de Z0 a ZX, en L*): None sin él (sin paño, sin
        exportación o antes de la segunda fase)
        """
        n = (2 * KS.TERCIOS_LADO) + 1
        medidos = self.__datos.contraste
        if len(medidos) != n:
            return [None] * n
        return [float(c) if math.isfinite(c) else None for c in medidos]

    #
    @staticmethod
    def disp_textura(z: ZonaMedida | None) -> tuple[float | None,
                                                    float | None]:
        """
        Dispersión del paño y de la tarjeta en verde con las que se mide
        la textura de una toma para la latitud de texturas: por píxel
        (Tony, 2026-11-13: a escala de pantalla, TD daba «desde Z0⅓»;
        por píxel, Z2 apreciable y Z2⅓ recomendada, lo que ve Tony). La
        escala de pantalla queda solo para la secuencia de ISO (ver
        zona_sombras_iso y oecfCalc.review). (None, None) sin toma; el
        paño, None si no hay
        """
        verde = 1
        if z is None:
            return None, None
        tela = z.telaDispRGB
        return (None if tela is None else tela[verde]), z.dispRGB[verde]

    #
    @staticmethod
    def umbral_sombras(k: dict) -> float:
        """
        Textura/ruido desde la que se aprecia la textura en las sombras:
        C_ROSE_TEXTURA (por píxel en la latitud de texturas; a escala de
        pantalla en la secuencia de ISO)
        """
        return k[KXL.C_ROSE_TEXTURA]

    #
    def limites_texturas(self, k: dict, por_zona: dict[str, list]
                         ) -> dict[str, Tramo]:
        """
        Límites de la latitud de texturas (en zonas; si no se alcanzan, el
        texto de C_TEXTO_NO_ALCANZADO): sombras recomendadas (la primera
        zona cuyo contraste de la trama del paño llega a
        C_CONTRASTE_SOMBRAS del de la ZV sin volver a bajar hasta ella;
        antes de la segunda fase, sin ese contraste, el texto de
        C_TEXTO_SIN_REVELADO) y apreciables (C_MARGEN_SOMBRAS tercios más
        abajo), luces apreciables (la última con la textura conservada) y
        recomendadas (la última sin pasar de C_TELA_RECORTADO_MAX, sin
        pasar de la apreciable) y las dos latitudes (sin revelado, su
        texto). Solo cuentan los tercios con dato (Tony, 2026-11-13: las
        sombras, del contraste en las exportaciones, no de la
        textura/ruido de los RAW).
        """
        no = self.__textos[KXL.V_NO_ALCANZADO]
        sin_revelado = self.__textos[KXL.V_SIN_REVELADO]
        tercio = k[KXL.C_TERCIO_POR_ZONA]
        es = por_zona[KXL.T_CAB_ESPERADO]
        fraccion = por_zona[KXL.T_CAB_CONTRASTE_ZV]
        cumple = por_zona[KXL.T_CAB_CUMPLE_SOMBRAS]

        # --- Sin paño, no alcanzado; con paño y sin ningún contraste en
        #     las sombras (antes de la segunda fase), sin revelado
        if isinstance(self.__datos.tela, str):
            sombra_rec = no
        elif all(f is None for f in fraccion[:KS.TERCIOS_LADO + 1]):
            sombra_rec = sin_revelado
        else:
            primera = next((i for i, c in enumerate(cumple)
                            if c and (fraccion[i] is not None)), None)
            sombra_rec = no if (primera is None) else es[primera]
        sombra = ((sombra_rec - (k[KXL.C_MARGEN_SOMBRAS] / tercio))
                  if isinstance(sombra_rec, float) else sombra_rec)
        luces = [e for e, c, v in zip(es, por_zona[KXL.T_CAB_CUMPLE_LUCES],
                                      por_zona[KXL.T_CAB_CONSERVADA])
                 if c and (v is not None)]
        luz = max(luces) if luces else no
        cortes = [e for e, c, v in zip(es, por_zona[KXL.T_CAB_SIN_RECORTE],
                                       por_zona[KXL.T_CAB_TELA_RECORTADO])
                  if c and (v is not None)]
        luz_rec = ((min(luz, max(cortes)) if isinstance(luz, float)
                    else max(cortes)) if cortes else no)

        # --- Las latitudes: sin revelado, su texto
        latitud = (sin_revelado if (sombra == sin_revelado)
                   else self.latitud(luz, sombra, k))
        latitud_rec = (sin_revelado if (sombra_rec == sin_revelado)
                       else self.latitud(luz_rec, sombra_rec, k))
        return {KXL.T_APRECIABLE: (sombra, luz, latitud),
                KXL.T_RECOMENDADA: (sombra_rec, luz_rec, latitud_rec)}

    #
    def latitud(self, alto: object, bajo: object,
                k: dict) -> float | str:
        """
        Latitud entre dos zonas, contando las dos puntas (de Z3 a Z8, 6
        zonas): alto − bajo + C_ANCHO_ZONA, si los dos son números; si no,
        C_TEXTO_NO_ALCANZADO.
        """
        if isinstance(alto, float) and isinstance(bajo, float):
            return alto - bajo + k[KXL.C_ANCHO_ZONA]
        return self.__textos[KXL.V_NO_ALCANZADO]

    #
    def numero_texto(self, valor: float, decimales: int) -> str:
        """ Número como texto, con el separador decimal del idioma. """
        return f"{valor:.{decimales}f}".replace(
            ".", self.__textos[KXL.T_SEPARADOR_DECIMAL])

    #
    def lineas_pixeles(self) -> list[str]:
        """
        Las líneas de los píxeles defectuosos, para Datos, Análisis y el
        PDF: los calientes y los muertos (cuántos y por megapíxel; si no
        hay, «ninguno») o, sin tapadas, que no se pueden contar los
        calientes. Sin ninguno de los dos, una sola línea: no hay píxeles
        defectuosos. Vacío si no se contaron píxeles.
        """
        t, pixeles = self.__textos, self.__datos.pixeles
        if pixeles is None:
            return []
        if (pixeles.calientes == 0) and (pixeles.muertos == 0):
            return [t[KXL.T_PIXELES_NINGUNO]]
        lineas = []
        if (pixeles.calientes is None) or (pixeles.calientesMpx is None):
            lineas.append(t[KXL.T_PIXELES_SIN_TAPADAS])
        elif pixeles.calientes == 0:
            lineas.append(t[KXL.T_PIXELES_SIN_CALIENTES])
        else:
            lineas.append(t[KXL.T_PIXELES_CALIENTES].format(
                n=pixeles.calientes, por_mpx=self.numero_texto(
                    pixeles.calientesMpx, KXL.DECIMALES_MPX)))
        if pixeles.muertos == 0:
            lineas.append(t[KXL.T_PIXELES_SIN_MUERTOS])
        elif ((pixeles.muertos is not None)
              and (pixeles.muertosMpx is not None)):
            lineas.append(t[KXL.T_PIXELES_MUERTOS].format(
                n=pixeles.muertos, por_mpx=self.numero_texto(
                    pixeles.muertosMpx, KXL.DECIMALES_MPX)))
        return lineas

    #
    def filas_pixeles(self) -> list[tuple[str, str, str, bool | None]]:
        """
        Las filas de la tabla de píxeles defectuosos del PDF, calientes y
        muertos: su rótulo, cuántos, cuántos por megapíxel y si no hay
        ninguno (True), hay (False) o no se pudieron contar (None, con
        «—» en lugar de los números). Vacía si no se contaron píxeles.
        """
        t, pixeles = self.__textos, self.__datos.pixeles
        if pixeles is None:
            return []
        filas = []
        for rotulo, n, mpx in (
                (t[KXL.T_PIXELES_TIPO_CALIENTES], pixeles.calientes,
                 pixeles.calientesMpx),
                (t[KXL.T_PIXELES_TIPO_MUERTOS], pixeles.muertos,
                 pixeles.muertosMpx)):
            if (n is None) or (mpx is None):
                filas.append((rotulo, KXL.SIN_NUMERO, KXL.SIN_NUMERO, None))
            else:
                filas.append((rotulo, str(n), self.numero_texto(
                    mpx, KXL.DECIMALES_MPX), n == 0))
        return filas

    #
    def suelos_ruido(self, k: dict) -> list[float | str]:
        """
        Por canal (rojo, verde y azul), la zona desde la que el ruido es
        aceptable: el suelo sugerido del bloque 1 de Cálculo (C_SNR_MINIMA),
        en zonas. No alcanzado, el texto de C_TEXTO_NO_ALCANZADO; "" sin
        dato.
        """
        return [canal[KRES.R_SUELO_SUGERIDO] for canal in self.canales(k)]

    #
    @staticmethod
    def __tercio_ruido(suelo: float) -> int:
        """
        Primer tercio (tercioEV) con ruido aceptable para este suelo, en
        zonas: a partir de él, todos hacia las luces. Por debajo de
        -KS.TERCIOS_LADO es todo el rango; por encima de KS.TERCIOS_LADO,
        ninguno.
        """
        return (math.ceil((suelo * KP.TERCIOS) - KXL.MARGEN_TERCIO)
                - KS.TERCIOS_LADO)

    #
    def frase_ruido(self, canal: str, suelo: float | str) -> str:
        """
        Frase del ruido aceptable de un canal, con su suelo: en todo el
        rango, desde su tercio o en ninguna zona ("" sin dato).
        """
        t = self.__textos
        if isinstance(suelo, float):
            if suelo <= 0:
                return t[KXL.T_RUIDO_COLOR_TODO].format(canal=canal)
            tercio_ev = self.__tercio_ruido(suelo)
            if tercio_ev <= KS.TERCIOS_LADO:
                return t[KXL.T_RUIDO_COLOR_DESDE].format(
                    canal=canal, zona=self.nombre_zona(tercio_ev))
        if suelo:
            return t[KXL.T_RUIDO_COLOR_NUNCA].format(canal=canal)
        return ""

    #
    def zona_ruido(self, suelo: float | str) -> tuple[str, int | None]:
        """
        Zona desde la que el ruido de un canal es aceptable, con su suelo,
        para la tabla del PDF, y su estado (KXL.RUIDO_*): la primera del
        rango si lo es en todo él, una zona o «ninguna zona». ("", None)
        sin dato.
        """
        if isinstance(suelo, float):
            tercio_ev = self.__tercio_ruido(suelo)
            if tercio_ev <= -KS.TERCIOS_LADO:
                return self.nombre_zona(-KS.TERCIOS_LADO), KXL.RUIDO_TODO
            if tercio_ev <= KS.TERCIOS_LADO:
                return self.nombre_zona(tercio_ev), KXL.RUIDO_DESDE
        if suelo:
            return (self.__textos[KXL.T_RUIDO_COLOR_NINGUNA],
                    KXL.RUIDO_NINGUNO)
        return "", None

    #
    def frases_ruido(self, k: dict) -> list[str]:
        """
        Las frases del ruido aceptable de rojo, verde y azul (las que
        tienen dato), para Análisis y el PDF.
        """
        t = self.__textos
        frases = (self.frase_ruido(t[clave], suelo) for clave, suelo
                  in zip(KXL.T_CANALES, self.suelos_ruido(k)))
        return [frase for frase in frases if frase]

    #
    def suelo_snr(self, snr: str, j: int, zv: str) -> str:
        """
        Suelo de un canal (j: rojo, verde, azul), en zonas: donde la
        señal/ruido, normalizada a C_MPX_REFERENCIA, llega a la constante
        snr, según la curva de transferencia de Datos (la raíz positiva
        de (1 − T²·p²)·S² − (T²/g)·S − T²·l² = 0, con T la señal/ruido de
        un píxel). zv: la celda de la Z-V media del canal. La fórmula; su
        resultado, valor_suelo.
        """
        f = self.__filas
        c = KXL.COLUMNA_INICIO + KXL.COL_VALORES + j
        lectura, ganancia, proporcional = (
            self.ref(KXL.T_HOJA_DATOS, f[clave], c, True, True)
            for clave in (KXL.F_LECTURA, KXL.F_GANANCIA, KXL.F_PROPORCIONAL))
        mpx = self.ref(KXL.T_HOJA_DATOS, f[KXL.F_MPX],
                       KXL.COLUMNA_INICIO + KXL.COL_VALORES, True, True)
        t2 = f"({snr}^2*{KXL.C_MPX_REFERENCIA}/{mpx})"
        a = f"(1-{t2}*N({proporcional})^2)"
        b = f"({t2}/{ganancia})"
        signal = (f"(({b}+SQRT({b}^2+4*{a}*{t2}*N({lectura})^2))"
                  f"/(2*{a}))")
        return (f'=IF(AND(N({ganancia})>0,N({zv})>0),IF({a}>0,'
                f'{KXL.C_ZONA_ZV}+LOG({signal}/{zv},{KXL.C_FACTOR_ZONA}),'
                f'{KXL.C_TEXTO_NO_ALCANZADO}),"")')

    #
    def valor_suelo(self, snr: str, j: int, k: dict) -> float | str:
        """
        Suelo de un canal (j: rojo, verde, azul), en zonas, como el de
        suelo_snr: no alcanzado si la parte proporcional lo impide; ""
        sin curva.
        """
        d = self.__datos
        curvas, medias = d.transferenciaRGB, self.medias_zv()
        if (not curvas) or (medias[j] <= 0):
            return ""
        escala = escala_mpx(d.alto, d.ancho, k[KXL.C_MPX_REFERENCIA])
        signal_suelo = signal_para_snr(curvas[j], k[snr] / escala)
        if signal_suelo is None:
            return self.__textos[KXL.V_NO_ALCANZADO]
        return k[KXL.C_ZONA_ZV] + math.log(signal_suelo / medias[j],
                                           k[KXL.C_FACTOR_ZONA])

    #
    def luz_esperada(self, tercio_ev: int, k: dict) -> float:
        """
        Luz esperada de una zona: un paso de luz por zona desde la ZV
        (la de L* C_LZV), hasta el blanco de pantalla.
        """
        lzv = self.lab_a_luz(k[KXL.C_LZV], k)
        return min(1.0, lzv * (k[KXL.C_FACTOR_ZONA] ** (
            (tercio_ev / k[KXL.C_TERCIO_POR_ZONA]))))

    #
    def revelador_medido(self) -> list[float | None]:
        """
        L* del revelador medido en las TIFF, por zona (None: sin medir);
        todo None si aún no se midieron.
        """
        n = (2 * KS.TERCIOS_LADO) + 1
        medido = list(self.__datos.revelador or ((None,) * n))
        return [None if ((v is None) or math.isnan(v)) else v for v in medido]

    #
    def revelador_estimado(self) -> list[float | None]:
        """
        L* del revelador por zona, como sale en Datos: el medido y, en un
        tercio sin él, el estimado. La diferencia con el esperado (L*
        medido menos esperado) de las dos zonas enteras vecinas se
        reparte en recta y se suma al esperado del tercio, sin salirse de
        los L* de esas dos zonas (cerca del blanco, el esperado se
        recorta a 100 y lo sacaría). Si falta una de las dos, sin dato
        (None).
        """
        k = self.valores_constantes()
        por_zona = k[KXL.C_TERCIO_POR_ZONA]
        medido = self.revelador_medido()
        esperado = [self.luz_a_lab(self.luz_esperada(
            i - KS.TERCIOS_LADO, k), k) for i in range(len(medido))]
        estimado = list(medido)
        for i, valor in enumerate(medido):
            tercio = (i - KS.TERCIOS_LADO) % por_zona
            if (valor is not None) or (tercio == 0):
                continue
            antes, tras = i - tercio, i - tercio + por_zona
            if (medido[antes] is None) or (medido[tras] is None):
                continue
            dif_antes = medido[antes] - esperado[antes]
            dif_tras = medido[tras] - esperado[tras]
            recta = (esperado[i] + dif_antes + ((dif_tras - dif_antes)
                     * tercio / por_zona))
            estimado[i] = sorted((medido[antes], medido[tras], recta))[1]
        return estimado

    #
    @staticmethod
    def luz_a_lab(luz: float, k: dict) -> float:
        """ L* de una luminancia relativa (CIELAB), como en el libro. """
        if luz > k[KXL.C_LAB_UMBRAL]:
            return ((k[KXL.C_LAB_ESCALA] * (luz ** (1 / 3)))
                    - k[KXL.C_LAB_DESPLAZA])
        return k[KXL.C_LAB_PENDIENTE] * luz

    #
    @staticmethod
    def lab_a_luz(lab: float, k: dict) -> float:
        """ Luminancia relativa de un L* (inversa de CIELAB). """
        if lab > (k[KXL.C_LAB_UMBRAL] * k[KXL.C_LAB_PENDIENTE]):
            return ((lab + k[KXL.C_LAB_DESPLAZA]) / k[KXL.C_LAB_ESCALA]) ** 3
        return lab / k[KXL.C_LAB_PENDIENTE]

    #
    @staticmethod
    def curva(luz: float, k: dict) -> int:
        """ Valor de 0 a 255 de la curva de Lightroom (sRGB) de una luz. """
        if luz <= k[KXL.C_SRGB_UMBRAL]:
            srgb = k[KXL.C_SRGB_PENDIENTE] * luz
        else:
            srgb = ((k[KXL.C_SRGB_ESCALA] * (luz ** (1 / k[KXL.C_SRGB_GAMMA])))
                    - k[KXL.C_SRGB_DESPLAZA])
        return round(k[KXL.C_ESCALA_CURVA] * srgb)

    #
    @staticmethod
    def formula_lab(luz: str) -> str:
        """ Fórmula del L* de la luz de esta celda. """
        return (f"IF({luz}>{KXL.C_LAB_UMBRAL},{KXL.C_LAB_ESCALA}*{luz}^(1/3)"
                f"-{KXL.C_LAB_DESPLAZA},{KXL.C_LAB_PENDIENTE}*{luz})")

    #
    @staticmethod
    def formula_luz(lab: str) -> str:
        """ Fórmula de la luz del L* de esta celda (inversa de CIELAB). """
        return (f"IF({lab}>{KXL.C_LAB_UMBRAL}*{KXL.C_LAB_PENDIENTE},"
                f"(({lab}+{KXL.C_LAB_DESPLAZA})/{KXL.C_LAB_ESCALA})^3,"
                f"{lab}/{KXL.C_LAB_PENDIENTE})")

    #
    @staticmethod
    def formula_luz_curva(valor: str) -> str:
        """
        Fórmula de la luz de un valor de 0 a 255 de la curva de esta celda
        (inversa de sRGB).
        """
        v = f"({valor}/{KXL.C_ESCALA_CURVA})"
        return (f"IF({v}<={KXL.C_SRGB_UMBRAL}*{KXL.C_SRGB_PENDIENTE},"
                f"{v}/{KXL.C_SRGB_PENDIENTE},"
                f"(({v}+{KXL.C_SRGB_DESPLAZA})/{KXL.C_SRGB_ESCALA})"
                f"^{KXL.C_SRGB_GAMMA})")

    #
    @staticmethod
    def formula_curva(luz: str) -> str:
        """ Fórmula del valor de 0 a 255 de la curva de la luz de la celda. """
        return (f"ROUND({KXL.C_ESCALA_CURVA}*IF({luz}<={KXL.C_SRGB_UMBRAL},"
                f"{KXL.C_SRGB_PENDIENTE}*{luz},{KXL.C_SRGB_ESCALA}*{luz}^(1/"
                f"{KXL.C_SRGB_GAMMA})-{KXL.C_SRGB_DESPLAZA}),0)")

    #
    def ref(self, clave_hoja: str, fila: int, col: int,
            fila_fija: bool = False, col_fija: bool = False) -> str:
        """ Referencia a una celda de otra hoja: 'Datos'!F8. """
        return (f"'{self.__textos[clave_hoja]}'!"
                f"{xl_rowcol_to_cell(fila, col, fila_fija, col_fija)}")

    #
    def valor(self, hoja: Worksheet, fila: int, col: int) -> object:
        """
        Resultado ya escrito de una celda de esta hoja (para la réplica),
        o "" si no lo hay.
        """
        celda = hoja.table.get(fila, {}).get(col)
        return getattr(celda, "value", "") if (celda is not None) else ""

    #
    @staticmethod
    def en_blanco(valor: object) -> object:
        """ Resultado de una fórmula que da "" si no hay dato (None). """
        return "" if (valor is None) else valor

    #
    def si_no(self, valor: bool) -> str:
        """ El texto «Sí» o «No» de un dato, en el idioma del libro. """
        return self.__textos[KXL.T_SI if valor else KXL.T_NO]

    # endregion Métodos públicos

    #
    # --- Piezas comunes de las hojas
    #
    # region Piezas comunes

    #
    def marco(self, hoja: Worksheet,
              tarjetas: tuple[tuple[int, tuple[float | None, ...]], ...],
              anillo: str = KXL.ANILLO, ancho_anillo: float = KXL.ANCHO_ANILLO,
              ancho_relleno: float = KXL.ANCHO_RELLENO,
              alto: float | None = None) -> None:
        """
        Marco «tarjeta» de una hoja: una o varias tarjetas, una al lado de
        la otra, cada una (última fila de su contenido, anchos de sus
        columnas; None: oculta). La primera empieza en C3 y las demás,
        tras relleno, anillo y relleno (KXL.ENTRE_TARJETAS). Anillo gris
        alrededor y entre ellas; cada tarjeta, con borde medio y relleno.
        Oculta las columnas de la derecha y las filas de debajo;
        cuadrícula oculta; impresión apaisada, de una página de ancho.
        alto: el de las filas (None: el de Excel).
        """
        primera_fila = KXL.FILA_INICIO - 1
        fila_anillo = max(ultima for ultima, _ in tarjetas) + 2

        # --- Anchos: anillo y, por tarjeta, relleno, contenido, relleno
        #     y anillo. Cada tarjeta: (primera columna, columna de cierre,
        #     fila de cierre)
        hoja.set_column(0, 0, ancho_anillo)
        cajas = []
        col_contenido = KXL.COLUMNA_INICIO
        for ultima_fila, anchos in tarjetas:
            primera_col = col_contenido - 1
            col_cierre = col_contenido + len(anchos)
            hoja.set_column(primera_col, primera_col, ancho_relleno)
            for i, ancho in enumerate(anchos):
                c = col_contenido + i
                if ancho is None:
                    hoja.set_column(c, c, None, None, {"hidden": True})
                else:
                    hoja.set_column(c, c, ancho)
            hoja.set_column(col_cierre, col_cierre, ancho_relleno)
            hoja.set_column(col_cierre + 1, col_cierre + 1, ancho_anillo)
            cajas.append((primera_col, col_cierre, ultima_fila + 1))
            col_contenido += len(anchos) + KXL.ENTRE_TARJETAS
        col_anillo = cajas[-1][1] + 1
        hoja.set_column(col_anillo + 1, KXL.ULTIMA_COLUMNA_EXCEL, None,
                        None, {"hidden": True})

        # --- Anillo: todo lo que queda fuera de las tarjetas
        gris = self.formato(bg_color=anillo, pattern=1)
        for f in range(fila_anillo + 1):
            for c in range(col_anillo + 1):
                if not any((desde <= c <= hasta)
                           and (primera_fila <= f <= cierre)
                           for desde, hasta, cierre in cajas):
                    hoja.write_blank(f, c, None, gris)

        # --- Cada tarjeta: borde medio por fuera de su relleno
        for desde, hasta, cierre in cajas:
            for c in range(desde, hasta + 1):
                for f, lado in ((primera_fila, "top"), (cierre, "bottom")):
                    bordes = {lado: KXL.MEDIO}
                    if c == desde:
                        bordes["left"] = KXL.MEDIO
                    if c == hasta:
                        bordes["right"] = KXL.MEDIO
                    hoja.write_blank(f, c, None, self.formato(**bordes))
            for f in range(primera_fila + 1, cierre):
                hoja.write_blank(f, desde, None,
                                 self.formato(left=KXL.MEDIO))
                hoja.write_blank(f, hasta, None,
                                 self.formato(right=KXL.MEDIO))

        hoja.set_default_row(alto, hide_unused_rows=True)
        hoja.hide_gridlines(2)
        hoja.set_landscape()
        hoja.fit_to_pages(1, 0)

    #
    @staticmethod
    def columna_derecha() -> int:
        """ Primera columna de la tarjeta derecha de Análisis. """
        return (KXL.COLUMNA_INICIO + len(KXL.ANCHOS_RESUMEN)
                + KXL.ENTRE_TARJETAS)

    #
    def fmt_resumen(self, letra: int = KXL.LETRA_RESUMEN,
                    **mas: object) -> Format:
        """ Formato de Análisis: su fuente, en este tamaño. """
        return self.formato(font_name=KXL.FUENTE_RESUMEN, font_size=letra,
                            **mas)

    #
    def fondo_resumen(self, letra: int = KXL.LETRA_RESUMEN,
                      **mas: object) -> Format:
        """
        Formato de Análisis en blanco y negrita sobre el color de las
        cabeceras.
        """
        return self.fmt_resumen(letra, bold=True,
                                font_color=KXL.CABECERA_TEXTO,
                                bg_color=KXL.CABECERA_FONDO, pattern=1,
                                **mas)

    #
    def barra_resumen(self, hoja: Worksheet, fila: int, col: int,
                      ultima: int, texto: str) -> None:
        """ Barra de una sección de Análisis, de col a ultima. """
        hoja.merge_range(fila, col, fila, ultima, texto,
                         self.fondo_resumen(align="center",
                                            valign="vcenter"))

    #
    def cabecera_tarjeta(self, hoja: Worksheet, fila: int, col: int,
                         columnas: tuple[tuple[str, int], ...],
                         filas: int) -> int:
        """
        Cabecera de una tabla de Análisis desde col: cada (texto,
        columnas que ocupa), en filas filas combinadas. Devuelve su
        última fila.
        """
        formato = self.cabecera_resumen()
        abajo = fila + filas - 1
        for texto, ancho in columnas:
            if (ancho > 1) or (filas > 1):
                hoja.merge_range(fila, col, abajo, col + ancho - 1, texto,
                                 formato)
            else:
                hoja.write(fila, col, texto, formato)
            col += ancho
        return abajo

    #
    def nota_tarjeta(self, hoja: Worksheet, fila: int, col: int,
                     ultima: int, texto: str,
                     anchos: tuple[float, ...], formato: Format,
                     formula: str | None = None,
                     medida: str | None = None) -> int:
        """
        Nota de Análisis de col a ultima, en las filas de la rejilla que
        piden sus líneas (las de medida, si se da: el texto más largo que
        puede salir). Con fórmula, la escribe con texto como resultado.
        Devuelve su última fila.
        """
        abajo = fila + self.filas_texto(medida or texto, sum(anchos),
                                        KXL.ALTO_LINEA_NOTA) - 1
        hoja.merge_range(fila, col, abajo, ultima,
                         "" if formula else texto, formato)
        if formula is not None:
            self.formula(hoja, fila, col, formula, formato, texto)
        return abajo

    #
    def filas_texto(self, texto: str, ancho: float, alto_linea: float) -> int:
        """
        Filas de la rejilla de Análisis que ocupa un texto en este ancho,
        con líneas de este alto.
        """
        return max(1, math.ceil(self.lineas(texto, ancho) * alto_linea
                                / KXL.ALTO_REJILLA))

    #
    def nota_resumen(self, color: str) -> Format:
        """ Formato de una nota de Análisis, en su color. """
        return self.fmt_resumen(KXL.LETRA_RESUMEN_NOTA, font_color=color,
                                text_wrap=True, align="left", valign="top")

    #
    def cabecera_resumen(self) -> Format:
        """ Formato de la cabecera de una tabla de Análisis. """
        return self.fondo_resumen(KXL.LETRA_RESUMEN_NOTA, text_wrap=True,
                                  align="center", valign="vcenter",
                                  border=KXL.FINO)

    #
    def celda_resumen(self, banda: bool, alineado: str,
                      numero: str | None = None, **mas: object) -> Format:
        """
        Formato de una celda de tabla de Análisis: fila alterna (con
        fondo), alineación y formato de número.
        """
        propiedades: dict = dict(align=alineado, valign="vcenter",
                                 border=KXL.FINO,
                                 border_color=KXL.BORDE_TABLA, **mas)
        if banda:
            propiedades.update(bg_color=KXL.BANDA, pattern=1)
        if numero:
            propiedades["num_format"] = numero
        return self.fmt_resumen(KXL.LETRA_RESUMEN_TABLA, **propiedades)

    #
    def fila_serie(self, hoja: Worksheet, fila: int, col: int,
                   tercio_ev: int, toma: ZonaMedida | None,
                   banda: bool) -> None:
        """
        Fila de una toma en Datos: zona y tercios (literales), archivo,
        valor y dispersión de cada canal (datos). Sin toma, los datos en
        blanco, con su formato; un valor no finito (la dispersión de una
        toma sin medir aún: infinita), también en blanco.
        """
        self.zona_y_tercios(hoja, fila, col, tercio_ev, banda)
        dato = self.celda(KXL.COLOR_DATO, banda, "center")
        archivo = col + KXL.COL_VALORES - 1
        if toma is None:
            for c in range(archivo, archivo + 1 + (2 * KXL.CANALES)):
                hoja.write_blank(fila, c, None, dato)
            return
        hoja.write(fila, archivo, toma.archivo, dato)
        for j, valor in enumerate(toma.nivelRGB + toma.dispRGB):
            formato = self.celda(KXL.COLOR_DATO, banda, "center",
                                 KXL.NUM_UNO if (j < KXL.CANALES)
                                 else KXL.NUM_TRES)
            if math.isfinite(valor):
                hoja.write_number(fila, col + KXL.COL_VALORES + j, valor,
                                  formato)
            else:
                hoja.write_blank(fila, col + KXL.COL_VALORES + j, None,
                                 formato)

    #
    def fila_canales(self, hoja: Worksheet, fila: int, col: int,
                     valores: tuple[float, ...] | None,
                     banda: bool, numero: str) -> None:
        """
        Rojo, verde y azul de una fila de Datos (datos, con este formato
        de número), desde la primera columna de valores; sin valores (o
        un valor no finito), en blanco con su formato.
        """
        dato = self.celda(KXL.COLOR_DATO, banda, "center", numero)
        for j in range(KXL.CANALES):
            c = col + KXL.COL_VALORES + j
            if valores and math.isfinite(valores[j]):
                hoja.write_number(fila, c, valores[j], dato)
            else:
                hoja.write_blank(fila, c, None, dato)

    #
    def zona_y_tercios(self, hoja: Worksheet, fila: int, col: int,
                       tercio_ev: int, banda: bool) -> None:
        """ Nombre de la zona y sus tercios respecto a la ZV (literales). """
        hoja.write(fila, col, self.nombre_zona(tercio_ev),
                   self.celda(KXL.COLOR_LITERAL, banda, "center"))
        hoja.write_number(fila, col + 1, tercio_ev,
                          self.celda(KXL.COLOR_LITERAL, banda, "center",
                                     KXL.NUM_ENTERO))

    #
    def nombre_balance(self, nombre: str | None) -> str:
        """
        Nombre traducido de un balance (DAYLIGHT…; los preajustes con
        número, PRESET2, como «Preajuste 2»), o tal cual.
        """
        if nombre is None:
            return ""
        preset = re.fullmatch(KXL.REGEX_PRESET, nombre)
        if preset:
            return self.__textos[KXL.T_PRESET].format(n=preset.group(1))
        return self.__textos.get(KXL.PREFIJO_BALANCE + nombre, nombre)

    #
    @staticmethod
    def nombre_zona(tercio_ev: int) -> str:
        """ Nombre de una zona en el libro: Z0, Z0 1/3, … ZV, … ZX. """
        entera, tercio = zona_tercio(tercio_ev)
        return (f"{KP.PREFIJO}{KP.ROMANOS.get(entera, entera)}"
                f"{KXL.TERCIOS_EXCEL[tercio]}")

    #
    def titulo(self, hoja: Worksheet, fila: int, col: int, titulo: str,
               nota: str, anchos: tuple[float | None, ...]) -> None:
        """
        Título de la hoja y, debajo, su nota en gris (en las columnas de
        anchos, ver nota).
        """
        hoja.write(fila, col, titulo,
                   self.formato(bold=True, font_size=KXL.LETRA_TITULO))
        self.nota(hoja, fila + 1, col, nota, anchos)

    #
    def nota(self, hoja: Worksheet, fila: int, col: int, texto: str,
             anchos: tuple[float | None, ...], formato: Format | None = None,
             formula: str | None = None) -> None:
        """
        Nota en gris (o en este formato) partida en líneas: ocupa las
        columnas de anchos (las de su tabla, desde col) que caben en
        KXL.ANCHO_NOTA, y la fila crece según las líneas. Con fórmula, la
        escribe con texto como resultado.
        """
        ancho, columnas = 0.0, 0
        for a in anchos:
            if columnas and ((ancho + (a or 0)) > KXL.ANCHO_NOTA):
                break
            ancho += a or 0
            columnas += 1
        if formato is None:
            formato = self.formato(font_color=KXL.COLOR_ROTULO,
                                   text_wrap=True, valign="top")
        if columnas > 1:
            hoja.merge_range(fila, col, fila, col + columnas - 1,
                             "" if formula else texto, formato)
        elif formula is None:
            hoja.write(fila, col, texto, formato)
        if formula is not None:
            self.formula(hoja, fila, col, formula, formato, texto)
        hoja.set_row(fila, KXL.ALTO_LINEA * self.lineas(texto, ancho))

    #
    @staticmethod
    def lineas(texto: str, ancho: float) -> int:
        """ Líneas que ocupa un texto en una celda de este ancho. """
        return sum(max(1, math.ceil(len(bloque) * KXL.ANCHO_LETRA / ancho))
                   for bloque in texto.split("\n"))

    #
    def rotulo_fila(self, hoja: Worksheet, fila: int, col: int, texto: str,
                    formato: Format) -> None:
        """
        Rótulo de una fila de Datos, en las KXL.COLUMNAS_ROTULO primeras
        columnas (no cabe en una).
        """
        hoja.merge_range(fila, col, fila, col + KXL.COLUMNAS_ROTULO - 1,
                         texto, formato)

    #
    def cabecera(self, hoja: Worksheet, fila: int, col: int,
                 textos: tuple[str, ...]) -> None:
        """
        Cabecera de una tabla: blanco y negrita sobre el color de las
        cabeceras.
        """
        formato = self.fmt_cabecera()
        for i, texto in enumerate(textos):
            hoja.write(fila, col + i, texto, formato)

    #
    def fmt_cabecera(self) -> Format:
        """ Formato de la cabecera de una tabla. """
        return self.formato(
            bold=True, font_color=KXL.CABECERA_TEXTO,
            bg_color=KXL.CABECERA_FONDO, pattern=1, text_wrap=True,
            align="center", valign="vcenter", border=KXL.FINO)

    #
    @staticmethod
    def tercios_texto(zonas: float) -> str:
        """ Zonas en tercios, como en el libro: 1/3, 2/3, 1, 1 1/3… """
        tercios = round(zonas * len(KXL.TERCIOS_EXCEL))
        entera, resto = divmod(tercios, len(KXL.TERCIOS_EXCEL))
        texto = f"{entera}{KXL.TERCIOS_EXCEL[resto]}" if entera else \
            KXL.TERCIOS_EXCEL[resto].strip()
        return texto or "0"

    #
    def celda(self, color: str, banda: bool, alineado: str,
              numero: str | None = None, **mas: object) -> Format:
        """
        Formato de una celda de tabla: color del texto, fila alterna (con
        fondo), alineación, formato de número y más propiedades.
        """
        propiedades: dict = dict(font_color=color, align=alineado,
                                 border=KXL.FINO,
                                 border_color=KXL.BORDE_TABLA, **mas)
        if banda:
            propiedades.update(bg_color=KXL.BANDA, pattern=1)
        if numero:
            propiedades["num_format"] = numero
        return self.formato(**propiedades)

    #
    def texto(self, color: str, negrita: bool = False) -> Format:
        """ Formato de un texto suelto, en su color. """
        return self.formato(font_color=color, bold=negrita)

    #
    def apartado(self) -> Format:
        """ Formato del título de una sección de la hoja. """
        return self.formato(bold=True, font_size=KXL.LETRA_APARTADO)

    #
    @staticmethod
    def cadena(texto: str) -> str:
        """ Texto como cadena de una fórmula: entre comillas, dobladas. """
        comilla = KXL.COMILLA
        return f"{comilla}{texto.replace(comilla, comilla * 2)}{comilla}"

    #
    def formato(self, **propiedades: object) -> Format:
        """
        Formato con estas propiedades (sin fuente: la del libro, en su
        tamaño: XlsxWriter pondría Calibri 11); los iguales se reutilizan.
        """
        propiedades.setdefault("font_name", KXL.FUENTE)
        propiedades.setdefault("font_size", KXL.LETRA)
        clave = tuple(sorted(propiedades.items()))
        if clave not in self.__formatos:
            self.__formatos[clave] = self.__excel.add_format(
                dict(propiedades))
        return self.__formatos[clave]

    #
    def fmt_formula(self, banda: bool, numero: str | None = None) -> Format:
        """
        Formato de una celda de fórmula de Cálculo: centrada, en su fila
        alterna y con este formato de número.
        """
        return self.celda(KXL.COLOR_FORMULA, banda, "center", numero)

    #
    @staticmethod
    def rango_columna(fila: int, n: int, c: int) -> str:
        """ Rango absoluto de n filas de la columna c, desde fila. """
        return (f"{xl_rowcol_to_cell(fila, c, True, True)}:"
                f"{xl_rowcol_to_cell(fila + n - 1, c, True, True)}")

    #
    @staticmethod
    def celda_desp(fila: int, col: int, desp: int) -> str:
        """ Celda de esta fila, desp columnas a la derecha de col. """
        return xl_rowcol_to_cell(fila, col + desp)

    #
    @staticmethod
    def rango_graf(hoja: str, col: int, n: int, fila: int, desp: int) -> str:
        """
        Rango de una serie de gráfica: n filas de la hoja (su nombre),
        desde fila, en la columna col + desp.
        """
        celdas = xl_range_abs(fila, col + desp, (fila + n) - 1, col + desp)
        return f"='{hoja}'!{celdas}"

    #
    def nueva_graf(self, t: dict[str, str], tipo: str, titulo: str,
                   eje: tuple, nombre_eje: str,
                   base: int | None = None) -> Chart:
        """
        Gráfica nueva del libro, con su título numerado, sus ejes, su
        leyenda y su medida (t: los textos ya traducidos).
        """
        g = cast(Chart, self.__excel.add_chart({"type": tipo}))
        g.set_title({"name": KXL.FORMATO_TITULO_GRAF.format(
            numero=KXL.ORDEN_GRAF.index(titulo) + 1, titulo=t[titulo])
            if (titulo in KXL.ORDEN_GRAF) else t[titulo]})
        g.set_x_axis({"name": t[KXL.T_EJE_ZONA],
                      "label_position": "low",
                      "num_font": {"rotation": KXL.GIRO_ZONAS,
                                   "size": KXL.LETRA_ZONAS}})
        # --- Eje y: con base, logarítmico (sin paso: una marca por
        #     potencia de la base)
        piso, tope, paso, formato_num = eje
        eje_y = {"name": t[nombre_eje], "min": piso, "max": tope,
                 "num_format": formato_num}
        if paso is not None:
            eje_y["major_unit"] = paso
        if base:
            eje_y["log_base"] = base
        g.set_y_axis(eje_y)
        g.set_legend({"position": "bottom"})
        g.set_size({"width": KXL.MEDIDA_GRAF[0],
                    "height": KXL.MEDIDA_GRAF[1]})
        return g

    #
    @staticmethod
    def linea_graf(color: str, ancho: float = 1.5,
                   trazo: str | None = None) -> dict:
        """ Línea de una serie de gráfica: color, grosor y trazo. """
        propiedades: dict = {"color": color, "width": ancho}
        if trazo:
            propiedades["dash_type"] = trazo
        return propiedades

    #
    @staticmethod
    def marcador_graf(color: str, forma: str = KXL.FORMA_REDONDA) -> dict:
        """
        Marcador de una serie de gráfica, en su color (redondo si no se
        dice otra forma).
        """
        return {"type": forma, "size": KXL.MEDIDA_MARCADOR,
                "fill": {"color": color}, "border": {"color": color}}

    #
    @staticmethod
    def formula(hoja: Worksheet, fila: int, col: int, texto: str,
                formato: Format | None, valor: object) -> None:
        """
        Escribe una fórmula con su resultado ya calculado (así se ve en la
        Vista protegida de Excel y en los visores que no recalculan).
        """
        # --- type: ignore: XlsxWriter declara el resultado como int, pero
        #     admite cualquier número o texto
        hoja.write_formula(fila, col, texto, formato, valor)  # type: ignore

    #
    @staticmethod
    def formula_matriz(hoja: Worksheet, fila: int, col: int, fila_fin: int,
                       col_fin: int, texto: str, formato: Format | None,
                       valor: object) -> None:
        """ Escribe una fórmula matricial con su resultado ya calculado. """
        # --- type: ignore: como en formula()
        hoja.write_array_formula(fila, col, fila_fin, col_fin, texto,
                                 formato, valor)        # type: ignore

    # endregion Piezas comunes
