# -*- coding: utf-8 *-*
"""
    :Propósito: Lo común a los mediadores: lo que necesita saber quien
                lee el JSON del estudio (FE, que no lleva el código de PyOECF),
                como las claves de sus grupos y la versión de su formato. Solo
                depende de std: nunca de otros paquetes de PyOECF. Lleva
                también lo que solo usa PyOECF (KP y parte de KFR…): FE
                no lo necesita, pero separarlo cuesta mucho de programar
                (muchos imports de oecfCalc y la réplica de FE) y no se
                hace
    :Autor:     Tony Diana
    :Versión:   26.11.10
"""

# cSpell:ignore camara, codificacion, codigo, desviacion, kmed, kres
# cSpell:ignore límpiela, lstar, oecf, repítela

__all__ = ["KES", "KI", "KRES", "KMA", "MARCADORES_INCIDENCIA",
           "TEXTOS_INCIDENCIA_ES", "KMED", "KP", "KFR", "TXT_DONDE", "TXT_Y",
           "TEXTOS_LADO", "partes_version", "estado_version",
           "version_formato", "zona_tercio", "texto_zona", "texto_iso",
           "ident_toma", "marcadores_incidencia"]

# --- Bibliotecas estándar Python
import builtins
import re
from collections.abc import Mapping, Sequence
from pathlib import PurePath

# --- Bibliotecas internas
from bib import std

# --- Marcador de textos traducibles: en FE existe un «_» (el de gettext) y
#     devuelve el texto en su idioma; donde no existe (PyOECF, que traduce
#     con sus diccionarios), devuelve el español tal cual
_ = getattr(builtins, "_", lambda texto: texto)


#
# --- Constantes de los datos
class KES(std.EnumMutable):
    """ Constantes del JSON del estudio. """

    # --- Codificación del archivo, al escribirlo y al leerlo
    CODIFICACION = "utf-8"

    # --- Nombre del JSON dentro de la carpeta OECF del estudio
    ARCHIVO = "estudio.json"

    # --- Grupos del JSON, en su orden. Claves en camelCase (las siglas, en
    #     mayúsculas: WB, ZV). Las etapas del análisis (medida, revelado y
    #     resultados) valen null hasta que se hacen (Tony, 2026-10-21)
    OECF = "oecf"
    INFO = "info"
    SERIE = "serie"
    INCIDENCIAS = "incidencias"
    MEDIDA = "medida"
    REVELADO = "revelado"
    RESULTADOS = "resultados"

    # --- oecf: las tres versiones del estudio, cada una por su motivo
    #     (Tony, 2026-11-13):
    #     - versionApp: la del programa que lo grabó (sube en cada
    #       publicación); la da quien llama a grabar_json
    #     - versionAnalisis: la de cómo se miden los RAW
    #       (review.KAN.VERSION_ANALISIS); null sin medida. Si es anterior
    #       a la de la app, hay que volver a medir
    #     - versionFormato: la de las claves de este JSON (VERSION_FORMATO,
    #       MAYOR.MENOR). Es lo primero que mira quien lo lee (FE). SI
    #       CAMBIAS, AÑADES O QUITAS UNA CLAVE (aquí, en review.KAN o en
    #       excel.KXL), SUBE ESTA VERSIÓN:
    #       - MAYOR: se quita o renombra una clave, o cambia lo que
    #         significa (quien lee una versión más nueva que la suya la
    #         rechaza; una más antigua, puede leerla si se programa)
    #       - MENOR: se añade una clave (quien lee ignora lo que no conoce)
    #     Historia del formato: 1.0, la primera que leen PyOECF y FE
    #     (2026-10-23); 1.1, medida.factorLamina (2026-11-13); 2.0, las
    #     tres versiones en oecf y sin info.programa.version (2026-11-13);
    #     2.1, revelado.exportaciones[].contraste (2026-11-13).
    #     Los JSON 1.x guardaban la del formato en oecf.version
    #     (O_VERSION_ANTIGUA): ver version_formato
    O_VERSION_ANALISIS = "versionAnalisis"
    O_VERSION_ANTIGUA = "version"
    O_VERSION_APP = "versionApp"
    O_VERSION_FORMATO = "versionFormato"
    VERSION_FORMATO = "2.1"

    # --- info: de dónde sale el archivo; nada de aquí se usa para
    #     calcular. El programa que lo grabó, {nombre} (su versión, en
    #     oecf.versionApp), lo da quien llama a grabar_json: este módulo
    #     no sabe qué programa lo usa. La carpeta de la serie, solo para
    #     saber el origen (Tony, 2026-10-21). La cámara, {marca, modelo}
    #     (la lee restaurar_serie si no queda ninguna copia RAW)
    I_PROGRAMA = "programa"
    P_NOMBRE = "nombre"
    I_FECHA = "fecha"
    I_CARPETA = "carpeta"
    I_CAMARA = "camara"
    C_MARCA = "marca"
    C_MODELO = "modelo"

    # --- serie: lo que se disparó y lo que se deduce al prepararla. Sin
    #     recuentos ni la rejilla (cómo la dibuja PyOECF): salen de las
    #     tomas y de las incidencias (Tony, 2026-10-21)
    S_ISO = "iso"
    S_BALANCE = "balancePersonalizado"
    S_ANALIZABLE = "esAnalizable"
    S_SALTOS = "saltos"
    # tercioEVEsperado es la clave de cada elemento de saltos ({archivo,
    # tercioEVEsperado, tercioEV}), no de serie: el prefijo S_ es por el
    # grupo donde se declara
    S_TERCIO_EV_ESPERADO = "tercioEVEsperado"

    # --- Las tomas, en orden de disparo, y lo que se guarda de cada una
    #     (lo que escribe grabar_json y lee restaurar_serie). Con fecha,
    #     tapada y oscura, la serie se restaura sin los originales (Tony,
    #     2026-10-19). La copia, relativa a la carpeta de la serie y con
    #     «/» (null si no se copió)
    S_TOMAS = "tomas"
    T_ARCHIVO = "archivo"
    T_COPIA = "copia"
    T_F = "f"
    T_TV = "tv"
    T_ISO = "iso"
    T_FECHA = "fecha"
    T_TERCIO_EV = "tercioEV"
    T_WB = "WB"
    T_NOMBRE_WB = "nombreWB"
    T_KELVIN = "kelvin"
    T_BITS = "bits"
    T_TAPADA = "tapada"
    T_OSCURA = "oscura"
    T_ZONA = "zona"
    T_PARTE = "parte"

    # --- incidencias: oecfCalc.Incidencia con los archivos en vez de
    #     índices (sus campos son las claves): códigos, sin frases; las
    #     traduce quien las lea

    # --- revelado: lo medido en cada exportación del revelador
    #     (oecfCalc.MedidaTiff), por su tercioEV, con su archivo relativo a
    #     la carpeta de la serie y con «/». El contraste: el de la trama del
    #     paño en L* (null sin paño o sin medir; ausente en los JSON
    #     anteriores al 2.1)
    R_EXPORTACIONES = "exportaciones"
    E_BITS = "bits"
    E_CONTRASTE = "contraste"
    E_ESPACIO = "espacio"
    E_LSTAR = "lstar"
    E_MOTIVO = "motivo"

    # --- resultados: los del análisis (Excel.resultados), tras Generar y
    #     Analizar revelado: lo que lee FotoEstación, que no lleva el
    #     código de PyOECF


#
# --- Claves de los resultados del JSON (grupo resultados): las toman de
#     aquí quien los produce (Excel.resultados) y quien los lee. Camel
#     case como las de estudio.json. Si cambias, añades o quitas una,
#     sube la versión del formato (KES.VERSION_FORMATO)
class KRES(std.EnumMutable):
    """ Constantes de los resultados del JSON del estudio. """

    # --- Los canales (rojo, verde y azul), en este orden
    CANALES_JSON = ("R", "G", "B")

    # --- Grupos de los resultados
    J_CANALES = "canales"
    J_CONSTANTES = "constantes"
    J_CURVA = "curva"
    J_DIFERENCIAS = "diferenciasMedias"
    J_LINEALIDAD = "linealidad"
    J_TEXTURAS = "latitudTexturas"
    """Clave de la latitud de texturas en los resultados del JSON."""

    # --- Por canal: lo que da el bloque 1 de Cálculo. Unidades, como en
    #     el libro: zonas (Z-V = zonaZV; una posición negativa es más
    #     oscura que la zona 0), salvo mediaZV y max (niveles del sensor).
    #     Una posición dice DÓNDE está un punto en la escala de zonas; un
    #     ancho, cuántas zonas ocupa
    R_FIN_LINEAL = "finLineal"  # posición (zonas): último punto lineal
    # ancho (zonas): finLineal − sueloSugerido + anchoZona (cuenta las dos
    # puntas)
    R_LATITUD = "latitudSugerida"
    R_MAX = "max"  # nivel del sensor: el mayor de la serie
    R_MEDIA_ZV = "mediaZV"  # nivel del sensor: media de las Z-V
    R_PRIMER_RECORTADO = "primerRecortado"  # posición (zonas)
    R_RANGO = "rango"  # ancho (zonas): techo − suelo
    # posición (zonas): donde la señal/ruido llega a RelacionSR del libro (1)
    R_SUELO = "suelo"
    R_SUELO_EXCELENTE = "sueloExcelente"  # posición (zonas): snrExcelente
    R_SUELO_SUGERIDO = "sueloSugerido"  # posición (zonas): snrMinima
    R_TECHO = "techo"  # posición (zonas): donde llega el máximo

    # --- Estado de una cifra de los canales: la cifra es un número o
    #     None, y su estado dice por qué. Códigos fijos, sin traducir (los
    #     traduce quien lee el JSON): ok (es un número), ninguno (no hay
    #     ninguna zona lineal), noAlcanzado (no se llega a ese punto) y
    #     sinDato (no se pudo medir). Se dan para ESTADOS_JSON
    J_ESTADOS = "estados"
    ESTADOS_JSON = (R_FIN_LINEAL, R_LATITUD, R_PRIMER_RECORTADO,
                    R_SUELO_EXCELENTE, R_SUELO_SUGERIDO)
    EST_NINGUNO = "ninguno"
    EST_NO_ALCANZADO = "noAlcanzado"
    EST_OK = "ok"
    EST_SIN_DATO = "sinDato"

    # --- La curva zona a zona
    J_ENTRADA = "entrada"
    J_ESPERADO = "esperado"
    J_OBJETIVO = "objetivo"
    J_PUNTO = "punto"
    J_REVELADOR = "revelador"
    J_SALIDA = "salida"
    J_SENSOR = "sensor"
    J_TERCIO = "tercioEV"  # entero: tercios de paso desde la Z-V (0 = Z-V)
    J_ZONA = "zona"

    # --- La linealidad por tercio: la desviación de cada canal respecto a
    #     la recta de pendiente 1 por la ZV (obtenido − esperado, en zonas;
    #     positiva = por encima) y si está recortado (true, false o null
    #     sin toma)
    J_DESVIACION = "desviacion"
    J_RECORTADO = "recortado"

    # --- Los tramos de la latitud de texturas: sombras, luces y zonas,
    #     en este orden. Solo del canal verde, en dos grupos (apreciable y
    #     recomendada) con los tres tramos cada uno: sombras y luces son
    #     posiciones en zonas, y zonas es el ancho (luces − sombras +
    #     anchoZona). None si no se alcanza; todo el grupo latitudTexturas
    #     es None si no hay paño
    TEXTURAS_JSON = ("sombras", "luces", "zonas")
    """Claves de cada tramo de la latitud de texturas en el JSON:
    sombras, luces y zonas."""

    # --- Las constantes que usó el análisis (en J_CONSTANTES, o sea
    #     resultados.constantes), para que quien lea el JSON no dependa de
    #     los valores actuales
    CONST_ANCHO_ZONA = "anchoZona"  # lo que ocupa una zona, en zonas
    CONST_FACTOR_ZONA = "factorZona"  # veces más luz entre zonas vecinas
    CONST_L_POR_ZONA = "lPorZona"  # L* que sube cada zona del objetivo
    CONST_LZV = "lzv"  # L* de la Z-V
    CONST_SNR_EXCELENTE = "snrExcelente"  # señal/ruido del suelo excelente
    CONST_SNR_MINIMA = "snrMinima"  # señal/ruido del suelo sugerido
    CONST_TERCIO_POR_ZONA = "tercioPorZona"  # tercios de paso en una zona
    # zonas: desviación máxima (en valor absoluto) de un punto lineal
    CONST_TOLERANCIA_LINEAL = "toleranciaLineal"
    CONST_UMBRAL_RECORTE = "umbralRecorte"  # fracción del máximo del canal
    CONST_ZONA_ZV = "zonaZV"  # número de la zona de la Z-V


#
# --- Códigos de las incidencias (los de info.incidencias en el JSON)
class KI(std.EnumMutable):
    """ Códigos de las incidencias, en el orden en que se informan. """

    # --- ISO
    ISO_DISTINTO = "ISO_DISTINTO"
    """ISO distinto del de la ZV en la serie: impide analizar."""

    # --- Balance personalizado
    MISMO_BALANCE = "MISMO_BALANCE"
    """Las dos primeras son Z-V con el mismo balance de blancos."""

    SIN_BALANCE = "SIN_BALANCE"
    """La 2.ª toma ya es de un lado: no se hizo el balance personalizado."""

    # --- Secuencia (ver OECF.secuencia)
    MEDIO_PASO = "MEDIO_PASO"
    """Serie por medios pasos: impide analizar."""

    PASO_ENTERO = "PASO_ENTERO"
    """Serie por pasos enteros, sin tercios: se analiza sin ellos."""

    INICIALES_SOBRAN = "INICIALES_SOBRAN"
    """Hay más Z-V iniciales de las que pide el protocolo."""

    LADOS = "LADOS"
    """No están los dos lados de la serie."""

    SIN_CAMBIO = "SIN_CAMBIO"
    """Falta la Z-V de cambio de lado."""

    CAMBIOS_SOBRAN = "CAMBIOS_SOBRAN"
    """Hay más Z-V de cambio de las que pide el protocolo."""

    SIN_FINAL = "SIN_FINAL"
    """Falta la Z-V final, tras el segundo lado."""

    SALTO = "SALTO"
    """En un lado, el tercioEV no avanza de uno en uno."""

    SOBRANTES = "SOBRANTES"
    """Tomas que no son de ninguna parte de la serie."""

    # --- Tapadas y balances de cámara
    TAPADAS_MAL = "TAPADAS_MAL"
    """No hay las tomas tapadas que pide el protocolo."""

    TAPADAS_CON_LUZ = "TAPADAS_CON_LUZ"
    """Tapadas que no salieron casi negras: se taparon mal (no sirven
    para el negro)."""

    ISO_TAPADAS = "ISO_TAPADAS"
    """Tapadas con otro ISO que la ZV (solo se avisa)."""

    SIN_BALANCES = "SIN_BALANCES"
    """No hay tomas de balance de cámara."""

    # --- Secuencia de ISO (ver OECF.secuencia)
    MARCADOR_TAPADAS = "MARCADOR_TAPADAS"
    """Marcadores de la secuencia de ISO hechos con la exposición de las
    tapadas (f/11 y 1/160) y no con la de la Z-V: se aceptan (Tony,
    2026-11-10)."""

    SIN_MARCADOR_FINAL = "SIN_MARCADOR_FINAL"
    """Falta el marcador final de la secuencia de ISO: son suyas todas las
    tomas tras el inicial."""

    ISO_ESTIMADO = "ISO_ESTIMADO"
    """ISO cuya Z2 no está justo en su sitio (por el tiempo más corto de
    la cámara): su textura es una estimación (sus Z2)."""

    ISO_SIN_MEDIR = "ISO_SIN_MEDIR"
    """ISO que no se puede medir: le falta la Z-V o la Z2, o su Z2 se
    aparta demasiado (una toma por ISO)."""

    # --- Posiciones de la rejilla y tomas que no caben o se desvían
    SIN_TOMA = "SIN_TOMA"
    """Posición sin toma: impide analizar si es de Z1 a Z9."""

    REPETIDA = "REPETIDA"
    """Posición con más de una toma."""

    FUERA = "FUERA"
    """Tomas que no caben en la rejilla."""

    DESVIADAS = "DESVIADAS"
    """Tomas que se apartan de su tercio más que KP.DEV_MAX."""

    # --- Teselas de la Z-V (tras OECF.Seleccionar)
    SIN_TARJETA = "SIN_TARJETA"
    """Sin tarjeta gris (menos de KTE.MIN_TESELAS buenas): no se
    analiza."""

    RECHAZADAS = "RECHAZADAS"
    """Teselas de tarjeta que rechazan los filtros: cuántas y qué
    porcentaje de las de tarjeta."""

    # --- Avisos de las rechazadas, uno por causa (ver KTE.AVISO_*)
    TARJETA_SUCIA = "TARJETA_SUCIA"
    """Tarjeta sucia o dañada: rechazadas por dispersión o asimetría."""

    LUZ_DESIGUAL = "LUZ_DESIGUAL"
    """Luz desigual: rechazadas por nivel, con sus lados."""

    REVISAR_SERIE = "REVISAR_SERIE"
    """Por el total de rechazadas: revisar la serie."""

    REPETIR_SERIE = "REPETIR_SERIE"
    """Por el total de rechazadas: repetir la serie."""

    # --- Tras medir (OECF.Medir)
    LUZ_CAMBIO = "LUZ_CAMBIO"
    """Z-V de control que se apartan de la ZV más que
    COM.TOLERANCIA_LINEAL: la luz cambió; no entran en la media de las
    Z-V."""

    SOMBRAS_ALZADAS = "SOMBRAS_ALZADAS"
    """Con tapadas, las sombras salen más claras de lo que dice su tiempo
    de exposición, más que COM.TOLERANCIA_LINEAL (antiparpadeo, obturador
    o luz que parpadea): en cuánto, como porcentaje."""


#
# --- Marcadores que lleva la frase de cada incidencia, y de dónde sale cada
#     dato (campos de ``Incidencia``, en ``oecfCalc/incidencias.py``). Quien
#     escribe la frase rellena los marcadores con ``str.format``:
#     - n: número de tomas (``len(tomas)``) si las hay; si no, ``n``. Si la
#       frase es una tupla (singular, plural), n elige la forma, aunque la
#       frase no lo escriba (LUZ_CAMBIO)
#     - esperadas, esperados: ``esperado``
#     - esperada: ``esperado``, como zona (SALTO: el tercioEV esperado)
#     - real, zona: ``tercioEV``, como zona (SALTO: el tercioEV real)
#     - zonas: ``tercioEVs``, como zonas, unidas con un separador
#     - ident: identificador de la primera toma de ``tomas``
#     - idents: identificadores de ``tomas``, unidos con un separador (en
#       DESVIADAS y LUZ_CAMBIO, cada uno con lo que se aparta: ``valores``)
#     - iso: ISO de la serie (dato de la serie, no de ``Incidencia``)
#     - umbral: ``KP.DEV_MAX``, de PyOECF, ya como texto
#     - porcentaje: ``porcentaje``, ya como texto con el decimal del idioma
#     - lados: texto compuesto desde ``lados`` (LUZ_DESIGUAL), con
#       el inicio «, sobre todo» y la unión «y»
#     Los textos de formato (ident, zonas, porcentaje, lados…) los pone cada
#     proyecto: aquí solo se dice qué marcadores lleva cada frase
class KMA(std.EnumMutable):
    """ Nombres de los marcadores de las frases de las incidencias. """

    ESPERADA = "esperada"
    ESPERADAS = "esperadas"
    ESPERADOS = "esperados"
    IDENT = "ident"
    IDENTS = "idents"
    ISO = "iso"
    LADOS = "lados"
    N = "n"
    PORCENTAJE = "porcentaje"
    REAL = "real"
    UMBRAL = "umbral"
    ZONA = "zona"
    ZONAS = "zonas"


MARCADORES_INCIDENCIA: dict[str, tuple[str, ...]] = {
    KI.ISO_DISTINTO: (KMA.N, KMA.IDENTS, KMA.ISO),
    KI.MISMO_BALANCE: (),
    KI.SIN_BALANCE: (),
    KI.MEDIO_PASO: (),
    KI.PASO_ENTERO: (),
    KI.INICIALES_SOBRAN: (KMA.N,),
    KI.LADOS: (KMA.N, KMA.ESPERADOS),
    KI.SIN_CAMBIO: (),
    KI.CAMBIOS_SOBRAN: (KMA.N,),
    KI.SIN_FINAL: (),
    KI.SALTO: (KMA.IDENT, KMA.ESPERADA, KMA.REAL),
    KI.SOBRANTES: (KMA.N, KMA.IDENTS),
    KI.TAPADAS_MAL: (KMA.N, KMA.ESPERADAS),
    KI.TAPADAS_CON_LUZ: (KMA.N, KMA.IDENTS),
    KI.ISO_TAPADAS: (KMA.N, KMA.IDENTS, KMA.ISO),
    KI.SIN_BALANCES: (),
    KI.MARCADOR_TAPADAS: (KMA.N, KMA.IDENTS),
    KI.SIN_MARCADOR_FINAL: (),
    KI.ISO_ESTIMADO: (KMA.N, KMA.IDENTS),
    KI.ISO_SIN_MEDIR: (KMA.N, KMA.IDENTS),
    KI.SIN_TOMA: (KMA.ZONA,),
    KI.REPETIDA: (KMA.N, KMA.ZONA),
    KI.FUERA: (KMA.N, KMA.IDENTS),
    KI.DESVIADAS: (KMA.N, KMA.IDENTS, KMA.UMBRAL),
    KI.SIN_TARJETA: (),
    KI.RECHAZADAS: (KMA.N, KMA.PORCENTAJE, KMA.ESPERADAS),
    KI.TARJETA_SUCIA: (KMA.PORCENTAJE,),
    KI.LUZ_DESIGUAL: (KMA.PORCENTAJE, KMA.LADOS),
    KI.REVISAR_SERIE: (KMA.PORCENTAJE,),
    KI.REPETIR_SERIE: (KMA.PORCENTAJE,),
    KI.LUZ_CAMBIO: (KMA.N, KMA.IDENTS),
    KI.SOMBRAS_ALZADAS: (KMA.PORCENTAJE,)}


#
# --- Español de la frase de cada incidencia: fuente única. El valor es el
#     texto, o la tupla (singular, plural) si la frase lleva «n»
#     (singular solo con n == 1). Los marcadores, en MARCADORES_INCIDENCIA
TEXTOS_INCIDENCIA_ES: dict[str, str | tuple[str, str]] = {
    KI.ISO_DISTINTO: (
        _("El ISO cambia en {n} toma de la serie: {idents} (se esperaba "
          "ISO {iso})."),
        _("El ISO cambia en {n} tomas de la serie: {idents} (se esperaba "
          "ISO {iso}).")),
    KI.MISMO_BALANCE: _(
        "Las dos primeras Z-V tienen el mismo balance de blancos: no se "
        "hizo el personalizado."),
    KI.SIN_BALANCE: _(
        "No se hizo el balance de blancos personalizado inicial."),
    KI.MEDIO_PASO: _(
        "Serie por medios pasos: no se puede analizar. Repítela por "
        "tercios o por pasos enteros."),
    KI.PASO_ENTERO: _(
        "Serie por pasos enteros: se analiza sin tercios."),
    KI.INICIALES_SOBRAN: (
        _("Sobra {n} Z-V al principio."),
        _("Sobran {n} Z-V al principio.")),
    KI.LADOS: (
        _("Solo hay {n} lado; se esperaban {esperados}."),
        _("Solo hay {n} lados; se esperaban {esperados}.")),
    KI.SIN_CAMBIO: _("Falta la Z-V de cambio de lado."),
    KI.CAMBIOS_SOBRAN: (
        _("Sobra {n} Z-V en el cambio de lado."),
        _("Sobran {n} Z-V en el cambio de lado.")),
    KI.SIN_FINAL: _("Falta la Z-V final."),
    KI.SALTO: _(
        "Secuencia rota en {ident}: se esperaba {esperada} y es {real}."),
    KI.SOBRANTES: (
        _("Hay {n} toma fuera del orden esperado: {idents}."),
        _("Hay {n} tomas fuera del orden esperado: {idents}.")),
    KI.TAPADAS_MAL: (
        _("Hay {n} toma tapada; se esperaban {esperadas}."),
        _("Hay {n} tomas tapadas; se esperaban {esperadas}.")),
    KI.TAPADAS_CON_LUZ: (
        _("Hay {n} toma tapada que no salió negra: {idents}. Se tapó mal "
          "y no sirve para el negro."),
        _("Hay {n} tomas tapadas que no salieron negras: {idents}. Se "
          "taparon mal y no sirven para el negro.")),
    KI.ISO_TAPADAS: (
        _("Hay {n} toma tapada con otro ISO: {idents} (se esperaba ISO "
          "{iso})."),
        _("Hay {n} tomas tapadas con otro ISO: {idents} (se esperaba ISO "
          "{iso}).")),
    KI.SIN_BALANCES: _("No hay balances de cámara."),
    KI.MARCADOR_TAPADAS: (
        _("El marcador de la secuencia de ISO se hizo con los valores de "
          "las tapadas (f/11 y 1/160): {idents}. Se acepta, pero debe "
          "hacerse con los valores de la ZV."),
        _("Los marcadores de la secuencia de ISO se hicieron con los "
          "valores de las tapadas (f/11 y 1/160): {idents}. Se aceptan, "
          "pero deben hacerse con los valores de la ZV.")),
    KI.SIN_MARCADOR_FINAL: _(
        "Falta el marcador final de la secuencia de ISO: se toman como "
        "suyas todas las tomas que siguen al marcador inicial."),
    KI.ISO_ESTIMADO: (
        _("En {n} ISO, la toma de sombras (Z2 o Z3) no llegó a su sitio por "
          "el tiempo más corto de la cámara: su textura es una estimación: "
          "{idents}."),
        _("En {n} ISO, la toma de sombras (Z2 o Z3) no llegó a su sitio por "
          "el tiempo más corto de la cámara: su textura es una estimación: "
          "{idents}.")),
    KI.ISO_SIN_MEDIR: (
        _("No se puede medir {n} ISO de la secuencia: le falta la ZV o la "
          "toma de sombras (Z2 o Z3), o esta se aparta demasiado: "
          "{idents}."),
        _("No se pueden medir {n} ISO de la secuencia: les falta la ZV o "
          "la toma de sombras (Z2 o Z3), o esta se aparta demasiado: "
          "{idents}.")),
    KI.SIN_TOMA: _("No hay toma en {zona}."),
    KI.REPETIDA: _("Hay {n} tomas en {zona}."),
    KI.FUERA: (
        _("Hay {n} toma más allá de las zonas teóricas: {idents}."),
        _("Hay {n} tomas más allá de las zonas teóricas: {idents}.")),
    KI.DESVIADAS: (
        _("Hay {n} toma que se aparta de su tercio más de {umbral} "
          "tercios: {idents}."),
        _("Hay {n} tomas que se apartan de su tercio más de {umbral} "
          "tercios: {idents}.")),
    KI.SIN_TARJETA: _(
        "No se encontró la tarjeta gris: no se puede analizar."),
    # --- «%\u00a0de»: espacio duro tras el %, para que Babel no lea «% d»
    #     como un marcador antiguo (python-format) y falle al compilar
    KI.RECHAZADAS: (
        _("Hay {n} tesela de tarjeta fuera por los filtros: el "
          "{porcentaje} %\u00a0de las {esperadas}."),
        _("Hay {n} teselas de tarjeta fuera por los filtros: el "
          "{porcentaje} %\u00a0de las {esperadas}.")),
    KI.TARJETA_SUCIA: _(
        "El {porcentaje} %\u00a0de las teselas de tarjeta tiene un ruido o "
        "unos valores raros, quizá por polvo, marcas o algún defecto de la "
        "tarjeta. El análisis sigue adelante; para la próxima serie "
        "conviene limpiar la tarjeta o usar otra."),
    KI.LUZ_DESIGUAL: _(
        "El {porcentaje} %\u00a0de las teselas de tarjeta recibe una luz "
        "distinta de la del resto: la luz no es uniforme{lados}. El "
        "análisis sigue adelante; en la próxima serie conviene colocar la "
        "luz de otra forma o centrar mejor la tarjeta."),
    KI.REVISAR_SERIE: _(
        "En total queda fuera el {porcentaje} %\u00a0de las teselas de "
        "tarjeta. El análisis sigue adelante; en la próxima serie conviene "
        "comprobar la luz y la tarjeta."),
    KI.REPETIR_SERIE: _(
        "En total queda fuera el {porcentaje} %\u00a0de las teselas de "
        "tarjeta: conviene repetir la serie."),
    KI.LUZ_CAMBIO: (
        _("La luz cambió durante la serie: esta Z-V se aparta de la ZV y "
          "no entra en la media: {idents}."),
        _("La luz cambió durante la serie: estas Z-V se apartan de la ZV "
          "y no entran en la media: {idents}.")),
    KI.SOMBRAS_ALZADAS: _(
        "Las tomas de sombra salen hasta un {porcentaje} % más claras "
        "de lo que dice su tiempo de exposición. Puede deberse al "
        "antiparpadeo de la cámara, al obturador o a una luz que "
        "parpadea: desactive el antiparpadeo y repita la serie.")}


#
# --- Estados de un mediador: códigos fijos, sin traducir (los traduce
#     quien los use). ILEGIBLE: JSON mal formado, que no se puede abrir o
#     sin una versión numérica; NO_EXISTE: no hay archivo; VERSION_ANTIGUA:
#     su MAYOR es menor que el de quien lo lee; VERSION_NUEVA: su MAYOR es
#     mayor
class KMED(std.EnumMutable):
    """ Constantes de los estados de un mediador. """

    ILEGIBLE = "ilegible"
    NO_EXISTE = "noExiste"
    OK = "ok"
    VERSION_ANTIGUA = "versionAntigua"
    VERSION_NUEVA = "versionNueva"


#
# --- Constantes de la posición (de zonas.py: las necesitan las frases de
#     las incidencias, en PyOECF y en FE)
class KP(std.EnumMutable):
    """ Constantes de la posición de cada toma. """

    TERCIOS = 3
    """Tercios por zona."""

    ZONA_REF = 5
    """Zona de la referencia (Z-V)."""

    DEV_MAX = 0.33
    """Desvío máximo, en tercios, entre la posición exacta de una toma y su
    tercio entero. Lo normal es el redondeo de los tiempos que rotula la
    cámara (0,20 en la R7); más, se avisa."""

    PREFIJO = "Z"
    """Nombres de las zonas como en el fotómetro: Z0, Z0.3, Z0.7, Z1…
    Las zonas 5 y 10 van en romanos (ZV, ZV.3, ZX)."""

    ROMANOS = {ZONA_REF: "V", 10: "X"}
    """Diccionario para representar las zonas 5 (V) y 10 (X) en números
    romanos."""

    TERCIOS_TEXTO = ("", ".3", ".7")
    """Sufijos de texto para los tercios de zona."""


#
# --- Constantes de las frases de las incidencias: datos de PyOECF que
#     usan sus marcadores (KRV.BITS_DEFINITIVOS y KTE.LADO_* leen de aquí)
class KFR(std.EnumMutable):
    """ Constantes de las frases de las incidencias. """

    # --- Bits mínimos de las exportaciones del revelador: con menos (las de
    #     8 bits de XnView, p. ej.) no se miden (Tony, 2026-11-13)
    BITS_DEFINITIVOS = 16

    LADO_IZQUIERDA = "IZQUIERDA"
    """Mitad de la toma donde se agrupan las rechazadas por nivel."""

    LADO_DERECHA = "DERECHA"
    """Mitad de la toma donde se agrupan las rechazadas por nivel."""

    LADO_ARRIBA = "ARRIBA"
    """Mitad de la toma donde se agrupan las rechazadas por nivel."""

    LADO_ABAJO = "ABAJO"
    """Mitad de la toma donde se agrupan las rechazadas por nivel."""

    # --- Identificador corto de una toma: número final del nombre del
    #     archivo, sin la extensión
    PATRON_IDENT = r"(\d+)$"

    # --- Formatos de los números: desvío de una toma (identificador y
    #     desvío con signo, en tercios), umbral y porcentaje. El punto
    #     decimal se cambia por el del idioma
    FORMATO_DEV = "{ident} ({dev:+.2f})"
    FORMATO_UMBRAL = "{:.2f}"
    FORMATO_PORCENTAJE = "{:.2f}"
    PUNTO = "."

    # --- Entre los identificadores o las zonas de una lista
    SEP_IDENTS = ", "

    # --- Claves de cada incidencia en el JSON (grupo incidencias): las
    #     escribe oecfCalc.incidencias.incidencia_a_dict, a partir de los
    #     campos de Incidencia; el nombre del campo y el de la clave son
    #     independientes
    J_CODIGO = "codigo"
    J_DETIENE = "detiene"
    J_ESPERADO = "esperado"
    J_LADOS = "lados"
    J_N = "n"
    J_PORCENTAJE = "porcentaje"
    J_TERCIO_EV = "tercioEV"
    J_TERCIO_EVS = "tercioEVs"
    J_TOMAS = "tomas"
    J_VALORES = "valores"


#
# --- Español de las piezas de la frase de LUZ_DESIGUAL ({lados}): la
#     entrada, la unión y cada lado. Con _(): en FE salen ya traducidos
TXT_DONDE = _(", sobre todo {donde}")
TXT_Y = _(" y ")
TEXTOS_LADO: dict[str, str] = {
    KFR.LADO_IZQUIERDA: _("a la izquierda"),
    KFR.LADO_DERECHA: _("a la derecha"),
    KFR.LADO_ARRIBA: _("arriba"),
    KFR.LADO_ABAJO: _("abajo")}


#
def partes_version(version: str) -> tuple[int, ...]:
    """
    Las partes numéricas de una versión del formato («1.0» → (1, 0)): así
    1.10 es mayor que 1.9 (ValueError si no son números)
    """
    return tuple(int(parte) for parte in version.split("."))


#
def estado_version(version_dato: str, version_propia: str,
                   acepta_menor: bool) -> str:
    """
    Estado (un KMED.*) de la versión de un JSON frente a la que sabe leer
    quien llama: VERSION_NUEVA si es mayor, VERSION_ANTIGUA si su MAYOR es
    menor y OK en los demás casos. Con acepta_menor, solo cuenta el MAYOR
    (un MENOR distinto se acepta, ignorando las claves nuevas); sin él,
    cualquier parte mayor es VERSION_NUEVA (ValueError si alguna versión no
    son números)
    """
    dato, propia = partes_version(version_dato), partes_version(version_propia)
    es_nueva = (dato[0] > propia[0]) if acepta_menor else (dato > propia)
    if es_nueva:
        return KMED.VERSION_NUEVA
    if dato[0] < propia[0]:
        return KMED.VERSION_ANTIGUA
    return KMED.OK


#
def version_formato(datos: Mapping) -> str:
    """
    Versión del formato de un JSON del estudio ya leído: la de
    oecf.versionFormato o, en los JSON 1.x, la de oecf.version (KeyError
    o TypeError si no trae ninguna)
    """
    oecf = datos[KES.OECF]
    if KES.O_VERSION_FORMATO in oecf:
        return oecf[KES.O_VERSION_FORMATO]
    return oecf[KES.O_VERSION_ANTIGUA]


#
def zona_tercio(tercioEV: int) -> tuple[int, int]:
    """Zona entera (0 a 10) y tercio (0, 1 o 2) de un tercioEV: (5, 1) es
    ZV.3. De aquí salen los nombres de pantalla y los de las copias."""
    return divmod((KP.ZONA_REF * KP.TERCIOS) + tercioEV, KP.TERCIOS)


#
def texto_zona(tercioEV: int) -> str:
    """Nombre de la zona de un tercioEV: ZV, ZV.3, Z9.7, ZX…"""
    entera, tercio = zona_tercio(tercioEV)
    return (f"{KP.PREFIJO}{KP.ROMANOS.get(entera, entera)}"
            f"{KP.TERCIOS_TEXTO[tercio]}")


#
def texto_iso(iso: float) -> str:
    """ ISO como texto, en número entero: 100. """
    return str(round(iso))


#
def ident_toma(archivo: str, archivos: Sequence[str]) -> str:
    """
    Identificador corto de una toma: número final de su nombre sin la
    extensión o, si no tiene, su orden en la serie (contando desde 1).
    archivo: nombre del archivo; archivos: los de la serie, en su orden
    (ValueError si archivo no está en archivos y no acaba en número)
    """
    numero = re.search(KFR.PATRON_IDENT, PurePath(archivo).stem)
    return numero.group(1) if numero else str(archivos.index(archivo) + 1)


#
def marcadores_incidencia(incidencia: Mapping, archivos: Sequence[str],
                          iso: float | None, *, sep_decimal: str = ",",
                          textos_lado: Mapping[str, str] = TEXTOS_LADO,
                          txt_donde: str = TXT_DONDE,
                          txt_y: str = TXT_Y) -> dict[str, str | int]:
    """
    Marcadores de la frase de una incidencia, listos para
    ``TEXTOS_INCIDENCIA_ES[codigo].format(**marcadores)``: siempre «n»
    (int: elige singular, si es 1, o plural en las tuplas) y los de
    ``MARCADORES_INCIDENCIA[codigo]``, ya como texto.

    De dónde sale cada argumento en el JSON del estudio:

    - incidencia: un elemento de ``incidencias`` (claves ``KFR.J_*``;
      ``tomas`` son nombres de archivo). Sin ``valores`` (DESVIADAS de un
      JSON anterior), los identificadores salen sin desvío
    - archivos: ``[t["archivo"] for t in serie["tomas"]]``, en su orden
    - iso: ``serie["iso"]`` (None si no se leyó)

    Lo que depende del idioma llega por parámetro, ya traducido: el
    separador decimal y las piezas de {lados}. Por defecto, los de este
    módulo (en FE, ya traducidos por gettext al importarlo)
    """
    codigo = incidencia[KFR.J_CODIGO]
    marcadores = MARCADORES_INCIDENCIA[codigo]
    tomas = incidencia.get(KFR.J_TOMAS) or ()
    valores = incidencia.get(KFR.J_VALORES) or ()
    tercio_ev = incidencia.get(KFR.J_TERCIO_EV)

    # --- Tomas: su identificador y, si lo hay, cuánto se apartan
    if valores:
        idents = [KFR.FORMATO_DEV.format(
            ident=ident_toma(archivo, archivos), dev=valor).replace(
                KFR.PUNTO, sep_decimal)
                  for archivo, valor in zip(tomas, valores)]
    else:
        idents = [ident_toma(archivo, archivos) for archivo in tomas]

    # --- Cada marcador, solo si la frase lo lleva
    datos: dict[str, str | int] = {
        KMA.N: len(tomas) if tomas else incidencia.get(KFR.J_N, 0)}
    if KMA.IDENTS in marcadores:
        datos[KMA.IDENTS] = KFR.SEP_IDENTS.join(idents)
    if KMA.IDENT in marcadores:
        datos[KMA.IDENT] = idents[0] if idents else ""
    if (KMA.ESPERADAS in marcadores) or (KMA.ESPERADOS in marcadores):
        datos[KMA.ESPERADAS] = datos[KMA.ESPERADOS] = str(
            incidencia.get(KFR.J_ESPERADO, 0))
    if KMA.ESPERADA in marcadores:
        datos[KMA.ESPERADA] = texto_zona(incidencia[KFR.J_ESPERADO])
    if (KMA.ZONA in marcadores) or (KMA.REAL in marcadores):
        datos[KMA.ZONA] = datos[KMA.REAL] = (
            texto_zona(tercio_ev) if (tercio_ev is not None) else "")
    if KMA.ZONAS in marcadores:
        datos[KMA.ZONAS] = KFR.SEP_IDENTS.join(
            texto_zona(t) for t in (incidencia.get(KFR.J_TERCIO_EVS) or ()))
    if KMA.ISO in marcadores:
        datos[KMA.ISO] = texto_iso(iso) if (iso is not None) else ""
    if KMA.UMBRAL in marcadores:
        datos[KMA.UMBRAL] = KFR.FORMATO_UMBRAL.format(KP.DEV_MAX).replace(
            KFR.PUNTO, sep_decimal)
    if KMA.PORCENTAJE in marcadores:
        datos[KMA.PORCENTAJE] = KFR.FORMATO_PORCENTAJE.format(
            incidencia.get(KFR.J_PORCENTAJE, 0.0)).replace(KFR.PUNTO,
                                                           sep_decimal)
    if KMA.LADOS in marcadores:
        lados = incidencia.get(KFR.J_LADOS) or ()
        datos[KMA.LADOS] = (txt_donde.format(donde=txt_y.join(
            textos_lado[lado] for lado in lados)) if lados else "")
    return datos
