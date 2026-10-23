# Normas para Claude en PyOECF

<!-- cSpell:ignore biboecf, gris18, Morales, KCOM, margenTV, esCarpeta, esNOSQL, pyoecf, openpyxl -->

@~/Dev/Python/Bibliotecas/Repo/.claude/BASE.md

Las rutas son relativas a la raíz del repo, `~/Dev/Python/Aplicaciones/PyOECF`. En Claude web no hay acceso al disco: Tony pegará los archivos que hagan falta (pídeselos por su ruta).

Lo pendiente está en `rec/estrategias/bitacora/CLD_TODO.md`; el estado del código, el método, las decisiones y el historial, en `rec/estrategias/bitacora/CLD_BITACORA.md`. Si algo de estos archivos contradice el código o un archivo más reciente, **pregunta** antes de decidir.


## Cómo trabajar con Tony

- Las normas generales (español, dislexia y TDA, «cd», «espera», cambiar solo lo pedido, esperar el sí, literales repetidos…) están en `~/.claude/CLAUDE.md`. Claude web no lo lee: allí, Tony las pegará.
- Claude web ayuda con lo «filosófico» (criterios, diseño); el código es cosa del agente de VS Code.


## Normas de código (además de la Estrategia)

- Estándar de programación: `rec/estrategias/Estrategia_slr.md`. Arquitectura y pieza 1: `rec/contexto.md` (lo que ya no vale de él, en el apartado 1 de `CLD_BITACORA.md`).
- **Orden alfabético en todo** (listas, tuplas de constantes, `__slots__`, nombres de un `import`, comentarios que enumeran), sin distinguir mayúsculas. Excepción, `__all__`: en un módulo, en orden de aparición; en los `__init__` que lo ofrecen, alfabético.
- **Nombres:**
    - Propiedades y atributos públicos en camelCase, empezando en minúscula; las siglas en mayúsculas (`margenTV`). Las booleanas empiezan por `es` (`esCarpeta`).
    - Métodos públicos: empiezan en mayúscula, con un verbo en infinitivo.
    - Lo privado lleva `__` y no sigue esas normas (`__buscar_raw`).
- **Clases:**
    - `class Nombre(object):` y `__slots__` lo primero.
    - Lo que ofrece el objeto va como `@property` de solo lectura sobre una variable privada `__nombre`. Dentro de la clase se **lee la property** (`self.path`), nunca la variable; la variable solo se asigna y se devuelve en su property.
    - Bloques `# region Propiedades públicas` / `# endregion …` y `# region Métodos privados` / `# endregion …`. Una línea `#` sola antes de cada método. Las properties llevan docstring («Saber la marca… (None si no se leyó).»).
- **Constantes:**
    - Clases `std.EnumMutable`, no `enum.Enum` (es más lento y funde valores iguales). Sin `INMUTABLE`.
    - Se exportan con su nombre real (`COM`) y quien las usa las importa con un alias que empieza por K, en mayúsculas: `from .constantes import COM as KCOM`.
    - En biboecf, las compartidas van en `src/bib/biboecf/src/constantes.py`; las que solo usa un módulo, en el suyo.
- **Exposición:** el orden es siempre **f, Tv e ISO**. Se usa la tupla con nombres `Exp` de `biboecf` (`exp.f`, `exp.tv`, `exp.iso`).
- Líneas de 79 caracteres como máximo.

### Resumen de la Estrategia (manda el original; donde choque con lo de arriba, manda lo de arriba)

- Identificadores en español, minúsculas con guion bajo, **sin tildes ni `ñ`** (inglés para los típicos: `next`, `aux`, `temp`…). Comentarios en español. **Comillas dobles siempre.** Los docstrings no terminan en punto.
- **Anotaciones de tipo obligatorias** en toda función, método y propiedad. `# type: ignore` solo cuando el análisis estático no pueda inferir.
- Cabecera de módulo con `:Propósito:`, `:Autor:` y `:Versión:`, `# cSpell:ignore`, `__all__`, y secciones de import comentadas: estándar, externas, hub, paquete propio.
- **Imports relativos** dentro del paquete; desnudos hacia paquetes hermanos; los imports desde fuera van al `__init__`. Las bibliotecas independientes no asumen ningún `sys.path` externo.
- **Sin literales mágicos:** constantes con nombre al principio del módulo.
- Funciones si no hay persistencia; clases si hay varias interrelacionadas. `if True:` como colapso por sección.
- Los `Thread` no usan lambdas: `th_nombre` (módulo) o `ith_nombre` (interna).
- **Mejor legible que compacto, mejor explícito que implícito**; todo pasa el corrector ortográfico.
- Estructura de repo: `src/` con `main.py`, `hub`, `bib` y paquetes; recursos no Python sin `__init__.py`; versión en el fichero `VERSION`.


## Trampas conocidas

1. **`openpyxl` + gráficas = se pierden.** Nunca guardes con él un libro que las tenga.
2. `XlsxWriter`: las barras de error personalizadas necesitan **fórmulas en texto** (`"='Cálculo'!$L$51:$L$81"`), no listas.
3. `set_default_row(hide_unused_rows=True)` oculta las filas sin celdas escritas: cada fila visible necesita al menos una celda.
4. Los nombres definidos del libro no pueden parecer referencias de celda (por eso `ZonaZV` y no `ZV`).
5. `rawpy` describe los RAF de Fujifilm como `RGBG` aunque solo haya tres canales.
6. El tiempo de exposición de `rawpy` es `float32`: nunca se compara por igualdad.
7. El ISO base de la X70 es 200 (no graba RAW a 100) y el del X-T3, 160.
8. Los tiempos nominales de la cámara están redondeados (hasta 0,20 tercios en la R7).
9. El Lab de Photoshop acepta solo enteros por teclado.
10. La curva de Lightroom se aplica después de los controles básicos.


## Datos

- Versión actual: **0.5** (alfa; las 0.x son pre-release a propósito).
- **Series reales para probar:** en la torre, `~/Documentos/gris18/`; en el portátil, `~/pCloudDrive/Temporales/gris18/` (29 series: CR2, CR3, NEF y ARW; ningún RAF). Leer de pCloud funciona, pero al preparar PyOECF graba en cada carpeta una subcarpeta `OECF` con las copias y `estudio.json`: en pCloud, preguntar antes.
