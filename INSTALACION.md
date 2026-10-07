# Instalación de PyOECF


## Opción 1: ejecutable (recomendada)

No necesita instalar nada más.

1. Entre en la [última versión publicada](https://github.com/TonyDiana/PyOECF/releases/latest) y descargue el archivo de su sistema: Windows, macOS o Linux.

2. La primera vez que lo abra, el sistema puede avisar de que el programa no está firmado:

    - **Windows**: aparece «Windows protegió su PC». Pulse **Más información** y después **Ejecutar de todas formas**.

    - **macOS**: solo para equipos con Apple Silicon (M1 o posterior). Si dice que no se puede abrir, haga **clic derecho** sobre la aplicación y elija **Abrir**.

    - **Linux**: descomprima el archivo y haga doble clic en `PyOECF`.


## Opción 2: desde el código fuente

1. Instale **Python 3.14**.

2. Solo en **Linux**: instale el paquete del sistema de Tk.

    ```bash
    sudo apt install python3-tk
    ```

3. Descargue el código (botón **Code → Download ZIP** de esta página) y descomprímalo.

4. Dentro de la carpeta, cree el entorno virtual e instale las dependencias de [`requirements.txt`](requirements.txt):

    - Linux y macOS:

        ```bash
        python3 -m venv .venv
        .venv/bin/pip install -r requirements.txt
        ```

    - Windows:

        ```bat
        py -m venv .venv
        .venv\Scripts\pip install -r requirements.txt
        ```

5. Arranque PyOECF desde esa misma carpeta:

    - Linux y macOS:

        ```bash
        .venv/bin/python src/main.py
        ```

    - Windows:

        ```bat
        .venv\Scripts\python src\main.py
        ```
