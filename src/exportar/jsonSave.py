# -*- coding: utf-8 *-*
"""
    :Propósito: Graba en la carpeta OECF de la serie un JSON con los
                datos del estudio, y de él restaura la serie preparada.
                Solo datos, sin textos traducidos. JSON y no YAML: viene
                con Python, sin dependencias. Lo leen programas (FE), no
                personas: cada dato en un solo sitio, cada clave con un
                solo tipo de valor y siempre presente (null si no hay
                dato). La sangría, solo para poder depurarlo a mano.
                Lee, comprueba y graba el mismo archivo con las mismas
                piezas internas: no se parte en «leer» y «grabar» (sería
                un tercer archivo para lo común, y solo lo usa gui/main.py)
    :Autor:     Tony Diana
    :Versión:   26.10.30
"""

# cSpell:ignore camara, codificacion, kmed, lstar, oecf, timespec

__all__ = ["archivos_serie", "es_mas_nuevo", "es_preparada",
           "grabar_factor_lamina",
           "grabar_json", "grabar_resultados", "grabar_revelado",
           "hay_review", "leer_factor_lamina", "leer_resultados",
           "leer_review", "restaurar_serie", "revelado_pendiente",
           "version_analisis"]

# --- Bibliotecas estándar Python
import dataclasses
from datetime import datetime
import json
import math
from pathlib import Path

# --- Bibliotecas internas
from bib import std
from bib.oecfMediadores import (KES, KMED, estado_version, texto_zona,
                                version_formato)
from leer import Cam
from oecfCalc import (BalanceMedido, calcular_incidencias, Exp,
                      incidencia_a_dict, KAN, KS, MedidaTiff, OECF, Review,
                      review_a_dict, review_de_dict, Toma)


#
# --- Constantes de la grabación (solo las usa este módulo; FE no las
#     necesita: recibe el dict)
class KEE(std.EnumMutable):
    """ Constantes de la escritura del JSON del estudio. """

    # --- Sangría, para que se pueda depurar a mano
    SANGRIA = 2

    # --- Fecha de la grabación, sin microsegundos
    FORMATO_FECHA = "seconds"


#
# --- Ruta del JSON de esta carpeta OECF: en su raíz. Con ZONAS, basta
#     para rehacer el análisis: es lo que se lleva FE (Tony, 2026-10-19)
def _ruta(carpeta: Path) -> Path:
    return carpeta / KES.ARCHIVO


#
# --- El JSON de esta carpeta OECF, leído (OSError o ValueError si no
#     existe o no se puede leer)
def _leer(carpeta: Path) -> dict:
    return json.loads(_ruta(carpeta).read_text(encoding=KES.CODIFICACION))


#
# --- ¿El JSON es de una versión del formato más nueva que la de esta
#     aplicación? (KeyError, TypeError o ValueError si no trae una versión
#     que se entienda). Los 1.x, con la clave antigua: ver version_formato
def _es_mas_nuevo(datos: dict) -> bool:
    return (estado_version(version_formato(datos), KES.VERSION_FORMATO,
                           False)
            == KMED.VERSION_NUEVA)


#
# --- Escribe el JSON de esta carpeta OECF. Se compone entero antes de
#     escribir: si algo falla, no queda un archivo a medias
def _escribir(carpeta: Path, datos: dict) -> None:
    texto = json.dumps(datos, ensure_ascii=False, indent=KEE.SANGRIA)
    _ruta(carpeta).write_text(texto, encoding=KES.CODIFICACION)


#
# --- Ruta relativa a la carpeta de la serie, con «/» en cualquier sistema
def _relativa(ruta: Path, oecf: OECF) -> str:
    return ruta.relative_to(oecf.path).as_posix()


#
# --- Las incidencias de la serie, con los archivos en vez de índices
def _incidencias(oecf: OECF) -> list[dict]:
    return [incidencia_a_dict(i, oecf.raws)
            for i in calcular_incidencias(oecf)]


#
def hay_review(carpeta: Path) -> bool:
    """
    ¿El JSON de esta carpeta OECF tiene ya la medida (tras Generar)? No,
    si no existe o no se puede leer.
    """
    try:
        return bool(_leer(carpeta).get(KES.MEDIDA))
    except (OSError, ValueError):
        return False


#
def version_analisis(carpeta: Path) -> str | None:
    """
    Versión del análisis guardada en el JSON de esta carpeta OECF
    (oecf.versionAnalisis): None si no la hay (JSON 1.x, sin medida) o no
    se puede leer (Tony, 2026-11-13)
    """
    try:
        return _leer(carpeta)[KES.OECF].get(KES.O_VERSION_ANALISIS)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


#
def archivos_serie(carpeta: Path) -> list[str] | None:
    """
    Nombres de los RAW originales de la serie guardada en el JSON de esta
    carpeta OECF, en orden de disparo (None si no se puede leer). Para
    saber si las fotos de la carpeta cambiaron desde que se preparó
    (Tony, 2026-11-13)
    """
    try:
        return [t[KES.T_ARCHIVO]
                for t in _leer(carpeta)[KES.SERIE][KES.S_TOMAS]]
    except (OSError, ValueError, KeyError, TypeError):
        return None


#
def revelado_pendiente(oecf: OECF) -> bool:
    """
    ¿Hay exportaciones del revelador por medir? Sí, si hay alguna y el
    JSON aún no tiene su revelado, o si alguna es más nueva que el JSON
    (se volvió a exportar después de medir). No, si no hay ninguna o no
    se puede leer (Tony, 2026-11-13)
    """
    rutas = list(oecf.exportaciones.values())
    if not rutas:
        return False
    try:
        if _leer(oecf.carpeta).get(KES.REVELADO) is None:
            return True
        medido = _ruta(oecf.carpeta).stat().st_mtime
        return any(ruta.stat().st_mtime > medido for ruta in rutas)
    except (OSError, ValueError):
        return False


#
def leer_review(oecf: OECF) -> Review | None:
    """
    El análisis de esta serie guardado en su JSON (None si no lo hay o no
    se puede leer), con lo que no se guarda en la medida repuesto desde
    la serie y desde el revelado (ver _completar)
    """
    try:
        datos = _leer(oecf.carpeta)
        medida = datos.get(KES.MEDIDA)
        if not medida:
            return None
        return _completar(review_de_dict(medida), oecf,
                          datos.get(KES.REVELADO))
    except (OSError, ValueError, KeyError, TypeError):
        return None


#
# --- Repone en el análisis leído lo que es de la serie (cada dato, en un
#     solo sitio: ver review.KAN): la cámara, la fecha, la exposición y
#     los bits de la ZV, la copia de cada toma medida y, en los balances,
#     lo que guarda la cámara; y el L* del revelador y el contraste del
#     paño por zona (las 31: NaN sin exportación o si no se pudo medir; ()
#     sin revelado)
def _completar(review: Review, oecf: OECF, revelado: dict | None) -> Review:
    por_nombre = {raw.name: (raw, toma)
                  for raw, toma in zip(oecf.raws, oecf.tomas)}

    #
    def copia_de(archivo: str) -> str | None:
        raw, _ = por_nombre[archivo]
        ruta = oecf.copias.get(raw)
        return ruta.name if ruta else None

    #
    def balance_de(b: BalanceMedido) -> BalanceMedido:
        _, toma = por_nombre[b.archivo]
        return b._replace(
            nombre=toma.nombreWB, kelvin_cam=toma.kelvin,
            multiplicadores=(tuple(float(x) for x in toma.WB) if toma.WB
                             else None))

    revelador: tuple[float, ...] = ()
    contraste: tuple[float, ...] = ()
    if revelado is not None:
        exportaciones = revelado[KES.R_EXPORTACIONES]
        lstar = {e[KES.T_TERCIO_EV]: e[KES.E_LSTAR] for e in exportaciones}
        revelador = tuple(
            math.nan if (lstar.get(t) is None) else float(lstar[t])
            for t in range(-KS.TERCIOS_LADO, KS.TERCIOS_LADO + 1))

        # --- El contraste del paño (sin la clave, JSON anteriores al
        #     2.1: NaN en todas)
        medido = {e[KES.T_TERCIO_EV]: e.get(KES.E_CONTRASTE)
                  for e in exportaciones}
        contraste = tuple(
            math.nan if (medido.get(t) is None) else float(medido[t])
            for t in range(-KS.TERCIOS_LADO, KS.TERCIOS_LADO + 1))
    exp = oecf.ZV
    return dataclasses.replace(
        review,
        cam=oecf.cam.nombre if oecf.cam else "",
        fecha=oecf.fecha.isoformat() if oecf.fecha else None,
        f=exp.f if exp else None,
        tv=exp.tv if exp else None,
        iso=exp.iso if exp else None,
        bits=oecf.bits,
        zonas=tuple(dataclasses.replace(z, copia=copia_de(z.archivo)) if z
                    else None for z in review.zonas),
        control=tuple(dataclasses.replace(z, copia=copia_de(z.archivo))
                      for z in review.control),
        balances=tuple(balance_de(b) for b in review.balances),
        revelador=revelador,
        contraste=contraste)


#
def grabar_revelado(oecf: OECF, medidas: dict[int, MedidaTiff]) -> bool:
    """
    Sustituye el revelado del JSON de esta serie por lo medido en sus
    exportaciones ({tercioEV: MedidaTiff}), y rehace sus incidencias
    (pueden avisar de las exportaciones). Lo demás, como estaba. False
    si no se puede leer o escribir.
    """
    rutas = oecf.exportaciones
    try:
        datos = _leer(oecf.carpeta)
        datos[KES.REVELADO] = {KES.R_EXPORTACIONES: [
            {KES.T_TERCIO_EV: tercio_ev,
             KES.T_ARCHIVO: _relativa(rutas[tercio_ev], oecf),
             KES.E_BITS: m.bits, KES.E_CONTRASTE: m.contraste,
             KES.E_ESPACIO: m.espacio, KES.E_LSTAR: m.lstar,
             KES.E_MOTIVO: m.motivo}
            for tercio_ev, m in sorted(medidas.items())]}
        datos[KES.INCIDENCIAS] = _incidencias(oecf)
        _escribir(oecf.carpeta, datos)
    except (OSError, ValueError):
        return False
    return True


#
def leer_resultados(carpeta: Path) -> dict | None:
    """
    Los resultados del análisis guardados en el JSON de esta carpeta OECF
    (None si no los hay o no se puede leer)
    """
    try:
        return _leer(carpeta).get(KES.RESULTADOS)
    except (OSError, ValueError):
        return None


#
def grabar_resultados(carpeta: Path, resultados: dict) -> bool:
    """
    Añade (o sustituye) los resultados del análisis en el JSON de esta
    carpeta OECF (lo demás, como estaba). False si no se puede leer o
    escribir.
    """
    try:
        datos = _leer(carpeta)
        datos[KES.RESULTADOS] = resultados
        _escribir(carpeta, datos)
    except (OSError, ValueError):
        return False
    return True


#
def grabar_factor_lamina(carpeta: Path, factor: int) -> bool:
    """
    Añade (o sustituye) en la medida del JSON de esta carpeta OECF el
    tamaño de la segunda lámina elegido en la caja Lámina (lo demás, como
    estaba). False si no se puede leer o escribir, o si aún no hay medida
    """
    try:
        datos = _leer(carpeta)
        medida = datos.get(KES.MEDIDA)
        if not medida:
            return False
        medida[KAN.J_FACTOR_LAMINA] = factor
        _escribir(carpeta, datos)
    except (OSError, ValueError, TypeError):
        return False
    return True


#
def leer_factor_lamina(carpeta: Path) -> int | None:
    """
    El tamaño de la segunda lámina guardado en el JSON de esta carpeta
    OECF (None si no lo hay, como en los JSON 1.0, o no se puede leer)
    """
    try:
        medida = _leer(carpeta).get(KES.MEDIDA)
        return medida.get(KAN.J_FACTOR_LAMINA) if medida else None
    except (OSError, ValueError, AttributeError):
        return None


#
def grabar_json(OECF: OECF, programa: str, version: str) -> Path | None:
    """
    Graba el JSON en la carpeta OECF de la serie, con lo que ya tiene OECF
    (leído, repartido y copiado) y el nombre y la versión del programa que
    lo graba, y devuelve su ruta, o None si no se pudo escribir (no impide
    el análisis). Las tomas de la serie, por el nombre de su archivo. El
    revelado y los resultados, null: son de etapas posteriores
    """
    raws = OECF.raws
    cam = OECF.cam

    tomas = []
    for raw, toma, tercioEV, parte in zip(raws, OECF.tomas, OECF.tercioEVs,
                                          OECF.partes):
        exp = toma.exp
        copia = OECF.copias.get(raw)
        tomas.append({
            KES.T_ARCHIVO: raw.name,
            KES.T_COPIA: _relativa(copia, OECF) if copia else None,
            KES.T_F: exp.f if exp else None,
            KES.T_TV: exp.tv if exp else None,
            KES.T_ISO: exp.iso if exp else None,
            KES.T_FECHA: toma.fecha.isoformat() if toma.fecha else None,
            KES.T_TERCIO_EV: tercioEV,
            KES.T_WB: list(toma.WB) if toma.WB else None,
            KES.T_NOMBRE_WB: toma.nombreWB,
            KES.T_KELVIN: toma.kelvin,
            KES.T_BITS: toma.bits,
            KES.T_TAPADA: toma.tapada,
            KES.T_OSCURA: toma.oscura,
            KES.T_ZONA: (OECF.KT.NOMBRE_TAPADA
                         if (parte == OECF.KT.PARTE_TAPADA)
                         else (None if (tercioEV is None)
                               else texto_zona(tercioEV))),
            KES.T_PARTE: parte})

    datos = {
        KES.OECF: {
            KES.O_VERSION_APP: version,
            KES.O_VERSION_FORMATO: KES.VERSION_FORMATO,
            KES.O_VERSION_ANALISIS: (KAN.VERSION_ANALISIS if OECF.review
                                     else None)},
        KES.INFO: {
            KES.I_PROGRAMA: {KES.P_NOMBRE: programa},
            KES.I_FECHA: datetime.now().isoformat(
                timespec=KEE.FORMATO_FECHA),
            KES.I_CARPETA: str(OECF.path),
            KES.I_CAMARA: ({KES.C_MARCA: cam.marca, KES.C_MODELO: cam.modelo}
                           if cam else None)},
        KES.SERIE: {
            KES.S_ISO: (round(OECF.isoSerie)
                        if (OECF.isoSerie is not None) else None),
            KES.S_BALANCE: OECF.balancePersonalizado,
            KES.S_ANALIZABLE: OECF.esAnalizable,
            KES.S_SALTOS: [{KES.T_ARCHIVO: raws[i].name,
                            KES.S_TERCIO_EV_ESPERADO: esperado,
                            KES.T_TERCIO_EV: tercioEV}
                           for i, esperado, tercioEV
                           in OECF.secuencia.saltos],           # type: ignore
            KES.S_TOMAS: tomas},
        KES.INCIDENCIAS: _incidencias(OECF),
        KES.MEDIDA: (review_a_dict(OECF.review) if OECF.review else None),
        KES.REVELADO: None,
        KES.RESULTADOS: None}

    try:
        _escribir(OECF.carpeta, datos)
    except OSError:
        return None
    return _ruta(OECF.carpeta)


#
def es_preparada(carpeta: Path) -> bool:
    """
    ¿Esta carpeta es la OECF de una serie preparada? Sí, si tiene el
    JSON.
    """
    return _ruta(carpeta).is_file()


#
def es_mas_nuevo(carpeta: Path) -> bool:
    """
    ¿El JSON de esta carpeta OECF es de una versión del formato más nueva
    que la que conoce esta aplicación? Falso si no se puede leer o no trae
    versión: eso es un JSON dañado, no uno nuevo
    """
    try:
        return _es_mas_nuevo(_leer(carpeta))
    except (OSError, ValueError, KeyError, TypeError):
        return False


#
def restaurar_serie(carpeta: Path) -> OECF | None:
    """
    La serie preparada de esta carpeta OECF (o de la que se guardó con el
    JSON, se llame como se llame), desde su JSON y sus copias, sin leer
    los originales (ver OECF.Restaurar). None si el JSON no se puede leer
    o es de una versión del formato más nueva (ver es_mas_nuevo).
    """
    try:
        datos = _leer(carpeta)
        if _es_mas_nuevo(datos):
            return None
        archivos, tomas, copias = [], [], {}
        for t in datos[KES.SERIE][KES.S_TOMAS]:
            exp = (Exp(f=t[KES.T_F], tv=t[KES.T_TV], iso=t[KES.T_ISO])
                   if None not in (t[KES.T_F], t[KES.T_TV], t[KES.T_ISO])
                   else None)
            fecha = t[KES.T_FECHA]
            tomas.append(Toma(
                exp=exp,
                fecha=datetime.fromisoformat(fecha) if fecha else None,
                WB=tuple(t[KES.T_WB]) if t[KES.T_WB] else None,
                tapada=t[KES.T_TAPADA],
                oscura=t[KES.T_OSCURA],
                nombreWB=t[KES.T_NOMBRE_WB],
                bits=t[KES.T_BITS],
                kelvin=t[KES.T_KELVIN]))
            archivos.append(t[KES.T_ARCHIVO])
            if t[KES.T_COPIA]:
                copias[t[KES.T_ARCHIVO]] = t[KES.T_COPIA]
        camara = datos[KES.INFO][KES.I_CAMARA]
        cam = (Cam(marca=camara[KES.C_MARCA],
                   modelo=camara[KES.C_MODELO]) if camara else None)
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return OECF.Restaurar(carpeta, archivos, tomas, copias, cam)
