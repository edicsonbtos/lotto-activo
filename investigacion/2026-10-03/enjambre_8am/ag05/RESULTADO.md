VEREDICTO: NULO

# ag05: la cadena de los primeros sorteos como serie propia

**Hipótesis.** El operador maneja el primer sorteo como una lista aparte: una bolsa sin reposición o un balanceo
de frecuencias entre primeros sorteos. Se usó la subserie de primeros sorteos indexada por día con sorteo:
183 filas de 'cal', 263 de dev a las 9:00 y 372 de dev a las 8:00. Todo se midió contra `P_aj`, salvo los conteos
crudos de cal+dev, que van contra 1/38. Se miraron **69 contrastes en dev**. Ninguno llegó a p < 0,01 con el mismo signo en
las dos eras. Por eso, siguiendo la regla pre-registrada, **no se envió ningún candidato a prueba**. Prueba y vivo
quedan sin mirar y no se gasta ninguno de los 30 contrastes del presupuesto común.

## (1) Evitación acumulada C_k (salió como primer sorteo en los últimos k primeros sorteos), O/E contra P_aj en dev
| k | 9:00 dev | 8:00 dev | dev [IC 95 %] | crudo cal+dev contra 1/38 |
|---|---|---|---|---|
| 1 | 0,80 (1/1,3) | 0,00 (0/1,1) | 0,42 [0,01; 2,32] | **0,09** (2/21,5) |
| 2 | 1,85 | 0,83 | 1,23 [0,81; 1,79] | 0,79 |
| 3 | 1,27 | 0,96 | 1,08 [0,81; 1,41] | 1,07 |
| 5 | 1,16 | 1,14 | 1,15 [0,92; 1,41] | 1,12 |
| 8 | 0,99 | 1,06 | 1,03 [0,86; 1,23] | 1,06 |
| 10 | 1,06 | 1,04 | 1,05 [0,89; 1,23] | 1,08 |
| 15 | 0,94 | 1,06 | 1,01 [0,88; 1,16] | 1,04 |

No hay evitación acumulada. Fuera de k = 1, que ya está en P_aj, la curva es plana en ≈ 1 y en crudo incluso
queda algo por encima de 1. Una bolsa sin reposición daría O/E ≪ 1 para todo k < 38.
Por posición exacta, contra P_aj en dev:

| posición | O/E | p |
|---|---|---|
| 1 | 0,42 | ya ajustada |
| 2 | 1,33 | 0,19. Por era: 2,03 a las 9:00 y 0,90 a las 8:00, inestable |
| 3 | 0,99 | ya ajustada |
| 4 | 1,13 | 0,67 |
| 5 | 1,33 | 0,22 |
| 6 | 0,66 | 0,19 |
| 8 | 1,34 | 0,19 |
| 10 | 1,31 | 0,25 |
| resto | 0,75 a 1,01 | — |

En crudo, la posición 2 da 1,49 y la 3 da 1,63, pero el motor ya las recoge.

## (2) Coleccionista: nº de primeros sorteos hasta ver los 38 animales (media sobre todos los arranques)
| serie | observado | azar | P_aj (1000 simulaciones) | P(sim ≤ obs) |
|---|---|---|---|---|
| dev 9:00 | 126,5 | — | — | 0,24 (azar) / 0,22 (P_aj) |
| dev 8:00 | 152,4 | — | — | 0,58 / 0,59 |
| dev completo | 135,2 | 155,9 | 157,4 | 0,10 / 0,09 |
| cal+dev (crudo) | 152,8 | 157,3 | — | 0,41 |

Las columnas "azar" y "P_aj" de las filas por era quedan vacías porque esas medias no se calcularon: con 263 o 372
sorteos, algunas series simuladas no llegan a juntar los 38 animales. Los valores p de esas filas sí son válidos.

Los animales distintos por ventana tampoco apoyan la hipótesis. En ventanas de 38 primeros sorteos salen 23,96
distintos, contra 24,15 bajo P_aj (P = 0,72), y en ventanas de 19 salen 14,95 contra 15,08. Una bolsa daría 38 y 19.
Hay **menos** variedad que por azar, no más. El T algo corto de dev no se repite en cal+dev ni dentro de cada era.

## (3) Balanceo por el nº de apariciones como primer sorteo en los últimos 38 o 76
| grupo | O/E dev | grupo | O/E dev |
|---|---|---|---|
| c38 = 0 | 1,00 | c76 = 0 | 0,94 |
| c38 = 1 | 1,01 | c76 = 1 | 1,04 |
| c38 = 2 | 1,00 | c76 = 2 | 1,02 |
| c38 ≥ 3 | 0,98 | c76 = 3 / ≥ 4 | 1,03 / 0,91 |

La tendencia log-lineal da b = +0,001 para c38 (p = 0,98) y −0,009 para c76 (p = 0,77). Las dos eras van en
signos opuestos. **Los "pocos" no salen más.**

## (4) Hueco entre apariciones del mismo animal como primer sorteo
En crudo (cal+dev, 780 huecos) la distribución sí difiere de la geométrica: χ² = 40,8 con 8 gl, p < 10⁻⁴. Todo el
efecto está en los huecos cortos:

| hueco | observado / esperado |
|---|---|
| 1 | 2 / 20,5 |
| 2 | 32 / 20,0 |
| 3 | 34 / 19,5 |
| 4-5 | 46 / 37,4 |
| 6-38 | sin desvío |

El hueco medio es 36,1, cerca del 38 esperado. Contra P_aj el riesgo por hueco queda plano:

| hueco | O/E |
|---|---|
| 1 | 0,42 |
| 2 | 1,33 |
| 3 | 0,96 |
| 4 | 1,06 |
| 5 | 1,44 (p = 0,12) |
| 6-10 | 0,94 |
| 11-20 | 1,07 |
| 21-38 | 0,89 |
| 39-76 | 1,03 |
| 77-152 | 0,92 |

Es decir, el motor más el ajuste de producción ya absorbe toda la estructura de huecos cortos.

## Mejor candidato de dev (no enviado)
El mejor candidato fue "salió como primer sorteo hace 2, 4 o 5". Da O/E 1,25 en dev (1,34 a las 9:00 y 1,20 a las
8:00, p = 0,089). Con ×1,25 suma **+3,8 mbits por primer sorteo [−3,4; +11,5] dentro de muestra**, con P(≤ 0) = 0,16.
Por era da +5,7 a las 9:00 y +2,4 a las 8:00. Con 69 contrastes miramos, es lo esperable por azar. No llega al umbral.

## Efecto en plata y recomendación
No hay ningún candidato, así que no cambia el Top-5 ni el Top-15. **No recomiendo nada para producción.** El primer
sorteo no se comporta como una lista propia con bolsa ni con balanceo. Su única memoria propia es la de corto alcance
(hace 1 día ≪ 1, hace 2-3 días > 1), que `P_aj` y `ensamble_v2` ya capturan. Más allá de 5 primeros sorteos la
cadena es indistinguible del azar.

Salvedad: con 635 filas en dev, la potencia para detectar efectos de O/E 0,9 en conjuntos grandes es modesta. Aun así,
una bolsa o un balanceo real darían efectos enormes (O/E ≪ 1 en C_k y 38 distintos por ventana), y eso está descartado.

Archivos (en esta carpeta):
- `comun.py`: subserie y rasgos, construidos solo con el pasado.
- `explorar_dev.py` → `explorar_dev.out`: 63 contrastes, 12 s.
- `extra_dev.py` → `extra_dev.out`: coleccionista con 1000 simulaciones y mejor candidato.
- `PREREGISTRO.md`, con su adenda escrita antes de prueba.
