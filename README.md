# Plantilla de biblioteca TD


## Información
```yaml
Versión:        Ver archivo VERSION
Autor:          Tony Diana
Licencia:       Atribución, No Comercial, Compartir Igual
Lenguajes:      Python
```

> Información sobre la licencia: [CC BY-NC-SA](https://creativecommons.org/licenses/by-nc-sa/4.0/)


## Descripción

Repositorio base para crear nuevas bibliotecas o aplicaciones TEP8. Contiene la estructura estándar, scripts de mantenimiento y documentación de referencia.

Deberá adaptarse a las necesidades de cada proyecto.

> Consultar `rec/estrategias/Estrategias.rst` para el flujo completo de desarrollo y despliegue.


## Estructura
```text
 Repo
    ├── __init__.py         ← MNS (Module Name Server).
    ├── main.???            ← Lanzador del proyecto.
    │
    ├───_doc                ← Documentación técnica.
    │   ├───guide           ← Guía desplegada en HTML.
    │   └───src             ← Fuentes del la guía. 
    │       ├───rec         ← Recursos para la documentación técnica.
    │       └───sources     ← Archivos .rst.
    │
    ├───guide               ← Documentación del usuario final (idéntica a _doc).
    │
    ├───rec                 ← Recursos para el mantenimiento del proyecto.
    │   ├── estrategias/    ← Notas y decisiones de diseño
    │   │   ├── sl/         ← Enlaces simbólicos del proyecto
    │   │   │
    │   │   ├── changelog.md        ← Historial de cambios
    │   │   ├── changelog.md        ← Historial de cambios
    │   │   ├── requirements.md     ← Comentarios humanos a los requerimientos
    │   │   ├── requirements.txt    ← Requerimientos para despliegue (Docker)
    │   │   │   
    │   │   └── TODO.rst            ← Hoja de ruta general
    │   │
    │   └───scripts
    │       ├── deploy.sh       ← Generador de la rama deploy
    │       ├── submodule.sh    ← Generador de la rama SubmoduleLite
    │       └── pycacher.sh     ← Limpieza de bytecode Python
    │
    └───src                 ← Código fuente.
        ├── __init__.py     ← MNS (Module Name Server).
        ├───bib             ← Bibliotecas propias.
        └───vendor          ← Librerías vendorizadas.
```


## Dependencias

- Python 3.12
