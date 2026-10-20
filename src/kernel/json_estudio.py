# -*- coding: utf-8 *-*
"""
    :Propósito: Graba en la carpeta OECF de la serie un JSON con los
                datos de la preparación, y de él restaura la serie
                preparada. Solo datos, sin textos traducidos. JSON y no
                YAML: viene con Python, sin dependencias
    :Autor:     Tony Diana
    :Versión:   26.10.19
"""

# cSpell:ignore analisis, biboecf, camara, idxs, ocupadas, pyoecf, timespec

__all__ = ["es_preparada", "grabar_json", "hay_review", "leer_review",
           "grabar_review", "restaurar_serie"]

# --- Bibliotecas estándar Python
import json
from datetime import datetime
from pathlib import Path

# --- Bibliotecas internas
import biboecf
from bib import std
from .constantes import K


#
# --- Constantes de los datos
class KD(std.EnumMutable):
    """ Constantes del JSON de la serie. """

    # --- Nombre del archivo, en la carpeta OECF de la serie (ver _ruta)
    ARCHIVO = "estudio.json"

    # --- Sangría, para que se pueda leer a mano
    SANGRIA = 2

    # --- Fecha del análisis, sin microsegundos
    FORMATO_FECHA = "seconds"

    # --- Lo medido en los RAW (biboecf.Review), tras Generar: lo que
    #     necesita la segunda parte (las exportaciones del revelador)
    REVIEW = "analisis"

    # --- Las incidencias de la serie, como códigos (biboecf.Incidencia,
    #     con los archivos en vez de índices): sin frases, las traduce
    #     quien las lea. Y los resultados del análisis (biboecf.Excel.
    #     resultados), tras Generar y Analizar revelado: lo que lee
    #     FotoEstación, que no lleva biboecf (sin constantes)
    INCIDENCIAS = "incidencias"
    RESULTADOS = "resultados"

    # --- Las tomas, en orden de disparo, y lo que se guarda de cada una
    #     (lo que escribe grabar_json y lee restaurar_serie). Con fecha,
    #     tapada y oscura, la serie se restaura sin los originales (Tony,
    #     2026-10-19)
    TOMAS = "tomas"

    # --- La cámara: {marca, modelo} (la lee restaurar_serie si no queda
    #     ninguna copia RAW)
    CAMARA = "camara"
    C_MARCA = "marca"
    C_MODELO = "modelo"
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


#
# --- Ruta del JSON de esta carpeta OECF: en su raíz. Con ZONAS, basta
#     para rehacer el análisis: es lo que se lleva FE (Tony, 2026-10-19)
def _ruta(carpeta: Path) -> Path:
    return carpeta / KD.ARCHIVO


#
def hay_review(carpeta: Path) -> bool:
    """
    ¿El JSON de esta carpeta OECF tiene ya el análisis (tras Generar)? No, si
    no existe o no se puede leer.
    """
    try:
        datos = json.loads(_ruta(carpeta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(datos.get(KD.REVIEW))


#
def leer_review(carpeta: Path) -> biboecf.Review | None:
    """
    El análisis guardado en el JSON de esta carpeta OECF (None si no lo hay o
    no se puede leer)
    """
    try:
        datos = json.loads(_ruta(carpeta).read_text(encoding="utf-8"))
        review = datos.get(KD.REVIEW)
        return biboecf.review_de_dict(review) if review else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


#
def grabar_review(carpeta: Path, review: biboecf.Review) -> bool:
    """
    Sustituye el análisis del JSON de esta carpeta OECF (lo demás, como
    estaba). False si no se puede leer o escribir.
    """
    ruta = _ruta(carpeta)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos[KD.REVIEW] = biboecf.review_a_dict(review)
        ruta.write_text(json.dumps(datos, ensure_ascii=False,
                                   indent=KD.SANGRIA), encoding="utf-8")
    except (OSError, ValueError):
        return False
    return True


#
def leer_resultados(carpeta: Path) -> dict | None:
    """
    Los resultados del análisis guardados en el JSON de esta carpeta OECF (None
    si no los hay o no se puede leer)
    """
    try:
        datos = json.loads(_ruta(carpeta).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return datos.get(KD.RESULTADOS)


#
def grabar_resultados(carpeta: Path, resultados: dict) -> bool:
    """
    Añade (o sustituye) los resultados del análisis en el JSON de esta carpeta
    OECF (lo demás, como estaba). False si no se puede leer o escribir.
    """
    ruta = _ruta(carpeta)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos[KD.RESULTADOS] = resultados
        ruta.write_text(json.dumps(datos, ensure_ascii=False,
                                   indent=KD.SANGRIA), encoding="utf-8")
    except (OSError, ValueError):
        return False
    return True


#
def grabar_json(OECF: biboecf.OECF) -> Path | None:
    """
    Graba el JSON en la carpeta OECF de la serie, con lo que ya tiene OECF
    (leído, repartido y copiado), y devuelve su ruta, o None si no se pudo
    escribir (no impide el análisis). Las copias van
    relativas a la carpeta de la serie y con «/» en cualquier sistema
    (None si no se copió); las tomas de la rejilla, por el nombre de
    su archivo.
    """
    raws = OECF.raws
    cam = OECF.cam

    tomas = []
    for raw, toma, tercioEV, parte in zip(raws, OECF.tomas, OECF.tercioEVs,
                                          OECF.partes):
        exp = toma.exp
        copia = OECF.copias.get(raw)
        tomas.append({
            KD.T_ARCHIVO: raw.name,
            KD.T_COPIA: (copia.relative_to(OECF.path).as_posix() if copia
                         else None),
            KD.T_F: exp.f if exp else None,
            KD.T_TV: exp.tv if exp else None,
            KD.T_ISO: exp.iso if exp else None,
            KD.T_FECHA: toma.fecha.isoformat() if toma.fecha else None,
            KD.T_TERCIO_EV: tercioEV,
            KD.T_WB: list(toma.WB) if toma.WB else None,
            KD.T_NOMBRE_WB: toma.nombreWB,
            KD.T_KELVIN: toma.kelvin,
            KD.T_BITS: toma.bits,
            KD.T_TAPADA: toma.tapada,
            KD.T_OSCURA: toma.oscura,
            "zona": (OECF.KT.NOMBRE_TAPADA
                     if (parte == OECF.KT.PARTE_TAPADA)
                     else (None if (tercioEV is None)
                           else biboecf.texto_zona(tercioEV))),
            "parte": parte})

    posiciones = (biboecf.KS.LADOS * biboecf.KS.TERCIOS_LADO) + 1
    datos = {
        "pyoecf": K.version,
        "fecha": datetime.now().isoformat(timespec=KD.FORMATO_FECHA),
        "carpeta": str(OECF.path),
        KD.CAMARA: ({KD.C_MARCA: cam.marca, KD.C_MODELO: cam.modelo}
                    if cam else None),
        "balance_personalizado": OECF.balancePersonalizado,
        "tapadas": len(OECF.tapadas),
        "iso": (round(OECF.isoSerie) if (OECF.isoSerie is not None)
                else None),
        "balances_camara": len(OECF.WBs),
        "saltos": [{KD.T_ARCHIVO: raws[i].name,
                    "tercioEV_esperado": esperado,
                    KD.T_TERCIO_EV: tercioEV}
                   for i, esperado, tercioEV
                   in OECF.secuencia.saltos],                   # type: ignore
        KD.TOMAS: tomas,
        "rejilla": {
            "posiciones": posiciones,
            "ocupadas": posiciones - len(OECF.huecos),
            "huecos": [biboecf.texto_zona(t) for t in OECF.huecos],
            "repetidas": {biboecf.texto_zona(t): [raws[i].name
                                                  for i in idxs]
                          for t, idxs in OECF.repetidas.items()},
            "fuera": [raws[i].name for i in OECF.fuera]},
        "analizable": OECF.esAnalizable,
        KD.INCIDENCIAS: [
            i._replace(tomas=tuple(raws[t].name for t in i.tomas))._asdict()
            for i in biboecf.incidencias(OECF)],
        KD.REVIEW: (biboecf.review_a_dict(OECF.review)
                    if OECF.review else None)}

    # --- Se compone entero antes de escribir: si algo falla, no queda
    #     un archivo a medias
    texto = json.dumps(datos, ensure_ascii=False, indent=KD.SANGRIA)
    ruta = _ruta(OECF.carpeta)
    try:
        ruta.write_text(texto, encoding="utf-8")
    except OSError:
        return None
    return ruta


#
def es_preparada(carpeta: Path) -> bool:
    """
    ¿Esta carpeta es la OECF de una serie preparada? Sí, si tiene el
    JSON.
    """
    return _ruta(carpeta).is_file()


#
def restaurar_serie(carpeta: Path) -> biboecf.OECF | None:
    """
    La serie preparada de esta carpeta OECF (o de la que se guardó con el
    JSON, se llame como se llame), desde su JSON y sus copias, sin leer
    los originales (ver biboecf.OECF.Restaurar). None si el JSON
    no se puede leer o es de antes de poder restaurarse (le faltan datos
    de las tomas: hay que preparar la serie otra vez).
    """
    try:
        datos = json.loads(_ruta(carpeta).read_text(encoding="utf-8"))
        archivos, tomas, copias = [], [], {}
        for t in datos[KD.TOMAS]:
            exp = (biboecf.Exp(f=t[KD.T_F], tv=t[KD.T_TV], iso=t[KD.T_ISO])
                   if None not in (t[KD.T_F], t[KD.T_TV], t[KD.T_ISO])
                   else None)
            fecha = t[KD.T_FECHA]
            tomas.append(biboecf.Toma(
                exp=exp,
                fecha=datetime.fromisoformat(fecha) if fecha else None,
                WB=tuple(t[KD.T_WB]) if t[KD.T_WB] else None,
                tapada=t[KD.T_TAPADA],
                oscura=t[KD.T_OSCURA],
                nombreWB=t[KD.T_NOMBRE_WB],
                bits=t[KD.T_BITS],
                kelvin=t[KD.T_KELVIN]))
            archivos.append(t[KD.T_ARCHIVO])
            if t[KD.T_COPIA]:
                copias[t[KD.T_ARCHIVO]] = t[KD.T_COPIA]
        camara = datos.get(KD.CAMARA)
        cam = (biboecf.Cam(marca=camara[KD.C_MARCA],
                           modelo=camara[KD.C_MODELO]) if camara else None)
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return biboecf.OECF.Restaurar(carpeta, archivos, tomas, copias, cam)
