# Procedimiento paso a paso


| Conjunto | Secuencia | n.º de foto | Requerido |
| :--- | :--- | :---: | :---: |
| Preparación | Formatear la tarjeta | | Recomendable
| | Colocar el [resultado fotométrico][resultado_fotometrico] logrado | | Sí
| | Enfocar la escena según las [instrucciones][encuadre_escena] presentadas | | Sí
| | Verificar que la luz es estable y no incide en la lente | | Sí
| | Fotografiar sólo la tarjeta gris en ZV con balance de blancos automático | 1 | Sí
| | Utilizar la fotografía para personalizar el balance de blancos | | No[^a]
| | Fotografiar toda la escena en ZV con balance de blancos personalizado | 2 | No[^a]
|
| Secuencia inicial de luz | Realizar 15 fotografías cambiando el tiempo de exposición hacia un lado del mecanismo de cambio de tiempo de exposición[^b][^g] | 3-17 | Sí[^c]
| | *Considerar*: Si los tiempos de exposición comenzaron a resultar en segundos, realizar una pequeña pausa entre tomas o reducir el ritmo de capturas, para no calentar el sensor y no obtener resultados erróneos en el análisis del ruido digital | | Sí
| | Fotografía ZV con balance de blancos personalizado (determina el cambio de dirección) | 18 | Sí
|
| Secuencia final de luz | Realizar 15 fotografías cambiando el tiempo de exposición hacia el otro lado del mecanismo de cambio de tiempo de exposición[^b][^g] | 19-33 | Sí[^c]
| | *Considerar*: Si los tiempos de exposición comenzaron a resultar en segundos, realizar una pequeña pausa entre tomas o reducir el ritmo de capturas, para no calentar el sensor y no obtener resultados erróneos en el análisis del ruido digital | | Sí
| | Fotografiar ZV con balance de blancos personalizado (determina el fin del proceso) | 34 | No[^f]
|
| Secuencia del ruido digital | Realizar 2 fotografías en f/11 Tv 1/160 y el mismo ISO que la serie, con balance de blancos personalizado, con la tapa puesta y, en cámaras con espejo, el visor tapado, justo después de la foto 34 | 35-36 | No[^d]
|
| Secuencia del balance de blancos | Realizar 1 fotografía por cada uno de los balances de blancos que disponga la cámara, siempre en ZV | -- | No[^e]



[^a]: En caso de no realizar este paso, el programa mostrará una incidencia, pero permitirá continuar. Sin embargo, es probable que las fotografías aparezcan amarillentas.

[^b]: La forma más sencilla es dar 15 clics en la rueda.

[^c]: Si se duda de haber realizado la captura correctamente, verificar en pantalla los datos de la última fotografía tomada y, en caso de duda, repetirla. El software siempre utilizará la última fotografía capturada de cada zona lumínica y descartará las anteriores. Lo mismo vale para cualquier otra fotografía de la secuencia que se repita: las ZV y los balances de blancos.

[^f]: Si no se captura esta fotografía, no se buscarán las fotografías con las tapas puestas. Además, el software solo la reconocerá como ZV final si las fotografías con la tapa puesta van justo después, sin ninguna otra entre medias, y si tiene el mismo balance de blancos que la serie.

[^d]: En caso de no realizarlas, el software no podrá informar correctamente de los valores de negro y ruido digital del sensor, ni reconocerá la ZV final (foto 34): mostrará incidencia pero permitirá realizar el resto del análisis. Si entra luz en alguna de ellas, el software lo avisará y no la utilizará.

[^e]: En caso de no realizarlas, el software no podrá informar correctamente de los valores de kelvin reales de la cámara: mostrará incidencia pero permitirá realizar el resto del análisis.

[^g]: Con la rueda en tercios de paso, lo habitual. También se puede realizar por pasos enteros: 5 fotografías hacia cada lado, y el análisis se hará sin los tercios. Nunca por medios pasos: el software no podrá analizar la serie.
