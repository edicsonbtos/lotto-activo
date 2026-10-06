# A2: réplica sin motor de "mié-vie recicla menos" (2026-10-06)
Pre-registro: `PREREGISTRO.md`. Scripts: `replica.py` (pre-registrado, salida en `salida.txt`) y `explora.py` (POST-HOC,
salida en `salida_explora.txt`). Uso: `python3 replica.py <SP>`.
Métrica: el ganador ya salió en d−1 o d−2 (mismo juego). E = |S\T|/(N−|T|), donde T son los ya salidos hoy.
RR de Mantel-Haenszel por hora entre mié-vie y el resto; p por permutación de jornadas e IC por bootstrap de jornadas.

## Pre-registrado
| tramo | O/E mié-vie / resto | RR [IC95] | p unil. |
|---|---|---|---|
| LA dev 2024-25 | 1,17 / 1,07 | 1,09 [1,04; 1,14] | 1,00 |
| **LA 2026** | 1,02 / 1,20 | **0,85 [0,80; 0,91]** | 0,0002 |
| LA 2026 abr-sep | 1,04 / 1,17 | 0,89 [0,82; 0,96] | 0,002 |
| RD 2024-25 | 1,00 / 0,95 | 1,05 [1,00; 1,10] | 0,98 |
| RD 2026 | 1,05 / 1,03 | 1,02 [0,95; 1,09] | 0,74 |
| LARD 2025-S2 / 2026 | — | 1,08 / 0,99 [0,92; 1,05] | 0,97 / 0,33 |
| La Granjita 2026 | 0,89 / 1,03 | 0,86 [0,77; 0,96] | 0,002 |
| Selva Plus 2026 | 2,54 / 2,20 | 1,16 [1,01; 1,33] (al revés) | 0,98 |
| Guácharo 2026 | 1,26 / 1,36 | 0,92 [0,81; 1,05] | 0,11 |
| **Combinado de los 5 ciegos** | | **0,99 [0,95; 1,03]** | 0,25 |

- **Reproducción en LA: SÍ.** Sin motor, LA 2026 recicla un 15 % menos en mié-vie (en dev pasaba al revés: 1,09).
  No es un artefacto de la expectativa del motor. hist_0605 coincide con la API oficial en 5144 de 5148 sorteos.
- **Réplica ciega: NO.** Solo pasa 1 de 5 (La Granjita). Los dos juegos del mismo operador (RD y LARD) dan 1,00
  combinados, y el combinado de los 5 da 0,99 (p 0,25). Por el criterio pre-registrado, la réplica es **RUIDO**.

## Post-hoc (no pre-registrado): el control explica el patrón
- **Repetición en el mismo día** en LA 2026: mié-vie 0,67 contra el resto 0,31 (O/E contra el azar), RR 2,17,
  p 0,0003. El 9,3 % de los sorteos de mié-vie repite un animal de ese mismo día, contra el 4,4 % del resto.
  La API oficial lo confirma: 1,12 repeticiones por jornada en mié-vie contra 0,54 en el resto.
  Se mantiene en los 3 trimestres (0,81/0,32; 0,65/0,39; 0,57/0,23).
- **En dev, el día "permisivo" era el domingo**: en LA, RR 1,66 (p 0,0003); en RD, 2,20. Es justo el día en que el
  motor rendía mal en dev (O/E 0,82). Por meses, en LA el domingo deja de ser permisivo desde 2025-07, y mié-vie lo
  pasa a ser desde 2026-01 (con un adelanto en 2025-01/02). Parece un **régimen operativo que cambia de día** y que
  cuesta al motor porque este penaliza al que ya salió hoy.
- Aun así, entre los sorteos con un ganador nuevo en el día, LA 2026 mié-vie sigue reciclando menos (RR 0,87, p 0,0005).
  Son dos rasgos del mismo régimen.
- En RD 2026 hay un eco débil en el control (mié-vie RR 1,37, p 0,04), pero no aparece en el reciclaje. LARD no evita
  repetir en el día (control ≈ 1,0). La Granjita sube algo (1,21, p 0,04).
- En LA 2026, en mié-vie las repeticiones caen cerca (a 1-4 sorteos: 81 de 127), mientras que en el resto se reparten.

## Veredicto: DUDOSO
El patrón no es azar dentro de LA: aparece sin motor y en los datos oficiales. Pero no es un fenómeno general:
la réplica ciega pre-registrada falla (RUIDO fuera de LA). La explicación más probable es un régimen de LA que depende
del día de la semana (permite repetir en el mismo día), que antes caía en domingo y en 2026 cae en mié-vie. Como ya
cambió de día una vez, puede volver a cambiar, y se descubrió mirando. Hay que vigilar en vivo la tasa de repetición
en el mismo día por día de la semana, a partir del 2026-10-07. Si mié-vie sigue con O/E ≥ 0,55 frente a ≤ 0,35 en el
resto, merece una prueba de "no penalizar repetidos en mié-vie" (pre-registrada, con el motor congelado).
