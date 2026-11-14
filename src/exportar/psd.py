# -*- coding: utf-8 *-*
"""
    :Propósito: Láminas PSD de una serie (pieza E): la plantilla con sus
                31 cuadros rellenos con el recorte del paño de cada zona,
                a 16 bits, y su cajetín de datos (texto editable).
                Con las exportaciones TIFF del revelador
    :Autor:     Tony Diana
    :Versión:   26.10.18
"""

# cSpell:ignore findfont, getbbox, getlength, getmetrics, iinfo, imread, kcom
# cSpell:ignore kpsd, oecf, recoloca, recolocada, Rght, tobytes

__all__ = ["KPSD", "Psd"]

# --- Bibliotecas estándar Python
from collections.abc import Iterator
from pathlib import Path
import re

# --- Bibliotecas externas
import numpy as np
import tifffile
from psd_tools import PSDImage
from psd_tools.api.layers import AdjustmentLayer, Group, Layer, TypeLayer
from psd_tools.composite import composite
from psd_tools.constants import ChannelID, Tag
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont

# --- Bibliotecas internas
from bib import std
from bib.oecfMediadores import KP
from kernel import COM as KCOM
from oecfCalc import Ventana, porcentaje, recorte


#
class KPSD(std.EnumMutable):
    """ Constantes de las láminas. """

    BITS = 16
    """Bits por canal de las capas del PSD."""

    # --- Cartela de datos (Tony, 2026-10-16): sus capas de texto, de
    #     arriba abajo, se rellenan con las líneas que da la aplicación (ya
    #     traducidas), repartidas a la misma distancia dentro del marco y
    #     alineadas a la izquierda, con la letra y el tamaño de la
    #     plantilla. Se cambia el texto editable (el motor de texto y su
    #     copia) y la imagen de la capa (la que enseñan los visores)
    GRUPO_CARTELA = "Cajetín de datos"
    """Nombre del grupo de la cartela en la plantilla."""

    MARCO_CARTELA = "Cajetín"
    """Nombre de la capa del marco de la cartela."""

    BORDE_CARTELA = 10
    """Grosor del borde del marco, en píxeles."""

    # --- Capas de los cuadros de la plantilla: prefijo de zona y su
    #     número (Z03, Z03_3…). De cada zona, el sufijo no se lee: solo
    #     su orden por nombre (la entera, el primer y el segundo tercio),
    #     así el sufijo está únicamente en OECF.KT.TERCIOS_ZONA
    PATRON_CAPA_ZONA = re.compile(rf"{re.escape(KP.PREFIJO)}(\d+)(?:\D.*)?")
    """Patrón del nombre de una capa de cuadro; su grupo 1 es la zona."""

    # --- Del formato PSD (no son decisiones nuestras): canales de color de
    #     una capa y su transparencia, orden de bytes de los 16 bits,
    #     posición de la x y de la y (línea base) en la transformación de
    #     una capa de texto, final de la copia del texto y del párrafo,
    #     alineación a la izquierda, claves de la copia del texto y de sus
    #     límites, y copia de los textos del documento (Txt2)
    CANALES = (ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2)
    CANAL_ALFA = ChannelID.TRANSPARENCY_MASK
    TIPO_PSD = ">u2"
    TRANSFORM_X = 4
    TRANSFORM_Y = 5
    FIN_TEXTO = "\x00"
    FIN_LINEA = "\r"
    IZQUIERDA = 0
    TEXTO_COPIA = b"Txt "
    LIMITES = (b"bounds", b"boundingBox")
    LIMITE_IZQUIERDA = b"Left"
    LIMITE_DERECHA = b"Rght"
    TEXTOS_DOCUMENTO = Tag.TEXT_ENGINE_DATA


#
class Psd(object):
    """
    Láminas de una serie: se crea con la plantilla, la toma de cada zona
    ({tercioEV: archivo}), la ventana del paño, los divisores
    del recorte (KTE.FACTORES: 1 → 100 %) y el tamaño del sensor (alto,
    ancho). La toma puede ser el RAW (revelado propio y neutro) o la
    exportación del revelador en TIFF (en el espacio de la plantilla; su
    recorte se supone centrado y la ventana se recoloca). Con cartela,
    sus líneas ya traducidas (cámara, latitud, fecha, soporte: de arriba
    abajo), que rellenan sus capas de texto. Revelar() revela o lee y
    recorta (una zona cada vez); Escribir() graba la lámina de un
    divisor.
    """

    __slots__ = ["__cartela", "__cuadros", "__factores", "__plantilla",
                 "__sensor", "__ventana", "__zonas"]

    #
    def __init__(self, plantilla: Path, zonas: dict[int, Path],
                 ventana: Ventana, factores: tuple[int, ...],
                 sensor: tuple[int, int],
                 cartela: tuple[str, ...] = ()) -> None:

        # --- Variables de instancia. cuadros: {divisor: {tercioEV:
        #     píxeles}}
        self.__plantilla: Path = plantilla
        self.__zonas: dict[int, Path] = zonas
        self.__ventana: Ventana = ventana
        self.__factores: tuple[int, ...] = factores
        self.__sensor: tuple[int, int] = sensor
        self.__cartela: tuple[str, ...] = cartela
        self.__cuadros: dict[int, dict[int, np.ndarray]] = {
            f: {} for f in factores}

    #
    @property
    def factores(self) -> tuple[int, ...]:
        """ Saber los divisores de la lámina (1 → 100 %, 2 → 50 %…). """
        return self.__factores

    #
    def Revelar(self) -> Iterator[tuple[int, int]]:
        """
        Revela cada zona una sola vez y saca su cuadro en cada divisor
        (el recorte del centro de la ventana, reducido por área). Tras
        cada una dice cuántas lleva y cuántas son.
        """
        total = len(self.__zonas)
        for hechas, (tercioEV, archivo) in enumerate(self.__zonas.items(), 1):
            imagen, ventana = self.imagen(archivo)
            for factor in self.__factores:
                self.__cuadros[factor][tercioEV] = recorte(imagen, ventana,
                                                           factor)
            yield hechas, total

    #
    def imagen(self, archivo: Path) -> tuple[np.ndarray, Ventana]:
        """
        Imagen de una zona (RGB de 16 bits) y la ventana del paño en ella:
        la TIFF del revelador, leída, con la ventana recolocada por su
        recorte.
        """
        imagen = tifffile.imread(archivo)
        alto, ancho = self.__sensor
        dy, dx = (alto - imagen.shape[0]) // 2, (ancho - imagen.shape[1]) // 2
        v = self.__ventana
        return imagen, Ventana(
            x=v.x - dx,
            y=v.y - dy,
            ancho=v.ancho,
            alto=v.alto)

    #
    @staticmethod
    def __capas_zona(psd: PSDImage) -> list[tuple[Layer, int]]:
        """
        Capas de los cuadros de la plantilla con su tercioEV. De cada zona
        (las cifras tras la Z) se ordenan sus capas por nombre: la más
        corta es la entera y siguen el primer y el segundo tercio. El
        sufijo del nombre no se lee, así que vale cualquiera.
        """
        por_zona: dict[int, list[Layer]] = {}
        for capa in psd.descendants():
            coincide = KPSD.PATRON_CAPA_ZONA.fullmatch(capa.name)
            if (coincide is None) or isinstance(capa, (Group, TypeLayer)):
                continue
            por_zona.setdefault(int(coincide.group(1)), []).append(capa)
        capas: list[tuple[Layer, int]] = []
        for entera, grupo in por_zona.items():
            grupo.sort(key=lambda c: (len(c.name), c.name))
            for tercio, capa in enumerate(grupo):
                capas.append((capa, ((entera - KP.ZONA_REF) * KP.TERCIOS)
                              + tercio))
        return capas

    #
    def Escribir(self, factor: int, destino: Path) -> None:
        """
        Graba la lámina de un divisor: la plantilla con cada cuadro en su
        capa y, con cartela, sus líneas (las demás capas y las marcas, sin
        tocar). Si no se puede escribir, OSError.
        """
        psd = PSDImage.open(self.__plantilla)
        cuadros = self.__cuadros[factor]
        for capa, tercioEV in self.__capas_zona(psd):
            px = cuadros.get(tercioEV)
            if (px is None) or (not capa.has_pixels()):
                continue
            alto, ancho = capa.height, capa.width
            for info, datos in zip(capa._record.channel_info,   # type: ignore
                                   capa._channels):              # type: ignore
                if info.id in KPSD.CANALES:
                    canal = px[:alto, :ancho, KPSD.CANALES.index(info.id)]
                    datos.set_data(canal.astype(KPSD.TIPO_PSD).tobytes(),
                                   ancho, alto, KPSD.BITS)
        self.rellenar_cartela(psd)
        self.componer(psd)
        psd.save(destino)

    #
    def rellenar_cartela(self, psd: PSDImage) -> None:
        """
        Escribe las líneas de la cartela en sus capas de texto (de arriba
        abajo), repartidas a la misma distancia dentro de su marco y
        alineadas a la izquierda de la primera. Sin cartela (o si la
        plantilla no la tiene), nada. Quita la copia de los textos del
        documento (Txt2), que tendría los de la plantilla.
        """
        grupo = next((c for c in psd if isinstance(c, Group)
                      and (c.name == KPSD.GRUPO_CARTELA)), None)
        if (not self.__cartela) or (grupo is None):
            return
        marco = next((c for c in grupo if c.name == KPSD.MARCO_CARTELA),
                     None)
        lineas = sorted((c for c in grupo if isinstance(c, TypeLayer)),
                        key=Psd.base)
        if (marco is None) or (not lineas):
            return
        fuente = self.fuente(lineas[0])
        ascenso, descenso = fuente.getmetrics()
        alto = ascenso + descenso
        arriba = marco.top + KPSD.BORDE_CARTELA
        libre = marco.bottom - KPSD.BORDE_CARTELA - arriba
        hueco = (libre - (len(lineas) * alto)) / (len(lineas) + 1)
        x = lineas[0].transform[KPSD.TRANSFORM_X]

        # --- Si la plantilla tiene menos capas que líneas, sobran las de
        #     arriba: así las demás siguen en su capa (Tony, 2026-11-13)
        textos = self.__cartela[-len(lineas):]
        for i, (capa, texto) in enumerate(zip(lineas, textos)):
            base = arriba + (hueco * (i + 1)) + (alto * i) + ascenso
            self.escribir_texto(capa, texto, x, base, fuente)

        # --- El PSD guarda además, para todo el documento, otra copia de
        #     los textos (Txt2), que Photoshop usa al editarlos: seguiría
        #     el texto de la plantilla. Sin ella, Photoshop los rehace
        #     desde cada capa (las demás, sin cambios: igual que estaban)
        bloques = psd._record.layer_and_mask_information.tagged_blocks
        if (bloques is not None) and (KPSD.TEXTOS_DOCUMENTO in bloques):
            del bloques[KPSD.TEXTOS_DOCUMENTO]

    #
    @staticmethod
    def base(capa: TypeLayer) -> float:
        """ Altura de la línea base de una capa de texto. """
        return capa.transform[KPSD.TRANSFORM_Y]

    #
    @staticmethod
    def fuente(capa: TypeLayer) -> ImageFont.FreeTypeFont:
        """
        Letra de una capa de texto, en su tamaño (la de su primer estilo;
        si no está en el sistema, la de reserva de matplotlib).
        """
        estilo = capa.engine_dict["StyleRun"]["RunArray"][0]
        datos = estilo["StyleSheet"]["StyleSheetData"]
        nombre = capa.resource_dict["FontSet"][int(datos["Font"])][
            "Name"].value
        return ImageFont.truetype(font_manager.findfont(nombre),
                                  round(float(datos["FontSize"])))

    #
    @staticmethod
    def escribir_texto(capa: TypeLayer, texto: str, x: float, base: float,
                       fuente: ImageFont.FreeTypeFont) -> None:
        """
        Cambia una capa de texto: el texto editable (motor de texto, su
        copia, el ancho de sus límites, alineado a la izquierda), su
        posición (línea base en x, base), su nombre y su imagen (el texto
        dibujado, negro, con su transparencia).
        """
        ajustes = capa.tagged_blocks.get_data(Tag.TYPE_TOOL_OBJECT_SETTING)
        motor = capa.engine_dict
        largo = len(texto) + len(KPSD.FIN_LINEA)
        motor["Editor"]["Text"] = type(motor["Editor"]["Text"])(
            texto + KPSD.FIN_LINEA)
        for tiradas in (motor["StyleRun"]["RunLengthArray"],
                        motor["ParagraphRun"]["RunLengthArray"]):
            antes = sum(int(n) for n in tiradas[:-1])
            tiradas[-1] = type(tiradas[-1])(largo - antes)
        for bloque in motor["ParagraphRun"]["RunArray"]:
            propiedades = bloque["ParagraphSheet"]["Properties"]
            if "Justification" in propiedades:
                propiedades["Justification"] = type(
                    propiedades["Justification"])(KPSD.IZQUIERDA)
        datos = ajustes.text_data
        datos[KPSD.TEXTO_COPIA] = type(datos[KPSD.TEXTO_COPIA])(
            texto + KPSD.FIN_TEXTO)
        ancho_texto = fuente.getlength(texto)
        for clave in KPSD.LIMITES:
            if clave in datos:
                limites = datos[clave]
                limites[KPSD.LIMITE_IZQUIERDA] = type(
                    limites[KPSD.LIMITE_IZQUIERDA])(0.0)
                limites[KPSD.LIMITE_DERECHA] = type(
                    limites[KPSD.LIMITE_DERECHA])(ancho_texto)
        ajustes.transform = (ajustes.transform[:KPSD.TRANSFORM_X]
                             + (x, base))
        capa.name = texto

        # --- La imagen: el texto dibujado en su sitio (la caja de la capa,
        #     la de la tinta), negro y con su transparencia a 16 bits
        ascenso, descenso = fuente.getmetrics()
        margen = ascenso + descenso
        lienzo = Image.new("L", (round(ancho_texto) + (2 * margen),
                                 3 * margen), 0)
        ImageDraw.Draw(lienzo).text((margen, 2 * margen), texto,
                                    font=fuente, fill=255, anchor="ls")
        caja = lienzo.getbbox()
        if caja is None:
            return
        alfa = np.asarray(lienzo.crop(caja), dtype=np.float64)
        alto, ancho = alfa.shape
        izquierda = round(x + caja[0] - margen)
        arriba = round(base + caja[1] - (2 * margen))
        registro = capa._record                                  # type: ignore
        registro.top, registro.left = arriba, izquierda
        registro.bottom, registro.right = arriba + alto, izquierda + ancho
        for info, canal in zip(registro.channel_info,
                               capa._channels):                 # type: ignore
            plano = (((alfa / np.iinfo(np.uint8).max) * KCOM.MAX_16)
                     if (info.id == KPSD.CANAL_ALFA)
                     else np.zeros_like(alfa))
            canal.set_data(plano.round().astype(KPSD.TIPO_PSD).tobytes(),
                           ancho, alto, KPSD.BITS)

    #
    @staticmethod
    def componer(psd: PSDImage) -> None:
        """
        Rehace la imagen compuesta que guarda el PSD (la que enseñan los
        visores y las miniaturas; Photoshop recompone desde las capas):
        si no, seguiría la de la plantilla, con los cuadros lisos. Sin las
        capas de ajuste (componerlas pediría scipy): en la vista previa no
        se aplican; en Photoshop, sí.
        """
        color, _, alfa = composite(psd, layer_filter=Psd.sin_ajustes)
        canales = [color[..., i] for i in range(KCOM.CANALES_RGB)]
        if psd._record.header.channels > KCOM.CANALES_RGB:  # type: ignore
            canales.append(alfa if (alfa.ndim == 2) else alfa[..., 0])
        psd._record.image_data.set_data(                         # type: ignore
            [(np.clip(c, 0, 1) * KCOM.MAX_16).round()
             .astype(KPSD.TIPO_PSD).tobytes() for c in canales],
            psd._record.header)                                  # type: ignore

    #
    @staticmethod
    def sin_ajustes(capa: Layer) -> bool:
        """ Saber si una capa entra en la imagen compuesta: visible y no
            de ajuste. """
        return capa.is_visible() and (not isinstance(capa, AdjustmentLayer))

    #
    def nombre(self, factor: int) -> str:
        """
        Nombre de la lámina de un divisor: el de la plantilla con su
        porcentaje (Soportes100.psd, Soportes50.psd…).
        """
        return (f"{self.__plantilla.stem}{porcentaje(factor)}"
                f"{self.__plantilla.suffix}")
