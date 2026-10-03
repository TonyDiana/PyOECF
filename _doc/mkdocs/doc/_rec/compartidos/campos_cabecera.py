"""
Detecta bloques ":Campo: valor" consecutivos (la cabecera custom de
docstring usada en el proyecto: :Propósito:, :Autor:, :Versión:, etc.)
y los convierte en una tabla HTML sencilla antes de que Python-Markdown
procese el resto del texto.

Soporta el estilo reST de "campo sin valor en la misma línea, valor en la
línea siguiente indentada" (p.ej. ``:Propósito:`` seguido de una línea
aparte con la descripción), no solo ``:Campo: valor`` en una sola línea.
"""

import re
import markdown
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

_CAMPO_RE = re.compile(r"^:([^:]+):[ \t]*(.*)$")
_INDENTADA_RE = re.compile(r"^[ \t]+\S")


def _valor_html(valor: str) -> str:
    """Convierte el valor de un campo (puede llevar *cursiva*, **negrita**,
    ``code``...) a HTML en línea, sin el <p> que envuelve markdown.markdown()."""
    html = markdown.markdown(valor)
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[len("<p>"):-len("</p>")]
    return html


class CamposCabeceraPreprocessor(Preprocessor):
    def run(self, lines):
        salida = []
        i, n = 0, len(lines)
        while i < n:
            bloque = []
            j = i
            while j < n and (m := _CAMPO_RE.match(lines[j])):
                campo, valor = m.group(1), m.group(2).strip()
                j += 1
                if not valor:
                    # Valor en línea(s) siguiente(s) indentada(s), no en la
                    # misma línea que ":Campo:"
                    continuacion = []
                    while (
                        j < n
                        and lines[j].strip()
                        and _INDENTADA_RE.match(lines[j])
                        and not _CAMPO_RE.match(lines[j])
                    ):
                        continuacion.append(lines[j].strip())
                        j += 1
                    valor = " ".join(continuacion)
                bloque.append((campo, valor))
            if len(bloque) >= 2:
                salida.append("")
                salida.append('<table class="campos-cabecera">')
                for campo, valor in bloque:
                    salida.append(
                        f"<tr><th>{campo.strip()}</th><td>{_valor_html(valor.strip())}</td></tr>"
                    )
                salida.append("</table>")
                salida.append("")
                i = j
            else:
                salida.append(lines[i])
                i += 1
        return salida


class CamposCabeceraExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(CamposCabeceraPreprocessor(md), "campos_cabecera", 27)


def makeExtension(**kwargs):
    return CamposCabeceraExtension(**kwargs)
