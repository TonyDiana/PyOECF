# -*- coding: utf-8 *-*
"""
    :Propósito: Libro Excel de resultados de una serie (pieza D), escrito
                desde cero con XlsxWriter: cada valor calculado va con su
                fórmula y su resultado (así se ve en la Vista protegida de
                Excel). Sin textos propios: los recibe ya traducidos
    :Autor:     Tony Diana
    :Versión:   26.10.15
"""

# cSpell:ignore xlsxwriter, CIELAB, Srgb

__all__ = ["KLI", "Libro", "PuntoCurva"]

# --- Bibliotecas estándar Python
import math
import re
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

# --- Bibliotecas externas
import xlsxwriter
from xlsxwriter.utility import xl_range_abs, xl_rowcol_to_cell
from xlsxwriter.worksheet import Worksheet

# --- Bibliotecas internas
from bib import clases
from .analisis import Analisis, ZonaMedida
from .constantes import COM as KCOM
from .kernel import OECF
from .secuencia import KS
from .teselas import KTE
from .transferencia import KTR, escala_mpx, senal_para_snr, snr_modelo
from .zonas import KP, zona_tercio


#
class KLI(clases.EnumMutable):
    """ Diseño del libro: fuentes, colores, medidas, nombres y textos. """

    # --- Fuente de todas las hojas salvo Análisis, y sus tamaños
    FUENTE = "Arial"
    TAMANO = 10
    TAMANO_TITULO = 14
    TAMANO_SECCION = 11

    # --- Colores del texto: dato (lo leído de los RAW), literal (lo
    #     escrito por diseño), fórmula y rótulo o nota
    COLOR_DATO = "#0000FF"
    COLOR_LITERAL = "#C55A11"
    COLOR_FORMULA = "#000000"
    COLOR_ROTULO = "#595959"

    # --- Tablas: cabecera, filas alternas y bordes finos, en la gama de
    #     verdes del libro (Tony, 2026-10-15; antes, azules). La cabecera,
    #     lo bastante oscura para que se lea el blanco
    CABECERA_FONDO = "#548235"
    CABECERA_TEXTO = "#FFFFFF"
    BANDA = "#E2EFDA"
    BORDE_TABLA = "#A9D08E"
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
    TERCIOS_LIBRO = ("", " 1/3", " 2/3")

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
    CANALES = 3
    COL_VALORES = 3

    # --- Columna del L* del revelador en su tabla de Datos, tras zona y
    #     tercios
    COL_REVELADOR = 2

    # --- Hojas, en su orden (claves de sus nombres en los textos)
    T_HOJA_ANALISIS = "hoja_analisis"
    T_HOJA_GRAFICOS = "hoja_graficos"
    T_HOJA_DATOS = "hoja_datos"
    T_HOJA_CONSTANTES = "hoja_constantes"
    T_HOJA_CALCULO = "hoja_calculo"
    T_HOJA_RECHAZADAS = "hoja_rechazadas"
    T_HOJA_IA = "hoja_ia"
    HOJAS = (T_HOJA_ANALISIS, T_HOJA_GRAFICOS, T_HOJA_DATOS,
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
    C_TERCIO_POR_ZONA = "TercioPorZona"
    C_FACTOR_ZONA = "FactorZona"
    C_LZV = "LZV"
    C_L_POR_ZONA = "LPorZona"
    C_RELACION_SR = "RelacionSR"
    C_SNR_MINIMA = "SNRMinima"
    C_SNR_EXCELENTE = "SNRExcelente"
    C_MPX_REFERENCIA = "MpxReferencia"
    C_TOLERANCIA_LINEAL = "ToleranciaLineal"
    C_UMBRAL_RECORTE = "UmbralRecorte"
    C_ROSE_TEXTURA = "RoseTextura"
    C_TEXTURA_CONSERVADA = "TexturaConservada"
    C_PANO_RECORTADO_MAX = "PanoRecortadoMax"
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
    U_FRACCION = "unidad_fraccion"
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
        (C_RELACION_SR, 1, U_VECES),
        (C_SNR_MINIMA, 10, U_VECES),
        (C_SNR_EXCELENTE, 40, U_VECES),
        (C_MPX_REFERENCIA, 8, U_MPX),
        (C_TOLERANCIA_LINEAL, KP.TOLERANCIA_LINEAL, U_ZONAS),
        (C_UMBRAL_RECORTE, KTE.UMBRAL_RECORTE, U_FRACCION),
        (C_ROSE_TEXTURA, 5, U_VECES),
        (C_TEXTURA_CONSERVADA, 0.5, U_FRACCION),
        (C_PANO_RECORTADO_MAX, 0.1, U_FRACCION),
        (C_MARGEN_SOMBRAS, 1, U_TERCIOS),
        (C_ANCHO_ZONA, 1, U_ZONAS),
        (C_LAB_ESCALA, KCOM.LAB_ESCALA, U_NUMERO),
        (C_LAB_DESPLAZA, KCOM.LAB_DESPLAZA, U_NUMERO),
        (C_LAB_UMBRAL, KCOM.LAB_UMBRAL, U_FRACCION),
        (C_LAB_PENDIENTE, KCOM.LAB_PENDIENTE, U_NUMERO),
        (C_SRGB_UMBRAL, 0.0031308, U_FRACCION),
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
    DERIVADAS = (
        (C_LUZ_POR_TERCIO, f"={C_FACTOR_ZONA}^(1/{C_TERCIO_POR_ZONA})",
         U_VECES),
        (C_LUZ_ZV, f"=IF({C_LZV}>{C_LAB_UMBRAL}*{C_LAB_PENDIENTE},"
                   f"(({C_LZV}+{C_LAB_DESPLAZA})/{C_LAB_ESCALA})^3,"
                   f"{C_LZV}/{C_LAB_PENDIENTE})", U_FRACCION))

    # --- Hoja Constantes: anchos (C a F; la de la unidad, oculta, como en
    #     el libro de Tony) y textos
    ANCHOS_CONSTANTES = (20.71, 12.71, None, 100.71)
    T_TITULO_CONSTANTES = "titulo_constantes"
    T_NOTA_CONSTANTES = "nota_constantes"
    T_CAB_NOMBRE = "cab_nombre"
    T_CAB_VALOR = "cab_valor"
    T_CAB_UNIDAD = "cab_unidad"
    T_CAB_QUE_ES = "cab_que_es"

    # --- Nota de SNRMinima: su primera línea lleva el valor de la
    #     constante, por fórmula (si se cambia, el texto no se desfasa)
    T_NOTA_SNR_ANTES = "nota_snr_antes"
    T_NOTA_SNR_DESPUES = "nota_snr_despues"
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
    PATRON_PRESET = r"PRESET(\d+)"
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
    T_PANO = "pano"
    T_NOTA_PANO = "nota_pano"
    T_CAB_PANO_REC_ROJO = "cab_pano_rec_rojo"
    T_CAB_PANO_REC_VERDE = "cab_pano_rec_verde"
    T_CAB_PANO_REC_AZUL = "cab_pano_rec_azul"
    T_NOTA_REVELADOR = "nota_revelador"
    T_CAB_REVELADOR = "cab_revelador"

    # --- Ruido y negro: origen del ruido (biboecf.KTE) y su texto, la
    #     comparación con las tapadas, el negro restado y sus avisos
    T_ORIGEN_CURVA = "origen_curva"
    ORIGEN_RUIDO = {KTE.ORIGEN_BORDE: T_ORIGEN_BORDE,
                    KTE.ORIGEN_TAPADAS: T_ORIGEN_TAPADAS,
                    KTE.ORIGEN_CURVA: T_ORIGEN_CURVA}
    T_COMPARACION_TAPADAS = "comparacion_tapadas"
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
    #     Libro.filas: se calculan al escribirla)
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
    F_PANO = "pano"

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
    T_CAB_MAXIMO = "cab_maximo"
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
    T_CAB_SNR_INGENIERIA = "cab_snr_ingenieria"
    T_CURVA = "curva"
    T_NOTA_CURVA_ANTES = "nota_curva_antes"
    T_NOTA_CURVA_MEDIO = "nota_curva_medio"
    T_NOTA_CURVA_DESPUES = "nota_curva_despues"
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

    # --- Resultados para el JSON (Libro.resultados): claves de los
    #     canales, sin idioma
    CANALES_JSON = ("R", "G", "B")

    # --- Claves de zonas_canal (por zona y canal) y de canales (por
    #     canal: lo que da el bloque 1 de Cálculo)
    Z_ESPERADO = "esperado"
    Z_OBTENIDO = "obtenido"
    Z_DESVIACION = "desviacion"
    Z_RECORTADO = "recortado"
    R_MEDIA_ZV = "media_zv"
    R_MAXIMO = "maximo"
    R_TECHO = "techo"
    R_SUELO = "suelo"
    R_RANGO = "rango"
    R_ULTIMO_LINEAL = "ultimo_lineal"
    R_PRIMER_RECORTADO = "primer_recortado"
    R_SUELO_SUGERIDO = "suelo_sugerido"
    R_SUELO_EXCELENTE = "suelo_excelente"
    R_LATITUD = "latitud_sugerida"

    # --- Claves de los resultados en el JSON (Libro.resultados)
    J_CANALES = "canales"
    J_TEXTURAS = "latitud_texturas"
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
    T_CAB_PANO_RECORTADO = "cab_pano_recortado"
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

    # --- Filas de Cálculo que leen otras hojas (claves de Libro.filas)
    F_CANALES = "canales"
    F_TERCIOS = "tercios"
    F_CURVA = "curva"
    F_LIMITES = "limites"

    # --- Hoja Análisis: su propio estilo (el de Tony): Verdana, anillo
    #     más claro y otros anchos (del cuadro de diálogo de Excel). Dos
    #     tarjetas, una al lado de la otra: la izquierda (cabecera, ruido
    #     y negro, balances) y la derecha (sugerencia y tabla por zona).
    #     Entre las dos, relleno, anillo y relleno
    FUENTE_ANALISIS = "Verdana"
    TAMANO_ANALISIS = 11
    TAMANO_ANALISIS_TITULO = 16
    TAMANO_ANALISIS_TABLA = 10
    TAMANO_ANALISIS_NOTA = 9
    ANILLO_ANALISIS = "#D9D9D9"
    ANCHO_ANILLO_ANALISIS = 9.0
    ANCHO_RELLENO_ANALISIS = 1.86
    ANCHOS_ANALISIS = (22.57, 9.29) + (12.29,) * 5
    ANCHOS_ANALISIS_DERECHA = (10.71,) + (12.29,) * 6
    ENTRE_TARJETAS = 3

    # --- Rejilla de Análisis: todas las filas del mismo alto (el de Excel
    #     por defecto), porque las dos tarjetas comparten filas; lo que
    #     necesita más ocupa varias combinadas: el título, las cabeceras
    #     (dos filas; tres, las altas) y las notas y los rótulos largos,
    #     según sus líneas. Alto de una línea (puntos) de las notas
    #     (Verdana 9) y de las tablas (Verdana 10), y cuánto más ancha es
    #     la letra de las tablas que la de Excel
    ALTO_REJILLA = 15
    FILAS_TITULO_ANALISIS = 2
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
    #     (clave de Libro.filas), su columna (tras la de la zona) y color
    #     de lo estimado (los tercios sin L* leído, entre las dos zonas
    #     enteras vecinas)
    F_LEIDO = "leido"
    COL_LEIDO = 1
    COLOR_ESTIMADO = "#C2185B"
    T_CAB_L_LEIDO = "cab_l_leido"
    T_ESTIMADO = "estimado"
    NUM_LSTAR = '0.0" L*"'
    NUM_BITS = '0" bits"'
    T_TITULO_ANALISIS = "titulo_analisis"
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
    T_NOTA_TEXTURAS_ANALISIS = "nota_texturas_analisis"
    T_SIN_PANO = "sin_pano"

    # --- Zonas de la latitud de texturas en Análisis: en tercios (8 1/3)
    NUM_TERCIOS = "# ?/3"

    # --- Hoja Gráficos: seis huecos (dos columnas × tres filas) de 6
    #     columnas × 18 filas con borde gris, separados por una columna y
    #     una fila; cada gráfica, a 3 px de la esquina de su hueco
    ANCHOS_GRAFICOS = (15.0,) * 6 + (3.0,) + (15.0,) * 6
    COLUMNAS_HUECO = 6
    FILAS_HUECO = 18
    FILA_HUECOS = 5
    BORDE_HUECO = "#7F7F7F"
    TAMANO_GRAFICA = (654, 354)
    MARGEN_GRAFICA = 3

    # --- Colores y trazos de las gráficas: canales, esperado (gris
    #     grueso, algo transparente), objetivo, sensor y barras lilas
    COLORES_CANALES = ("#C0392B", "#2E8B57", "#1F5FA8")
    COLOR_ESPERADO = "#808080"
    TRANSPARENCIA_ESPERADO = 60
    ANCHO_ESPERADO = 3
    COLOR_OBJETIVO = "#7B3FA0"
    COLOR_SENSOR = "#E08A1E"
    COLOR_BARRAS = "#B39DDB"
    ANCHO_BARRAS = 3
    COLOR_NEGATIVO = "#C0392B"
    TAMANO_MARCADOR = 4
    ROTACION_ZONAS = -45
    TAMANO_ZONAS = 8

    # --- Ejes: (mínimo, máximo, paso, formato de los números; si no, los
    #     ejes copian el de las celdas, con decimales de sobra). El
    #     segundo eje de la de esperado y obtenido, en pasos respecto a
    #     la Z-V: el primero menos ZonaZV
    EJE_ZONAS = (-4, 10, 1, "0")
    EJE_DESV_LINEAL = (-0.2, 0.2, 0.05, "+0.00;-0.00;0")
    EJE_DESV_COMPLETA = (-1.5, 0.5, 0.5, "+0.0;-0.0;0")
    EJE_SNR = (1, 1000, None, "0")
    BASE_EJE_SNR = 10
    EJE_LSTAR = (0, 100, 20, "0")
    EJE_DIF_LSTAR = (-15, 10, 5, "+0;-0;0")

    # --- Textos de Gráficos
    T_TITULO_GRAFICOS = "titulo_graficos"
    T_NOTA_GRAFICOS = "nota_graficos"
    T_G_ESPERADO = "g_esperado"
    T_G_DESV_LINEAL = "g_desv_lineal"
    T_G_DESV_COMPLETA = "g_desv_completa"
    T_G_SNR = "g_snr"
    T_G_CURVA = "g_curva"
    T_G_DIFERENCIA = "g_diferencia"

    # --- Orden de las gráficas en la hoja (de izquierda a derecha y de
    #     arriba abajo): primero lo que más interesa al estudiante (Tony).
    #     Su número en el título sale de aquí
    ORDEN_GRAFICAS = (T_G_CURVA, T_G_DIFERENCIA, T_G_ESPERADO,
                      T_G_DESV_LINEAL, T_G_DESV_COMPLETA, T_G_SNR)
    FORMATO_TITULO_GRAFICA = "{numero}. {titulo}"
    T_EJE_ZONA = "eje_zona"
    T_EJE_SENAL = "eje_senal"
    T_EJE_PASOS = "eje_pasos"
    T_EJE_DESVIACION = "eje_desviacion"
    T_EJE_SNR = "eje_snr"
    T_EJE_LSTAR = "eje_lstar"
    T_EJE_DIF_LSTAR = "eje_dif_lstar"
    T_S_MINIMO = "s_minimo"
    T_S_EXCELENTE = "s_excelente"
    T_S_INGENIERIA = "s_ingenieria"
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
    T_MOTIVO_DISPERSION = "motivo_dispersion"
    T_MOTIVO_ASIMETRIA = "motivo_asimetria"
    MOTIVOS = ((KTE.RECHAZO_NIVEL, T_MOTIVO_NIVEL, "#E08A1E"),
               (KTE.RECHAZO_DISPERSION, T_MOTIVO_DISPERSION, "#1F5FA8"),
               (KTE.RECHAZO_ASIMETRIA, T_MOTIVO_ASIMETRIA, "#7B3FA0"))
    EJE_POSICION = (0, 10, 1, "0")

    # --- Qué significa cada motivo (junto a su recuento): claves de sus
    #     textos, que llevan los umbrales de biboecf.KTE
    T_EXPLICA_NIVEL = "explica_nivel"
    T_EXPLICA_DISPERSION = "explica_dispersion"
    T_EXPLICA_ASIMETRIA = "explica_asimetria"
    EXPLICA_MOTIVO = {KTE.RECHAZO_NIVEL: T_EXPLICA_NIVEL,
                      KTE.RECHAZO_DISPERSION: T_EXPLICA_DISPERSION,
                      KTE.RECHAZO_ASIMETRIA: T_EXPLICA_ASIMETRIA}
    NUM_DESVIACION = "+0.00;-0.00;0"
    T_TITULO_RECHAZADAS = "titulo_rechazadas"
    T_NOTA_RECHAZADAS = "nota_rechazadas"
    T_RECUENTO = "recuento"
    T_CAB_CONCEPTO = "cab_concepto"
    T_TESELAS_TARJETA = "teselas_tarjeta"
    T_TESELAS_RECHAZADAS = "teselas_rechazadas"
    T_PORCENTAJE = "porcentaje"
    T_POR_MOTIVO = "por_motivo"
    T_G_RECHAZADAS = "g_rechazadas"
    T_DATOS_GRAFICO = "datos_grafico"
    T_CAB_POSICION = "cab_posicion"
    T_CAB_MOTIVO = "cab_motivo"
    T_CAB_DESVIACION = "cab_desviacion"

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
    Lightroom (de 0 a EscalaCurva; la entrada, None sin revelador).
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
class Libro(object):
    """
    Libro Excel de una serie. Se crea con la ruta, los textos ya
    traducidos ({clave de KLI: texto}) y lo medido en los RAW (Analisis);
    escribir() lo graba.
    """

    __slots__ = ["__datos", "__filas", "__formatos", "__hojas", "__libro",
                 "__revelador", "__rotulos", "__textos"]

    #
    def __init__(self, ruta: Path, textos: dict[str, str],
                 datos: Analisis) -> None:

        # --- Variables de instancia. filas: dónde quedó cada bloque de
        #     Datos (KLI.F_*), para las fórmulas de las demás hojas
        self.__textos: dict[str, str] = textos
        self.__datos: Analisis = datos
        self.__libro = xlsxwriter.Workbook(str(ruta))
        self.__formatos: dict[tuple, object] = {}
        self.__hojas: dict[str, Worksheet] = {}
        self.__filas: dict[str, int] = {}

        # --- Texto de la primera columna de las filas de Datos que lee
        #     Análisis (el ruido y el negro), {fila: texto}
        self.__rotulos: dict[int, str] = {}

        # --- L* del revelador por zona, como sale en Datos: el leído y,
        #     en los tercios sin él, el estimado (None: sin dato)
        self.__revelador: list[float | None] = self.revelador_estimado()

        # --- Fuente por defecto de todas las celdas
        self.__libro.formats[0].set_font_name(KLI.FUENTE)
        self.__libro.formats[0].set_font_size(KLI.TAMANO)

        # --- Las hojas, en su orden, antes de escribir ninguna: las
        #     fórmulas de unas leen de otras
        for clave in KLI.HOJAS:
            self.__hojas[clave] = self.__libro.add_worksheet(textos[clave])

    #
    # --- Métodos públicos
    #
    # region Métodos públicos

    #
    @property
    def analisis(self) -> Analisis:
        """ Saber lo medido en los RAW con que se hace el libro. """
        return self.__datos

    #
    def escribir(self) -> None:
        """ Escribe todas las hojas y graba el libro. """
        self.hoja_constantes()
        self.hoja_datos()
        self.hoja_calculo()
        self.hoja_analisis()
        self.revelador_datos()
        self.hoja_graficos()
        self.hoja_rechazadas()
        self.hoja_ia()
        for clave in KLI.HOJAS_OCULTAS:
            self.__hojas[clave].hide()
        self.__libro.close()

    #
    def hoja_datos(self) -> None:
        """
        Hoja Datos: lo leído de los RAW, sin cálculos salvo la media de
        las Z-V. La serie por zonas, las demás Z-V, su media, el ruido de
        lectura y la tabla del L* medido (vacía: la rellena el usuario).
        """
        t, d = self.__textos, self.__datos
        hoja = self.__hojas[KLI.T_HOJA_DATOS]
        fila, col = KLI.FILA_INICIO, KLI.COLUMNA_INICIO
        canales = (t[KLI.T_CAB_ROJO], t[KLI.T_CAB_VERDE], t[KLI.T_CAB_AZUL])
        cabecera = ((t[KLI.T_CAB_ZONA], t[KLI.T_CAB_TERCIOS],
                     t[KLI.T_CAB_ARCHIVO]) + canales
                    + (t[KLI.T_CAB_DISP_ROJO], t[KLI.T_CAB_DISP_VERDE],
                       t[KLI.T_CAB_DISP_AZUL]))
        self.titulo(hoja, fila, col, t[KLI.T_TITULO_DATOS],
                    t[KLI.T_NOTA_DATOS],
                    KLI.ANCHOS_DATOS)

        # --- Serie por zonas: una fila por zona, de Z0 a ZX
        fila += 3
        hoja.write(fila, col, t[KLI.T_SERIE_ZONAS], self.seccion())
        fila += 1
        self.cabecera(hoja, fila, col, cabecera)
        hoja.set_row(fila, KLI.ALTO_CABECERA)
        self.__filas[KLI.F_ZONAS] = fila + 1
        for i, toma in enumerate(d.zonas):
            fila += 1
            self.fila_serie(hoja, fila, col, i - KS.TERCIOS_LADO, toma,
                            i % 2 == 0)

        # --- Las demás Z-V de la serie (huecos vacíos si hay menos)
        fila += 2
        hoja.write(fila, col, t[KLI.T_CONTROL], self.seccion())
        fila += 1
        self.cabecera(hoja, fila, col, cabecera)
        hoja.set_row(fila, KLI.ALTO_CABECERA)
        self.__filas[KLI.F_CONTROL] = fila + 1
        control = d.control[:KLI.CONTROLES]
        for i in range(KLI.CONTROLES):
            fila += 1
            toma = control[i] if i < len(control) else None
            self.fila_serie(hoja, fila, col, 0, toma, i % 2 == 0)

        # --- Media de todas las Z-V: la de la serie y las de control
        fila += 2
        hoja.write(fila, col, t[KLI.T_MEDIA_ZV], self.seccion())
        fila += 1
        self.__filas[KLI.F_MEDIA] = fila
        literal = self.celda(KLI.COLOR_LITERAL, True, "center")
        hoja.write(fila, col, self.nombre_zona(0), literal)
        hoja.write_blank(fila, col + 1, None, literal)
        hoja.write(fila, col + 2, t[KLI.T_MEDIA],
                   self.celda(KLI.COLOR_ROTULO, True, "center"))
        # --- Solo entran las Z-V de control cuyo verde se aparta de la
        #     ZV como mucho ToleranciaLineal (si no, la luz cambió): una
        #     fórmula matricial, que lee la constante
        fila_zv = self.__filas[KLI.F_ZONAS] + KS.TERCIOS_LADO
        desde = self.__filas[KLI.F_CONTROL]
        hasta = desde + KLI.CONTROLES - 1
        c_verde = col + KLI.COL_VALORES + 1
        verdes = (f"{xl_rowcol_to_cell(desde, c_verde, False, True)}:"
                  f"{xl_rowcol_to_cell(hasta, c_verde, False, True)}")
        verde_zv = xl_rowcol_to_cell(fila_zv, c_verde, False, True)
        entra = (f"IF(ISNUMBER({verdes}),IF(ABS(LOG({verdes}/{verde_zv},"
                 f"{KLI.C_FACTOR_ZONA}))<={KLI.C_TOLERANCIA_LINEAL},1,0),0)")
        zv = d.zonas[KS.TERCIOS_LADO]
        desviados = d.controlesDesviados
        valores = [v for v in ([zv] + [z for z in control
                                        if z not in desviados])
                   if v is not None]
        for j in range(2 * KLI.CANALES):
            c = col + KLI.COL_VALORES + j
            celdas = (f"{xl_rowcol_to_cell(desde, c)}:"
                      f"{xl_rowcol_to_cell(hasta, c)}")
            numeros = [(v.nivelRGB + v.dispersionRGB)[j] for v in valores]
            hoja.write_array_formula(
                fila, c, fila, c,
                f"{{=({xl_rowcol_to_cell(fila_zv, c)}+SUM({entra}*"
                f"IF(ISNUMBER({celdas}),{celdas},0)))/(1+SUM({entra}))}}",
                self.celda(KLI.COLOR_FORMULA, True, "center",
                           KLI.NUM_UNO if j < KLI.CANALES
                           else KLI.NUM_TRES),
                sum(numeros) / len(numeros) if numeros else "")
        dispersion_zv = [sum(v.dispersionRGB[j] for v in valores)
                         / len(valores) if valores else None
                         for j in range(KLI.CANALES)]

        # --- Ruido de lectura por canal, con su origen (o que no se midió)
        fila += 2
        hoja.write(fila, col, t[KLI.T_RUIDO], self.seccion())
        fila += 1
        self.cabecera(hoja, fila, col, (t[KLI.T_CAB_ORIGEN], "", "")
                      + canales)
        fila += 1
        self.__filas[KLI.F_RUIDO] = fila
        ruido = d.ruidoRGB
        origen = (t[KLI.ORIGEN_RUIDO[d.origen_ruido]] if ruido
                  else t[KLI.T_SIN_RUIDO])
        self.rotulo_fila(hoja, fila, col, origen, literal)
        self.__rotulos[fila] = origen
        self.fila_canales(hoja, fila, col, ruido, True, KLI.NUM_DOS)

        # --- Si el ruido es del borde y además hay tapadas, las tapadas,
        #     para comparar; y el negro restado, con su origen
        filas_extra = []
        if d.origen_ruido == KTE.ORIGEN_BORDE and d.ruidoTapadasRGB:
            filas_extra.append((KLI.F_RUIDO_TAPADAS,
                                t[KLI.T_COMPARACION_TAPADAS],
                                d.ruidoTapadasRGB, KLI.NUM_DOS))
        filas_extra.append((KLI.F_NEGRO, t[KLI.ORIGEN_NEGRO[d.origen_negro]],
                            d.negroRGB, KLI.NUM_ENTERO))
        for i, (clave, texto, valores, numero) in enumerate(filas_extra):
            fila += 1
            banda = i % 2 == 1
            self.__filas[clave] = fila
            literal_i = self.celda(KLI.COLOR_LITERAL, banda, "center")
            self.rotulo_fila(hoja, fila, col, texto, literal_i)
            self.__rotulos[fila] = texto
            self.fila_canales(hoja, fila, col, valores, banda, numero)

        # --- Curva de transferencia del ruido (de las zonas): lectura,
        #     ganancia y parte proporcional por canal; el ruido aleatorio
        #     de la Z-V (con una de control) y, por fórmula, lo fijo (lo
        #     que queda de la dispersión media de las Z-V); y los
        #     megapíxeles del sensor (para normalizar la señal/ruido)
        fila += 2
        hoja.write(fila, col, t[KLI.T_TRANSFERENCIA], self.seccion())
        self.nota(hoja, fila + 1, col, t[KLI.T_NOTA_TRANSFERENCIA],
                  KLI.ANCHOS_DATOS)
        fila += 2
        self.cabecera(hoja, fila, col, (t[KLI.T_CAB_CONCEPTO], "", "")
                      + canales)
        curvas = d.transferenciaRGB
        aleatorio = d.aleatorioRGB
        filas_curva = (
            (KLI.F_LECTURA, KLI.T_LECTURA, KLI.NUM_DOS,
             tuple(c.lectura for c in curvas) if curvas else None),
            (KLI.F_GANANCIA, KLI.T_GANANCIA, KLI.NUM_TRES,
             tuple(c.ganancia for c in curvas) if curvas else None),
            (KLI.F_PROPORCIONAL, KLI.T_PROPORCIONAL, KLI.NUM_PORCENTAJE,
             tuple(c.proporcional for c in curvas) if curvas else None),
            (KLI.F_ALEATORIO, KLI.T_ALEATORIO_ZV, KLI.NUM_CUATRO,
             aleatorio))
        for i, (clave, texto, numero, valores_curva) in enumerate(
                filas_curva):
            fila += 1
            banda = i % 2 == 0
            self.__filas[clave] = fila
            literal_i = self.celda(KLI.COLOR_LITERAL, banda, "center")
            self.rotulo_fila(hoja, fila, col, t[texto], literal_i)
            self.fila_canales(hoja, fila, col, valores_curva, banda, numero)

        # --- Lo fijo de la Z-V: raíz de (dispersión media² − aleatorio²)
        fila += 1
        banda = len(filas_curva) % 2 == 0
        self.__filas[KLI.F_FIJO] = fila
        literal_i = self.celda(KLI.COLOR_LITERAL, banda, "center")
        self.rotulo_fila(hoja, fila, col, t[KLI.T_FIJO_ZV], literal_i)
        formula_i = self.celda(KLI.COLOR_FORMULA, banda, "center",
                               KLI.NUM_CUATRO)
        for j in range(KLI.CANALES):
            c = col + KLI.COL_VALORES + j
            total = xl_rowcol_to_cell(self.__filas[KLI.F_MEDIA],
                                      c + KLI.CANALES)
            azar = xl_rowcol_to_cell(self.__filas[KLI.F_ALEATORIO], c)
            hoja.write_formula(
                fila, c, f'=IF(AND(ISNUMBER({total}),ISNUMBER({azar})),'
                         f'SQRT(MAX(0,{total}^2-{azar}^2)),"")', formula_i,
                math.sqrt(max(0.0, dispersion_zv[j] ** 2 - aleatorio[j] ** 2))
                if aleatorio and dispersion_zv[j] is not None else "")

        # --- Megapíxeles del sensor (un solo valor, en la primera columna)
        fila += 1
        banda = (len(filas_curva) + 1) % 2 == 0
        self.__filas[KLI.F_MPX] = fila
        literal_i = self.celda(KLI.COLOR_LITERAL, banda, "center")
        self.rotulo_fila(hoja, fila, col, t[KLI.T_MPX_SENSOR], literal_i)
        hoja.write_number(fila, col + KLI.COL_VALORES,
                          d.alto * d.ancho / KTR.PIXELES_MPX,
                          self.celda(KLI.COLOR_DATO, banda, "center",
                                     KLI.NUM_UNO))

        # --- Balances de blancos de la cámara (sin repetir los iguales):
        #     balance, archivo, Kelvin de la cámara y reales y los
        #     multiplicadores rojo y azul (el verde es 1)
        fila += 2
        hoja.write(fila, col, t[KLI.T_BALANCES], self.seccion())
        self.nota(hoja, fila + 1, col, t[KLI.T_NOTA_BALANCES],
                  KLI.ANCHOS_DATOS)
        fila += 2
        self.cabecera(hoja, fila, col, (
            t[KLI.T_CAB_BALANCE], "", t[KLI.T_CAB_ARCHIVO],
            t[KLI.T_CAB_KELVIN_ANOTADO], t[KLI.T_CAB_KELVIN_MEDIDO],
            t[KLI.T_CAB_MULT_ROJO], t[KLI.T_CAB_MULT_AZUL]))
        hoja.set_row(fila, KLI.ALTO_CABECERA)
        self.__filas[KLI.F_BALANCES] = fila + 1
        balances = d.balancesDistintos
        if not balances:
            fila += 1
            hoja.write(fila, col, t[KLI.T_SIN_BALANCES], literal)
        for i, balance in enumerate(balances):
            fila += 1
            banda = i % 2 == 0
            dato = self.celda(KLI.COLOR_DATO, banda, "center")
            hoja.write(fila, col, self.nombre_balance(balance.nombre), dato)
            hoja.write_blank(fila, col + 1, None, dato)
            hoja.write(fila, col + 2, balance.archivo, dato)
            valores = ((balance.kelvin_camara, KLI.NUM_ENTERO),
                       (balance.kelvin, KLI.NUM_ENTERO),
                       (balance.multiplicadores[0]
                        if balance.multiplicadores else None, KLI.NUM_TRES),
                       (balance.multiplicadores[2]
                        if balance.multiplicadores else None, KLI.NUM_TRES))
            for j, (valor, numero) in enumerate(valores):
                formato = self.celda(KLI.COLOR_DATO, banda, "center", numero)
                if valor is None:
                    hoja.write_blank(fila, col + KLI.COL_VALORES + j, None,
                                     formato)
                else:
                    hoja.write_number(fila, col + KLI.COL_VALORES + j, valor,
                                      formato)

        # --- Paño por zona: dispersión y fracción recortada de cada canal
        #     (en blanco sin paño). Lo lee la latitud de texturas
        fila += 2
        hoja.write(fila, col, t[KLI.T_PANO], self.seccion())
        self.nota(hoja, fila + 1, col, t[KLI.T_NOTA_PANO],
                  KLI.ANCHOS_DATOS)
        fila += 2
        self.cabecera(hoja, fila, col, (
            t[KLI.T_CAB_ZONA], t[KLI.T_CAB_TERCIOS], t[KLI.T_CAB_ARCHIVO],
            t[KLI.T_CAB_DISP_ROJO], t[KLI.T_CAB_DISP_VERDE],
            t[KLI.T_CAB_DISP_AZUL], t[KLI.T_CAB_PANO_REC_ROJO],
            t[KLI.T_CAB_PANO_REC_VERDE], t[KLI.T_CAB_PANO_REC_AZUL]))
        hoja.set_row(fila, KLI.ALTO_CABECERA)
        self.__filas[KLI.F_PANO] = fila + 1
        for i, toma in enumerate(d.zonas):
            fila += 1
            banda = i % 2 == 0
            self.zona_y_tercios(hoja, fila, col, i - KS.TERCIOS_LADO, banda)
            dato = self.celda(KLI.COLOR_DATO, banda, "center")
            archivo = col + KLI.COL_VALORES - 1
            if toma is None:
                hoja.write_blank(fila, archivo, None, dato)
            else:
                hoja.write(fila, archivo, toma.archivo, dato)
            for desp, valores, numero in (
                    (0, toma.panoDispersionRGB if toma else None,
                     KLI.NUM_TRES),
                    (KLI.CANALES, toma.panoRecortadoRGB if toma else None,
                     KLI.NUM_PORCENTAJE)):
                self.fila_canales(hoja, fila, col + desp, valores, banda,
                                  numero)

        # --- L* del revelador por zona: lee el L* leído de Análisis y
        #     estima los tercios que no lo tienen. Sus fórmulas, en
        #     revelador_datos (leen de Cálculo y de Análisis)
        fila += 2
        hoja.write(fila, col, t[KLI.T_REVELADOR], self.seccion())
        self.nota(hoja, fila + 1, col, t[KLI.T_NOTA_REVELADOR],
                  KLI.ANCHOS_DATOS)
        fila += 2
        self.cabecera(hoja, fila, col, (t[KLI.T_CAB_ZONA],
                                        t[KLI.T_CAB_TERCIOS],
                                        t[KLI.T_CAB_REVELADOR]))
        self.__filas[KLI.F_REVELADOR] = fila + 1
        for i in range(2 * KS.TERCIOS_LADO + 1):
            fila += 1
            banda = i % 2 == 0
            tercio_ev = i - KS.TERCIOS_LADO
            self.zona_y_tercios(hoja, fila, col, tercio_ev, banda)

        self.marco(hoja, ((fila, KLI.ANCHOS_DATOS),))

    #
    def hoja_constantes(self) -> None:
        """
        Hoja Constantes: cada constante del método con su nombre definido
        en el libro, las derivadas (con fórmula), la nota de SNRMinima y
        la leyenda de los colores.
        """
        t = self.__textos
        hoja = self.__hojas[KLI.T_HOJA_CONSTANTES]
        nombre_hoja = t[KLI.T_HOJA_CONSTANTES]
        fila, col = KLI.FILA_INICIO, KLI.COLUMNA_INICIO

        self.titulo(hoja, fila, col, t[KLI.T_TITULO_CONSTANTES],
                    t[KLI.T_NOTA_CONSTANTES],
                    KLI.ANCHOS_CONSTANTES)
        fila += 3
        self.cabecera(hoja, fila, col, (t[KLI.T_CAB_NOMBRE],
                                        t[KLI.T_CAB_VALOR],
                                        t[KLI.T_CAB_UNIDAD],
                                        t[KLI.T_CAB_QUE_ES]))

        # --- Una fila por constante, por orden alfabético; las derivadas,
        #     con su fórmula y su valor calculado (si no, el archivo
        #     guarda 0 y un visor que no recalcula lo muestra). «Qué es»,
        #     partido en líneas
        k = self.valores_constantes()
        ancho_que_es = KLI.ANCHOS_CONSTANTES[3]
        for i, (nombre, valor, unidad) in enumerate(sorted(
                KLI.CONSTANTES + KLI.DERIVADAS,
                key=lambda constante: constante[0].casefold())):
            fila += 1
            banda = i % 2 == 0
            es_formula = isinstance(valor, str) and valor.startswith("=")
            hoja.write(fila, col, nombre,
                       self.celda(KLI.COLOR_LITERAL, banda, "left"))
            if es_formula:
                hoja.write_formula(
                    fila, col + 1, valor,
                    self.celda(KLI.COLOR_FORMULA, banda, "center",
                               KLI.NUM_CUATRO), k[nombre])
            else:
                hoja.write(fila, col + 1,
                           t[valor] if isinstance(valor, str) else valor,
                           self.celda(KLI.COLOR_LITERAL, banda, "center"))
            hoja.write(fila, col + 2, t[unidad],
                       self.celda(KLI.COLOR_ROTULO, banda, "center"))
            hoja.write(fila, col + 3, t[nombre],
                       self.celda(KLI.COLOR_ROTULO, banda, "left",
                                  text_wrap=True, valign="top"))
            lineas = self.lineas(t[nombre], ancho_que_es)
            if lineas > 1:
                hoja.set_row(fila, KLI.ALTO_LINEA * lineas)
            self.__libro.define_name(
                nombre, f"='{nombre_hoja}'!"
                        f"{xl_rowcol_to_cell(fila, col + 1, True, True)}")

        # --- Nota de SNRMinima: la primera línea, con su valor por fórmula
        fila += 2
        snr = KLI.C_SNR_MINIMA
        valor_snr = dict((c[0], c[1]) for c in KLI.CONSTANTES)[snr]
        antes, despues = t[KLI.T_NOTA_SNR_ANTES], t[KLI.T_NOTA_SNR_DESPUES]
        self.nota(hoja, fila, col, f"{antes}{valor_snr}{despues}",
                  KLI.ANCHOS_CONSTANTES,
                  self.formato(font_color=KLI.COLOR_ROTULO, bold=True,
                               text_wrap=True, valign="top"),
                  f"={self.cadena(antes)}&{snr}&{self.cadena(despues)}")
        for clave in (KLI.T_NOTA_SNR_ISO, KLI.T_NOTA_SNR_USUARIO):
            fila += 1
            self.nota(hoja, fila, col, t[clave], KLI.ANCHOS_CONSTANTES)

        # --- Leyenda: cada tipo de texto en su color
        fila += 2
        hoja.write(fila, col, t[KLI.T_LEYENDA], self.seccion())
        for clave, color in ((KLI.T_LEYENDA_DATO, KLI.COLOR_DATO),
                             (KLI.T_LEYENDA_LITERAL, KLI.COLOR_LITERAL),
                             (KLI.T_LEYENDA_FORMULA, KLI.COLOR_FORMULA),
                             (KLI.T_LEYENDA_ROTULO, KLI.COLOR_ROTULO)):
            fila += 1
            hoja.write(fila, col, t[clave], self.texto(color, negrita=True))

        self.marco(hoja, ((fila, KLI.ANCHOS_CONSTANTES),))

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
        hoja = self.__hojas[KLI.T_HOJA_CALCULO]
        fila, col = KLI.FILA_INICIO, KLI.COLUMNA_INICIO
        k = self.valores_constantes()
        n = 2 * KS.TERCIOS_LADO + 1
        cols_datos = [KLI.COLUMNA_INICIO + KLI.COL_VALORES + j
                      for j in range(2 * KLI.CANALES)]
        medias = self.medias_zv()
        maximos = self.maximos()
        disp = [z.dispersionRGB if z else None for z in d.zonas]
        self.titulo(hoja, fila, col, t[KLI.T_TITULO_CALCULO],
                    t[KLI.T_NOTA_CALCULO],
                    KLI.ANCHOS_CALCULO)

        # --- Posiciones de los bloques (los tres se leen entre sí)
        fila_b1 = fila + 6
        fila_b2 = fila_b1 + KLI.CANALES + 4
        fila_b3 = fila_b2 + n + 4
        f[KLI.F_CANALES], f[KLI.F_TERCIOS], f[KLI.F_CURVA] = (
            fila_b1, fila_b2, fila_b3)
        celda = xl_rowcol_to_cell

        def rango(c: int) -> str:
            return (f"{celda(fila_b2, c, True, True)}:"
                    f"{celda(fila_b2 + n - 1, c, True, True)}")

        # --- Bloque 2 primero en Python (zonas_canal): lo usa el bloque 1
        #     (sus resultados, de canales)
        por_zona = self.zonas_canal(k)
        esperado, obtenido, desviacion, recortado = (
            por_zona[clave] for clave in (KLI.Z_ESPERADO, KLI.Z_OBTENIDO,
                                          KLI.Z_DESVIACION, KLI.Z_RECORTADO))
        resultados = self.canales(k)
        snr = [[None if q is None else (1 / q[j] if q[j] > 0
                                        else t[KLI.V_SATURADO])
                for q in disp] for j in range(KLI.CANALES)]

        # --- Bloque 1: por canal (sección, nota y cabecera, como el 2)
        fila = fila_b1 - 3
        hoja.write(fila, col, t[KLI.T_POR_CANAL], self.seccion())
        self.nota(hoja, fila + 1, col, t[KLI.T_NOTA_POR_CANAL],
                  KLI.ANCHOS_CALCULO)
        self.cabecera(hoja, fila_b1 - 1, col, tuple(t[c] for c in (
            KLI.T_CAB_CANAL, KLI.T_CAB_ZV_MEDIA, KLI.T_CAB_MAXIMO,
            KLI.T_CAB_TECHO, KLI.T_CAB_SUELO, KLI.T_CAB_RANGO,
            KLI.T_CAB_LINEAL, KLI.T_CAB_RECORTADO, KLI.T_CAB_SUELO_SNR,
            KLI.T_CAB_SUELO_EXCELENTE, KLI.T_CAB_LATITUD)))
        hoja.set_row(fila_b1 - 1, KLI.ALTO_CABECERA_ALTA)
        c_desv = col + 6
        c_rec = col + 9
        for j in range(KLI.CANALES):
            r = fila_b1 + j
            banda = j % 2 == 0
            uno = self.celda(KLI.COLOR_FORMULA, banda, "center",
                             KLI.NUM_UNO)
            dos = self.celda(KLI.COLOR_FORMULA, banda, "center",
                             KLI.NUM_DOS)
            hoja.write(r, col, t[KLI.T_CANALES[j]],
                       self.celda(KLI.COLOR_LITERAL, banda, "center"))
            media = self.ref(KLI.T_HOJA_DATOS, f[KLI.F_MEDIA],
                             cols_datos[j])
            canal = resultados[j]
            hoja.write_formula(r, col + 1, f"={media}", uno,
                               canal[KLI.R_MEDIA_ZV])
            columna = self.ref(KLI.T_HOJA_DATOS, f[KLI.F_ZONAS],
                               cols_datos[j], True, False)
            hasta = celda(f[KLI.F_ZONAS] + n - 1, cols_datos[j], True)
            hoja.write_formula(r, col + 2, f"=MAX({columna}:{hasta})", uno,
                               canal[KLI.R_MAXIMO])
            dz, ez = celda(r, col + 1), celda(r, col + 2)
            hoja.write_formula(
                r, col + 3, f'=IF(AND(N({dz})>0,N({ez})>0),{KLI.C_ZONA_ZV}'
                            f'+LOG({ez}/{dz},{KLI.C_FACTOR_ZONA}),"")', dos,
                canal[KLI.R_TECHO])
            # --- Suelo: donde la señal/ruido (normalizada) llega a
            #     RelacionSR, según la curva de transferencia
            hoja.write_formula(r, col + 4,
                               self.suelo_snr(KLI.C_RELACION_SR, j, dz), dos,
                               canal[KLI.R_SUELO])
            fz, gz = celda(r, col + 3), celda(r, col + 4)
            hoja.write_formula(
                r, col + 5, f'=IF(AND(ISNUMBER({fz}),ISNUMBER({gz})),'
                            f'{fz}-{gz},"")', dos, canal[KLI.R_RANGO])

            # --- Último punto lineal y primer recortado: fórmulas
            #     matriciales (sin literales ni trucos)
            dv, rc = rango(c_desv + j), rango(c_rec + j)
            es = rango(col + 2)
            condicion = (f"IF(ISNUMBER({dv}),IF(ABS({dv})<="
                         f"{KLI.C_TOLERANCIA_LINEAL},IF({rc}="
                         f"{KLI.C_TEXTO_NO_RECORTADO},1,0),0),0)")
            hoja.write_array_formula(
                r, col + 6, r, col + 6,
                f"{{=IF(SUM({condicion})=0,{KLI.C_TEXTO_NINGUNO},"
                f"MAX(IF({condicion}=1,{es})))}}", dos,
                canal[KLI.R_ULTIMO_LINEAL])
            hoja.write_formula(
                r, col + 7, f"=IF(COUNTIF({rc},{KLI.C_TEXTO_RECORTADO})=0,"
                            f"{KLI.C_TEXTO_NO_ALCANZADO},INDEX({es},MATCH("
                            f"{KLI.C_TEXTO_RECORTADO},{rc},0)))", dos,
                canal[KLI.R_PRIMER_RECORTADO])
            # --- Suelos sugeridos, aceptable (SNRMinima) y excelente
            #     (SNRExcelente), como el suelo; y la latitud, con el
            #     aceptable
            for desp, umbral, clave in (
                    (8, KLI.C_SNR_MINIMA, KLI.R_SUELO_SUGERIDO),
                    (9, KLI.C_SNR_EXCELENTE, KLI.R_SUELO_EXCELENTE)):
                hoja.write_formula(r, col + desp,
                                   self.suelo_snr(umbral, j, dz), dos,
                                   canal[clave])
            iz, kz = celda(r, col + 6), celda(r, col + 8)
            hoja.write_formula(
                r, col + 10, f"=IF(AND(ISNUMBER({iz}),ISNUMBER({kz})),"
                             f"{iz}-{kz}+{KLI.C_ANCHO_ZONA},"
                             f"{KLI.C_TEXTO_NO_ALCANZADO})", dos,
                canal[KLI.R_LATITUD])
        # --- Debajo, de qué suelo sale la latitud y por qué es asimétrica
        self.nota(hoja, fila_b1 + KLI.CANALES, col, t[KLI.T_NOTA_LATITUD],
                  KLI.ANCHOS_CALCULO)
        techo_verde = celda(fila_b1 + 1, col + 3, True, True)
        suelo_verde = celda(fila_b1 + 1, col + 4, True, True)

        # --- Bloque 2: por tercio de zona
        fila = fila_b2 - 3
        hoja.write(fila, col, t[KLI.T_POR_TERCIO], self.seccion())
        self.nota(hoja, fila + 1, col, t[KLI.T_NOTA_POR_TERCIO],
                  KLI.ANCHOS_CALCULO)
        self.cabecera(hoja, fila_b2 - 1, col, tuple(t[c] for c in (
            KLI.T_CAB_ZONA, KLI.T_CAB_TERCIOS, KLI.T_CAB_ESPERADO,
            KLI.T_CAB_OBTENIDO_ROJO, KLI.T_CAB_OBTENIDO_VERDE,
            KLI.T_CAB_OBTENIDO_AZUL, KLI.T_CAB_DESV_ROJO,
            KLI.T_CAB_DESV_VERDE, KLI.T_CAB_DESV_AZUL, KLI.T_CAB_REC_ROJO,
            KLI.T_CAB_REC_VERDE, KLI.T_CAB_REC_AZUL, KLI.T_CAB_SNR_ROJO,
            KLI.T_CAB_SNR_VERDE, KLI.T_CAB_SNR_AZUL, KLI.T_CAB_FALTA_VERDE,
            KLI.T_CAB_TECHO_VERDE, KLI.T_CAB_SUELO_VERDE,
            KLI.T_CAB_SNR_SUGERIDA, KLI.T_CAB_SNR8_ROJO, KLI.T_CAB_SNR8_VERDE,
            KLI.T_CAB_SNR8_AZUL, KLI.T_CAB_SNR_MODELO,
            KLI.T_CAB_SNR_EXCELENTE, KLI.T_CAB_SNR_INGENIERIA)))
        hoja.set_row(fila_b2 - 1, KLI.ALTO_CABECERA)
        techo_v = self.valor(hoja, fila_b1 + 1, col + 3)
        suelo_v = self.valor(hoja, fila_b1 + 1, col + 4)

        # --- Para la señal/ruido normalizada y el modelo (verde): los
        #     megapíxeles del sensor, la curva del verde, su Z-V media y
        #     su máximo (por encima, el modelo no vale: recorte)
        mpx = self.ref(KLI.T_HOJA_DATOS, f[KLI.F_MPX],
                       KLI.COLUMNA_INICIO + KLI.COL_VALORES, True, True)
        normalizar = f"SQRT({mpx}/{KLI.C_MPX_REFERENCIA})"
        escala = escala_mpx(d.alto, d.ancho, k[KLI.C_MPX_REFERENCIA])
        curvas = d.transferenciaRGB
        c_verde = KLI.COLUMNA_INICIO + KLI.COL_VALORES + 1
        lectura_v, ganancia_v, proporcional_v = (
            self.ref(KLI.T_HOJA_DATOS, f[clave], c_verde, True, True)
            for clave in (KLI.F_LECTURA, KLI.F_GANANCIA, KLI.F_PROPORCIONAL))
        media_v = self.ref(KLI.T_HOJA_DATOS, f[KLI.F_MEDIA], c_verde, True,
                           True)
        maximo_v = celda(fila_b1 + 1, col + 2, True, True)
        for i in range(n):
            r, dz = fila_b2 + i, f[KLI.F_ZONAS] + i
            banda = i % 2 == 0

            def fmt(numero: str | None = None) -> object:
                return self.celda(KLI.COLOR_FORMULA, banda, "center", numero)

            hoja.write_formula(r, col, "=" + self.ref(KLI.T_HOJA_DATOS, dz,
                                                      col), fmt(),
                               self.nombre_zona(i - KS.TERCIOS_LADO))
            hoja.write_formula(r, col + 1, "=" + self.ref(
                KLI.T_HOJA_DATOS, dz, col + 1), fmt(KLI.NUM_ENTERO),
                i - KS.TERCIOS_LADO)
            hoja.write_formula(
                r, col + 2, f"={KLI.C_ZONA_ZV}+{celda(r, col + 1)}/"
                            f"{KLI.C_TERCIO_POR_ZONA}", fmt(KLI.NUM_DOS),
                esperado[i])
            for j in range(KLI.CANALES):
                valor = self.ref(KLI.T_HOJA_DATOS, dz, cols_datos[j])
                media = self.ref(KLI.T_HOJA_DATOS, f[KLI.F_MEDIA],
                                 cols_datos[j], True, False)
                oz = celda(r, col + 3 + j)
                hoja.write_formula(
                    r, col + 3 + j, f'=IF(N({valor})>0,{KLI.C_ZONA_ZV}+LOG('
                                    f'{valor}/{media},{KLI.C_FACTOR_ZONA}),'
                                    f'"")', fmt(KLI.NUM_DOS),
                    self.vacio(obtenido[j][i]))
                hoja.write_formula(
                    r, col + 6 + j, f'=IF(ISNUMBER({oz}),{oz}-'
                                    f'{celda(r, col + 2, False, True)},"")',
                    fmt(KLI.NUM_SIGNO_TRES), self.vacio(desviacion[j][i]))
                maximo = celda(fila_b1 + j, col + 2, True, True)
                hoja.write_formula(
                    r, col + 9 + j, f'=IF(ISNUMBER({valor}),IF({valor}>='
                                    f'{KLI.C_UMBRAL_RECORTE}*{maximo},'
                                    f'{KLI.C_TEXTO_RECORTADO},'
                                    f'{KLI.C_TEXTO_NO_RECORTADO}),"")',
                    fmt(), self.vacio(recortado[j][i]))
                dispersion = self.ref(KLI.T_HOJA_DATOS, dz,
                                      cols_datos[KLI.CANALES + j])
                hoja.write_formula(
                    r, col + 12 + j, f'=IF(ISNUMBER({dispersion}),IF('
                                     f'{dispersion}>0,1/{dispersion},'
                                     f'{KLI.C_TEXTO_SATURADO}),"")',
                    fmt(KLI.NUM_UNO), self.vacio(snr[j][i]))
            verde = celda(r, col + 4)
            hoja.write_formula(
                r, col + 15, f'=IF(ISNUMBER({verde}),MAX(0,'
                             f'{celda(r, col + 2, False, True)}-{verde}),"")',
                fmt(KLI.NUM_TRES), self.vacio(
                    None if obtenido[1][i] is None
                    else max(0.0, esperado[i] - obtenido[1][i])))
            hoja.write_formula(r, col + 16, f"={techo_verde}",
                               fmt(KLI.NUM_DOS), techo_v)
            hoja.write_formula(r, col + 17, f"={suelo_verde}",
                               fmt(KLI.NUM_DOS), suelo_v)
            hoja.write_formula(r, col + 18, f"={KLI.C_SNR_MINIMA}",
                               fmt(KLI.NUM_ENTERO), k[KLI.C_SNR_MINIMA])

            # --- Señal/ruido normalizada a MpxReferencia (NA() sin dato:
            #     la gráfica no lo dibuja)
            for j in range(KLI.CANALES):
                pixel = celda(r, col + 12 + j)
                hoja.write_formula(
                    r, col + 19 + j, f"=IF(ISNUMBER({pixel}),{pixel}*"
                                     f"{normalizar},{KLI.FORMULA_NA})",
                    fmt(KLI.NUM_UNO), snr[j][i] * escala
                    if isinstance(snr[j][i], float) else KLI.RESULTADO_NA)

            # --- Modelo (verde): la señal/ruido de la curva en la señal
            #     esperada de la zona, normalizada; hasta el máximo
            senal = (f"({media_v}*{KLI.C_FACTOR_ZONA}^({celda(r, col + 1)}"
                     f"/{KLI.C_TERCIO_POR_ZONA}))")
            senal_v = medias[1] * k[KLI.C_FACTOR_ZONA] ** (
                (i - KS.TERCIOS_LADO) / k[KLI.C_TERCIO_POR_ZONA])
            hoja.write_formula(
                r, col + 22, f"=IF(AND(N({ganancia_v})>0,N({media_v})>0),"
                             f"IF({senal}<={maximo_v},{senal}/SQRT(N("
                             f"{lectura_v})^2+{senal}/{ganancia_v}+(N("
                             f"{proporcional_v})*{senal})^2)*{normalizar},"
                             f"{KLI.FORMULA_NA}),{KLI.FORMULA_NA})",
                fmt(KLI.NUM_UNO), snr_modelo(curvas[1], senal_v) * escala
                if curvas and medias[1] > 0 and senal_v <= maximos[1]
                else KLI.RESULTADO_NA)

            # --- Umbrales excelente y de ingeniería (el aceptable, arriba)
            for desp, umbral in ((23, KLI.C_SNR_EXCELENTE),
                                 (24, KLI.C_RELACION_SR)):
                hoja.write_formula(r, col + desp, f"={umbral}",
                                   fmt(KLI.NUM_ENTERO), k[umbral])

        # --- Bloque 3: curva tonal (esperado, sensor y revelador)
        self.bloque_curva(hoja, fila_b3, col, k)

        # --- Bloque 4: latitud de texturas (verde)
        ultima = self.bloque_texturas(hoja, fila_b3 + n + 4, col, k)
        self.marco(hoja, ((ultima, KLI.ANCHOS_CALCULO),))

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
        n = 2 * KS.TERCIOS_LADO + 1
        zv = KS.TERCIOS_LADO
        celda = xl_rowcol_to_cell
        por_zona = self.texturas(k)
        limites = self.limites_texturas(k, por_zona)
        verde = KLI.COLUMNA_INICIO + KLI.COL_VALORES + 1
        fila_t = fila_b4 + 5

        # --- Sección, nota y cabecera de los límites
        hoja.write(fila_b4 - 3, col, t[KLI.T_POR_TEXTURA], self.seccion())
        self.nota(hoja, fila_b4 - 2, col, t[KLI.T_NOTA_TEXTURAS],
                  KLI.ANCHOS_CALCULO)
        self.cabecera(hoja, fila_b4 - 1, col, (
            "", t[KLI.T_CAB_SOMBRAS], t[KLI.T_CAB_LUCES],
            t[KLI.T_CAB_LATITUD_TEXTURAS]))
        f[KLI.F_LIMITES] = fila_b4

        # --- Rangos de la tabla por zona: el lado de las sombras (de Z0 a
        #     la ZV) y el de las luces (de la ZV a ZX)
        columnas = {clave: col + desp for clave, desp in (
            (KLI.T_CAB_ESPERADO, KLI.TEXTURA_ESPERADO),
            (KLI.T_CAB_TEXTURA_RUIDO, KLI.TEXTURA_RUIDO),
            (KLI.T_CAB_CONSERVADA, KLI.TEXTURA_CONSERVADA),
            (KLI.T_CAB_PANO_RECORTADO, KLI.TEXTURA_RECORTADO),
            (KLI.T_CAB_CUMPLE_SOMBRAS, KLI.TEXTURA_SOMBRAS),
            (KLI.T_CAB_CUMPLE_LUCES, KLI.TEXTURA_LUCES),
            (KLI.T_CAB_SIN_RECORTE, KLI.TEXTURA_SIN_RECORTE))}
        bajo = {clave: f"{celda(fila_t, c, True, True)}:"
                       f"{celda(fila_t + zv, c, True, True)}"
                for clave, c in columnas.items()}
        alto = {clave: f"{celda(fila_t + zv, c, True, True)}:"
                       f"{celda(fila_t + n - 1, c, True, True)}"
                for clave, c in columnas.items()}

        # --- Límites: apreciable y recomendada
        no = KLI.C_TEXTO_NO_ALCANZADO
        tercio = KLI.C_TERCIO_POR_ZONA
        cumple, es, q = (bajo[KLI.T_CAB_CUMPLE_SOMBRAS],
                         bajo[KLI.T_CAB_ESPERADO],
                         bajo[KLI.T_CAB_TEXTURA_RUIDO])
        # --- Solo cuentan los tercios con dato: el criterio por
        #     ISNUMBER de su valor (matriciales)
        valido = f"{cumple}*ISNUMBER({q})"
        m = f"MATCH(1,{valido},0)"
        sombra = (f"{{=IF(SUM({valido})=0,{no},IF({m}=1,INDEX({es},{m}),IF("
                  f"ISNUMBER(INDEX({q},{m}-1)),ROUND((INDEX({es},{m}-1)+("
                  f"{KLI.C_ROSE_TEXTURA}-INDEX({q},{m}-1))/(INDEX({q},{m})-"
                  f"INDEX({q},{m}-1))/{tercio})*{tercio},0)/{tercio},INDEX("
                  f"{es},{m}))))}}")
        luces = (f"{alto[KLI.T_CAB_CUMPLE_LUCES]}*ISNUMBER("
                 f"{alto[KLI.T_CAB_CONSERVADA]})")
        cortes = (f"{alto[KLI.T_CAB_SIN_RECORTE]}*ISNUMBER("
                  f"{alto[KLI.T_CAB_PANO_RECORTADO]})")
        es_alto = alto[KLI.T_CAB_ESPERADO]
        for i, (clave, valores) in enumerate(limites.items()):
            r = fila_b4 + i
            banda = i % 2 == 0
            dos = self.celda(KLI.COLOR_FORMULA, banda, "center", KLI.NUM_DOS)
            hoja.write(r, col, t[clave],
                       self.celda(KLI.COLOR_LITERAL, banda, "center"))
            c_sombra, c_luz = (celda(fila_b4, col + KLI.LIMITE_SOMBRAS),
                               celda(fila_b4, col + KLI.LIMITE_LUCES))
            if clave == KLI.T_APRECIABLE:
                formulas = (sombra, f"{{=IF(SUM({luces})=0,{no},"
                                    f"MAX(IF({luces}=1,{es_alto})))}}")
            else:
                maximo = f"MAX(IF({cortes}=1,{es_alto}))"
                formulas = (f"=IF(ISNUMBER({c_sombra}),{c_sombra}+"
                            f"{KLI.C_MARGEN_SOMBRAS}/{tercio},{c_sombra})",
                            f"{{=IF(SUM({cortes})=0,{no},IF(ISNUMBER("
                            f"{c_luz}),MIN({c_luz},{maximo}),{maximo}))}}")
            for j, formula in enumerate(formulas):
                c = col + KLI.LIMITE_SOMBRAS + j
                if formula.startswith("{"):
                    hoja.write_array_formula(r, c, r, c, formula, dos,
                                             valores[j])
                else:
                    hoja.write_formula(r, c, formula, dos, valores[j])
            luz_r, sombra_r = (celda(r, col + KLI.LIMITE_LUCES),
                               celda(r, col + KLI.LIMITE_SOMBRAS))
            hoja.write_formula(
                r, col + KLI.LIMITE_LATITUD,
                f"=IF(AND(ISNUMBER({luz_r}),ISNUMBER({sombra_r})),"
                f"{luz_r}-{sombra_r}+{KLI.C_ANCHO_ZONA},{no})", dos,
                valores[2])

        # --- Tabla por zona
        self.cabecera(hoja, fila_t - 1, col, tuple(t[c] for c in (
            KLI.T_CAB_ZONA, KLI.T_CAB_TERCIOS, KLI.T_CAB_ESPERADO,
            KLI.T_CAB_TEXTURA, KLI.T_CAB_TEXTURA_RUIDO, KLI.T_CAB_CONSERVADA,
            KLI.T_CAB_PANO_RECORTADO, KLI.T_CAB_CUMPLE_SOMBRAS,
            KLI.T_CAB_CUMPLE_LUCES, KLI.T_CAB_SIN_RECORTE)))
        hoja.set_row(fila_t - 1, KLI.ALTO_CABECERA_ALTA)
        textura_zv = celda(fila_t + zv, col + KLI.TEXTURA_TEXTURA, True, True)
        for i in range(n):
            r, dz, pz = fila_t + i, f[KLI.F_ZONAS] + i, f[KLI.F_PANO] + i
            banda = i % 2 == 0
            hoja.write_formula(r, col, "=" + self.ref(KLI.T_HOJA_DATOS, dz,
                                                      col),
                               self.celda(KLI.COLOR_FORMULA, banda, "center"),
                               self.nombre_zona(i - zv))
            hoja.write_formula(r, col + 1, "=" + self.ref(
                KLI.T_HOJA_DATOS, dz, col + 1), self.celda(
                KLI.COLOR_FORMULA, banda, "center", KLI.NUM_ENTERO), i - zv)
            hoja.write_formula(
                r, col + KLI.TEXTURA_ESPERADO,
                f"={KLI.C_ZONA_ZV}+{celda(r, col + 1)}/{tercio}",
                self.celda(KLI.COLOR_FORMULA, banda, "center", KLI.NUM_DOS),
                por_zona[KLI.T_CAB_ESPERADO][i])
            pano = self.ref(KLI.T_HOJA_DATOS, pz, verde)
            tarjeta = self.ref(KLI.T_HOJA_DATOS, dz, verde + KLI.CANALES)
            recorte = self.ref(KLI.T_HOJA_DATOS, pz, verde + KLI.CANALES)
            tx = celda(r, col + KLI.TEXTURA_TEXTURA)
            qr = celda(r, col + KLI.TEXTURA_RUIDO)
            cv = celda(r, col + KLI.TEXTURA_CONSERVADA)
            rp = celda(r, col + KLI.TEXTURA_RECORTADO)
            numericas = (
                (KLI.TEXTURA_TEXTURA, KLI.T_CAB_TEXTURA, KLI.NUM_CUATRO,
                 f'=IF(AND(ISNUMBER({pano}),ISNUMBER({tarjeta})),SQRT(MAX(0,'
                 f'{pano}^2-{tarjeta}^2)),"")'),
                (KLI.TEXTURA_RUIDO, KLI.T_CAB_TEXTURA_RUIDO, KLI.NUM_DOS,
                 f'=IF(AND(ISNUMBER({tx}),N({tarjeta})>0),{tx}/{tarjeta},"")'),
                (KLI.TEXTURA_CONSERVADA, KLI.T_CAB_CONSERVADA,
                 KLI.NUM_PORCENTAJE,
                 f'=IF(AND(ISNUMBER({tx}),N({textura_zv})>0),'
                 f'{tx}/{textura_zv},"")'),
                (KLI.TEXTURA_RECORTADO, KLI.T_CAB_PANO_RECORTADO,
                 KLI.NUM_PORCENTAJE, f'=IF(ISNUMBER({recorte}),{recorte},"")'))
            for desp, clave, numero, formula in numericas:
                hoja.write_formula(
                    r, col + desp, formula,
                    self.celda(KLI.COLOR_FORMULA, banda, "center", numero),
                    self.vacio(por_zona[clave][i]))

            # --- Criterios: sombras, de la ZV hacia abajo (lee la fila de
            #     debajo); luces, de la ZV hacia arriba (lee la de encima)
            criterios = []
            #     Sin dato, pasa lo que viene del lado de la ZV
            if i <= zv:
                sigue = ("TRUE" if i == zv else
                         celda(r + 1, col + KLI.TEXTURA_SOMBRAS))
                criterios.append((KLI.TEXTURA_SOMBRAS,
                                  KLI.T_CAB_CUMPLE_SOMBRAS,
                                  f"=IF(ISNUMBER({qr}),AND({qr}>="
                                  f"{KLI.C_ROSE_TEXTURA},{sigue}),{sigue})"))
            if i >= zv:
                for desp, clave, dato, condicion in (
                        (KLI.TEXTURA_LUCES, KLI.T_CAB_CUMPLE_LUCES, cv,
                         f"{cv}>={KLI.C_TEXTURA_CONSERVADA}"),
                        (KLI.TEXTURA_SIN_RECORTE, KLI.T_CAB_SIN_RECORTE, rp,
                         f"{rp}<={KLI.C_PANO_RECORTADO_MAX}")):
                    antes = ("TRUE" if i == zv else
                             celda(r - 1, col + desp))
                    criterios.append((desp, clave,
                                      f"=IF(ISNUMBER({dato}),AND("
                                      f"{condicion},{antes}),{antes})"))
            formato = self.celda(KLI.COLOR_FORMULA, banda, "center")
            for desp in (KLI.TEXTURA_SOMBRAS, KLI.TEXTURA_LUCES,
                         KLI.TEXTURA_SIN_RECORTE):
                hoja.write_blank(r, col + desp, None, formato)
            for desp, clave, formula in criterios:
                hoja.write_formula(r, col + desp, formula, formato,
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
        n = 2 * KS.TERCIOS_LADO + 1
        celda = xl_rowcol_to_cell
        c_verde = KLI.COLUMNA_INICIO + KLI.COL_VALORES + 1
        c_rev = KLI.COLUMNA_INICIO + KLI.COL_REVELADOR
        puntos = self.puntos_curva(k)
        hoja.write(fila_b3 - 3, col, t[KLI.T_CURVA], self.seccion())
        self.cabecera(hoja, fila_b3 - 1, col, tuple(t[c] for c in (
            KLI.T_CAB_ZONA, KLI.T_CAB_TERCIOS, KLI.T_CAB_LUZ_ESPERADA,
            KLI.T_CAB_L_ESPERADO, KLI.T_CAB_L_OBJETIVO, KLI.T_CAB_LUZ_SENSOR,
            KLI.T_CAB_L_SENSOR, KLI.T_CAB_DIF_SENSOR, KLI.T_CAB_L_REVELADOR,
            KLI.T_CAB_LUZ_REVELADOR, KLI.T_CAB_DIF_REVELADOR, KLI.T_CAB_FALTA,
            KLI.T_CAB_SOBRA, KLI.T_CAB_ENTRADA, KLI.T_CAB_SALIDA,
            KLI.T_CAB_PUNTO)))
        hoja.set_row(fila_b3 - 1, KLI.ALTO_CABECERA_ALTA)
        salida_zv = None
        for i in range(n):
            r, dz = fila_b3 + i, f[KLI.F_ZONAS] + i
            tercio_ev = i - KS.TERCIOS_LADO
            banda = i % 2 == 0
            p = puntos[i]

            def fmt(numero: str | None = None) -> object:
                return self.celda(KLI.COLOR_FORMULA, banda, "center", numero)

            def c(desp: int) -> str:
                return celda(r, col + desp)

            hoja.write_formula(r, col, "=" + self.ref(KLI.T_HOJA_DATOS, dz,
                                                      col), fmt(),
                               self.nombre_zona(tercio_ev))
            hoja.write_formula(r, col + 1, "=" + self.ref(
                KLI.T_HOJA_DATOS, dz, col + 1), fmt(KLI.NUM_ENTERO),
                tercio_ev)

            # --- Esperado: un paso de luz por zona desde la ZV, hasta el
            #     blanco de pantalla; objetivo: 10 L* por zona
            hoja.write_formula(
                r, col + 2, f"=MIN(1,{KLI.C_LUZ_ZV}*{KLI.C_FACTOR_ZONA}^("
                            f"{c(1)}/{KLI.C_TERCIO_POR_ZONA}))",
                fmt(KLI.NUM_CUATRO), p.luz_esperada)
            hoja.write_formula(r, col + 3, f"={self.formula_lab(c(2))}",
                               fmt(KLI.NUM_UNO), p.esperado)
            hoja.write_formula(
                r, col + 4, f"={KLI.C_L_POR_ZONA}*({KLI.C_ZONA_ZV}+{c(1)}/"
                            f"{KLI.C_TERCIO_POR_ZONA})", fmt(KLI.NUM_UNO),
                p.objetivo)

            # --- Sensor: el verde de la zona entre el de la ZV (media)
            verde = self.ref(KLI.T_HOJA_DATOS, dz, c_verde)
            media = self.ref(KLI.T_HOJA_DATOS, f[KLI.F_MEDIA], c_verde,
                             True, True)
            hoja.write_formula(
                r, col + 5, f'=IF(N({verde})>0,MIN(1,{KLI.C_LUZ_ZV}*{verde}'
                            f'/{media}),"")', fmt(KLI.NUM_CUATRO),
                self.vacio(p.luz_sensor))
            hoja.write_formula(
                r, col + 6, f'=IF(ISNUMBER({c(5)}),{self.formula_lab(c(5))},'
                            f'"")', fmt(KLI.NUM_UNO), self.vacio(p.sensor))
            hoja.write_formula(
                r, col + KLI.CURVA_DIF_SENSOR,
                f'=IF(ISNUMBER({c(6)}),{c(6)}-{c(3)},"")',
                fmt(KLI.NUM_SIGNO_UNO),
                self.vacio(None if p.sensor is None
                           else p.sensor - p.esperado))

            # --- Revelador: de su tabla en Datos (leído o estimado). Sin
            #     dato, NA() en lo que dibujan la curva tonal y la
            #     diferencia en L*
            revelador = self.ref(KLI.T_HOJA_DATOS, f[KLI.F_REVELADOR] + i,
                                 c_rev)
            l_esp, l_rev, luz_rev = p.esperado, p.revelador, p.luz_revelador
            hoja.write_formula(
                r, col + 8, f'=IF(ISNUMBER({revelador}),{revelador},'
                            f'{KLI.FORMULA_NA})',
                fmt(KLI.NUM_UNO), KLI.RESULTADO_NA if l_rev is None
                else l_rev)
            hoja.write_formula(
                r, col + 9, f'=IF(ISNUMBER({c(8)}),IF({c(8)}>'
                            f'{KLI.C_LAB_UMBRAL}*{KLI.C_LAB_PENDIENTE},'
                            f'(({c(8)}+'
                            f'{KLI.C_LAB_DESPLAZA})/{KLI.C_LAB_ESCALA})^3,'
                            f'{c(8)}/{KLI.C_LAB_PENDIENTE}),"")',
                fmt(KLI.NUM_CUATRO), self.vacio(luz_rev))
            hoja.write_formula(
                r, col + KLI.CURVA_DIF_REVELADOR,
                f'=IF(ISNUMBER({c(8)}),{c(8)}-{c(3)},{KLI.FORMULA_NA})',
                fmt(KLI.NUM_SIGNO_UNO),
                KLI.RESULTADO_NA if l_rev is None else l_rev - l_esp)
            hoja.write_formula(
                r, col + 11, f'=IF(ISNUMBER({c(8)}),MAX(0,{c(3)}-{c(8)}),"")',
                fmt(KLI.NUM_UNO),
                "" if l_rev is None else max(0.0, l_esp - l_rev))
            hoja.write_formula(
                r, col + 12, f'=IF(ISNUMBER({c(8)}),MAX(0,{c(8)}-{c(3)}),"")',
                fmt(KLI.NUM_UNO),
                "" if l_rev is None else max(0.0, l_rev - l_esp))
            hoja.write_formula(
                r, col + KLI.CURVA_ENTRADA,
                f'=IF(ISNUMBER({c(9)}),{self.formula_curva(c(9))},"")',
                fmt(KLI.NUM_ENTERO),
                self.vacio(p.entrada))
            salida = p.salida
            hoja.write_formula(
                r, col + KLI.CURVA_SALIDA,
                f'=IF(ISNUMBER({c(8)}),{self.formula_curva(c(2))},"")',
                fmt(KLI.NUM_ENTERO), "" if l_rev is None else salida)
            if tercio_ev == 0:
                salida_zv = (celda(r, col + 2), salida)
            hoja.write_formula(
                r, col + KLI.CURVA_PUNTO,
                f'=IF(MOD({c(1)},{KLI.C_TERCIO_POR_ZONA})=0,'
                f'{KLI.C_TEXTO_PUNTO},"")', fmt(),
                t[KLI.V_PUNTO] if tercio_ev % k[KLI.C_TERCIO_POR_ZONA] == 0
                else "")

        # --- Nota, con la lectura que debe dar el parche ZV en Revelar
        #     calculada (si cambia LZV, no se desfasa)
        luz_zv, valor_zv = salida_zv                            # type: ignore
        porcentaje = 100 * valor_zv / k[KLI.C_ESCALA_CURVA]
        cien = KLI.CIEN
        self.nota(
            hoja, fila_b3 - 2, col,
            f"{t[KLI.T_NOTA_CURVA_ANTES]}{porcentaje:.1f}"
            f"{t[KLI.T_NOTA_CURVA_MEDIO]}{valor_zv}"
            f"{t[KLI.T_NOTA_CURVA_DESPUES]}", KLI.ANCHOS_CALCULO,
            formula=f"={self.cadena(t[KLI.T_NOTA_CURVA_ANTES])}&FIXED("
                    f"{self.formula_curva(luz_zv)}/{KLI.C_ESCALA_CURVA}*"
                    f"{cien},1)&{self.cadena(t[KLI.T_NOTA_CURVA_MEDIO])}&"
                    f"{self.formula_curva(luz_zv)}&"
                    f"{self.cadena(t[KLI.T_NOTA_CURVA_DESPUES])}")

    #
    def hoja_analisis(self) -> None:
        """
        Hoja Análisis, con el estilo de Tony, en dos tarjetas sobre una
        rejilla de filas iguales (KLI.ALTO_REJILLA): lo alto ocupa varias
        filas combinadas, así una tarjeta no estira las filas de la otra.
        Izquierda: cabecera (cámara, fecha, bits y exposición de la Z-V),
        latitud de texturas, ruido de lectura y negro, y balances de
        blancos. Derecha: sugerencia de revelado, diferencias medias, las
        decisiones propias del estudiante y las recomendaciones (la tabla
        por zona: L* leído, diferencias del sensor y del revelador,
        entrada, salida y punto de la curva).
        """
        # --- Cada tarjeta, por su cuenta (la rejilla las independiza)
        hoja = self.__hojas[KLI.T_HOJA_ANALISIS]
        fila_balances = self.analisis_izquierda(hoja)
        ultima_derecha = self.analisis_derecha(hoja)
        ultima_izquierda = self.analisis_balances(hoja, fila_balances)
        self.marco(hoja, ((ultima_izquierda, KLI.ANCHOS_ANALISIS),
                          (ultima_derecha, KLI.ANCHOS_ANALISIS_DERECHA)),
                   KLI.ANILLO_ANALISIS, KLI.ANCHO_ANILLO_ANALISIS,
                   KLI.ANCHO_RELLENO_ANALISIS, KLI.ALTO_REJILLA)

    #
    def analisis_izquierda(self, hoja: Worksheet) -> int:
        """
        Tarjeta izquierda de Análisis: título, cámara, fecha, bits y
        exposición de la Z-V; latitud de texturas; ruido de lectura y
        negro, con sus avisos; y la barra y la nota de los balances de
        blancos. Devuelve la fila donde puede ir la cabecera de los
        balances (ver analisis_balances).
        """
        t, d, f = self.__textos, self.__datos, self.__filas
        col = KLI.COLUMNA_INICIO
        ultima = col + len(KLI.ANCHOS_ANALISIS) - 1
        rotulo = self.fmt_analisis(bold=True, align="right", valign="top")
        valor = self.fmt_analisis(align="left", valign="top")
        nota = self.nota_analisis(KLI.COLOR_ROTULO)

        # --- Cabecera: título, cámara, fecha, profundidad de bits de los
        #     RAW y exposición de la Z-V
        fila = KLI.FILA_INICIO
        hoja.merge_range(fila, col, fila + KLI.FILAS_TITULO_ANALISIS - 1,
                         ultima, t[KLI.T_TITULO_ANALISIS],
                         self.fondo_analisis(KLI.TAMANO_ANALISIS_TITULO,
                                            align="center", valign="vcenter"))
        fila += KLI.FILAS_TITULO_ANALISIS + 1
        hoja.write(fila, col, t[KLI.T_MARCA_MODELO], rotulo)
        hoja.merge_range(fila, col + 1, fila, ultima, d.camara, valor)
        fila += 1
        hoja.write(fila, col, t[KLI.T_FECHA], rotulo)
        fecha = self.fmt_analisis(align="left", valign="top",
                                  num_format=t[KLI.T_FORMATO_FECHA])
        hoja.merge_range(fila, col + 1, fila, ultima, "", fecha)
        if d.fecha:
            hoja.write_datetime(fila, col + 1,
                                datetime.fromisoformat(d.fecha), fecha)
        fila += 1
        hoja.write(fila, col, t[KLI.T_BITS], rotulo)
        bits = self.fmt_analisis(align="left", valign="top",
                                 num_format=KLI.NUM_BITS)
        hoja.merge_range(fila, col + 1, fila, ultima, "", bits)
        if d.bits:
            hoja.write_number(fila, col + 1, d.bits, bits)
        fila += 1
        hoja.write(fila, col, t[KLI.T_ZV], rotulo)
        for i, (clave, dato) in enumerate((
                (KLI.T_ISO, OECF.TextoISO(d.iso) if d.iso else ""),
                (KLI.T_TV, OECF.TextoTV(d.tv) if d.tv else ""),
                (KLI.T_F, OECF.TextoF(d.f) if d.f else ""))):
            hoja.write(fila, col + 1 + 2 * i, t[clave], rotulo)
            hoja.write(fila, col + 2 + 2 * i, dato, valor)

        # --- Latitud de texturas (de Cálculo, bloque 4): barra, cabecera,
        #     apreciable y recomendada (sombras, luces y latitud, en
        #     tercios) y la nota con los criterios (o que no hay paño)
        fila += 2
        self.barra_analisis(hoja, fila, col, ultima, t[KLI.T_TEXTURAS])
        fila = self.cabecera_tarjeta(
            hoja, fila + 2, col, (("", KLI.COLUMNAS_ROTULO),
                                  (t[KLI.T_CAB_SOMBRAS], 1),
                                  (t[KLI.T_CAB_LUCES], 1),
                                  (t[KLI.T_CAB_LATITUD_TEXTURAS], 1)),
            KLI.FILAS_CABECERA)
        k = self.valores_constantes()
        limites = self.limites_texturas(k, self.texturas(k))
        for i, (clave, valores) in enumerate(limites.items()):
            fila += 1
            banda = i % 2 == 0
            hoja.merge_range(fila, col, fila, col + KLI.COLUMNAS_ROTULO - 1,
                             t[clave], self.celda_analisis(banda, "left"))
            numero = self.celda_analisis(banda, "center", KLI.NUM_TERCIOS)
            for j in range(len(valores)):
                origen = self.ref(KLI.T_HOJA_CALCULO, f[KLI.F_LIMITES] + i,
                                  col + KLI.LIMITE_SOMBRAS + j)
                hoja.write_formula(fila, col + KLI.COLUMNAS_ROTULO + j,
                                   f"={origen}", numero, valores[j])
        if isinstance(d.pano, str):
            nota_texturas = t[KLI.T_SIN_PANO]
        else:
            nota_texturas = t[KLI.T_NOTA_TEXTURAS_ANALISIS].format(
                rose=k[KLI.C_ROSE_TEXTURA],
                conservada=round(k[KLI.C_TEXTURA_CONSERVADA] * KLI.CIEN),
                recortado=round(k[KLI.C_PANO_RECORTADO_MAX] * KLI.CIEN),
                margen=k[KLI.C_MARGEN_SOMBRAS])
        fila = self.nota_tarjeta(hoja, fila + 1, col, ultima, nota_texturas,
                                 KLI.ANCHOS_ANALISIS, nota)

        # --- Ruido de lectura y negro (de Datos): barra, una fila por
        #     dato (ruido usado, tapadas para comparar, negro; dos si su
        #     rótulo no cabe en una línea) y los avisos
        fila += 2
        self.barra_analisis(hoja, fila, col, ultima, t[KLI.T_RUIDO_NEGRO])
        fila = self.cabecera_tarjeta(
            hoja, fila + 2, col, (("", KLI.COLUMNAS_ROTULO),)
            + tuple((t[clave], 1) for clave in KLI.T_CANALES),
            KLI.FILAS_CABECERA)
        datos_ruido = [(f[KLI.F_RUIDO], d.ruidoRGB, KLI.NUM_DOS)]
        if KLI.F_RUIDO_TAPADAS in f:
            datos_ruido.append((f[KLI.F_RUIDO_TAPADAS], d.ruidoTapadasRGB,
                                KLI.NUM_DOS))
        datos_ruido.append((f[KLI.F_NEGRO], d.negroRGB, KLI.NUM_ENTERO))
        ancho_rotulo = sum(KLI.ANCHOS_ANALISIS[:KLI.COLUMNAS_ROTULO])
        for i, (origen, valores, formato) in enumerate(datos_ruido):
            fila += 1
            banda = i % 2 == 0
            rotulo_ruido = self.__rotulos[origen]
            filas = self.filas_texto(rotulo_ruido, ancho_rotulo
                                     / KLI.ESCALA_LETRA_TABLA,
                                     KLI.ALTO_LINEA_TABLA)
            abajo = fila + filas - 1
            texto = self.celda_analisis(banda, "left", text_wrap=True)
            numero = self.celda_analisis(banda, "center", formato)
            hoja.merge_range(fila, col, abajo, col + KLI.COLUMNAS_ROTULO - 1,
                             "", texto)
            hoja.write_formula(
                fila, col, "=" + self.ref(KLI.T_HOJA_DATOS, origen, col),
                texto, rotulo_ruido)
            for j in range(KLI.CANALES):
                c = col + KLI.COLUMNAS_ROTULO + j
                celda_datos = self.ref(KLI.T_HOJA_DATOS, origen,
                                       col + KLI.COL_VALORES + j)
                if filas > 1:
                    hoja.merge_range(fila, c, abajo, c, "", numero)
                hoja.write_formula(
                    fila, c, f'=IF(ISNUMBER({celda_datos}),{celda_datos},"")',
                    numero, valores[j] if valores else "")
            fila = abajo
        avisos = []
        if d.ruidoRGB is None:
            avisos.append(t[KLI.T_SIN_RUIDO_SUELO])
        if d.difieren:
            avisos.append(t[KLI.T_RUIDOS_DIFIEREN].format(
                porcentaje=round(KTE.DIFERENCIA_RUIDO * KLI.CIEN)))
        for aviso in avisos:
            fila = self.nota_tarjeta(hoja, fila + 1, col, ultima, aviso,
                                     KLI.ANCHOS_ANALISIS, nota)

        # --- Balances de blancos (de Datos): barra y nota; la cabecera y
        #     los balances, en analisis_balances
        fila += 2
        self.barra_analisis(hoja, fila, col, ultima, t[KLI.T_BALANCES])
        fila = self.nota_tarjeta(hoja, fila + 1, col, ultima,
                                 t[KLI.T_NOTA_BALANCES], KLI.ANCHOS_ANALISIS,
                                 nota)
        return fila + 1

    #
    def analisis_balances(self, hoja: Worksheet, fila: int) -> int:
        """
        Balances de blancos de la tarjeta izquierda de Análisis (de
        Datos): la cabecera, desde fila, y, por balance, su nombre y los
        Kelvin de la cámara y reales. Devuelve su última fila.
        """
        t, d, f = self.__textos, self.__datos, self.__filas
        col = KLI.COLUMNA_INICIO
        fila = self.cabecera_tarjeta(
            hoja, fila, col + 2, ((t[KLI.T_CAB_BALANCE], 3),
                                  (t[KLI.T_CAB_KELVIN_ANOTADO], 1),
                                  (t[KLI.T_CAB_KELVIN_MEDIDO], 1)),
            KLI.FILAS_CABECERA_ALTA)
        for i, balance in enumerate(d.balancesDistintos):
            fila += 1
            banda = i % 2 == 0
            texto = self.celda_analisis(banda, "left")
            numero = self.celda_analisis(banda, "center", KLI.NUM_ENTERO)
            origen = f[KLI.F_BALANCES] + i
            hoja.merge_range(fila, col + 2, fila, col + 4, "", texto)
            hoja.write_formula(
                fila, col + 2, "=" + self.ref(KLI.T_HOJA_DATOS, origen, col),
                texto, self.nombre_balance(balance.nombre))
            for j, valor_k in enumerate((balance.kelvin_camara,
                                         balance.kelvin)):
                celda_datos = self.ref(KLI.T_HOJA_DATOS, origen,
                                       col + KLI.COL_VALORES + j)
                hoja.write_formula(
                    fila, col + 5 + j,
                    f'=IF(ISNUMBER({celda_datos}),{celda_datos},"")',
                    numero, self.vacio(valor_k))
        return fila

    #
    def analisis_derecha(self, hoja: Worksheet) -> int:
        """
        Tarjeta derecha de Análisis: sugerencia de revelado (un solo
        texto), qué es lo estimado, las diferencias medias (sensor y
        revelador), el aviso si no hay L* leído, las decisiones propias
        (los puntos de la curva que elige el estudiante: zona de la lista,
        entrada y salida de 0 a EscalaCurva) y las recomendaciones: la
        tabla por zona, con el L* leído (lo escribe el estudiante o el
        programa con las TIFF) y lo demás, de Cálculo. Lo estimado
        (tercios sin L* leído), en su color. Devuelve su última fila.
        """
        t, f = self.__textos, self.__filas
        hoja_calculo = self.__hojas[KLI.T_HOJA_CALCULO]
        col = self.columna_derecha()
        ultima = col + len(KLI.ANCHOS_ANALISIS_DERECHA) - 1
        col_calculo = KLI.COLUMNA_INICIO
        b3 = f[KLI.F_CURVA]
        n = 2 * KS.TERCIOS_LADO + 1
        celda = xl_rowcol_to_cell
        nota = self.nota_analisis(KLI.COLOR_ROTULO)

        # --- Sugerencia de revelado: barra y su texto, en un bloque
        fila = KLI.FILA_INICIO
        self.barra_analisis(hoja, fila, col, ultima, t[KLI.T_SUGERENCIA])
        fila = self.nota_tarjeta(
            hoja, fila + 1, col, ultima, KLI.SEPARADOR_NOTAS.join(
                t[clave] for clave in (KLI.T_SUGERIDO, KLI.T_REFERENCIA,
                                       KLI.T_ES_SUGERENCIA)),
            KLI.ANCHOS_ANALISIS_DERECHA, nota)

        # --- Qué es lo estimado, en su color
        fila = self.nota_tarjeta(hoja, fila + 1, col, ultima,
                                 t[KLI.T_ESTIMADO],
                                 KLI.ANCHOS_ANALISIS_DERECHA,
                                 self.nota_analisis(KLI.COLOR_ESTIMADO))

        # --- Diferencias medias (sensor y revelador) y, sin revelador, la
        #     nota que lo explica (sus filas, aunque salga vacía)
        rotulo = self.fmt_analisis(bold=True, align="right", valign="top")
        valor_media = self.fmt_analisis(align="left", valign="top",
                                        num_format=KLI.NUM_LSTAR)
        col_media = col + KLI.COLUMNAS_ROTULO_MEDIA
        medias = []
        for desp, clave in ((KLI.CURVA_DIF_SENSOR, KLI.T_DIF_MEDIA_SENSOR),
                            (KLI.CURVA_DIF_REVELADOR,
                             KLI.T_DIF_MEDIA_REVELADOR)):
            fila += 1
            primera = self.ref(KLI.T_HOJA_CALCULO, b3, col_calculo + desp,
                               True, True)
            columna = (f"{primera}:"
                       f"{celda(b3 + n - 1, col_calculo + desp, True, True)}")
            numeros = [v for v in (self.valor(hoja_calculo, b3 + i,
                                              col_calculo + desp)
                                   for i in range(n))
                       if isinstance(v, (int, float))]
            hoja.merge_range(fila, col, fila, col_media - 1, t[clave], rotulo)
            hoja.merge_range(fila, col_media, fila, ultima, "", valor_media)
            hoja.write_array_formula(
                fila, col_media, fila, col_media,
                f'{{=IF(COUNT({columna})=0,"",SUM(IF(ISNUMBER({columna}),'
                f'ABS({columna}),0))/COUNT({columna}))}}', valor_media,
                sum(abs(x) for x in numeros) / len(numeros) if numeros
                else "")
            medias.append(columna)
        aviso = self.cadena(t[KLI.T_SIN_REVELADOR])
        sin_revelador = not any(v is not None for v in self.__revelador)
        fila = self.nota_tarjeta(
            hoja, fila + 2, col, ultima,
            t[KLI.T_SIN_REVELADOR] if sin_revelador else "",
            KLI.ANCHOS_ANALISIS_DERECHA, nota,
            f'=IF(COUNT({medias[1]})=0,{aviso},"")', t[KLI.T_SIN_REVELADOR])

        # --- Decisiones propias: barra, cabecera doble (zona, entrada y
        #     salida, en cada lado) y sus filas en blanco, que escribe el
        #     estudiante (validadas al final, cuando se sabe dónde está la
        #     lista de las zonas)
        fila += 2
        self.barra_analisis(hoja, fila, col, ultima, t[KLI.T_DECISIONES])
        punto = ((t[KLI.T_CAB_ZONA], 1), (t[KLI.T_CAB_ENTRADA], 1),
                 (t[KLI.T_CAB_SALIDA], 1))
        for lado in KLI.LADOS_DECISIONES:
            fin_cabecera = self.cabecera_tarjeta(hoja, fila + 1, col + lado,
                                                 punto, KLI.FILAS_CABECERA)
        primera_decision = fin_cabecera + 1
        fila = fin_cabecera
        for i in range(KLI.FILAS_DECISIONES):
            fila += 1
            banda = i % 2 == 0
            for lado in KLI.LADOS_DECISIONES:
                hoja.write_blank(fila, col + lado, None, self.celda_analisis(
                    banda, "center", font_color=KLI.COLOR_DATO))
                for j in (1, 2):
                    hoja.write_blank(fila, col + lado + j, None,
                                     self.celda_analisis(
                                         banda, "center", KLI.NUM_ENTERO,
                                         font_color=KLI.COLOR_DATO))
        ultima_decision = fila

        # --- Recomendaciones, justo debajo: barra y la tabla por zona
        #     (zona, L* leído y, de Cálculo, las diferencias, la entrada,
        #     la salida y el punto de la curva)
        fila += 3
        self.barra_analisis(hoja, fila - 1, col, ultima,
                            t[KLI.T_RECOMENDACIONES])
        fila = self.cabecera_tarjeta(
            hoja, fila, col, tuple((t[clave], 1) for clave in (
                KLI.T_CAB_ZONA, KLI.T_CAB_L_LEIDO, KLI.T_CAB_DIF_SENSOR,
                KLI.T_CAB_DIF_REVELADOR, KLI.T_CAB_ENTRADA, KLI.T_CAB_SALIDA,
                KLI.T_CAB_PUNTO)), KLI.FILAS_CABECERA_ALTA)
        f[KLI.F_LEIDO] = fila + 1
        col_leido = col + KLI.COL_LEIDO
        numericas = ((KLI.CURVA_DIF_SENSOR, KLI.NUM_SIGNO_UNO),
                     (KLI.CURVA_DIF_REVELADOR, KLI.NUM_SIGNO_UNO),
                     (KLI.CURVA_ENTRADA, KLI.NUM_ENTERO),
                     (KLI.CURVA_SALIDA, KLI.NUM_ENTERO))
        estimables = (KLI.CURVA_DIF_REVELADOR, KLI.CURVA_ENTRADA)
        cols_estimadas = [col_leido + 1 + j
                          for j, (desp, _) in enumerate(numericas)
                          if desp in estimables]
        col_punto = col_leido + 1 + len(numericas)
        medido = self.revelador_medido()
        por_zona = self.valores_constantes()[KLI.C_TERCIO_POR_ZONA]
        for i in range(n):
            fila += 1
            banda = i % 2 == 0

            # --- Las zonas enteras (los puntos de la curva), en negrita
            entera = (i - KS.TERCIOS_LADO) % por_zona == 0
            hoja.write_formula(
                fila, col, "=" + self.ref(KLI.T_HOJA_CALCULO, b3 + i,
                                          col_calculo),
                self.celda_analisis(banda, "right", bold=entera),
                self.nombre_zona(i - KS.TERCIOS_LADO))
            leido = self.celda_analisis(banda, "center", KLI.NUM_UNO,
                                        font_color=KLI.COLOR_DATO,
                                        bold=entera)
            if medido[i] is None:
                hoja.write_blank(fila, col_leido, None, leido)
            else:
                hoja.write_number(fila, col_leido, medido[i], leido)
            for j, (desp, numero) in enumerate(numericas):
                origen = self.ref(KLI.T_HOJA_CALCULO, b3 + i,
                                  col_calculo + desp)
                resultado = self.valor(hoja_calculo, b3 + i,
                                       col_calculo + desp)
                hoja.write_formula(
                    fila, col_leido + 1 + j,
                    f'=IF(ISNUMBER({origen}),{origen},"")',
                    self.celda_analisis(banda, "center", numero,
                                        bold=entera),
                    resultado if isinstance(resultado, (int, float))
                    else "")
            origen = self.ref(KLI.T_HOJA_CALCULO, b3 + i,
                              col_calculo + KLI.CURVA_PUNTO)
            hoja.write_formula(
                fila, col_punto, f'=IF({origen}="","",{origen})',
                self.celda_analisis(banda, "center", bold=entera),
                self.valor(hoja_calculo, b3 + i,
                           col_calculo + KLI.CURVA_PUNTO))

        # --- Lo estimado, en su color: hay valor sin L* leído
        primera = f[KLI.F_LEIDO]
        leido_fila = celda(primera, col_leido, False, True)
        estimado = self.__libro.add_format(
            {"font_color": KLI.COLOR_ESTIMADO})
        for c in cols_estimadas:
            hoja.conditional_format(
                primera, c, fila, c,
                {"type": "formula",
                 "criteria": f'=AND({leido_fila}="",'
                             f'ISNUMBER({celda(primera, c)}))',
                 "format": estimado})

        # --- Decisiones propias validadas: la zona, de la lista de la
        #     tabla; entrada y salida, enteros de 0 a EscalaCurva
        zonas = (f"={celda(primera, col, True, True)}:"
                 f"{celda(fila, col, True, True)}")
        for lado in KLI.LADOS_DECISIONES:
            hoja.data_validation(
                primera_decision, col + lado, ultima_decision, col + lado,
                {"validate": "list", "source": zonas,
                 "error_title": t[KLI.T_DECISIONES],
                 "error_message": t[KLI.T_VALIDA_ZONA]})
            hoja.data_validation(
                primera_decision, col + lado + 1, ultima_decision,
                col + lado + 2,
                {"validate": "integer", "criteria": "between",
                 "minimum": 0, "maximum": f"={KLI.C_ESCALA_CURVA}",
                 "error_title": t[KLI.T_DECISIONES],
                 "error_message": t[KLI.T_VALIDA_CURVA].format(
                     maximo=self.valores_constantes()[KLI.C_ESCALA_CURVA])})
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
        hoja = self.__hojas[KLI.T_HOJA_DATOS]
        col = KLI.COLUMNA_INICIO
        col_leido = self.columna_derecha() + KLI.COL_LEIDO
        col_esperado = col + KLI.CURVA_L_ESPERADO
        por_zona = self.valores_constantes()[KLI.C_TERCIO_POR_ZONA]
        for i, valor in enumerate(self.__revelador):
            tercio = (i - KS.TERCIOS_LADO) % por_zona
            leido = self.ref(KLI.T_HOJA_ANALISIS, f[KLI.F_LEIDO] + i,
                             col_leido)
            formula = f'=IF(ISNUMBER({leido}),{leido},"")'
            if tercio:
                antes, despues = i - tercio, i - tercio + por_zona
                leido_a, leido_d = (
                    self.ref(KLI.T_HOJA_ANALISIS, f[KLI.F_LEIDO] + z,
                             col_leido) for z in (antes, despues))
                esp_i, esp_a, esp_d = (
                    self.ref(KLI.T_HOJA_CALCULO, f[KLI.F_CURVA] + z,
                             col_esperado) for z in (i, antes, despues))
                dif_a = f"({leido_a}-{esp_a})"
                dif_d = f"({leido_d}-{esp_d})"
                formula = (f'=IF(ISNUMBER({leido}),{leido},'
                           f'IF(AND(ISNUMBER({leido_a}),ISNUMBER({leido_d})),'
                           f'MEDIAN({leido_a},{leido_d},{esp_i}+{dif_a}+'
                           f'({dif_d}-{dif_a})*{tercio}/'
                           f'{KLI.C_TERCIO_POR_ZONA}),""))')
            hoja.write_formula(
                f[KLI.F_REVELADOR] + i, col + KLI.COL_REVELADOR, formula,
                self.celda(KLI.COLOR_FORMULA, i % 2 == 0, "center",
                           KLI.NUM_UNO), self.vacio(valor))

    #
    def hoja_graficos(self) -> None:
        """
        Hoja Gráficos: seis gráficas que leen de Cálculo, en el orden de
        KLI.ORDEN_GRAFICAS (que les da su número): la curva tonal en L*,
        la diferencia en L*, esperado y obtenido (con un segundo eje en
        pasos respecto a la Z-V), la desviación (tramo lineal y rango
        completo) y la señal/ruido. La serie del revelador, siempre: el L*
        leído puede llegar después (a mano); sin él, Cálculo da NA() y la
        gráfica no lo dibuja.
        """
        t, d, f = self.__textos, self.__datos, self.__filas
        hoja = self.__hojas[KLI.T_HOJA_GRAFICOS]
        col, n = KLI.COLUMNA_INICIO, 2 * KS.TERCIOS_LADO + 1
        b2, b3 = f[KLI.F_TERCIOS], f[KLI.F_CURVA]
        self.titulo(hoja, KLI.FILA_INICIO, col, t[KLI.T_TITULO_GRAFICOS],
                    t[KLI.T_NOTA_GRAFICOS].format(camara=d.camara),
                    KLI.ANCHOS_GRAFICOS)
        canales = KLI.T_CANALES

        def rango(fila: int, desp: int) -> str:
            celdas = xl_range_abs(fila, col + desp, fila + n - 1, col + desp)
            return f"='{t[KLI.T_HOJA_CALCULO]}'!{celdas}"

        def linea(color: str, ancho: float = 1.5,
                  trazo: str | None = None) -> dict:
            propiedades: dict = {"color": color, "width": ancho}
            if trazo:
                propiedades["dash_type"] = trazo
            return propiedades

        def marcador(color: str) -> dict:
            return {"type": "circle", "size": KLI.TAMANO_MARCADOR,
                    "fill": {"color": color}, "border": {"color": color}}

        def grafica(tipo: str, titulo: str, eje: tuple, nombre_eje: str,
                    fila: int, base: int | None = None) -> object:
            g = self.__libro.add_chart({"type": tipo})
            g.set_title({"name": KLI.FORMATO_TITULO_GRAFICA.format(
                numero=KLI.ORDEN_GRAFICAS.index(titulo) + 1,
                titulo=t[titulo])})
            g.set_x_axis({"name": t[KLI.T_EJE_ZONA],
                          "label_position": "low",
                          "num_font": {"rotation": KLI.ROTACION_ZONAS,
                                       "size": KLI.TAMANO_ZONAS}})
            # --- Eje y: con base, logarítmico (sin paso: una marca por
            #     potencia de la base)
            minimo, maximo, paso, numeros = eje
            eje_y = {"name": t[nombre_eje], "min": minimo, "max": maximo,
                     "num_format": numeros}
            if paso is not None:
                eje_y["major_unit"] = paso
            if base:
                eje_y["log_base"] = base
            g.set_y_axis(eje_y)
            g.set_legend({"position": "bottom"})
            g.set_size({"width": KLI.TAMANO_GRAFICA[0],
                        "height": KLI.TAMANO_GRAFICA[1]})
            return g

        zonas_b2, zonas_b3 = rango(b2, 0), rango(b3, 0)
        graficas: dict[str, object] = {}

        # --- Esperado y obtenido, con barras lilas del verde hasta el
        #     esperado y un segundo eje en pasos respecto a la Z-V
        g = grafica("line", KLI.T_G_ESPERADO, KLI.EJE_ZONAS,
                    KLI.T_EJE_SENAL, b2)
        g.add_series({"name": t[KLI.T_CAB_ESPERADO], "categories": zonas_b2,
                      "values": rango(b2, 2),
                      "line": {**linea(KLI.COLOR_ESPERADO,
                                       KLI.ANCHO_ESPERADO),
                               "transparency": KLI.TRANSPARENCIA_ESPERADO}})
        for j in range(KLI.CANALES):
            serie = {"name": t[canales[j]], "categories": zonas_b2,
                     "values": rango(b2, 3 + j), "line": {"none": True},
                     "marker": marcador(KLI.COLORES_CANALES[j])}
            if j == 1:
                serie["y_error_bars"] = {
                    "type": "custom", "direction": "plus",
                    "plus_values": rango(b2, 15), "end_style": 0,
                    "line": linea(KLI.COLOR_BARRAS, KLI.ANCHO_BARRAS)}
            g.add_series(serie)
        g.add_series({"name": t[KLI.T_CAB_TECHO_VERDE],
                      "categories": zonas_b2, "values": rango(b2, 16),
                      "line": linea(KLI.COLORES_CANALES[1], trazo="dash")})
        g.add_series({"name": t[KLI.T_CAB_SUELO_VERDE],
                      "categories": zonas_b2, "values": rango(b2, 17),
                      "line": linea(KLI.COLORES_CANALES[1],
                                    trazo="round_dot")})
        g.add_series({"categories": zonas_b2, "values": rango(b2, 2),
                      "y2_axis": True, "line": {"none": True}})
        minimo, maximo, paso, numeros = KLI.EJE_ZONAS
        zona_zv = dict((c[0], c[1]) for c in KLI.CONSTANTES)[KLI.C_ZONA_ZV]
        g.set_y2_axis({"name": t[KLI.T_EJE_PASOS], "min": minimo - zona_zv,
                       "max": maximo - zona_zv, "major_unit": paso,
                       "num_format": numeros})
        g.set_legend({"position": "bottom",
                      "delete_series": [KLI.CANALES + 3]})
        graficas[KLI.T_G_ESPERADO] = g

        # --- Desviación por canal: tramo lineal y rango completo
        for titulo, eje in ((KLI.T_G_DESV_LINEAL, KLI.EJE_DESV_LINEAL),
                            (KLI.T_G_DESV_COMPLETA, KLI.EJE_DESV_COMPLETA)):
            g = grafica("line", titulo, eje, KLI.T_EJE_DESVIACION, b2)
            for j in range(KLI.CANALES):
                g.add_series({"name": t[canales[j]], "categories": zonas_b2,
                              "values": rango(b2, 6 + j),
                              "line": linea(KLI.COLORES_CANALES[j])})
            graficas[titulo] = g

        # --- Señal/ruido por canal, normalizada a MpxReferencia (en
        #     escala logarítmica), el modelo del verde y los tres umbrales:
        #     ingeniería, mínimo sugerido y excelente
        g = grafica("line", KLI.T_G_SNR, KLI.EJE_SNR, KLI.T_EJE_SNR, b2,
                    KLI.BASE_EJE_SNR)
        for j in range(KLI.CANALES):
            g.add_series({"name": t[canales[j]], "categories": zonas_b2,
                          "values": rango(b2, 19 + j), "line": {"none": True},
                          "marker": marcador(KLI.COLORES_CANALES[j])})
        g.add_series({"name": t[KLI.T_S_MODELO], "categories": zonas_b2,
                      "values": rango(b2, 22),
                      "line": linea(KLI.COLORES_CANALES[1], trazo="dash")})
        for nombre, desp, trazo in ((KLI.T_S_INGENIERIA, 24, "round_dot"),
                                    (KLI.T_S_MINIMO, 18, "dash"),
                                    (KLI.T_S_EXCELENTE, 23, "long_dash")):
            g.add_series({"name": t[nombre], "categories": zonas_b2,
                          "values": rango(b2, desp),
                          "line": linea(KLI.COLOR_ESPERADO, trazo=trazo)})
        graficas[KLI.T_G_SNR] = g

        # --- Curva tonal en L*: esperado, objetivo, sensor y
        #     revelador, con barras lilas hasta el esperado
        g = grafica("line", KLI.T_G_CURVA, KLI.EJE_LSTAR, KLI.T_EJE_LSTAR, b3)
        g.add_series({"name": t[KLI.T_CAB_ESPERADO], "categories": zonas_b3,
                      "values": rango(b3, 3),
                      "line": {**linea(KLI.COLOR_ESPERADO,
                                       KLI.ANCHO_ESPERADO),
                               "transparency": KLI.TRANSPARENCIA_ESPERADO}})
        g.add_series({"name": t[KLI.T_CAB_L_OBJETIVO],
                      "categories": zonas_b3, "values": rango(b3, 4),
                      "line": linea(KLI.COLOR_OBJETIVO, trazo="dash")})
        g.add_series({"name": t[KLI.T_S_SENSOR], "categories": zonas_b3,
                      "values": rango(b3, 6),
                      "line": linea(KLI.COLOR_SENSOR)})
        g.add_series({
            "name": t[KLI.T_S_REVELADOR], "categories": zonas_b3,
            "values": rango(b3, 8),
            "line": linea(KLI.COLORES_CANALES[2]),
            "marker": marcador(KLI.COLORES_CANALES[2]),
            "y_error_bars": {
                "type": "custom", "plus_values": rango(b3, 11),
                "minus_values": rango(b3, 12), "end_style": 0,
                "line": linea(KLI.COLOR_BARRAS, KLI.ANCHO_BARRAS)}})
        graficas[KLI.T_G_CURVA] = g

        # --- Diferencia en L*: sensor y revelador; las negativas, en
        #     rojo
        g = grafica("column", KLI.T_G_DIFERENCIA, KLI.EJE_DIF_LSTAR,
                    KLI.T_EJE_DIF_LSTAR, b3)
        for nombre, desp, color in (
                (KLI.T_S_SENSOR, KLI.CURVA_DIF_SENSOR, KLI.COLOR_SENSOR),
                (KLI.T_S_REVELADOR, KLI.CURVA_DIF_REVELADOR,
                 KLI.COLORES_CANALES[2])):
            g.add_series({"name": t[nombre], "categories": zonas_b3,
                          "values": rango(b3, desp),
                          "fill": {"color": color},
                          "invert_if_negative": True,
                          "invert_if_negative_color": KLI.COLOR_NEGATIVO})
        graficas[KLI.T_G_DIFERENCIA] = g

        # --- Los huecos, con su borde, y cada gráfica en el suyo
        gris = KLI.BORDE_HUECO
        ultima_fila = 0
        for i, clave in enumerate(KLI.ORDEN_GRAFICAS):
            g = graficas[clave]
            fila0 = KLI.FILA_HUECOS + (i // 2) * (KLI.FILAS_HUECO + 1)
            col0 = col + (i % 2) * (KLI.COLUMNAS_HUECO + 1)
            fila1 = fila0 + KLI.FILAS_HUECO - 1
            col1 = col0 + KLI.COLUMNAS_HUECO - 1
            for r in range(fila0, fila1 + 1):
                for c in range(col0, col1 + 1):
                    bordes: dict = {}
                    if r == fila0:
                        bordes.update(top=KLI.FINO, top_color=gris)
                    if r == fila1:
                        bordes.update(bottom=KLI.FINO, bottom_color=gris)
                    if c == col0:
                        bordes.update(left=KLI.FINO, left_color=gris)
                    if c == col1:
                        bordes.update(right=KLI.FINO, right_color=gris)
                    if bordes:
                        hoja.write_blank(r, c, None, self.formato(**bordes))
            hoja.insert_chart(fila0, col0, g,
                              {"x_offset": KLI.MARGEN_GRAFICA,
                               "y_offset": KLI.MARGEN_GRAFICA})
            ultima_fila = max(ultima_fila, fila1)
        self.marco(hoja, ((ultima_fila, KLI.ANCHOS_GRAFICOS),))

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
        hoja = self.__hojas[KLI.T_HOJA_RECHAZADAS]
        fila, col = KLI.FILA_INICIO, KLI.COLUMNA_INICIO
        self.titulo(hoja, fila, col, t[KLI.T_TITULO_RECHAZADAS],
                    t[KLI.T_NOTA_RECHAZADAS],
                    KLI.ANCHOS_RECHAZADAS)
        motivos = d.motivos.ravel()
        tarjeta = int((motivos != KTE.NO_TARJETA).sum())
        es_rechazada = (motivos != KTE.NO_TARJETA) & (motivos != KTE.BUENA)
        rechazadas = int(es_rechazada.sum())

        # --- Recuento
        fila += 3
        hoja.write(fila, col, t[KLI.T_RECUENTO], self.seccion())
        #     Junto a cada motivo, qué significa (en las columnas que
        #     quedan, partido en líneas)
        fila += 1
        ultima = col + len(KLI.ANCHOS_RECHAZADAS) - 1
        ancho_explica = sum(KLI.ANCHOS_RECHAZADAS[2:])
        self.cabecera(hoja, fila, col, (t[KLI.T_CAB_CONCEPTO],
                                        t[KLI.T_CAB_VALOR]))
        hoja.merge_range(fila, col + 2, fila, ultima, t[KLI.T_CAB_QUE_ES],
                         self.fmt_cabecera())
        umbrales = dict(nivel=self.tercios_texto(KTE.NIVEL_MAX_ZONAS),
                        rareza=KTE.RAREZA, lado=KTE.LADO)
        recuento = [(t[KLI.T_TESELAS_TARJETA], tarjeta, KLI.NUM_ENTERO, ""),
                    (t[KLI.T_TESELAS_RECHAZADAS], rechazadas,
                     KLI.NUM_ENTERO, ""),
                    (t[KLI.T_PORCENTAJE], KLI.CIEN * rechazadas / tarjeta
                     if tarjeta else 0.0, KLI.NUM_UNO, "")]
        recuento += [(t[KLI.T_POR_MOTIVO].format(motivo=t[clave]),
                      int((motivos == codigo).sum()), KLI.NUM_ENTERO,
                      t[KLI.EXPLICA_MOTIVO[codigo]].format(**umbrales))
                     for codigo, clave, _ in KLI.MOTIVOS]
        for i, (texto, valor, numero, explica) in enumerate(recuento):
            fila += 1
            banda = i % 2 == 0
            hoja.write(fila, col, texto,
                       self.celda(KLI.COLOR_ROTULO, banda, "left",
                                  valign="top"))
            hoja.write_number(fila, col + 1, valor,
                              self.celda(KLI.COLOR_DATO, banda, "center",
                                         numero, valign="top"))
            hoja.merge_range(fila, col + 2, fila, ultima, explica,
                             self.celda(KLI.COLOR_ROTULO, banda, "left",
                                        text_wrap=True, valign="top"))
            if explica:
                hoja.set_row(fila, KLI.ALTO_LINEA
                             * self.lineas(explica, ancho_explica))

        # --- Hueco del gráfico; los datos, debajo
        fila_grafico = fila + 2
        fila = fila_grafico + KLI.FILAS_HUECO + 1
        hoja.write(fila, col, t[KLI.T_DATOS_GRAFICO], self.seccion())
        fila += 1
        self.cabecera(hoja, fila, col, (t[KLI.T_CAB_ZONA],
                                        t[KLI.T_CAB_POSICION],
                                        t[KLI.T_CAB_MOTIVO],
                                        t[KLI.T_CAB_DESVIACION]))
        hoja.set_row(fila, KLI.ALTO_CABECERA)
        motivo_rechazada = motivos[es_rechazada]
        zona_zv = dict((c[0], c[1]) for c in KLI.CONSTANTES)[KLI.C_ZONA_ZV]
        tercios = dict((c[0], c[1]) for c in KLI.CONSTANTES)[
            KLI.C_TERCIO_POR_ZONA]
        series = []
        banda = True
        for codigo, clave, color in KLI.MOTIVOS:
            desde = fila + 1
            for i, zona in enumerate(d.zonas):
                if zona is None:
                    continue
                tercio_ev = i - KS.TERCIOS_LADO
                for desvio, motivo in zip(zona.desviacion, motivo_rechazada):
                    if (motivo != codigo or desvio is None
                            or not math.isfinite(desvio)):
                        continue
                    fila += 1
                    banda = not banda
                    hoja.write(fila, col, self.nombre_zona(tercio_ev),
                               self.celda(KLI.COLOR_LITERAL, banda,
                                          "center"))
                    hoja.write_number(fila, col + 1,
                                      zona_zv + tercio_ev / tercios,
                                      self.celda(KLI.COLOR_DATO, banda,
                                                 "center", KLI.NUM_DOS))
                    hoja.write(fila, col + 2, t[clave],
                               self.celda(KLI.COLOR_DATO, banda, "center"))
                    hoja.write_number(fila, col + 3, desvio,
                                      self.celda(KLI.COLOR_DATO, banda,
                                                 "center",
                                                 KLI.NUM_DESVIACION))
            if fila >= desde:
                series.append((t[clave], color, desde, fila))

        # --- El gráfico de dispersión, una serie por motivo
        g = self.__libro.add_chart({"type": "scatter"})
        g.set_title({"name": t[KLI.T_G_RECHAZADAS]})
        minimo, maximo, paso, numeros = KLI.EJE_POSICION
        g.set_x_axis({"name": t[KLI.T_EJE_ZONA], "min": minimo,
                      "max": maximo, "major_unit": paso,
                      "num_format": numeros})
        g.set_y_axis({"name": t[KLI.T_EJE_DESVIACION],
                      "num_format": KLI.NUM_DESVIACION})
        g.set_legend({"position": "bottom"})
        g.set_size({"width": KLI.TAMANO_GRAFICA[0],
                    "height": KLI.TAMANO_GRAFICA[1]})
        nombre = t[KLI.T_HOJA_RECHAZADAS]
        for texto, color, desde, hasta in series:
            g.add_series({
                "name": texto,
                "categories": f"='{nombre}'!" + xl_range_abs(
                    desde, col + 1, hasta, col + 1),
                "values": f"='{nombre}'!" + xl_range_abs(
                    desde, col + 3, hasta, col + 3),
                "marker": {"type": "circle", "size": KLI.TAMANO_MARCADOR,
                           "fill": {"color": color},
                           "border": {"color": color}}})
        hoja.insert_chart(fila_grafico, col, g,
                          {"x_offset": KLI.MARGEN_GRAFICA,
                           "y_offset": KLI.MARGEN_GRAFICA})
        self.marco(hoja, ((fila, KLI.ANCHOS_RECHAZADAS),))

    #
    def hoja_ia(self) -> None:
        """
        Hoja IA: las instrucciones para revisar el libro con una IA, de
        su archivo (siempre en español), una línea por fila: la IA las lee
        en las celdas. Las líneas de título, en negrita. Si el archivo no
        se puede leer, la hoja sale vacía
        """
        hoja = self.__hojas[KLI.T_HOJA_IA]
        col = KLI.COLUMNA_INICIO
        hoja.set_column(col, col, KLI.ANCHO_IA)
        normal = self.formato(text_wrap=True, valign="top")
        titulo = self.formato(text_wrap=True, valign="top", bold=True)
        try:
            lineas = KCOM.RUTA_PROMPT_IA.read_text(
                encoding="utf-8").splitlines()
        except OSError:
            lineas = []
        for i, linea in enumerate(lineas):
            if linea.strip():
                hoja.write_string(KLI.FILA_INICIO + i, col, linea,
                                  titulo if linea.startswith(
                                      KLI.MARCA_TITULO_IA) else normal)
        hoja.hide_gridlines(2)

    #
    def zonas_canal(self, k: dict) -> dict[str, list]:
        """
        Por zona y canal, lo que calcula el bloque 2 de Cálculo y usan el
        1 y canales: el esperado (en zonas), el obtenido (zona
        equivalente), la desviación y si está recortado (los textos de
        TextoRecortado y TextoNoRecortado; None sin toma).
        """
        t, d = self.__textos, self.__datos
        n = 2 * KS.TERCIOS_LADO + 1
        medias = self.medias_zv()
        zonas = [z.nivelRGB if z else None for z in d.zonas]
        esperado = [k[KLI.C_ZONA_ZV] + (i - KS.TERCIOS_LADO)
                    / k[KLI.C_TERCIO_POR_ZONA] for i in range(n)]
        maximos = self.maximos()
        obtenido = [[k[KLI.C_ZONA_ZV] + math.log(z[j] / medias[j],
                                                 k[KLI.C_FACTOR_ZONA])
                     if z and z[j] > 0 else None for z in zonas]
                    for j in range(KLI.CANALES)]
        desviacion = [[o - e if o is not None else None
                       for o, e in zip(obtenido[j], esperado)]
                      for j in range(KLI.CANALES)]
        recortado = [[None if z is None else (
            t[KLI.V_RECORTADO] if z[j] >= k[KLI.C_UMBRAL_RECORTE]
            * maximos[j] else t[KLI.V_NO_RECORTADO]) for z in zonas]
            for j in range(KLI.CANALES)]
        return {KLI.Z_ESPERADO: esperado, KLI.Z_OBTENIDO: obtenido,
                KLI.Z_DESVIACION: desviacion, KLI.Z_RECORTADO: recortado}

    #
    def maximos(self) -> list[float]:
        """ Máximo de cada canal en la serie (rojo, verde, azul). """
        zonas = [z.nivelRGB for z in self.__datos.zonas if z]
        return [max((z[j] for z in zonas), default=0.0)
                for j in range(KLI.CANALES)]

    #
    def canales(self, k: dict) -> list[dict[str, object]]:
        """
        Por canal (rojo, verde, azul), lo que da el bloque 1 de Cálculo:
        Z-V media, máximo, techo, suelo (RelacionSR), rango, último punto
        lineal, primer punto recortado, suelos sugerido (SNRMinima) y
        excelente (SNRExcelente) y la latitud sugerida (KLI.R_*). Lo que
        no se alcanza o falta, con el mismo texto o vacío que en el
        libro.
        """
        t = self.__textos
        medias, maximos = self.medias_zv(), self.maximos()
        por_zona = self.zonas_canal(k)
        esperado = por_zona[KLI.Z_ESPERADO]
        resultados = []
        for j in range(KLI.CANALES):
            techo = (k[KLI.C_ZONA_ZV] + math.log(maximos[j] / medias[j],
                                                 k[KLI.C_FACTOR_ZONA])
                     if maximos[j] > 0 and medias[j] > 0 else "")
            suelo = self.valor_suelo(KLI.C_RELACION_SR, j, k)
            lineales = [e for e, dvi, rci in zip(
                esperado, por_zona[KLI.Z_DESVIACION][j],
                por_zona[KLI.Z_RECORTADO][j])
                if dvi is not None and abs(dvi) <= k[KLI.C_TOLERANCIA_LINEAL]
                and rci == t[KLI.V_NO_RECORTADO]]
            primeros = [e for e, rci in zip(esperado,
                                            por_zona[KLI.Z_RECORTADO][j])
                        if rci == t[KLI.V_RECORTADO]]
            sugerido = self.valor_suelo(KLI.C_SNR_MINIMA, j, k)
            resultados.append({
                KLI.R_MEDIA_ZV: medias[j], KLI.R_MAXIMO: maximos[j],
                KLI.R_TECHO: techo, KLI.R_SUELO: suelo,
                KLI.R_RANGO: (techo - suelo if isinstance(techo, float)
                              and isinstance(suelo, float) else ""),
                KLI.R_ULTIMO_LINEAL: (max(lineales) if lineales
                                      else t[KLI.V_NINGUNO]),
                KLI.R_PRIMER_RECORTADO: (primeros[0] if primeros
                                         else t[KLI.V_NO_ALCANZADO]),
                KLI.R_SUELO_SUGERIDO: sugerido,
                KLI.R_SUELO_EXCELENTE: self.valor_suelo(KLI.C_SNR_EXCELENTE,
                                                        j, k),
                KLI.R_LATITUD: (self.latitud(max(lineales), sugerido, k)
                                if lineales else t[KLI.V_NO_ALCANZADO])})
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
                   for clave, canal in zip(KLI.CANALES_JSON,
                                           self.canales(k))}
        limites = self.limites_texturas(k, self.texturas(k))
        sin_pano = isinstance(self.__datos.pano, str)
        texturas = None if sin_pano else {
            clave: dict(zip(KLI.TEXTURAS_JSON, (self.numero_json(v)
                                                for v in valores)))
            for clave, valores in limites.items()}
        puntos = self.puntos_curva(k)
        curva = [{KLI.J_ZONA: p.nombre, KLI.J_TERCIO: p.tercio_ev,
                  KLI.J_ESPERADO: p.esperado, KLI.J_OBJETIVO: p.objetivo,
                  KLI.J_SENSOR: p.sensor, KLI.J_REVELADOR: p.revelador,
                  KLI.J_ENTRADA: p.entrada, KLI.J_SALIDA: p.salida,
                  KLI.J_PUNTO: p.tercio_ev % k[KLI.C_TERCIO_POR_ZONA] == 0}
                 for p in puntos]
        sensor = [abs(p.sensor - p.esperado) for p in puntos
                  if p.sensor is not None]
        revelador = [abs(p.revelador - p.esperado) for p in puntos
                     if p.revelador is not None]
        medias = {KLI.J_SENSOR: self.media(sensor),
                  KLI.J_REVELADOR: self.media(revelador)}
        return {KLI.J_CANALES: canales, KLI.J_TEXTURAS: texturas,
                KLI.J_CURVA: curva, KLI.J_DIFERENCIAS: medias}

    #
    @staticmethod
    def media(valores: list[float]) -> float | None:
        """ Media de unos valores, o None si no hay ninguno. """
        return sum(valores) / len(valores) if valores else None

    #
    @staticmethod
    def numero_json(valor: object) -> float | None:
        """ Un resultado para el JSON: el número, o None si no lo es. """
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            return float(valor) if math.isfinite(valor) else None
        return None

    #
    def puntos_curva(self, k: dict) -> list[PuntoCurva]:
        """
        La curva tonal en L*, zona a zona (de Z0 a ZX): lo que escribe el
        bloque 3 de Cálculo y dibuja la ficha PDF. Esperado: un paso de
        luz por zona desde la ZV, hasta el blanco; objetivo: LPorZona por
        zona; sensor: el verde de la zona entre el de la ZV (media);
        revelador: el de Datos (leído o estimado).
        """
        medias = self.medias_zv()
        lzv = self.lab_a_luz(k[KLI.C_LZV], k)
        puntos = []
        for i, zona in enumerate(self.__datos.zonas):
            tercio_ev = i - KS.TERCIOS_LADO
            luz_esp = self.luz_esperada(tercio_ev, k)
            luz_sen = (min(1.0, lzv * zona.nivelRGB[1] / medias[1])
                       if zona and zona.nivelRGB[1] > 0 else None)
            l_rev = self.__revelador[i]
            luz_rev = None if l_rev is None else self.lab_a_luz(l_rev, k)
            puntos.append(PuntoCurva(
                tercio_ev, self.nombre_zona(tercio_ev), luz_esp,
                self.luz_a_lab(luz_esp, k),
                k[KLI.C_L_POR_ZONA] * (k[KLI.C_ZONA_ZV] + tercio_ev
                                       / k[KLI.C_TERCIO_POR_ZONA]),
                luz_sen, None if luz_sen is None
                else self.luz_a_lab(luz_sen, k), luz_rev, l_rev,
                None if luz_rev is None else self.curva(luz_rev, k),
                self.curva(luz_esp, k)))
        return puntos

    #
    def medias_zv(self) -> list[float]:
        """ Media de las Z-V (la de la serie y las de control) por canal. """
        d = self.__datos
        zv = d.zonas[KS.TERCIOS_LADO]
        desviados = d.controlesDesviados
        valores = [v.nivelRGB for v in [zv] + list(d.control[:KLI.CONTROLES])
                   if v is not None and v not in desviados]
        return [sum(v[j] for v in valores) / len(valores) if valores else 0.0
                for j in range(KLI.CANALES)]

    #
    def valores_constantes(self) -> dict:
        """ Valor de cada constante del libro: {nombre: valor}. """
        k = {nombre: valor for nombre, valor, _ in KLI.CONSTANTES}
        k[KLI.C_LUZ_POR_TERCIO] = (k[KLI.C_FACTOR_ZONA]
                                   ** (1 / k[KLI.C_TERCIO_POR_ZONA]))
        k[KLI.C_LUZ_ZV] = self.lab_a_luz(k[KLI.C_LZV], k)
        return k

    #
    def texturas(self, k: dict) -> dict[str, list]:
        """
        Latitud de texturas del verde, por zona (de Z0 a ZX): esperado,
        textura del paño (su dispersión sin el ruido de la tarjeta),
        textura/ruido, textura conservada (frente a la de la ZV), paño
        recortado y si cumple cada criterio (sombras: textura/ruido de
        RoseTextura en adelante hasta la ZV; luces: desde la ZV, textura
        conservada de TexturaConservada y paño recortado de
        PanoRecortadoMax como mucho). None: sin dato o fuera de su lado.
        """
        n = 2 * KS.TERCIOS_LADO + 1
        zv = KS.TERCIOS_LADO
        verde = 1
        esperado = [k[KLI.C_ZONA_ZV] + (i - zv) / k[KLI.C_TERCIO_POR_ZONA]
                    for i in range(n)]
        textura, ruido, recortado = [], [], []
        for z in self.__datos.zonas:
            pano = z.panoDispersionRGB if z else None
            tarjeta = z.dispersionRGB[verde] if z else None
            if (pano is None or tarjeta is None or not math.isfinite(tarjeta)
                    or not math.isfinite(pano[verde])):
                textura.append(None)
                ruido.append(None)
            else:
                tx = math.sqrt(max(0.0, pano[verde] ** 2 - tarjeta ** 2))
                textura.append(tx)
                ruido.append(tx / tarjeta if tarjeta > 0 else None)
            recorte = z.panoRecortadoRGB if z else None
            recortado.append(recorte[verde] if recorte
                             and math.isfinite(recorte[verde]) else None)
        base = textura[zv]
        conservada = [tx / base if tx is not None and base else None
                      for tx in textura]

        # --- Sombras, de la ZV hacia abajo; luces, de la ZV hacia arriba.
        #     Un tercio sin dato no corta la cadena: deja pasar lo que
        #     viene del lado de la ZV
        sombras: list = [None] * n
        luces: list = [None] * n
        sin_recorte: list = [None] * n
        for i in range(zv, -1, -1):
            sigue = True if i == zv else sombras[i + 1]
            sombras[i] = (sigue if ruido[i] is None else
                          ruido[i] >= k[KLI.C_ROSE_TEXTURA] and sigue)
        for i in range(zv, n):
            luz = True if i == zv else luces[i - 1]
            corte = True if i == zv else sin_recorte[i - 1]
            luces[i] = (luz if conservada[i] is None else
                        conservada[i] >= k[KLI.C_TEXTURA_CONSERVADA] and luz)
            sin_recorte[i] = (
                corte if recortado[i] is None else
                recortado[i] <= k[KLI.C_PANO_RECORTADO_MAX] and corte)
        return {KLI.T_CAB_ESPERADO: esperado, KLI.T_CAB_TEXTURA: textura,
                KLI.T_CAB_TEXTURA_RUIDO: ruido,
                KLI.T_CAB_CONSERVADA: conservada,
                KLI.T_CAB_PANO_RECORTADO: recortado,
                KLI.T_CAB_CUMPLE_SOMBRAS: sombras,
                KLI.T_CAB_CUMPLE_LUCES: luces,
                KLI.T_CAB_SIN_RECORTE: sin_recorte}

    #
    def limites_texturas(self, k: dict, por_zona: dict[str, list]
                         ) -> dict[str, object]:
        """
        Límites de la latitud de texturas (en zonas; si no se alcanzan, el
        texto de TextoNoAlcanzado): sombras apreciables (donde la
        textura/ruido llega a RoseTextura, entre los dos tercios vecinos y
        al tercio más próximo; sin dato en el de debajo, el tercio que
        cumple) y recomendadas (MargenSombras tercios más arriba), luces
        apreciables (la última con la textura conservada) y recomendadas
        (la última sin pasar de PanoRecortadoMax, sin pasar de la
        apreciable) y las dos latitudes. Solo cuentan los tercios con dato.
        """
        no = self.__textos[KLI.V_NO_ALCANZADO]
        tercio = k[KLI.C_TERCIO_POR_ZONA]
        es = por_zona[KLI.T_CAB_ESPERADO]
        ruido = por_zona[KLI.T_CAB_TEXTURA_RUIDO]
        cumple = por_zona[KLI.T_CAB_CUMPLE_SOMBRAS]
        primera = next((i for i, c in enumerate(cumple)
                        if c and ruido[i] is not None), None)
        if primera is None:
            sombra = no
        elif primera == 0 or ruido[primera - 1] is None:
            sombra = es[primera]
        else:
            antes = primera - 1
            cruce = es[antes] + ((k[KLI.C_ROSE_TEXTURA] - ruido[antes])
                                 / (ruido[primera] - ruido[antes]) / tercio)
            # --- Al tercio más próximo; el medio, hacia arriba (como
            #     ROUND de Excel; round() de Python iría al par)
            sombra = math.floor(cruce * tercio + 0.5) / tercio
        sombra_rec = (sombra + k[KLI.C_MARGEN_SOMBRAS] / tercio
                      if isinstance(sombra, float) else sombra)
        luces = [e for e, c, v in zip(es, por_zona[KLI.T_CAB_CUMPLE_LUCES],
                                      por_zona[KLI.T_CAB_CONSERVADA])
                 if c and v is not None]
        luz = max(luces) if luces else no
        cortes = [e for e, c, v in zip(es, por_zona[KLI.T_CAB_SIN_RECORTE],
                                       por_zona[KLI.T_CAB_PANO_RECORTADO])
                  if c and v is not None]
        luz_rec = ((min(luz, max(cortes)) if isinstance(luz, float)
                    else max(cortes)) if cortes else no)
        return {KLI.T_APRECIABLE: (sombra, luz,
                                   self.latitud(luz, sombra, k)),
                KLI.T_RECOMENDADA: (sombra_rec, luz_rec,
                                    self.latitud(luz_rec, sombra_rec, k))}

    #
    def latitud(self, alto: object, bajo: object, k: dict) -> object:
        """
        Latitud entre dos zonas, contando las dos puntas (de Z3 a Z8, 6
        zonas): alto − bajo + AnchoZona, si los dos son números; si no,
        TextoNoAlcanzado.
        """
        if isinstance(alto, float) and isinstance(bajo, float):
            return alto - bajo + k[KLI.C_ANCHO_ZONA]
        return self.__textos[KLI.V_NO_ALCANZADO]

    #
    def suelo_snr(self, snr: str, j: int, zv: str) -> str:
        """
        Suelo de un canal (j: rojo, verde, azul), en zonas: donde la
        señal/ruido, normalizada a MpxReferencia, llega a la constante
        snr, según la curva de transferencia de Datos (la raíz positiva
        de (1 − T²·p²)·S² − (T²/g)·S − T²·l² = 0, con T la señal/ruido de
        un píxel). zv: la celda de la Z-V media del canal. La fórmula; su
        resultado, valor_suelo.
        """
        f = self.__filas
        c = KLI.COLUMNA_INICIO + KLI.COL_VALORES + j
        lectura, ganancia, proporcional = (
            self.ref(KLI.T_HOJA_DATOS, f[clave], c, True, True)
            for clave in (KLI.F_LECTURA, KLI.F_GANANCIA, KLI.F_PROPORCIONAL))
        mpx = self.ref(KLI.T_HOJA_DATOS, f[KLI.F_MPX],
                       KLI.COLUMNA_INICIO + KLI.COL_VALORES, True, True)
        t2 = f"({snr}^2*{KLI.C_MPX_REFERENCIA}/{mpx})"
        a = f"(1-{t2}*N({proporcional})^2)"
        b = f"({t2}/{ganancia})"
        senal = (f"(({b}+SQRT({b}^2+4*{a}*{t2}*N({lectura})^2))"
                 f"/(2*{a}))")
        return (f'=IF(AND(N({ganancia})>0,N({zv})>0),IF({a}>0,'
                f'{KLI.C_ZONA_ZV}+LOG({senal}/{zv},{KLI.C_FACTOR_ZONA}),'
                f'{KLI.C_TEXTO_NO_ALCANZADO}),"")')

    #
    def valor_suelo(self, snr: str, j: int, k: dict) -> object:
        """
        Suelo de un canal (j: rojo, verde, azul), en zonas, como el de
        suelo_snr: no alcanzado si la parte proporcional lo impide; ""
        sin curva.
        """
        d = self.__datos
        curvas, medias = d.transferenciaRGB, self.medias_zv()
        if not curvas or medias[j] <= 0:
            return ""
        escala = escala_mpx(d.alto, d.ancho, k[KLI.C_MPX_REFERENCIA])
        senal_suelo = senal_para_snr(curvas[j], k[snr] / escala)
        if senal_suelo is None:
            return self.__textos[KLI.V_NO_ALCANZADO]
        return k[KLI.C_ZONA_ZV] + math.log(senal_suelo / medias[j],
                                           k[KLI.C_FACTOR_ZONA])

    #
    def luz_esperada(self, tercio_ev: int, k: dict) -> float:
        """
        Luz esperada de una zona: un paso de luz por zona desde la ZV
        (la de L* LZV), hasta el blanco de pantalla.
        """
        lzv = self.lab_a_luz(k[KLI.C_LZV], k)
        return min(1.0, lzv * k[KLI.C_FACTOR_ZONA] ** (
            tercio_ev / k[KLI.C_TERCIO_POR_ZONA]))

    #
    def revelador_medido(self) -> list[float | None]:
        """
        L* del revelador medido en las TIFF, por zona (None: sin medir);
        todo None si aún no se midieron.
        """
        n = 2 * KS.TERCIOS_LADO + 1
        medido = list(self.__datos.revelador or (None,) * n)
        return [None if v is None or math.isnan(v) else v for v in medido]

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
        por_zona = k[KLI.C_TERCIO_POR_ZONA]
        medido = self.revelador_medido()
        esperado = [self.luz_a_lab(self.luz_esperada(
            i - KS.TERCIOS_LADO, k), k) for i in range(len(medido))]
        estimado = list(medido)
        for i, valor in enumerate(medido):
            tercio = (i - KS.TERCIOS_LADO) % por_zona
            if valor is not None or tercio == 0:
                continue
            antes, despues = i - tercio, i - tercio + por_zona
            if medido[antes] is None or medido[despues] is None:
                continue
            dif_antes = medido[antes] - esperado[antes]
            dif_despues = medido[despues] - esperado[despues]
            recta = (esperado[i] + dif_antes + (dif_despues - dif_antes)
                     * tercio / por_zona)
            estimado[i] = sorted((medido[antes], medido[despues], recta))[1]
        return estimado

    #
    @staticmethod
    def luz_a_lab(luz: float, k: dict) -> float:
        """ L* de una luminancia relativa (CIELAB), como en el libro. """
        if luz > k[KLI.C_LAB_UMBRAL]:
            return k[KLI.C_LAB_ESCALA] * luz ** (1 / 3) - k[KLI.C_LAB_DESPLAZA]
        return k[KLI.C_LAB_PENDIENTE] * luz

    #
    @staticmethod
    def lab_a_luz(lab: float, k: dict) -> float:
        """ Luminancia relativa de un L* (inversa de CIELAB). """
        if lab > k[KLI.C_LAB_UMBRAL] * k[KLI.C_LAB_PENDIENTE]:
            return ((lab + k[KLI.C_LAB_DESPLAZA]) / k[KLI.C_LAB_ESCALA]) ** 3
        return lab / k[KLI.C_LAB_PENDIENTE]

    #
    @staticmethod
    def curva(luz: float, k: dict) -> int:
        """ Valor de 0 a 255 de la curva de Lightroom (sRGB) de una luz. """
        if luz <= k[KLI.C_SRGB_UMBRAL]:
            srgb = k[KLI.C_SRGB_PENDIENTE] * luz
        else:
            srgb = (k[KLI.C_SRGB_ESCALA] * luz ** (1 / k[KLI.C_SRGB_GAMMA])
                    - k[KLI.C_SRGB_DESPLAZA])
        return round(k[KLI.C_ESCALA_CURVA] * srgb)

    #
    @staticmethod
    def formula_lab(luz: str) -> str:
        """ Fórmula del L* de la luz de esta celda. """
        return (f"IF({luz}>{KLI.C_LAB_UMBRAL},{KLI.C_LAB_ESCALA}*{luz}^(1/3)"
                f"-{KLI.C_LAB_DESPLAZA},{KLI.C_LAB_PENDIENTE}*{luz})")

    #
    @staticmethod
    def formula_curva(luz: str) -> str:
        """ Fórmula del valor de 0 a 255 de la curva de la luz de la celda. """
        return (f"ROUND({KLI.C_ESCALA_CURVA}*IF({luz}<={KLI.C_SRGB_UMBRAL},"
                f"{KLI.C_SRGB_PENDIENTE}*{luz},{KLI.C_SRGB_ESCALA}*{luz}^(1/"
                f"{KLI.C_SRGB_GAMMA})-{KLI.C_SRGB_DESPLAZA}),0)")

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
        return getattr(celda, "value", "") if celda is not None else ""

    #
    @staticmethod
    def vacio(valor: object) -> object:
        """ Resultado de una fórmula que da "" si no hay dato (None). """
        return "" if valor is None else valor

    # endregion Métodos públicos

    #
    # --- Piezas comunes de las hojas
    #
    # region Piezas comunes

    #
    def marco(self, hoja: Worksheet,
              tarjetas: tuple[tuple[int, tuple[float | None, ...]], ...],
              anillo: str = KLI.ANILLO, ancho_anillo: float = KLI.ANCHO_ANILLO,
              ancho_relleno: float = KLI.ANCHO_RELLENO,
              alto: float | None = None) -> None:
        """
        Marco «tarjeta» de una hoja: una o varias tarjetas, una al lado de
        la otra, cada una (última fila de su contenido, anchos de sus
        columnas; None: oculta). La primera empieza en C3 y las demás,
        tras relleno, anillo y relleno (KLI.ENTRE_TARJETAS). Anillo gris
        alrededor y entre ellas; cada tarjeta, con borde medio y relleno.
        Oculta las columnas de la derecha y las filas de debajo;
        cuadrícula oculta; impresión apaisada, de una página de ancho.
        alto: el de las filas (None: el de Excel).
        """
        primera_fila = KLI.FILA_INICIO - 1
        fila_anillo = max(ultima for ultima, _ in tarjetas) + 2

        # --- Anchos: anillo y, por tarjeta, relleno, contenido, relleno
        #     y anillo. Cada tarjeta: (primera columna, columna de cierre,
        #     fila de cierre)
        hoja.set_column(0, 0, ancho_anillo)
        cajas = []
        col_contenido = KLI.COLUMNA_INICIO
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
            col_contenido += len(anchos) + KLI.ENTRE_TARJETAS
        col_anillo = cajas[-1][1] + 1
        hoja.set_column(col_anillo + 1, KLI.ULTIMA_COLUMNA_EXCEL, None,
                        None, {"hidden": True})

        # --- Anillo: todo lo que queda fuera de las tarjetas
        gris = self.formato(bg_color=anillo, pattern=1)
        for f in range(fila_anillo + 1):
            for c in range(col_anillo + 1):
                if not any(desde <= c <= hasta and primera_fila <= f <= cierre
                           for desde, hasta, cierre in cajas):
                    hoja.write_blank(f, c, None, gris)

        # --- Cada tarjeta: borde medio por fuera de su relleno
        for desde, hasta, cierre in cajas:
            for c in range(desde, hasta + 1):
                for f, lado in ((primera_fila, "top"), (cierre, "bottom")):
                    bordes = {lado: KLI.MEDIO}
                    if c == desde:
                        bordes["left"] = KLI.MEDIO
                    if c == hasta:
                        bordes["right"] = KLI.MEDIO
                    hoja.write_blank(f, c, None, self.formato(**bordes))
            for f in range(primera_fila + 1, cierre):
                hoja.write_blank(f, desde, None,
                                 self.formato(left=KLI.MEDIO))
                hoja.write_blank(f, hasta, None,
                                 self.formato(right=KLI.MEDIO))

        hoja.set_default_row(alto, hide_unused_rows=True)
        hoja.hide_gridlines(2)
        hoja.set_landscape()
        hoja.fit_to_pages(1, 0)

    #
    @staticmethod
    def columna_derecha() -> int:
        """ Primera columna de la tarjeta derecha de Análisis. """
        return (KLI.COLUMNA_INICIO + len(KLI.ANCHOS_ANALISIS)
                + KLI.ENTRE_TARJETAS)

    #
    def fmt_analisis(self, tamano: int = KLI.TAMANO_ANALISIS,
                     **mas: object) -> object:
        """ Formato de Análisis: su fuente, en este tamaño. """
        return self.formato(font_name=KLI.FUENTE_ANALISIS, font_size=tamano,
                            **mas)

    #
    def fondo_analisis(self, tamano: int = KLI.TAMANO_ANALISIS,
                      **mas: object) -> object:
        """
        Formato de Análisis en blanco y negrita sobre el color de las
        cabeceras.
        """
        return self.fmt_analisis(tamano, bold=True,
                                 font_color=KLI.CABECERA_TEXTO,
                                 bg_color=KLI.CABECERA_FONDO, pattern=1,
                                 **mas)

    #
    def barra_analisis(self, hoja: Worksheet, fila: int, col: int,
                       ultima: int, texto: str) -> None:
        """ Barra de una sección de Análisis, de col a ultima. """
        hoja.merge_range(fila, col, fila, ultima, texto,
                         self.fondo_analisis(align="center",
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
        formato = self.cabecera_analisis()
        abajo = fila + filas - 1
        for texto, ancho in columnas:
            if ancho > 1 or filas > 1:
                hoja.merge_range(fila, col, abajo, col + ancho - 1, texto,
                                 formato)
            else:
                hoja.write(fila, col, texto, formato)
            col += ancho
        return abajo

    #
    def nota_tarjeta(self, hoja: Worksheet, fila: int, col: int,
                     ultima: int, texto: str,
                     anchos: tuple[float, ...], formato: object,
                     formula: str | None = None,
                     medida: str | None = None) -> int:
        """
        Nota de Análisis de col a ultima, en las filas de la rejilla que
        piden sus líneas (las de medida, si se da: el texto más largo que
        puede salir). Con fórmula, la escribe con texto como resultado.
        Devuelve su última fila.
        """
        abajo = fila + self.filas_texto(medida or texto, sum(anchos),
                                        KLI.ALTO_LINEA_NOTA) - 1
        hoja.merge_range(fila, col, abajo, ultima,
                         "" if formula else texto, formato)
        if formula is not None:
            hoja.write_formula(fila, col, formula, formato, texto)
        return abajo

    #
    def filas_texto(self, texto: str, ancho: float, alto_linea: float) -> int:
        """
        Filas de la rejilla de Análisis que ocupa un texto en este ancho,
        con líneas de este alto.
        """
        return max(1, math.ceil(self.lineas(texto, ancho) * alto_linea
                                / KLI.ALTO_REJILLA))

    #
    def nota_analisis(self, color: str) -> object:
        """ Formato de una nota de Análisis, en su color. """
        return self.fmt_analisis(KLI.TAMANO_ANALISIS_NOTA, font_color=color,
                                 text_wrap=True, align="left", valign="top")

    #
    def cabecera_analisis(self) -> object:
        """ Formato de la cabecera de una tabla de Análisis. """
        return self.fondo_analisis(KLI.TAMANO_ANALISIS_NOTA, text_wrap=True,
                                  align="center", valign="vcenter",
                                  border=KLI.FINO)

    #
    def celda_analisis(self, banda: bool, alineado: str,
                       numero: str | None = None, **mas: object) -> object:
        """
        Formato de una celda de tabla de Análisis: fila alterna (con
        fondo), alineación y formato de número.
        """
        propiedades: dict = dict(align=alineado, valign="vcenter",
                                 border=KLI.FINO,
                                 border_color=KLI.BORDE_TABLA, **mas)
        if banda:
            propiedades.update(bg_color=KLI.BANDA, pattern=1)
        if numero:
            propiedades["num_format"] = numero
        return self.fmt_analisis(KLI.TAMANO_ANALISIS_TABLA, **propiedades)

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
        dato = self.celda(KLI.COLOR_DATO, banda, "center")
        archivo = col + KLI.COL_VALORES - 1
        if toma is None:
            for c in range(archivo, archivo + 1 + 2 * KLI.CANALES):
                hoja.write_blank(fila, c, None, dato)
            return
        hoja.write(fila, archivo, toma.archivo, dato)
        for j, valor in enumerate(toma.nivelRGB + toma.dispersionRGB):
            formato = self.celda(KLI.COLOR_DATO, banda, "center",
                                 KLI.NUM_UNO if j < KLI.CANALES
                                 else KLI.NUM_TRES)
            if math.isfinite(valor):
                hoja.write_number(fila, col + KLI.COL_VALORES + j, valor,
                                  formato)
            else:
                hoja.write_blank(fila, col + KLI.COL_VALORES + j, None,
                                 formato)

    #
    def fila_canales(self, hoja: Worksheet, fila: int, col: int,
                     valores: tuple[float, float, float] | None,
                     banda: bool, numero: str) -> None:
        """
        Rojo, verde y azul de una fila de Datos (datos, con este formato
        de número), desde la primera columna de valores; sin valores (o
        un valor no finito), en blanco con su formato.
        """
        dato = self.celda(KLI.COLOR_DATO, banda, "center", numero)
        for j in range(KLI.CANALES):
            c = col + KLI.COL_VALORES + j
            if valores and math.isfinite(valores[j]):
                hoja.write_number(fila, c, valores[j], dato)
            else:
                hoja.write_blank(fila, c, None, dato)

    #
    def zona_y_tercios(self, hoja: Worksheet, fila: int, col: int,
                       tercio_ev: int, banda: bool) -> None:
        """ Nombre de la zona y sus tercios respecto a la ZV (literales). """
        hoja.write(fila, col, self.nombre_zona(tercio_ev),
                   self.celda(KLI.COLOR_LITERAL, banda, "center"))
        hoja.write_number(fila, col + 1, tercio_ev,
                          self.celda(KLI.COLOR_LITERAL, banda, "center",
                                     KLI.NUM_ENTERO))

    #
    def nombre_balance(self, nombre: str | None) -> str:
        """
        Nombre traducido de un balance (DAYLIGHT…; los preajustes con
        número, PRESET2, como «Preajuste 2»), o tal cual.
        """
        if nombre is None:
            return ""
        preset = re.fullmatch(KLI.PATRON_PRESET, nombre)
        if preset:
            return self.__textos[KLI.T_PRESET].format(n=preset.group(1))
        return self.__textos.get(KLI.PREFIJO_BALANCE + nombre, nombre)

    #
    @staticmethod
    def nombre_zona(tercio_ev: int) -> str:
        """ Nombre de una zona en el libro: Z0, Z0 1/3, … ZV, … ZX. """
        entera, tercio = zona_tercio(tercio_ev)
        return (f"{KP.PREFIJO}{KP.ROMANOS.get(entera, entera)}"
                f"{KLI.TERCIOS_LIBRO[tercio]}")

    #
    def titulo(self, hoja: Worksheet, fila: int, col: int, titulo: str,
               nota: str, anchos: tuple[float | None, ...]) -> None:
        """
        Título de la hoja y, debajo, su nota en gris (en las columnas de
        anchos, ver nota).
        """
        hoja.write(fila, col, titulo,
                   self.formato(bold=True, font_size=KLI.TAMANO_TITULO))
        self.nota(hoja, fila + 1, col, nota, anchos)

    #
    def nota(self, hoja: Worksheet, fila: int, col: int, texto: str,
             anchos: tuple[float | None, ...], formato: object = None,
             formula: str | None = None) -> None:
        """
        Nota en gris (o en este formato) partida en líneas: ocupa las
        columnas de anchos (las de su tabla, desde col) que caben en
        KLI.ANCHO_NOTA, y la fila crece según las líneas. Con fórmula, la
        escribe con texto como resultado.
        """
        ancho, columnas = 0.0, 0
        for a in anchos:
            if columnas and ancho + (a or 0) > KLI.ANCHO_NOTA:
                break
            ancho += a or 0
            columnas += 1
        if formato is None:
            formato = self.formato(font_color=KLI.COLOR_ROTULO,
                                   text_wrap=True, valign="top")
        if columnas > 1:
            hoja.merge_range(fila, col, fila, col + columnas - 1,
                             "" if formula else texto, formato)
        elif formula is None:
            hoja.write(fila, col, texto, formato)
        if formula is not None:
            hoja.write_formula(fila, col, formula, formato, texto)
        hoja.set_row(fila, KLI.ALTO_LINEA * self.lineas(texto, ancho))

    #
    @staticmethod
    def lineas(texto: str, ancho: float) -> int:
        """ Líneas que ocupa un texto en una celda de este ancho. """
        return sum(max(1, math.ceil(len(parrafo) * KLI.ANCHO_LETRA / ancho))
                   for parrafo in texto.split("\n"))

    #
    def rotulo_fila(self, hoja: Worksheet, fila: int, col: int, texto: str,
                    formato: object) -> None:
        """
        Rótulo de una fila de Datos, en las KLI.COLUMNAS_ROTULO primeras
        columnas (no cabe en una).
        """
        hoja.merge_range(fila, col, fila, col + KLI.COLUMNAS_ROTULO - 1,
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
    def fmt_cabecera(self) -> object:
        """ Formato de la cabecera de una tabla. """
        return self.formato(
            bold=True, font_color=KLI.CABECERA_TEXTO,
            bg_color=KLI.CABECERA_FONDO, pattern=1, text_wrap=True,
            align="center", valign="vcenter", border=KLI.FINO)

    #
    @staticmethod
    def tercios_texto(zonas: float) -> str:
        """ Zonas en tercios, como en el libro: 1/3, 2/3, 1, 1 1/3… """
        tercios = round(zonas * len(KLI.TERCIOS_LIBRO))
        entera, resto = divmod(tercios, len(KLI.TERCIOS_LIBRO))
        texto = f"{entera}{KLI.TERCIOS_LIBRO[resto]}" if entera else \
            KLI.TERCIOS_LIBRO[resto].strip()
        return texto or "0"

    #
    def celda(self, color: str, banda: bool, alineado: str,
              numero: str | None = None, **mas: object) -> object:
        """
        Formato de una celda de tabla: color del texto, fila alterna (con
        fondo), alineación, formato de número y más propiedades.
        """
        propiedades: dict = dict(font_color=color, align=alineado,
                                 border=KLI.FINO,
                                 border_color=KLI.BORDE_TABLA, **mas)
        if banda:
            propiedades.update(bg_color=KLI.BANDA, pattern=1)
        if numero:
            propiedades["num_format"] = numero
        return self.formato(**propiedades)

    #
    def texto(self, color: str, negrita: bool = False) -> object:
        """ Formato de un texto suelto, en su color. """
        return self.formato(font_color=color, bold=negrita)

    #
    def seccion(self) -> object:
        """ Formato del título de una sección de la hoja. """
        return self.formato(bold=True, font_size=KLI.TAMANO_SECCION)

    #
    @staticmethod
    def cadena(texto: str) -> str:
        """ Texto como cadena de una fórmula: entre comillas, dobladas. """
        comilla = KLI.COMILLA
        return f"{comilla}{texto.replace(comilla, comilla * 2)}{comilla}"

    #
    def formato(self, **propiedades: object) -> object:
        """
        Formato con estas propiedades (sin fuente: la del libro, en su
        tamaño: XlsxWriter pondría Calibri 11); los iguales se reutilizan.
        """
        propiedades.setdefault("font_name", KLI.FUENTE)
        propiedades.setdefault("font_size", KLI.TAMANO)
        clave = tuple(sorted(propiedades.items()))
        if clave not in self.__formatos:
            self.__formatos[clave] = self.__libro.add_format(
                dict(propiedades))
        return self.__formatos[clave]

    # endregion Piezas comunes
