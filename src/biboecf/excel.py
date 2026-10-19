# -*- coding: utf-8 *-*
"""
    :Propósito: Libro Excel de resultados de una serie (pieza D), escrito
                desde cero con XlsxWriter: cada valor calculado va con su
                fórmula y su resultado (así se ve en la Vista protegida de
                Excel). Sin textos propios: los recibe ya traducidos
    :Autor:     Tony Diana
    :Versión:   26.10.18
"""

# cSpell:ignore asim, biboecf, Calibri, CIELAB, COUNTIF, desp, desv, dif, disp
# cSpell:ignore dvi, graf, grafs, gridlines, ISNUMBER, kcom, kte, ktr, kxl
# cSpell:ignore Lightroom, lstar, lzv, mpx, mult, preajuste, preajustes, rci
# cSpell:ignore recalculan, Relacion, rowcol, srgb, valign, vcenter, Verdana
# cSpell:ignore xlsxwriter

__all__ = ["KXL", "Excel", "PuntoCurva"]

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
from .review import Review, ZonaMedida
from .constantes import COM as KCOM
from .kernel import OECF
from .secuencia import KS
from .teselas import KTE
from .transferencia import KTR, escala_mpx, signal_para_snr, snr_modelo
from .zonas import KP, zona_tercio


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
    """Color del texto de rótulos y notas (también en la ficha)."""

    # --- Tablas: cabecera, filas alternas y bordes finos, en la gama de
    #     verdes del libro (Tony, 2026-10-15; antes, azules). La cabecera,
    #     lo bastante oscura para que se lea el blanco
    CABECERA_FONDO = "#548235"
    """Fondo de la cabecera de las tablas (también en la ficha)."""
    CABECERA_TEXTO = "#FFFFFF"
    BANDA = "#E2EFDA"
    """Fondo de las filas alternas de las tablas (también en la ficha)."""
    BORDE_TABLA = "#A9D08E"
    """Color de los bordes finos de las tablas (también en la ficha)."""
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

    # --- Para pasar fracciones a porcentaje (el de biboecf)
    CIEN = KCOM.CIEN
    """Para pasar fracciones a porcentaje: el COM.CIEN de biboecf."""

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

    # --- Columna del L* del revelador en su tabla de Datos, tras zona y
    #     tercios
    COL_REVELADOR = 2

    # --- Hojas, en su orden (claves de sus nombres en los textos)
    T_HOJA_RESUMEN = "hoja_resumen"
    T_HOJA_GRAF = "hoja_graf"
    T_HOJA_DATOS = "hoja_datos"
    T_HOJA_CONSTANTES = "hoja_constantes"
    T_HOJA_CALCULO = "hoja_calculo"
    T_HOJA_RECHAZADAS = "hoja_rechazadas"
    T_HOJA_IA = "hoja_ia"
    HOJAS = (T_HOJA_RESUMEN, T_HOJA_GRAF, T_HOJA_DATOS,
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
    C_TEXTURA_CONSERVADA = "TexturaConservada"
    C_TELA_RECORTADO_MAX = "TelaRecortadoMax"
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
        (C_ROSE_TEXTURA, 5, U_VECES),
        (C_TEXTURA_CONSERVADA, 0.5, U_PART),
        (C_TELA_RECORTADO_MAX, 0.1, U_PART),
        (C_MARGEN_SOMBRAS, 1, U_TERCIOS),
        (C_ANCHO_ZONA, 1, U_ZONAS),
        (C_LAB_ESCALA, KCOM.LAB_ESCALA, U_NUMERO),
        (C_LAB_DESPLAZA, KCOM.LAB_DESPLAZA, U_NUMERO),
        (C_LAB_UMBRAL, KCOM.LAB_UMBRAL, U_PART),
        (C_LAB_PENDIENTE, KCOM.LAB_PENDIENTE, U_NUMERO),
        (C_SRGB_UMBRAL, 0.0031308, U_PART),
        (C_SRGB_PENDIENTE, 12.92, U_NUMERO),
        (C_SRGB_ESCALA, 1.055, U_NUMERO),
        (C_SRGB_GAMMA, 2.4, U_NUMERO),
        (C_SRGB_DESPLAZA, 0.055, U_NUMERO),
        (C_ESCALA_CURVA, 255, U_NUMERO),
        (C_TEXTO_RECORTADO, V_RECORTADO, U_TEXTO),
        (C_TEXTO_NO_RECORTADO, V_NO_RECORTADO, U_TEXTO),
        (C_TEXTO_NINGUNO, V_NINGUNO, U_TEXTO),
        (C_TEXTO_NO_ALCANZADO, V_NO_ALCANZADO, U_TEXTO),
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

    # --- Hoja Datos: anchos (C a K), Z-V de control que caben y textos
    ANCHOS_DATOS = (12.0, 9.0, 16.0, 14.0, 14.0, 14.0, 14.0, 14.0, 14.0)
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
    #     del nombre traducido de cada balance (el de biboecf: DAYLIGHT…;
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
    T_ORIGEN_TAPADAS = "origen_tapadas"
    T_SIN_RUIDO = "sin_ruido"
    T_REVELADOR = "revelador"
    T_TELA = "tela"
    T_NOTA_TELA = "nota_tela"
    T_CAB_TELA_REC_ROJO = "cab_tela_rec_rojo"
    T_CAB_TELA_REC_VERDE = "cab_tela_rec_verde"
    T_CAB_TELA_REC_AZUL = "cab_tela_rec_azul"
    T_NOTA_REVELADOR = "nota_revelador"
    T_CAB_REVELADOR = "cab_revelador"

    # --- Ruido y negro: origen del ruido (biboecf.KTE) y su texto, la
    #     comparación con las tapadas, el negro restado y sus avisos
    T_ORIGEN_CURVA = "origen_curva"
    ORIGEN_RUIDO = {KTE.ORIGEN_BORDE: T_ORIGEN_BORDE,
                    KTE.ORIGEN_TAPADAS: T_ORIGEN_TAPADAS,
                    KTE.ORIGEN_CURVA: T_ORIGEN_CURVA}
    T_COMPARAR_TAPADAS = "comparar_tapadas"
    T_NEGRO_TAPADAS = "negro_tapadas"
    T_NEGRO_SOMBRAS = "negro_sombras"
    T_NEGRO_DECLARADO = "negro_declarado"
    ORIGEN_NEGRO = {KTE.ORIGEN_TAPADAS: T_NEGRO_TAPADAS,
                    KTE.ORIGEN_SOMBRAS: T_NEGRO_SOMBRAS,
                    KTE.ORIGEN_DECLARADO: T_NEGRO_DECLARADO}
    T_RUIDO_NEGRO = "ruido_negro"
    T_RUIDOS_DIFIEREN = "ruidos_difieren"
    T_SIN_RUIDO_SUELO = "sin_ruido_suelo"

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
    ANCHOS_CALCULO = (12.0,) * 25
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

    # --- Resultados para el JSON (Excel.resultados): claves de los
    #     canales, sin idioma
    CANALES_JSON = ("R", "G", "B")

    # --- Claves de zonas_canal (por zona y canal) y de canales (por
    #     canal: lo que da el bloque 1 de Cálculo)
    Z_ESPERADO = "esperado"
    Z_OBTENIDO = "obtenido"
    Z_DEV = "dev"
    Z_RECORTADO = "recortado"
    R_MEDIA_ZV = "media_zv"
    R_MAX = "max"
    R_TECHO = "techo"
    R_SUELO = "suelo"
    R_RANGO = "rango"
    R_FIN_LINEAL = "fin_lineal"
    R_PRIMER_RECORTADO = "primer_recortado"
    R_SUELO_SUGERIDO = "suelo_sugerido"
    R_SUELO_EXCELENTE = "suelo_excelente"
    R_LATITUD = "latitud_sugerida"

    # --- Claves de los resultados en el JSON (Excel.resultados)
    J_CANALES = "canales"
    J_TEXTURAS = "latitud_texturas"
    """Clave de la latitud de texturas en los resultados del JSON."""
    J_CURVA = "curva"
    J_DIFERENCIAS = "diferencias_medias"
    J_ZONA = "zona"
    J_TERCIO = "tercioEV"
    J_ESPERADO = "esperado"
    J_OBJETIVO = "objetivo"
    J_SENSOR = "sensor"
    J_REVELADOR = "revelador"
    J_ENTRADA = "entrada"
    J_SALIDA = "salida"
    J_PUNTO = "punto"
    TEXTURAS_JSON = ("sombras", "luces", "zonas")
    """Claves de cada tramo de la latitud de texturas en el JSON:
    sombras, luces y zonas."""

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
    LIMITE_SOMBRAS = 1
    LIMITE_LUCES = 2
    LIMITE_LATITUD = 3

    # --- Columnas del bloque 3 de Cálculo que leen Análisis y Datos
    #     (desde la de la zona)
    CURVA_L_ESPERADO = 3
    CURVA_DIF_SENSOR = 7
    CURVA_DIF_REVELADOR = 10
    CURVA_ENTRADA = 13
    CURVA_SALIDA = 14
    CURVA_PUNTO = 15

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
    T_SUGERENCIA = "sugerencia"
    T_REFERENCIA = "referencia"
    T_ES_SUGERENCIA = "es_sugerencia"
    T_SUGERIDO = "sugerido"
    T_DIF_MEDIA_SENSOR = "dif_media_sensor"
    T_DIF_MEDIA_REVELADOR = "dif_media_revelador"
    T_SIN_REVELADOR = "sin_revelador"
    T_NOTA_TEXTURAS_RESUMEN = "nota_texturas_resumen"
    T_SIN_TELA = "sin_tela"

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
    EJE_DIF_LSTAR = (-15, 10, 5, "+0;-0;0")

    # --- Textos de Gráficos
    T_TITULO_GRAF = "titulo_graf"
    T_NOTA_GRAF = "nota_graf"
    T_G_ESPERADO = "g_esperado"
    T_G_DESV_LINEAL = "g_desv_lineal"
    T_G_DESV_COMPLETA = "g_desv_completa"
    T_G_SNR = "g_snr"
    T_G_CURVA = "g_curva"
    T_G_DIFERENCIA = "g_diferencia"

    # --- Orden de las gráficas en la hoja (de izquierda a derecha y de
    #     arriba abajo): primero lo que más interesa al estudiante (Tony).
    #     Su número en el título sale de aquí
    ORDEN_GRAF = (T_G_CURVA, T_G_DIFERENCIA, T_G_ESPERADO,
                  T_G_DESV_LINEAL, T_G_DESV_COMPLETA, T_G_SNR)
    """Orden de las gráficas en la hoja; da su número en el título."""
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
    #     archivo, KCOM.RUTA_PROMPT_IA), una línea por fila. Las de
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
    #     textos, que llevan los umbrales de biboecf.KTE
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
class Excel(object):
    """
    Libro Excel de una serie. Se crea con la ruta, los textos ya
    traducidos ({clave de KXL: texto}) y lo medido en los RAW (Review);
    escribir() lo graba.
    """

    __slots__ = ["__datos", "__filas", "__formatos", "__hojas", "__excel",
                 "__revelador", "__etiquetas", "__textos"]

    #
    def __init__(self, ruta: Path, textos: dict[str, str],
                 datos: Review) -> None:

        # --- Variables de instancia. filas: dónde quedó cada bloque de
        #     Datos (KXL.F_*), para las fórmulas de las demás hojas
        self.__textos: dict[str, str] = self.con_nombres(textos)
        self.__datos: Review = datos
        self.__excel = xlsxwriter.Workbook(str(ruta))
        self.__formatos: dict[tuple, Format] = {}
        self.__hojas: dict[str, Worksheet] = {}
        self.__filas: dict[str, int] = {}

        # --- Texto de la primera columna de las filas de Datos que lee
        #     Análisis (el ruido y el negro), {fila: texto}
        self.__etiquetas: dict[int, str] = {}

        # --- L* del revelador por zona, como sale en Datos: el leído y,
        #     en los tercios sin él, el estimado (None: sin dato)
        self.__revelador: list[float | None] = self.revelador_estimado()

        # --- Fuente por defecto de todas las celdas
        self.__excel.formats[0].set_font_name(KXL.FUENTE)
        self.__excel.formats[0].set_font_size(KXL.LETRA)

        # --- Las hojas, en su orden, antes de escribir ninguna: las
        #     fórmulas de unas leen de otras
        for clave in KXL.HOJAS:
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
        self.revelador_datos()
        self.hoja_graf()
        self.hoja_rechazadas()
        self.hoja_ia()
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

        # --- Ruido de lectura por canal, con su origen (o que no se midió)
        fila += 2
        hoja.write(fila, col, t[KXL.T_RUIDO], self.apartado())
        fila += 1
        self.cabecera(hoja, fila, col, (t[KXL.T_CAB_ORIGEN], "", "")
                      + canales)
        fila += 1
        self.__filas[KXL.F_RUIDO] = fila
        ruido = d.ruidoRGB
        origen = (t[KXL.ORIGEN_RUIDO[d.origen_ruido]]
                  if (ruido and (d.origen_ruido is not None))
                  else t[KXL.T_SIN_RUIDO])
        self.rotulo_fila(hoja, fila, col, origen, literal)
        self.__etiquetas[fila] = origen
        self.fila_canales(hoja, fila, col, ruido, True, KXL.NUM_DOS)

        # --- Si el ruido es del borde y además hay tapadas, las tapadas,
        #     para comparar; y el negro restado, con su origen
        filas_extra = []
        if (d.origen_ruido == KTE.ORIGEN_BORDE) and d.ruidoTapadasRGB:
            filas_extra.append((KXL.F_RUIDO_TAPADAS,
                                t[KXL.T_COMPARAR_TAPADAS],
                                d.ruidoTapadasRGB, KXL.NUM_DOS))
        filas_extra.append((KXL.F_NEGRO, t[KXL.ORIGEN_NEGRO[d.origen_negro]],
                            d.negroRGB, KXL.NUM_ENTERO))
        for i, (clave, texto, valores, numero) in enumerate(filas_extra):
            fila += 1
            banda = (i % 2) == 1
            self.__filas[clave] = fila
            literal_i = self.celda(KXL.COLOR_LITERAL, banda, "center")
            self.rotulo_fila(hoja, fila, col, texto, literal_i)
            self.__etiquetas[fila] = texto
            self.fila_canales(hoja, fila, col, valores, banda, numero)

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
            t[KXL.T_CAB_TELA_REC_VERDE], t[KXL.T_CAB_TELA_REC_AZUL]))
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
                                        t[KXL.T_CAB_REVELADOR]))
        self.__filas[KXL.F_REVELADOR] = fila + 1
        for i in range((2 * KS.TERCIOS_LADO) + 1):
            fila += 1
            banda = (i % 2) == 0
            tercio_ev = i - KS.TERCIOS_LADO
            self.zona_y_tercios(hoja, fila, col, tercio_ev, banda)

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
                         canal[KXL.R_MEDIA_ZV])
            columna = self.ref(KXL.T_HOJA_DATOS, f[KXL.F_ZONAS],
                               cols_datos[j], True, False)
            hasta = celda(f[KXL.F_ZONAS] + n - 1, cols_datos[j], True)
            self.formula(hoja, r, col + 2, f"=MAX({columna}:{hasta})", uno,
                         canal[KXL.R_MAX])
            dz, ez = celda(r, col + 1), celda(r, col + 2)
            self.formula(
                hoja,
                r, col + 3, f'=IF(AND(N({dz})>0,N({ez})>0),{KXL.C_ZONA_ZV}'
                f'+LOG({ez}/{dz},{KXL.C_FACTOR_ZONA}),"")', dos,
                canal[KXL.R_TECHO])
            # --- Suelo: donde la señal/ruido (normalizada) llega a
            #     C_RATIO_SR, según la curva de transferencia
            self.formula(hoja, r, col + 4,
                         self.suelo_snr(KXL.C_RATIO_SR, j, dz), dos,
                         canal[KXL.R_SUELO])
            fz, gz = celda(r, col + 3), celda(r, col + 4)
            self.formula(
                hoja, r, col + 5, f'=IF(AND(ISNUMBER({fz}),ISNUMBER({gz})),'
                f'{fz}-{gz},"")', dos, canal[KXL.R_RANGO])

            # --- Último punto lineal y primer recortado: fórmulas
            #     matriciales (sin literales ni trucos)
            dv, rc = rango(c_desv + j), rango(c_rec + j)
            es = rango(col + 2)
            cond = (f"IF(ISNUMBER({dv}),IF(ABS({dv})<="
                    f"{KXL.C_TOLERANCIA_LINEAL},IF({rc}="
                    f"{KXL.C_TEXTO_NO_RECORTADO},1,0),0),0)")
            self.formula_matriz(
                hoja, r, col + 6, r, col + 6,
                f"{{=IF(SUM({cond})=0,{KXL.C_TEXTO_NINGUNO},"
                f"MAX(IF({cond}=1,{es})))}}", dos,
                canal[KXL.R_FIN_LINEAL])
            self.formula(
                hoja,
                r, col + 7, f"=IF(COUNTIF({rc},{KXL.C_TEXTO_RECORTADO})=0,"
                f"{KXL.C_TEXTO_NO_ALCANZADO},INDEX({es},MATCH("
                f"{KXL.C_TEXTO_RECORTADO},{rc},0)))", dos,
                canal[KXL.R_PRIMER_RECORTADO])
            # --- Suelos sugeridos, aceptable (C_SNR_MINIMA) y excelente
            #     (C_SNR_EXCELENTE), como el suelo; y la latitud, con el
            #     aceptable
            for desp, umbral, clave in (
                    (8, KXL.C_SNR_MINIMA, KXL.R_SUELO_SUGERIDO),
                    (9, KXL.C_SNR_EXCELENTE, KXL.R_SUELO_EXCELENTE)):
                self.formula(hoja, r, col + desp,
                             self.suelo_snr(umbral, j, dz), dos,
                             canal[clave])
            iz, kz = celda(r, col + 6), celda(r, col + 8)
            self.formula(
                hoja, r, col + 10, f"=IF(AND(ISNUMBER({iz}),ISNUMBER({kz})),"
                f"{iz}-{kz}+{KXL.C_ANCHO_ZONA},"
                f"{KXL.C_TEXTO_NO_ALCANZADO})", dos,
                canal[KXL.R_LATITUD])
        # --- Debajo, de qué suelo sale la latitud y por qué es asimétrica
        self.nota(hoja, fila_b1 + KXL.CANALES, col, t[KXL.T_NOTA_LATITUD],
                  KXL.ANCHOS_CALCULO)
        techo_verde = celda(fila_b1 + 1, col + 3, True, True)
        suelo_verde = celda(fila_b1 + 1, col + 4, True, True)

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
        techo_v = self.valor(hoja, fila_b1 + 1, col + 3)
        suelo_v = self.valor(hoja, fila_b1 + 1, col + 4)

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
        self.marco(hoja, ((ultima, KXL.ANCHOS_CALCULO),))

    #
    def bloque_texturas(self, hoja: Worksheet, fila_b4: int, col: int,
                        k: dict) -> int:
        """
        Bloque 4 de Cálculo: latitud de texturas del verde. Arriba, los
        límites (apreciable y recomendada: sombras, luces y latitud; los
        lee Análisis); debajo, una fila por zona con la textura del paño
        (de Datos), su relación con el ruido de la tarjeta, la conservada
        frente a la ZV, el paño recortado y si cumple cada criterio (ver
        texturas y limites_texturas). Devuelve su última fila.
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
            (KXL.T_CAB_SIN_RECORTE, KXL.TEXTURA_SIN_RECORTE))}
        bajo = {clave: f"{celda(fila_t, c, True, True)}:"
                f"{celda(fila_t + zv, c, True, True)}"
                for clave, c in columnas.items()}
        alto = {clave: f"{celda(fila_t + zv, c, True, True)}:"
                f"{celda(fila_t + n - 1, c, True, True)}"
                for clave, c in columnas.items()}

        # --- Límites: apreciable y recomendada
        no = KXL.C_TEXTO_NO_ALCANZADO
        tercio = KXL.C_TERCIO_POR_ZONA
        cumple, es, q = (bajo[KXL.T_CAB_CUMPLE_SOMBRAS],
                         bajo[KXL.T_CAB_ESPERADO],
                         bajo[KXL.T_CAB_TEXTURA_RUIDO])
        # --- Solo cuentan los tercios con dato: el criterio por
        #     ISNUMBER de su valor (matriciales)
        ok = f"{cumple}*ISNUMBER({q})"
        m = f"MATCH(1,{ok},0)"
        sombra = (f"{{=IF(SUM({ok})=0,{no},IF({m}=1,INDEX({es},{m}),IF("
                  f"ISNUMBER(INDEX({q},{m}-1)),ROUND((INDEX({es},{m}-1)+("
                  f"{KXL.C_ROSE_TEXTURA}-INDEX({q},{m}-1))/(INDEX({q},{m})-"
                  f"INDEX({q},{m}-1))/{tercio})*{tercio},0)/{tercio},INDEX("
                  f"{es},{m}))))}}")
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
            c_sombra, c_luz = (celda(fila_b4, col + KXL.LIMITE_SOMBRAS),
                               celda(fila_b4, col + KXL.LIMITE_LUCES))
            if clave == KXL.T_APRECIABLE:
                formulas = (sombra, f"{{=IF(SUM({luces})=0,{no},"
                            f"MAX(IF({luces}=1,{es_alto})))}}")
            else:
                tope = f"MAX(IF({cortes}=1,{es_alto}))"
                formulas = (f"=IF(ISNUMBER({c_sombra}),{c_sombra}+"
                            f"{KXL.C_MARGEN_SOMBRAS}/{tercio},{c_sombra})",
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
                f"=IF(AND(ISNUMBER({luz_r}),ISNUMBER({sombra_r})),"
                f"{luz_r}-{sombra_r}+{KXL.C_ANCHO_ZONA},{no})", dos,
                valores[2])

        # --- Tabla por zona
        self.cabecera(hoja, fila_t - 1, col, tuple(t[c] for c in (
            KXL.T_CAB_ZONA, KXL.T_CAB_TERCIOS, KXL.T_CAB_ESPERADO,
            KXL.T_CAB_TEXTURA, KXL.T_CAB_TEXTURA_RUIDO, KXL.T_CAB_CONSERVADA,
            KXL.T_CAB_TELA_RECORTADO, KXL.T_CAB_CUMPLE_SOMBRAS,
            KXL.T_CAB_CUMPLE_LUCES, KXL.T_CAB_SIN_RECORTE)))
        hoja.set_row(fila_t - 1, KXL.ALTO_CABECERA_ALTA)
        textura_zv = celda(fila_t + zv, col + KXL.TEXTURA_TEXTURA, True, True)
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
            tela = self.ref(KXL.T_HOJA_DATOS, pz, verde)
            tarjeta = self.ref(KXL.T_HOJA_DATOS, dz, verde + KXL.CANALES)
            recorte = self.ref(KXL.T_HOJA_DATOS, pz, verde + KXL.CANALES)
            tx = celda(r, col + KXL.TEXTURA_TEXTURA)
            qr = celda(r, col + KXL.TEXTURA_RUIDO)
            cv = celda(r, col + KXL.TEXTURA_CONSERVADA)
            rp = celda(r, col + KXL.TEXTURA_RECORTADO)
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
                 KXL.NUM_PORCENTAJE, f'=IF(ISNUMBER({recorte}),{recorte},"")'))
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
                                  f"=IF(ISNUMBER({qr}),AND({qr}>="
                                  f"{KXL.C_ROSE_TEXTURA},{sigue}),{sigue})"))
            if i >= zv:
                for desp, clave, dato, cond in (
                        (KXL.TEXTURA_LUCES, KXL.T_CAB_CUMPLE_LUCES, cv,
                         f"{cv}>={KXL.C_TEXTURA_CONSERVADA}"),
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
        y el revelador (de su tabla en Datos), sus diferencias, falta y
        sobra (para las barras de la gráfica), entrada y salida de la
        curva de Lightroom (con el revelador) y si es punto de la curva.
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
            l_esp, l_rev, luz_rev = p.esperado, p.revelador, p.luz_revelador
            self.formula(
                hoja, r, col + 8, f'=IF(ISNUMBER({revelador}),{revelador},'
                f'{KXL.FORMULA_NA})',
                fmt(KXL.NUM_UNO), KXL.RESULTADO_NA if (l_rev is None)
                else l_rev)
            self.formula(
                hoja, r, col + 9, f'=IF(ISNUMBER({c(8)}),IF({c(8)}>'
                f'{KXL.C_LAB_UMBRAL}*{KXL.C_LAB_PENDIENTE},'
                f'(({c(8)}+'
                f'{KXL.C_LAB_DESPLAZA})/{KXL.C_LAB_ESCALA})^3,'
                f'{c(8)}/{KXL.C_LAB_PENDIENTE}),"")',
                fmt(KXL.NUM_CUATRO), self.en_blanco(luz_rev))
            self.formula(
                hoja, r, col + KXL.CURVA_DIF_REVELADOR,
                f'=IF(ISNUMBER({c(8)}),{c(8)}-{c(3)},{KXL.FORMULA_NA})',
                fmt(KXL.NUM_SIGNO_UNO),
                KXL.RESULTADO_NA if (l_rev is None) else (l_rev - l_esp))
            self.formula(
                hoja,
                r, col + 11, f'=IF(ISNUMBER({c(8)}),MAX(0,{c(3)}-{c(8)}),"")',
                fmt(KXL.NUM_UNO),
                "" if (l_rev is None) else max(0.0, l_esp - l_rev))
            self.formula(
                hoja,
                r, col + 12, f'=IF(ISNUMBER({c(8)}),MAX(0,{c(8)}-{c(3)}),"")',
                fmt(KXL.NUM_UNO),
                "" if (l_rev is None) else max(0.0, l_rev - l_esp))
            self.formula(
                hoja, r, col + KXL.CURVA_ENTRADA,
                f'=IF(ISNUMBER({c(9)}),{self.formula_curva(c(9))},"")',
                fmt(KXL.NUM_ENTERO),
                self.en_blanco(p.entrada))
            salida = p.salida
            self.formula(
                hoja, r, col + KXL.CURVA_SALIDA,
                f'=IF(ISNUMBER({c(8)}),{self.formula_curva(c(2))},"")',
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
        Izquierda: cabecera (cámara, fecha, bits y exposición de la Z-V),
        latitud de texturas, ruido de lectura y negro, y balances de
        blancos. Derecha: sugerencia de revelado, diferencias medias, las
        decisiones propias del estudiante y las recomendaciones (la tabla
        por zona: L* leído, diferencias del sensor y del revelador,
        entrada, salida y punto de la curva).
        """
        # --- Cada tarjeta, por su cuenta (la rejilla las independiza)
        hoja = self.__hojas[KXL.T_HOJA_RESUMEN]
        fila_balances = self.resumen_izquierda(hoja)
        ultima_derecha = self.resumen_derecha(hoja)
        ultima_izquierda = self.resumen_balances(hoja, fila_balances)
        self.marco(hoja, ((ultima_izquierda, KXL.ANCHOS_RESUMEN),
                          (ultima_derecha, KXL.ANCHOS_RESUMEN_DERECHA)),
                   KXL.ANILLO_RESUMEN, KXL.ANCHO_ANILLO_RESUMEN,
                   KXL.ANCHO_RELLENO_RESUMEN, KXL.ALTO_REJILLA)

    #
    def resumen_izquierda(self, hoja: Worksheet) -> int:
        """
        Tarjeta izquierda de Análisis: título, cámara, fecha, bits y
        exposición de la Z-V; latitud de texturas; ruido de lectura y
        negro, con sus avisos; y la barra y la nota de los balances de
        blancos. Devuelve la fila donde puede ir la cabecera de los
        balances (ver resumen_balances).
        """
        t, d, f = self.__textos, self.__datos, self.__filas
        col = KXL.COLUMNA_INICIO
        ultima = col + len(KXL.ANCHOS_RESUMEN) - 1
        rotulo = self.fmt_resumen(bold=True, align="right", valign="top")
        valor = self.fmt_resumen(align="left", valign="top")
        nota = self.nota_resumen(KXL.COLOR_ROTULO)

        # --- Cabecera: título, cámara, fecha, profundidad de bits de los
        #     RAW y exposición de la Z-V
        fila = KXL.FILA_INICIO
        hoja.merge_range(fila, col, fila + KXL.FILAS_TITULO_RESUMEN - 1,
                         ultima, t[KXL.T_TITULO_RESUMEN],
                         self.fondo_resumen(KXL.LETRA_RESUMEN_TITULO,
                                            align="center", valign="vcenter"))
        fila += KXL.FILAS_TITULO_RESUMEN + 1
        hoja.write(fila, col, t[KXL.T_MARCA_MODELO], rotulo)
        hoja.merge_range(fila, col + 1, fila, ultima, d.cam, valor)
        fila += 1
        hoja.write(fila, col, t[KXL.T_FECHA], rotulo)
        fecha = self.fmt_resumen(align="left", valign="top",
                                 num_format=t[KXL.T_FORMATO_FECHA])
        hoja.merge_range(fila, col + 1, fila, ultima, "", fecha)
        if d.fecha:
            hoja.write_datetime(fila, col + 1,
                                datetime.fromisoformat(d.fecha), fecha)
        fila += 1
        hoja.write(fila, col, t[KXL.T_BITS], rotulo)
        bits = self.fmt_resumen(align="left", valign="top",
                                num_format=KXL.NUM_BITS)
        hoja.merge_range(fila, col + 1, fila, ultima, "", bits)
        if d.bits:
            hoja.write_number(fila, col + 1, d.bits, bits)
        fila += 1
        hoja.write(fila, col, t[KXL.T_ZV], rotulo)
        for i, (clave, dato) in enumerate((
                (KXL.T_ISO, OECF.TextoISO(d.iso) if d.iso else ""),
                (KXL.T_TV, OECF.TextoTV(d.tv) if d.tv else ""),
                (KXL.T_F, OECF.TextoF(d.f) if d.f else ""))):
            hoja.write(fila, col + 1 + (2 * i), t[clave], rotulo)
            hoja.write(fila, col + 2 + (2 * i), dato, valor)

        # --- Latitud de texturas (de Cálculo, bloque 4): barra, cabecera,
        #     apreciable y recomendada (sombras, luces y latitud, en
        #     tercios) y la nota con los criterios (o que no hay paño)
        fila += 2
        self.barra_resumen(hoja, fila, col, ultima, t[KXL.T_TEXTURAS])
        fila = self.cabecera_tarjeta(
            hoja, fila + 2, col, (("", KXL.COLUMNAS_ROTULO),
                                  (t[KXL.T_CAB_SOMBRAS], 1),
                                  (t[KXL.T_CAB_LUCES], 1),
                                  (t[KXL.T_CAB_LATITUD_TEXTURAS], 1)),
            KXL.FILAS_CABECERA)
        k = self.valores_constantes()
        limites = self.limites_texturas(k, self.texturas(k))
        for i, (clave, valores) in enumerate(limites.items()):
            fila += 1
            banda = (i % 2) == 0
            hoja.merge_range(fila, col, fila, col + KXL.COLUMNAS_ROTULO - 1,
                             t[clave], self.celda_resumen(banda, "left"))
            numero = self.celda_resumen(banda, "center", KXL.NUM_TERCIOS)
            for j in range(len(valores)):
                origen = self.ref(KXL.T_HOJA_CALCULO, f[KXL.F_LIMITES] + i,
                                  col + KXL.LIMITE_SOMBRAS + j)
                self.formula(hoja, fila, col + KXL.COLUMNAS_ROTULO + j,
                             f"={origen}", numero, valores[j])
        if isinstance(d.tela, str):
            nota_texturas = t[KXL.T_SIN_TELA]
        else:
            nota_texturas = t[KXL.T_NOTA_TEXTURAS_RESUMEN].format(
                rose=k[KXL.C_ROSE_TEXTURA],
                conservada=round(k[KXL.C_TEXTURA_CONSERVADA] * KXL.CIEN),
                recortado=round(k[KXL.C_TELA_RECORTADO_MAX] * KXL.CIEN),
                margen=k[KXL.C_MARGEN_SOMBRAS])
        fila = self.nota_tarjeta(hoja, fila + 1, col, ultima, nota_texturas,
                                 KXL.ANCHOS_RESUMEN, nota)

        # --- Ruido de lectura y negro (de Datos): barra, una fila por
        #     dato (ruido usado, tapadas para comparar, negro; dos si su
        #     rótulo no cabe en una línea) y los avisos
        fila += 2
        self.barra_resumen(hoja, fila, col, ultima, t[KXL.T_RUIDO_NEGRO])
        fila = self.cabecera_tarjeta(
            hoja, fila + 2, col, (("", KXL.COLUMNAS_ROTULO),)
            + tuple((t[clave], 1) for clave in KXL.T_CANALES),
            KXL.FILAS_CABECERA)
        datos_ruido = [(f[KXL.F_RUIDO], d.ruidoRGB, KXL.NUM_DOS)]
        if KXL.F_RUIDO_TAPADAS in f:
            datos_ruido.append((f[KXL.F_RUIDO_TAPADAS], d.ruidoTapadasRGB,
                                KXL.NUM_DOS))
        datos_ruido.append((f[KXL.F_NEGRO], d.negroRGB, KXL.NUM_ENTERO))
        ancho_rotulo = sum(KXL.ANCHOS_RESUMEN[:KXL.COLUMNAS_ROTULO])
        for i, (origen, valores, formato) in enumerate(datos_ruido):
            fila += 1
            banda = (i % 2) == 0
            rotulo_ruido = self.__etiquetas[origen]
            filas = self.filas_texto(rotulo_ruido, ancho_rotulo
                                     / KXL.ESCALA_LETRA_TABLA,
                                     KXL.ALTO_LINEA_TABLA)
            abajo = fila + filas - 1
            texto = self.celda_resumen(banda, "left", text_wrap=True)
            numero = self.celda_resumen(banda, "center", formato)
            hoja.merge_range(fila, col, abajo, col + KXL.COLUMNAS_ROTULO - 1,
                             "", texto)
            self.formula(
                hoja, fila, col, "=" + self.ref(KXL.T_HOJA_DATOS, origen, col),
                texto, rotulo_ruido)
            for j in range(KXL.CANALES):
                c = col + KXL.COLUMNAS_ROTULO + j
                celda_datos = self.ref(KXL.T_HOJA_DATOS, origen,
                                       col + KXL.COL_VALORES + j)
                if filas > 1:
                    hoja.merge_range(fila, c, abajo, c, "", numero)
                self.formula(
                    hoja,
                    fila, c, f'=IF(ISNUMBER({celda_datos}),{celda_datos},"")',
                    numero, valores[j] if valores else "")
            fila = abajo
        avisos = []
        if d.ruidoRGB is None:
            avisos.append(t[KXL.T_SIN_RUIDO_SUELO])
        if d.difieren:
            avisos.append(t[KXL.T_RUIDOS_DIFIEREN].format(
                porcentaje=round(KTE.DIFERENCIA_RUIDO * KXL.CIEN)))
        for aviso in avisos:
            fila = self.nota_tarjeta(hoja, fila + 1, col, ultima, aviso,
                                     KXL.ANCHOS_RESUMEN, nota)

        # --- Balances de blancos (de Datos): barra y nota; la cabecera y
        #     los balances, en resumen_balances
        fila += 2
        self.barra_resumen(hoja, fila, col, ultima, t[KXL.T_BALANCES])
        fila = self.nota_tarjeta(hoja, fila + 1, col, ultima,
                                 t[KXL.T_NOTA_BALANCES], KXL.ANCHOS_RESUMEN,
                                 nota)
        return fila + 1

    #
    def resumen_balances(self, hoja: Worksheet, fila: int) -> int:
        """
        Balances de blancos de la tarjeta izquierda de Análisis (de
        Datos): la cabecera, desde fila, y, por balance, su nombre y los
        Kelvin de la cámara y reales. Devuelve su última fila.
        """
        t, d, f = self.__textos, self.__datos, self.__filas
        col = KXL.COLUMNA_INICIO
        fila = self.cabecera_tarjeta(
            hoja, fila, col + 2, ((t[KXL.T_CAB_BALANCE], 3),
                                  (t[KXL.T_CAB_KELVIN_ANOTADO], 1),
                                  (t[KXL.T_CAB_KELVIN_MEDIDO], 1)),
            KXL.FILAS_CABECERA_ALTA)
        for i, balance in enumerate(d.balancesDistintos):
            fila += 1
            banda = (i % 2) == 0
            texto = self.celda_resumen(banda, "left")
            numero = self.celda_resumen(banda, "center", KXL.NUM_ENTERO)
            origen = f[KXL.F_BALANCES] + i
            hoja.merge_range(fila, col + 2, fila, col + 4, "", texto)
            self.formula(
                hoja,
                fila, col + 2, "=" + self.ref(KXL.T_HOJA_DATOS, origen, col),
                texto, self.nombre_balance(balance.nombre))
            for j, valor_k in enumerate((balance.kelvin_cam,
                                         balance.kelvin)):
                celda_datos = self.ref(KXL.T_HOJA_DATOS, origen,
                                       col + KXL.COL_VALORES + j)
                self.formula(
                    hoja, fila, col + 5 + j,
                    f'=IF(ISNUMBER({celda_datos}),{celda_datos},"")',
                    numero, self.en_blanco(valor_k))
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

        # --- Diferencias medias (sensor y revelador) y, sin revelador, la
        #     nota que lo explica (sus filas, aunque salga vacía)
        rotulo = self.fmt_resumen(bold=True, align="right", valign="top")
        valor_media = self.fmt_resumen(align="left", valign="top",
                                       num_format=KXL.NUM_LSTAR)
        col_media = col + KXL.COLUMNAS_ROTULO_MEDIA
        medias = []
        for desp, clave in ((KXL.CURVA_DIF_SENSOR, KXL.T_DIF_MEDIA_SENSOR),
                            (KXL.CURVA_DIF_REVELADOR,
                             KXL.T_DIF_MEDIA_REVELADOR)):
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
        #     salida, en cada lado) y sus filas en blanco, que escribe el
        #     estudiante (validadas al final, cuando se sabe dónde está la
        #     lista de las zonas)
        fila += 2
        self.barra_resumen(hoja, fila, col, ultima, t[KXL.T_DECISIONES])
        punto = ((t[KXL.T_CAB_ZONA], 1), (t[KXL.T_CAB_ENTRADA], 1),
                 (t[KXL.T_CAB_SALIDA], 1))
        for lado in KXL.LADOS_DECISIONES:
            fin_cabecera = self.cabecera_tarjeta(hoja, fila + 1, col + lado,
                                                 punto, KXL.FILAS_CABECERA)
        primera_propia = fin_cabecera + 1
        fila = fin_cabecera
        for i in range(KXL.FILAS_DECISIONES):
            fila += 1
            banda = (i % 2) == 0
            for lado in KXL.LADOS_DECISIONES:
                hoja.write_blank(fila, col + lado, None, self.celda_resumen(
                    banda, "center", font_color=KXL.COLOR_DATO))
                for j in (1, 2):
                    hoja.write_blank(fila, col + lado + j, None,
                                     self.celda_resumen(
                                         banda, "center", KXL.NUM_ENTERO,
                                         font_color=KXL.COLOR_DATO))
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

        # --- Decisiones propias validadas: la zona, de la lista de la
        #     tabla; entrada y salida, enteros de 0 a C_ESCALA_CURVA
        zonas = (f"={celda(primera, col, True, True)}:"
                 f"{celda(fila, col, True, True)}")
        for lado in KXL.LADOS_DECISIONES:
            hoja.data_validation(
                primera_propia, col + lado, ultima_propia, col + lado,
                {"validate": "list", "source": zonas,
                 "error_title": t[KXL.T_DECISIONES],
                 "error_message": t[KXL.T_VALIDA_ZONA]})
            hoja.data_validation(
                primera_propia, col + lado + 1, ultima_propia,
                col + lado + 2,
                {"validate": "integer", "criteria": "between",
                 "minimum": 0, "maximum": f"={KXL.C_ESCALA_CURVA}",
                 "error_title": t[KXL.T_DECISIONES],
                 "error_message": t[KXL.T_VALIDA_CURVA].format(
                     tope=self.valores_constantes()[KXL.C_ESCALA_CURVA])})
        return fila

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
        Hoja Gráficos: seis gráficas que leen de Cálculo, en el orden de
        KXL.ORDEN_GRAF (que les da su número): la curva tonal en L*,
        la diferencia en L*, esperado y obtenido (con un segundo eje en
        pasos respecto a la Z-V), la desviación (tramo lineal y rango
        completo) y la señal/ruido. La serie del revelador, siempre: el L*
        leído puede llegar después (a mano); sin él, Cálculo da NA() y la
        gráfica no lo dibuja.
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
                     "marker": marcador(KXL.COLORES_CANALES[j])}
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
                          "marker": marcador(KXL.COLORES_CANALES[j])})
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
        #     revelador, con barras lilas hasta el esperado
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

        # --- Diferencia en L*: sensor y revelador; las negativas, en
        #     rojo
        g = graf("column", KXL.T_G_DIFERENCIA, KXL.EJE_DIF_LSTAR,
                 KXL.T_EJE_DIF_LSTAR)
        for nombre, desp, color in (
                (KXL.T_S_SENSOR, KXL.CURVA_DIF_SENSOR, KXL.COLOR_SENSOR),
                (KXL.T_S_REVELADOR, KXL.CURVA_DIF_REVELADOR,
                 KXL.COLORES_CANALES[2])):
            g.add_series({"name": t[nombre], "categories": zonas_b3,
                          "values": rango(b3, desp),
                          "fill": {"color": color},
                          "invert_if_negative": True,
                          "invert_if_negative_color": KXL.COLOR_NEGATIVO})
        grafs[KXL.T_G_DIFERENCIA] = g

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
            lineas = self.con_nombre(KCOM.RUTA_PROMPT_IA.read_text(
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
        excelente (C_SNR_EXCELENTE) y la latitud sugerida (KXL.R_*). Lo que
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
                KXL.R_MEDIA_ZV: medias[j], KXL.R_MAX: topes[j],
                KXL.R_TECHO: techo, KXL.R_SUELO: suelo,
                KXL.R_RANGO: ((techo - suelo) if (isinstance(techo, float)
                              and isinstance(suelo, float)) else ""),
                KXL.R_FIN_LINEAL: (max(lineales) if lineales
                                   else t[KXL.V_NINGUNO]),
                KXL.R_PRIMER_RECORTADO: (primeros[0] if primeros
                                         else t[KXL.V_NO_ALCANZADO]),
                KXL.R_SUELO_SUGERIDO: sugerido,
                KXL.R_SUELO_EXCELENTE: self.valor_suelo(KXL.C_SNR_EXCELENTE,
                                                        j, k),
                KXL.R_LATITUD: (self.latitud(max(lineales), sugerido, k)
                                if lineales else t[KXL.V_NO_ALCANZADO])})
        return resultados

    #
    def resultados(self) -> dict:
        """
        Resultados del análisis para el JSON (los que lee FotoEstación,
        que no lleva biboecf): por canal (canales), la latitud de
        texturas, la curva zona a zona y las diferencias medias. Sin
        constantes ni textos: lo que no es un número (no alcanzado, sin
        dato) va como None.
        """
        k = self.valores_constantes()

        canales = {clave: {nombre: self.numero_json(valor)
                           for nombre, valor in canal.items()}
                   for clave, canal in zip(KXL.CANALES_JSON,
                                           self.canales(k))}
        limites = self.limites_texturas(k, self.texturas(k))
        sin_tela = isinstance(self.__datos.tela, str)
        texturas = None if sin_tela else {
            clave: dict(zip(KXL.TEXTURAS_JSON, (self.numero_json(v)
                                                for v in valores)))
            for clave, valores in limites.items()}
        puntos = self.puntos_curva(k)
        curva = [{KXL.J_ZONA: p.nombre, KXL.J_TERCIO: p.tercio_ev,
                  KXL.J_ESPERADO: p.esperado, KXL.J_OBJETIVO: p.objetivo,
                  KXL.J_SENSOR: p.sensor, KXL.J_REVELADOR: p.revelador,
                  KXL.J_ENTRADA: p.entrada, KXL.J_SALIDA: p.salida,
                  KXL.J_PUNTO: (p.tercio_ev % k[KXL.C_TERCIO_POR_ZONA]) == 0}
                 for p in puntos]
        sensor = [abs(p.sensor - p.esperado) for p in puntos
                  if p.sensor is not None]
        revelador = [abs(p.revelador - p.esperado) for p in puntos
                     if p.revelador is not None]
        medias = {KXL.J_SENSOR: self.media(sensor),
                  KXL.J_REVELADOR: self.media(revelador)}
        return {KXL.J_CANALES: canales, KXL.J_TEXTURAS: texturas,
                KXL.J_CURVA: curva, KXL.J_DIFERENCIAS: medias}

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
    def puntos_curva(self, k: dict) -> list[PuntoCurva]:
        """
        La curva tonal en L*, zona a zona (de Z0 a ZX): lo que escribe el
        bloque 3 de Cálculo y dibuja la ficha PDF. Esperado: un paso de
        luz por zona desde la ZV, hasta el blanco; objetivo: C_L_POR_ZONA por
        zona; sensor: el verde de la zona entre el de la ZV (media);
        revelador: el de Datos (leído o estimado).
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
            puntos.append(PuntoCurva(
                tercio_ev=tercio_ev,
                nombre=self.nombre_zona(tercio_ev),
                luz_esperada=luz_esp,
                esperado=self.luz_a_lab(luz_esp, k),
                objetivo=k[KXL.C_L_POR_ZONA] * (
                    k[KXL.C_ZONA_ZV]
                    + (tercio_ev / k[KXL.C_TERCIO_POR_ZONA])),
                luz_sensor=luz_sen,
                sensor=None if (luz_sen is None)
                else self.luz_a_lab(luz_sen, k),
                luz_revelador=luz_rev,
                revelador=l_rev,
                entrada=None if (luz_rev is None) else self.curva(luz_rev, k),
                salida=self.curva(luz_esp, k)))
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
        recortado y si cumple cada criterio (sombras: textura/ruido de
        C_ROSE_TEXTURA en adelante hasta la ZV; luces: desde la ZV, textura
        conservada de C_TEXTURA_CONSERVADA y paño recortado de
        C_TELA_RECORTADO_MAX como mucho). None: sin dato o fuera de su lado.
        """
        n = (2 * KS.TERCIOS_LADO) + 1
        zv = KS.TERCIOS_LADO
        verde = 1
        esperado = [k[KXL.C_ZONA_ZV] + ((i - zv) / k[KXL.C_TERCIO_POR_ZONA])
                    for i in range(n)]
        textura, ruido, recortado = [], [], []
        for z in self.__datos.zonas:
            tela = z.telaDispRGB if z else None
            tarjeta = z.dispRGB[verde] if z else None
            if ((tela is None) or (tarjeta is None)
                    or (not math.isfinite(tarjeta))
                    or (not math.isfinite(tela[verde]))):
                textura.append(None)
                ruido.append(None)
            else:
                tx = math.sqrt(max(0.0, (tela[verde] ** 2) - (tarjeta ** 2)))
                textura.append(tx)
                ruido.append((tx / tarjeta) if (tarjeta > 0) else None)
            recorte = z.telaRecortadoRGB if z else None
            recortado.append(recorte[verde] if (recorte
                             and math.isfinite(recorte[verde])) else None)
        base = textura[zv]
        conservada = [(tx / base) if ((tx is not None) and base) else None
                      for tx in textura]

        # --- Sombras, de la ZV hacia abajo; luces, de la ZV hacia arriba.
        #     Un tercio sin dato no corta la cadena: deja pasar lo que
        #     viene del lado de la ZV
        sombras: list = [None] * n
        luces: list = [None] * n
        sin_recorte: list = [None] * n
        for i in range(zv, -1, -1):
            sigue = True if (i == zv) else sombras[i + 1]
            sombras[i] = (sigue if (ruido[i] is None) else
                          ((ruido[i] >= k[KXL.C_ROSE_TEXTURA]) and sigue))
        for i in range(zv, n):
            luz = True if (i == zv) else luces[i - 1]
            corte = True if (i == zv) else sin_recorte[i - 1]
            luces[i] = (luz if (conservada[i] is None) else
                        ((conservada[i] >= k[KXL.C_TEXTURA_CONSERVADA])
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
                KXL.T_CAB_SIN_RECORTE: sin_recorte}

    #
    def limites_texturas(self, k: dict, por_zona: dict[str, list]
                         ) -> dict[str, Tramo]:
        """
        Límites de la latitud de texturas (en zonas; si no se alcanzan, el
        texto de C_TEXTO_NO_ALCANZADO): sombras apreciables (donde la
        textura/ruido llega a C_ROSE_TEXTURA, entre los dos tercios vecinos y
        al tercio más próximo; sin dato en el de debajo, el tercio que
        cumple) y recomendadas (C_MARGEN_SOMBRAS tercios más arriba), luces
        apreciables (la última con la textura conservada) y recomendadas
        (la última sin pasar de C_TELA_RECORTADO_MAX, sin pasar de la
        apreciable) y las dos latitudes. Solo cuentan los tercios con dato.
        """
        no = self.__textos[KXL.V_NO_ALCANZADO]
        tercio = k[KXL.C_TERCIO_POR_ZONA]
        es = por_zona[KXL.T_CAB_ESPERADO]
        ruido = por_zona[KXL.T_CAB_TEXTURA_RUIDO]
        cumple = por_zona[KXL.T_CAB_CUMPLE_SOMBRAS]
        primera = next((i for i, c in enumerate(cumple)
                        if c and (ruido[i] is not None)), None)
        if primera is None:
            sombra = no
        elif (primera == 0) or (ruido[primera - 1] is None):
            sombra = es[primera]
        else:
            antes = primera - 1
            cruce = es[antes] + ((k[KXL.C_ROSE_TEXTURA] - ruido[antes])
                                 / (ruido[primera] - ruido[antes]) / tercio)
            # --- Al tercio más próximo; el medio, hacia arriba (como
            #     ROUND de Excel; round() de Python iría al par)
            sombra = math.floor((cruce * tercio) + 0.5) / tercio
        sombra_rec = ((sombra + (k[KXL.C_MARGEN_SOMBRAS] / tercio))
                      if isinstance(sombra, float) else sombra)
        luces = [e for e, c, v in zip(es, por_zona[KXL.T_CAB_CUMPLE_LUCES],
                                      por_zona[KXL.T_CAB_CONSERVADA])
                 if c and (v is not None)]
        luz = max(luces) if luces else no
        cortes = [e for e, c, v in zip(es, por_zona[KXL.T_CAB_SIN_RECORTE],
                                       por_zona[KXL.T_CAB_TELA_RECORTADO])
                  if c and (v is not None)]
        luz_rec = ((min(luz, max(cortes)) if isinstance(luz, float)
                    else max(cortes)) if cortes else no)
        return {KXL.T_APRECIABLE: (sombra, luz,
                                   self.latitud(luz, sombra, k)),
                KXL.T_RECOMENDADA: (sombra_rec, luz_rec,
                                    self.latitud(luz_rec, sombra_rec, k))}

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
            numero=KXL.ORDEN_GRAF.index(titulo) + 1,
            titulo=t[titulo])})
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
    def marcador_graf(color: str) -> dict:
        """ Marcador redondo de una serie de gráfica, en su color. """
        return {"type": "circle", "size": KXL.MEDIDA_MARCADOR,
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
