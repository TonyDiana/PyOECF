#!/usr/bin/env bash

# Autor:     Tony Diana
# Versión:   26.03.28

# =============================================================================
# Para Sincronizar la rama Submodule desde la rama master:
#   - Elimina los archivos que no deben desplegarse
#
# Debe ejecutarse estando en la rama master, sin cambios sin commit.
# Puede lanzarse desde cualquier ubicación dentro del repo.
# =============================================================================
# read -p "Pulsa ENTER para continuar..."

# --- Versión normal
set -euo pipefail
# --- Versión desarrollo
# set -euxo pipefail

# --- Elementos a eliminar ----------------------------------------------------
REMOVE_PATHS=(
    "__UsarEste"
    "_doc/src"
    "_doc/_temp"
    ".vscode"
    "rec"
    ".gitignore"
)

# --- Configuración -----------------------------------------------------------
BASE_BRANCH="master"

# --- Localización del repo y del script --------------------------------------
REPO_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"


# --- Verificar rama actual ---------------------------------------------------
if [[ "${1:-}" != "--sin-verificar" ]]; then
    echo "==> Verificando rama actual"
    _Current_Branch="$(git rev-parse --abbrev-ref HEAD)"
    if [[ "$_Current_Branch" != "$BASE_BRANCH" ]]; then
        echo ""
        echo "ERROR: Debes estar en '$BASE_BRANCH'. Estás en '$_Current_Branch'."
        echo ""
        exit 1
    fi
    echo "==> OK: Estás en la rama correcta ($BASE_BRANCH)"


    # --- Verificar que no hay cambios sin commit -----------------------------
    echo "==> Verificando que no hay cambios sin commit"
    if ! git diff-index --quiet HEAD --; then
        echo "ERROR: Tienes cambios sin commit en '$BASE_BRANCH'."
        exit 1
    fi
    echo "==> OK: Rama limpia"
fi

# --- Eliminar rutas no deseadas ----------------------------------------------
echo "==> Eliminando rutas no deseadas"
for path in "${REMOVE_PATHS[@]}"; do
    echo "   - $path"
    git rm -r --cached --ignore-unmatch "$path"
    rm -rf -- "$REPO_ROOT/$path"
done
