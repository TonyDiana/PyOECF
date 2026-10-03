#!/usr/bin/env bash
# mkgen.sh - Motor generico compartido: lanza MkDocs con el venv de Repo,
# sobre el mkdocs.yml del proyecto que invoca su symlink "mk" local
# (no sobre Repo). Lo especial de cada proyecto vive en su mkdocs.yml, no
# aqui - ver Repo/_doc/mkdocs/base.yml.

set -euo pipefail

VENV_MKDOCS="$HOME/Dev/Python/Bibliotecas/Repo/.venv/bin/mkdocs"
PROYECTO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Direccion del "serve": puerto estable y distinto por proyecto, derivado del
# nombre del repo (PROYECTO es <repo>/_doc/mkdocs). Asi cada proyecto es un
# origen distinto y el navegador no mezcla su cache de favicon con la de otro
# (con un puerto unico y la misma ruta _rec/local/logo_slp.png en todos, se
# pisaban). Unico sitio donde vive el puerto: no hay dev_addr en base.yml.
HOST_SERVE="127.0.0.1"
PUERTO_BASE=9000
NOMBRE_REPO="$(basename "$(cd "$PROYECTO/../.." && pwd)")"
PUERTO_SERVE=$(( PUERTO_BASE + ( $(printf '%s' "$NOMBRE_REPO" | cksum | cut -d' ' -f1) % 1000 ) ))

cd "$PROYECTO"

# PYTHONPATH sobre doc/_rec/compartidos_slr/: necesario para que Python-Markdown
# pueda importar campos_cabecera.py (u otra extension propia) directamente
# por su nombre. Vive DENTRO de docs_dir (doc/) a proposito: es lo unico que
# hace que "mkdocs serve/build" copie tambien compartidos_slr/extra.css al
# sitio (solo copia lo que cae dentro de docs_dir).
export PYTHONPATH="$PROYECTO/doc/_rec/compartidos_slr${PYTHONPATH:+:$PYTHONPATH}"

case "${1:-serve}" in
    serve)
        # Sin "&&": al cortar con Ctrl+C, "serve" sale con codigo de error
        # (interrumpido por señal) y "set -e" abortaria antes del build.
        # El "|| true" absorbe solo esa salida esperada, para que el build
        # del estatico se genere siempre al terminar el serve.
        echo "Sirviendo $NOMBRE_REPO en http://$HOST_SERVE:$PUERTO_SERVE"
        "$VENV_MKDOCS" serve --livereload --dev-addr="$HOST_SERVE:$PUERTO_SERVE" || true
        "$VENV_MKDOCS" build --clean
        ;;
    build) "$VENV_MKDOCS" build --clean ;;
    *) echo "Uso: mk [serve|build]" >&2; exit 1 ;;
esac
