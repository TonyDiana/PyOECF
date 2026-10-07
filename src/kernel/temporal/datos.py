# -*- coding: utf-8 *-*
"""
    :Propósito: TEMPORAL. Graba en la carpeta de la serie un JSON con los
                datos del análisis, para ir viendo qué se le pasará a FE.
                Solo datos, sin textos traducidos. JSON y no YAML: viene
                con Python, sin dependencias
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
from ..constantes import K
from .rejilla import Rejilla


#
# --- Constantes de los datos
class KD(std.EnumMutable):
    """ Constantes del JSON de la serie. """

    # --- Nombre del archivo, en la carpeta de la serie
    archivo = "pyoecf_serie.json"

    # --- Sangría, para que se pueda leer a mano
    sangria = 2

    # --- Fecha del análisis, sin microsegundos
    formato_fecha = "seconds"

    # --- Parte de la secuencia de cada toma (None si no encaja o no se
    #     pudo leer): {índice: parte}
    @staticmethod
    def partes(sec: biboecf.Secuencia, tapadas: list[bool]) -> dict[int, str]:
        partes = {i: "inicial" for i in sec.iniciales}
        for n, lado in enumerate(sec.lados, 1):
            partes.update({i: f"lado{n}" for i in lado})
        partes.update({i: "cambio" for i in sec.cambios})
        partes.update({i: "tapada" for i, t in enumerate(tapadas) if t})
        partes.update({i: "balance" for i in sec.balances})
        partes.update({i: "sobrante" for i in sec.sobrantes})
        return partes


# --- Graba el JSON en la carpeta de la serie y devuelve su ruta, o None
#     si no se pudo escribir (no impide el análisis). exps: (segundos,
#     diafragma, ISO) de cada toma; ks: su posición en tercios; tapadas:
#     si es una toma tapada; quitar: si no va a la rejilla. Todas en el
#     orden de raws (None si no se pudo leer). sec: partes de la secuencia
def grabar_json(carpeta: Path, raws: list[Path],
                exps: list[tuple[float, float, float] | None],
                ks: list[int | None], balance: bool | None,
                tapadas: list[bool], sec: biboecf.Secuencia,
                quitar: list[bool]) -> Path | None:
    cam = biboecf.leer_cam(raws[0])
    celdas, fuera = Rejilla.repartir(*Rejilla.sin(raws, ks, quitar))
    partes = KD.partes(sec, tapadas)

    tomas = []
    for i, (raw, exp, k) in enumerate(zip(raws, exps, ks)):
        segundos, diafragma, iso = exp if exp else (None, None, None)
        tomas.append({
            "archivo": raw.name,
            "tv": segundos,
            "f": diafragma,
            "iso": iso,
            "k": k,
            "zona": None if k is None else biboecf.texto_zona(k),
            "parte": partes.get(i)})

    datos = {
        "pyoecf": K.version,
        "fecha": datetime.now().isoformat(timespec=KD.formato_fecha),
        "carpeta": str(carpeta),
        "camara": {"marca": cam[0], "modelo": cam[1]} if cam else None,
        "balance_personalizado": balance,
        "tapadas": sum(tapadas),
        "balances_camara": len(sec.balances),
        "saltos": [{"archivo": raws[i].name, "k_esperado": esperado, "k": k}
                   for i, esperado, k in sec.saltos],
        "tomas": tomas,
        "rejilla": {
            "posiciones": Rejilla.KR.posiciones,
            "ocupadas": Rejilla.KR.posiciones - len(Rejilla.vacias(celdas)),
            "vacias": [Rejilla.nombre(p) for p in Rejilla.vacias(celdas)],
            "repetidas": {Rejilla.nombre(p): idents
                          for p, idents in sorted(celdas.items())
                          if len(idents) > 1},
            "fuera": fuera}}

    # --- Se compone entero antes de escribir: si algo falla, no queda
    #     un archivo a medias
    texto = json.dumps(datos, ensure_ascii=False, indent=KD.sangria)
    ruta = carpeta / KD.archivo
    try:
        ruta.write_text(texto, encoding="utf-8")
    except OSError:
        return None
    return ruta
