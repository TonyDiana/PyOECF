# -*- coding: utf-8 *-*
"""
    :Propósito: Kernel PyOECF.
    :Autor:     Tony Diana
    :Versión:   26.10.09
"""

# cSpell:ignore biboecf, borderwidth, boton, choosedir, codigo, customtkinter
# cSpell:ignore exps, initialdir, leidas, mclocale, mcset, meipass, msgcat
# cSpell:ignore oecf, padx, pady, redibuja, redibujar, relx, screeninfo, tamano
# cSpell:ignore textvariable, winfo, startfile, zenity, kdialog
# cSpell:ignore getexistingdirectory

# --- Valenciano
# cSpell:ignore acadèmica, accedir, acord, Ajuda, Analitzar, Càmera, carpetes
# cSpell:ignore Copiant, denegat, Eixir, escriure, espai, existeix, fitxer
# cSpell:ignore imatge, imatges, Incidències, incidències, Llegint, llegir
# cSpell:ignore Llicència, lliure, Mostra, nincidències, obrir, Permís, pogut
# cSpell:ignore resultats, Selecció, Seleccioneu, Sense, sense, Sèrie, sèrie
# cSpell:ignore Trieu, vàlid, Versió

__all__ = ["Ventana"]

# --- Bibliotecas estándar Python
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
from pathlib import Path
from tkinter import filedialog, messagebox

# --- Bibliotecas externas
import customtkinter as ctk
import numpy as np
import screeninfo

# --- Bibliotecas internas
import biboecf
from bib import clases
from .actualizacion import KA, es_mas_nueva, version_publicada
from .constantes import K
from .json_estudio import (grabar_analisis, grabar_json, grabar_resultados,
                           hay_analisis, leer_analisis, leer_resultados)
from .rejilla import Rejilla
from .textos_libro import textos_libro


#
class Ventana(ctk.CTk):
    """ Ventana principal de PyOECF. """

    # --- OJO: aquí NO tiene efecto. __slots__ solo impide crear atributos
    #     nuevos si todas las clases de las que se hereda también lo usan,
    #     y customtkinter (ctk.CTk) no lo usa: la ventana sigue teniendo su
    #     __dict__ y admite cualquier atributo. Se deja por la norma
    # __slots__ = []

    # --- Constantes de la ventana (las de toda la app están en K)
    class KV(clases.EnumMutable):
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
        TXT_YA_ANALISIS = {K.ES: "La carpeta OECF ya tiene el análisis.",
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

        TXT_TITULO_LAMINAS = {K.ES: "Rehacer las láminas",
                              K.EN: "Rebuild the print sheets",
                              K.CA: "Refer les làmines"}
        TXT_PREGUNTA_LAMINAS = {
            K.ES: "¿Rehacer las láminas con las exportaciones del revelador? "
                  "Se sustituirán las que hay.",
            K.EN: "Rebuild the print sheets with the developer exports? The "
                  "existing ones will be replaced.",
            K.CA: "Voleu refer les làmines amb les exportacions del "
                  "revelador? Se substituiran les que hi ha."}
        TXT_REHACER = {K.ES: "Rehacer", K.EN: "Rebuild", K.CA: "Refer"}
        TXT_LEYENDO_LAMINA = {K.ES: "Lámina: leyendo {n} de {total}…",
                              K.EN: "Print sheet: reading {n} of {total}…",
                              K.CA: "Làmina: llegint {n} de {total}…"}
        TXT_PROBLEMAS_TIFF = {
            biboecf.KRV.TAMANO_DISTINTO: {
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
            biboecf.KRV.COMPRESION: {
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

        TXT_EXP = {K.ES: "Tv",  K.EN: "Tv",  K.CA: "Tv"}
        TXT_F = {K.ES: "f/",    K.EN: "f/",  K.CA: "f/"}
        TXT_ISO = {K.ES: "ISO", K.EN: "ISO", K.CA: "ISO"}

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
        SEP_RESUMEN = " · "

        # --- Incidencias de la rejilla: botón bajo la Z0, con cuántas
        #     hay, y su propia ventana (ancho × alto, en píxeles)
        TXT_INCIDENCIAS = {K.ES: "Incidencias ({n})", K.EN: "Issues ({n})",
                           K.CA: "Incidències ({n})"}
        TXT_SIN_INCIDENCIAS = {K.ES: "Sin incidencias", K.EN: "No issues",
                               K.CA: "Sense incidències"}

        # --- Las incidencias, una por línea, también en un archivo de
        #     texto en la carpeta OECF, en el idioma de la ventana
        SEP_INCIDENCIAS = "\n"
        ARCHIVO_INCIDENCIAS = "incidencias.txt"
        # --- Analizar: botón bajo la ZX, activo solo si la serie sirve
        TXT_ANALIZAR = {K.ES: "Analizar", K.EN: "Analyze",
                        K.CA: "Analitzar"}
        TXT_TITULO_INCIDENCIAS = {K.ES: "Incidencias de la serie",
                                  K.EN: "Series issues",
                                  K.CA: "Incidències de la sèrie"}
        TAMANO_INCIDENCIAS = "520x320"

        # --- Caja Lámina (la crea Analizar): el paño de la Z-V, su recorte
        #     y los tamaños, con su porcentaje (100 entre el divisor)
        TXT_FASE_LAMINA = {K.ES: "Lámina", K.EN: "Print sheet",
                           K.CA: "Làmina"}
        TXT_BUSCANDO_PANO = {K.ES: "Buscando el paño…",
                             K.EN: "Looking for the fabric…",
                             K.CA: "Buscant el drap…"}
        TXT_PROBLEMA_PANO = {
            biboecf.KTE.SIN_PANO: {
                K.ES: "No se encontró el paño: solo se generará el Excel.",
                K.EN: "The fabric was not found: only the Excel workbook "
                      "will be generated.",
                K.CA: "No s'ha trobat el drap: només es generarà l'Excel."},
            biboecf.KTE.PANO_PEQUENO: {
                K.ES: "El paño es demasiado pequeño para la lámina: solo "
                      "se generará el Excel.",
                K.EN: "The fabric is too small for the print sheet: only "
                      "the Excel workbook will be generated.",
                K.CA: "El drap és massa menut per a la làmina: només es "
                      "generarà l'Excel."}}
        TXT_TAMANO = {K.ES: "Tamaño", K.EN: "Size", K.CA: "Grandària"}

        # --- Ventanita de mensajes: ancho de sus líneas (píxeles) y
        #     separación entre mensajes
        ANCHO_MENSAJES = 260
        SEP_MENSAJES = "\n"

        # --- Generar: progreso de la medida, el libro (en la carpeta OECF,
        #     con el nombre del programa) y si no se pudo escribir
        TXT_MIDIENDO = {K.ES: "Midiendo {n} de {total}…",
                        K.EN: "Measuring {n} of {total}…",
                        K.CA: "Mesurant {n} de {total}…"}
        TXT_LIBRO = {K.ES: "Libro escrito: {archivo}",
                     K.EN: "Workbook written: {archivo}",
                     K.CA: "Llibre escrit: {archivo}"}
        TXT_SIN_LIBRO = {
            K.ES: "No se pudo escribir el libro (¿está abierto?): {archivo}",
            K.EN: "The workbook could not be written (is it open?): "
                  "{archivo}",
            K.CA: "No s'ha pogut escriure el llibre (està obert?): "
                  "{archivo}"}
        TXT_ERROR_LIBRO = {
            K.ES: "Error al escribir el libro {archivo}: {error}",
            K.EN: "Error writing the workbook {archivo}: {error}",
            K.CA: "Error en escriure el llibre {archivo}: {error}"}
        EXTENSION_LIBRO = ".xlsx"

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
        TXT_CAJETIN_CAMARA = {K.ES: "Cámara: {camara}",
                              K.EN: "Camera: {camara}",
                              K.CA: "Càmera: {camara}"}
        TXT_CAJETIN_LATITUD = {
            K.ES: "Latitud recomendada: {desde} a {hasta} ({zonas} zonas)",
            K.EN: "Recommended latitude: {desde} to {hasta} ({zonas} zones)",
            K.CA: "Latitud recomanada: {desde} a {hasta} ({zonas} zones)"}
        TXT_CAJETIN_SIN_LATITUD = {K.ES: "Latitud recomendada: —",
                                   K.EN: "Recommended latitude: —",
                                   K.CA: "Latitud recomanada: —"}
        TXT_CAJETIN_FECHA = {K.ES: "Fecha: {fecha}", K.EN: "Date: {fecha}",
                             K.CA: "Data: {fecha}"}
        TXT_CAJETIN_SOPORTE = {
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
        FORMATO_FECHA_CAJETIN = "{dia} {mes} {anio}"

        # --- Generar, la lámina: progreso del revelado, las escritas y si
        #     no se pudo
        TXT_REVELANDO = {K.ES: "Lámina: revelando {n} de {total}…",
                         K.EN: "Print sheet: developing {n} of {total}…",
                         K.CA: "Làmina: revelant {n} de {total}…"}
        TXT_ESCRIBIENDO = {K.ES: "Lámina: escribiendo {archivo}…",
                           K.EN: "Print sheet: writing {archivo}…",
                           K.CA: "Làmina: escrivint {archivo}…"}
        TXT_LAMINA = {K.ES: "Lámina escrita: {archivos}",
                      K.EN: "Print sheet written: {archivos}",
                      K.CA: "Làmina escrita: {archivos}"}
        TXT_SIN_LAMINA = {
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

        # --- Texto de cada problema de la carpeta (biboecf.KCA)
        TXT_PROBLEMA_CARPETA = {
            biboecf.KCA.NO_EXISTE: TXT_SIN_CARPETA,
            biboecf.KCA.NO_LEGIBLE: TXT_SIN_PERMISO_LEER,
            biboecf.KCA.SIN_RAW: TXT_SIN_RAW,
            biboecf.KCA.NO_ESCRIBIBLE: TXT_SIN_PERMISO_ESCRIBIR}
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

        # --- Posición de una ventana en Tk: se pide con TK_POSICION
        #     ("+x+y") y wm_geometry() la devuelve tras el tamaño
        #     ("anchoxalto+x+y"), separada por SEP_POSICION
        TK_POSICION = "+{x}+{y}"
        SEP_POSICION = "+"

        # --- Alto que no puede ocupar la ventana bajo ARRIBA: barra de
        #     título y barra de tareas del sistema. Si el contenido no cabe
        #     en el resto, se desplaza como una página web
        RESERVA_ALTO = 100

        # --- Rueda del ratón: líneas por paso, y eventos (Windows y
        #     macOS dan MouseWheel con delta; Linux, los botones 4 y 5)
        LINEAS_RUEDA = 3
        TK_RUEDA = ("<MouseWheel>", "<Button-4>", "<Button-5>")
        BOTON_RUEDA_ARRIBA = 4

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

    def caja_ayuda(self) -> None:
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
        self.boton_version = ctk.CTkButton(
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

        # --- En el idioma de la app y no en el del sistema: se completan
        #     las traducciones que le faltan a Tk y, si el diálogo ya
        #     existe, se destruye para que se cree de nuevo en ese idioma
        def _idioma() -> None:
            try:
                for original, textos in kv.TCL_FALTAN.items():
                    for codigo, traducido in textos.items():
                        self.tk.call(*kv.TCL_ESPACIO, (kv.TCL_TRADUCIR,
                                                       codigo, original,
                                                       traducido))
                self.tk.call(kv.TCL_IDIOMA, K.idioma)
                if int(self.tk.call("winfo", "exists", kv.TCL_DIALOGO)):
                    self.tk.call("destroy", kv.TCL_DIALOGO)
            except tk.TclError:
                pass

        # --- Orden del explorador del escritorio en Linux, o None si no
        #     hay ninguno instalado
        def _orden_linux(inicio: Path) -> list[str] | None:
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

        # --- Entorno del explorador: el del sistema, no el del ejecutable
        def _entorno_sistema() -> dict[str, str]:
            entorno = dict(os.environ)
            if kv.LD_RUTA_ORIGINAL in entorno:
                entorno[kv.LD_RUTA] = entorno[kv.LD_RUTA_ORIGINAL]
            elif getattr(sys, "frozen", False):
                entorno.pop(kv.LD_RUTA, None)
            return entorno

        # --- Escribe la carpeta elegida en la casilla
        def _usar(ruta: str) -> None:
            self.ruta.set(ruta)
            _mostrar_cam()

        # --- Diálogo de Tk: Windows, macOS y Linux sin explorador
        def _dialogo_tk(inicio: Path) -> None:
            _sin_ocultos()
            _idioma()
            ruta = filedialog.askdirectory(parent=self, initialdir=inicio)
            if ruta:
                _usar(ruta)

        # --- Espera a que se cierre el explorador de Linux sin bloquear
        #     la ventana. Si falla, se abre el de Tk
        def _esperar(inicio: Path) -> None:
            if self.explorador is None:
                return
            if self.explorador.poll() is None:
                self.after(kv.ESPERA_EXPLORADOR, _esperar, inicio)
                return

            codigo = self.explorador.returncode
            salida = self.explorador.stdout.read().strip() \
                if self.explorador.stdout else ""
            self.explorador = None
            if codigo == kv.SALIDA_ELEGIDA and salida:
                _usar(salida)
            elif codigo != kv.SALIDA_CANCELADA:
                _dialogo_tk(inicio)

        # --- Pide la carpeta y la escribe en la casilla. El diálogo
        #     empieza en la carpeta de la casilla, si existe; si no, en la
        #     del usuario (no en la de la app)
        def _elegir() -> None:
            if self.explorador is not None:
                return

            escrita = self.ruta.get().strip()
            inicio = Path(escrita) if escrita else Path.home()
            if not inicio.is_dir():
                inicio = Path.home()

            orden = (_orden_linux(inicio)
                     if sys.platform.startswith(kv.PLATAFORMA_LINUX)
                     else None)
            if orden is not None:
                try:
                    self.explorador = subprocess.Popen(
                        orden, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, text=True,
                        env=_entorno_sistema())
                except OSError:
                    self.explorador = None
                else:
                    self.after(kv.ESPERA_EXPLORADOR, _esperar, inicio)
                    return

            _dialogo_tk(inicio)

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
            self.__espera = self.after(kv.ESPERA_TECLEO, _mostrar_cam)

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

        # --- La caja: botón · ruta elegida · Analizar revelado (oculto
        #     hasta que haya análisis) · Preparar.
        #     Las cajas que haya hasta esta (incluida) son las propias; el
        #     resto, de encima
        fila = self.CrearCaja(kv.TXT_FASE_CARPETA)
        self.__propias_carpeta = len(self.cajas)
        self.ApuntarTexto(ctk.CTkButton(fila, command=_elegir),
                          kv.TXT_CARPETA).pack(side="left")

        # --- Preparar antes que la casilla, para que esta ocupe el hueco.
        #     Empieza inactivo: aún no hay RAW
        self.boton_preparar = ctk.CTkButton(fila, command=self.Preparar,
                                            state="disabled")
        self.ApuntarTexto(self.boton_preparar, kv.TXT_PREPARAR)
        self.boton_preparar.pack(side="right", padx=(kv.MARGEN, 0))

        # --- Analizar revelado, a la izquierda de Preparar: se crea
        #     oculto; lo enseña ActivarCarpeta
        self.boton_revelado = ctk.CTkButton(
            fila, command=self.AnalizarRevelado, state="disabled")
        self.ApuntarTexto(self.boton_revelado, kv.TXT_ANALIZAR_REVELADO)

        # --- Cada cambio en la ruta (elegida o tecleada) quita las cajas
        #     de encima y muestra la cámara de la carpeta nueva
        self.ruta = ctk.StringVar()
        self.ruta.trace_add("write", _otra_carpeta)
        carpeta = ctk.CTkEntry(fila, width=kv.ANCHO_CARPETA,
                               textvariable=self.ruta)
        carpeta.pack(side="left", fill="x", expand=True, padx=(kv.MARGEN, 0))

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
                hueco = kv.SEP_DATOS if grupo.winfo_children() else 0
                self.ApuntarTexto(ctk.CTkLabel(grupo), nombre).pack(
                    side="left", padx=(hueco, 0))
                valor = ctk.CTkLabel(grupo, text="")
                valor.pack(side="left", padx=(kv.MARGEN, 0))
                return valor

            # --- Los datos van en un grupo que no se estira: así queda
            #     centrado en la caja
            interior = self.CrearCaja(kv.TXT_FASE_CAM, self.ReiniciarCam)
            self.propias_cam = len(self.cajas)
            grupo = ctk.CTkFrame(interior, fg_color="transparent")
            grupo.pack()

            self.val_archivo = _nuevo_dato(kv.TXT_ARCHIVO)
            self.val_fecha = _nuevo_dato(kv.TXT_FECHA)
            self.val_modelo = _nuevo_dato(kv.TXT_MODELO)

            # --- Profundidad de bits
            self.val_bits = ctk.CTkLabel(grupo, text="")
            self.val_bits.pack(side="left", padx=(kv.SEP_DATOS, 0))

            # --- Exposición: f, Tv e ISO en un solo texto, centrado en su
            #     hueco
            self.val_exp = ctk.CTkLabel(grupo, text="")
            self.val_exp.pack(side="left", padx=(kv.SEP_DATOS, 0))

            # --- Pone los textos nuevos y hace crecer la ventana
            self.Traducir()

        # --- Siempre es nueva: al cambiar de carpeta se quita la anterior
        _construir_caja()

        # --- Fase 1 de la serie: la carpeta, sus RAW y la exposición de
        #     la primera. Se guarda para Preparar (y su carpeta, para no
        #     rehacer la caja si se vuelve a elegir la misma)
        OECF = self.OECF = biboecf.OECF(self.carpetaEscrita)

        # --- Si la carpeta no sirve (no existe, no se lee, sin RAW o sin
        #     permiso para escribir los resultados), se dice por qué y
        #     Preparar no se activa
        problema = biboecf.problema_carpeta(OECF)
        if problema:
            self.Poner(self.val_archivo,                        # type: ignore
                       kv.TXT_PROBLEMA_CARPETA[problema])
            return

        self.Poner(self.val_archivo, OECF.primera)              # type: ignore

        # --- Fecha y hora de disparo, en el formato de cada idioma
        fecha = OECF.fecha
        if fecha is None:
            self.Poner(self.val_fecha, kv.TXT_NO_READ)          # type: ignore
        else:
            self.Poner(self.val_fecha,                          # type: ignore
                       lambda: fecha.strftime(K.tr(kv.FORMATO_FECHA)))

        # --- Marca y modelo juntos, sin repetir la marca
        cam = OECF.cam
        self.Poner(self.val_modelo,                             # type: ignore
                   kv.TXT_NO_READ if cam is None else cam.nombre)

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
            def _str_exp() -> str:
                return kv.SEP_RESUMEN.join((
                    K.tr(kv.TXT_F) + biboecf.OECF.TextoF(exp.f),
                    f"{K.tr(kv.TXT_EXP)} {biboecf.OECF.TextoTV(exp.tv)}",
                    f"{K.tr(kv.TXT_ISO)} {biboecf.OECF.TextoISO(exp.iso)}"))
            self.Poner(self.val_exp, _str_exp)                   # type: ignore

        # --- Con RAW, ya se puede preparar
        self.ActivarCarpeta()

    #
    # --- Caja --- Serie
    #

    # --- Se crea nueva en cada preparación, encima de la cámara: resumen,
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
                ventana.geometry(kv.TAMANO_INCIDENCIAS)
                ventana.transient(self)
                self.texto_incidencias = ctk.CTkTextbox(ventana, wrap="word")
                self.texto_incidencias.pack(fill="both", expand=True,
                                            padx=kv.MARGEN, pady=kv.MARGEN)
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
            self.Poner(val_serie, kv.TXT_LEYENDO,
                       n=leidas + 1, total=len(raws))
            self.update_idletasks()

            next(self.lectura)                                  # type: ignore
            barra.set(len(self.OECF.tomas) / len(raws))         # type: ignore

            # --- after (y no un bucle): entre imagen e imagen, la ventana
            #     atiende al ratón y se repinta
            self.tarea = self.after(kv.PAUSA_LECTURA, _leer_toma)

        # --- Calcula la zona de cada imagen y muestra el resumen.
        #     PROVISIONAL: la referencia es la primera imagen leída (sin
        #     tapadas todavía)
        def _fin_serie() -> None:
            barra.pack_forget()

            # --- La serie, leída y repartida por OECF: el tercioEV de
            #     cada archivo, en su orden (None si no se leyó)
            serie: biboecf.OECF = self.OECF                     # type: ignore
            leidas = [t for t in serie.tercioEVs if t is not None]
            if not leidas:
                self.leyendo = False
                self.ActivarCarpeta()
                self.Poner(val_serie, kv.TXT_NO_READ)
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
                texto = K.tr_n(kv.TXT_RESUMEN, len(raws)).format(
                    total=len(raws), desde=desde, hasta=hasta)
                if sin_leer:
                    texto += K.tr(kv.TXT_SIN_LEER).format(n=sin_leer)
                return texto

            self.Poner(val_serie, _resumen)
            _mostrar_rejilla()
            self.Ajustar()

            # --- A copiar las tomas que sirven a la carpeta OECF, una
            #     cada vez, con su progreso bajo la rejilla. Los botones
            #     siguen inactivos hasta el final
            self.copia = serie.Copiar()
            barra.set(0)
            barra.pack(fill="x", pady=(kv.MARGEN, 0))
            val_copia.pack()
            self.Ajustar()
            _copiar_toma()

        # --- Copia la siguiente toma (la copia OECF) y se vuelve a
        #     programar. Antes de copiar se pinta el progreso: la copia
        #     bloquea la ventana un momento
        def _copiar_toma() -> None:
            self.tarea = None
            paso = next(self.copia, None)                       # type: ignore
            if paso is None:
                _fin_copia()
                return

            hechas, total = paso
            barra.set(hechas / total if total else 1)
            if hechas < total:
                self.Poner(val_copia, kv.TXT_COPIANDO,
                           n=hechas + 1, total=total)
                self.update_idletasks()
            self.tarea = self.after(kv.PAUSA_COPIA, _copiar_toma)

        # --- Con las copias hechas, allí mismo los datos de la
        #     preparación (JSON) y las incidencias. Analizar, solo si la
        #     serie sirve y se copió
        def _fin_copia() -> None:
            serie: biboecf.OECF = self.OECF                     # type: ignore
            barra.pack_forget()

            # --- Con las copias hechas, el JSON y las incidencias. Si la
            #     copia falló, se avisa donde iba su progreso
            if not serie.copias:
                self.Poner(val_copia, kv.TXT_NO_COPIADO,
                           error=serie.errorCopia or "")
            else:
                val_copia.pack_forget()
                grabar_json(serie)
                self.GrabarIncidencias()
            boton_analizar.configure(
                state="normal" if serie.esAnalizable and serie.copias
                else "disabled")
            self.leyendo = False
            self.ActivarCarpeta()
            self.Ajustar()

        # --- Rejilla de zonas y tercios y su pie: el resumen, el botón
        #     de incidencias, que dice cuántas hay y las muestra todas (sin
        #     ninguna, queda inactivo y lo dice), y Analizar, activo solo
        #     si la serie sirve
        def _mostrar_rejilla() -> None:
            serie: biboecf.OECF = self.OECF                     # type: ignore
            rejilla.mostrar(serie)
            self.Poner(val_rejilla, lambda: "\n".join((
                Rejilla.resumen(serie),
                kv.SEP_RESUMEN.join((
                    Rejilla.linea_balance(serie.balancePersonalizado),
                    Rejilla.linea_balances(len(serie.WBs)))),
                Rejilla.linea_tapadas(len(serie.tapadas)))))
            rejilla.pack(fill="x", pady=(kv.MARGEN, 0))
            rejilla.dibujar()

            self.incidencias = lambda: Rejilla.incidencias(serie)
            self.ContarIncidencias()

        # --- La caja. La rejilla y el resumen se muestran al terminar
        interior = self.CrearCaja(kv.TXT_FASE_SERIE, self.ReiniciarSerie)
        self.propias_serie = len(self.cajas)
        val_serie = ctk.CTkLabel(interior, text="")
        val_serie.pack()
        barra = ctk.CTkProgressBar(interior)
        rejilla = self.rejilla = Rejilla(interior)
        val_copia = ctk.CTkLabel(interior, text="")
        # --- Pie de la rejilla: Incidencias bajo la Z0, el resumen, y
        #     Abrir resultados (la carpeta OECF, inactivo hasta copiar) y
        #     Analizar bajo la ZX (crea la caja Lámina). Son hijos de la
        #     rejilla, que los coloca
        val_rejilla = ctk.CTkLabel(rejilla, text="")
        self.boton_incidencias = ctk.CTkButton(rejilla,
                                               command=_ver_incidencias)
        self.boton_resultados = self.boton_resultados_serie = ctk.CTkButton(
            rejilla, command=self.AbrirResultados, state="disabled")
        self.ApuntarTexto(self.boton_resultados, kv.TXT_ABRIR_RESULTADOS)
        boton_analizar = ctk.CTkButton(rejilla, command=self.Analizar,
                                       state="disabled")
        self.ApuntarTexto(boton_analizar, kv.TXT_ANALIZAR)
        rejilla.poner_pie(self.boton_incidencias, val_rejilla,
                          (self.boton_resultados, boton_analizar), kv.MARGEN)
        self.Traducir()

        # --- A leer: Preparar queda inactivo hasta el final
        self.leyendo = True
        self.ActivarCarpeta()
        self.lectura = OECF.Leer()
        barra.set(len(OECF.tomas) / len(raws))
        barra.pack(fill="x", pady=(kv.MARGEN, 0))
        self.Ajustar()
        _leer_toma()

    # --- Caja Lámina: la crea Analizar. Mide las teselas de la Z-V
    #     (OECF.Seleccionar): sin tarjeta gris, lo dice y no hay más. Con
    #     tarjeta, dos secciones a todo el ancho: el recorte del paño (si
    #     lo hay; si no, por qué, y solo se generará el Excel) y, a la
    #     derecha, los tamaños, la ventanita de mensajes (las teselas
    #     rechazadas y, al generar, el proceso) y Generar: mide la serie
    #     y escribe el JSON, el libro y, con paño, la lámina
    def caja_lamina(self, OECF: biboecf.OECF) -> None:
        kv = self.KV

        # --- Rehace el recorte con el tamaño elegido
        def _mostrar_recorte() -> None:
            trozo = biboecf.recorte(self.imagen_zv,             # type: ignore
                                    self.ventana_pano,          # type: ignore
                                    self.factor.get())          # type: ignore
            alto, ancho = trozo.shape[:2]
            self.foto_recorte = tk.PhotoImage(
                data=(kv.CABECERA_PPM.format(ancho=ancho, alto=alto).encode()
                      + trozo.tobytes()), format=kv.FORMATO_PPM)
            self.val_recorte.configure(                         # type: ignore
                image=self.foto_recorte)

        # --- Generar: mide la serie (una toma cada vez, con el progreso en
        #     la ventanita) y, al terminar, el JSON, el libro y, con paño,
        #     la lámina. Mientras, Generar y Preparar inactivos
        def _generar() -> None:
            boton_generar.configure(state="disabled")
            self.escritos = []
            self.leyendo = True
            self.ActivarCarpeta()
            self.medicion = OECF.Medir()
            self.Mensaje(lambda: "")
            _medir_toma()

        # --- Mide la siguiente toma y se vuelve a programar (con after:
        #     entre toma y toma, la ventana atiende al ratón y se repinta)
        def _medir_toma() -> None:
            self.tarea = None
            hechas, total = next(self.medicion)                 # type: ignore
            if hechas < total:
                self.Mensaje(lambda: K.tr(kv.TXT_MIDIENDO).format(
                    n=hechas + 1, total=total), sustituir=True)
                self.update_idletasks()
                self.tarea = self.after(kv.PAUSA_LECTURA, _medir_toma)
                return
            _fin_medida()

        # --- Con la serie medida: el JSON (ya con el análisis) y el libro
        def _fin_medida() -> None:
            self.medicion = None
            grabar_json(OECF)
            ruta = OECF.carpeta / f"{K.NOMBRE}{kv.EXTENSION_LIBRO}"
            # --- Cualquier otro fallo del libro (un dato que no se puede
            #     escribir…) también se dice, con su error, y se sigue
            error = ""
            libro = None
            try:
                libro = biboecf.Libro(ruta, textos_libro(),
                                      OECF.analisis)            # type: ignore
                libro.escribir()
                self.escritos.append(ruta.name)
                texto = kv.TXT_LIBRO
            except OSError:
                texto = kv.TXT_SIN_LIBRO
            except Exception as e:
                texto = kv.TXT_ERROR_LIBRO
                error = f"{type(e).__name__}: {e}"
            self.Mensaje(lambda: K.tr(texto).format(archivo=ruta.name,
                                                    error=error),
                         sustituir=True)

            # --- Y, con lo que calculó el libro, los resultados en el JSON
            #     (para FotoEstación) y la ficha PDF
            if libro is not None:
                grabar_resultados(OECF.carpeta, libro.resultados())
                ficha, archivo, fallo = self.EscribirFicha(libro,
                                                           OECF.carpeta)
                self.Mensaje(lambda: K.tr(ficha).format(archivo=archivo,
                                                        error=fallo))

            # --- Tras medir puede haber incidencias nuevas (la luz que
            #     cambió): al botón y, esa, también a la ventanita
            self.ContarIncidencias()
            luz = next((inc for inc in biboecf.incidencias(OECF)
                        if inc.codigo == biboecf.KI.LUZ_CAMBIO), None)
            if luz is not None:
                self.Mensaje(lambda: Rejilla.texto_incidencia(luz, OECF))

            # --- Con paño, la lámina: al 100 % y, si se eligió otro
            #     tamaño, también en ese. Sin paño, se acaba aquí
            if self.ventana_pano is None:
                _terminar()
                return
            factores = tuple(sorted({biboecf.KTE.FACTORES[0],
                                     self.factor.get()}))       # type: ignore
            zonas = {OECF.NombreZona(t): raw
                     for t, raw in sorted(OECF.zonas.items()) if raw}
            analisis: biboecf.Analisis = OECF.analisis          # type: ignore
            self.lamina = biboecf.Lamina(
                biboecf.RUTA_PLANTILLA, zonas, self.ventana_pano, factores,
                (analisis.alto, analisis.ancho),
                self.TextosCajetin(analisis, OECF.carpeta))
            self.revelado = self.lamina.Revelar()
            self.Mensaje(lambda: "")
            _revelar_zona()

        # --- Revela la siguiente zona de la lámina y se vuelve a programar
        #     (con after, como la medida); al terminar, las escribe
        def _revelar_zona() -> None:
            self.tarea = None
            hechas, total = next(self.revelado)                 # type: ignore
            if hechas < total:
                self.Mensaje(lambda: K.tr(kv.TXT_REVELANDO).format(
                    n=hechas + 1, total=total), sustituir=True)
                self.update_idletasks()
                self.tarea = self.after(kv.PAUSA_LECTURA, _revelar_zona)
                return
            self.revelado = None
            lamina: biboecf.Lamina = self.lamina                # type: ignore
            escritas = []
            for factor in lamina.factores:
                nombre = lamina.nombre(factor)
                self.Mensaje(lambda n=nombre: K.tr(kv.TXT_ESCRIBIENDO).format(
                    archivo=n), sustituir=True)
                self.update_idletasks()
                try:
                    lamina.Escribir(factor, OECF.carpeta / nombre)
                    escritas.append(nombre)
                    self.escritos.append(nombre)
                except OSError:
                    self.Mensaje(lambda n=nombre: K.tr(
                        kv.TXT_SIN_LAMINA).format(archivo=n))
            if escritas:
                self.Mensaje(lambda: K.tr(kv.TXT_LAMINA).format(
                    archivos=kv.SEP_ARCHIVOS.join(escritas)),
                    sustituir=True)
            _terminar()

        # --- Fin de Generar (con láminas o sin ellas): lo dice en la
        #     ventanita y Generar y Preparar, otra vez activos
        def _terminar() -> None:
            self.lamina = None
            self.Mensaje(self.TextoFinalizado)
            boton_generar.configure(state="normal")
            self.leyendo = False
            self.ActivarCarpeta()

            # --- Con exportaciones del revelador ya en la carpeta, se
            #     pregunta si medirlas ahora (si no, siguen ahí para
            #     Analizar revelado)
            n = len(OECF.exportaciones)
            if n and self.Confirmar(
                    kv.TXT_TITULO_TIFF_YA,
                    [K.tr_n(kv.TXT_PREGUNTA_TIFF_YA, n).format(n=n)],
                    kv.TXT_MEDIR):
                self.AnalizarRevelado()

        # --- La caja, con el aviso mientras se mide: la medida bloquea la
        #     ventana un momento
        interior = self.CrearCaja(kv.TXT_FASE_LAMINA, self.ReiniciarLamina)
        aviso = ctk.CTkLabel(interior, text="")
        aviso.pack()
        self.Poner(aviso, kv.TXT_BUSCANDO_PANO)
        self.Traducir()
        self.Ajustar()
        self.update_idletasks()

        # --- Teselas de la Z-V: paño y tarjeta. Hay incidencias nuevas
        OECF.Seleccionar()
        self.ContarIncidencias()
        ventana, seleccion = OECF.pano, OECF.seleccion
        if seleccion is None or not seleccion.hayTarjeta:
            self.Poner(aviso, Rejilla.KR.TXT_SIN_TARJETA)
            self.Traducir()
            self.Ajustar()
            return

        # --- Dos secciones: el recorte (si hay paño; si no, el porqué
        #     queda en el aviso) y una línea como la del marco
        grupo = ctk.CTkFrame(interior, fg_color="transparent")
        grupo.pack(fill="x")
        hay_pano = isinstance(ventana, biboecf.Ventana)
        if hay_pano:
            aviso.pack_forget()
            self.ventana_pano = ventana
            self.imagen_zv = biboecf.revelar(OECF.zonas[0])     # type: ignore
            fondo = self._apply_appearance_mode(
                ctk.ThemeManager.theme["CTk"]["fg_color"])
            self.val_recorte = tk.Label(grupo, bg=fondo, borderwidth=0)
            self.val_recorte.pack(side="left")
            ctk.CTkFrame(grupo, width=kv.GROSOR_MARCO, corner_radius=0,
                         fg_color=ctk.ThemeManager.theme["CTkFrame"]
                         ["border_color"]).pack(side="left", fill="y",
                                                padx=kv.MARGEN)
        else:
            self.Poner(aviso, kv.TXT_PROBLEMA_PANO[ventana])

        # --- A la derecha: arriba, los tamaños (si hay paño; los que no
        #     caben, inactivos) y la ventanita de mensajes; abajo, Generar
        derecha = ctk.CTkFrame(grupo, fg_color="transparent")
        derecha.pack(side="left", fill="both", expand=True)
        arriba = ctk.CTkFrame(derecha, fg_color="transparent")
        arriba.pack(fill="both", expand=True)
        if hay_pano:
            tamanos = ctk.CTkFrame(arriba, fg_color="transparent")
            tamanos.pack(side="left", fill="y", padx=(0, kv.MARGEN))
            self.ApuntarTexto(ctk.CTkLabel(tamanos),
                              kv.TXT_TAMANO).pack(anchor="w")
            caben = biboecf.factores(ventana)                   # type: ignore
            self.factor = ctk.IntVar(value=biboecf.KTE.FACTORES[0])
            for factor in biboecf.KTE.FACTORES:
                opcion = ctk.CTkRadioButton(
                    tamanos, variable=self.factor, value=factor,
                    command=_mostrar_recorte,
                    state="normal" if factor in caben else "disabled")
                self.ApuntarTexto(opcion, kv.TXT_PORCENTAJE,
                                  p=biboecf.porcentaje(factor))
                opcion.pack(anchor="w", pady=(kv.MARGEN, 0))
            _mostrar_recorte()

        marco = ctk.CTkFrame(arriba, fg_color="transparent",
                             border_width=kv.GROSOR_MARCO)
        marco.pack(side="left", fill="both", expand=True)
        self.val_mensajes = ctk.CTkLabel(marco, text="", anchor="nw",
                                         justify="left",
                                         wraplength=kv.ANCHO_MENSAJES)
        self.val_mensajes.pack(fill="both", expand=True, padx=kv.MARGEN,
                               pady=kv.MARGEN)

        # --- Primeros mensajes: las teselas de tarjeta rechazadas y sus
        #     avisos, uno por causa (los mismos textos que en las
        #     incidencias)
        for inc in biboecf.incidencias(OECF):
            if inc.codigo in kv.INCIDENCIAS_TESELAS:
                self.Mensaje(lambda inc=inc: Rejilla.texto_incidencia(inc,
                                                                      OECF))

        # --- Abajo, Generar y, a su izquierda, Abrir resultados: se trae
        #     aquí (el de la Serie queda oculto mientras esté esta caja)
        botones = ctk.CTkFrame(derecha, fg_color="transparent")
        botones.pack(side="bottom", anchor="e", pady=(kv.MARGEN, 0))
        boton_generar = ctk.CTkButton(botones, command=_generar)
        self.ApuntarTexto(boton_generar, kv.TXT_GENERAR)
        boton_generar.pack(side="right")
        self.ResultadosEnSerie(False)
        self.boton_resultados = ctk.CTkButton(
            botones, command=self.AbrirResultados, state="disabled")
        self.ApuntarTexto(self.boton_resultados, kv.TXT_ABRIR_RESULTADOS)
        self.boton_resultados.pack(side="right", padx=(0, kv.MARGEN))
        self.ActivarCarpeta()
        self.Traducir()
        self.Ajustar()

    # --- Añade una línea a la ventanita de mensajes de la caja Lámina, o
    #     sustituye la última (el progreso). linea: cómo se compone (para
    #     rehacerla al cambiar de idioma)
    def Mensaje(self, linea: Callable[[], str],
                sustituir: bool = False) -> None:
        if sustituir and self.lineas:
            self.lineas[-1] = linea
        else:
            self.lineas.append(linea)
        self.Poner(self.val_mensajes,                           # type: ignore
                   lambda: self.KV.SEP_MENSAJES.join(
                       componer() for componer in self.lineas))

    def EscribirFicha(self, libro: biboecf.Libro,
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
            biboecf.Ficha(ruta, textos_libro(), libro).escribir()
        except OSError:
            return kv.TXT_SIN_FICHA, ruta.name, ""
        except Exception as e:
            return kv.TXT_ERROR_FICHA, ruta.name, f"{type(e).__name__}: {e}"
        self.escritos.append(ruta.name)
        return kv.TXT_FICHA, ruta.name, ""

    def ErrorInesperado(self, tipo: type, valor: BaseException,
                        traza: object) -> None:
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

    def MostrarError(self, error: str) -> None:
        """ Ventana de error con el texto del error, traducida. """
        kv = self.KV
        messagebox.showerror(K.tr(kv.TXT_TITULO_ERROR),
                             K.tr(kv.TXT_ERROR_INESPERADO).format(
                                 error=error), parent=self)

    def TextosCajetin(self, analisis: biboecf.Analisis,
                      carpeta: Path) -> tuple[str, ...]:
        """
        Líneas del cajetín de la lámina, de arriba abajo y traducidas: la
        cámara, la latitud de texturas recomendada (de los resultados del
        JSON de la carpeta OECF), la fecha de las tomas (la de la ZV) y el
        soporte, para escribirlo a mano.
        """
        kv = self.KV
        constantes = {nombre: valor
                      for nombre, valor, _ in biboecf.KLI.CONSTANTES}
        zona_zv = constantes[biboecf.KLI.C_ZONA_ZV]
        por_zona = constantes[biboecf.KLI.C_TERCIO_POR_ZONA]
        resultados = leer_resultados(carpeta) or {}
        texturas = resultados.get(biboecf.KLI.J_TEXTURAS) or {}
        recomendada = texturas.get(biboecf.KLI.T_RECOMENDADA) or {}
        sombras, luces, zonas = (recomendada.get(clave)
                                 for clave in biboecf.KLI.TEXTURAS_JSON)
        if None in (sombras, luces, zonas):
            latitud = K.tr(kv.TXT_CAJETIN_SIN_LATITUD)
        else:
            latitud = K.tr(kv.TXT_CAJETIN_LATITUD).format(
                desde=biboecf.Libro.nombre_zona(
                    round((sombras - zona_zv) * por_zona)),
                hasta=biboecf.Libro.nombre_zona(
                    round((luces - zona_zv) * por_zona)),
                zonas=biboecf.Libro.tercios_texto(zonas))
        fecha = ""
        if analisis.fecha:
            dia = datetime.fromisoformat(analisis.fecha)
            fecha = kv.FORMATO_FECHA_CAJETIN.format(
                dia=dia.day, mes=K.tr(kv.TXT_MESES)[dia.month - 1],
                anio=dia.year)
        return (K.tr(kv.TXT_CAJETIN_CAMARA).format(camara=analisis.camara),
                latitud, K.tr(kv.TXT_CAJETIN_FECHA).format(fecha=fecha),
                K.tr(kv.TXT_CAJETIN_SOPORTE))

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

    # --- Pone en el botón de incidencias cuántas hay (o que no hay), lo
    #     activa si las hay y rehace su ventana si está abierta
    def ContarIncidencias(self) -> None:
        boton = self.boton_incidencias
        if boton is None:
            return
        n = len(self.incidencias())
        if n:
            self.Poner(boton, self.KV.TXT_INCIDENCIAS, n=n)
        else:
            self.Poner(boton, self.KV.TXT_SIN_INCIDENCIAS)
        boton.configure(state="normal" if n else "disabled")
        self.rellenar_incidencias()
        self.GrabarIncidencias()

    # --- Graba las incidencias, como en su ventana (o que no hay), en
    #     incidencias.txt de la carpeta OECF, en el idioma de la ventana.
    #     Se rehace cada vez que cambian (Analizar y Generar añaden). Sin
    #     copias (la carpeta OECF no está lista), nada
    def GrabarIncidencias(self) -> None:
        kv = self.KV
        oecf = self.OECF
        if oecf is None or not oecf.copias:
            return
        incidencias = self.incidencias() or [K.tr(kv.TXT_SIN_INCIDENCIAS)]
        try:
            (oecf.carpeta / kv.ARCHIVO_INCIDENCIAS).write_text(
                kv.SEP_INCIDENCIAS.join(incidencias) + kv.SEP_INCIDENCIAS,
                encoding="utf-8")
        except OSError:
            pass

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

        # --- Caja Carpeta (caja_carpeta): los botones Preparar y Analizar
        #     revelado (los enseña, activa y desactiva ActivarCarpeta) y la
        #     variable de la casilla
        self.boton_preparar: ctk.CTkButton
        self.boton_revelado: ctk.CTkButton
        self.ruta: ctk.StringVar

        # --- Explorador de Linux abierto al elegir carpeta (caja_carpeta):
        #     solo uno a la vez; None si no hay ninguno
        self.explorador: subprocess.Popen | None = None

        # --- Respuesta de la confirmación de Preparar (ConfirmarPreparar)
        self.confirmado: bool = False

        # --- Caja Serie (caja_serie): Abrir resultados, en el pie de la
        #     rejilla (None sin caja Serie). Con Generar a la vista, el que
        #     vale es el de la caja Lámina, a su lado, y el de la Serie se
        #     guarda oculto. boton_resultados es el que se ve (lo activa
        #     ActivarCarpeta)
        self.boton_resultados: ctk.CTkButton | None
        self.boton_resultados_serie: ctk.CTkButton | None

        # --- Caja Ayuda (caja_ayuda): el botón de nueva versión, oculto
        #     hasta saber que la hay, y el grupo de Idioma, para ponerlo
        #     delante de él. La versión publicada la escribe el hilo de
        #     ComprobarVersion y la lee MostrarVersion: None hasta saberla
        #     (o si no se pudo) y si ya se comprobó
        self.boton_version: ctk.CTkButton
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
        self.boton_incidencias: ctk.CTkButton | None

        # --- Caja Lámina (ReiniciarLamina): la Z-V revelada (para el
        #     recorte), la ventana del paño, el tamaño elegido (divisor),
        #     la etiqueta del recorte y su imagen (se guarda: si no, Python
        #     la borra)
        self.imagen_zv: np.ndarray | None
        self.ventana_pano: biboecf.Ventana | None
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
        self.val_lamina_tiff: ctk.CTkLabel | None
        self.analisis_revelado: biboecf.Analisis | None
        self.tiff_pendientes: list[tuple[int, Path]]
        self.tiff_medidos: dict[int, float | str]
        self.lamina_tiff: biboecf.Lamina | None
        self.revelado_tiff: Iterator[tuple[int, int]] | None

        # --- La ventanita de mensajes de la caja Lámina y cómo se compone
        #     cada línea (para rehacerla al cambiar de idioma)
        self.val_mensajes: ctk.CTkLabel | None
        self.lineas: list[Callable[[], str]]

        # --- La medida en marcha (OECF.Medir), al pulsar Generar, y la
        #     lámina con su revelado en marcha (Lamina.Revelar)
        self.medicion: Iterator[tuple[int, int]] | None
        self.lamina: biboecf.Lamina | None
        self.revelado: Iterator[tuple[int, int]] | None

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
        self.ReiniciarLamina()
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
        self.lienzo.bind("<Configure>", self.EstirarCuerpo)
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

    # --- Valores iniciales de las variables de la caja Cámara (se
    #     declaran en el __init__): al arrancar y al quitar la caja
    def ReiniciarCam(self) -> None:
        self.OECF = None
        self.propias_cam = 0
        self.val_archivo = None
        self.val_bits = None
        self.val_exp = None
        self.val_fecha = None
        self.val_modelo = None

    # --- Valores iniciales de las variables de la caja Serie (se
    #     declaran en el __init__): al arrancar y al quitar la caja
    def ReiniciarSerie(self) -> None:
        self.copia = None
        self.incidencias = list
        self.lectura = None
        self.leyendo = False
        self.rejilla = None
        self.boton_resultados = None
        self.boton_resultados_serie = None
        self.tarea = None
        self.texto_incidencias = None
        self.ventana_incidencias = None
        self.propias_serie = 0
        self.boton_incidencias = None

    # --- Valores iniciales de las variables de la caja Revelado (se
    #     declaran en el __init__): al arrancar y al quitar la caja
    def ReiniciarRevelado(self) -> None:
        self.caja_revelado = None
        self.val_revelado = None
        self.val_lamina_tiff = None
        self.analisis_revelado = None
        self.tiff_pendientes = []
        self.tiff_medidos = {}
        self.lamina_tiff = None
        self.revelado_tiff = None

    # --- Valores iniciales de las variables de la caja Lámina (se
    #     declaran en el __init__): al arrancar y al quitar la caja
    def ReiniciarLamina(self) -> None:
        self.ResultadosEnSerie(True)
        self.imagen_zv = None
        self.ventana_pano = None
        self.factor = None
        self.val_recorte = None
        self.foto_recorte = None
        self.val_mensajes = None
        self.lineas = []
        self.medicion = None
        self.lamina = None
        self.revelado = None

    # --- Abrir resultados de la caja Serie, en el pie de la rejilla
    #     (poner) o fuera de él, oculto (lo trae la caja Lámina junto a
    #     Generar). Al ponerlo, vuelve a ser el que se ve. Sin caja Serie,
    #     nada
    def ResultadosEnSerie(self, poner: bool) -> None:
        rejilla, boton = self.rejilla, self.boton_resultados_serie
        if (rejilla is None or boton is None or rejilla.pie is None
                or not rejilla.winfo_exists()):
            return
        izquierdo, resumen, derechos, sep = rejilla.pie
        analizar = derechos[-1]
        if not poner:
            rejilla.poner_pie(izquierdo, resumen, (analizar,), sep)
            return
        rejilla.poner_pie(izquierdo, resumen, (boton, analizar), sep)
        self.boton_resultados = boton
        self.ActivarCarpeta()

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

    # --- Ajusta la ventana al contenido (llamar tras añadir filas). Si no
    #     cabe en el alto del monitor, la ventana se queda en ese alto, el
    #     contenido se desplaza y aparece la barra
    def Ajustar(self) -> None:

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
        def _repintar() -> None:
            pendientes: list[tk.Misc] = [self]
            while pendientes:
                elemento = pendientes.pop()
                elemento.event_generate(
                    self.KV.TK_REDIBUJAR, x=0, y=0,
                    width=elemento.winfo_width(),
                    height=elemento.winfo_height())
                pendientes.extend(elemento.winfo_children())

        for espera in self.KV.ESPERAS_REPINTADO:
            self.after(espera, _repintar)

    # --- Coloca la ventana centrada en horizontal y arriba del monitor
    #     principal: al añadir filas crece hacia abajo sin salirse
    def Centrar(self) -> None:
        x, y, ancho, _ = self.MonitorPrincipal()

        # --- Centrada en horizontal y arriba de ese monitor
        x += (ancho - self.winfo_width()) // 2
        y += self.KV.ARRIBA
        self.geometry(self.KV.TK_POSICION.format(x=x, y=y))

    def MeterEnMonitor(self) -> None:
        """Si la ventana se sale del monitor principal (al crecer con
        filas nuevas, o en una pantalla pequeña), la mueve lo justo para
        que quepa. Si cabe, no la toca: respeta que se haya movido a
        mano."""
        mx, my, m_ancho, m_alto = self.MonitorPrincipal()

        # --- Posición actual, en las mismas unidades en que se pide
        _, x_txt, y_txt = tk.Tk.wm_geometry(self).split(self.KV.SEP_POSICION)
        x_antes, y_antes = int(x_txt), int(y_txt)

        # --- Que no pase del borde derecho ni del de abajo; y, si es más
        #     grande que el monitor, que empiece en su borde izquierdo y en
        #     el de arriba
        x = max(mx, min(x_antes, mx + m_ancho - self.winfo_reqwidth()))
        y = max(my, min(y_antes, my + m_alto - self.winfo_reqheight()))
        if (x, y) != (x_antes, y_antes):
            self.geometry(self.KV.TK_POSICION.format(x=x, y=y))

    # --- Posición y tamaño del monitor principal: (x, y, ancho, alto). Tk
    #     ve todos los monitores como una sola pantalla. Si no se pueden
    #     leer los monitores, toda la pantalla de Tk
    def MonitorPrincipal(self) -> tuple[int, int, int, int]:
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

    # --- El cuerpo, tan ancho como el lienzo: así las filas se estiran
    #     si la ventana se ensancha
    def EstirarCuerpo(self, evento: tk.Event) -> None:
        self.lienzo.itemconfigure(self.id_cuerpo, width=evento.width)

    # --- Rueda del ratón: desplaza el contenido, solo si no cabe (con la
    #     barra a la vista) y si el ratón está en esta ventana (no en la
    #     de incidencias, que tiene su propio desplazamiento)
    def Rueda(self, evento: tk.Event) -> None:
        widget = evento.widget
        if (not self.barra.winfo_ismapped()
                or not isinstance(widget, tk.Misc)
                or widget.winfo_toplevel() is not self):
            return
        arriba = (evento.num == self.KV.BOTON_RUEDA_ARRIBA
                  or getattr(evento, "delta", 0) > 0)
        self.lienzo.yview_scroll(
            -self.KV.LINEAS_RUEDA if arriba else self.KV.LINEAS_RUEDA,
            "units")

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

    # --- Se calcula cada vez a partir de la casilla (self.ruta), así que
    #     siempre está al día
    @property
    def carpetaEscrita(self) -> Path:
        """ Saber la carpeta escrita en la casilla, como ruta: así «/a/b» y
            «/a/b/» son la misma, y «~» es la carpeta del usuario. """
        return Path(self.ruta.get().strip()).expanduser()

    # --- Preparar: lanza la serie de la carpeta elegida, quitando antes
    #     la de la preparación anterior. Vuelve a leer la carpeta (rehace
    #     la Cámara): pueden haber cambiado sus archivos desde que se
    #     eligió (borrados a mano…) y la serie se copia de los que hay
    def Preparar(self) -> None:
        if not self.ConfirmarPreparar():
            return
        self.QuitarCajas(self.__propias_carpeta)
        self.caja_cam()
        if biboecf.problema_carpeta(self.OECF) is not None:     # type: ignore
            return
        self.caja_serie(self.OECF)                              # type: ignore

    # --- Preparar vacía la carpeta OECF (salvo las exportaciones del
    #     revelador y las subcarpetas): si ya tiene el análisis, se pide
    #     confirmación, con Cancelar por defecto, y se dice que las
    #     exportaciones se conservan. Sin análisis, sí sin preguntar
    def ConfirmarPreparar(self) -> bool:
        kv = self.KV
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        if not hay_analisis(oecf.carpeta):
            return True
        lineas = [K.tr(kv.TXT_YA_ANALISIS), K.tr(kv.TXT_SE_BORRARA)]
        n = len(oecf.exportaciones)
        if n:
            lineas.insert(1, K.tr_n(kv.TXT_TIFF_SE_CONSERVAN, n).format(n=n))
        return self.Confirmar(kv.TXT_TITULO_CONFIRMAR, lineas,
                              kv.TXT_PREPARAR)

    # --- Pregunta con una ventanita modal de CTk, centrada sobre la
    #     principal: el mensaje (sus líneas) y, a la derecha, Cancelar y el
    #     botón que acepta (texto_si). Intro, Escape y cerrar la ventana
    #     cancelan. La respuesta, también en self.confirmado
    def Confirmar(self, titulo: dict, lineas: list[str],
                  texto_si: dict) -> bool:
        kv = self.KV

        def _responder(si: bool) -> None:
            self.confirmado = si
            dialogo.destroy()

        self.confirmado = False
        dialogo = ctk.CTkToplevel(self)
        dialogo.title(K.tr(titulo))
        dialogo.transient(self)
        dialogo.resizable(False, False)
        ctk.CTkLabel(dialogo, text=kv.SEP_LINEAS.join(lineas), justify="left",
                     wraplength=kv.ANCHO_CONFIRMAR).pack(
            padx=2 * kv.MARGEN, pady=(2 * kv.MARGEN, kv.MARGEN))
        botones = ctk.CTkFrame(dialogo, fg_color="transparent")
        botones.pack(fill="x", padx=2 * kv.MARGEN, pady=(0, 2 * kv.MARGEN))
        ctk.CTkButton(botones, text=K.tr(texto_si),
                      command=lambda: _responder(True)).pack(
            side="right", padx=(kv.MARGEN, 0))
        ctk.CTkButton(botones, text=K.tr(kv.TXT_CANCELAR),
                      command=lambda: _responder(False)).pack(side="right")
        for tecla in kv.TECLAS_CANCELAR:
            dialogo.bind(tecla, lambda _: _responder(False))
        dialogo.protocol(kv.TK_CERRAR, lambda: _responder(False))

        dialogo.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width()
                                  - dialogo.winfo_reqwidth()) // 2
        y = self.winfo_rooty() + (self.winfo_height()
                                  - dialogo.winfo_reqheight()) // 2
        dialogo.geometry(kv.TK_POSICION.format(x=x, y=y))
        dialogo.wait_visibility()
        dialogo.grab_set()
        dialogo.focus_set()
        self.wait_window(dialogo)
        return self.confirmado

    # --- Analizar: quita la caja Lámina anterior (si la hay) y la crea
    def Analizar(self) -> None:
        self.QuitarCajas(self.propias_serie)
        self.caja_lamina(self.OECF)                             # type: ignore

    # --- En un hilo aparte (no puede tocar la ventana): pregunta a
    #     GitHub la versión publicada y apunta que ya está comprobada
    def ComprobarVersion(self) -> None:
        try:
            self.version_publicada = version_publicada()
        except Exception as e:
            self.error_version = f"{type(e).__name__}: {e}"
        self.version_comprobada = True

    # --- Mira cada poco si el hilo ya respondió. Si hay una versión más
    #     nueva, enseña su botón a la derecha de Ayuda
    def MostrarVersion(self) -> None:
        if not self.version_comprobada:
            self.after(self.KV.PAUSA_VERSION, self.MostrarVersion)
            return
        if self.error_version is not None:
            self.MostrarError(self.error_version)
            return
        publicada = self.version_publicada
        if publicada is None or not es_mas_nueva(publicada, K.version):
            return
        self.Poner(self.boton_version, self.KV.TXT_NUEVA_VERSION,
                   version=publicada)
        self.boton_version.pack(side="left", padx=(self.KV.MARGEN, 0),
                                before=self.grupo_idioma)
        self.Ajustar()

    # --- Botones, sin estar leyendo una serie: Preparar (caja Carpeta),
    #     activo si la carpeta sirve; Abrir resultados (pie de la rejilla,
    #     si hay caja Serie), solo si ya se prepararon las copias
    def ActivarCarpeta(self) -> None:
        libre = self.OECF is not None and not self.leyendo
        preparar = (libre and biboecf.problema_carpeta(         # type: ignore
            self.OECF) is None)
        resultados = libre and bool(self.OECF.copias)           # type: ignore
        self.boton_preparar.configure(
            state="normal" if preparar else "disabled")

        # --- Analizar revelado: a la vista si la carpeta OECF ya tiene el
        #     análisis; activo si además hay exportaciones del revelador
        oecf = self.OECF
        hay = oecf is not None and hay_analisis(oecf.carpeta)
        if hay and not self.boton_revelado.winfo_ismapped():
            self.boton_revelado.pack(side="right", padx=(self.KV.MARGEN, 0),
                                     after=self.boton_preparar)
        elif not hay and self.boton_revelado.winfo_ismapped():
            self.boton_revelado.pack_forget()
        revelado = hay and libre and bool(oecf.exportaciones)  # type: ignore
        self.boton_revelado.configure(
            state="normal" if revelado else "disabled")
        if self.boton_resultados is not None:
            self.boton_resultados.configure(
                state="normal" if resultados else "disabled")

    # --- Segunda parte del análisis: mide las exportaciones del revelador
    #     (las TIFF de la carpeta OECF) en las mismas teselas que el
    #     análisis del JSON. En su propia caja, encima de la Cámara (quita
    #     las que hubiera: Serie, Lámina o un Revelado anterior)
    def AnalizarRevelado(self) -> None:
        kv = self.KV
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        analisis = leer_analisis(oecf.carpeta)
        if analisis is None:
            return
        self.QuitarCajas(self.propias_cam)
        self.caja_revelado = self.CrearCaja(kv.TXT_FASE_REVELADO,
                                            self.ReiniciarRevelado)
        self.val_revelado = ctk.CTkLabel(self.caja_revelado, text="",
                                         wraplength=kv.ANCHO_REVELADO)
        self.val_revelado.pack()
        self.analisis_revelado = analisis
        self.tiff_pendientes = sorted(oecf.exportaciones.items())
        self.tiff_medidos = {}
        self.escritos = []
        self.leyendo = True
        self.ActivarCarpeta()
        self.Traducir()
        self.Ajustar()
        self.MedirTiff()

    # --- Mide la siguiente exportación y se vuelve a programar (con
    #     after: la ventana atiende entre una y otra). Al terminar, guarda
    #     el L* del revelador en el JSON y rehace el libro
    def MedirTiff(self) -> None:
        kv = self.KV
        self.tarea = None
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        analisis: biboecf.Analisis = self.analisis_revelado     # type: ignore
        if self.tiff_pendientes:
            total = len(self.tiff_medidos) + len(self.tiff_pendientes)
            n = len(self.tiff_medidos) + 1
            self.Poner(self.val_revelado,                       # type: ignore
                       lambda: K.tr(kv.TXT_MIDIENDO_REVELADO).format(
                           n=n, total=total))
            self.update_idletasks()
            tercio_ev, ruta = self.tiff_pendientes.pop(0)
            self.tiff_medidos[tercio_ev] = biboecf.lstar_tiff(analisis, ruta)
            self.tarea = self.after(kv.PAUSA_LECTURA, self.MedirTiff)
            return

        # --- Las 31 zonas, en orden: el L* medido o NaN (sin TIFF, o si no
        #     se pudo medir)
        medidos = self.tiff_medidos
        revelador = tuple(
            float(medidos[t]) if isinstance(medidos.get(t), float)
            else math.nan
            for t in range(-biboecf.KS.TERCIOS_LADO,
                           biboecf.KS.TERCIOS_LADO + 1))
        validas = sum(not math.isnan(v) for v in revelador)
        analisis = analisis._replace(revelador=revelador)
        guardado = grabar_analisis(oecf.carpeta, analisis)
        ruta = oecf.carpeta / f"{K.NOMBRE}{kv.EXTENSION_LIBRO}"
        # --- Cualquier fallo del libro se dice, con su error, y se sigue
        #     (si no, la caja se queda a medias)
        libro = None
        escrito = False
        error = ""
        try:
            libro = biboecf.Libro(ruta, textos_libro(), analisis)
            libro.escribir()
            self.escritos.append(ruta.name)
            escrito = True
        except OSError:
            pass
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        texto = (kv.TXT_REVELADO_HECHO if guardado and escrito
                 else kv.TXT_REVELADO_FALLO)
        # --- Y, si alguna no se pudo medir, cuáles y por qué
        rutas = dict(self.OECF.exportaciones)                   # type: ignore
        problemas = [K.tr(kv.TXT_PROBLEMAS_TIFF[codigo]).format(
            archivos=kv.SEP_ARCHIVOS.join(
                rutas[t].name for t, v in sorted(medidos.items())
                if v == codigo))
            for codigo in kv.TXT_PROBLEMAS_TIFF
            if codigo in medidos.values()]
        lineas = [K.tr(texto).format(n=validas, total=len(medidos),
                                     archivo=ruta.name)]
        if error:
            lineas.append(K.tr(kv.TXT_ERROR_LIBRO).format(archivo=ruta.name,
                                                          error=error))
        if libro is not None:
            grabar_resultados(oecf.carpeta, libro.resultados())
            ficha, archivo, fallo = self.EscribirFicha(libro, oecf.carpeta)
            lineas.append(K.tr(ficha).format(archivo=archivo, error=fallo))
        lineas += problemas
        self.Poner(self.val_revelado,                           # type: ignore
                   kv.SEP_LINEAS.join(lineas))

        # --- Abrir resultados, al pie de la caja
        boton = ctk.CTkButton(self.caja_revelado,               # type: ignore
                              command=self.AbrirResultados)
        self.ApuntarTexto(boton, kv.TXT_ABRIR_RESULTADOS)
        boton.pack(side="bottom", anchor="e", pady=(kv.MARGEN, 0))
        self.Traducir()
        self.Ajustar()

        # --- Con paño, si se quiere, las láminas otra vez, ya con el
        #     revelado del revelador (las mismas que haya; al menos la del
        #     100 %)
        if (isinstance(analisis.pano, biboecf.Ventana) and validas
                and self.Confirmar(kv.TXT_TITULO_LAMINAS,
                                   [K.tr(kv.TXT_PREGUNTA_LAMINAS)],
                                   kv.TXT_REHACER)):
            self.EmpezarLaminaTiff(analisis)
            return
        self.analisis_revelado = None
        self.leyendo = False
        self.ActivarCarpeta()

    # --- Láminas desde las exportaciones del revelador: las mismas que ya
    #     haya en la carpeta OECF (al menos la del 100 %), con su progreso
    #     en la segunda línea de la caja Revelado
    def EmpezarLaminaTiff(self, analisis: biboecf.Analisis) -> None:
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        zonas = {oecf.NombreZona(t): ruta
                 for t, ruta in sorted(oecf.exportaciones.items())
                 if isinstance(self.tiff_medidos.get(t), float)}
        prueba = biboecf.Lamina(biboecf.RUTA_PLANTILLA, {}, analisis.pano,
                                biboecf.KTE.FACTORES,
                                (analisis.alto, analisis.ancho))
        factores = tuple(f for f in biboecf.KTE.FACTORES
                         if f == biboecf.KTE.FACTORES[0]
                         or (oecf.carpeta / prueba.nombre(f)).exists())
        self.lamina_tiff = biboecf.Lamina(
            biboecf.RUTA_PLANTILLA, zonas, analisis.pano,       # type: ignore
            factores, (analisis.alto, analisis.ancho),
            self.TextosCajetin(analisis, oecf.carpeta))
        self.revelado_tiff = self.lamina_tiff.Revelar()
        self.val_lamina_tiff = ctk.CTkLabel(
            self.caja_revelado, text="",                        # type: ignore
            wraplength=self.KV.ANCHO_REVELADO)
        self.val_lamina_tiff.pack(pady=(self.KV.MARGEN, 0))
        self.LeerLaminaTiff()

    # --- Lee la siguiente exportación para la lámina y se vuelve a
    #     programar; al terminar, escribe las láminas
    def LeerLaminaTiff(self) -> None:
        kv = self.KV
        self.tarea = None
        hechas, total = next(self.revelado_tiff)                # type: ignore
        if hechas < total:
            self.Poner(self.val_lamina_tiff,                    # type: ignore
                       lambda: K.tr(kv.TXT_LEYENDO_LAMINA).format(
                           n=hechas + 1, total=total))
            self.update_idletasks()
            self.tarea = self.after(kv.PAUSA_LECTURA, self.LeerLaminaTiff)
            return
        oecf: biboecf.OECF = self.OECF                          # type: ignore
        lamina: biboecf.Lamina = self.lamina_tiff               # type: ignore
        escritas, fallos = [], []
        for factor in lamina.factores:
            nombre = lamina.nombre(factor)
            self.Poner(self.val_lamina_tiff,                    # type: ignore
                       lambda n=nombre: K.tr(kv.TXT_ESCRIBIENDO).format(
                           archivo=n))
            self.update_idletasks()
            try:
                lamina.Escribir(factor, oecf.carpeta / nombre)
                escritas.append(nombre)
                self.escritos.append(nombre)
            except OSError:
                fallos.append(nombre)
        texto = kv.TXT_LAMINA if not fallos else kv.TXT_SIN_LAMINA
        archivos = kv.SEP_ARCHIVOS.join(escritas or fallos)
        self.Poner(self.val_lamina_tiff,                        # type: ignore
                   lambda: kv.SEP_LINEAS.join((
                       K.tr(texto).format(archivos=archivos,
                                          archivo=archivos),
                       self.TextoFinalizado())))
        self.revelado_tiff = None
        self.lamina_tiff = None
        self.analisis_revelado = None
        self.leyendo = False
        self.ActivarCarpeta()
        self.Ajustar()

    # --- Abre los resultados: la carpeta OECF de la serie, en el
    #     explorador de archivos del sistema
    def AbrirResultados(self) -> None:
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
        self.title(f"{K.NOMBRE} - {K.tr(self.KV.TXT_VERSION)} {K.version}")
        for elemento, componer in self._textos.items():
            elemento.configure(text=componer())

        # --- La rejilla dibuja sus textos («falta»…) en el Canvas
        if self.rejilla is not None:
            self.rejilla.dibujar()
        self.rellenar_incidencias()
        self.Ajustar()

    # --- Cambia el idioma activo al elegido en la lista
    def CambiarIdioma(self, nombre: str) -> None:
        for codigo, nombre_idioma in K.IDIOMAS.items():
            if nombre_idioma == nombre:
                K.idioma = codigo
        self.Traducir()

    # endregion Gestión del idioma
