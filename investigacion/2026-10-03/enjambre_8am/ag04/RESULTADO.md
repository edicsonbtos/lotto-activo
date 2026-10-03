VEREDICTO: NULO

# ag04 — Relación numérica/geométrica en la transición nocturna (primer sorteo)
Pregunta: ¿el ganador del primer sorteo de hoy (D) se relaciona de forma estructurada con (a) el 7 PM de ayer o
(b) el primer sorteo de ayer, más allá de lo que ya da `P_aj`? Pre-registro: `PREREGISTRO.md` (escrito antes de
correr nada). Script: `analisis.py dev` (~5 s). Post-hoc solo dev: `posthoc_union.py`.

## Qué se miró (dev; prueba y vivo NO se abrieron)
- 10 familias de conjuntos S(O) × 2 orígenes = 20 contrastes O/E contra P_aj. Familias: val ±1, val ±2 (círculo de 38
  con 00 = 37), espejo 37−n, dígitos invertidos (1↔10, 12↔21…), misma terminación, misma decena, misma suma de dígitos,
  rueda americana ±1 y ±2 (orden de `herramientas/exploracion/secuencia_tests.py`) y tablero 3×12 (vecinos ortogonales).
  En todas se excluye la identidad (D = O), que ya cubren el motor y el ×0,272.
- 4 chi² de la distribución (D−O) mod 38 (en número y en posición de rueda; 36 gl, sin la clase 0).
- Total: 24 contrastes pre-registrados (Bonferroni en dev: 0,0021). Post-hoc: la unión de las 10 familias por origen (2),
  y p con varianza binomial para los conjuntos grandes (mismos contrastes). Son 26 contrastes distintos.
- Nota sobre el tablero: el repo no tiene un tablero de apuestas propio. El reglamento dice "dispuestos en una ruleta",
  así que el tablero físico es la rueda (F8/F9). F10 usa la mesa estándar de ruleta americana como supuesto.
- Filas: dev 9:00 = 261, dev 8:00 = 367 (origen a); 261 / 366 (origen b). Se descartan los días cuyo "ayer" no tiene 7 PM
  o no tiene primer sorteo de la misma era. 'cal' = 179 filas, conteo crudo contra |S|/38.

## Tabla dev: O/E contra P_aj (9:00 | 8:00 | dev conjunto [IC 95 % Poisson], p bilateral) y cal crudo
| origen | familia | 9:00 O/E (O/E esp.) | 8:00 O/E | dev O/E [IC] | p | mismo signo | cal crudo |
|---|---|---|---|---|---|---|---|
| 7 PM | val ±1 | 1,01 (14/13,8) | 0,67 (13/19,3) | 0,82 [0,54; 1,19] | 0,33 | no | 0,96 |
| 7 PM | val ±2 | 1,21 (17/14,1) | 0,94 (19/20,1) | 1,05 [0,74; 1,46] | 0,80 | no | 0,74 |
| 7 PM | espejo | 0,87 (6/6,9) | 0,61 (6/9,9) | 0,71 [0,37; 1,25] | 0,29 | sí | 1,06 |
| 7 PM | invertido | 1,71 (4/2,3) | 0,00 (0/3,8) | 0,65 [0,18; 1,67] | 0,54 | no | 0,62 |
| 7 PM | terminación | 1,00 (19/18,9) | 0,75 (20/26,6) | 0,86 [0,61; 1,17] | 0,38 | no | 0,76 |
| 7 PM | decena | 0,95 (54/57,0) | 0,85 (69/80,8) | 0,89 [0,74; 1,06] | 0,22 | sí | 0,85 |
| 7 PM | suma dígitos | 1,16 (19/16,4) | 0,88 (21/23,8) | 1,00 [0,71; 1,36] | 1,00 | no | 1,07 |
| 7 PM | rueda ±1 | 0,92 (13/14,1) | 1,10 (21/19,1) | 1,03 [0,71; 1,43] | 0,93 | no | 0,85 |
| 7 PM | rueda ±2 | 0,71 (10/14,2) | 1,38 (27/19,5) | 1,10 [0,77; 1,51] | 0,62 | no | 1,38 |
| 7 PM | tablero | 1,07 (24/22,5) | 0,82 (26/31,7) | 0,92 [0,68; 1,22] | 0,63 | no | 0,85 |
| 1.º ayer | val ±1 | 1,07 (15/14,0) | 0,82 (16/19,5) | 0,92 [0,63; 1,31] | 0,75 | no | 1,06 |
| 1.º ayer | val ±2 | 0,86 (12/14,0) | 0,87 (17/19,4) | 0,87 [0,58; 1,24] | 0,50 | sí | 1,80 |
| 1.º ayer | espejo | 1,58 (11/6,9) | 0,88 (9/10,2) | 1,16 [0,71; 1,80] | 0,56 | no | 0,64 |
| 1.º ayer | invertido | 0,42 (1/2,4) | 0,91 (3/3,3) | 0,70 [0,19; 1,80] | 0,66 | sí | 0,00 |
| 1.º ayer | terminación | 0,68 (13/19,2) | 1,07 (29/27,1) | 0,91 [0,65; 1,22] | 0,58 | no | 0,97 |
| 1.º ayer | decena | 0,91 (52/57,3) | 0,94 (74/78,6) | 0,93 [0,77; 1,10] | 0,42 | sí | 1,03 |
| 1.º ayer | suma dígitos | 0,47 (8/17,0) | 0,96 (23/24,0) | 0,76 [0,51; 1,07] | 0,13 | sí | 1,23 |
| 1.º ayer | rueda ±1 | 1,15 (16/13,9) | 1,04 (21/20,2) | 1,09 [0,76; 1,50] | 0,66 | sí | 0,96 |
| 1.º ayer | rueda ±2 | 1,21 (17/14,0) | 1,03 (21/20,3) | 1,11 [0,78; 1,52] | 0,57 | sí | 0,42 |
| 1.º ayer | tablero | 0,75 (17/22,8) | 0,84 (27/32,1) | 0,80 [0,58; 1,08] | 0,15 | sí | 1,38 |

El p más bajo de los 20 es 0,13. Con varianza binomial (más justa en conjuntos grandes), el mínimo es 0,10.
Ninguno baja de 0,05 sin corregir, y en 12 de 20 las dos eras van en sentido contrario.

Diferencia (D−O) mod 38 (chi², 36 gl): 7 PM número p = 0,99, 7 PM rueda p = 0,32, 1.º número p = 0,70,
1.º rueda p = 0,88. Por era, todos los p van de 0,14 a 0,997. Las clases más desviadas no se repiten entre eras
con fuerza. El p = 0,99 (demasiado uniforme) es un extremo esperable entre 4 chi².

Post-hoc (unión de las 10 familias, ~18 animales "relacionados"): 7 PM O/E 0,93 (9:00 0,96, 8:00 0,91; z binomial −1,6,
p = 0,10); 1.º O/E 0,92 (9:00 0,87, 8:00 0,96; p = 0,07). En cal crudo da 0,95 y 1,07. Es un leve déficit sin
significancia, mirado después de ver la tabla. No se envía a prueba.

## Prueba / vivo
Por la regla pre-registrada (p_dev < 0,05 y mismo signo en las dos eras), hay **0 candidatos**. Prueba y vivo no se
tocaron, y no se gastó ninguno de los 3 contrastes de prueba. Por eso no hay mbits, Top-5/Top-15 ni retorno que reportar.
Cualquier multiplicador sería 1.

## Conclusión y recomendación
Las relaciones numéricas o geométricas entre la noche anterior (7 PM o primer sorteo de ayer) y el primer sorteo de hoy
son ruido una vez que se mide contra P_aj, igual que el Markov 38×38 general. La única estructura nocturna real
sigue siendo la identidad (primero de ayer ×0,272, ya en producción). **No cambiar nada en producción.** Añadir a ideas
cerradas: "vecinos/espejo/dígitos/decena/terminación/rueda/tablero y diferencia mod 38 en la transición hacia el primer
sorteo: nulo (24 contrastes, p mínimo 0,13 en dev)".
