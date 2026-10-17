# -*- coding: utf-8 *-*
"""
    :Propósito: Graba en la carpeta OECF de la serie un JSON con los
                datos de la preparación. Solo datos, sin textos
                traducidos. JSON y no YAML: viene con Python, sin
                dependencias
    :Autor:     Tony Diana
    :Versión:   26.10.12
"""

# cSpell:ignore biboecf, camara, ocupadas, pyoecf, timespec, vacias

__all__ = ["grabar_json", "hay_analisis", "leer_analisis",
           "grabar_analisis"]

# --- Bibliotecas estándar Python
import json
from datetime import datetime
from pathlib import Path

# --- Bibliotecas internas
import biboecf
from bib import clases
from .constantes import K


#
# --- Constantes de los datos
class KD(clases.EnumMutable):
    """ Constantes del JSON de la serie. """

    # --- Nombre del archivo, en la carpeta OECF de la serie
    ARCHIVO = "estudio.json"

    # --- Sangría, para que se pueda leer a mano
    SANGRIA = 2

    # --- Fecha del análisis, sin microsegundos
    FORMATO_FECHA = "seconds"

    # --- Lo medido en los RAW (biboecf.Analisis), tras Generar: lo que
    #     necesita la segunda parte (las exportaciones del revelador)
    ANALISIS = "analisis"

    # --- Las incidencias de la serie, como códigos (biboecf.Incidencia,
    #     con los archivos en vez de índices): sin frases, las traduce
    #     quien las lea. Y los resultados del análisis (biboecf.Libro.
    #     resultados), tras Generar y Analizar revelado: lo que lee
    #     FotoEstación, que no lleva biboecf (sin constantes)
    INCIDENCIAS = "incidencias"
    RESULTADOS = "resultados"


# --- ¿El JSON de esta carpeta OECF tiene ya el análisis (tras Generar)?
#     No, si no existe o no se puede leer
def hay_analisis(carpeta: Path) -> bool:
    try:
        datos = json.loads((carpeta / KD.ARCHIVO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(datos.get(KD.ANALISIS))


# --- El análisis guardado en el JSON de esta carpeta OECF (None si no lo
#     hay o no se puede leer)
def leer_analisis(carpeta: Path) -> biboecf.Analisis | None:
    try:
        datos = json.loads((carpeta / KD.ARCHIVO).read_text(encoding="utf-8"))
        analisis = datos.get(KD.ANALISIS)
        return biboecf.analisis_de_dict(analisis) if analisis else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


# --- Sustituye el análisis del JSON de esta carpeta OECF (lo demás, como
#     estaba). False si no se puede leer o escribir
def grabar_analisis(carpeta: Path, analisis: biboecf.Analisis) -> bool:
    ruta = carpeta / KD.ARCHIVO
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos[KD.ANALISIS] = biboecf.analisis_a_dict(analisis)
        ruta.write_text(json.dumps(datos, ensure_ascii=False,
                                   indent=KD.SANGRIA), encoding="utf-8")
    except (OSError, ValueError):
        return False
    return True


# --- Los resultados del análisis guardados en el JSON de esta carpeta
#     OECF (None si no los hay o no se puede leer)
def leer_resultados(carpeta: Path) -> dict | None:
    try:
        datos = json.loads((carpeta / KD.ARCHIVO).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return datos.get(KD.RESULTADOS)


# --- Añade (o sustituye) los resultados del análisis en el JSON de esta
#     carpeta OECF (lo demás, como estaba). False si no se puede leer o
#     escribir
def grabar_resultados(carpeta: Path, resultados: dict) -> bool:
    ruta = carpeta / KD.ARCHIVO
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        datos[KD.RESULTADOS] = resultados
        ruta.write_text(json.dumps(datos, ensure_ascii=False,
                                   indent=KD.SANGRIA), encoding="utf-8")
    except (OSError, ValueError):
        return False
    return True


# --- Graba el JSON en la carpeta OECF de la serie, con lo que ya tiene
#     OECF (leído, repartido y copiado), y devuelve su ruta, o None si no
#     se pudo escribir (no impide el análisis). Las copias van relativas
#     a la carpeta de la serie y con «/» en cualquier sistema (None si no
#     se copió); las tomas de la rejilla, por el nombre de su archivo
def grabar_json(OECF: biboecf.OECF) -> Path | None:
    raws = OECF.raws
    cam = OECF.cam

    tomas = []
    for raw, toma, tercioEV, parte in zip(raws, OECF.tomas, OECF.tercioEVs,
                                          OECF.partes):
        exp = toma.exp
        copia = OECF.copias.get(raw)
        tomas.append({
            "archivo": raw.name,
            "copia": (copia.relative_to(OECF.path).as_posix() if copia
                      else None),
            "f": exp.f if exp else None,
            "tv": exp.tv if exp else None,
            "iso": exp.iso if exp else None,
            "tercioEV": tercioEV,
            "WB": list(toma.WB) if toma.WB else None,
            "nombreWB": toma.nombreWB,
            "kelvin": toma.kelvin,
            "bits": toma.bits,
            "zona": (OECF.KT.NOMBRE_TAPADA
                     if parte == OECF.KT.PARTE_TAPADA
                     else None if tercioEV is None
                     else biboecf.texto_zona(tercioEV)),
            "parte": parte})

    posiciones = biboecf.KS.LADOS * biboecf.KS.TERCIOS_LADO + 1
    datos = {
        "pyoecf": K.version,
        "fecha": datetime.now().isoformat(timespec=KD.FORMATO_FECHA),
        "carpeta": str(OECF.path),
        "camara": {"marca": cam.marca, "modelo": cam.modelo} if cam else None,
        "balance_personalizado": OECF.balancePersonalizado,
        "tapadas": len(OECF.tapadas),
        "iso": (round(OECF.isoSerie) if OECF.isoSerie is not None
                else None),
        "balances_camara": len(OECF.WBs),
        "saltos": [{"archivo": raws[i].name, "tercioEV_esperado": esperado,
                    "tercioEV": tercioEV}
                   for i, esperado, tercioEV
                   in OECF.secuencia.saltos],                   # type: ignore
        "tomas": tomas,
        "rejilla": {
            "posiciones": posiciones,
            "ocupadas": posiciones - len(OECF.vacias),
            "vacias": [biboecf.texto_zona(t) for t in OECF.vacias],
            "repetidas": {biboecf.texto_zona(t): [raws[i].name
                                                  for i in indices]
                          for t, indices in OECF.repetidas.items()},
            "fuera": [raws[i].name for i in OECF.fuera]},
        "analizable": OECF.esAnalizable,
        KD.INCIDENCIAS: [
            i._replace(tomas=tuple(raws[t].name for t in i.tomas))._asdict()
            for i in biboecf.incidencias(OECF)],
        KD.ANALISIS: (biboecf.analisis_a_dict(OECF.analisis)
                      if OECF.analisis else None)}

    # --- Se compone entero antes de escribir: si algo falla, no queda
    #     un archivo a medias
    texto = json.dumps(datos, ensure_ascii=False, indent=KD.SANGRIA)
    ruta = OECF.carpeta / KD.ARCHIVO
    try:
        ruta.write_text(texto, encoding="utf-8")
    except OSError:
        return None
    return ruta
