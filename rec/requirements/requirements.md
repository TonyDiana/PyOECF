# Requerimientos

# Instalación forzada contra el PEP668 (Marking Python base environments as 'externally managed')

pip install Flask~=3.1 --break-system-packages

- Framework web Flask:
    - [Documentación oficial](https://flask.palletsprojects.com/en/stable/)
    - [Traducción oficial al español](https://flask.palletsprojects.com/es/stable/)
    - [Tutorial en Español](https://j2logo.com/tutorial-flask-espanol/)

- [platformdirs](https://platformdirs.readthedocs.io/en/latest/): Variables del sistema en cualquier SO.

## Copia de seguridad de MkDocs y su ecosistema (2026-09-14)

El equipo de Material for MkDocs avisó (post del 2026-02-18, enlazado desde el
propio aviso que sale en cada `build --strict`) de que **MkDocs 2.0** —
próxima versión del framework base, sin fecha ni licencia claras todavía —
romperá sin ruta de migración todo lo montado aquí: plugins y overrides de
tema dejarán de funcionar. Por eso, además de fijar versión con `~=` en
`requirements.txt`, se guardan aquí los `sdist` reales (descargados de PyPI,
no de GitHub, mismo criterio que ya se usó con `cryptography`/`bcrypt` en
Criptex) de todo el árbol de dependencias en uso — por si en algún momento
dejan de estar disponibles o de instalar bien contra un MkDocs más nuevo:

- **`mkdocs-1.6.1.tar.gz`** — el framework base.
- **`mkdocs_material-9.7.7.tar.gz`** — tema, trae el plugin `offline`
  (búsqueda funcional bajo `file://`, ver `_doc/mkdocs/RESUMEN.md`).
- **`mkdocs_autorefs-1.4.4.tar.gz`** — plugin `autorefs`, referencias
  automáticas a secciones/figuras.
- **`mkdocstrings-1.0.6.tar.gz`** / **`mkdocstrings_python-2.0.8.tar.gz`** —
  genera la documentación de API a partir de docstrings reales (vía AST, sin
  importar el código — ver hallazgo principal de `_doc/mkdocs/RESUMEN.md`).
- **`griffelib-2.3.0.tar.gz`** — analizador AST del que depende
  `mkdocstrings-python` (paquete real en PyPI, aunque el proyecto se llama
  "Griffe"; no confundir con un paquete `griffe` aparte).
- **`pymdown_extensions-10.21.3.tar.gz`** — extensiones de Markdown
  (`superfences`, `snippets`, resaltado de código, etc.).
- **`mkdocs_macros_plugin-1.5.0.tar.gz`** — plugin `macros`, variables
  `{{ }}` en las páginas.
- **`mkdocs_glightbox-0.5.2.tar.gz`** — plugin `glightbox`, imágenes en modal.
- **`mkdocs_to_pdf-0.11.2.tar.gz`** — plugin `to-pdf`, exportación a PDF.
- **`mkdocs_get_deps-0.2.2.tar.gz`** / **`mkdocs_material_extensions-1.3.1.tar.gz`**
  — dependencias transitivas de `mkdocs-material`.

Todas las versiones son las que de verdad están instaladas en `Repo/.venv`
en la fecha de esta nota (`pip list`), no solo el rango `~=` de
`requirements.txt` — así la copia reproduce exactamente lo que ya se validó
funcionando, no una versión futura dentro del rango que podría no estar
probada.