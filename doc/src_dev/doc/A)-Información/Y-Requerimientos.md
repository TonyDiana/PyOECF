# Requerimientos

<!-- cSpell:ignore venv -->

Este producto tiene una fuerte dependencia de bibliotecas externas: la lectura de los RAW, el cálculo, el libro Excel, las láminas PSD, la ficha PDF y la ventana.

- **Única fuente:** `rec/requirements/requirements.conf`. Las tablas de esta página salen de él al construir la ayuda: para cambiar un paquete o una versión, se cambia allí.
- **Python:** el del sistema. El código usa sintaxis de Python 3.10 o posterior.
- **Instalación:** `rec/requirements/requirements_slr.sh`, desde la raíz del repo:
    - `--mostrar`: enseña lo que instalaría y dónde, sin tocar nada.
    - `--deploy`: instala lo del sistema y el venv para usar la aplicación.
    - `--dev`: lo mismo y, además, lo de desarrollo.

<!-- requisitos -->
