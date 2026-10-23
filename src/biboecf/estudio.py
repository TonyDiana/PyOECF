# -*- coding: utf-8 *-*
"""
    :Propósito: Graba en la carpeta OECF de la serie un JSON con los
                datos del estudio, y de él restaura la serie preparada.
                Solo datos, sin textos traducidos. JSON y no YAML: viene
                con Python, sin dependencias. Lo leen programas (FE), no
                personas: cada dato en un solo sitio, cada clave con un
                solo tipo de valor y siempre presente (null si no hay
                dato). La sangría, solo para poder depurarlo a mano
    :Autor:     Tony Diana
    :Versión:   26.10.21
"""

# cSpell:ignore biboecf, camara, timespec

__all__ = ["KES", "es_mas_nuevo", "es_preparada", "grabar_json",
           "grabar_resultados", "grabar_revelado", "hay_review",
           "leer_resultados", "leer_review", "restaurar_serie"]

# --- Bibliotecas estándar Python
import dataclasses
from datetime import datetime
import json
import math
from pathlib import Path

# --- Bibliotecas internas
from bib import std
from .cam import Cam
from .constantes import COM as KCOM
from .informe import incidencias
from .kernel import Exp, OECF, Toma
from .review import BalanceMedido, Review, review_a_dict, review_de_dict
from .revelado import MedidaTiff
from .secuencia import KS
from .zonas import texto_zona


#
# --- Constantes de los datos
class KES(std.EnumMutable):
    """ Constantes del JSON del estudio. """

    # --- Nombre del archivo, en la carpeta OECF de la serie (ver _ruta)
    ARCHIVO = "estudio.json"

    # --- Sangría, para que se pueda depurar a mano
    SANGRIA = 2

    # --- Fecha de la grabación, sin microsegundos
    FORMATO_FECHA = "seconds"

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

    # --- oecf: lo genérico, el estudio: {version}, la del formato de este
    #     JSON (KCOM.RUTA_VERSION_JSON, MAYOR.MENOR), no la del programa.
    #     Es lo primero que mira quien lo lee (FE). SI CAMBIAS, AÑADES O
    #     QUITAS UNA CLAVE (aquí, en review.KAN o en excel.KXL), SUBE LA
    #     VERSIÓN:
    #     - MAYOR: se quita o renombra una clave, o cambia lo que
    #       significa (quien lee una versión más nueva que la suya la
    #       rechaza; una más antigua, puede leerla si se programa)
    #     - MENOR: se añade una clave (quien lee ignora lo que no conoce)
    #     EN CONSTRUCCIÓN: hasta que FE lea el JSON por primera vez, el
    #     formato se queda en 1.0 aunque cambie (Tony, 2026-10-21)
    O_VERSION = "version"

    # --- info: de dónde sale el archivo; nada de aquí se usa para
    #     calcular. El programa que lo grabó, {nombre, version}, lo da
    #     quien llama a grabar_json: la biblioteca no sabe qué programa la
    #     usa. La carpeta de la serie, solo para saber el origen (Tony,
    #     2026-10-21). La cámara, {marca, modelo} (la lee restaurar_serie
    #     si no queda ninguna copia RAW)
    I_PROGRAMA = "programa"
    P_NOMBRE = "nombre"
    P_VERSION = "version"
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

    # --- incidencias: biboecf.Incidencia con los archivos en vez de
    #     índices (sus campos son las claves): códigos, sin frases; las
    #     traduce quien las lea

    # --- revelado: lo medido en cada exportación del revelador
    #     (biboecf.MedidaTiff), por su tercioEV, con su archivo relativo a
    #     la carpeta de la serie y con «/»
    R_EXPORTACIONES = "exportaciones"
    E_BITS = "bits"
    E_ESPACIO = "espacio"
    E_LSTAR = "lstar"
    E_MOTIVO = "motivo"

    # --- resultados: los del análisis (Excel.resultados), tras Generar y
    #     Analizar revelado: lo que lee FotoEstación, que no lleva biboecf


#
# --- Ruta del JSON de esta carpeta OECF: en su raíz. Con ZONAS, basta
#     para rehacer el análisis: es lo que se lleva FE (Tony, 2026-10-19)
def _ruta(carpeta: Path) -> Path:
    return carpeta / KES.ARCHIVO


#
# --- Versión del formato del JSON: la primera línea no vacía de su
#     archivo (si alguien escribe algo debajo, no se cuela en el JSON)
def _version_formato() -> str:
    texto = KCOM.RUTA_VERSION_JSON.read_text(encoding="utf-8")
    return next(linea.strip() for linea in texto.splitlines()
                if linea.strip())


#
# --- El JSON de esta carpeta OECF, leído (OSError o ValueError si no
#     existe o no se puede leer)
def _leer(carpeta: Path) -> dict:
    return json.loads(_ruta(carpeta).read_text(encoding="utf-8"))


#
# --- Las partes numéricas de una versión del formato («1.0» → (1, 0)):
#     así 1.10 es mayor que 1.9 (ValueError si no son números)
def _partes(version: str) -> tuple[int, ...]:
    return tuple(int(parte) for parte in version.split("."))


#
# --- ¿El JSON es de una versión del formato más nueva que la de esta
#     aplicación? (KeyError, TypeError o ValueError si no trae una versión
#     que se entienda)
def _es_mas_nuevo(datos: dict) -> bool:
    return (_partes(datos[KES.OECF][KES.O_VERSION])
            > _partes(_version_formato()))


#
# --- Escribe el JSON de esta carpeta OECF. Se compone entero antes de
#     escribir: si algo falla, no queda un archivo a medias
def _escribir(carpeta: Path, datos: dict) -> None:
    texto = json.dumps(datos, ensure_ascii=False, indent=KES.SANGRIA)
    _ruta(carpeta).write_text(texto, encoding="utf-8")


#
# --- Ruta relativa a la carpeta de la serie, con «/» en cualquier sistema
def _relativa(ruta: Path, oecf: OECF) -> str:
    return ruta.relative_to(oecf.path).as_posix()


#
# --- Las incidencias de la serie, con los archivos en vez de índices
def _incidencias(oecf: OECF) -> list[dict]:
    raws = oecf.raws
    return [i._replace(tomas=tuple(raws[t].name for t in i.tomas))._asdict()
            for i in incidencias(oecf)]


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
#     lo que guarda la cámara; y el L* del revelador por zona (las 31: NaN
#     sin exportación o si no se pudo medir; () sin revelado)
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
    if revelado is not None:
        lstar = {e[KES.T_TERCIO_EV]: e[KES.E_LSTAR]
                 for e in revelado[KES.R_EXPORTACIONES]}
        revelador = tuple(
            math.nan if (lstar.get(t) is None) else float(lstar[t])
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
        revelador=revelador)


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
             KES.E_BITS: m.bits, KES.E_ESPACIO: m.espacio,
             KES.E_LSTAR: m.lstar, KES.E_MOTIVO: m.motivo}
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
        KES.OECF: {KES.O_VERSION: _version_formato()},
        KES.INFO: {
            KES.I_PROGRAMA: {KES.P_NOMBRE: programa,
                             KES.P_VERSION: version},
            KES.I_FECHA: datetime.now().isoformat(
                timespec=KES.FORMATO_FECHA),
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
