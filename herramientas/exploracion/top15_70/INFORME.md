# Top-15 al 70 %: 10 planes probados, el techo y cómo seguir atacando

Fecha: 2026-10-01. Carpeta: `herramientas/exploracion/top15_70/`. Todo se pre-registró antes de medir
(`PREREGISTRO*.md`, con sus huellas en `registro.jsonl` y en git). No se tocó producción, ni el historial,
ni Railway, ni el tramo de prueba (≥ 9357).

## La respuesta corta

1. **Acertar el Top-15 en el 70 % de los sorteos, sorteo por sorteo, no es posible con la información que
   existe.** Para eso harían falta al menos **275 mbits** de información por sorteo. El mejor modelo que se pudo
   armar llega a **177 mbits** en el mejor año de datos (2025) y el ensamble en uso, a ~96 en 2026.
   Ningún modelo, en ningún sorteo de los 7.357 del desarrollo, le dio jamás un 70 % a su propio Top-15
   (el máximo fue 68 %).
2. **Lo que sí se consiguió:** el Top-15 sube de **55,0 % a 57,7 %** (+2,7 puntos) en el tramo de medida
   (dev-B, 2025). Se logra juntando tres cosas: ag12 reajustado limpio, la regla de RD y una **señal nueva**,
   que es que el operador esquiva el número de la fecha y el de la hora. En 2026, donde el ensamble da ~49-50 %,
   eso equivale a ~52 %.
3. **El 70 % sí se alcanza cambiando la forma de jugar, no el pronóstico:**
   - **Top-22 escalonado** (3-3-3-2-2 y 1 ficha a los puestos 6-22, 30 fichas): en dev-B **no pierde en el
     74,4 %** de los sorteos (gana en el 21,6 % y recupera lo apostado en el 52,9 %), con un retorno de
     +9,5 % por ficha [+6,2; +12,7]. Es un nivel optimista (ver §6) y en 2026 será menor.
   - **Top-15 en dos sorteos seguidos**: sale en al menos uno de los dos el **79,8 %** de las veces (al azar,
     63,4 %). No es mejor pronóstico: es el mismo Top-15 contado de otra manera, y cuesta el doble.
4. **Hallazgo nuevo y real:** el animal cuyo número es **el día del mes** sale **la mitad** de lo esperado
   (O/E 0,51 en dev-B, pre-registrado). También se esquivan el de **mañana** (0,66) y el de **la hora** en reloj
   de 12 h (0,78). RD Internacional también esquiva el día (0,78), y lo mismo hacen La Granjita (0,47),
   Selva Plus (0,68) y Guácharo (0,32). Es la primera fuente de información nueva desde el hilo 7, y apunta
   a que los operadores esquivan lo que más juega la gente.
5. **Error corregido:** el análisis de "las 8:00" del 01-10 medía en realidad las 16:00 (`hora == 8`). El Top-15
   real de las 8:00 es **60,5 %** (no 53,1 %). Es la mejor hora del día, pero tampoco llega al 70 %.

## 1. Por qué el 70 % por sorteo está fuera de alcance

El Top-15 acierta lo que suman las probabilidades de sus 15 animales. Para que esa suma llegue al 70 %, cada
uno de los 15 tendría que tener ~4,7 % (el azar da 2,6 %). Hoy el #1 del motor acierta ~5 % y el #15 ~3 %.

| Top-15 deseado | Información mínima por sorteo |
|---|---|
| 50 % | 33 mbits |
| 55 % | 71 mbits |
| 60 % | 123 mbits |
| 65 % | 191 mbits |
| **70 %** | **275 mbits** |

| Modelo (dev-B, 3.669 sorteos) | mbits | Top-15 |
|---|---|---|
| Azar | 0 | 39,5 % |
| Ensamble (producción) | 145,6 | 55,0 % |
| Ensamble + regla RD (B1) | — | 55,6 % |
| P6: ag12 reajustado + RD | 171,0 | 56,9 % |
| P6 + exposición (fecha y hora) + regla RD | 177,1 | **57,7 %** |

**La información que hay sirve para descartar, no para concentrar.** Los puestos 30-38 aciertan ~1 % cada uno
(el operador casi no repite lo que acaba de salir), pero los puestos 1-15 aciertan entre 3 y 5 %. Por eso
177 mbits solo dan 57,7 %: la mayor parte de la información dice quién NO sale. Hasta el modelo más afinado
le da a su Top-15 un 55,6 % de media y un 67,7 % como máximo. Elegir "los sorteos buenos" tampoco lleva al
70 %, porque no existen (el hilo 6 ya lo probó a ciegas y falló).

Además, 2025 fue el mejor año: el ensamble tuvo 145 mbits en dev-B, ~95 en dev-A (2024) y ~96 en abr-sep 2026.
El operador "evita repetir" con distinta fuerza según la época, y en 2026 lo hace menos.

## 2. Los 10 planes (ronda 1, pre-registrada; dev-A elige, dev-B mide una vez)

Comparador: B1 = ensamble + regla RD en el Top-15. Criterio de MEJORA: diferencia > 0 con p < 0,005
(Bonferroni por 10). OBJETIVO: Top-15 ≥ 70 %.

| # | Plan | Top-15 dev-B | Diferencia con B1 [IC95] | Veredicto |
|---|---|---|---|---|
| 1 | Sacar del Top-15 lo que ya salió hoy en LA | 55,57 % | +0,03 [−0,30; +0,38] | NO PASA: el ensamble ya lo hace |
| 2 | Sacar todo lo que salió hoy en RD (desfases 1, 2, 3, 8 y 11) | 55,00 % | −0,55 [−1,25; +0,16] | NO PASA: solo sirve el (h−1) |
| 3 | Chorro LA+RD con "rechazo" (24 desfases) | 55,14 % | −0,41 [−1,36; +0,57] | NO PASA (+1,9 mbits) |
| 4 | Árboles (LightGBM) sobre el ensamble, 73 variables | 56,12 % | +0,57 [−0,84; +1,94] | NO PASA en Top-15; +24 mbits |
| 5 | Árboles que ordenan para el Top-15 (LambdaRank) | 54,16 % | −1,39 [−2,84; −0,03] | NO PASA: empeora |
| 6 | **ag12 reajustado SOLO con dev-A + RD (h−1, h−2)** | **56,88 %** | **+1,34 [−0,03; +2,64]**, p = 0,03 | NO PASA por Bonferroni; el mejor; +25,5 mbits [+18; +33] |
| 7 | Jugar solo las horas buenas (dev-A eligió las 17:00) | 55,08 % | −0,51 frente al resto | NO PASA. Las 8:00 dan 61,1 % [55,6; 66,7] (réplica débil) |
| 8 | Top-15 en dos sorteos seguidos | 79,8 % (al menos uno) | — | Llega al 70 % como reencuadre, no como mejora |
| 9 | Top-N mínimo para el 70 % (dev-A: N = 22) | 74,4 % (Top-22) | — | Llega al 70 %; plano +1,5 % [−0,4; +3,5] (no se distingue de 0), escalonado +9,5 % por ficha |
| 10 | Otras loterías (h−1) como fuente | O/E 0,87-0,90 | — | NO PASA (el control RD da 0,20, como se sabía) |

Lo que enseña la ronda 1:
- **ag12 queda respaldado fuera de muestra.** Sus pesos en sombra se ajustaron con todo el desarrollo; aquí se
  reajustó solo con dev-A y en dev-B sumó +25,5 mbits y +1,3 puntos de Top-15. Es lo mismo que ya corre en
  sombra como `ag12_rd`.
- Optimizar "directamente para el Top-15" (plan 5) es peor que modelar bien las probabilidades.
- Los árboles con 73 variables no superan a un término log-lineal de 35: no hay estructura escondida grande.

## 3. Rondas 2-4: buscar información nueva

**Ronda 2 (pre-registrada):** ¿el operador esquiva lo que más juega la gente?
| Prueba | dev-A O/E | dev-B O/E [IC 99,17 %] | Veredicto | Top-15 al sacarlo |
|---|---|---|---|---|
| A1: número = día del mes | 0,71 | **0,51 [0,35; 0,68]** | **PASA** | +0,44 pp |
| A2: número = hora (reloj de 12 h) | 0,91 | **0,64 [0,46; 0,83]** | **PASA** | +0,16 pp |
| A3: los mismos animales salen poco siempre | ρ = +0,33, p = 0,023 | | NO PASA (por poco) | |

Placebos en todo el desarrollo de LA (para descartar un artefacto). Del día del mes con un corrimiento s:
s = −1 0,87; **s = 0 0,61; s = +1 0,66**; s = +2 0,87; el resto, entre 0,97 y 1,15. La hora en 12 h
da 0,78; en 24 h, por la tarde, da 1,10 (nada). Es decir, el efecto está en "el número que la gente asocia a hoy
y a esta hora", no en números vecinos.

**Ronda 3 (pre-registrada): réplicas en juegos nunca mirados para esto.** Criterio para "todo el operador":
D0 o D1 replicado en RD **y** en LARD → **NO CONFIRMADA**, porque LARD no lo muestra (LARD tampoco tiene el
"no repetir" de LA: se comporta como azar puro).
| Juego | D0 (día) | D1 (día+1) | H12 (hora) |
|---|---|---|---|
| RD Internacional (mismo operador) | **0,78 [0,62; 0,96]** se replica | 0,87 | 0,88 |
| LARD (mismo operador) | 0,96 | 1,07 | 0,97 |
| La Granjita (otro operador) | **0,47 [0,23; 0,73]** | 0,89 | 1,00 |
| Selva Plus (otro operador) | **0,68 [0,41; 0,95]** | **0,64 [0,38; 0,91]** | 0,89 |
| Guácharo (otro operador) | **0,32 [0,09; 0,64]** | 0,73 | 0,70 |

**Corrección por exposición en LA** (descriptivo: las variables se eligieron viendo todo el desarrollo).
Sobre P6, multiplicadores ajustados en dev-A: día−1 ×0,88, día ×0,82, día+1 ×0,75, día+2 ×0,98,
hora ×0,96, mes ×0,90. En dev-B da Top-15 **57,67 %** (+0,79 [+0,22; +1,39] sobre P6; +2,13 sobre B1) y
+6,1 mbits sobre P6.

**Ronda 4 (pre-registrada): "La Pirámide de Hoy".** Una sola variante (las páginas que la publican están
bloqueadas desde aquí). Punta: LA dev-B 0,57, pero RD 0,96 → **NO PASA**. Pares: 0,84 y 1,01 → **NO PASA**.

## 4. Cómo seguir atacando (en orden de valor)

1. **[HECHO el 2026-10-01, se mide desde el 10-02 en `/api/sombra` → `exposicion`; criterio en `PREREGISTRO_sombra_exposicion.md`] Poner en sombra "ag12_rd + exposición"** (fecha, fecha+1, hora). Es lo único que sube el Top-15 por sorteo
   y tiene respaldo fuera de muestra. ag12_rd ya corre en sombra; habría que añadir los tres multiplicadores en
   `herramientas/modelos/ag12/sombra.py` y en `/api/sombra`. Eso toca el servidor y necesita tu OK.
   Juez: el marcador en vivo, con el criterio fijado antes, como el de ag12. En dev-B la exposición sumó
   +6,1 mbits sobre P6, con una dispersión de 74,8 por sorteo. Con 80 % de potencia hacen falta **~930
   sorteos (~78 días)** para verlo. Si el efecto real fuera la mitad, harían falta ~3.800. Para ver los +0,8 pp
   de Top-15 hacen falta ~3.150 sorteos (~9 meses). Por eso se decide en mbits, no en aciertos.
2. **[HECHO el 2026-10-01: `scraping/datos_publicados.py` guarda cada mañana entre 6:00 y 7:55 seis páginas de datos en el volumen; se ve en `/api/datos_publicados`] Fuente nueva: los "datos" que publica la gente.** Si los operadores esquivan lo más jugado (la fecha lo
   sugiere en 5 loterías), lo que recomiendan los pronosticadores populares (foros como El Grupo Sortario, las
   pirámides de tuazar.com y juegoactivo.com) también debería salir menos. Plan: que Railway, que sí tiene
   internet, guarde cada mañana los datos publicados antes del primer sorteo. Después de ~2 meses se prueba
   con el mismo protocolo (pre-registro, O/E contra el ensamble, réplica en RD). Es la única vía que podría
   aportar decenas de mbits. Aun así, no se espera que llegue al 70 %.
3. **Si lo que importa es "cobrar seguido": Top-22 escalonado en sombra, sin plata.** En dev-B no pierde en
   3 de cada 4 sorteos y da +9,5 % por ficha. En 2026 el motor rinde menos y ese número bajará. Hay que medirlo
   en vivo antes de poner plata. El Top-15 ponderado sigue dando más por ficha (+18 % en dev-B), pero cobra
   solo el 56 % de las veces.
4. **Las 8:00:** la mejor hora (60,5 % en desarrollo, 61,1 % en dev-B), pero 1 sorteo al día y con IC ancho.
   Se sigue en vivo con la H1 de `PREREGISTRO_manana_8am.md`, leyendo su fe de erratas.
5. **No insistir** en: excluir más cosas de RD (plan 2), modelos más flexibles o árboles (planes 4-5), elegir
   horas o sorteos "calientes" (plan 7 y hilo 6), otras loterías como fuente (plan 10), ni la pirámide.

## 5. Límites declarados
- dev-B ya se usó una vez para cada plan de la ronda 1. Las combinaciones posteriores (B-comb, exposición) son
  descriptivas y su confirmación tiene que venir del marcador en vivo.
- El mecanismo de la regla RD salió de H4b (filas ≥ 9357 de LA) y los pesos congelados de ag12 se ajustaron con
  todo el desarrollo. Aquí ag12 se reajustó solo con dev-A, y nada se midió en filas ≥ 9357.
- No se pudo leer el marcador en vivo desde este equipo (el proxy bloquea el dominio de Railway).
- LARD no replica la fecha. Si el efecto fuera de "todo el operador", debería verse; por eso la regla queda
  como hipótesis de LA y RD, a confirmar en vivo.

## 6. Auditoría (subagente `revisor-sesgo`, 2026-10-01) y lo que se corrigió
**No hay fuga de información futura.** La auditoría barajó el futuro desde 4 cortes (incluido el borde de dev-B)
y nada de lo anterior cambió: variables, pesos, rondas, temperatura, desfases, horas y N*. Una corrida
independiente reproduce `salida.txt` byte a byte. Los 10 NO PASA de la ronda 1 se sostienen. Lo que señaló:
- **Los niveles de dev-B son optimistas.** Los modelos del ensamble y las 33 variables de ag12 se diseñaron
  mirando todo el desarrollo, incluido dev-B. Por eso el 55,0 % de B0, el 74,4 % del Top-22, el 79,8 % de dos
  sorteos y la ventaja de P6 salen algo inflados. En 2026 todo rinde menos (ensamble ~49-50 %).
- **El plan 10 miró resultados de LA del tramo de prueba** (2026-04..09). Ya está anotado en
  `herramientas/registro_final.jsonl`. Nada se eligió con eso.
- **Veredicto del plan 9 corregido.** El Top-22 llega al 70 %, pero su retorno plano (+1,5 %, IC [−0,4; +3,5])
  no se distingue de 0. Antes decía "y gana".
- **Fechas corridas en el historial congelado** (155 filas del desarrollo, sobre todo feriados y las primeras
  8:00 de nov-2024). `robustez_fechas.py` repite A1 y A2 con las fechas corregidas: A1 da O/E 0,72 en dev-A y
  **0,50 en dev-B**, A2 0,91 y 0,64, y día+1 0,66. **La señal de la fecha no depende de ese error.**
- Desviaciones del pre-registro, ninguna ajustada en dev-B:
  - P3 usa dos multiplicadores, "hoy LA" y "hoy RD", en vez de uno.
  - P4 añade lambda_l2 = 1, bagging 0,8 y tres variables (la_veces_ayer, rd_hueco, hay_rd). El ensamble entra
    como log P y no como logit, y falta el penúltimo hueco en días.
  - El umbral de 56 % del plan 7 se fijó después de haber visto las horas en todo el desarrollo.
  - El IC del plan 10 es al 99,5 %, más estricto que el 98,75 % que pedía Bonferroni por 4.
- Arreglos de código: los pares del plan 8 exigen ahora hora consecutiva (no cambió ningún número). Las
  rondas 2-4 ya no reescriben las salidas de la ronda 1 al importarla.

## Archivos
- `PREREGISTRO.md`, `PREREGISTRO_ronda2.md`, `PREREGISTRO_ronda3.md`, `PREREGISTRO_ronda4.md`: las reglas,
  escritas antes de medir (sus huellas están en `registro.jsonl`).
- `top15_70.py` → `resultados.json`, `salida.txt` (los 10 planes).
- `ronda2.py`, `ronda3.py`, `ronda4.py` → `ronda*.json`, `salida_ronda*.txt`.
- `robustez_fechas.py` → `salida_robustez_fechas.txt` (A1/A2 con las fechas corregidas).
- Para reproducir: `pip install numpy scipy lightgbm` y luego `python herramientas/exploracion/top15_70/top15_70.py`
  (~10 s). Las rondas 2-4 se corren igual.
