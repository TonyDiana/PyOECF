# Pendientes · PyOECF

Lo que queda por hacer y por decidir. El estado del código, el método, las decisiones tomadas y el historial están en `CLD_BITACORA.md`.


## 1. Lo siguiente

- **Código repetido, no urgente (Tony, 2026-10-22: de momento no; ver `CLD_BITACORA.md`, 4.5):** el `try/except` que escribe el libro (unas 12 líneas) está en `_escribir_informe` y al final de `MedirTiff`; los mensajes, su orden y la caja donde salen son distintos en cada uno. Unificarlo con `_escribir_libro(review)` (devuelve ruta, libro y error) ahorra unas 8 líneas y obliga a repetir las pruebas de Generar y de Analizar revelado. Hacerlo cuando haya que cambiar cómo se escribe el libro o cómo se tratan sus errores.


## 1b. A medias, esperando datos o pruebas

- **Píxeles muertos y calientes con las tapadas** (Tony, 2026-10-19): pieza nueva, por hacer cuando haya una serie con tapadas. El manual ya no lo promete (se quitó de `3) Captura`); si se hace, volver a decirlo allí.

- **Tomas tapadas** (por exposición, hecho 2026-10-19, ver CLD_BITACORA): ninguna serie tiene. Falta probar que se reconocen (f/11 y 1/160, solo tras una Z-V final válida), el negro y el ruido que salen de ellas, el aviso de tapada con luz y el aviso si no casan con el borde tapado. Hace falta una serie con Z-V final y dos tapadas (basta una corta).

## 2. Pequeños, señalados sin hacer

- Probar los códigos de balance de **Fujifilm** con tomas que no estén en Auto, y los de **Sony** además de Personalizado y Temperatura.

- **Umbrales de los avisos de rechazadas** (hechos 2026-10-16, provisionales): validarlos con más series cuando estén procesadas (`KTE.AVISO_*`; hoy medidos con la R7, 2,3 %, sin aviso, y la D750 de Carolina, 8,9 %, luz desigual a la izquierda).

## 5. De la guía de Claude web (2026-10-12)

Lo que la guía de diseño dejaba **[ABIERTO]**, **[PROPUESTA]** o **[NO VERIFICADO]** y el código todavía no resuelve. Lo ya resuelto está en `CLD_BITACORA.md` (apartado 6 y tabla 4.3).

### 5.1 Por decidir (Tony)

1. **Qué más sube a «Análisis»** (la tabla de resultados por canal está en `Cálculo`). Tony: «ya veremos». Incluye las tarjetas de resultados (cámara, ajustes, diferencia media, latitud **en zonas**, nunca en EV).

2. **Mapa de uniformidad de luz y viñeteo:** guardar el valor de cada tesela de la Z-V (posición y mediana por canal). ¿Entra en esta versión?

4. **Pieza I:** qué hacer con las fotos tapadas y el balance de blancos personalizado. Tony: «hay que hablarlo»; se busca un método y software, no hacer el análisis real con Claude. En parte resuelto el 2026-10-19 (cómo se reconocen y dónde se copian las tapadas y la toma `WB-CTRL`: ver CLD_BITACORA); queda el método.

### 5.3 Por comprobar

1. **Lightroom:** el parche de la ZV de la lámina debe leer **46,6 %** (119 de 255) en la lectura RGB del módulo Revelar. Si marca otra cosa, la escala 0-255 de la curva no es la de sRGB y hay que cambiar la conversión. **[NO VERIFICADO]**

2. **Límite de linealidad** en las demás cámaras (solo está medido en la R7).

3. **Tamaño de tesela:** validar los 48 px con una tarjeta con diana y más cámaras.
