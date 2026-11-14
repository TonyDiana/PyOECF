# Instalación de PyOECF

<!-- cSpell:ignore Sabsik, Wacatac -->

> **Quién genera los ejecutables.** Los ejecutables **no los genera el autor en su equipo: los genera GitHub** de forma automática (GitHub Actions), a partir del código público de este repositorio, y los publica en la página de versiones. Por eso su contenido es el del código publicado, y puede comprobar que el archivo descargado es el original con el `SHA256SUMS.txt` de cada versión (paso 3 de la opción 1).


## Opción 1: ejecutable (recomendada)

No necesita instalar nada más.

1. Entre en la [última versión publicada](https://github.com/TonyDiana/PyOECF/releases) y descargue el archivo de su sistema: Windows, macOS o Linux.

2. La primera vez que lo abra, el sistema puede avisar de que el programa no está firmado:

    - **Windows**: el archivo es un único `.exe` portable: no hay que instalar ni descomprimir nada. Haga doble click en él desde donde lo haya guardado. Puede aparecer «Windows protegió su PC»: pulse **Más información** y después **Ejecutar de todas formas**. Si Microsoft Defender lo marca como amenaza o lo borra, vea el apartado «Si Windows borra o bloquea el programa».

    - **macOS**: solo para equipos con Apple Silicon (M1 o posterior). Si dice que no se puede abrir, vaya a **Ajustes del Sistema → Privacidad y seguridad** (en versiones anteriores, **Preferencias del Sistema → Seguridad y privacidad**) y pulse **Abrir igualmente**. Hace falta una cuenta de administrador.

    - **Linux**: descomprima el archivo y haga doble click en `PyOECF`.

3. Opcional, para comprobar que el archivo es el publicado: cada versión lleva un `SHA256SUMS.txt`. En PowerShell:

    ```powershell
    Get-FileHash .\PyOECF-X.Y-windows.exe -Algorithm SHA256
    ```

    (cambie `X.Y` por la versión) y compare el resultado con la línea de su archivo en `SHA256SUMS.txt`.


### Si Windows borra o bloquea el programa

PyOECF es de código abierto y no contiene ningún virus, pero **no está firmado digitalmente** y es un programa nuevo con pocas descargas. Microsoft Defender lo puntúa por aprendizaje automático y a veces lo marca por error (detecciones como `Trojan:Win32/Wacatac.C!ml` o `Trojan:Win32/Sabsik.TE.A!ml`; el `!ml` indica que es una suposición del sistema, no un virus conocido). Es un falso positivo habitual en programas hechos con PyInstaller. Puede ver el código en el [repositorio](https://github.com/TonyDiana/PyOECF). Al ser un único archivo portable, Defender puede marcarlo al ejecutarlo en unos equipos y no en otros; si le pasa, siga los pasos de abajo.

Si Defender lo ha puesto en cuarentena:

1. Abra **Seguridad de Windows → Protección contra virus y amenazas → Historial de protección**.
2. Busque la entrada de PyOECF y elija **Acciones → Restaurar**.
3. Para que no vuelva a borrarlo, añada el archivo `PyOECF.exe` (o la carpeta donde lo guarde) en **Protección contra virus y amenazas → Administrar la configuración → Exclusiones**.

Si prefiere no excluirla, compruebe antes el hash (paso 3 de arriba).


## Opción 2: desde el código fuente (Sólo mantenedores)

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
