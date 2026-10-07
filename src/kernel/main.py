# -*- coding: utf-8 *-*
"""
    :Propósito: Kernel PyOECF.
    :Autor:     Tony Diana
    :Versión:   26.10.06
"""

# cSpell:ignore biboecf, boton, codigo, customtkinter, initialdir, meipass
# cSpell:ignore padx, pady, screeninfo, tamano, textvariable, winfo
# cSpell:ignore choosedir, exps, leidas, mclocale, mcset, msgcat, redibuja

# --- Valenciano
# cSpell:ignore accedir, acord, Ajuda, Analitzar, Càmera, carpetes, denegat
# cSpell:ignore Eixir, existeix, fitxer, imatge, imatges, Incidències
# cSpell:ignore Llegint, llegir, Mostra, nincidències, Permís, pogut
# cSpell:ignore Selecció, Seleccioneu, Sèrie, sèrie, Trieu, vàlid, Versió

__all__ = ["Ventana"]

# --- Bibliotecas estándar Python
import tkinter as tk
import webbrowser
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog

# --- Bibliotecas externas
import customtkinter as ctk
import screeninfo

# --- Bibliotecas internas
from bib import biboecf, std
from .constantes import K
from .temporal import Rejilla, grabar_json


#
class Ventana(ctk.CTk):
    """ Ventana principal de PyOECF. """

    # --- Constantes de la ventana (las de toda la app están en K)
    class KV(std.EnumMutable):
        """ Constantes de la ventana principal. """

        # --- Textos {idioma: texto}
        txt_version = {K.es: "Versión", K.en: "Version",
                       K.ca: "Versió"}
        txt_carpeta = {K.es: "Seleccione carpeta", K.en: "Select folder",
                       K.ca: "Seleccioneu carpeta"}
        txt_analizar = {K.es: "Analizar", K.en: "Analyze",
                        K.ca: "Analitzar"}
        txt_fase_carpeta = {K.es: "Carpeta", K.en: "Folder",
                            K.ca: "Carpeta"}
        txt_fase_cam = {K.es: "Cámara", K.en: "Camera",
                        K.ca: "Càmera"}
        txt_archivo = {K.es: "Primera imagen", K.en: "First image",
                       K.ca: "Primera imatge"}
        txt_marca = {K.es: "Marca", K.en: "Brand",
                     K.ca: "Marca"}
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

        # --- Incidencias de la rejilla: botón en su hueco de ZX 2/3, con
        #     cuántas hay, y su propia ventana (ancho × alto, en píxeles)
        txt_incidencias = {K.es: "Incidencias\n{n}", K.en: "Issues\n{n}",
                           K.ca: "Incidències\n{n}"}
        txt_sin_incidencias = {K.es: "Sin\nincidencias", K.en: "No\nissues",
                               K.ca: "Sense\nincidències"}
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
        txt_ayuda = {K.es: "Ayuda", K.en: "Help",
                     K.ca: "Ajuda"}
        txt_idioma = {K.es: "Idioma", K.en: "Language",
                      K.ca: "Idioma"}
        txt_salir = {K.es: "Salir", K.en: "Exit",
                     K.ca: "Eixir"}

        # --- Medidas (píxeles)
        margen = 10
        borde_caja = 2

        # --- Datos en una línea: hueco entre un dato y el siguiente
        sep_datos = 30

        # --- A cada lado del título de una caja, entre su texto y la línea
        relleno_titulo = 12

        # --- Dentro de una caja con título: entre el título y el contenido
        separador_superior = 0
        ancho_carpeta = 650

        # --- Milisegundos tras abrir la ventana para volver a poner el
        #     icono: en Windows, customtkinter pone el suyo a los 200 ms
        retraso_icono = 300

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

    #
    # --- Caja --- | Ayuda | Idioma | Salir |
    #

    def caja_ayuda(self) -> None:
        kv = self.KV
        fila = self.nueva_caja()

        # --- Los extremos primero, para que Idioma ocupe el centro
        self.traducible(ctk.CTkButton(fila, command=self.ayuda),
                        kv.txt_ayuda).pack(side="left")
        self.traducible(ctk.CTkButton(fila, command=self.destroy),
                        kv.txt_salir).pack(side="right")

        # --- Idioma: grupo centrado en el hueco entre Ayuda y Salir. Al
        #     elegir otro en la lista, cambia toda la ventana
        grupo = ctk.CTkFrame(fila, fg_color="transparent")
        grupo.pack(side="left", expand=True)

        self.traducible(ctk.CTkLabel(grupo), kv.txt_idioma).pack(
            side="left")

        lista = ctk.CTkComboBox(
            grupo, values=list(K.idiomas.values()), state="readonly",
            command=self.cambiar_idioma)

        lista.set(K.idiomas[K.idioma])
        lista.pack(side="left", padx=(kv.margen, 0))

    #
    # --- Caja --- Carpeta
    #

    def caja_carpeta(self) -> None:
        kv = self.KV

        # --- Diálogo de carpetas: estas dos preparaciones solo afectan al
        #     de Tk de Linux; Windows y macOS usan el suyo propio
        #
        # --- Sin carpetas ocultas (las que empiezan por punto), pero con
        #     la casilla para verlas
        def sin_ocultos() -> None:
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
        def en_su_idioma() -> None:
            try:
                for original, textos in kv.tcl_faltan.items():
                    for idioma, traducido in textos.items():
                        self.tk.call(*kv.tcl_espacio, (kv.tcl_traducir, idioma,
                                                       original, traducido))
                self.tk.call(kv.tcl_idioma, K.idioma)
                if int(self.tk.call("winfo", "exists", kv.tcl_dialogo)):
                    self.tk.call("destroy", kv.tcl_dialogo)
            except tk.TclError:
                pass

        # --- Pide la carpeta y la escribe en la casilla. El diálogo
        #     empieza en la carpeta de la casilla, si existe; si no, en la
        #     del usuario (no en la de la app)
        def elegir() -> None:
            sin_ocultos()
            en_su_idioma()
            escrita = self.ruta.get().strip()
            inicio = Path(escrita) if escrita else Path.home()
            if not inicio.is_dir():
                inicio = Path.home()

            ruta = filedialog.askdirectory(parent=self, initialdir=inicio)
            if ruta:
                self.ruta.set(ruta)

        # --- Otra carpeta: se quitan las cajas de encima de esta, sean
        #     las que sean. Los argumentos los pone trace_add y no se usan
        def otra_carpeta(*_) -> None:
            if self.carpeta_escrita() != self.analizada:
                self.quitar_cajas(propias)

        # --- La caja: botón · ruta elegida · Analizar. Las cajas que haya
        #     hasta esta (incluida) son las propias; el resto, de encima
        fila = self.nueva_caja(kv.txt_fase_carpeta)
        propias = len(self.cajas)
        self.traducible(ctk.CTkButton(fila, command=elegir),
                        kv.txt_carpeta).pack(side="left")

        # --- Analizar antes que la casilla, para que esta ocupe el hueco.
        #     Empieza inactivo: aún no hay ruta
        self.boton_analizar = self.traducible(
            ctk.CTkButton(fila, command=self.caja_cam, state="disabled"),
            kv.txt_analizar)
        self.boton_analizar.pack(side="right", padx=(kv.margen, 0))

        # --- Cada cambio en la ruta (elegida o tecleada) activa o
        #     desactiva Analizar
        self.ruta = ctk.StringVar()
        self.ruta.trace_add("write", self.activar_analizar)
        self.ruta.trace_add("write", otra_carpeta)
        carpeta = ctk.CTkEntry(fila, width=kv.ancho_carpeta,
                               textvariable=self.ruta)
        carpeta.pack(side="left", fill="x", expand=True, padx=(kv.margen, 0))

    #
    # --- Caja --- Cámara
    #

    def caja_cam(self) -> None:
        kv = self.KV

        # --- La caja se construye la primera vez que se pulsa Analizar,
        #     encima de la carpeta: todos los datos en una línea
        def construir_caja() -> None:

            # --- Añade «nombre valor» a la derecha de los que ya hay y
            #     devuelve la etiqueta del valor, para rellenarla. El
            #     primero va pegado al borde; los demás, separados
            def nuevo_dato(nombre: dict) -> ctk.CTkLabel:
                hueco = kv.sep_datos if grupo.winfo_children() else 0
                self.traducible(ctk.CTkLabel(grupo), nombre).pack(
                    side="left", padx=(hueco, 0))
                valor = ctk.CTkLabel(grupo, text="")
                valor.pack(side="left", padx=(kv.margen, 0))
                return valor

            # --- Los datos van en un grupo que no se estira: así queda
            #     centrado en la caja
            interior = self.nueva_caja(kv.txt_fase_cam, self.reiniciar_cam)
            self.propias_cam = len(self.cajas)
            grupo = ctk.CTkFrame(interior, fg_color="transparent")
            grupo.pack()

            self.val_archivo = nuevo_dato(kv.txt_archivo)
            self.val_marca = nuevo_dato(kv.txt_marca)
            self.val_modelo = nuevo_dato(kv.txt_modelo)
            self.val_f = nuevo_dato(kv.txt_f)
            self.val_exp = nuevo_dato(kv.txt_exp)
            self.val_iso = nuevo_dato(kv.txt_iso)

            # --- Pone los textos nuevos y hace crecer la ventana
            self.traducir()

        if self.val_archivo is None:
            construir_caja()
        self.analizada = self.carpeta_escrita()

        # --- Se vacían los datos de la vez anterior y se quitan las cajas
        #     de encima (la serie): si esta carpeta falla, no deben quedar
        #     a la vista
        for valor in (self.val_marca, self.val_modelo, self.val_exp,
                      self.val_f, self.val_iso):
            self.poner(valor, "")                               # type: ignore
        self.quitar_cajas(self.propias_cam)

        carpeta = self.analizada
        if not carpeta.is_dir():
            self.poner(self.val_archivo, kv.txt_sin_carpeta)    # type: ignore
            return

        raws = biboecf.buscar_raw(carpeta)
        if not raws:
            self.poner(self.val_archivo, kv.txt_sin_raw)        # type: ignore
            return

        archivo = raws[0]
        self.poner(self.val_archivo, archivo.name)              # type: ignore

        # --- Marca y modelo tal como vienen en el archivo
        cam = biboecf.leer_cam(archivo)
        if cam is None:
            self.poner(self.val_modelo, kv.txt_no_read)         # type: ignore
        else:
            marca, modelo = cam
            self.poner(self.val_marca, marca)                   # type: ignore
            self.poner(self.val_modelo, modelo)                 # type: ignore

        # --- Tv, f e ISO salen juntos: si no se leen, se avisa en Tv
        exp = biboecf.leer_exp(archivo)
        if exp is None:
            self.poner(self.val_exp, kv.txt_no_read)            # type: ignore
        else:
            segundos, diafragma, iso = exp
            tv = biboecf.texto_exp(segundos)
            self.poner(self.val_exp, tv)                        # type: ignore
            self.poner(self.val_f, biboecf.texto_f(diafragma))  # type: ignore
            self.poner(self.val_iso, biboecf.texto_iso(iso))    # type: ignore

        # --- El resto de la serie; la primera ya está leída
        self.caja_serie(raws, exp)

    #
    # --- Caja --- Serie
    #

    # --- Se crea nueva en cada análisis, encima de la cámara: resumen,
    #     barra de progreso, rejilla y botón de incidencias. Lee la serie
    #     una imagen cada vez (la exposición de la primera ya se tiene),
    #     para que la ventana no se congele y vaya mostrando el progreso
    def caja_serie(self, raws: list[Path],
                   exp_primera: tuple[float, float, float] | None) -> None:
        kv = self.KV

        # --- Exposición de cada imagen (None si no se pudo leer)
        exps = [exp_primera]

        # --- Abre (o trae delante) la ventana con todas las incidencias
        def ver_incidencias() -> None:
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

        # --- Lee la siguiente imagen y se vuelve a programar. Antes de
        #     leer se pinta el progreso: la lectura bloquea la ventana un
        #     momento
        def leer_toma() -> None:
            self.tarea = None
            if len(exps) == len(raws):
                fin_serie()
                return

            self.poner(val_serie, kv.txt_leyendo,
                       n=len(exps) + 1, total=len(raws))
            self.update_idletasks()

            exps.append(biboecf.leer_exp(raws[len(exps)]))
            barra.set(len(exps) / len(raws))

            # --- after (y no un bucle): entre imagen e imagen, la ventana
            #     atiende al ratón y se repinta
            self.tarea = self.after(kv.pausa_lectura, leer_toma)

        # --- Calcula la zona de cada imagen y muestra el resumen.
        #     PROVISIONAL: la referencia es la primera imagen leída (sin
        #     tapadas todavía)
        def fin_serie() -> None:
            self.leyendo = False
            self.activar_analizar()
            barra.pack_forget()

            relativas = [biboecf.exp_relativa(*e) if e else None
                         for e in exps]
            leidas = [e for e in relativas if e is not None]
            if not leidas:
                self.poner(val_serie, kv.txt_no_read)
                self.ajustar()
                return

            # --- k de cada archivo, en su orden (None si no se leyó)
            ks_todas = [None if e is None else
                        biboecf.calcular_k(e, leidas[0]) for e in relativas]

            # --- Partes de la secuencia. Las tapadas y los balances de
            #     cámara no van a la rejilla ni al rango «de … a …»
            tapadas = [e is not None and biboecf.es_tapada(raw, e[0])
                       for raw, e in zip(raws, exps)]
            sec = biboecf.secuencia(ks_todas, tapadas)
            quitar = [tapada or i in sec.balances
                      for i, tapada in enumerate(tapadas)]
            ks = [k for k, q in zip(ks_todas, quitar)
                  if k is not None and not q]
            desde = biboecf.texto_zona(min(ks))
            hasta = biboecf.texto_zona(max(ks))
            sin_leer = len(raws) - len(leidas)

            # --- Resumen en dos trozos (el segundo, solo si falta
            #     alguna): se rehace entero al cambiar de idioma
            def resumen() -> str:
                texto = K.tr_n(kv.txt_resumen, len(raws)).format(
                    total=len(raws), desde=desde, hasta=hasta)
                if sin_leer:
                    texto += K.tr(kv.txt_sin_leer).format(n=sin_leer)
                return texto

            balance = biboecf.balance_personalizado(ks_todas)
            self.poner(val_serie, resumen)
            mostrar_rejilla(ks_todas, balance, tapadas, sec, quitar)
            self.ajustar()

            # --- TEMPORAL: los datos del análisis, en un JSON en la carpeta
            grabar_json(raws[0].parent, raws, exps, ks_todas, balance,
                        tapadas, sec, quitar)

        # --- TEMPORAL: rejilla de zonas y tercios, su resumen debajo
        #     (centrado bajo las celdas de las zonas) y el botón de
        #     incidencias, que dice cuántas hay y las muestra todas. Sin
        #     ninguna, queda inactivo y lo dice
        def mostrar_rejilla(ks: list[int | None], balance: bool | None,
                            tapadas: list[bool], sec: biboecf.Secuencia,
                            quitar: list[bool]) -> None:
            celdas, fuera = Rejilla.repartir(*Rejilla.sin(raws, ks, quitar))
            n_tapadas = sum(tapadas)
            rejilla.mostrar(celdas)
            self.poner(val_rejilla, lambda: "\n".join((
                kv.sep_resumen.join(Rejilla.resumen(celdas)),
                kv.sep_resumen.join((
                    Rejilla.linea_balance(balance),
                    Rejilla.linea_balances(len(sec.balances)))),
                Rejilla.linea_tapadas(n_tapadas))))
            rejilla.pack(fill="x", pady=(kv.margen, 0))
            val_rejilla.pack(padx=(Rejilla.KR.ancho_etiquetas, 0))

            self.incidencias = lambda: Rejilla.incidencias(
                celdas, fuera, balance, n_tapadas, sec, raws)
            n = len(self.incidencias())
            if n:
                self.poner(boton_incidencias, kv.txt_incidencias, n=n)
            else:
                self.poner(boton_incidencias, kv.txt_sin_incidencias)
            boton_incidencias.configure(state="normal" if n else "disabled")

        # --- La caja. La rejilla y el resumen se muestran al terminar
        interior = self.nueva_caja(kv.txt_fase_serie, self.reiniciar_serie)
        val_serie = ctk.CTkLabel(interior, text="")
        val_serie.pack()
        barra = ctk.CTkProgressBar(interior)
        rejilla = self.rejilla = Rejilla(interior)
        val_rejilla = ctk.CTkLabel(interior, text="")

        # --- Botón de incidencias: hijo de la rejilla, que lo coloca en
        #     su hueco de ZX 2/3. Letra de las celdas: dos líneas
        boton_incidencias = ctk.CTkButton(rejilla, command=ver_incidencias,
                                          font=Rejilla.KR.fuente)
        rejilla.poner_boton(boton_incidencias)
        self.traducir()

        # --- A leer: Analizar queda inactivo hasta el final
        self.leyendo = True
        self.activar_analizar()
        barra.set(len(exps) / len(raws))
        barra.pack(fill="x", pady=(kv.margen, 0))
        self.ajustar()
        leer_toma()

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
        texto.insert("1.0", "\n".join(self.incidencias()))      # type: ignore
        texto.configure(state="disabled")                       # type: ignore

    #
    # --- Elementos de servicio general
    #
    # region Elementos de servicio general

    #
    def __init__(self) -> None:
        super().__init__()

        # --- Elementos con texto traducible.
        #     Cada elemento guarda cómo se compone su texto, para
        #     rehacerlo al cambiar de idioma
        self._textos: dict[ctk.CTkBaseClass, Callable[[], str]] = {}

        # --- Cajas (su fila y cómo reiniciar sus atributos), en el orden
        #     en que se crean: de abajo arriba. Las de encima de una caja
        #     se quitan con quitar_cajas, sean las que sean
        self.cajas: list[tuple[ctk.CTkFrame, Callable[[], None] | None]] = []

        # --- Atributos de las cajas que se crean al analizar
        self.reiniciar_cam()
        self.reiniciar_serie()

        # --- Cuerpo: pone el margen de arriba y el de los lados; cada fila
        #     pone el suyo por debajo
        self.cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        self.cuerpo.pack(fill="both", expand=True, padx=self.KV.margen,
                         pady=(self.KV.margen, 0))

        # --- Filas, de abajo hacia arriba
        self.caja_ayuda()
        self.caja_carpeta()

        # --- Textos en el idioma activo; tamaño justo para el contenido,
        #     centrada en horizontal y arriba en la pantalla
        self.traducir()
        self.centrar()
        self.poner_icono()
        self.after(self.KV.retraso_icono, self.poner_icono)

    # --- Atributos de la caja Cámara: no existen hasta que se analiza
    #     una carpeta, y vuelven a no existir al quitar la caja
    def reiniciar_cam(self) -> None:

        # --- Carpeta analizada: si se vuelve a elegir, no se quita nada
        self.analizada: Path | None = None

        # --- Cajas hasta la de la cámara (incluida): las de encima se
        #     quitan en cada análisis
        self.propias_cam = 0

        # --- Valores de la caja
        self.val_archivo: ctk.CTkLabel | None = None
        self.val_marca: ctk.CTkLabel | None = None
        self.val_modelo: ctk.CTkLabel | None = None
        self.val_exp: ctk.CTkLabel | None = None
        self.val_f: ctk.CTkLabel | None = None
        self.val_iso: ctk.CTkLabel | None = None

    # --- Atributos de la caja Serie que se usan desde fuera de ella: la
    #     rejilla (se redibuja al traducir), la lectura (leyendo y la
    #     siguiente pendiente) y la ventana de incidencias y cómo se
    #     componen
    def reiniciar_serie(self) -> None:
        self.rejilla: Rejilla | None = None
        self.leyendo = False
        self.tarea: str | None = None
        self.ventana_incidencias: ctk.CTkToplevel | None = None
        self.texto_incidencias: ctk.CTkTextbox | None = None
        self.incidencias: Callable[[], list[str]] = list

    # --- Quita las cajas desde la posición «desde» (las de encima) y lo
    #     que depende de ellas: la lectura en marcha, la ventana de
    #     incidencias, sus textos traducibles y sus atributos
    def quitar_cajas(self, desde: int) -> None:
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

        self.activar_analizar()
        self.ajustar()

    # --- Icono de la ventana según el tema: negro en el claro y blanco en
    #     el oscuro. Se guarda la imagen: si no, Python la borra y el
    #     icono desaparece. Si falta el archivo, la ventana sigue sin él
    def poner_icono(self) -> None:
        oscuro = ctk.get_appearance_mode() == "Dark"
        nombre = K.icono_tema_oscuro if oscuro else K.icono_tema_claro
        try:
            self.icono = tk.PhotoImage(
                file=K.path / K.carpeta_recursos / nombre)
            self.iconphoto(True, self.icono)
        except tk.TclError:
            pass

    # --- Abre la ayuda en el navegador
    def ayuda(self) -> None:
        webbrowser.open(K.url_help)

    # --- Al cerrar, se cancela la lectura pendiente: si no, Tk avisa de
    #     un error al intentar seguir con una ventana que ya no existe
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
    def ajustar(self) -> None:
        # --- customtkinter no admite geometry(""): se pide a tkinter
        tk.Tk.geometry(self, "")
        self.update_idletasks()

    # --- Coloca la ventana centrada en horizontal y arriba del monitor
    #     principal: al añadir filas crece hacia abajo sin salirse
    def centrar(self) -> None:
        x, y, ancho, _ = self.monitor_principal()
        x += (ancho - self.winfo_width()) // 2
        y += self.KV.arriba
        self.geometry(f"+{x}+{y}")

    # --- Posición y tamaño del monitor principal: (x, y, ancho, alto).
    #     Si no se pueden leer los monitores, toda la pantalla de Tk
    def monitor_principal(self) -> tuple[int, int, int, int]:
        try:
            monitores = screeninfo.get_monitors()
        except screeninfo.ScreenInfoError:
            monitores = []
        if not monitores:
            return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

        principal = next((m for m in monitores if m.is_primary), monitores[0])
        return principal.x, principal.y, principal.width, principal.height

    # --- Crea una fila vacía encima de las que ya hay
    def nueva_fila(self) -> ctk.CTkFrame:
        fila = ctk.CTkFrame(self.cuerpo, fg_color="transparent")
        fila.pack(side="bottom", fill="x", pady=(0, self.KV.margen))
        return fila

    # --- Crea una caja con borde encima de las filas que ya hay (una por
    #     fase) y devuelve su interior, donde van los elementos. El título
    #     es opcional y va montado a mitad de la línea de arriba. reiniciar:
    #     cómo dejar sus atributos al quitarla (si tiene)
    def nueva_caja(self, titulo: dict | None = None,
                   reiniciar: Callable[[], None] | None = None
                   ) -> ctk.CTkFrame:
        fila = self.nueva_fila()
        self.cajas.append((fila, reiniciar))

        # --- Caja solo con borde: transparente, para que el fondo del
        #     título tape la línea sin que se note
        caja = ctk.CTkFrame(fila, fg_color="transparent",
                            border_width=self.KV.borde_caja)

        # --- Con título, la caja baja media altura del título y este se
        #     coloca encima (lift), centrado en la línea
        arriba = 0
        hueco = self.KV.margen
        if titulo:
            etiqueta = self.traducible(
                ctk.CTkLabel(fila, padx=self.KV.relleno_titulo), titulo)
            arriba = etiqueta.winfo_reqheight() // 2
            etiqueta.place(x=self.KV.margen, y=arriba, anchor="w")
            etiqueta.lift()
            hueco = arriba + self.KV.separador_superior
        caja.pack(fill="x", pady=(arriba, 0))

        # --- Dentro, el margen separa el contenido del borde. Arriba, con
        #     título, el hueco es la media altura del título que queda
        #     dentro de la caja más el separador_superior
        interior = ctk.CTkFrame(caja, fg_color="transparent")
        interior.pack(fill="x", padx=self.KV.margen,
                      pady=(hueco, self.KV.margen))
        return interior

    # --- Carpeta escrita en la casilla, como ruta: así «/a/b» y «/a/b/»
    #     son la misma. «~» es la carpeta del usuario, también a mano
    def carpeta_escrita(self) -> Path:
        return Path(self.ruta.get().strip()).expanduser()

    # --- Analizar solo está activo cuando hay ruta y no se está leyendo
    #     una serie. Los argumentos los pone trace_add y no se usan
    def activar_analizar(self, *_) -> None:
        activo = self.ruta.get().strip() and not self.leyendo
        estado = "normal" if activo else "disabled"
        self.boton_analizar.configure(state=estado)

    # endregion Posicionamiento y tamaño de la ventana

    #
    # --- Gestión del idioma
    #
    # region Gestión del idioma

    # --- Apunta un elemento para traducirlo y lo devuelve
    #     Los {campos} del texto se rellenan con datos
    def traducible(self, elemento: ctk.CTkBaseClass, texto: dict,
                   **datos: object) -> ctk.CTkBaseClass:
        self._textos[elemento] = lambda: K.tr(texto).format(**datos)
        return elemento

    # --- Pone un texto en un elemento. Puede ser:
    #       str      fijo (un nombre de archivo): no se traduce
    #       dict     {idioma: texto}, con sus {campos} en datos
    #       función  que compone el texto en el idioma activo
    def poner(self, elemento: ctk.CTkBaseClass,
              texto: str | dict | Callable[[], str], **datos: object) -> None:
        if isinstance(texto, str):
            self._textos.pop(elemento, None)
            elemento.configure(text=texto)
            return

        if isinstance(texto, dict):
            self.traducible(elemento, texto, **datos)

        else:
            self._textos[elemento] = texto

        elemento.configure(text=self._textos[elemento]())

    # --- Pone el título y los textos en el idioma activo
    def traducir(self) -> None:
        self.title(f"{K.nombre} - {K.tr(self.KV.txt_version)} {K.version}")
        for elemento, componer in self._textos.items():
            elemento.configure(text=componer())

        # --- La rejilla dibuja sus textos («falta»…) en el Canvas
        if self.rejilla is not None:
            self.rejilla.dibujar()
        self.rellenar_incidencias()
        self.ajustar()

    # --- Cambia el idioma activo al elegido en la lista
    def cambiar_idioma(self, nombre: str) -> None:
        for codigo, nombre_idioma in K.idiomas.items():
            if nombre_idioma == nombre:
                K.idioma = codigo
        self.traducir()

    # endregion Gestión del idioma
