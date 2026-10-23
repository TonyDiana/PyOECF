# -*- coding: utf-8 *-*
"""
    :Propósito: Kernel PyOECF.
    :Autor:     Tony Diana
    :Versión:   26.10.19
"""

# cSpell:ignore anchoxalto, biboecf, borderwidth, choosedir, customtkinter
# cSpell:ignore expórtelas, exps, getexistingdirectory, highlightthickness
# cSpell:ignore initialdir, kdialog, lstar, mclocale, mcset, meipass, msgcat
# cSpell:ignore oecf, padx, pady, redibuja, redibujar, relx, screeninfo
# cSpell:ignore scrollregion, startfile, textvariable, tobytes, Ventanita
# cSpell:ignore ventanita, winfo, wraplength, yscrollcommand, zenity

# --- Valenciano
# cSpell:ignore acadèmica, accedir, acord, Ajuda, Analitzant, Analitzar
# cSpell:ignore analitzat, aquest, aturat, Buscant, Càmera, carpetes
# cSpell:ignore compressió, Copiant, denegat, desconegut, diferent, drap, Eixir
# cSpell:ignore envieu, escrit, escriure, escrivint, espai, està, existeix
# cSpell:ignore exportació, Exportacions, exportacions, exporteu, fallat, Febr
# cSpell:ignore Finalitzat, Fitxa, fitxa, fitxer, generarà, Grandària
# cSpell:ignore grandària, imatge, imatges, Incidències, incidències, inesperat
# cSpell:ignore Juny, Làmina, làmina, làmines, l'anàlisi, Llegint, llegint
# cSpell:ignore llegir, Llibre, llibre, Llicència, lliure, l'operació, Maig
# cSpell:ignore Març, menut, mesurades, Mesurant, mesurat, missatge, Mostra
# cSpell:ignore nincidències, només, obert, oberta, obrir, Permís, permís, però
# cSpell:ignore Podeu, pogut, prepareu, provar, recomanada, refet, repetix
# cSpell:ignore resultats, revelant, Revelat, revelat, Selecció, Seleccioneu
# cSpell:ignore Sense, sense, Sèrie, sèrie, s'esborrarà, seua, seues
# cSpell:ignore substituiran, Suport, targeta, tessel, Trieu, trobat, vàlid
# cSpell:ignore Versió, versió, Voleu

__all__ = ["Ventana"]

# --- Bibliotecas estándar Python
import dataclasses
import math
from datetime import datetime
import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import traceback
import webbrowser
from collections.abc import Callable, Iterator
from functools import partial
from pathlib import Path
from tkinter import filedialog, messagebox
from types import TracebackType

# --- Bibliotecas externas
import customtkinter as ctk
import numpy as np
import screeninfo

# --- Bibliotecas internas
import biboecf
from bib import std
from .constantes import K
from .rejilla import Rejilla
from .textos_excel import textos_excel
from .update import KA, es_mas_nueva, version_publicada


#
class Ventana(ctk.CTk):
    """ Ventana principal de PyOECF. """

    # --- OJO: aquí NO tiene efecto. __slots__ solo impide crear atributos
    #     nuevos si todas las std de las que se hereda también lo usan,
    #     y customtkinter (ctk.CTk) no lo usa: la ventana sigue teniendo su
    #     __dict__ y admite cualquier atributo. Se deja por la norma
    # __slots__ = []

    #
    # --- Constantes de la ventana (las de toda la app están en K)
    class KV(std.EnumMutable):
        """ Constantes de la ventana principal. """

        # --- Textos {idioma: texto}
        TXT_VERSION = {K.ES: "Versión", K.EN: "Version",
                       K.CA: "Versió"}

        TXT_CARPETA = {K.ES: "Seleccione carpeta", K.EN: "Select folder",
                       K.CA: "Seleccioneu carpeta"}

        TXT_PREPARAR = {K.ES: "Preparar", K.EN: "Prepare", K.CA: "Preparar"}

        # --- Confirmación de Preparar si la carpeta OECF ya tiene el
        #     análisis: se borraría (las exportaciones del revelador, no:
        #     se conservan, y se dice)
        TXT_TITULO_CONFIRMAR = {K.ES: "Preparar de nuevo",
                                K.EN: "Prepare again",
                                K.CA: "Preparar de nou"}
        TXT_YA_REVIEW = {K.ES: "La carpeta OECF ya tiene el análisis.",
                         K.EN: "The OECF folder already has the analysis.",
                         K.CA: "La carpeta OECF ja té l'anàlisi."}
        TXT_TIFF_SE_CONSERVAN = {
            K.ES: ("Su exportación del revelador se conserva.",
                   "Sus {n} exportaciones del revelador se conservan."),
            K.EN: ("Its developer export is kept.",
                   "Its {n} developer exports are kept."),
            K.CA: ("La seua exportació del revelador es conserva.",
                   "Les seues {n} exportacions del revelador es "
                   "conserven.")}
        SEP_LINEAS = "\n"
        ANCHO_CONFIRMAR = 380
        TXT_CANCELAR = {K.ES: "Cancelar", K.EN: "Cancel", K.CA: "Cancel·lar"}
        TECLAS_CANCELAR = ("<Return>", "<Escape>")
        TK_CERRAR = "WM_DELETE_WINDOW"

        # --- Órdenes de Tcl para ver y cancelar lo programado con after
        #     (ver destroy). Se cancela en Tcl y no con after_cancel, que
        #     además borra su comando de Python y falla con los que no lo
        #     son («can't delete Tcl command»)
        TCL_AFTER = "after"
        TCL_INFO = "info"
        TCL_CANCEL = "cancel"
        TXT_SE_BORRARA = {
            K.ES: "Si prepara de nuevo, el análisis se borrará. ¿Seguir?",
            K.EN: "If you prepare again, the analysis will be deleted. "
                  "Continue?",
            K.CA: "Si prepareu de nou, l'anàlisi s'esborrarà. Voleu "
                  "continuar?"}

        # --- Segunda parte del análisis (las exportaciones del revelador):
        #     se ve si ya hay análisis en el JSON; activo si hay TIFF
        TXT_ANALIZAR_REVELADO = {K.ES: "Analizar revelado",
                                 K.EN: "Analyze development",
                                 K.CA: "Analitzar revelat"}
        TXT_MIDIENDO_REVELADO = {
            K.ES: "Analizando el revelado: {n} de {total}…",
            K.EN: "Analyzing the development: {n} of {total}…",
            K.CA: "Analitzant el revelat: {n} de {total}…"}
        TXT_REVELADO_HECHO = {
            K.ES: "Revelado analizado: {n} de {total} exportaciones medidas. "
                  "Libro rehecho: {archivo}",
            K.EN: "Development analyzed: {n} of {total} exports measured. "
                  "Workbook rebuilt: {archivo}",
            K.CA: "Revelat analitzat: {n} de {total} exportacions mesurades. "
                  "Llibre refet: {archivo}"}
        TXT_FASE_REVELADO = {K.ES: "Revelado", K.EN: "Development",
                             K.CA: "Revelat"}
        ANCHO_REVELADO = 600
        # --- Al terminar Generar, si la carpeta OECF ya tiene
        #     exportaciones del revelador (Preparar las conserva): se
        #     pregunta si medirlas ya con el análisis nuevo (Tony,
        #     2026-10-16: sí, con aviso)
        TXT_TITULO_TIFF_YA = {K.ES: "Exportaciones del revelador",
                              K.EN: "Developer exports",
                              K.CA: "Exportacions del revelador"}
        TXT_PREGUNTA_TIFF_YA = {
            K.ES: ("La carpeta OECF tiene {n} exportación del revelador. "
                   "¿Medirla ya con el análisis nuevo?",
                   "La carpeta OECF tiene {n} exportaciones del revelador. "
                   "¿Medirlas ya con el análisis nuevo?"),
            K.EN: ("The OECF folder has {n} developer export. Measure it "
                   "now with the new analysis?",
                   "The OECF folder has {n} developer exports. Measure "
                   "them now with the new analysis?"),
            K.CA: ("La carpeta OECF té {n} exportació del revelador. "
                   "Voleu mesurar-la ja amb l'anàlisi nova?",
                   "La carpeta OECF té {n} exportacions del revelador. "
                   "Voleu mesurar-les ja amb l'anàlisi nova?")}
        TXT_MEDIR = {K.ES: "Medir", K.EN: "Measure", K.CA: "Mesurar"}

        TXT_TITULO_PSD = {K.ES: "Rehacer las láminas",
                          K.EN: "Rebuild the print sheets",
                          K.CA: "Refer les làmines"}
        TXT_PREGUNTA_PSD = {
            K.ES: "¿Rehacer las láminas con las exportaciones del revelador? "
                  "Se sustituirán las que hay.",
            K.EN: "Rebuild the print sheets with the developer exports? The "
                  "existing ones will be replaced.",
            K.CA: "Voleu refer les làmines amb les exportacions del "
                  "revelador? Se substituiran les que hi ha."}
        TXT_REHACER = {K.ES: "Rehacer", K.EN: "Rebuild", K.CA: "Refer"}
        TXT_LEYENDO_PSD = {K.ES: "Lámina: leyendo {n} de {total}…",
                           K.EN: "Print sheet: reading {n} of {total}…",
                           K.CA: "Làmina: llegint {n} de {total}…"}
        TXT_PROBLEMAS_TIFF = {
            biboecf.KRV.MEDIDA_DISTINTA: {
                K.ES: "No se midieron, por tamaño distinto (expórtelas a "
                      "tamaño completo y sin recortar): {archivos}",
                K.EN: "Not measured, wrong size (export them at full size "
                      "and uncropped): {archivos}",
                K.CA: "No s'han mesurat, per grandària diferent "
                      "(exporteu-les a grandària completa i sense "
                      "retallar): {archivos}"},
            biboecf.KRV.ESPACIO_DESCONOCIDO: {
                K.ES: "No se midieron, por espacio de color desconocido "
                      "(expórtelas en sRGB o, si no, en Adobe RGB): "
                      "{archivos}",
                K.EN: "Not measured, unknown colour space (export them in "
                      "sRGB or, failing that, Adobe RGB): {archivos}",
                K.CA: "No s'han mesurat, per espai de color desconegut "
                      "(exporteu-les en sRGB o, si no, en Adobe RGB): "
                      "{archivos}"},
            biboecf.KRV.COMPRIMIDA: {
                K.ES: "No se midieron, por su compresión (expórtelas sin "
                      "comprimir o en ZIP; LZW no se puede leer): "
                      "{archivos}",
                K.EN: "Not measured, because of their compression (export "
                      "them uncompressed or in ZIP; LZW cannot be read): "
                      "{archivos}",
                K.CA: "No s'han mesurat, per la seua compressió "
                      "(exporteu-les sense comprimir o en ZIP; LZW no es pot "
                      "llegir): {archivos}"},
            biboecf.KRV.SIN_TESELAS: {
                K.ES: "No se midieron, sin teselas de tarjeta dentro: "
                      "{archivos}",
                K.EN: "Not measured, no card tiles inside: {archivos}",
                K.CA: "No s'han mesurat, sense tessel·les de targeta "
                      "dins: {archivos}"}}
        TXT_REVELADO_FALLO = {
            K.ES: "Revelado analizado ({n} de {total}), pero no se pudo "
                  "guardar o rehacer el libro (¿está abierto?): {archivo}",
            K.EN: "Development analyzed ({n} of {total}), but the workbook "
                  "could not be saved or rebuilt (is it open?): {archivo}",
            K.CA: "Revelat analitzat ({n} de {total}), però no s'ha pogut "
                  "guardar o refer el llibre (està obert?): {archivo}"}
        TXT_SIN_CONTROL = {
            K.ES: "Faltan las tomas de control de la serie (los balances "
                  "de blancos, las tomas tapadas y las repeticiones de la "
                  "toma de referencia que comprueban que la luz no "
                  "cambió): no se puede volver a medir. Se toman como "
                  "buenos los datos del análisis anterior.",
            K.EN: "The control shots of the series are missing (the white "
                  "balance shots, the covered shots and the repetitions of "
                  "the reference shot that check that the light did not "
                  "change): the series cannot be measured again. The data "
                  "from the previous analysis are taken as valid.",
            K.CA: "Falten les preses de control de la sèrie (els balanços "
                  "de blancs, les preses tapades i les repeticions de la "
                  "presa de referència que comproven que la llum no va "
                  "canviar): no es pot tornar a mesurar. Es prenen com a "
                  "bones les dades de l'anàlisi anterior."}
        TXT_SIN_ZONAS = {
            K.ES: "Esta carpeta no tiene las imágenes de las zonas: no se "
                  "puede analizar nada más con ella. Los resultados ya "
                  "hechos siguen disponibles.",
            K.EN: "This folder does not have the zone images: nothing else "
                  "can be analyzed with it. The results already produced "
                  "are still available.",
            K.CA: "Esta carpeta no té les imatges de les zones: no es pot "
                  "analitzar res més amb ella. Els resultats ja fets "
                  "continuen disponibles."}
        # --- Error técnico (sin traducir, como los de Tk que enseña
        #     MostrarError): el JSON dice tener análisis y no se lee
        ERROR_ANALISIS_ILEGIBLE = "No se puede leer el análisis guardado"

        TXT_ABRIR_RESULTADOS = {K.ES: "Abrir resultados",
                                K.EN: "Open results",
                                K.CA: "Obrir resultats"}

        TXT_FASE_CARPETA = {K.ES: "Carpeta", K.EN: "Folder", K.CA: "Carpeta"}
        TXT_FASE_CAM = {K.ES: "Cámara",      K.EN: "Camera", K.CA: "Càmera"}
        TXT_FECHA = {K.ES: "Fecha",          K.EN: "Date",   K.CA: "Data"}

        TXT_ARCHIVO = {K.ES: "Primera imagen", K.EN: "First image",
                       K.CA: "Primera imatge"}

        # --- Fecha y hora de disparo, como se escriben en cada idioma
        FORMATO_FECHA = {K.ES: "%d/%m/%Y %H:%M:%S",
                         K.EN: "%Y-%m-%d %H:%M:%S",
                         K.CA: "%d/%m/%Y %H:%M:%S"}

        TXT_MODELO = {K.ES: "Modelo", K.EN: "Model", K.CA: "Model"}

        # --- Profundidad de bits de los RAW
        TXT_BITS = {K.ES: "{n} bits", K.EN: "{n} bits", K.CA: "{n} bits"}

        # --- Serie: los {campos} se rellenan al mostrarlos
        TXT_FASE_SERIE = {K.ES: "Serie", K.EN: "Series", K.CA: "Sèrie"}
        TXT_LEYENDO = {K.ES: "Leyendo {n} de {total}…",
                       K.EN: "Reading {n} of {total}…",
                       K.CA: "Llegint {n} de {total}…"}

        TXT_COPIANDO = {K.ES: "Copiando {n} de {total}…",
                        K.EN: "Copying {n} of {total}…",
                        K.CA: "Copiant {n} de {total}…"}

        TXT_RESUMEN = {K.ES: ("{total} imagen · de {desde} a {hasta}",
                              "{total} imágenes · de {desde} a {hasta}"),
                       K.EN: ("{total} image · from {desde} to {hasta}",
                              "{total} images · from {desde} to {hasta}"),
                       K.CA: ("{total} imatge · de {desde} a {hasta}",
                              "{total} imatges · de {desde} a {hasta}")}

        TXT_SIN_LEER = {K.ES: " · {n} sin leer", K.EN: " · {n} unreadable",
                        K.CA: " · {n} sense llegir"}

        # --- Resumen de la rejilla en una línea: separador entre trozos
        #     (el de biboecf, el mismo de la exposición)
        SEP_RESUMEN = biboecf.OECF.KT.SEPARADOR

        # --- Incidencias de la rejilla: botón bajo la Z0, con cuántas
        #     hay, y su propia ventana (ancho × alto, en píxeles)
        TXT_INCIDENCIAS = {K.ES: "Incidencias ({n})", K.EN: "Issues ({n})",
                           K.CA: "Incidències ({n})"}
        TXT_SIN_INCIDENCIAS = {K.ES: "Sin incidencias", K.EN: "No issues",
                               K.CA: "Sense incidències"}

        # --- Las incidencias, una por línea, también en un archivo de
        #     texto en la carpeta ANALISIS, en el idioma de la ventana
        SEP_INCIDENCIAS = "\n"
        ARCHIVO_INCIDENCIAS = "incidencias.txt"
        # --- Analizar: botón bajo la ZX, activo solo si la serie sirve
        TXT_ANALIZAR = {K.ES: "Analizar", K.EN: "Analyze",
                        K.CA: "Analitzar"}
        TXT_TITULO_INCIDENCIAS = {K.ES: "Incidencias de la serie",
                                  K.EN: "Series issues",
                                  K.CA: "Incidències de la sèrie"}
        MEDIDA_INCIDENCIAS = "520x320"

        # --- Caja Lámina (la crea Analizar): el paño de la Z-V, su recorte
        #     y los tamaños, con su porcentaje (100 entre el divisor)
        TXT_FASE_PSD = {K.ES: "Lámina", K.EN: "Print sheet",
                        K.CA: "Làmina"}
        TXT_BUSCANDO_TELA = {K.ES: "Buscando el paño…",
                             K.EN: "Looking for the fabric…",
                             K.CA: "Buscant el drap…"}
        TXT_PROBLEMA_TELA = {
            biboecf.KTE.SIN_TELA: {
                K.ES: "No se encontró el paño: solo se generará el Excel.",
                K.EN: "The fabric was not found: only the Excel workbook "
                      "will be generated.",
                K.CA: "No s'ha trobat el drap: només es generarà l'Excel."},
            biboecf.KTE.TELA_MIN: {
                K.ES: "El paño es demasiado pequeño para la lámina: solo "
                      "se generará el Excel.",
                K.EN: "The fabric is too small for the print sheet: only "
                      "the Excel workbook will be generated.",
                K.CA: "El drap és massa menut per a la làmina: només es "
                      "generarà l'Excel."}}
        TXT_MEDIDA = {K.ES: "Tamaño", K.EN: "Size", K.CA: "Grandària"}

        # --- Ventanita de mensajes: ancho inicial de sus líneas (píxeles;
        #     luego sigue al de la ventanita, ver _ajustar_mensajes) y
        #     separación entre mensajes
        ANCHO_MENSAJES = 260
        SEP_MENSAJES = "\n"

        # --- Ancho de los botones de tamaño: 0 en customtkinter es «el de
        #     su contenido» (por defecto reservan 100 px, y sobraba hueco
        #     entre los porcentajes y la ventanita)
        ANCHO_CONTENIDO = 0

        # --- Generar: progreso de la medida, el libro (en la carpeta OECF,
        #     con el nombre del programa) y si no se pudo escribir
        TXT_MIDIENDO = {K.ES: "Midiendo {n} de {total}…",
                        K.EN: "Measuring {n} of {total}…",
                        K.CA: "Mesurant {n} de {total}…"}
        TXT_EXCEL = {K.ES: "Libro escrito: {archivo}",
                     K.EN: "Workbook written: {archivo}",
                     K.CA: "Llibre escrit: {archivo}"}
        TXT_SIN_EXCEL = {
            K.ES: "No se pudo escribir el libro (¿está abierto?): {archivo}",
            K.EN: "The workbook could not be written (is it open?): "
                  "{archivo}",
            K.CA: "No s'ha pogut escriure el llibre (està obert?): "
                  "{archivo}"}
        TXT_ERROR_EXCEL = {
            K.ES: "Error al escribir el libro {archivo}: {error}",
            K.EN: "Error writing the workbook {archivo}: {error}",
            K.CA: "Error en escriure el llibre {archivo}: {error}"}
        EXTENSION_EXCEL = ".xlsx"

        # --- Ficha PDF de la cámara (biboecf.Ficha): junto al libro, con
        #     su mismo nombre; se escribe con él (Generar y Analizar
        #     revelado)
        TXT_FICHA = {K.ES: "Ficha escrita: {archivo}",
                     K.EN: "Camera sheet written: {archivo}",
                     K.CA: "Fitxa escrita: {archivo}"}
        TXT_SIN_FICHA = {
            K.ES: "No se pudo escribir la ficha (¿está abierta?): {archivo}",
            K.EN: "The camera sheet could not be written (is it open?): "
                  "{archivo}",
            K.CA: "No s'ha pogut escriure la fitxa (està oberta?): "
                  "{archivo}"}
        TXT_ERROR_FICHA = {
            K.ES: "Error al escribir la ficha {archivo}: {error}",
            K.EN: "Error writing the camera sheet {archivo}: {error}",
            K.CA: "Error en escriure la fitxa {archivo}: {error}"}
        EXTENSION_FICHA = ".pdf"

        # --- Cajetín de datos de la lámina (Tony, 2026-10-16), de arriba
        #     abajo: la cámara, la latitud de texturas recomendada (de los
        #     resultados del JSON), la fecha de las tomas (la de la ZV, no
        #     la de generar) y el soporte, para escribirlo a mano
        TXT_CARTELA_CAM = {K.ES: "Cámara: {cam}",
                           K.EN: "Camera: {cam}",
                           K.CA: "Càmera: {cam}"}
        TXT_CARTELA_LATITUD = {
            K.ES: "Latitud recomendada: {desde} a {hasta} ({zonas} zonas)",
            K.EN: "Recommended latitude: {desde} to {hasta} ({zonas} zones)",
            K.CA: "Latitud recomanada: {desde} a {hasta} ({zonas} zones)"}
        TXT_CARTELA_SIN_LATITUD = {K.ES: "Latitud recomendada: —",
                                   K.EN: "Recommended latitude: —",
                                   K.CA: "Latitud recomanada: —"}
        TXT_CARTELA_FECHA = {K.ES: "Fecha: {fecha}", K.EN: "Date: {fecha}",
                             K.CA: "Data: {fecha}"}
        TXT_CARTELA_SOPORTE = {
            K.ES: "Soporte: ____________________________",
            K.EN: "Paper: ____________________________",
            K.CA: "Suport: ____________________________"}
        TXT_MESES = {
            K.ES: ("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago",
                   "Sep", "Oct", "Nov", "Dic"),
            K.EN: ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug",
                   "Sep", "Oct", "Nov", "Dec"),
            K.CA: ("Gen", "Febr", "Març", "Abr", "Maig", "Juny", "Jul",
                   "Ag", "Set", "Oct", "Nov", "Des")}
        FORMATO_FECHA_CARTELA = "{dia} {mes} {year}"

        # --- Generar, la lámina: progreso del revelado, las escritas y si
        #     no se pudo
        TXT_REVELANDO = {K.ES: "Lámina: revelando {n} de {total}…",
                         K.EN: "Print sheet: developing {n} of {total}…",
                         K.CA: "Làmina: revelant {n} de {total}…"}
        TXT_ESCRIBIENDO = {K.ES: "Lámina: escribiendo {archivo}…",
                           K.EN: "Print sheet: writing {archivo}…",
                           K.CA: "Làmina: escrivint {archivo}…"}
        TXT_PSD = {K.ES: "Lámina escrita: {archivos}",
                   K.EN: "Print sheet written: {archivos}",
                   K.CA: "Làmina escrita: {archivos}"}
        TXT_SIN_PSD = {
            K.ES: "No se pudo escribir la lámina (¿está abierta?): "
                  "{archivo}",
            K.EN: "The print sheet could not be written (is it open?): "
                  "{archivo}",
            K.CA: "No s'ha pogut escriure la làmina (està oberta?): "
                  "{archivo}"}
        SEP_ARCHIVOS = ", "
        # --- Incidencias de las teselas que dice la ventanita de la caja
        #     Lámina al analizar: las rechazadas y sus avisos
        INCIDENCIAS_TESELAS = (biboecf.KI.RECHAZADAS,
                               biboecf.KI.TARJETA_SUCIA,
                               biboecf.KI.LUZ_DESIGUAL,
                               biboecf.KI.REVISAR_SERIE,
                               biboecf.KI.REPETIR_SERIE)

        TXT_FINALIZADO = {K.ES: "Finalizado.", K.EN: "Finished.",
                          K.CA: "Finalitzat."}
        # --- Error que nadie recogió (Tony: ningún error silencioso): se
        #     dice en una ventana, además de en la terminal
        TXT_TITULO_ERROR = {K.ES: "Error inesperado",
                            K.EN: "Unexpected error",
                            K.CA: "Error inesperat"}
        TXT_ERROR_INESPERADO = {
            K.ES: "Algo ha fallado y la operación se ha detenido:\n\n"
                  "{error}\n\nLo ya escrito en la carpeta se conserva. "
                  "Puede volver a intentarlo; si se repite, envíe este "
                  "mensaje al autor.",
            K.EN: "Something went wrong and the operation stopped:\n\n"
                  "{error}\n\nWhat was already written in the folder is "
                  "kept. You can try again; if it happens again, send this "
                  "message to the author.",
            K.CA: "Alguna cosa ha fallat i l'operació s'ha aturat:\n\n"
                  "{error}\n\nEl que ja s'ha escrit en la carpeta es "
                  "conserva. Podeu tornar-ho a provar; si es repetix, "
                  "envieu aquest missatge a l'autor."}

        TXT_FINALIZADO_ARCHIVOS = {K.ES: "Finalizado: {archivos}.",
                                   K.EN: "Finished: {archivos}.",
                                   K.CA: "Finalitzat: {archivos}."}
        TXT_PORCENTAJE = {K.ES: "{p} %", K.EN: "{p}%", K.CA: "{p} %"}
        TXT_GENERAR = {K.ES: "Generar", K.EN: "Generate", K.CA: "Generar"}

        # --- Imagen del recorte para Tk, sin Pillow: PPM (RGB de 8 bits)
        CABECERA_PPM = "P6 {ancho} {alto} 255\n"
        FORMATO_PPM = "PPM"

        TXT_SIN_CARPETA = {K.ES: "La carpeta no existe",
                           K.EN: "The folder does not exist",
                           K.CA: "La carpeta no existeix"}

        TXT_SIN_RAW = {K.ES: "No hay RAW en la carpeta",
                       K.EN: "No RAW files in the folder",
                       K.CA: "No hi ha RAW en la carpeta"}

        # --- Permisos: para leer la carpeta, para escribir en ella (la
        #     carpeta OECF) y si la copia falla al preparar
        TXT_SIN_PERMISO_LEER = {K.ES: "Sin permiso para leer la carpeta",
                                K.EN: "No permission to read the folder",
                                K.CA: "Sense permís per a llegir la carpeta"}
        TXT_SIN_PERMISO_ESCRIBIR = {
            K.ES: "Sin permiso para escribir en la carpeta",
            K.EN: "No permission to write to the folder",
            K.CA: "Sense permís per a escriure en la carpeta"}

        # --- Carpeta OECF de una serie preparada cuyo JSON no sirve para
        #     restaurarla: de una versión del formato más nueva o dañado
        TXT_ESTUDIO_NUEVO = {
            K.ES: "Esta preparación es de una versión más nueva de PyOECF: "
                  "actualiza la aplicación para abrirla",
            K.EN: "This preparation is from a newer version of PyOECF: "
                  "update the application to open it",
            K.CA: "Esta preparació és d'una versió més nova de PyOECF: "
                  "actualitza l'aplicació per a obrir-la"}
        TXT_ESTUDIO_DANADO = {
            K.ES: "El archivo de estudio de esta carpeta está dañado y no "
                  "se puede leer",
            K.EN: "The study file in this folder is damaged and cannot be "
                  "read",
            K.CA: "El fitxer d'estudi d'esta carpeta està danyat i no es "
                  "pot llegir"}

        # --- Texto de cada problema de la carpeta (biboecf.KCA)
        TXT_PROBLEMA_CARPETA = {
            biboecf.KCA.SIN_CARPETA: TXT_SIN_CARPETA,
            biboecf.KCA.SIN_PERMISO_LEER: TXT_SIN_PERMISO_LEER,
            biboecf.KCA.SIN_RAW: TXT_SIN_RAW,
            biboecf.KCA.SIN_PERMISO_ESCRIBIR: TXT_SIN_PERMISO_ESCRIBIR}
        TXT_NO_COPIADO = {
            K.ES: "No se pudieron copiar los resultados. {error}",
            K.EN: "The results could not be copied. {error}",
            K.CA: "No s'han pogut copiar els resultats. {error}"}

        TXT_NO_READ = {K.ES: "No se ha podido leer", K.EN: "Could not be read",
                       K.CA: "No s'ha pogut llegir"}
        TXT_LICENCIA = {K.ES: "Licencia académica de uso libre",
                        K.EN: "Academic license, free to use",
                        K.CA: "Llicència acadèmica d'ús lliure"}
        TXT_AYUDA = {K.ES: "Ayuda", K.EN: "Help",
                     K.CA: "Ajuda"}
        TXT_IDIOMA = {K.ES: "Idioma", K.EN: "Language",
                      K.CA: "Idioma"}
        TXT_NUEVA_VERSION = {K.ES: "Nueva versión {version}",
                             K.EN: "New version {version}",
                             K.CA: "Nova versió {version}"}
        TXT_SALIR = {K.ES: "Salir", K.EN: "Exit",
                     K.CA: "Eixir"}

        # --- Medidas (píxeles)
        MARGEN = 10
        GROSOR_MARCO = 2

        # --- Tamaño de la letra de la licencia, en la cabecera (la normal
        #     del tema es 13)
        LETRA_LICENCIA = 15

        # --- Hueco entre el icono y la licencia, en la cabecera
        SEP_LICENCIA = 20

        # --- Datos en una línea: hueco entre un dato y el siguiente
        SEP_DATOS = 30

        # --- A cada lado del título de una caja, entre su texto y la línea
        RELLENO_TITULO = 12

        # --- Dentro de una caja con título: entre el título y el contenido
        SEPARADOR_SUPERIOR = 0
        ANCHO_CARPETA = 650

        # --- Principio de sys.platform en Windows: ahí el icono va con
        #     iconbitmap() y el .ico, o customtkinter pone el suyo
        PLATAFORMA_WINDOWS = "win"

        # --- Abrir una carpeta en el explorador de archivos: macOS
        #     (sys.platform) y la orden de macOS y de Linux. En Windows,
        #     os.startfile
        PLATAFORMA_MAC = "darwin"
        ABRIR_MAC = "open"
        ABRIR_LINUX = "xdg-open"

        # --- Elegir carpeta en Linux con el explorador del escritorio: el
        #     de Tk no ve los discos externos. En Windows y macOS el de Tk
        #     ya es el del sistema. En KDE va primero kdialog; si no hay
        #     ninguno, el de Tk
        PLATAFORMA_LINUX = "linux"
        ELEGIR_ZENITY = ("zenity", "--file-selection", "--directory")
        ELEGIR_KDIALOG = ("kdialog", "--getexistingdirectory")
        ESCRITORIO = "XDG_CURRENT_DESKTOP"
        ESCRITORIO_KDE = "KDE"

        # --- Códigos de salida del explorador: carpeta elegida o
        #     cancelado. Cualquier otro es un fallo: se abre el de Tk
        SALIDA_ELEGIDA = 0
        SALIDA_CANCELADA = 1

        # --- Cada cuántos ms se mira si el explorador se ha cerrado: la
        #     ventana sigue viva mientras tanto
        ESPERA_EXPLORADOR = 200

        # --- En el ejecutable de PyInstaller, LD_LIBRARY_PATH apunta a sus
        #     bibliotecas y rompería el explorador: se le da la del sistema
        LD_RUTA = "LD_LIBRARY_PATH"
        LD_RUTA_ORIGINAL = "LD_LIBRARY_PATH_ORIG"

        # --- Milisegundos sin teclear en la ruta antes de mostrar la
        #     cámara: así no se lee la carpeta con cada letra
        ESPERA_TECLEO = 500

        # --- Repintado forzado (ver Ajustar): milisegundos tras ajustar
        #     el tamaño en que se pide a cada elemento que se redibuje (una
        #     pasada por cada uno: la segunda repasa lo que se pinte tarde)
        #     y el evento de Tk que lo pide
        ESPERAS_REPINTADO = (200, 600)
        TK_REDIBUJAR = "<Expose>"

        # --- Evento de Tk: un elemento cambió de tamaño (el lienzo, para
        #     estirar el cuerpo; la ventanita de mensajes, para cortar sus
        #     líneas a su ancho)
        TK_CAMBIO_MEDIDA = "<Configure>"

        # --- Milisegundos entre la lectura de una imagen y la siguiente:
        #     lo justo para que la ventana atienda al ratón y se repinte
        PAUSA_LECTURA = 1

        # --- Cada cuántos milisegundos se mira si ya llegó la respuesta
        #     de GitHub sobre la versión publicada
        PAUSA_VERSION = 200

        # --- Lo mismo entre la copia de una toma y la siguiente
        PAUSA_COPIA = 1

        # --- Separación entre el borde superior del monitor y la ventana:
        #     arriba del todo, para que tenga sitio al crecer hacia abajo
        ARRIBA = 40

        # --- Posición de una ventana en Tk: se pide con TK_POS
        #     ("+x+y") y wm_geometry() la devuelve tras el tamaño
        #     ("anchoxalto+x+y"), separada por SEP_POS
        TK_POS = "+{x}+{y}"
        SEP_POS = "+"

        # --- Alto que no puede ocupar la ventana bajo ARRIBA: barra de
        #     título y barra de tareas del sistema. Si el contenido no cabe
        #     en el resto, se desplaza como una página web
        RESERVA_ALTO = 100

        # --- Rueda del ratón: líneas por paso, y eventos (Windows y
        #     macOS dan MouseWheel con delta; Linux, los botones 4 y 5)
        LINEAS_RUEDA = 3
        TK_RUEDA = ("<MouseWheel>", "<Button-4>", "<Button-5>")
        BTN_RUEDA_ARRIBA = 4

        # --- Diálogo de carpetas de Tk (el de Linux): variables Tcl que
        #     muestran la casilla «ocultos» y la dejan desmarcada. Para que
        #     existan hay que cargar antes el diálogo: se le llama con una
        #     opción que no existe, falla y queda cargado
        TCL_VER_CASILLA_OCULTOS = "::tk::dialog::file::showHiddenBtn"
        TCL_MOSTRAR_OCULTOS = "::tk::dialog::file::showHiddenVar"
        TCL_CARGAR_DIALOGO = ("tk_getOpenFile", "-opc-que-no-existe")
        TCL_ASIGNAR = "set"
        TCL_SI, TCL_NO = "1", "0"

        # --- Idioma del diálogo de Tk: sus textos salen de un catálogo
        #     (msgcat) en el espacio de nombres de Tk. El diálogo se crea
        #     una vez y se reutiliza: se destruye para que salga con el
        #     idioma nuevo. Traducciones que le faltan al catálogo de Tk
        TCL_IDIOMA = "::msgcat::mclocale"
        TCL_TRADUCIR = "::msgcat::mcset"
        TCL_ESPACIO = ("namespace", "eval", "::tk")
        TCL_DIALOGO = ".__tk_choosedir"
        TCL_FALTAN = {
            "Show &Hidden Directories": {
                K.ES: "Mostrar carpetas &ocultas",
                K.CA: "Mostra les carpetes &ocultes"},
            "&OK": {K.CA: "&D'acord"},
            "&Cancel": {K.CA: "&Cancel·la"},
            "Choose Directory": {K.CA: "Trieu una carpeta"},
            "&Selection:": {K.CA: "&Selecció:"},
            'Directory "%1$s" does not exist.': {
                K.CA: 'La carpeta "%1$s" no existeix.'},
            'Cannot change to the directory "%1$s".\nPermission denied.': {
                K.CA: 'No es pot accedir a la carpeta "%1$s".\n'
                      'Permís denegat.'},
            'Invalid file name "%1$s".': {
                K.CA: 'Nom de fitxer no vàlid "%1$s".'}}

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

    #
    def caja_cabecera(self) -> None:
        """ Siempre arriba, aunque crezcan las cajas de debajo. """
        # --- Abreviar escritura
        kv = self.KV

        fila = self.CrearCaja(fija=True, marco=False)

        # --- Icono del programa en una etiqueta de Tk, con el fondo de la
        #     ventana: la de customtkinter pide CTkImage, y esa necesita
        #     Pillow. Se guarda la imagen: si no, Python la borra
        try:
            self.icono_cabecera = tk.PhotoImage(
                file=K.path / K.CARPETA_RECURSOS / K.ICONO_PNG)
            fondo = self._apply_appearance_mode(
                ctk.ThemeManager.theme["CTk"]["fg_color"])
            tk.Label(fila, image=self.icono_cabecera, bg=fondo,
                     borderwidth=0).pack(side="left")
        except tk.TclError:
            pass

        # --- La licencia, a la izquierda tras el icono, un poco separada;
        #     el autor, a la derecha
        self.ApuntarTexto(ctk.CTkLabel(
            fila, font=ctk.CTkFont(size=kv.LETRA_LICENCIA)),
            kv.TXT_LICENCIA).pack(side="left", padx=(kv.SEP_LICENCIA, 0))
        ctk.CTkLabel(fila, text=K.derechos).pack(side="right")

    #
    # --- Caja --- | Ayuda | Idioma | Salir |
    #

    #
    def caja_ayuda(self) -> None:
        """
        Caja Ayuda: el botón de la ayuda web, el de nueva versión (oculto
        hasta saber que la hay), la lista de idiomas y Salir.
        """
        # --- Abreviar escritura
        kv = self.KV

        fila = self.CrearCaja()

        # --- Los extremos primero, para que Idioma ocupe el centro. Ayuda
        #     abre la web de ayuda en el navegador
        self.ApuntarTexto(ctk.CTkButton(
            fila, command=lambda: webbrowser.open(K.URL_HELP)),
            kv.TXT_AYUDA).pack(side="left")
        self.ApuntarTexto(ctk.CTkButton(fila, command=self.destroy),
                          kv.TXT_SALIR).pack(side="right")

        # --- Idioma: grupo centrado en el hueco entre Ayuda y Salir. Al
        #     elegir otro en la lista, cambia toda la ventana
        grupo = ctk.CTkFrame(fila, fg_color="transparent")
        grupo.pack(side="left", expand=True)

        # --- Nueva versión, a la derecha de Ayuda: abre la página de
        #     descargas. Oculto: solo aparece si GitHub tiene una versión
        #     más nueva (ver MostrarVersion)
        self.btn_version = ctk.CTkButton(
            fila, command=lambda: webbrowser.open(KA.URL_RELEASES))
        self.grupo_idioma = grupo

        self.ApuntarTexto(ctk.CTkLabel(grupo), kv.TXT_IDIOMA).pack(
            side="left")

        lista = ctk.CTkComboBox(
            grupo, values=list(K.IDIOMAS.values()), state="readonly",
            command=self.CambiarIdioma)

        lista.set(K.IDIOMAS[K.idioma])
        lista.pack(side="left", padx=(kv.MARGEN, 0))

    #
    # --- Caja --- Carpeta
    #

    #
    def caja_carpeta(self) -> None:
        """
        Caja Carpeta: el botón para elegirla, la casilla con su ruta y sus
        botones: Preparar o, en una carpeta OECF ya preparada, Analizar; y,
        con análisis, Analizar revelado si hay exportaciones del revelador o,
        si no, Abrir resultados (los enseña ActivarCarpeta).
        """
        # --- Abreviar escritura
        kv = self.KV

        # --- La caja: botón · ruta elegida · Analizar revelado (oculto
        #     hasta que haya análisis) · Preparar.
        #     Las cajas que haya hasta esta (incluida) son las propias; el
        #     resto, de encima
        fila = self.CrearCaja(kv.TXT_FASE_CARPETA)
        self.__propias_carpeta = len(self.cajas)
        self.ApuntarTexto(ctk.CTkButton(fila, command=self._elegir),
                          kv.TXT_CARPETA).pack(side="left")

        # --- Los botones, en su grupo, antes que la casilla, para que esta
        #     ocupe el hueco. Se crean ocultos y los enseña ActivarCarpeta,
        #     en este orden: Analizar revelado (con análisis y
        #     exportaciones del revelador) o Abrir resultados (sin ellas) y
        #     Preparar o, en una carpeta OECF ya preparada, Analizar (Tony,
        #     2026-10-19)
        botones = self.botones_carpeta = ctk.CTkFrame(
            fila, fg_color="transparent")
        botones.pack(side="right")
        self.btn_revelado = ctk.CTkButton(botones,
                                          command=self.AnalizarRevelado)
        self.ApuntarTexto(self.btn_revelado, kv.TXT_ANALIZAR_REVELADO)
        self.btn_abrir_carpeta = ctk.CTkButton(
            botones, command=self.AbrirResultados)
        self.ApuntarTexto(self.btn_abrir_carpeta, kv.TXT_ABRIR_RESULTADOS)
        self.btn_analizar_carpeta = ctk.CTkButton(botones,
                                                  command=self.Analizar)
        self.ApuntarTexto(self.btn_analizar_carpeta, kv.TXT_ANALIZAR)
        self.btn_preparar = ctk.CTkButton(botones, command=self.Preparar,
                                          state="disabled")
        self.ApuntarTexto(self.btn_preparar, kv.TXT_PREPARAR)
        self.btn_preparar.pack(side="left", padx=(kv.MARGEN, 0))

        # --- Cada cambio en la ruta (elegida o tecleada) quita las cajas
        #     de encima y muestra la cámara de la carpeta nueva
        self.ruta = ctk.StringVar()
        self.ruta.trace_add("write", self._otra_carpeta)
        carpeta = ctk.CTkEntry(fila, width=kv.ANCHO_CARPETA,
                               textvariable=self.ruta)
        carpeta.pack(side="left", fill="x", expand=True, padx=(kv.MARGEN, 0))

    #
    # --- Diálogo de carpetas: estas dos preparaciones solo afectan al
    #     de Tk de Linux; Windows y macOS usan el suyo propio
    #
    # --- Sin carpetas ocultas (las que empiezan por punto), pero con
    #     la casilla para verlas
    def _sin_ocultos(self) -> None:
        kv = self.KV
        try:
            self.tk.call(*kv.TCL_CARGAR_DIALOGO)
        except tk.TclError:
            pass

        try:
            self.tk.call(kv.TCL_ASIGNAR, kv.TCL_VER_CASILLA_OCULTOS,
                         kv.TCL_SI)
            self.tk.call(kv.TCL_ASIGNAR, kv.TCL_MOSTRAR_OCULTOS,
                         kv.TCL_NO)
        except tk.TclError:
            pass

    #
    # --- En el idioma de la app y no en el del sistema: se completan
    #     las traducciones que le faltan a Tk y, si el diálogo ya
    #     existe, se destruye para que se cree de nuevo en ese idioma
    def _idioma_dialogo(self) -> None:
        kv = self.KV
        try:
            for original, textos in kv.TCL_FALTAN.items():
                for code, traducido in textos.items():
                    self.tk.call(*kv.TCL_ESPACIO, (kv.TCL_TRADUCIR,
                                                   code, original,
                                                   traducido))
            self.tk.call(kv.TCL_IDIOMA, K.idioma)
            if int(self.tk.call("winfo", "exists", kv.TCL_DIALOGO)):
                self.tk.call("destroy", kv.TCL_DIALOGO)
        except tk.TclError:
            pass

    #
    # --- Orden del explorador del escritorio en Linux, o None si no
    #     hay ninguno instalado
    def _orden_linux(self, inicio: Path) -> list[str] | None:
        kv = self.KV
        titulo = K.tr(kv.TXT_CARPETA)
        ordenes = [[*kv.ELEGIR_ZENITY, f"--filename={inicio}{os.sep}",
                    f"--title={titulo}"],
                   [*kv.ELEGIR_KDIALOG, str(inicio), "--title", titulo]]
        if kv.ESCRITORIO_KDE in os.environ.get(kv.ESCRITORIO, ""):
            ordenes.reverse()
        for orden in ordenes:
            if shutil.which(orden[0]):
                return orden
        return None

    #
    # --- Entorno del explorador: el del sistema, no el del ejecutable
    def _entorno_sistema(self) -> dict[str, str]:
        kv = self.KV
        entorno = dict(os.environ)
        if kv.LD_RUTA_ORIGINAL in entorno:
            entorno[kv.LD_RUTA] = entorno[kv.LD_RUTA_ORIGINAL]
        elif getattr(sys, "frozen", False):
            entorno.pop(kv.LD_RUTA, None)
        return entorno

    #
    # --- Escribe la carpeta elegida en la casilla
    def _usar_carpeta(self, ruta: str) -> None:
        self.ruta.set(ruta)
        self._mostrar_cam()

    #
    # --- Diálogo de Tk: Windows, macOS y Linux sin explorador
    def _dialogo_tk(self, inicio: Path) -> None:
        self._sin_ocultos()
        self._idioma_dialogo()
        ruta = filedialog.askdirectory(parent=self, initialdir=inicio)
        if ruta:
            self._usar_carpeta(ruta)

    #
    # --- Espera a que se cierre el explorador de Linux sin bloquear
    #     la ventana. Si falla, se abre el de Tk
    def _esperar_explorador(self, inicio: Path) -> None:
        kv = self.KV
        if self.explorador is None:
            return
        if self.explorador.poll() is None:
            self.after(kv.ESPERA_EXPLORADOR, self._esperar_explorador,
                       inicio)
            return

        code = self.explorador.returncode
        salida = self.explorador.stdout.read().strip() \
            if self.explorador.stdout else ""
        self.explorador = None
        if (code == kv.SALIDA_ELEGIDA) and salida:
            self._usar_carpeta(salida)
        elif code != kv.SALIDA_CANCELADA:
            self._dialogo_tk(inicio)

    #
    # --- Pide la carpeta y la escribe en la casilla. El diálogo
    #     empieza en la carpeta de la casilla, si existe; si no, en la
    #     del usuario (no en la de la app)
    def _elegir(self) -> None:
        kv = self.KV
        if self.explorador is not None:
            return

        escrita = self.ruta.get().strip()
        inicio = Path(escrita) if escrita else Path.home()
        if not inicio.is_dir():
            inicio = Path.home()

        orden = (self._orden_linux(inicio)
                 if sys.platform.startswith(kv.PLATAFORMA_LINUX)
                 else None)
        if orden is not None:
            try:
                self.explorador = subprocess.Popen(
                    orden, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, text=True,
                    env=self._entorno_sistema())
            except OSError:
                self.explorador = None
            else:
                self.after(kv.ESPERA_EXPLORADOR, self._esperar_explorador,
                           inicio)
                return

        self._dialogo_tk(inicio)

    #
    # --- ¿La carpeta escrita es la de la cámara que ya se ve?
    def _es_la_vista(self) -> bool:
        return ((self.OECF is not None)
                and (self.carpetaEscrita == self.carpetaVista))

    #
    # --- Otra carpeta: se quitan las cajas de encima de esta, sean
    #     las que sean. Los argumentos los pone trace_add y no se usan
    def _otra_carpeta(self, *_: object) -> None:
        if self._es_la_vista():
            return
        self.QuitarCajas(self.__propias_carpeta)

        # --- after() programa _mostrar_cam() para dentro de
        #     espera_tecleo ms y devuelve el identificador de esa
        #     llamada; after_cancel() la anula si aún no se ha hecho.
        #     Cada letra anula la llamada anterior y programa otra:
        #     solo se ejecuta la de la última, al dejar de teclear
        if self.__espera is not None:
            self.after_cancel(self.__espera)
        self.__espera = self.after(self.KV.ESPERA_TECLEO, self._mostrar_cam)

    #
    # --- Muestra la caja de la cámara de la carpeta escrita, si no es
    #     la que ya se ve
    def _mostrar_cam(self) -> None:

        # --- Si se llega desde el diálogo, se anula la llamada que
        #     pudiera quedar pendiente de haber tecleado antes
        if self.__espera is not None:
            self.after_cancel(self.__espera)
            self.__espera = None
        if not self._es_la_vista():
            self.caja_cam()

    #
    # --- Caja --- Cámara
    #

    #
    def caja_cam(self) -> None:
        """
        Caja Cámara: al elegir carpeta, lee su serie (fase 1) y enseña el
        archivo, la fecha, la cámara, los bits y la exposición de la Z-V;
        si la carpeta no sirve, dice por qué.
        """
        # --- Abreviar escritura
        kv = self.KV

        # --- La caja se construye al elegir carpeta, encima de la
        #     carpeta: todos los datos en una línea. Siempre es nueva: al
        #     cambiar de carpeta se quita la anterior. Los datos van en un
        #     grupo que no se estira: así queda centrado en la caja
        interior = self.CrearCaja(kv.TXT_FASE_CAM, self.ReiniciarCam)
        self.propias_cam = len(self.cajas)
        grupo = ctk.CTkFrame(interior, fg_color="transparent")
        grupo.pack()

        self.val_archivo = self._nuevo_dato(grupo, kv.TXT_ARCHIVO)
        self.val_fecha = self._nuevo_dato(grupo, kv.TXT_FECHA)
        self.val_modelo = self._nuevo_dato(grupo, kv.TXT_MODELO)

        # --- Profundidad de bits
        self.val_bits = ctk.CTkLabel(grupo, text="")
        self.val_bits.pack(side="left", padx=(kv.SEP_DATOS, 0))

        # --- Exposición: f, Tv e ISO en un solo texto, centrado en su
        #     hueco
        self.val_exp = ctk.CTkLabel(grupo, text="")
        self.val_exp.pack(side="left", padx=(kv.SEP_DATOS, 0))

        # --- Pone los textos nuevos y hace crecer la ventana
        self.Traducir()

        # --- Fase 1 de la serie: la carpeta, sus RAW y la exposición de
        #     la primera. Se guarda para Preparar (y la carpeta elegida,
        #     para no rehacer la caja si se vuelve a elegir la misma). Si
        #     es la OECF de una serie ya preparada, la serie se restaura
        #     de ella, sin Preparar: se va directo a Analizar (Tony,
        #     2026-10-19)
        carpeta = self.carpetaVista = self.carpetaEscrita
        self.preparada = biboecf.es_preparada(carpeta)
        if self.preparada:
            restaurada = biboecf.restaurar_serie(carpeta)
            if restaurada is None:
                self.OECF = biboecf.OECF(carpeta, buscar=False)
                self.Poner(self.val_archivo,                    # type: ignore
                           kv.TXT_ESTUDIO_NUEVO
                           if biboecf.es_mas_nuevo(carpeta)
                           else kv.TXT_ESTUDIO_DANADO)
                self.ActivarCarpeta()
                return
            OECF = self.OECF = restaurada
            self.propias_serie = len(self.cajas)
            self.incidencias = partial(Rejilla.incidencias, OECF)

            # --- Sin la copia de la ZV no hay Analizar ni nada que
            #     analizar de nuevo: se dice, en una caja Serie con una
            #     sola línea
            if not self._hay_zv(OECF):
                interior = self.CrearCaja(kv.TXT_FASE_SERIE,
                                          self.ReiniciarSerie)
                self.propias_serie = len(self.cajas)
                etiqueta = ctk.CTkLabel(interior, text="",
                                        wraplength=kv.ANCHO_REVELADO)
                etiqueta.pack()
                self.Poner(etiqueta, kv.TXT_SIN_ZONAS)
                self.Ajustar()
        else:
            OECF = self.OECF = biboecf.OECF(carpeta)

            # --- Si la carpeta no sirve (no existe, no se lee, sin RAW o
            #     sin permiso para escribir los resultados), se dice por
            #     qué y Preparar no se activa
            problema = biboecf.problema_carpeta(OECF)
            if problema:
                self.Poner(self.val_archivo,                    # type: ignore
                           kv.TXT_PROBLEMA_CARPETA[problema])
                self.ActivarCarpeta()
                return

        self.Poner(self.val_archivo, OECF.primera)              # type: ignore

        # --- Fecha y hora de disparo, en el formato de cada idioma
        fecha = OECF.fecha
        if fecha is None:
            self.Poner(self.val_fecha, kv.TXT_NO_READ)          # type: ignore
        else:
            self.Poner(self.val_fecha,                          # type: ignore
                       partial(self._texto_fecha, fecha))

        # --- Marca y modelo juntos, sin repetir la marca
        cam = OECF.cam
        self.Poner(self.val_modelo,                             # type: ignore
                   kv.TXT_NO_READ if (cam is None) else cam.nombre)

        # --- Profundidad de bits de los RAW
        bits = OECF.bits
        if bits is None:
            self.Poner(self.val_bits, kv.TXT_NO_READ)           # type: ignore
        else:
            self.Poner(self.val_bits, kv.TXT_BITS, n=bits)      # type: ignore

        # --- f, Tv e ISO salen juntos, en un solo texto: «f/9 · Tv 1/125 s
        #     · ISO 100». Si no se leen, se avisa ahí
        exp = OECF.ZV
        if exp is None:
            self.Poner(self.val_exp, kv.TXT_NO_READ)            # type: ignore
        else:
            self.Poner(self.val_exp,                            # type: ignore
                       partial(self._texto_exp, exp))

        # --- Con RAW, ya se puede preparar (o, preparada, analizar)
        self.ActivarCarpeta()

    #
    # --- Añade «nombre valor» a la derecha de los que ya hay en el grupo
    #     y devuelve la etiqueta del valor, para rellenarla. El primero va
    #     pegado al borde; los demás, separados
    def _nuevo_dato(self, grupo: ctk.CTkFrame, nombre: dict) -> ctk.CTkLabel:
        kv = self.KV
        hueco = kv.SEP_DATOS if grupo.winfo_children() else 0
        self.ApuntarTexto(ctk.CTkLabel(grupo), nombre).pack(
            side="left", padx=(hueco, 0))
        valor = ctk.CTkLabel(grupo, text="")
        valor.pack(side="left", padx=(kv.MARGEN, 0))
        return valor

    #
    # --- Fecha y hora de disparo, en el formato del idioma activo
    def _texto_fecha(self, fecha: datetime) -> str:
        return fecha.strftime(K.tr(self.KV.FORMATO_FECHA))

    #
    # --- f, Tv e ISO en un solo texto: «f/9 · Tv 1/125 s · ISO 100»; el
    #     mismo de la ficha, con los rótulos del libro
    def _texto_exp(self, exp: biboecf.Exp) -> str:
        t = textos_excel()
        return biboecf.OECF.TextoExp(exp.f, exp.tv, exp.iso, tuple(
            t[c] for c in biboecf.KXL.ROTULOS_EXP))

    #
    # --- Caja --- Serie
    #

    #
    def caja_serie(self, OECF: biboecf.OECF) -> None:
        """
        Se crea nueva en cada preparación, encima de la cámara: resumen, barra
        de progreso, rejilla y botón de incidencias. Lee la serie una imagen
        cada vez (la exposición de la primera ya se tiene), para que la ventana
        no se congele y vaya mostrando el progreso.
        """
        kv = self.KV

        # --- La caja. La rejilla y el resumen se muestran al terminar
        interior = self.CrearCaja(kv.TXT_FASE_SERIE, self.ReiniciarSerie)
        self.propias_serie = len(self.cajas)
        self.val_serie = ctk.CTkLabel(interior, text="")
        self.val_serie.pack()
        barra = self.barra_serie = ctk.CTkProgressBar(interior)
        rejilla = self.rejilla = Rejilla(interior)
        self.val_copia = ctk.CTkLabel(interior, text="")
        # --- Pie de la rejilla: Incidencias bajo la Z0, el resumen, y
        #     Abrir resultados (la carpeta OECF, inactivo hasta copiar) y
        #     Analizar bajo la ZX (crea la caja Lámina). Son hijos de la
        #     rejilla, que los coloca
        self.val_rejilla = ctk.CTkLabel(rejilla, text="")
        self.btn_incidencias = ctk.CTkButton(
            rejilla, command=self._ver_incidencias)
        self.btn_resultados = self.btn_resultados_serie = ctk.CTkButton(
            rejilla, command=self.AbrirResultados, state="disabled")
        self.ApuntarTexto(self.btn_resultados, kv.TXT_ABRIR_RESULTADOS)
        btn_analizar = self.btn_analizar = ctk.CTkButton(
            rejilla, command=self.Analizar, state="disabled")
        self.ApuntarTexto(btn_analizar, kv.TXT_ANALIZAR)
        rejilla.poner_pie(self.btn_incidencias, self.val_rejilla,
                          (self.btn_resultados, btn_analizar), kv.MARGEN)
        self.Traducir()

        # --- A leer: Preparar queda inactivo hasta el final
        self.leyendo = True
        self.ActivarCarpeta()
        self.lectura = OECF.Leer()
        barra.set(len(OECF.tomas) / len(OECF.raws))
        barra.pack(fill="x", pady=(kv.MARGEN, 0))
        self.Ajustar()
        self._leer_toma()

    #
    # --- Abre (o trae delante) la ventana con todas las incidencias
    def _ver_incidencias(self) -> None:
        kv = self.KV
        if not self.incidencias_abiertas():
            ventana = ctk.CTkToplevel(self)
            ventana.geometry(kv.MEDIDA_INCIDENCIAS)
            ventana.transient(self)
            self.texto_incidencias = ctk.CTkTextbox(ventana, wrap="word")
            self.texto_incidencias.pack(fill="both", expand=True,
                                        padx=kv.MARGEN, pady=kv.MARGEN)
            self.ventana_incidencias = ventana
        self.rellenar_incidencias()
        self.ventana_incidencias.lift()                         # type: ignore

    #
    # --- Lee la siguiente toma (la lee OECF) y se vuelve a programar.
    #     Antes de leer se pinta el progreso: la lectura bloquea la
    #     ventana un momento
    def _leer_toma(self) -> None:
        kv = self.KV
        serie: biboecf.OECF = self.OECF                         # type: ignore
        barra: ctk.CTkProgressBar = self.barra_serie            # type: ignore
        val_serie: ctk.CTkLabel = self.val_serie                # type: ignore
        self.tarea = None
        if serie.esRead:
            self._fin_serie()
            return

        total = len(serie.raws)
        self.Poner(val_serie, kv.TXT_LEYENDO, n=len(serie.tomas) + 1,
                   total=total)
        self.update_idletasks()

        next(self.lectura)                                      # type: ignore
        barra.set(len(serie.tomas) / total)

        # --- after (y no un bucle): entre imagen e imagen, la ventana
        #     atiende al ratón y se repinta
        self.tarea = self.after(kv.PAUSA_LECTURA, self._leer_toma)

    #
    # --- Calcula la zona de cada imagen y muestra el resumen.
    #     PROVISIONAL: la referencia es la primera imagen leída (sin
    #     tapadas todavía)
    def _fin_serie(self) -> None:
        kv = self.KV
        barra: ctk.CTkProgressBar = self.barra_serie            # type: ignore
        val_serie: ctk.CTkLabel = self.val_serie                # type: ignore
        val_copia: ctk.CTkLabel = self.val_copia                # type: ignore
        barra.pack_forget()

        # --- La serie, leída y repartida por OECF: el tercioEV de
        #     cada archivo, en su orden (None si no se leyó)
        serie: biboecf.OECF = self.OECF                         # type: ignore
        reads = [t for t in serie.tercioEVs if t is not None]
        if not reads:
            self.leyendo = False
            self.ActivarCarpeta()
            self.Poner(val_serie, kv.TXT_NO_READ)
            self.Ajustar()
            return

        # --- Rango «de … a …»: solo las tomas que van a la rejilla
        #     (sin tapadas, balances de cámara ni Z-V iniciales de más)
        en_rejilla = [t for t, va in zip(serie.tercioEVs, serie.enRejilla)
                      if va and (t is not None)]

        desde = biboecf.texto_zona(min(en_rejilla))
        hasta = biboecf.texto_zona(max(en_rejilla))
        total = len(serie.raws)
        self.Poner(val_serie, partial(self._texto_resumen, total, desde,
                                      hasta, total - len(reads)))
        self._mostrar_rejilla()
        self.Ajustar()

        # --- A copiar las tomas que sirven a la carpeta OECF, una
        #     cada vez, con su progreso bajo la rejilla. Los botones
        #     siguen inactivos hasta el final
        self.copia = serie.Copiar()
        barra.set(0)
        barra.pack(fill="x", pady=(kv.MARGEN, 0))
        val_copia.pack()
        self.Ajustar()
        self._copiar_toma()

    #
    # --- Resumen de la serie en dos trozos (el segundo, solo si falta
    #     alguna): se rehace entero al cambiar de idioma
    def _texto_resumen(self, total: int, desde: str, hasta: str,
                       sin_leer: int) -> str:
        kv = self.KV
        texto = K.tr_n(kv.TXT_RESUMEN, total).format(
            total=total, desde=desde, hasta=hasta)
        if sin_leer:
            texto += K.tr(kv.TXT_SIN_LEER).format(n=sin_leer)
        return texto

    #
    # --- Copia la siguiente toma (la copia OECF) y se vuelve a
    #     programar. Antes de copiar se pinta el progreso: la copia
    #     bloquea la ventana un momento
    def _copiar_toma(self) -> None:
        kv = self.KV
        barra: ctk.CTkProgressBar = self.barra_serie            # type: ignore
        val_copia: ctk.CTkLabel = self.val_copia                # type: ignore
        self.tarea = None
        paso = next(self.copia, None)                           # type: ignore
        if paso is None:
            self._fin_copia()
            return

        hechas, total = paso
        barra.set((hechas / total) if total else 1)
        if hechas < total:
            self.Poner(val_copia, kv.TXT_COPIANDO,
                       n=hechas + 1, total=total)
            self.update_idletasks()
        self.tarea = self.after(kv.PAUSA_COPIA, self._copiar_toma)

    #
    # --- Con las copias hechas, allí mismo los datos de la
    #     preparación (JSON) y las incidencias. Analizar, solo si la
    #     serie sirve y se copió
    def _fin_copia(self) -> None:
        kv = self.KV
        serie: biboecf.OECF = self.OECF                         # type: ignore
        barra: ctk.CTkProgressBar = self.barra_serie            # type: ignore
        val_copia: ctk.CTkLabel = self.val_copia                # type: ignore
        btn_analizar: ctk.CTkButton = self.btn_analizar     # type: ignore
        barra.pack_forget()

        # --- Con las copias hechas, el JSON y las incidencias. Si la
        #     copia falló, se avisa donde iba su progreso
        if not serie.copias:
            self.Poner(val_copia, kv.TXT_NO_COPIADO,
                       error=serie.errorCopia or "")
        else:
            val_copia.pack_forget()
            biboecf.grabar_json(serie, K.NOMBRE, K.version)
            self.GrabarIncidencias()
        btn_analizar.configure(
            state="normal" if (serie.esAnalizable and serie.copias)
            else "disabled")
        self.leyendo = False
        self.ActivarCarpeta()
        self.Ajustar()

    #
    # --- Rejilla de zonas y tercios y su pie: el resumen, el botón
    #     de incidencias, que dice cuántas hay y las muestra todas (sin
    #     ninguna, queda inactivo y lo dice), y Analizar, activo solo
    #     si la serie sirve
    def _mostrar_rejilla(self) -> None:
        kv = self.KV
        serie: biboecf.OECF = self.OECF                         # type: ignore
        rejilla: Rejilla = self.rejilla                         # type: ignore
        val_rejilla: ctk.CTkLabel = self.val_rejilla            # type: ignore
        rejilla.mostrar(serie)
        self.Poner(val_rejilla, partial(self._texto_rejilla, serie))
        rejilla.pack(fill="x", pady=(kv.MARGEN, 0))
        rejilla.dibujar()

        self.incidencias = partial(Rejilla.incidencias, serie)
        self.ContarIncidencias()

    #
    # --- Resumen bajo la rejilla: zonas, balances y tapadas
    def _texto_rejilla(self, serie: biboecf.OECF) -> str:
        return "\n".join((
            Rejilla.resumen(serie),
            self.KV.SEP_RESUMEN.join((
                Rejilla.linea_balance(serie.balancePersonalizado),
                Rejilla.linea_balances(len(serie.WBs)))),
            Rejilla.linea_tapadas(len(serie.tapadas))))

    #
    def caja_psd(self, OECF: biboecf.OECF) -> None:
        """
        Caja Lámina: la crea Analizar. Mide las teselas de la Z-V
        (OECF.Seleccionar): sin tarjeta gris, lo dice y no hay más. Con
        tarjeta, dos secciones a todo el ancho: el recorte del paño (si lo hay;
        si no, por qué, y solo se generará el Excel) y, a la derecha, los
        tamaños, la ventanita de mensajes (las teselas rechazadas y, al
        generar, el proceso) y Generar: mide la serie y escribe el JSON, el
        libro y, con paño, la lámina.
        """
        kv = self.KV

        # --- La caja, con el aviso mientras se mide: la medida bloquea la
        #     ventana un momento
        interior = self.CrearCaja(kv.TXT_FASE_PSD, self.ReiniciarPsd)
        aviso = ctk.CTkLabel(interior, text="")
        aviso.pack()
        self.Poner(aviso, kv.TXT_BUSCANDO_TELA)
        self.Traducir()
        self.Ajustar()
        self.update_idletasks()

        # --- Teselas de la Z-V: paño y tarjeta. Hay incidencias nuevas
        OECF.Seleccionar()
        self.ContarIncidencias()
        ventana, select = OECF.tela, OECF.select
        if (select is None) or (not select.hayTarjeta):
            self.Poner(aviso, Rejilla.KR.TXT_SIN_TARJETA)
            self.Traducir()
            self.Ajustar()
            return

        # --- Dos secciones: el recorte (si hay paño; si no, el porqué
        #     queda en el aviso) y una línea como la del marco
        grupo = ctk.CTkFrame(interior, fg_color="transparent")
        grupo.pack(fill="x")
        hay_tela = isinstance(ventana, biboecf.Ventana)
        if hay_tela:
            aviso.pack_forget()
            self.ventana_tela = ventana
            self.imagen_zv = biboecf.revelar(
                OECF.zonasCopia[0])                             # type: ignore
            fondo = self._apply_appearance_mode(
                ctk.ThemeManager.theme["CTk"]["fg_color"])
            self.val_recorte = tk.Label(grupo, bg=fondo, borderwidth=0)
            self.val_recorte.pack(side="left")
            ctk.CTkFrame(grupo, width=kv.GROSOR_MARCO, corner_radius=0,
                         fg_color=ctk.ThemeManager.theme["CTkFrame"]
                         ["border_color"]).pack(side="left", fill="y",
                                                padx=kv.MARGEN)
        else:
            self.Poner(aviso, kv.TXT_PROBLEMA_TELA[ventana])    # type: ignore

        # --- A la derecha: arriba, los tamaños (si hay paño; los que no
        #     caben, inactivos) y la ventanita de mensajes; abajo, Generar
        derecha = ctk.CTkFrame(grupo, fg_color="transparent")
        derecha.pack(side="left", fill="both", expand=True)
        arriba = ctk.CTkFrame(derecha, fg_color="transparent")
        arriba.pack(fill="both", expand=True)
        if hay_tela:
            sizes = ctk.CTkFrame(arriba, fg_color="transparent")
            sizes.pack(side="left", fill="y", padx=(0, kv.MARGEN))
            self.ApuntarTexto(ctk.CTkLabel(sizes),
                              kv.TXT_MEDIDA).pack(anchor="w")
            caben = biboecf.factores(ventana)                   # type: ignore
            self.factor = ctk.IntVar(value=biboecf.KTE.FACTORES[0])
            for factor in biboecf.KTE.FACTORES:
                radio = ctk.CTkRadioButton(
                    sizes, variable=self.factor, value=factor,
                    width=kv.ANCHO_CONTENIDO,
                    command=self._mostrar_recorte,
                    state="normal" if (factor in caben) else "disabled")
                self.ApuntarTexto(radio, kv.TXT_PORCENTAJE,
                                  p=biboecf.porcentaje(factor))
                radio.pack(anchor="w", pady=(kv.MARGEN, 0))
            self._mostrar_recorte()

        marco = ctk.CTkFrame(arriba, fg_color="transparent",
                             border_width=kv.GROSOR_MARCO)
        marco.pack(side="left", fill="both", expand=True)
        self.val_mensajes = ctk.CTkLabel(marco, text="", anchor="nw",
                                         justify="left",
                                         wraplength=kv.ANCHO_MENSAJES)
        self.val_mensajes.pack(fill="both", expand=True, padx=kv.MARGEN,
                               pady=kv.MARGEN)
        self.val_mensajes.bind(kv.TK_CAMBIO_MEDIDA, self._ajustar_mensajes)

        # --- Primeros mensajes: las teselas de tarjeta rechazadas y sus
        #     avisos, uno por causa (los mismos textos que en las
        #     incidencias)
        for inc in biboecf.incidencias(OECF):
            if inc.codigo in kv.INCIDENCIAS_TESELAS:
                self.Mensaje(partial(Rejilla.texto_incidencia, inc, OECF))

        # --- Abajo, Generar y, a su izquierda, Abrir resultados: se trae
        #     aquí (el de la Serie queda oculto mientras esté esta caja)
        botones = ctk.CTkFrame(derecha, fg_color="transparent")
        botones.pack(side="bottom", anchor="e", pady=(kv.MARGEN, 0))
        btn_generar = self.btn_generar = ctk.CTkButton(
            botones, command=self._generar)
        self.ApuntarTexto(btn_generar, kv.TXT_GENERAR)
        btn_generar.pack(side="right")
        self.ResultadosEnSerie(False)
        self.btn_resultados = ctk.CTkButton(
            botones, command=self.AbrirResultados, state="disabled")
        self.ApuntarTexto(self.btn_resultados, kv.TXT_ABRIR_RESULTADOS)
        self.btn_resultados.pack(side="right", padx=(0, kv.MARGEN))
        self.ActivarCarpeta()
        self.Traducir()
        self.Ajustar()

    #
    # --- Rehace el recorte con el tamaño elegido
    def _mostrar_recorte(self) -> None:
        kv = self.KV
        trozo = biboecf.recorte(self.imagen_zv,                 # type: ignore
                                self.ventana_tela,              # type: ignore
                                self.factor.get())              # type: ignore
        alto, ancho = trozo.shape[:2]
        self.foto_recorte = tk.PhotoImage(
            data=(kv.CABECERA_PPM.format(ancho=ancho, alto=alto).encode()
                  + trozo.tobytes()), format=kv.FORMATO_PPM)
        self.val_recorte.configure(                             # type: ignore
            image=self.foto_recorte)

    #
    # --- Generar: mide la serie (una toma cada vez, con el progreso en
    #     la ventanita) y, al terminar, el JSON, el libro y, con paño,
    #     la lámina. Sin todas las copias no se puede medir: se rehace el
    #     informe con el análisis guardado (ver _rehacer_informe).
    #     Mientras, Generar y Preparar inactivos
    def _generar(self) -> None:
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        btn_generar: ctk.CTkButton = self.btn_generar       # type: ignore
        btn_generar.configure(state="disabled")
        self.escritos = []
        self.leyendo = True
        self.ActivarCarpeta()
        if not oecf.copiasEnSitio:
            self._rehacer_informe()
            return
        self.medida = oecf.Medir()
        self.Mensaje(lambda: "")
        self._medir_toma()

    #
    # --- Generar sin todas las copias (Tony, 2026-10-22): no se puede
    #     volver a medir, así que se avisa y se escribe el informe con el
    #     análisis guardado en el JSON. El JSON no se vuelve a grabar:
    #     pondría el revelado a null. La línea vacía es la que sustituye
    #     el libro, para que no pise el aviso
    def _rehacer_informe(self) -> None:
        kv = self.KV
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        review = biboecf.leer_review(oecf)
        if review is None:
            raise ValueError(kv.ERROR_ANALISIS_ILEGIBLE)
        self.Mensaje(partial(self._componer, kv.TXT_SIN_CONTROL))
        self.Mensaje(lambda: "")
        self._escribir_informe(review)

    #
    # --- Mide la siguiente toma y se vuelve a programar (con after:
    #     entre toma y toma, la ventana atiende al ratón y se repinta)
    def _medir_toma(self) -> None:
        kv = self.KV
        self.tarea = None
        hechas, total = next(self.medida)                       # type: ignore
        if hechas < total:
            self.Mensaje(partial(self._componer, kv.TXT_MIDIENDO,
                                 n=hechas + 1, total=total), sustituir=True)
            self.update_idletasks()
            self.tarea = self.after(kv.PAUSA_LECTURA, self._medir_toma)
            return
        self._fin_medida()

    #
    # --- Carpeta ANALISIS de la serie, creada si no está (en una serie
    #     ya preparada se puede haber borrado): ahí van el libro, la ficha
    #     y las láminas. Si no se puede crear, lo dirá quien escriba
    @staticmethod
    def _carpeta_analisis(oecf: biboecf.OECF) -> Path:
        try:
            oecf.carpetaAnalisis.mkdir(exist_ok=True)
        except OSError:
            pass
        return oecf.carpetaAnalisis

    #
    # --- Con la serie medida: el JSON (ya con el análisis) y el informe
    def _fin_medida(self) -> None:
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        self.medida = None
        biboecf.grabar_json(oecf, K.NOMBRE, K.version)
        self._escribir_informe(oecf.review)                     # type: ignore

    #
    # --- El informe desde un análisis (el recién medido): el libro, los
    #     resultados en el JSON, la ficha y, con paño, la lámina
    def _escribir_informe(self, review: biboecf.Review) -> None:
        kv = self.KV
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        ruta = (self._carpeta_analisis(oecf)
                / f"{K.NOMBRE}{kv.EXTENSION_EXCEL}")
        # --- Cualquier otro fallo del libro (un dato que no se puede
        #     escribir…) también se dice, con su error, y se sigue
        error = ""
        excel = None
        try:
            excel = biboecf.Excel(ruta, textos_excel(), review)
            excel.escribir()
            self.escritos.append(ruta.name)
            texto = kv.TXT_EXCEL
        except OSError:
            texto = kv.TXT_SIN_EXCEL
        except Exception as e:
            texto = kv.TXT_ERROR_EXCEL
            error = f"{type(e).__name__}: {e}"
        self.Mensaje(partial(self._componer, texto, archivo=ruta.name,
                             error=error), sustituir=True)

        # --- Y, con lo que calculó el libro, los resultados en el JSON
        #     (para FotoEstación) y la ficha PDF
        if excel is not None:
            biboecf.grabar_resultados(oecf.carpeta, excel.resultados())
            ficha, archivo, fallo = self.EscribirFicha(
                excel, oecf.carpetaAnalisis)
            self.Mensaje(partial(self._componer, ficha, archivo=archivo,
                                 error=fallo))

        # --- Tras medir puede haber incidencias nuevas (la luz que
        #     cambió): al botón y, esa, también a la ventanita
        self.ContarIncidencias()
        luz = next((inc for inc in biboecf.incidencias(oecf)
                    if inc.codigo == biboecf.KI.LUZ_CAMBIO), None)
        if luz is not None:
            self.Mensaje(partial(Rejilla.texto_incidencia, luz, oecf))

        # --- Con paño, la lámina: al 100 % y, si se eligió otro
        #     tamaño, también en ese. Sin paño, se acaba aquí
        if self.ventana_tela is None:
            self._terminar_generar()
            return
        factores = tuple(sorted({biboecf.KTE.FACTORES[0],
                                 self.factor.get()}))           # type: ignore
        zonas = {oecf.NombreZona(t): copia for t, copia
                 in oecf.RellenarTercios(oecf.zonasCopia).items()}
        self.psd = biboecf.Psd(
            biboecf.RUTA_PLANTILLA, zonas, self.ventana_tela, factores,
            (review.alto, review.ancho),
            self.TextosCartela(review, oecf.carpeta))
        self.revelado = self.psd.Revelar()
        self.Mensaje(lambda: "")
        self._revelar_zona()

    #
    # --- Revela la siguiente zona de la lámina y se vuelve a programar
    #     (con after, como la medida); al terminar, las escribe
    def _revelar_zona(self) -> None:
        kv = self.KV
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        self.tarea = None
        hechas, total = next(self.revelado)                     # type: ignore
        if hechas < total:
            self.Mensaje(partial(self._componer, kv.TXT_REVELANDO,
                                 n=hechas + 1, total=total), sustituir=True)
            self.update_idletasks()
            self.tarea = self.after(kv.PAUSA_LECTURA, self._revelar_zona)
            return
        self.revelado = None
        psd: biboecf.Psd = self.psd                             # type: ignore
        escritas = []
        for factor in psd.factores:
            nombre = psd.nombre(factor)
            self.Mensaje(partial(self._componer, kv.TXT_ESCRIBIENDO,
                                 archivo=nombre), sustituir=True)
            self.update_idletasks()
            try:
                psd.Escribir(factor, oecf.carpetaAnalisis / nombre)
                escritas.append(nombre)
                self.escritos.append(nombre)
            except OSError:
                self.Mensaje(partial(self._componer, kv.TXT_SIN_PSD,
                                     archivo=nombre))
        if escritas:
            self.Mensaje(partial(self._componer, kv.TXT_PSD,
                                 archivos=kv.SEP_ARCHIVOS.join(escritas)),
                         sustituir=True)
        self._terminar_generar()

    #
    # --- Fin de Generar (con láminas o sin ellas): lo dice en la
    #     ventanita y Generar y Preparar, otra vez activos
    def _terminar_generar(self) -> None:
        kv = self.KV
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        btn_generar: ctk.CTkButton = self.btn_generar       # type: ignore
        self.psd = None
        self.Mensaje(self.TextoFinalizado)
        btn_generar.configure(state="normal")
        self.leyendo = False
        self.ActivarCarpeta()

        # --- Con exportaciones del revelador ya en la carpeta y aún sin
        #     medir (el JSON no tiene su revelado: queda a null al medir
        #     la serie y se conserva al rehacerla con el análisis
        #     guardado), se pregunta si medirlas ahora (si no, siguen ahí
        #     para Analizar revelado)
        n = len(oecf.exportaciones)
        guardado = biboecf.leer_review(oecf) if n else None
        sin_medir = (guardado is None) or (not guardado.revelador)
        if n and sin_medir and self.Confirmar(
                kv.TXT_TITULO_TIFF_YA,
                [K.tr_n(kv.TXT_PREGUNTA_TIFF_YA, n).format(n=n)],
                kv.TXT_MEDIR):
            self.AnalizarRevelado()

    #
    def Mensaje(self, linea: Callable[[], str],
                sustituir: bool = False) -> None:
        """
        Añade una línea a la ventanita de mensajes de la caja Lámina, o
        sustituye la última (el progreso). linea: cómo se compone (para
        rehacerla al cambiar de idioma)
        """
        if sustituir and self.lineas:
            self.lineas[-1] = linea
        else:
            self.lineas.append(linea)
        self.Poner(self.val_mensajes,                           # type: ignore
                   self._texto_mensajes)

    #
    # --- La ventanita cambió de ancho: sus líneas se cortan a ese ancho
    #     (solo si cambia: así no se vuelve a llamar sin fin)
    def _ajustar_mensajes(self, evento: tk.Event) -> None:
        mensajes: ctk.CTkLabel = self.val_mensajes              # type: ignore
        if mensajes.cget("wraplength") != evento.width:
            mensajes.configure(wraplength=evento.width)

    #
    # --- Las líneas de la ventanita, cada una en el idioma activo
    def _texto_mensajes(self) -> str:
        return self.KV.SEP_MENSAJES.join(
            componer() for componer in self.lineas)

    #
    def EscribirFicha(self, excel: biboecf.Excel,
                      carpeta: Path) -> tuple[dict, str, str]:
        """
        Escribe la ficha PDF de la cámara en la carpeta, desde el libro
        ya calculado. Devuelve el texto del resultado (sin traducir: se
        traduce al mostrarlo), el nombre del archivo y el error, si lo
        hubo. Si la escribe, la apunta en escritos.
        """
        kv = self.KV
        ruta = carpeta / f"{K.NOMBRE}{kv.EXTENSION_FICHA}"
        try:
            biboecf.Ficha(ruta, textos_excel(), excel).escribir()
        except OSError:
            return kv.TXT_SIN_FICHA, ruta.name, ""
        except Exception as e:
            return kv.TXT_ERROR_FICHA, ruta.name, f"{type(e).__name__}: {e}"
        self.escritos.append(ruta.name)
        return kv.TXT_FICHA, ruta.name, ""

    #
    def ErrorInesperado(self, tipo: type, valor: BaseException,
                        traza: TracebackType | None) -> None:
        """
        Error que saltó en un botón o en una tarea programada y nadie
        recogió (report_callback_exception de Tk): lo escribe en la
        terminal, libera la app (para la tarea en marcha y reactiva los
        botones de la carpeta) y lo dice en una ventana.
        """
        traceback.print_exception(tipo, valor, traza)
        try:
            if self.tarea is not None:
                self.after_cancel(self.tarea)
            self.tarea = None
            self.leyendo = False
            self.ActivarCarpeta()
        except Exception:
            traceback.print_exc()
        self.MostrarError(f"{tipo.__name__}: {valor}")

    #
    def MostrarError(self, error: str) -> None:
        """ Ventana de error con el texto del error, traducida. """
        kv = self.KV
        messagebox.showerror(K.tr(kv.TXT_TITULO_ERROR),
                             K.tr(kv.TXT_ERROR_INESPERADO).format(
                                 error=error), parent=self)

    #
    def TextosCartela(self, review: biboecf.Review,
                      carpeta: Path) -> tuple[str, ...]:
        """
        Líneas del cajetín de la lámina, de arriba abajo y traducidas: la
        cámara, la latitud de texturas recomendada (de los resultados del
        JSON de la carpeta OECF), la fecha de las tomas (la de la ZV) y el
        soporte, para escribirlo a mano.
        """
        kv = self.KV
        constantes = {nombre: valor
                      for nombre, valor, _ in biboecf.KXL.CONSTANTES}
        zona_zv = constantes[biboecf.KXL.C_ZONA_ZV]
        por_zona = constantes[biboecf.KXL.C_TERCIO_POR_ZONA]
        resultados = biboecf.leer_resultados(carpeta) or {}
        texturas = resultados.get(biboecf.KXL.J_TEXTURAS) or {}
        recomendada = texturas.get(biboecf.KXL.T_RECOMENDADA) or {}
        sombras, luces, zonas = (recomendada.get(clave)
                                 for clave in biboecf.KXL.TEXTURAS_JSON)
        if (sombras is None) or (luces is None) or (zonas is None):
            latitud = K.tr(kv.TXT_CARTELA_SIN_LATITUD)
        else:
            latitud = K.tr(kv.TXT_CARTELA_LATITUD).format(
                desde=biboecf.Excel.nombre_zona(
                    round((sombras - zona_zv) * por_zona)),
                hasta=biboecf.Excel.nombre_zona(
                    round((luces - zona_zv) * por_zona)),
                zonas=biboecf.Excel.tercios_texto(zonas))
        fecha = ""
        if review.fecha:
            dia = datetime.fromisoformat(review.fecha)
            fecha = kv.FORMATO_FECHA_CARTELA.format(
                dia=dia.day, mes=K.tr(kv.TXT_MESES)[dia.month - 1],
                year=dia.year)
        return (K.tr(kv.TXT_CARTELA_CAM).format(cam=review.cam),
                latitud, K.tr(kv.TXT_CARTELA_FECHA).format(fecha=fecha),
                K.tr(kv.TXT_CARTELA_SOPORTE))

    #
    def TextoFinalizado(self) -> str:
        """
        Línea final de una tanda (Generar o Analizar revelado):
        «Finalizado» y los archivos que escribió (libro, ficha y
        láminas), traducida.
        """
        kv = self.KV
        if not self.escritos:
            return K.tr(kv.TXT_FINALIZADO)
        return K.tr(kv.TXT_FINALIZADO_ARCHIVOS).format(
            archivos=kv.SEP_ARCHIVOS.join(self.escritos))

    #
    def ContarIncidencias(self) -> None:
        """
        Pone en el botón de incidencias cuántas hay (o que no hay), lo activa
        si las hay y rehace su ventana si está abierta; y las graba. En una
        serie ya preparada no hay botón (ni rejilla): solo las graba.
        """
        btn = self.btn_incidencias
        if (btn is None) and (not self.preparada):
            return
        if btn is not None:
            n = len(self.incidencias())
            if n:
                self.Poner(btn, self.KV.TXT_INCIDENCIAS, n=n)
            else:
                self.Poner(btn, self.KV.TXT_SIN_INCIDENCIAS)
            btn.configure(state="normal" if n else "disabled")
            self.rellenar_incidencias()

        # --- También sin botón (sin rejilla: una serie ya preparada)
        self.GrabarIncidencias()

    #
    def GrabarIncidencias(self) -> None:
        """
        Graba las incidencias, como en su ventana (o que no hay), en
        incidencias.txt de la carpeta ANALISIS, en el idioma de la ventana:
        es para el usuario, que solo busca ahí (CTRL es interna). Se rehace
        cada vez que cambian (Analizar y Generar añaden). Sin copias (la
        carpeta OECF no está lista), nada.
        """
        kv = self.KV
        oecf = self.OECF
        if (oecf is None) or (not oecf.copias):
            return
        incidencias = self.incidencias() or [K.tr(kv.TXT_SIN_INCIDENCIAS)]
        try:
            oecf.carpetaAnalisis.mkdir(exist_ok=True)
            (oecf.carpetaAnalisis / kv.ARCHIVO_INCIDENCIAS).write_text(
                kv.SEP_INCIDENCIAS.join(incidencias) + kv.SEP_INCIDENCIAS,
                encoding="utf-8")
        except OSError:
            pass

    #
    def incidencias_abiertas(self) -> bool:
        """ ¿Está abierta la ventana de incidencias? """
        return ((self.ventana_incidencias is not None)
                and bool(self.ventana_incidencias.winfo_exists()))

    #
    def rellenar_incidencias(self) -> None:
        """
        Pone las incidencias en su ventana, en el idioma activo. Solo lectura:
        se desbloquea un momento para escribir.
        """
        if not self.incidencias_abiertas():
            return

        texto = self.texto_incidencias
        self.ventana_incidencias.title(                         # type: ignore
            K.tr(self.KV.TXT_TITULO_INCIDENCIAS))
        texto.configure(state="normal")                         # type: ignore
        texto.delete("1.0", "end")                              # type: ignore
        texto.insert("1.0", self.KV.SEP_INCIDENCIAS.join(       # type: ignore
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

        # --- Cuerpo: el marco que contiene todas las cajas, dentro de un
        #     lienzo que se desplaza si no cabe en la pantalla, con su
        #     barra (solo a la vista entonces) y el número de su ventana en
        #     el lienzo (para estirarlo a lo ancho)
        self.cuerpo: ctk.CTkFrame
        self.lienzo: tk.Canvas
        self.barra: ctk.CTkScrollbar
        self.id_cuerpo: int

        # --- Elementos con texto traducible: cada uno guarda cómo se
        #     compone su texto, para rehacerlo al cambiar de idioma
        self._textos: dict[ctk.CTkBaseClass, Callable[[], str]] = {}

        # --- Caja Carpeta (caja_carpeta): los botones Preparar, Analizar,
        #     Analizar revelado y Abrir resultados (los enseña, activa y
        #     desactiva ActivarCarpeta) y la variable de la casilla
        self.botones_carpeta: ctk.CTkFrame
        self.btn_preparar: ctk.CTkButton
        self.btn_analizar_carpeta: ctk.CTkButton
        self.btn_revelado: ctk.CTkButton
        self.btn_abrir_carpeta: ctk.CTkButton
        self.ruta: ctk.StringVar

        # --- Explorador de Linux abierto al elegir carpeta (caja_carpeta):
        #     solo uno a la vez; None si no hay ninguno
        self.explorador: subprocess.Popen | None = None

        # --- Respuesta de la confirmación de Preparar (ConfirmarPreparar)
        self.confirmado: bool = False
        self.dialogo_confirmar: ctk.CTkToplevel | None = None

        # --- Caja Serie (caja_serie): Abrir resultados, en el pie de la
        #     rejilla (None sin caja Serie). Con Generar a la vista, el que
        #     vale es el de la caja Lámina, a su lado, y el de la Serie se
        #     guarda oculto. btn_resultados es el que se ve (lo activa
        #     ActivarCarpeta)
        self.btn_resultados: ctk.CTkButton | None
        self.btn_resultados_serie: ctk.CTkButton | None

        # --- Caja Ayuda (caja_ayuda): el botón de nueva versión, oculto
        #     hasta saber que la hay, y el grupo de Idioma, para ponerlo
        #     delante de él. La versión publicada la escribe el hilo de
        #     ComprobarVersion y la lee MostrarVersion: None hasta saberla
        #     (o si no se pudo) y si ya se comprobó
        self.btn_version: ctk.CTkButton
        self.grupo_idioma: ctk.CTkFrame
        self.version_publicada: str | None = None
        self.version_comprobada: bool = False

        # --- Error del hilo de ComprobarVersion que no es de red (lo
        #     enseña MostrarVersion: el hilo no puede tocar la ventana)
        self.error_version: str | None = None

        # --- Imágenes de los iconos (SOicon y caja_cabecera): se guardan
        #     para que Python no las borre, o el icono desaparece
        self.icono: tk.PhotoImage
        self.icono_cabecera: tk.PhotoImage

        # --- Caja Cámara (ReiniciarCam): la serie de la carpeta (fase 1),
        #     para Preparar; cuántas cajas hay hasta la de la cámara
        #     (incluida), porque las de encima se quitan en cada preparación;
        #     y las etiquetas de sus valores
        self.OECF: biboecf.OECF | None
        self.carpetaVista: Path | None
        self.preparada: bool
        self.propias_cam: int
        self.val_archivo: ctk.CTkLabel | None
        self.val_bits: ctk.CTkLabel | None
        self.val_exp: ctk.CTkLabel | None
        self.val_fecha: ctk.CTkLabel | None
        self.val_modelo: ctk.CTkLabel | None

        # --- Caja Serie (ReiniciarSerie), lo que se usa desde fuera de
        #     ella: la copia en marcha (OECF.Copiar), cómo se componen las
        #     incidencias, la lectura en marcha de la serie (OECF.Leer), si
        #     se está leyendo o copiando, la rejilla (se redibuja al
        #     traducir), la siguiente lectura o copia pendiente y la
        #     ventana de incidencias con su texto
        self.copia: Iterator[tuple[int, int]] | None
        self.incidencias: Callable[[], list[str]]
        self.lectura: Iterator[int] | None
        self.leyendo: bool
        self.rejilla: Rejilla | None
        self.tarea: str | None
        self.texto_incidencias: ctk.CTkTextbox | None
        self.ventana_incidencias: ctk.CTkToplevel | None

        # --- Cuántas cajas hay hasta la Serie (incluida): Analizar quita
        #     las de encima; y el botón de incidencias (ContarIncidencias)
        self.propias_serie: int
        self.btn_incidencias: ctk.CTkButton | None

        # --- Lo demás de la caja Serie que usan sus pasos (_leer_toma,
        #     _fin_serie, _copiar_toma, _fin_copia, _mostrar_rejilla): el
        #     resumen, la barra de progreso, la línea de la copia, el
        #     resumen bajo la rejilla y el botón Analizar
        self.val_serie: ctk.CTkLabel | None
        self.barra_serie: ctk.CTkProgressBar | None
        self.val_copia: ctk.CTkLabel | None
        self.val_rejilla: ctk.CTkLabel | None
        self.btn_analizar: ctk.CTkButton | None

        # --- Caja Lámina (ReiniciarPsd): la Z-V revelada (para el
        #     recorte), la ventana del paño, el tamaño elegido (divisor),
        #     la etiqueta del recorte y su imagen (se guarda: si no, Python
        #     la borra)
        self.imagen_zv: np.ndarray | None
        self.ventana_tela: biboecf.Ventana | None
        self.factor: ctk.IntVar | None
        self.val_recorte: tk.Label | None
        self.foto_recorte: tk.PhotoImage | None

        # --- Caja Revelado (ReiniciarRevelado; la crea Analizar revelado):
        #     su interior y sus dos líneas (la medida y la lámina), el
        #     análisis (del JSON), las exportaciones que faltan por medir,
        #     lo medido en cada zona ({tercioEV: L* o por qué no}) y la
        #     lámina desde las TIFF con su lectura en marcha
        self.caja_revelado: ctk.CTkFrame | None
        self.val_revelado: ctk.CTkLabel | None
        self.val_psd_tiff: ctk.CTkLabel | None
        self.review_revelado: biboecf.Review | None
        self.tiff_pendientes: list[tuple[int, Path]]
        self.tiff_medidos: dict[int, biboecf.MedidaTiff]
        self.psd_tiff: biboecf.Psd | None
        self.revelado_tiff: Iterator[tuple[int, int]] | None

        # --- La ventanita de mensajes de la caja Lámina y cómo se compone
        #     cada línea (para rehacerla al cambiar de idioma)
        self.val_mensajes: ctk.CTkLabel | None
        self.lineas: list[Callable[[], str]]

        # --- La medida en marcha (OECF.Medir), al pulsar Generar, y la
        #     lámina con su revelado en marcha (Psd.Revelar)
        self.medida: Iterator[tuple[int, int]] | None
        self.psd: biboecf.Psd | None
        self.revelado: Iterator[tuple[int, int]] | None

        # --- El botón Generar de la caja Lámina (lo desactivan y activan
        #     _generar y _terminar_generar)
        self.btn_generar: ctk.CTkButton | None

        # --- Archivos escritos en la tanda en marcha (Generar o Analizar
        #     revelado: libro, ficha y láminas), para el resumen final
        self.escritos: list[str] = []

        # endregion Variables de instancia

        # --- Ningún error silencioso: el que salte en un botón o en una
        #     tarea programada (after) y nadie recoja, lo dice una ventana
        #     (y la terminal), y la app queda libre para seguir
        self.report_callback_exception = self.ErrorInesperado

        # --- Valores iniciales de las cajas Cámara, Serie y Lámina
        self.ReiniciarCam()
        self.ReiniciarSerie()
        self.ReiniciarPsd()
        self.ReiniciarRevelado()

        # --- Cuerpo, dentro del lienzo desplazable (ver Ajustar). El
        #     lienzo pone el margen de arriba y el de los lados; cada fila
        #     pone el suyo por debajo. La rueda del ratón desplaza estando
        #     en cualquier punto de la ventana
        fondo = self._apply_appearance_mode(
            ctk.ThemeManager.theme["CTk"]["fg_color"])
        self.barra = ctk.CTkScrollbar(self)
        self.lienzo = tk.Canvas(self, bg=fondo, highlightthickness=0,
                                yscrollcommand=self.barra.set)
        self.barra.configure(command=self.lienzo.yview)
        self.lienzo.pack(side="left", fill="both", expand=True,
                         padx=self.KV.MARGEN, pady=(self.KV.MARGEN, 0))
        self.cuerpo = ctk.CTkFrame(self.lienzo, fg_color="transparent")
        self.id_cuerpo = self.lienzo.create_window(0, 0, window=self.cuerpo,
                                                   anchor="nw")
        self.lienzo.bind(self.KV.TK_CAMBIO_MEDIDA, self.EstirarCuerpo)
        for evento in self.KV.TK_RUEDA:
            self.bind_all(evento, self.Rueda)

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

        # --- Versión publicada: se pregunta a GitHub en un hilo, para no
        #     frenar la ventana, y se mira cada poco si ya respondió
        threading.Thread(target=self.ComprobarVersion, daemon=True).start()
        self.after(self.KV.PAUSA_VERSION, self.MostrarVersion)

    #
    def ReiniciarCam(self) -> None:
        """
        Valores iniciales de las variables de la caja Cámara (se declaran en el
        __init__): al arrancar y al quitar la caja.
        """
        self.OECF = None
        self.carpetaVista = None
        self.preparada = False
        self.propias_cam = 0
        self.val_archivo = None
        self.val_bits = None
        self.val_exp = None
        self.val_fecha = None
        self.val_modelo = None

    #
    def ReiniciarSerie(self) -> None:
        """
        Valores iniciales de las variables de la caja Serie (se declaran en el
        __init__): al arrancar y al quitar la caja.
        """
        self.copia = None
        self.incidencias = list
        self.lectura = None
        self.leyendo = False
        self.rejilla = None
        self.btn_resultados = None
        self.btn_resultados_serie = None
        self.tarea = None
        self.texto_incidencias = None
        self.ventana_incidencias = None
        self.propias_serie = 0
        self.btn_incidencias = None
        self.val_serie = None
        self.barra_serie = None
        self.val_copia = None
        self.val_rejilla = None
        self.btn_analizar = None

    #
    def ReiniciarRevelado(self) -> None:
        """
        Valores iniciales de las variables de la caja Revelado (se declaran en
        el __init__): al arrancar y al quitar la caja.
        """
        self.caja_revelado = None
        self.val_revelado = None
        self.val_psd_tiff = None
        self.review_revelado = None
        self.tiff_pendientes = []
        self.tiff_medidos = {}
        self.psd_tiff = None
        self.revelado_tiff = None

    #
    def ReiniciarPsd(self) -> None:
        """
        Valores iniciales de las variables de la caja Lámina (se declaran en el
        __init__): al arrancar y al quitar la caja.
        """
        self.ResultadosEnSerie(True)
        self.imagen_zv = None
        self.ventana_tela = None
        self.factor = None
        self.val_recorte = None
        self.foto_recorte = None
        self.val_mensajes = None
        self.lineas = []
        self.medida = None
        self.psd = None
        self.revelado = None
        self.btn_generar = None

    #
    def ResultadosEnSerie(self, poner: bool) -> None:
        """
        Abrir resultados de la caja Serie, en el pie de la rejilla (poner) o
        fuera de él, oculto (lo trae la caja Lámina junto a Generar). Al
        ponerlo, vuelve a ser el que se ve. Sin caja Serie (serie
        restaurada), no hay ninguno: queda en None, que es lo que espera
        ActivarCarpeta (si no, seguiría apuntando al de la Lámina, ya
        destruido).
        """
        rejilla, btn = self.rejilla, self.btn_resultados_serie
        if poner:
            self.btn_resultados = btn
        if ((rejilla is None) or (btn is None) or (rejilla.pie is None)
                or (not rejilla.winfo_exists())):
            return
        izquierdo, resumen, derechos, sep = rejilla.pie
        analizar = derechos[-1]
        if not poner:
            rejilla.poner_pie(izquierdo, resumen, (analizar,), sep)
            return
        rejilla.poner_pie(izquierdo, resumen, (btn, analizar), sep)
        self.ActivarCarpeta()

    #
    def QuitarCajas(self, desde: int) -> None:
        """
        Quita las cajas desde la posición «desde» (las de encima) y lo que
        depende de ellas: la lectura en marcha, la ventana de incidencias, sus
        textos traducibles y sus atributos.
        """
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

    #
    def SOicon(self) -> None:
        """
        Icono de la ventana. En Windows, el .ico del programa con iconbitmap():
        así customtkinter no pone el suyo a los 200 ms. En los demás, según el
        tema: negro en el claro y blanco en el oscuro (se guarda la imagen: si
        no, Python la borra y el icono desaparece). Si falta el archivo, la
        ventana sigue sin él.
        """
        carpeta = K.path / K.CARPETA_RECURSOS
        try:
            if sys.platform.startswith(self.KV.PLATAFORMA_WINDOWS):
                self.iconbitmap(str(carpeta / K.ICONO_ICO))
                return

            oscuro = ctk.get_appearance_mode() == "Dark"
            nombre = K.ICONO_TEMA_OSCURO if oscuro else K.ICONO_TEMA_CLARO
            self.icono = tk.PhotoImage(file=carpeta / nombre)
            self.iconphoto(True, self.icono)
        except tk.TclError:
            pass

    #
    def destroy(self) -> None:
        """
        Cierra la ventana. Sustituye al destroy() de Tk: el nombre es
        OBLIGATORIO (no sigue las normas de nombres) porque lo llaman Tk al
        pulsar la X de la ventana y el botón Salir. Antes de cerrar se cancela
        todo lo que Tk tenga programado con after: la lectura pendiente de la
        serie y lo de CustomTkinter (la animación del clic, el ajuste de
        DPI…). Si no, Tk avisa de errores al intentar seguir con una ventana
        que ya no existe (bgerror). super().destroy() es el de Tk, el que
        cierra de verdad.
        """
        kv = self.KV
        for pendiente in self.tk.splitlist(
                self.tk.call(kv.TCL_AFTER, kv.TCL_INFO)):
            self.tk.call(kv.TCL_AFTER, kv.TCL_CANCEL, pendiente)
        super().destroy()

    # endregion Elementos de servicio general

    #
    # --- Posicionamiento y tamaño de la ventana
    #
    # region Posicionamiento y tamaño de la ventana

    #
    def Ajustar(self) -> None:
        """
        Ajusta la ventana al contenido (llamar tras añadir filas). Si no cabe
        en el alto del monitor, la ventana se queda en ese alto, el contenido
        se desplaza y aparece la barra.
        """

        # --- Lienzo del tamaño del cuerpo, sin pasar del alto disponible
        self.update_idletasks()
        kv = self.KV
        ancho = self.cuerpo.winfo_reqwidth()
        alto = self.cuerpo.winfo_reqheight()
        disponible = (self.MonitorPrincipal()[3] - kv.ARRIBA
                      - kv.RESERVA_ALTO - kv.MARGEN)
        self.lienzo.configure(width=ancho, height=min(alto, disponible),
                              scrollregion=(0, 0, ancho, alto))
        if alto > disponible:
            self.barra.pack(side="right", fill="y", before=self.lienzo)
        else:
            self.barra.pack_forget()
            self.lienzo.yview_moveto(0)

        # --- Tamaño que pide la ventana, ya calculado
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

        # --- Si al crecer se sale del monitor, se mete dentro
        self.MeterEnMonitor()

        # --- Repintado forzado, un momento después: se pide a cada
        #     elemento de la ventana que se vuelva a dibujar. Bajo
        #     XWayland, a veces se pierde el aviso de redibujar lo que se
        #     mueve a la zona nueva de la ventana (Tk sí lo tiene
        #     colocado) y queda en blanco hasta que se cambia el tamaño a
        #     mano
        #     La zona a redibujar es el elemento entero: sin ella, mide
        #     0 × 0, y los lienzos (botones y marcos de customtkinter) solo
        #     repintan esa zona, es decir, nada
        for espera in self.KV.ESPERAS_REPINTADO:
            self.after(espera, self._repintar)

    #
    # --- Pide a cada elemento de la ventana que se vuelva a dibujar,
    #     con su zona entera (ver Ajustar)
    def _repintar(self) -> None:
        pendientes: list[tk.Misc] = [self]
        while pendientes:
            elemento = pendientes.pop()
            elemento.event_generate(
                self.KV.TK_REDIBUJAR, x=0, y=0,
                width=elemento.winfo_width(),
                height=elemento.winfo_height())
            pendientes.extend(elemento.winfo_children())

    #
    def Centrar(self) -> None:
        """
        Coloca la ventana centrada en horizontal y arriba del monitor
        principal: al añadir filas crece hacia abajo sin salirse.
        """
        x, y, ancho, _ = self.MonitorPrincipal()

        # --- Centrada en horizontal y arriba de ese monitor
        x += (ancho - self.winfo_width()) // 2
        y += self.KV.ARRIBA
        self.geometry(self.KV.TK_POS.format(x=x, y=y))

    #
    def MeterEnMonitor(self) -> None:
        """Si la ventana se sale del monitor principal (al crecer con
        filas nuevas, o en una pantalla pequeña), la mueve lo justo para
        que quepa. Si cabe, no la toca: respeta que se haya movido a
        mano."""
        mx, my, m_ancho, m_alto = self.MonitorPrincipal()

        # --- Posición actual, en las mismas unidades en que se pide
        _, x_txt, y_txt = tk.Tk.wm_geometry(self).split(self.KV.SEP_POS)
        x_antes, y_antes = int(x_txt), int(y_txt)

        # --- Que no pase del borde derecho ni del de abajo; y, si es más
        #     grande que el monitor, que empiece en su borde izquierdo y en
        #     el de arriba
        x = max(mx, min(x_antes, mx + m_ancho - self.winfo_reqwidth()))
        y = max(my, min(y_antes, my + m_alto - self.winfo_reqheight()))
        if (x, y) != (x_antes, y_antes):
            self.geometry(self.KV.TK_POS.format(x=x, y=y))

    #
    def MonitorPrincipal(self) -> tuple[int, int, int, int]:
        """
        Posición y tamaño del monitor principal: (x, y, ancho, alto). Tk ve
        todos los monitores como una sola pantalla. Si no se pueden leer los
        monitores, toda la pantalla de Tk.
        """
        try:
            monitores = screeninfo.get_monitors()
        except screeninfo.ScreenInfoError:
            monitores = []
        if monitores:
            principal = next((m for m in monitores if m.is_primary),
                             monitores[0])
            return (principal.x, principal.y, principal.width,
                    principal.height)
        return 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()

    #
    def EstirarCuerpo(self, evento: tk.Event) -> None:
        """
        El cuerpo, tan ancho como el lienzo: así las filas se estiran si la
        ventana se ensancha.
        """
        self.lienzo.itemconfigure(self.id_cuerpo, width=evento.width)

    #
    def Rueda(self, evento: tk.Event) -> None:
        """
        Rueda del ratón: desplaza el contenido, solo si no cabe (con la barra a
        la vista) y si el ratón está en esta ventana (no en la de incidencias,
        que tiene su propio desplazamiento)
        """
        widget = evento.widget
        if ((not self.barra.winfo_ismapped())
                or (not isinstance(widget, tk.Misc))
                or (widget.winfo_toplevel() is not self)):
            return
        arriba = ((evento.num == self.KV.BTN_RUEDA_ARRIBA)
                  or (getattr(evento, "delta", 0) > 0))
        self.lienzo.yview_scroll(
            -self.KV.LINEAS_RUEDA if arriba else self.KV.LINEAS_RUEDA,
            "units")

    #
    def CrearCaja(self, titulo: dict | None = None,
                  reiniciar: Callable[[], None] | None = None,
                  fija: bool = False, marco: bool = True) -> ctk.CTkFrame:
        """
        Crea una caja con marco encima de las filas que ya hay (una por fase) y
        devuelve su interior, donde van los elementos. El título es opcional y
        va montado a mitad de la línea de arriba. reiniciar: cómo dejar sus
        atributos al quitarla (si tiene). fija: arriba del todo, por encima de
        las que vengan después (la cabecera). marco: si se dibuja (la cabecera
        y la de Ayuda van sin él)
        """

        # --- La fila, vacía, encima de las que ya hay (o arriba del todo)
        fila = ctk.CTkFrame(self.cuerpo, fg_color="transparent")
        fila.pack(side="top" if fija else "bottom", fill="x",
                  pady=(0, self.KV.MARGEN))
        self.cajas.append((fila, reiniciar))

        # --- Caja solo con marco: transparente, para que el fondo del
        #     título tape la línea sin que se note
        caja = ctk.CTkFrame(fila, fg_color="transparent",
                            border_width=self.KV.GROSOR_MARCO if marco else 0)

        # --- Con título, la caja baja media altura del título y este se
        #     coloca encima (lift), centrado en la línea
        arriba = 0
        hueco = self.KV.MARGEN
        if titulo:
            etiqueta = self.ApuntarTexto(
                ctk.CTkLabel(fila, padx=self.KV.RELLENO_TITULO), titulo)
            arriba = etiqueta.winfo_reqheight() // 2
            etiqueta.place(x=self.KV.MARGEN, y=arriba, anchor="w")
            etiqueta.lift()
            hueco = arriba + self.KV.SEPARADOR_SUPERIOR
        caja.pack(fill="x", pady=(arriba, 0))

        # --- Dentro, el margen separa el contenido del marco. Arriba, con
        #     título, el hueco es la media altura del título que queda
        #     dentro de la caja más el separador_superior
        interior = ctk.CTkFrame(caja, fg_color="transparent")
        interior.pack(fill="x", padx=self.KV.MARGEN,
                      pady=(hueco, self.KV.MARGEN))
        return interior

    #
    # --- Se calcula cada vez a partir de la casilla (self.ruta), así que
    #     siempre está al día
    @property
    def carpetaEscrita(self) -> Path:
        """ Saber la carpeta escrita en la casilla, como ruta: así «/a/b» y
            «/a/b/» son la misma, y «~» es la carpeta del usuario. """
        return Path(self.ruta.get().strip()).expanduser()

    #
    def Preparar(self) -> None:
        """
        Preparar: lanza la serie de la carpeta elegida, quitando antes la de la
        preparación anterior. Vuelve a leer la carpeta (rehace la Cámara):
        pueden haber cambiado sus archivos desde que se eligió (borrados a
        mano…) y la serie se copia de los que hay.
        """
        if not self.ConfirmarPreparar():
            return
        self.QuitarCajas(self.__propias_carpeta)
        self.caja_cam()
        if biboecf.problema_carpeta(self.OECF) is not None:     # type: ignore
            return
        self.caja_serie(self.OECF)                              # type: ignore

    #
    def ConfirmarPreparar(self) -> bool:
        """
        Preparar vacía la carpeta OECF (salvo las exportaciones del revelador y
        las subcarpetas): si ya tiene el análisis, se pide confirmación, con
        Cancelar por defecto, y se dice que las exportaciones se conservan. Sin
        análisis, sí sin preguntar.
        """
        kv = self.KV
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        if not biboecf.hay_review(oecf.carpeta):
            return True
        lineas = [K.tr(kv.TXT_YA_REVIEW), K.tr(kv.TXT_SE_BORRARA)]
        n = len(oecf.exportaciones)
        if n:
            lineas.insert(1, K.tr_n(kv.TXT_TIFF_SE_CONSERVAN, n).format(n=n))
        return self.Confirmar(kv.TXT_TITULO_CONFIRMAR, lineas,
                              kv.TXT_PREPARAR)

    #
    def Confirmar(self, titulo: dict, lineas: list[str],
                  texto_si: dict) -> bool:
        """
        Pregunta con una ventanita modal de CTk, centrada sobre la principal:
        el mensaje (sus líneas) y, a la derecha, Cancelar y el botón que acepta
        (texto_si). Intro, Escape y cerrar la ventana cancelan. La respuesta,
        también en self.confirmado.
        """
        kv = self.KV

        self.confirmado = False
        dialogo = self.dialogo_confirmar = ctk.CTkToplevel(self)
        dialogo.title(K.tr(titulo))
        dialogo.transient(self)
        dialogo.resizable(False, False)
        ctk.CTkLabel(dialogo, text=kv.SEP_LINEAS.join(lineas), justify="left",
                     wraplength=kv.ANCHO_CONFIRMAR).pack(
            padx=2 * kv.MARGEN, pady=(2 * kv.MARGEN, kv.MARGEN))
        botones = ctk.CTkFrame(dialogo, fg_color="transparent")
        botones.pack(fill="x", padx=2 * kv.MARGEN, pady=(0, 2 * kv.MARGEN))
        ctk.CTkButton(botones, text=K.tr(texto_si),
                      command=partial(self._responder, True)).pack(
            side="right", padx=(kv.MARGEN, 0))
        ctk.CTkButton(botones, text=K.tr(kv.TXT_CANCELAR),
                      command=partial(self._responder, False)).pack(
            side="right")
        for tecla in kv.TECLAS_CANCELAR:
            dialogo.bind(tecla, partial(self._responder, False))
        dialogo.protocol(kv.TK_CERRAR, partial(self._responder, False))

        dialogo.update_idletasks()
        x = self.winfo_rootx() + ((self.winfo_width()
                                  - dialogo.winfo_reqwidth()) // 2)
        y = self.winfo_rooty() + ((self.winfo_height()
                                  - dialogo.winfo_reqheight()) // 2)
        dialogo.geometry(kv.TK_POS.format(x=x, y=y))
        dialogo.wait_visibility()
        dialogo.grab_set()
        dialogo.focus_set()
        self.wait_window(dialogo)
        self.dialogo_confirmar = None
        return self.confirmado

    #
    # --- Respuesta del diálogo de Confirmar: la apunta y lo cierra. Lo
    #     que llega de más (el evento de la tecla) no se usa
    def _responder(self, si: bool, *_: object) -> None:
        self.confirmado = si
        dialogo: ctk.CTkToplevel = self.dialogo_confirmar       # type: ignore
        dialogo.destroy()

    #
    def Analizar(self) -> None:
        """ Analizar: quita la caja Lámina anterior (si la hay) y la crea. """
        self.QuitarCajas(self.propias_serie)
        self.caja_psd(self.OECF)                                # type: ignore

    #
    def ComprobarVersion(self) -> None:
        """
        En un hilo aparte (no puede tocar la ventana): pregunta a GitHub la
        versión publicada y apunta que ya está comprobada.
        """
        try:
            self.version_publicada = version_publicada()
        except Exception as e:
            self.error_version = f"{type(e).__name__}: {e}"
        self.version_comprobada = True

    #
    def MostrarVersion(self) -> None:
        """
        Mira cada poco si el hilo ya respondió. Si hay una versión más nueva,
        enseña su botón a la derecha de Ayuda.
        """
        if not self.version_comprobada:
            self.after(self.KV.PAUSA_VERSION, self.MostrarVersion)
            return
        if self.error_version is not None:
            self.MostrarError(self.error_version)
            return
        publicada = self.version_publicada
        if (publicada is None) or (not es_mas_nueva(publicada, K.version)):
            return
        self.Poner(self.btn_version, self.KV.TXT_NUEVA_VERSION,
                   version=publicada)
        self.btn_version.pack(side="left", padx=(self.KV.MARGEN, 0),
                              before=self.grupo_idioma)
        self.Ajustar()

    #
    def ActivarCarpeta(self) -> None:
        """
        Botones, sin estar leyendo una serie: Preparar (caja Carpeta), activo
        si la carpeta sirve; Abrir resultados (pie de la rejilla, si hay caja
        Serie), solo si ya se prepararon las copias.
        """
        libre = (self.OECF is not None) and (not self.leyendo)
        preparar = (libre and (biboecf.problema_carpeta(
            self.OECF) is None))                                 # type: ignore
        resultados = libre and bool(self.OECF.copias)           # type: ignore
        self.btn_preparar.configure(
            state="normal" if preparar else "disabled")

        # --- Los que se ven, en orden: con el análisis en la carpeta
        #     OECF, Analizar revelado si hay exportaciones del revelador;
        #     si no, Abrir resultados, salvo que ya se vea otro (los tres
        #     a la vez ensanchan demasiado la ventana); y Preparar o, en
        #     una carpeta OECF ya preparada (restaurada), Analizar, si
        #     están sus copias RAW o, sin ellas, si tiene el análisis
        #     guardado y la copia de la ZV (Tony, 2026-10-19 y
        #     2026-10-22: Generar lo rehace sin medir; sin la ZV no hay
        #     caja Lámina). Activos si además está libre. Al cambiar,
        #     la caja Carpeta cambia de ancho: la ventana se ajusta ya (si
        #     no, esperaba al siguiente Ajustar, p. ej. al cambiar de
        #     idioma)
        oecf = self.OECF
        analisis = (oecf is not None) and biboecf.hay_review(oecf.carpeta)
        tiff = analisis and bool(oecf.exportaciones)            # type: ignore
        abrir = analisis and (not tiff) and (self.btn_resultados is None)
        restaurada = (self.preparada and (oecf is not None)
                      and (oecf.copiasEnSitio
                           or (analisis and self._hay_zv(oecf))))
        vistos = [btn for btn, ver in (
            (self.btn_revelado, tiff),
            (self.btn_abrir_carpeta, abrir),
            (self.btn_analizar_carpeta, restaurada),
            (self.btn_preparar, not self.preparada)) if ver]
        botones = self.botones_carpeta
        if vistos != botones.pack_slaves():
            for btn in botones.pack_slaves():
                btn.pack_forget()
            for btn in vistos:
                btn.pack(side="left", padx=(self.KV.MARGEN, 0))
            self.Ajustar()
        for btn in (self.btn_revelado, self.btn_abrir_carpeta,
                    self.btn_analizar_carpeta):
            btn.configure(state="normal" if libre else "disabled")
        if self.btn_resultados is not None:
            self.btn_resultados.configure(
                state="normal" if resultados else "disabled")

    #
    def AnalizarRevelado(self) -> None:
        """
        Segunda parte del análisis: mide las exportaciones del revelador (las
        TIFF de OECF/ZONAS) en las mismas teselas que el análisis del JSON. En
        su propia caja, encima de la Cámara (quita las que hubiera: Serie,
        Lámina o un Revelado anterior)
        """
        kv = self.KV
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        review = biboecf.leer_review(oecf)
        if review is None:
            return
        self.QuitarCajas(self.propias_cam)
        self.caja_revelado = self.CrearCaja(kv.TXT_FASE_REVELADO,
                                            self.ReiniciarRevelado)
        self.val_revelado = ctk.CTkLabel(self.caja_revelado, text="",
                                         wraplength=kv.ANCHO_REVELADO)
        self.val_revelado.pack()
        self.review_revelado = review
        self.tiff_pendientes = sorted(oecf.exportaciones.items())
        self.tiff_medidos = {}
        self.escritos = []
        self.leyendo = True
        self.ActivarCarpeta()
        self.Traducir()
        self.Ajustar()
        self.MedirTiff()

    #
    # --- Aviso de que faltan las copias de control: sin ellas no se puede
    #     volver a medir y se toman como buenos los datos del análisis
    #     guardado (con todas las copias, lista vacía)
    def _aviso_sin_control(self) -> list[str]:
        kv = self.KV
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        if oecf.copiasEnSitio:
            return []
        return [K.tr(kv.TXT_SIN_CONTROL)]

    #
    # --- Saber si está la copia de la ZV (en ZONAS): sin ella no hay caja
    #     Lámina ni nada que analizar de nuevo
    @staticmethod
    def _hay_zv(oecf: biboecf.OECF | None) -> bool:
        zv = None if (oecf is None) else oecf.zonasCopia.get(0)
        return (zv is not None) and zv.is_file()

    #
    def MedirTiff(self) -> None:
        """
        Mide la siguiente exportación y se vuelve a programar (con after: la
        ventana atiende entre una y otra). Al terminar, guarda el L* del
        revelador en el JSON y rehace el libro.
        """
        kv = self.KV
        self.tarea = None
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        review: biboecf.Review = self.review_revelado           # type: ignore
        if self.tiff_pendientes:
            total = len(self.tiff_medidos) + len(self.tiff_pendientes)
            n = len(self.tiff_medidos) + 1
            self.Poner(self.val_revelado,                       # type: ignore
                       partial(self._componer, kv.TXT_MIDIENDO_REVELADO,
                               n=n, total=total))
            self.update_idletasks()
            tercio_ev, ruta = self.tiff_pendientes.pop(0)
            self.tiff_medidos[tercio_ev] = biboecf.medir_tiff(review, ruta)
            self.tarea = self.after(kv.PAUSA_LECTURA, self.MedirTiff)
            return

        # --- Las 31 zonas, en orden: el L* medido o NaN (sin TIFF, o si no
        #     se pudo medir). En el JSON, cada exportación con lo medido
        #     (bloque revelado)
        medidos = self.tiff_medidos
        lstars = {t: m.lstar for t, m in medidos.items()
                  if m.lstar is not None}
        revelador = tuple(lstars.get(t, math.nan)
                          for t in range(-biboecf.KS.TERCIOS_LADO,
                                         biboecf.KS.TERCIOS_LADO + 1))
        usables = sum(not math.isnan(v) for v in revelador)
        review = dataclasses.replace(review, revelador=revelador)
        guardado = biboecf.grabar_revelado(oecf, medidos)
        ruta = (self._carpeta_analisis(oecf)
                / f"{K.NOMBRE}{kv.EXTENSION_EXCEL}")
        # --- Cualquier fallo del libro se dice, con su error, y se sigue
        #     (si no, la caja se queda a medias)
        excel = None
        escrito = False
        error = ""
        try:
            excel = biboecf.Excel(ruta, textos_excel(), review)
            excel.escribir()
            self.escritos.append(ruta.name)
            escrito = True
        except OSError:
            pass
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        texto = (kv.TXT_REVELADO_HECHO if (guardado and escrito)
                 else kv.TXT_REVELADO_FALLO)
        # --- Y, si alguna no se pudo medir, cuáles y por qué
        rutas = dict(self.OECF.exportaciones)                   # type: ignore
        motivos = {m.motivo for m in medidos.values()}
        problemas = [K.tr(kv.TXT_PROBLEMAS_TIFF[code]).format(
            archivos=kv.SEP_ARCHIVOS.join(
                rutas[t].name for t, m in sorted(medidos.items())
                if m.motivo == code))
            for code in kv.TXT_PROBLEMAS_TIFF
            if code in motivos]
        lineas = [K.tr(texto).format(n=usables, total=len(medidos),
                                     archivo=ruta.name)]
        lineas += self._aviso_sin_control()
        if error:
            lineas.append(K.tr(kv.TXT_ERROR_EXCEL).format(archivo=ruta.name,
                                                          error=error))
        if excel is not None:
            biboecf.grabar_resultados(oecf.carpeta, excel.resultados())
            ficha, archivo, fallo = self.EscribirFicha(
                excel, oecf.carpetaAnalisis)
            lineas.append(K.tr(ficha).format(archivo=archivo, error=fallo))
        lineas += problemas

        # --- Exportaciones de menos bits que las definitivas: se avisa
        #     aquí y en las incidencias (botón, ventana e incidencias.txt)
        lineas += [Rejilla.texto_incidencia(inc, oecf)
                   for inc in biboecf.incidencias(oecf)
                   if inc.codigo == biboecf.KI.TIFF_8_BITS]
        self.ContarIncidencias()
        self.Poner(self.val_revelado,                           # type: ignore
                   kv.SEP_LINEAS.join(lineas))

        # --- Abrir resultados, al pie de la caja
        btn = ctk.CTkButton(self.caja_revelado,               # type: ignore
                            command=self.AbrirResultados)
        self.ApuntarTexto(btn, kv.TXT_ABRIR_RESULTADOS)
        btn.pack(side="bottom", anchor="e", pady=(kv.MARGEN, 0))
        self.Traducir()
        self.Ajustar()

        # --- Con paño, si se quiere, las láminas otra vez, ya con el
        #     revelado del revelador (las mismas que haya; al menos la del
        #     100 %)
        if (isinstance(review.tela, biboecf.Ventana) and usables
                and self.Confirmar(kv.TXT_TITULO_PSD,
                                   [K.tr(kv.TXT_PREGUNTA_PSD)],
                                   kv.TXT_REHACER)):
            self.EmpezarPsdTiff(review)
            return
        self.review_revelado = None
        self.leyendo = False
        self.ActivarCarpeta()

    #
    def EmpezarPsdTiff(self, review: biboecf.Review) -> None:
        """
        Láminas desde las exportaciones del revelador: las mismas que ya haya
        en la carpeta OECF (al menos la del 100 %), con su progreso en la
        segunda línea de la caja Revelado.
        """
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        tela: biboecf.Ventana = review.tela                     # type: ignore
        medidas = {t: ruta for t, ruta in oecf.exportaciones.items()
                   if (t in self.tiff_medidos)
                   and (self.tiff_medidos[t].lstar is not None)}
        zonas = {oecf.NombreZona(t): ruta for t, ruta
                 in oecf.RellenarTercios(medidas).items()}
        prueba = biboecf.Psd(biboecf.RUTA_PLANTILLA, {}, tela,
                             biboecf.KTE.FACTORES,
                             (review.alto, review.ancho))
        factores = tuple(f for f in biboecf.KTE.FACTORES
                         if (f == biboecf.KTE.FACTORES[0])
                         or (oecf.carpetaAnalisis / prueba.nombre(f)).exists())
        self.psd_tiff = biboecf.Psd(
            biboecf.RUTA_PLANTILLA, zonas, tela,
            factores, (review.alto, review.ancho),
            self.TextosCartela(review, oecf.carpeta))
        self.revelado_tiff = self.psd_tiff.Revelar()
        self.val_psd_tiff = ctk.CTkLabel(
            self.caja_revelado, text="",                        # type: ignore
            wraplength=self.KV.ANCHO_REVELADO)
        self.val_psd_tiff.pack(pady=(self.KV.MARGEN, 0))
        self.LeerPsdTiff()

    #
    def LeerPsdTiff(self) -> None:
        """
        Lee la siguiente exportación para la lámina y se vuelve a programar; al
        terminar, escribe las láminas.
        """
        kv = self.KV
        self.tarea = None
        hechas, total = next(self.revelado_tiff)                # type: ignore
        if hechas < total:
            self.Poner(self.val_psd_tiff,                       # type: ignore
                       partial(self._componer, kv.TXT_LEYENDO_PSD,
                               n=hechas + 1, total=total))
            self.update_idletasks()
            self.tarea = self.after(kv.PAUSA_LECTURA, self.LeerPsdTiff)
            return
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        psd: biboecf.Psd = self.psd_tiff                        # type: ignore
        escritas, fallos = [], []
        for factor in psd.factores:
            nombre = psd.nombre(factor)
            self.Poner(self.val_psd_tiff,                       # type: ignore
                       partial(self._componer, kv.TXT_ESCRIBIENDO,
                               archivo=nombre))
            self.update_idletasks()
            try:
                psd.Escribir(factor, oecf.carpetaAnalisis / nombre)
                escritas.append(nombre)
                self.escritos.append(nombre)
            except OSError:
                fallos.append(nombre)
        texto = kv.TXT_PSD if not fallos else kv.TXT_SIN_PSD
        archivos = kv.SEP_ARCHIVOS.join(escritas or fallos)
        self.Poner(self.val_psd_tiff,                           # type: ignore
                   partial(self._texto_psd_tiff, texto, archivos))
        self.revelado_tiff = None
        self.psd_tiff = None
        self.review_revelado = None
        self.leyendo = False
        self.ActivarCarpeta()
        self.Ajustar()

    #
    # --- Línea final de la lámina desde las TIFF: cómo fue y el
    #     «Finalizado» con los archivos de la tanda
    def _texto_psd_tiff(self, texto: dict, archivos: str) -> str:
        return self.KV.SEP_LINEAS.join((
            K.tr(texto).format(archivos=archivos, archivo=archivos),
            self.TextoFinalizado()))

    #
    def AbrirResultados(self) -> None:
        """
        Abre los resultados: la carpeta OECF de la serie, en el explorador de
        archivos del sistema.
        """
        if self.OECF is None:
            return
        carpeta = self.OECF.carpeta
        if sys.platform.startswith(self.KV.PLATAFORMA_WINDOWS):
            os.startfile(carpeta)                               # type: ignore
        elif sys.platform == self.KV.PLATAFORMA_MAC:
            subprocess.Popen([self.KV.ABRIR_MAC, carpeta])
        else:
            subprocess.Popen([self.KV.ABRIR_LINUX, carpeta])

    # endregion Posicionamiento y tamaño de la ventana

    #
    # --- Gestión del idioma
    #
    # region Gestión del idioma

    #
    def ApuntarTexto(self, elemento: ctk.CTkBaseClass, texto: dict,
                     **datos: object) -> ctk.CTkBaseClass:
        """
        Apunta un elemento para traducirlo y lo devuelve Los {campos} del texto
        se rellenan con datos.
        """
        self._textos[elemento] = partial(self._componer, texto, **datos)
        return elemento

    #
    # --- Texto en el idioma activo, con sus {campos} rellenos con datos
    @staticmethod
    def _componer(texto: dict, **datos: object) -> str:
        return K.tr(texto).format(**datos)

    #
    def Poner(self, elemento: ctk.CTkBaseClass,
              texto: str | dict | Callable[[], str], **datos: object) -> None:
        """
        Pone un texto en un elemento. Puede ser: str      fijo (un nombre de
        archivo): no se traduce dict     {idioma: texto}, con sus {campos} en
        datos función  que compone el texto en el idioma activo.
        """
        if isinstance(texto, str):
            self._textos.pop(elemento, None)
            elemento.configure(text=texto)
            return

        if isinstance(texto, dict):
            self.ApuntarTexto(elemento, texto, **datos)

        else:
            self._textos[elemento] = texto

        elemento.configure(text=self._textos[elemento]())

    #
    def Traducir(self) -> None:
        """ Pone el título y los textos en el idioma activo. """
        self.title(f"{K.NOMBRE} - {K.tr(self.KV.TXT_VERSION)} {K.version}")
        for elemento, componer in self._textos.items():
            elemento.configure(text=componer())

        # --- La rejilla dibuja sus textos («falta»…) en el Canvas
        if self.rejilla is not None:
            self.rejilla.dibujar()
        self.rellenar_incidencias()
        self.Ajustar()

    #
    def CambiarIdioma(self, nombre: str) -> None:
        """ Cambia el idioma activo al elegido en la lista. """
        for code, nombre_idioma in K.IDIOMAS.items():
            if nombre_idioma == nombre:
                K.idioma = code
        self.Traducir()

    # endregion Gestión del idioma
