#!/usr/bin/env bash
# cSpell:ignore venv
# --- Arranca PyOECF con el Python del entorno del proyecto (.venv): no
#     hace falta activarlo, ese Python ya usa sus bibliotecas
cd "$(dirname "$(readlink -f "$0")")" || exit 1
exec .venv/bin/python src/main.py "$@"
