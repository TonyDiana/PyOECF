# -*- coding: utf-8 *-*
"""
    :Propósito: Graba en la carpeta OECF de la serie un JSON con los
                datos de la preparación. Solo datos, sin textos
                traducidos. JSON y no YAML: viene con Python, sin
                dependencias
    :Autor:     Tony Diana
    :Versión:   26.10.07
"""

# cSpell:ignore biboecf, ocupadas

__all__ = ["grabar_json"]

# --- Bibliotecas estándar Python
import json
from datetime import datetime
from pathlib import Path

# --- Bibliotecas internas
from bib import biboecf, std
from .constantes import K


#
# --- Constantes de los datos
class KD(std.EnumMutable):
    """ Constantes del JSON de la serie. """

    # --- Nombre del archivo, en la carpeta OECF de la serie
    archivo = "estudio.json"

    # --- Sangría, para que se pueda leer a mano
    sangria = 2

    # --- Fecha del análisis, sin microsegundos
    formato_fecha = "seconds"


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
            "zona": (None if tercioEV is None
                     else biboecf.texto_zona(tercioEV)),
            "parte": parte})

    posiciones = biboecf.KS.lados * biboecf.KS.tercios_lado + 1
    datos = {
        "pyoecf": K.version,
        "fecha": datetime.now().isoformat(timespec=KD.formato_fecha),
        "carpeta": str(OECF.path),
        "camara": {"marca": cam.marca, "modelo": cam.modelo} if cam else None,
        "balance_personalizado": OECF.balancePersonalizado,
        "tapadas": len(OECF.tapadas),
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
        "analizable": OECF.esAnalizable}

    # --- Se compone entero antes de escribir: si algo falla, no queda
    #     un archivo a medias
    texto = json.dumps(datos, ensure_ascii=False, indent=KD.sangria)
    ruta = OECF.carpeta / KD.archivo
    try:
        ruta.write_text(texto, encoding="utf-8")
    except OSError:
        return None
    return ruta
