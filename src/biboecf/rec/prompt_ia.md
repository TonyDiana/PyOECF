# Revisión del libro PyOECF por una IA

Adjunto un libro Excel (`PyOECF.xlsx`) generado por **PyOECF**, un programa
que estudia la respuesta tonal de una cámara digital. Quiero que lo
**entiendas, lo compruebes y lo interpretes**. Busca también lo que pueda
estar **mal analizado**: datos dudosos, cálculos que no cuadran o
conclusiones que los datos no sostienen. Prefiero que me señales un error
de más a que lo pases por alto.

**Pero lee antes los apartados 3, 4 y 5.** Otras IA ya revisaron este
libro y se equivocaron en cosas que el libro tiene bien. Si afirmas que
algo está mal, demuéstralo con la celda y con tu cálculo.

---

## 1. Qué es el estudio

- Se fotografía una **tarjeta gris del 18 %** con luz constante, en una
  serie de exposiciones a pasos de **1/3 de zona** alrededor de la
  exposición de referencia, la **Z‑V** (zona V, la del gris medio).
- La serie va de **Z0 a ZX**: **31 posiciones** (11 zonas enteras por 3
  tercios, hasta ZX). Una zona es el doble de luz y se divide en 3
  tercios. **Todo se mide en zonas, no en EV.**
- **Primera fase:** se mide el **RAW** de cada toma, por canal (rojo,
  verde, azul): nivel sobre el negro y dispersión. Con eso se calculan la
  linealidad del sensor, el techo (recorte), la **curva de transferencia
  del ruido** (lectura, fotones y una parte proporcional a la señal), los
  suelos, la relación señal/ruido (por píxel y normalizada a 8 Mpx) y la
  latitud.
- **Segunda fase:** se miden las **TIFF exportadas por el revelador**
  (por ejemplo Lightroom) de esas mismas tomas, para ver qué curva tonal
  aplica, en **L\*** (CIELAB). Se compara con lo esperado: la Z‑V en
  L\* 50 y **un paso de luz por zona**, recortado al blanco de pantalla.
  La escala de 10 L\* por zona es solo una **referencia** («Objetivo»),
  no el esperado.
- Las medidas se hacen en **teselas** de la tarjeta elegidas en la Z‑V,
  que valen para toda la serie. Los filtros descartan las teselas malas
  por nivel, dispersión o asimetría. El **paño** es un paño **gris con
  textura** (la cartulina de base es negra), opcional en la escena; el
  programa lo excluye de las teselas por su posición y por un margen. Si
  no lo hay, no hay lámina PSD, pero sí libro.

## 2. Mapa del libro

Los colores del texto significan: **azul** = dato leído de los RAW;
**naranja oscuro** = literal escrito por diseño; **negro** = fórmula;
**gris** = rótulo o nota.

| Hoja | Qué contiene |
|---|---|
| **Análisis** | Cámara, fecha, profundidad RAW, exposición de la Z‑V; **latitud de texturas** (apreciable y recomendada: sombras, altas luces y latitud, en tercios); ruido de lectura y negro; balances de blancos (Kelvin anotado frente a medido); sugerencia de revelado (puntos de la curva de Lightroom, 0–255); tabla por zona con el **L\* leído** (lo escribe el usuario o el programa), la diferencia del sensor y la del revelador. Lo estimado, en otro color. |
| **Gráficos** | 1 curva tonal en L\*; 2 diferencia en L\*; 3 esperado y obtenido; 4 y 5 desviación (tramo lineal y rango completo); 6 señal/ruido normalizada a 8 Mpx, en escala logarítmica, con el modelo del verde y los umbrales 1, 10 y 40. Leen de Cálculo. Identifícalas por su título, no por su número: el orden puede cambiar. |
| **Datos** | Lo leído de los RAW, sin cálculos salvo la media de las Z‑V y los tercios estimados: serie por zonas (archivo, nivel y dispersión por canal), Z‑V de control y su media, ruido de lectura y su origen, negro y su origen, la **curva de transferencia** (lectura, ganancia, proporcional; aleatorio y fijo de la Z‑V; megapíxeles del sensor), balances de blancos, **paño por zona** (dispersión y fracción recortada de la ventana del paño, por canal) y L\* del revelador por zona: el L\* leído de Análisis y, en un tercio sin él, el estimado. |
| **Constantes** | Cada constante del método con nombre, valor, unidad y qué es, por orden alfabético. Las fórmulas usan esos nombres. Incluye la nota sobre `SNRMinima` y `SNRExcelente` (ISO 12232) y `MpxReferencia`. |
| **Cálculo** | Bloque 1, por canal: techo, suelo (`RelacionSR`), rango, último punto lineal, primer punto recortado, suelo sugerido (`SNRMinima`), suelo excelente (`SNRExcelente`) y latitud sugerida. Bloque 2, por tercio: esperado, obtenido, desviación, recortado y señal/ruido por canal (por píxel y a 8 Mpx), y el modelo del verde. Bloque 3, curva tonal por zona: luz y L\* esperados, del sensor y del revelador, sus diferencias, y entrada y salida de la curva. Bloque 4, **latitud de texturas** (verde): arriba los límites; debajo, por zona, textura del paño, textura/ruido, textura conservada, paño recortado y si cumple cada criterio. |
| **Rechazadas** | Teselas de tarjeta que los filtros dejaron fuera: recuento, porcentaje, motivo y desviación. Solo cuentan teselas de tarjeta: no el paño, su margen ni las oscuras. |

Si una celda está **en blanco**, falta el dato (zona sin toma, toma sin
medir o segunda fase sin hacer). No es un cero.

**Cuidado con las posiciones.** Tu copia puede tener más hojas o más
columnas que otras versiones del libro. **Identifica cada columna por su
rótulo y cada fila por su zona** («ZV», «Z3 1/3»…), nunca por la letra
de la columna ni por el número de fila que te suene de otro sitio. Antes
de recalcular, escribe qué columna es cuál.

## 3. Definiciones para recalcular

Los valores definitivos están en la hoja **Constantes**; si algo difiere
de lo que sigue, **manda la hoja**. Valores por defecto: `ZonaZV` = 5,
`TercioPorZona` = 3, `FactorZona` = 2, `LZV` = 50, `LPorZona` = 10,
`RelacionSR` = 1, `SNRMinima` = 10, `SNRExcelente` = 40,
`MpxReferencia` = 8, `ToleranciaLineal` = 0,1,
`UmbralRecorte` = 0,995, `EscalaCurva` = 255, `RoseTextura` = 5,
`TexturaConservada` = 0,5, `PanoRecortadoMax` = 0,1, `MargenSombras` = 1,
`AnchoZona` = 1. CIELAB: 116, 16, 0,008856 y
903,3. sRGB: 0,0031308, 12,92, 1,055, 2,4 y 0,055.

### Primera fase (RAW, por canal)

| Magnitud | Definición |
|---|---|
| Esperado (zona) | `ZonaZV + tercios / TercioPorZona` |
| Obtenido (zona equivalente) | `ZonaZV + log_FactorZona(nivel / Z‑V media)` |
| Desviación | obtenido − esperado, en zonas |
| Recortado | `nivel ≥ UmbralRecorte × máximo del canal` |
| **Techo** | `ZonaZV + log(máximo del canal / Z‑V media)`. **El máximo de un canal recortado es la saturación del sensor: es el techo.** |
| Curva de transferencia (Datos) | `ruido² = lectura² + señal / ganancia + (proporcional × señal)²`, en niveles, ajustada por mínimos cuadrados (peso relativo) con las zonas **sin ningún píxel recortado**. Ruido de cada zona = dispersión × nivel |
| Aleatorio y fijo de la Z‑V (Datos) | Aleatorio: la Z‑V menos una Z‑V de control de la misma exposición, igualadas en nivel, dentro de cada tesela (lo fijo se va). Fijo: `√(dispersión media de las Z‑V² − aleatorio²)` |
| Escala a 8 Mpx | `√(megapíxeles del sensor / MpxReferencia)`: al juntar píxeles, el ruido se promedia |
| Suelo, suelo sugerido, suelo excelente | Zona donde la señal/ruido **normalizada** llega a `RelacionSR`, `SNRMinima` y `SNRExcelente`, según la curva: con `T` = umbral / escala (la de un píxel), la raíz positiva de `(1 − T²·p²)·S² − (T²/g)·S − T²·l² = 0`, y `ZonaZV + log(S / Z‑V media)`. **Extrapolado por el modelo**: puede caer por debajo de Z0. «No alcanzado» si la parte proporcional lo impide |
| Rango | techo − suelo |
| Último punto lineal | mayor zona con `|desviación| ≤ ToleranciaLineal` y sin recorte |
| Primer punto recortado | primera zona marcada como recortada, o «no alcanzado» |
| Señal/ruido | `1 / dispersión relativa` de la tesela (la de **un píxel**); «saturado» si la dispersión es 0 |
| Señal/ruido (8 Mpx) | señal/ruido × escala a 8 Mpx. **Esta sí se compara entre cámaras** |
| Modelo verde (8 Mpx) | la señal/ruido de la curva en la señal esperada de la zona (Z‑V media × `FactorZona^(tercios / TercioPorZona)`), normalizada; hasta el máximo del canal |
| Latitud sugerida | último punto lineal − suelo sugerido + `AnchoZona`, en **zonas**: cuenta las zonas que caben, con las dos puntas (de Z3 a Z8, 6 zonas) |

### Latitud de texturas (paño, canal verde)

Se mide en el **paño**, no en la tarjeta. Un tercio **sin dato** (toma
sin medir) no corta la cadena: deja pasar lo que viene del lado de la
ZV, y ningún límite cae en él.

| Magnitud | Definición |
|---|---|
| Textura del paño | `√(dispersión del paño² − dispersión de la tarjeta²)`, las dos relativas y por píxel |
| Textura/ruido | textura del paño / dispersión de la tarjeta |
| Textura conservada | textura del paño / textura del paño en la ZV |
| Sombras apreciables | La primera zona desde la que textura/ruido ≥ `RoseTextura` **sin volver a bajar hasta la ZV**; entre ese tercio y el de debajo, interpolada en recta y llevada al tercio más próximo |
| Sombras recomendadas | apreciables + `MargenSombras` / `TercioPorZona` |
| Luces apreciables | La última zona, subiendo **sin cortes** desde la ZV, con textura conservada ≥ `TexturaConservada` |
| Luces recomendadas | La última, subiendo sin cortes desde la ZV, con paño recortado ≤ `PanoRecortadoMax`; nunca por encima de las apreciables |
| Latitud de texturas | luces − sombras + `AnchoZona`, en **zonas** (apreciable y recomendada), contando las dos puntas |

### Segunda fase y curva tonal (L\*, por zona y tercio)

Dos curvas se comparan con el **mismo esperado**: la del **sensor** (el
RAW sin curva, canal verde) y la del **revelador** (las exportaciones).
Las columnas del revelador salen **en blanco** mientras no haya L\*
leído. **Se identifican por su rótulo.**

| Rótulo del libro | Definición |
|---|---|
| Luz esperada | `MIN(1, LuzZV × FactorZona^(tercios / TercioPorZona))`, con `LuzZV` la luz de L\* = `LZV` |
| Esperado (L\*) | CIELAB de la luz esperada. **Un paso de luz por zona, recortado a 100** (el blanco se alcanza en la zona 7,44) |
| Objetivo (L\*) | `LPorZona × zona`. Solo referencia |
| Luz del sensor | `MIN(1, LuzZV × nivel verde / Z‑V media verde)`; en blanco si el nivel no es mayor que 0 |
| Sensor (L\*) | CIELAB de la luz del sensor |
| Dif. sensor | Sensor (L\*) − Esperado (L\*) |
| Revelador (L\*) | De la hoja Datos («L\* del revelador, por zona»): el **L\* leído** de Análisis, que mide el programa en las exportaciones (las 31) o escribe el usuario a mano (normalmente solo las 11 zonas enteras). Un **tercio sin L\* leído se estima**: la diferencia con el esperado de las dos zonas enteras vecinas, repartida en recta y sumada al esperado del tercio, sin salirse de los L\* de esas dos zonas (`MEDIAN`; cerca del blanco el esperado se recorta a 100); si falta una de las dos, en blanco |
| Luz del revelador | Inversa de CIELAB de Revelador (L\*) |
| Dif. revelador | Revelador (L\*) − Esperado (L\*) |
| Falta / Sobra | `MAX(0, Esperado − Revelador)` y `MAX(0, Revelador − Esperado)` |
| Entrada (0‑255) | `ROUND(EscalaCurva × sRGB(luz del revelador))` |
| Salida (0‑255) | `ROUND(EscalaCurva × sRGB(luz esperada))` |
| Punto de la curva | ● en las zonas enteras |

**Comprobaciones universales en la fila de la ZV:** la **salida** vale
119 con `LZV` = 50 y la curva sRGB (solo depende del esperado); la
**diferencia del sensor** es ≈ 0; y la **entrada** vale 119 solo si el
revelador deja la ZV en L\* 50.

## 4. Lo que es intencionado: no lo marques como error

Puedes discutirlo como **criterio del método** (categoría 3), con tu
razón, pero no es un fallo de cálculo.

1. Los **suelos** están extrapolados por la curva de transferencia, no
   medidos: la serie no siempre baja hasta ellos, y pueden caer por
   debajo de Z0.
2. El **esperado se recorta a 100**: por encima del blanco de pantalla no
   hay valores.
3. La relación señal/ruido sale de la dispersión **dentro de la tesela**,
   así que incluye lo fijo (textura de la tarjeta, diferencias entre
   píxeles). Cuánto pesa lo fijo se mide en la Z‑V (Datos: aleatorio y
   fijo). La de **un píxel** depende del tamaño del píxel: para comparar
   cámaras, usa la normalizada a 8 Mpx.
4. `SNRMinima` = 10 y `SNRExcelente` = 40 son **sugerencias** (ISO 12232:
   10:1 «aceptable», 40:1 «excelente»), sobre la señal/ruido normalizada a
   8 Mpx. Son el criterio del método: nadie los cambia en el libro (para
   estudiar otro, se usa una copia).
5. La **latitud es asimétrica a propósito**: por linealidad arriba y por
   señal/ruido abajo.
6. Una **dispersión de 0** en las zonas altas significa canal saturado.
   La señal/ruido dice «saturado» ahí, y la curva de transferencia no usa
   esas zonas.
7. El **sensor sale casi a 0 en los medios**: esperado y sensor comparten
   el patrón de luz. Es el resultado, no un fallo. Se separan en las
   sombras (ruido) y en las altas luces (recorte). Lo que mide la
   respuesta tonal es la **diferencia del revelador**.
8. **Sin L\* leído**, su diferencia, la entrada y la salida salen en
   blanco (en Cálculo, `#N/A`, para que las gráficas no lo dibujen a 0).
   No es un cero ni un error.
9. Solo las **zonas enteras** son puntos de la curva (11; Lightroom admite
   16 como máximo). Los tercios son informativos.
10. **Entrada y salida de 0 a 255** usan la curva de sRGB. Que esa sea la
    escala del editor de curvas de Lightroom es un **supuesto aún sin
    comprobar**: se verifica con la lectura del parche de la ZV (46,6 %).
11. La **escala es en zonas**: el proyecto no usa EV.
12. La **latitud de texturas** (Análisis, Cálculo bloque 4) **no es** la
    latitud sugerida (Cálculo bloque 1). La sugerida sale de la
    señal/ruido de la tarjeta; la de texturas, de **dónde se aprecia la
    textura del paño**, y por eso es más estrecha. Las dos son correctas:
    miden cosas distintas.
13. `RoseTextura` = 5 viene del **criterio de Rose** (Rose 1948; Burgess
    1999), pero se aplica **por píxel** a la textura del paño frente al
    ruido de la tarjeta: no es el criterio de Rose tal cual (que integra
    el área del objeto). El valor está **validado con la vista** del
    autor en una Canon R7: el límite de sombras cae donde él deja de ver
    textura.
14. Las **sombras recomendadas** están un tercio por encima de las
    apreciables a propósito: un umbral de Rose más alto no es estable
    (pasar de 5 a 6 mueve el límite hasta 2 zonas en algunas cámaras).
15. La latitud de texturas **depende del paño**: con otro paño (más o
    menos textura) el límite de sombras cambia.

## 5. Errores de revisores anteriores: no los repitas

Estas afirmaciones se hicieron sobre **versiones anteriores** de este
libro (con otras columnas y menos hojas) y son **falsas**. Las que
dependen de la letra de una columna no se pueden comprobar sin leer su
rótulo. Si crees que alguna es cierta en tu copia, cita la celda que lo
muestra.

### Sobre las columnas, las filas y el esperado

| # | Se afirmó | Por qué es falso |
|---|---|---|
| 1 | La entrada de la curva se calcula con una columna que es una diferencia, «error conceptual grave». | Falso. La entrada es `sRGB(luz del revelador)` y la salida `sRGB(luz esperada)`. **Ninguna usa una diferencia.** Se leyó mal una columna: **lee los rótulos, no las letras.** |
| 2 | El L\* esperado sale de la escala de 10 L\* por zona. | Falso. El esperado es la ZV en L\* 50 con **un paso de luz por zona**. Los 10 L\* por zona son el «Objetivo», una línea de referencia. |
| 3 | «Hay 16 zonas enteras (Z0 a ZX)», luego en Análisis sobran 15 filas. | Falso. De Z0 a ZX hay **11** zonas enteras. 16 es el **máximo de puntos** de la curva de Lightroom. |
| 4 | El techo debería calcularse sobre el último valor sin recortar, no sobre el máximo. | Error de concepto. El máximo de un canal recortado **es** el techo (la saturación). El último valor sin recortar daría un techo por debajo del real. El caso que sí merece aviso es otro: si la serie **no llega al recorte**, el máximo no es el techo, y la hoja lo indica con «no alcanzado» en el primer punto recortado. |
| 5 | La fila de la ZV es la 61. | Era otra fila (una de las de Z3 1/3). **Identifica la ZV por su rótulo.** |
| 6 | Los ceros de dispersión en zonas altas «distorsionan» el suelo sugerido. | No. Los suelos salen de la curva de transferencia, que solo usa zonas **sin ningún píxel recortado**: las filas altas no intervienen. |

### Sobre las normas, el número de filas y las unidades

| # | Se afirmó | Por qué es falso |
|---|---|---|
| 7 | El libro calcula la OECF «según la norma ISO 14524 / ISO 12232». | A medias. La OECF es de la **ISO 14524**. La **ISO 12232** (sensibilidad) solo se cita para el criterio de señal/ruido. La norma de L\* es **ISO/CIE 11664‑4:2019**. |
| 8 | «85 filas de muestras desde Z0 a ZX». | Son **31 posiciones**. |
| 9 | El suelo sugerido usa una señal/ruido «de valor 2 en rojo y azul y 1,33 en verde». | Esos números son **zonas** donde cae el suelo sugerido. El umbral de señal/ruido es `SNRMinima`. |
| 10 | «Latitud útil de ~7,3 EV». | Se habla en **zonas**, no en EV. Y una latitud cuenta las zonas que caben, con las dos puntas (`AnchoZona`): no es la simple resta de los límites. |

### Lo que sí acertaron (tómalo en serio)

1. La latitud mezcla dos criterios (linealidad arriba, señal/ruido abajo):
   conviene que **esté escrito** en una nota.
2. Cuando la dispersión vale 0, conviene separar «**canal recortado**» de
   «**sin dato**» con una marca explícita.
3. Falta una **celda de comprobación** de que la salida de la ZV da 119.
4. Hay que decir **qué suelo usa la latitud** (el de señal/ruido, no el de
   ruido de lectura).

### Preferencias de diseño, no errores

Fondo de color para «campos editables» (el alumno no toca el libro) y
fuentes como Aptos o Segoe UI (no existen en LibreOffice ni en Linux). Si
las propones, dilo como **preferencia**.

## 6. Qué te pido

Trabaja en este orden y **cita siempre la hoja y la celda** (o la fila y
la columna) de lo que digas.

### 6.1 Comprobar los datos de entrada

- ¿Faltan zonas? ¿Hay zonas con nivel 0, vacías o con dispersión enorme?
- ¿Crece el nivel de forma ordenada, más o menos el doble por zona,
  dentro del tramo lineal? Señala saltos, retrocesos o tomas que parezcan
  de otra serie (otro encuadre, otra luz, otro ISO).
- Z‑V de control: ¿se apartan de la media? Eso indicaría que la luz
  cambió durante la serie.
- Ruido y negro: ¿de dónde sale el ruido (borde tapado, tomas tapadas o
  curva de transferencia) y el negro (tapadas, estimado en las sombras o
  declarado)? ¿Casan entre sí? ¿Es razonable el negro para la cámara?
- Curva de transferencia: ¿son razonables la lectura, la ganancia y la
  parte proporcional? ¿Sigue el modelo del verde a la señal/ruido medida
  (gráfica de la relación señal/ruido)? ¿Cuánto pesa lo fijo en la Z‑V?
- Rechazadas: ¿el porcentaje es bajo? Si es alto, ¿qué motivo domina y
  qué puede significar (luz desigual, reflejos, tarjeta sucia)?
- Profundidad RAW: ¿cuadra con el máximo nivel de los datos y con el
  techo?

### 6.2 Comprobar los cálculos

- Recalcula por tu cuenta, con los valores de **Datos** y **Constantes**
  y las definiciones del apartado 3, al menos: la desviación de 3 tercios
  del tramo lineal, el L\* del sensor de 3 zonas (incluida la Z‑V) y un
  punto de entrada y salida de la curva. Compara con **Cálculo** y dime
  si coincide.
- Haz la **comprobación universal** de la ZV (apartado 3).
- ¿Son coherentes entre sí el techo, el primer punto recortado y el
  máximo? ¿Y los suelos, la curva de transferencia y la señal/ruido?
  Recalcula al menos un suelo con la fórmula del apartado 3.
- ¿Cuadran las gráficas con las tablas de las que leen?

### 6.3 Interpretar

- ¿Cuánto rango dinámico útil tiene la cámara (por encima y por debajo
  de la Z‑V), con el criterio de `SNRMinima` y con otros criterios
  razonables? **En zonas.**
- ¿Dónde se aparta el revelador de lo esperado (sombras, medios, altas
  luces) y cuánto, en L\*?
- ¿Es razonable la sugerencia de curva de Análisis? ¿La cambiarías?
- Balances de blancos: ¿se parecen el Kelvin anotado y el medido?

### 6.4 Posibles errores del análisis

Clasifica cada problema que encuentres en una de estas categorías:

1. **De los datos:** la serie se tomó mal (tomas mezcladas, ISO
   distinto, luz que cambia, falta de tomas tapadas…).
2. **Del cálculo:** una fórmula o un resultado del libro no cuadra con
   sus propios datos. **Aquí debes dar la celda y tu cálculo.**
3. **Del método:** una suposición del método que no te parece correcta
   o que no vale para esta cámara (por ejemplo, el negro, el umbral de
   recorte o la tolerancia lineal). Revisa antes el apartado 4.
4. **De interpretación:** una conclusión del libro que los datos no
   sostienen.
5. **Preferencia de diseño:** una mejora de presentación o de uso que no
   corrige ningún resultado.

## 7. Cómo quiero la respuesta

1. **Resumen en 5 líneas:** ¿es fiable este estudio? ¿Qué es lo más
   importante que dice de la cámara y del revelador?
2. **Tabla de problemas:** categoría, dónde (hoja y celda), qué pasa,
   gravedad (alta, media, baja) y qué harías.
3. **Comprobaciones hechas:** qué recalculaste y si coincidió.
4. **Interpretación** (apartado 6.3).
5. **Dudas:** lo que no hayas podido entender del libro. Dímelo en vez
   de suponer.

No inventes valores: si un dato no está, dilo. Distingue siempre lo que
**mides en el libro** de lo que **supones**. Antes de decir que algo está
mal, vuelve a leer el rótulo de la columna y la zona de la fila.
