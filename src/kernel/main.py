# -*- coding: utf-8 *-*
"""
    :Propósito: Kernel PyOECF.
    :Autor:     Tony Diana
    :Versión:   26.10.09
"""

# cSpell:ignore biboecf, borderwidth, boton, choosedir, codigo, customtkinter
# cSpell:ignore exps, initialdir, leidas, mclocale, mcset, meipass, msgcat
# cSpell:ignore oecf, padx, pady, redibuja, redibujar, relx, screeninfo, tamano
# cSpell:ignore textvariable, winfo

# --- Valenciano
# cSpell:ignore acadèmica, accedir, acord, Ajuda, Analitzar, Càmera, carpetes
# cSpell:ignore denegat, Eixir, existeix, fitxer, imatge, imatges, Incidències
# cSpell:ignore Llegint, llegir, Llicència, lliure, Mostra, nincidències
# cSpell:ignore Permís, pogut, Selecció, Seleccioneu, sèrie, Sèrie, Trieu
# cSpell:ignore vàlid, Versió

__all__ = ["Ventana"]

# --- Bibliotecas estándar Python
import os
import subprocess
import sys
import tkinter as tk
import webbrowser
from collections.abc import Callable, Iterator
from pathlib import Path
from tkinter import filedialog

# --- Bibliotecas externas
import customtkinter as ctk
import screeninfo

# --- Bibliotecas internas
from bib import biboecf, std
from .constantes import K
from .json_estudio import grabar_json
from .rejilla import Rejilla


#
class Ventana(ctk.CTk):
    """ Ventana principal de PyOECF. """

    # --- OJO: aquí NO tiene efecto. __slots__ solo impide crear atributos
    #     nuevos si todas las clases de las que se hereda también lo usan,
    #     y customtkinter (ctk.CTk) no lo usa: la ventana sigue teniendo su
    #     __dict__ y admite cualquier atributo. Se deja por la norma
    # __slots__ = []

    # --- Constantes de la ventana (las de toda la app están en K)
    class KV(std.EnumMutable):
        """ Constantes de la ventana principal. """

        # --- Textos {idioma: texto}
        txt_version = {K.es: "Versión", K.en: "Version",
                       K.ca: "Versió"}
        txt_carpeta = {K.es: "Seleccione carpeta", K.en: "Select folder",
                       K.ca: "Seleccioneu carpeta"}
        txt_preparar = {K.es: "Preparar", K.en: "Prepare",
                        K.ca: "Preparar"}
        txt_abrir_oecf = {K.es: "Abrir OECF", K.en: "Open OECF",
                          K.ca: "Obrir OECF"}
        txt_fase_carpeta = {K.es: "Carpeta", K.en: "Folder",
                            K.ca: "Carpeta"}
        txt_fase_cam = {K.es: "Cámara", K.en: "Camera",
                        K.ca: "Càmera"}
        txt_archivo = {K.es: "Primera imagen", K.en: "First image",
                       K.ca: "Primera imatge"}
        txt_fecha = {K.es: "Fecha", K.en: "Date", K.ca: "Data"}

        # --- Fecha y hora de disparo, como se escriben en cada idioma
        formato_fecha = {K.es: "%d/%m/%Y %H:%M:%S",
                         K.en: "%Y-%m-%d %H:%M:%S",
                         K.ca: "%d/%m/%Y %H:%M:%S"}
        txt_modelo = {K.es: "Modelo", K.en: "Model",
                      K.ca: "Model"}
        txt_exp = {K.es: "Tv", K.en: "Tv",
                   K.ca: "Tv"}
        txt_f = {K.es: "f/", K.en: "f/",
                 K.ca: "f/"}
        txt_iso = {K.es: "ISO", K.en: "ISO",
                   K.ca: "ISO"}

        # --- Serie: los {campos} se rellenan al mostrarlos
        txt_fase_serie = {K.es: "Serie", K.en: "Series",
                          K.ca: "Sèrie"}
        txt_leyendo = {K.es: "Leyendo {n} de {total}…",
                       K.en: "Reading {n} of {total}…",
                       K.ca: "Llegint {n} de {total}…"}
        txt_resumen = {K.es: ("{total} imagen · de {desde} a {hasta}",
                              "{total} imágenes · de {desde} a {hasta}"),
                       K.en: ("{total} image · from {desde} to {hasta}",
                              "{total} images · from {desde} to {hasta}"),
                       K.ca: ("{total} imatge · de {desde} a {hasta}",
                              "{total} imatges · de {desde} a {hasta}")}
        txt_sin_leer = {K.es: " · {n} sin leer", K.en: " · {n} unreadable",
                        K.ca: " · {n} sense llegir"}

        # --- Resumen de la rejilla en una línea: separador entre trozos
        sep_resumen = " · "

        # --- Incidencias de la rejilla: botón bajo la Z0, con cuántas
        #     hay, y su propia ventana (ancho × alto, en píxeles)
        txt_incidencias = {K.es: "Incidencias ({n})", K.en: "Issues ({n})",
                           K.ca: "Incidències ({n})"}
        txt_sin_incidencias = {K.es: "Sin incidencias", K.en: "No issues",
                               K.ca: "Sense incidències"}

        # --- Las incidencias, una por línea, también en un archivo de
        #     texto en la carpeta OECF, en el idioma de la ventana
        sep_incidencias = "\n"
        archivo_incidencias = "incidencias.txt"
        # --- Analizar: botón bajo la ZX, activo solo si la serie sirve
        txt_analizar = {K.es: "Analizar", K.en: "Analyze",
                        K.ca: "Analitzar"}
        txt_titulo_incidencias = {K.es: "Incidencias de la serie",
                                  K.en: "Series issues",
                                  K.ca: "Incidències de la sèrie"}
        tamano_incidencias = "520x320"

        txt_sin_carpeta = {K.es: "La carpeta no existe",
                           K.en: "The folder does not exist",
                           K.ca: "La carpeta no existeix"}

        txt_sin_raw = {K.es: "No hay RAW en la carpeta",
                       K.en: "No RAW files in the folder",
                       K.ca: "No hi ha RAW en la carpeta"}

        txt_no_read = {K.es: "No se ha podido leer", K.en: "Could not be read",
                       K.ca: "No s'ha pogut llegir"}
        txt_licencia = {K.es: "Licencia académica de uso libre",
                        K.en: "Academic license, free to use",
                        K.ca: "Llicència acadèmica d'ús lliure"}
        txt_ayuda = {K.es: "Ayuda", K.en: "Help",
                     K.ca: "Ajuda"}
        txt_idioma = {K.es: "Idioma", K.en: "Language",
                      K.ca: "Idioma"}
        txt_salir = {K.es: "Salir", K.en: "Exit",
                     K.ca: "Eixir"}

        # --- Medidas (píxeles)
        margen = 10
        grosor_marco = 2

        # --- Tamaño de la letra de la licencia, en la cabecera (la normal
        #     del tema es 13)
        letra_licencia = 15

        # --- Hueco entre el icono y la licencia, en la cabecera
        sep_licencia = 20

        # --- Datos en una línea: hueco entre un dato y el siguiente
        sep_datos = 30

        # --- A cada lado del título de una caja, entre su texto y la línea
        relleno_titulo = 12

        # --- Dentro de una caja con título: entre el título y el contenido
        separador_superior = 0
        ancho_carpeta = 650

        # --- Principio de sys.platform en Windows: ahí el icono va con
        #     iconbitmap() y el .ico, o customtkinter pone el suyo
        plataforma_windows = "win"

        # --- Abrir una carpeta en el explorador de archivos: macOS
        #     (sys.platform) y la orden de macOS y de Linux. En Windows,
        #     os.startfile
        plataforma_mac = "darwin"
        abrir_mac = "open"
        abrir_linux = "xdg-open"

        # --- Milisegundos sin teclear en la ruta antes de mostrar la
        #     cámara: así no se lee la carpeta con cada letra
        espera_tecleo = 500

        # --- Repintado forzado (ver Ajustar): milisegundos tras ajustar
        #     el tamaño en que se pide a cada elemento que se redibuje (una
        #     pasada por cada uno: la segunda repasa lo que se pinte tarde)
        #     y el evento de Tk que lo pide
        esperas_repintado = (200, 600)
        tk_redibujar = "<Expose>"

        # --- Milisegundos entre la lectura de una imagen y la siguiente:
        #     lo justo para que la ventana atienda al ratón y se repinte
        pausa_lectura = 1

        # --- Separación entre el borde superior del monitor y la ventana:
        #     arriba del todo, para que tenga sitio al crecer hacia abajo
        arriba = 40

        # --- Diálogo de carpetas de Tk (el de Linux): variables Tcl que
        #     muestran la casilla «ocultos» y la dejan desmarcada. Para que
        #     existan hay que cargar antes el diálogo: se le llama con una
        #     opción que no existe, falla y queda cargado
        tcl_ver_casilla_ocultos = "::tk::dialog::file::showHiddenBtn"
        tcl_mostrar_ocultos = "::tk::dialog::file::showHiddenVar"
        tcl_cargar_dialogo = ("tk_getOpenFile", "-opc-que-no-existe")
        tcl_asignar = "set"
        tcl_si, tcl_no = "1", "0"

        # --- Idioma del diálogo de Tk: sus textos salen de un catálogo
        #     (msgcat) en el espacio de nombres de Tk. El diálogo se crea
        #     una vez y se reutiliza: se destruye para que salga con el
        #     idioma nuevo. Traducciones que le faltan al catálogo de Tk
        tcl_idioma = "::msgcat::mclocale"
        tcl_traducir = "::msgcat::mcset"
        tcl_espacio = ("namespace", "eval", "::tk")
        tcl_dialogo = ".__tk_choosedir"
        tcl_faltan = {
            "Show &Hidden Directories": {
                K.es: "Mostrar carpetas &ocultas",
                K.ca: "Mostra les carpetes &ocultes"},
            "&OK": {K.ca: "&D'acord"},
            "&Cancel": {K.ca: "&Cancel·la"},
            "Choose Directory": {K.ca: "Trieu una carpeta"},
            "&Selection:": {K.ca: "&Selecció:"},
            'Directory "%1$s" does not exist.': {
                K.ca: 'La carpeta "%1$s" no existeix.'},
            'Cannot change to the directory "%1$s".\nPermission denied.': {
                K.ca: 'No es pot accedir a la carpeta "%1$s".\n'
                      'Permís denegat.'},
            'Invalid file name "%1$s".': {
                K.ca: 'Nom de fitxer no vàlid "%1$s".'}}

    # --- Variables de clase (solo hay una ventana)
    #
    # --- Llamada pendiente a _mostrar_cam(): al teclear la ruta, se espera
    #     a que se deje de escribir
    __espera: str | None = None

    # --- Cajas hasta Carpeta (incluida): las de encima se quitan al
    #     cambiar de carpeta
    __propias_carpeta: int = 0

    #
    # --- Caja --- | icono | Licencia académica | © Tony Diana |
    #

    # --- Siempre arriba, aunque crezcan las cajas de debajo
    def caja_cabecera(self) -> None:
        # --- Abreviar escritura
        kv = self.KV

        fila = self.CrearCaja(fija=True, marco=False)

        # --- Icono del programa en una etiqueta de Tk, con el fondo de la
        #     ventana: la de customtkinter pide CTkImage, y esa necesita
        #     Pillow. Se guarda la imagen: si no, Python la borra
        try:
            self.icono_cabecera = tk.PhotoImage(
                file=K.path / K.carpeta_recursos / K.icono_png)
            fondo = self._apply_appearance_mode(
                ctk.ThemeManager.theme["CTk"]["fg_color"])
            tk.Label(fila, image=self.icono_cabecera, bg=fondo,
                     borderwidth=0).pack(side="left")
        except tk.TclError:
            pass

        # --- La licencia, a la izquierda tras el icono, un poco separada;
        #     el autor, a la derecha
        self.ApuntarTexto(ctk.CTkLabel(
            fila, font=ctk.CTkFont(size=kv.letra_licencia)),
            kv.txt_licencia).pack(side="left", padx=(kv.sep_licencia, 0))
        ctk.CTkLabel(fila, text=K.derechos).pack(side="right")

    #
    # --- Caja --- | Ayuda | Idioma | Salir |
    #

    def caja_ayuda(self) -> None:
        # --- Abreviar escritura
        kv = self.KV

        fila = self.CrearCaja()

        # --- Los extremos primero, para que Idioma ocupe el centro. Ayuda
        #     abre la web de ayuda en el navegador
        self.ApuntarTexto(ctk.CTkButton(
            fila, command=lambda: webbrowser.open(K.url_help)),
            kv.txt_ayuda).pack(side="left")
        self.ApuntarTexto(ctk.CTkButton(fila, command=self.destroy),
                          kv.txt_salir).pack(side="right")

        # --- Idioma: grupo centrado en el hueco entre Ayuda y Salir. Al
        #     elegir otro en la lista, cambia toda la ventana
        grupo = ctk.CTkFrame(fila, fg_color="transparent")
        grupo.pack(side="left", expand=True)

        self.ApuntarTexto(ctk.CTkLabel(grupo), kv.txt_idioma).pack(
            side="left")

        lista = ctk.CTkComboBox(
            grupo, values=list(K.idiomas.values()), state="readonly",
            command=self.CambiarIdioma)

        lista.set(K.idiomas[K.idioma])
        lista.pack(side="left", padx=(kv.margen, 0))

    #
    # --- Caja --- Carpeta
    #

    def caja_carpeta(self) -> None:
        # --- Abreviar escritura
        kv = self.KV

        # --- Diálogo de carpetas: estas dos preparaciones solo afectan al
        #     de Tk de Linux; Windows y macOS usan el suyo propio
        #
        # --- Sin carpetas ocultas (las que empiezan por punto), pero con
        #     la casilla para verlas
        def _sin_ocultos() -> None:
            try:
                self.tk.call(*kv.tcl_cargar_dialogo)
            except tk.TclError:
                pass

            try:
                self.tk.call(kv.tcl_asignar, kv.tcl_ver_casilla_ocultos,
                             kv.tcl_si)
                self.tk.call(kv.tcl_asignar, kv.tcl_mostrar_ocultos,
                             kv.tcl_no)
            except tk.TclError:
                pass

        # --- En el idioma de la app y no en el del sistema: se completan
        #     las traducciones que le faltan a Tk y, si el diálogo ya
        #     existe, se destruye para que se cree de nuevo en ese idioma
        def _idioma() -> None:
            try:
                for original, textos in kv.tcl_faltan.items():
                    for codigo, traducido in textos.items():
                        self.tk.call(*kv.tcl_espacio, (kv.tcl_traducir,
                                                       codigo, original,
                                                       traducido))
                self.tk.call(kv.tcl_idioma, K.idioma)
                if int(self.tk.call("winfo", "exists", kv.tcl_dialogo)):
                    self.tk.call("destroy", kv.tcl_dialogo)
            except tk.TclError:
                pass

        # --- Pide la carpeta y la escribe en la casilla. El diálogo
        #     empieza en la carpeta de la casilla, si existe; si no, en la
        #     del usuario (no en la de la app)
        def _elegir() -> None:
            _sin_ocultos()
            _idioma()
            escrita = self.ruta.get().strip()
            inicio = Path(escrita) if escrita else Path.home()
            if not inicio.is_dir():
                inicio = Path.home()

            ruta = filedialog.askdirectory(parent=self, initialdir=inicio)
            if ruta:
                self.ruta.set(ruta)
                _mostrar_cam()

        # --- ¿La carpeta escrita es la de la cámara que ya se ve?
        def _es_la_vista() -> bool:
            return (self.OECF is not None
                    and self.carpetaEscrita == self.OECF.path)

        # --- Otra carpeta: se quitan las cajas de encima de esta, sean
        #     las que sean. Los argumentos los pone trace_add y no se usan
        def _otra_carpeta(*_) -> None:
            if _es_la_vista():
                return
            self.QuitarCajas(self.__propias_carpeta)

            # --- after() programa _mostrar_cam() para dentro de
            #     espera_tecleo ms y devuelve el identificador de esa
            #     llamada; after_cancel() la anula si aún no se ha hecho.
            #     Cada letra anula la llamada anterior y programa otra:
            #     solo se ejecuta la de la última, al dejar de teclear
            if self.__espera is not None:
                self.after_cancel(self.__espera)
            self.__espera = self.after(kv.espera_tecleo, _mostrar_cam)

        # --- Muestra la caja de la cámara de la carpeta escrita, si no es
        #     la que ya se ve
        def _mostrar_cam() -> None:

            # --- Si se llega desde el diálogo, se anula la llamada que
            #     pudiera quedar pendiente de haber tecleado antes
            if self.__espera is not None:
                self.after_cancel(self.__espera)
                self.__espera = None
            if not _es_la_vista():
                self.caja_cam()

        # --- La caja: botón · ruta elegida · Abrir OECF · Preparar. Las
        #     cajas que haya
        #     hasta esta (incluida) son las propias; el resto, de encima
        fila = self.CrearCaja(kv.txt_fase_carpeta)
        self.__propias_carpeta = len(self.cajas)
        self.ApuntarTexto(ctk.CTkButton(fila, command=_elegir),
                          kv.txt_carpeta).pack(side="left")

        # --- Preparar antes que la casilla, para que esta ocupe el hueco.
        #     Empieza inactivo: aún no hay RAW
        self.boton_preparar = ctk.CTkButton(fila, command=self.Preparar,
                                            state="disabled")
        self.ApuntarTexto(self.boton_preparar, kv.txt_preparar)
        self.boton_preparar.pack(side="right", padx=(kv.margen, 0))

        # --- Abrir OECF, a la izquierda de Preparar. Inactivo hasta que
        #     se prepare la serie
        self.boton_oecf = ctk.CTkButton(fila, command=self.AbrirOECF,
                                        state="disabled")
        self.ApuntarTexto(self.boton_oecf, kv.txt_abrir_oecf)
        self.boton_oecf.pack(side="right", padx=(kv.margen, 0))

        # --- Cada cambio en la ruta (elegida o tecleada) quita las cajas
        #     de encima y muestra la cámara de la carpeta nueva
        self.ruta = ctk.StringVar()
        self.ruta.trace_add("write", _otra_carpeta)
        carpeta = ctk.CTkEntry(fila, width=kv.ancho_carpeta,
                               textvariable=self.ruta)
        carpeta.pack(side="left", fill="x", expand=True, padx=(kv.margen, 0))

    #
    # --- Caja --- Cámara
    #

    def caja_cam(self) -> None:
        # --- Abreviar escritura
        kv = self.KV

        # --- La caja se construye al elegir carpeta, encima de la
        #     carpeta: todos los datos en una línea
        def _construir_caja() -> None:

            # --- Añade «nombre valor» a la derecha de los que ya hay y
            #     devuelve la etiqueta del valor, para rellenarla. El
            #     primero va pegado al borde; los demás, separados
            def _nuevo_dato(nombre: dict) -> ctk.CTkLabel:
                hueco = kv.sep_datos if grupo.winfo_children() else 0
                self.ApuntarTexto(ctk.CTkLabel(grupo), nombre).pack(
                    side="left", padx=(hueco, 0))
                valor = ctk.CTkLabel(grupo, text="")
                valor.pack(side="left", padx=(kv.margen, 0))
                return valor

            # --- Los datos van en un grupo que no se estira: así queda
            #     centrado en la caja
            interior = self.CrearCaja(kv.txt_fase_cam, self.ReiniciarCam)
            self.propias_cam = len(self.cajas)
            grupo = ctk.CTkFrame(interior, fg_color="transparent")
            grupo.pack()

            self.val_archivo = _nuevo_dato(kv.txt_archivo)
            self.val_fecha = _nuevo_dato(kv.txt_fecha)
            self.val_modelo = _nuevo_dato(kv.txt_modelo)

            # --- Exposición: f, Tv e ISO en un solo texto, centrado en su
            #     hueco
            self.val_exp = ctk.CTkLabel(grupo, text="")
            self.val_exp.pack(side="left", padx=(kv.sep_datos, 0))

            # --- Pone los textos nuevos y hace crecer la ventana
            self.Traducir()

        # --- Siempre es nueva: al cambiar de carpeta se quita la anterior
        _construir_caja()

        # --- Fase 1 de la serie: la carpeta, sus RAW y la exposición de
        #     la primera. Se guarda para Preparar (y su carpeta, para no
        #     rehacer la caja si se vuelve a elegir la misma)
        OECF = self.OECF = biboecf.OECF(self.carpetaEscrita)
        if not OECF.esCarpeta:
            self.Poner(self.val_archivo, kv.txt_sin_carpeta)    # type: ignore
            return

        if not OECF.raws:
            self.Poner(self.val_archivo, kv.txt_sin_raw)        # type: ignore
            return

        self.Poner(self.val_archivo, OECF.primera)              # type: ignore

        # --- Fecha y hora de disparo, en el formato de cada idioma
        fecha = OECF.fecha
        if fecha is None:
            self.Poner(self.val_fecha, kv.txt_no_read)          # type: ignore
        else:
            self.Poner(self.val_fecha,                          # type: ignore
                       lambda: fecha.strftime(K.tr(kv.formato_fecha)))

        # --- Marca y modelo juntos, sin repetir la marca
        cam = OECF.cam
        self.Poner(self.val_modelo,                             # type: ignore
                   kv.txt_no_read if cam is None else cam.nombre)

        # --- f, Tv e ISO salen juntos, en un solo texto: «f/9 · Tv 1/125 s
        #     · ISO 100». Si no se leen, se avisa ahí
        exp = OECF.ZV
        if exp is None:
            self.Poner(self.val_exp, kv.txt_no_read)            # type: ignore
        else:
            def _str_exp() -> str:
                return kv.sep_resumen.join((
                    K.tr(kv.txt_f) + biboecf.OECF.TextoF(exp.f),
                    f"{K.tr(kv.txt_exp)} {biboecf.OECF.TextoTV(exp.tv)}",
                    f"{K.tr(kv.txt_iso)} {biboecf.OECF.TextoISO(exp.iso)}"))
            self.Poner(self.val_exp, _str_exp)                   # type: ignore

        # --- Con RAW, ya se puede preparar
        self.ActivarCarpeta()

    #
    # --- Caja --- Serie
    #

    # --- Se crea nueva en cada análisis, encima de la cámara: resumen,
    #     barra de progreso, rejilla y botón de incidencias. Lee la serie
    #     una imagen cada vez (la exposición de la primera ya se tiene),
    #     para que la ventana no se congele y vaya mostrando el progreso
    def caja_serie(self, OECF: biboecf.OECF) -> None:
        kv = self.KV
        raws = OECF.raws

        # --- Abre (o trae delante) la ventana con todas las incidencias
        def _ver_incidencias() -> None:
            if not self.incidencias_abiertas():
                ventana = ctk.CTkToplevel(self)
                ventana.geometry(kv.tamano_incidencias)
                ventana.transient(self)
                self.texto_incidencias = ctk.CTkTextbox(ventana, wrap="word")
                self.texto_incidencias.pack(fill="both", expand=True,
                                            padx=kv.margen, pady=kv.margen)
                self.ventana_incidencias = ventana
            self.rellenar_incidencias()
            self.ventana_incidencias.lift()                     # type: ignore

        # --- Lee la siguiente toma (la lee OECF) y se vuelve a programar.
        #     Antes de leer se pinta el progreso: la lectura bloquea la
        #     ventana un momento
        def _leer_toma() -> None:
            self.tarea = None
            if self.OECF.esRead:                                # type: ignore
                _fin_serie()
                return

            leidas = len(self.OECF.tomas)                       # type: ignore
            self.Poner(val_serie, kv.txt_leyendo,
                       n=leidas + 1, total=len(raws))
            self.update_idletasks()

            next(self.lectura)                                  # type: ignore
            barra.set(len(self.OECF.tomas) / len(raws))         # type: ignore

            # --- after (y no un bucle): entre imagen e imagen, la ventana
            #     atiende al ratón y se repinta
            self.tarea = self.after(kv.pausa_lectura, _leer_toma)

        # --- Calcula la zona de cada imagen y muestra el resumen.
        #     PROVISIONAL: la referencia es la primera imagen leída (sin
        #     tapadas todavía)
        def _fin_serie() -> None:
            self.leyendo = False
            self.ActivarCarpeta()
            barra.pack_forget()

            # --- La serie, leída y repartida por OECF: el tercioEV de
            #     cada archivo, en su orden (None si no se leyó)
            serie: biboecf.OECF = self.OECF                     # type: ignore
            leidas = [t for t in serie.tercioEVs if t is not None]
            if not leidas:
                self.Poner(val_serie, kv.txt_no_read)
                self.Ajustar()
                return

            # --- Rango «de … a …»: solo las tomas que van a la rejilla
            #     (sin tapadas, balances de cámara ni Z-V iniciales de más)
            en_rejilla = [t for t, va in zip(serie.tercioEVs, serie.enRejilla)
                          if va and t is not None]

            desde = biboecf.texto_zona(min(en_rejilla))
            hasta = biboecf.texto_zona(max(en_rejilla))
            sin_leer = len(raws) - len(leidas)

            # --- Resumen en dos trozos (el segundo, solo si falta
            #     alguna): se rehace entero al cambiar de idioma
            def _resumen() -> str:
                texto = K.tr_n(kv.txt_resumen, len(raws)).format(
                    total=len(raws), desde=desde, hasta=hasta)
                if sin_leer:
                    texto += K.tr(kv.txt_sin_leer).format(n=sin_leer)
                return texto

            self.Poner(val_serie, _resumen)
            _mostrar_rejilla()
            self.Ajustar()

            # --- Copias de las tomas que sirven, en la carpeta OECF de la
            #     serie, y allí los datos de la preparación, en un JSON
            destino = serie.Copiar()
            if destino is not None:
                grabar_json(serie)

                # --- Las incidencias, como en su ventana (o que no hay)
                incidencias = (self.incidencias()
                               or [K.tr(kv.txt_sin_incidencias)])
                try:
                    (destino / kv.archivo_incidencias).write_text(
                        kv.sep_incidencias.join(incidencias)
                        + kv.sep_incidencias, encoding="utf-8")
                except OSError:
                    pass
            self.ActivarCarpeta()

        # --- Rejilla de zonas y tercios y su pie: el resumen, el botón
        #     de incidencias, que dice cuántas hay y las muestra todas (sin
        #     ninguna, queda inactivo y lo dice), y Analizar, activo solo
        #     si la serie sirve
        def _mostrar_rejilla() -> None:
            serie: biboecf.OECF = self.OECF                     # type: ignore
            rejilla.mostrar(serie)
            self.Poner(val_rejilla, lambda: "\n".join((
                Rejilla.resumen(serie),
                kv.sep_resumen.join((
                    Rejilla.linea_balance(serie.balancePersonalizado),
                    Rejilla.linea_balances(len(serie.WBs)))),
                Rejilla.linea_tapadas(len(serie.tapadas)))))
            rejilla.pack(fill="x", pady=(kv.margen, 0))
            rejilla.dibujar()

            self.incidencias = lambda: Rejilla.incidencias(serie)
            n = len(self.incidencias())
            if n:
                self.Poner(boton_incidencias, kv.txt_incidencias, n=n)
            else:
                self.Poner(boton_incidencias, kv.txt_sin_incidencias)
            boton_incidencias.configure(state="normal" if n else "disabled")
            boton_analizar.configure(state="normal" if serie.esAnalizable
                                     else "disabled")

        # --- La caja. La rejilla y el resumen se muestran al terminar
        interior = self.CrearCaja(kv.txt_fase_serie, self.ReiniciarSerie)
        val_serie = ctk.CTkLabel(interior, text="")
        val_serie.pack()
        barra = ctk.CTkProgressBar(interior)
        rejilla = self.rejilla = Rejilla(interior)
        # --- Pie de la rejilla: Incidencias bajo la Z0, el resumen y
        #     Analizar bajo la ZX. Son hijos de la rejilla, que los coloca.
        #     PENDIENTE: lo que hace Analizar
        val_rejilla = ctk.CTkLabel(rejilla, text="")
        boton_incidencias = ctk.CTkButton(rejilla, command=_ver_incidencias)
        boton_analizar = ctk.CTkButton(rejilla, state="disabled")
        self.ApuntarTexto(boton_analizar, kv.txt_analizar)
        rejilla.poner_pie(boton_incidencias, val_rejilla, boton_analizar)
        self.Traducir()

        # --- A leer: Preparar queda inactivo hasta el final
        self.leyendo = True
        self.ActivarCarpeta()
        self.lectura = OECF.Leer()
        barra.set(len(OECF.tomas) / len(raws))
        barra.pack(fill="x", pady=(kv.margen, 0))
        self.Ajustar()
        _leer_toma()

    # --- ¿Está abierta la ventana de incidencias?
    def incidencias_abiertas(self) -> bool:
        return (self.ventana_incidencias is not None
                and bool(self.ventana_incidencias.winfo_exists()))

    # --- Pone las incidencias en su ventana, en el idioma activo. Solo
    #     lectura: se desbloquea un momento para escribir
    def rellenar_incidencias(self) -> None:
        if not self.incidencias_abiertas():
            return

        texto = self.texto_incidencias
        self.ventana_incidencias.title(                         # type: ignore
            K.tr(self.KV.txt_titulo_incidencias))
        texto.configure(state="normal")                         # type: ignore
        texto.delete("1.0", "end")                              # type: ignore
        texto.insert("1.0", self.KV.sep_incidencias.join(       # type: ignore
            self.incidencias()))
        texto.configure(state="disabled")                       # type: ignore

    #
    # --- Elementos de servicio general
    #
    # region Elementos de servicio general

    #
    def __init__(self) -> None:
        super().__init__()

        #
        # --- Variables de instancia: TODAS aquí, con su tipo, antes de
        #     cualquier lógica. Las que no llevan valor lo toman después:
        #     las de las cajas fijas y los iconos, al crearse; las de las
        #     cajas Cámara y Serie, en ReiniciarCam y ReiniciarSerie (al
        #     arrancar y cada vez que se quitan esas cajas)
        #
        # region Variables de instancia

        # --- Cajas (su fila y cómo reiniciar sus atributos), en el orden
        #     en que se crean: de abajo arriba. Las de encima de una caja
        #     se quitan con QuitarCajas, sean las que sean
        self.cajas: list[tuple[ctk.CTkFrame, Callable[[], None] | None]] = []

        # --- Cuerpo: el marco que contiene todas las cajas
        self.cuerpo: ctk.CTkFrame

        # --- Elementos con texto traducible: cada uno guarda cómo se
        #     compone su texto, para rehacerlo al cambiar de idioma
        self._textos: dict[ctk.CTkBaseClass, Callable[[], str]] = {}

        # --- Caja Carpeta (caja_carpeta): los botones Preparar y Abrir
        #     OECF (los activa y desactiva ActivarCarpeta) y la variable
        #     de la casilla
        self.boton_oecf: ctk.CTkButton
        self.boton_preparar: ctk.CTkButton
        self.ruta: ctk.StringVar

        # --- Imágenes de los iconos (SOicon y caja_cabecera): se guardan
        #     para que Python no las borre, o el icono desaparece
        self.icono: tk.PhotoImage
        self.icono_cabecera: tk.PhotoImage

        # --- Caja Cámara (ReiniciarCam): la serie de la carpeta (fase 1),
        #     para Preparar; cuántas cajas hay hasta la de la cámara
        #     (incluida), porque las de encima se quitan en cada análisis;
        #     y las etiquetas de sus valores
        self.OECF: biboecf.OECF | None
        self.propias_cam: int
        self.val_archivo: ctk.CTkLabel | None
        self.val_exp: ctk.CTkLabel | None
        self.val_fecha: ctk.CTkLabel | None
        self.val_modelo: ctk.CTkLabel | None

        # --- Caja Serie (ReiniciarSerie), lo que se usa desde fuera de
        #     ella: cómo se componen las incidencias, la lectura en marcha
        #     de la serie (OECF.Leer), si se está leyendo,
        #     la rejilla (se redibuja al traducir), la siguiente lectura
        #     pendiente y la ventana de incidencias con su texto
        self.incidencias: Callable[[], list[str]]
        self.lectura: Iterator[int] | None
        self.leyendo: bool
        self.rejilla: Rejilla | None
        self.tarea: str | None
        self.texto_incidencias: ctk.CTkTextbox | None
        self.ventana_incidencias: ctk.CTkToplevel | None

        # endregion Variables de instancia

        # --- Valores iniciales de las cajas Cámara y Serie
        self.ReiniciarCam()
        self.ReiniciarSerie()

        # --- Cuerpo: pone el margen de arriba y el de los lados; cada fila
        #     pone el suyo por debajo
        self.cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        self.cuerpo.pack(fill="both", expand=True, padx=self.KV.margen,
                         pady=(self.KV.margen, 0))

        # --- Cabecera, fija arriba del todo; las demás filas, de abajo
        #     hacia arriba, por debajo de ella
        self.caja_cabecera()
        self.caja_ayuda()
        self.caja_carpeta()

        # --- Textos en el idioma activo; tamaño justo para el contenido,
        #     centrada en horizontal y arriba en la pantalla
        self.Traducir()
        self.Centrar()
        self.SOicon()

    # --- Valores iniciales de las variables de la caja Cámara (se
    #     declaran en el __init__): al arrancar y al quitar la caja
    def ReiniciarCam(self) -> None:
        self.OECF = None
        self.propias_cam = 0
        self.val_archivo = None
        self.val_exp = None
        self.val_fecha = None
        self.val_modelo = None

    # --- Valores iniciales de las variables de la caja Serie (se
    #     declaran en el __init__): al arrancar y al quitar la caja
    def ReiniciarSerie(self) -> None:
        self.incidencias = list
        self.lectura = None
        self.leyendo = False
        self.rejilla = None
        self.tarea = None
        self.texto_incidencias = None
        self.ventana_incidencias = None

    # --- Quita las cajas desde la posición «desde» (las de encima) y lo
    #     que depende de ellas: la lectura en marcha, la ventana de
    #     incidencias, sus textos traducibles y sus atributos
    def QuitarCajas(self, desde: int) -> None:
        if len(self.cajas) <= desde:
            return

        if self.tarea is not None:
            self.after_cancel(self.tarea)
        if self.incidencias_abiertas():
            self.ventana_incidencias.destroy()                  # type: ignore
        for fila, reiniciar in self.cajas[desde:]:
            fila.destroy()
            if reiniciar is not None:
                reiniciar()
        del self.cajas[desde:]
        self._textos = {elemento: componer for elemento, componer
                        in self._textos.items() if elemento.winfo_exists()}

        self.ActivarCarpeta()
        self.Ajustar()

    # --- Icono de la ventana. En Windows, el .ico del programa con
    #     iconbitmap(): así customtkinter no pone el suyo a los 200 ms. En
    #     los demás, según el tema: negro en el claro y blanco en el
    #     oscuro (se guarda la imagen: si no, Python la borra y el icono
    #     desaparece). Si falta el archivo, la ventana sigue sin él
    def SOicon(self) -> None:
        carpeta = K.path / K.carpeta_recursos
        try:
            if sys.platform.startswith(self.KV.plataforma_windows):
                self.iconbitmap(str(carpeta / K.icono_ico))
                return

            oscuro = ctk.get_appearance_mode() == "Dark"
            nombre = K.icono_tema_oscuro if oscuro else K.icono_tema_claro
            self.icono = tk.PhotoImage(file=carpeta / nombre)
            self.iconphoto(True, self.icono)
        except tk.TclError:
            pass

    # --- Cierra la ventana. Sustituye al destroy() de Tk: el nombre es
    #     OBLIGATORIO (no sigue las normas de nombres) porque lo llaman Tk
    #     al pulsar la X de la ventana y el botón Salir. Antes de cerrar
    #     se cancela la lectura pendiente de la serie (self.tarea): si no,
    #     Tk avisa de un error al intentar seguir con una ventana que ya
    #     no existe. super().destroy() es el de Tk, el que cierra de verdad
    def destroy(self) -> None:
        if self.tarea is not None:
            self.after_cancel(self.tarea)
        super().destroy()

    # endregion Elementos de servicio general

    #
    # --- Posicionamiento y tamaño de la ventana
    #
    # region Posicionamiento y tamaño de la ventana

    # --- Ajusta la ventana al contenido (llamar tras añadir filas)
    def Ajustar(self) -> None:

        # --- Tamaño que pide el contenido, ya calculado
        self.update_idletasks()
        ancho, alto = self.winfo_reqwidth(), self.winfo_reqheight()

        # --- Se pide con números concretos: con Tk bajo XWayland (GNOME en
        #     Wayland), el gestor de ventanas a veces se salta el «tamaño
        #     natural» (geometry("")) y la ventana queda cortada o sin
        #     repintar. Después se vuelve al tamaño natural, para que siga
        #     creciendo sola. customtkinter no admite geometry(""): ambas
        #     se piden a tkinter
        tk.Tk.geometry(self, f"{ancho}x{alto}")
        self.update_idletasks()
        tk.Tk.geometry(self, "")
        self.update_idletasks()

        # --- Repintado forzado, un momento después: se pide a cada
        #     elemento de la ventana que se vuelva a dibujar. Bajo
        #     XWayland, a veces se pierde el aviso de redibujar lo que se
        #     mueve a la zona nueva de la ventana (Tk sí lo tiene
        #     colocado) y queda en blanco hasta que se cambia el tamaño a
        #     mano
        #     La zona a redibujar es el elemento entero: sin ella, mide
        #     0 × 0, y los lienzos (botones y marcos de customtkinter) solo
        #     repintan esa zona, es decir, nada
        def _repintar() -> None:
            pendientes: list[tk.Misc] = [self]
            while pendientes:
                elemento = pendientes.pop()
                elemento.event_generate(
                    self.KV.tk_redibujar, x=0, y=0,
                    width=elemento.winfo_width(),
                    height=elemento.winfo_height())
                pendientes.extend(elemento.winfo_children())

        for espera in self.KV.esperas_repintado:
            self.after(espera, _repintar)

    # --- Coloca la ventana centrada en horizontal y arriba del monitor
    #     principal: al añadir filas crece hacia abajo sin salirse
    def Centrar(self) -> None:

        # --- Posición y ancho del monitor principal (Tk ve todos los
        #     monitores como una sola pantalla). Si no se pueden leer los
        #     monitores, toda la pantalla de Tk
        try:
            monitores = screeninfo.get_monitors()
        except screeninfo.ScreenInfoError:
            monitores = []
        if monitores:
            principal = next((m for m in monitores if m.is_primary),
                             monitores[0])
            x, y, ancho = principal.x, principal.y, principal.width
        else:
            x, y, ancho = 0, 0, self.winfo_screenwidth()

        # --- Centrada en horizontal y arriba de ese monitor
        x += (ancho - self.winfo_width()) // 2
        y += self.KV.arriba
        self.geometry(f"+{x}+{y}")

    # --- Crea una caja con marco encima de las filas que ya hay (una por
    #     fase) y devuelve su interior, donde van los elementos. El título
    #     es opcional y va montado a mitad de la línea de arriba. reiniciar:
    #     cómo dejar sus atributos al quitarla (si tiene). fija: arriba del
    #     todo, por encima de las que vengan después (la cabecera). marco:
    #     si se dibuja (la cabecera y la de Ayuda van sin él)
    def CrearCaja(self, titulo: dict | None = None,
                  reiniciar: Callable[[], None] | None = None,
                  fija: bool = False, marco: bool = True) -> ctk.CTkFrame:

        # --- La fila, vacía, encima de las que ya hay (o arriba del todo)
        fila = ctk.CTkFrame(self.cuerpo, fg_color="transparent")
        fila.pack(side="top" if fija else "bottom", fill="x",
                  pady=(0, self.KV.margen))
        self.cajas.append((fila, reiniciar))

        # --- Caja solo con marco: transparente, para que el fondo del
        #     título tape la línea sin que se note
        caja = ctk.CTkFrame(fila, fg_color="transparent",
                            border_width=self.KV.grosor_marco if marco else 0)

        # --- Con título, la caja baja media altura del título y este se
        #     coloca encima (lift), centrado en la línea
        arriba = 0
        hueco = self.KV.margen
        if titulo:
            etiqueta = self.ApuntarTexto(
                ctk.CTkLabel(fila, padx=self.KV.relleno_titulo), titulo)
            arriba = etiqueta.winfo_reqheight() // 2
            etiqueta.place(x=self.KV.margen, y=arriba, anchor="w")
            etiqueta.lift()
            hueco = arriba + self.KV.separador_superior
        caja.pack(fill="x", pady=(arriba, 0))

        # --- Dentro, el margen separa el contenido del marco. Arriba, con
        #     título, el hueco es la media altura del título que queda
        #     dentro de la caja más el separador_superior
        interior = ctk.CTkFrame(caja, fg_color="transparent")
        interior.pack(fill="x", padx=self.KV.margen,
                      pady=(hueco, self.KV.margen))
        return interior

    # --- Se calcula cada vez a partir de la casilla (self.ruta), así que
    #     siempre está al día
    @property
    def carpetaEscrita(self) -> Path:
        """ Saber la carpeta escrita en la casilla, como ruta: así «/a/b» y
            «/a/b/» son la misma, y «~» es la carpeta del usuario. """
        return Path(self.ruta.get().strip()).expanduser()

    # --- Preparar: lanza la serie de la carpeta elegida, quitando antes
    #     la del análisis anterior
    def Preparar(self) -> None:
        self.QuitarCajas(self.propias_cam)
        self.caja_serie(self.OECF)                              # type: ignore

    # --- Botones de la caja Carpeta, sin estar leyendo una serie:
    #     Preparar, activo si la carpeta tiene RAW; Abrir OECF, solo si
    #     ya se prepararon las copias de esta carpeta
    def ActivarCarpeta(self) -> None:
        libre = self.OECF is not None and not self.leyendo
        preparar = libre and bool(self.OECF.raws)               # type: ignore
        oecf = libre and bool(self.OECF.copias)                 # type: ignore
        self.boton_preparar.configure(
            state="normal" if preparar else "disabled")
        self.boton_oecf.configure(state="normal" if oecf else "disabled")

    # --- Abre la carpeta OECF de la serie en el explorador de archivos
    #     del sistema
    def AbrirOECF(self) -> None:
        if self.OECF is None:
            return
        carpeta = self.OECF.carpeta
        if sys.platform.startswith(self.KV.plataforma_windows):
            os.startfile(carpeta)                               # type: ignore
        elif sys.platform == self.KV.plataforma_mac:
            subprocess.Popen([self.KV.abrir_mac, carpeta])
        else:
            subprocess.Popen([self.KV.abrir_linux, carpeta])

    # endregion Posicionamiento y tamaño de la ventana

    #
    # --- Gestión del idioma
    #
    # region Gestión del idioma

    # --- Apunta un elemento para traducirlo y lo devuelve
    #     Los {campos} del texto se rellenan con datos
    def ApuntarTexto(self, elemento: ctk.CTkBaseClass, texto: dict,
                     **datos: object) -> ctk.CTkBaseClass:
        self._textos[elemento] = lambda: K.tr(texto).format(**datos)
        return elemento

    # --- Pone un texto en un elemento. Puede ser:
    #       str      fijo (un nombre de archivo): no se traduce
    #       dict     {idioma: texto}, con sus {campos} en datos
    #       función  que compone el texto en el idioma activo
    def Poner(self, elemento: ctk.CTkBaseClass,
              texto: str | dict | Callable[[], str], **datos: object) -> None:
        if isinstance(texto, str):
            self._textos.pop(elemento, None)
            elemento.configure(text=texto)
            return

        if isinstance(texto, dict):
            self.ApuntarTexto(elemento, texto, **datos)

        else:
            self._textos[elemento] = texto

        elemento.configure(text=self._textos[elemento]())

    # --- Pone el título y los textos en el idioma activo
    def Traducir(self) -> None:
        self.title(f"{K.nombre} - {K.tr(self.KV.txt_version)} {K.version}")
        for elemento, componer in self._textos.items():
            elemento.configure(text=componer())

        # --- La rejilla dibuja sus textos («falta»…) en el Canvas
        if self.rejilla is not None:
            self.rejilla.dibujar()
        self.rellenar_incidencias()
        self.Ajustar()

    # --- Cambia el idioma activo al elegido en la lista
    def CambiarIdioma(self, nombre: str) -> None:
        for codigo, nombre_idioma in K.idiomas.items():
            if nombre_idioma == nombre:
                K.idioma = codigo
        self.Traducir()

    # endregion Gestión del idioma
