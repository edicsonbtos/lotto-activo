# S2 (motor 0): motor nuevo desde cero para el Top-15 (sin PROD y sin RD dentro). Veredicto: DUDOSO

Pre-registro: `PREREGISTRO.md`, escrito antes de mirar resultados y sin cambios. Código: `rasgos_s2.py` y `hacer_rasgos.py`
(rasgos y su prueba de fuga), `motor_s2.py` (walk-forward), `eval_s2.py` (acierto y plata con la regla RD), `elegir.py`,
`ensamblar.py`, `fuga.py`, `final.py` → `salida_final.txt`, `final.json`.
Matriz: `<scratchpad>/motor0_S2.npz`. Contiene `P` (10744×38, S2 solo) y `P_mezcla075` (S2 mezclado con PROD, w = 0,75).

## Qué es
- **Rasgos (37), todos de sorteos anteriores.** Son los 31 de M4 sin rd1, rd2 ni hay_rd: retrasos, hoy, ayer, d−2, d−3,
  frecuencias, primer sorteo de ayer y de d−3, número de la fecha, de fecha+1, de la hora y del mes, hora, día de la
  semana, y el régimen (repeticiones y reciclaje de hoy, de este día de la semana en 8 semanas y de los últimos 7 días).
  A eso se suman 6 rasgos nuevos:
  - número de fecha−1;
  - **par_evita**: cuántos de los animales que ya salieron hoy forman con el candidato un par del decil de menor lift,
    calculado con los 365 días previos al mes. Se añade también el log-lift medio con los de hoy;
  - **prior de modo relajado**: q_prior, congelado antes de las 8:00, y q_post junto con el llr de hoy.
- **Cómo se calcula el modo relajado.** Hay dos modos generativos. En el normal, el peso de repetir un animal en el día es
  ρ = 0,24, calibrado con jul-dic-25 (AJUSTE). En el relajado, el sorteo es azar. Cada día pasado recibe una etiqueta
  blanda P(relajado | sus repeticiones). q_prior sale de una logística walk-forward, reajustada cada mes, sobre medias
  con olvido de esa etiqueta: el mismo día de la semana con vidas medias de 4 y 13 semanas, y todos los días con vida
  media de 7 días. q_post es la actualización bayesiana exacta con la secuencia de hoy. El prior encuentra solo el
  régimen de 2026: en ELECCION, mié 0,25, jue 0,24 y vie 0,30, frente a 0,16-0,19 el resto.
- **PROD y RD quedan fuera del modelo.** PROD solo sirve para comparar y para la mezcla. RD (h−1):30 se aplica después,
  con "quitar y subir" en todas las jugadas, y nunca a las 8:00.
- **Entrenamiento.** LightGBM (lr 0,05, 15 hojas, mínimo 400 filas por hoja, L2 = 10). Se reentrena el día 1 de cada
  mes, con parada temprana sobre los últimos 60 días y después un reajuste con todo el pasado. Los pesos tienen olvido.
- **Sin fuga.** Al alterar `seq[c:]`, los rasgos nuevos de las filas ≤ c no cambian. `A.chequear_fuga` da OK con el
  pipeline completo (rasgos recalculados, etiquetas y reentreno del mes) en los cortes 9100 y 11350. La matriz guardada
  coincide con ese pipeline (`salida_fuga.txt`).

## Objetivos (vida media de 180 días; Δ contra PROD; Top-15 con la regla RD, PROD = 55,6 / 50,1)
| variante | AJUSTE mbits Δ | AJUSTE Top-15 | ELECCION mbits Δ | ELECCION Top-15 |
|---|---|---|---|---|
| (a) A: softmax por sorteo | +175,5 Δ +14,8 | 55,4 | +90,5 Δ +11,5 | 52,1 |
| (b) B1: lambdarank NDCG@15 + calibración | +120,8 Δ **−40,0** | 51,8 | +54,2 Δ −24,8 | 48,3 |
| (b) B2: A + ajuste fino con la pérdida de cobertura del Top-15 | +169,0 Δ +8,2 | 55,1 | +87,4 Δ +8,4 | 51,2 |
| (c) C: mezcla de expertos normal/relajado, con q_post como compuerta | +176,6 Δ +15,8 | 55,6 | +88,9 Δ +9,8 | 52,4 |
| C, vida 90 días | +173,4 Δ +12,6 | 55,6 | **+90,8 Δ +11,7** | **52,5** |
| C, vida 365 días | +172,7 Δ +11,9 | 56,4 | +89,6 Δ +10,6 | 51,9 |

- **Los objetivos que optimizan el Top-15 directamente fallan otra vez.** Lambdarank pierde 40 mbits y casi 4 puntos.
  La pérdida de cobertura no mejora a la softmax. Se confirma lo de top15_70: hay que modelar bien la probabilidad.
- A, C-90, C-180 y C-365 empatan en mbits (diferencias < 3). La regla pre-registrada desempata por el Top-15 y elige
  **C con vida de 90 días**. La diferencia con A es ruido.
- Mezcla con PROD, p ∝ PROD^(1−w)·S2^w: en ELECCION, w = 0,5 y w = 0,75 dan +96,87 y +96,88 mbits. La regla elige
  **w = 0,75**.

## Final congelado (C, vida 90 días). Pareado contra PROD, ambos con la regla RD, IC 90 % por jornadas
| tramo | variante | Δ mbits | Top-15 (PROD) | Δ Top-15 en pp | T15 plano % (PROD) | T15 ponderado % (PROD) | T5 escalonado % (PROD) |
|---|---|---|---|---|---|---|---|
| AJUSTE | S2 solo | +12,6 [+0,2; +25,1] | 55,6 (55,6) | +0,04 [−1,5; +1,6] | +11,3 (+11,2) | +17,0 (+18,1) | +27,7 (+31,0) |
| AJUSTE | S2 mezclado, w = 0,75 | +21,2 [+11,9; +30,6] | 56,4 | +0,80 [−0,5; +2,1] | +12,8 | +19,0 | +30,6 |
| ELECCION | S2 solo | +11,7 [−3,6; +27,1] | 52,5 (50,1) | **+2,44 [+0,2; +4,7]** | +5,0 (+0,1) | +12,8 (+8,8) | +27,4 (+25,0) |
| ELECCION | S2 mezclado, w = 0,75 | +17,8 [+6,2; +29,5] | 51,9 | +1,87 [+0,0; +3,7] | +3,9 | +14,4 | +34,2 [Δ +9; IC −5; +23] |
| PRUEBA26* | S2 solo | +11,7 [−4,2; +27,5] | 53,4 (50,4) | +2,92 [+0,3; +5,5] | +6,7 (+0,9) | +11,0 (+5,9) | +19,2 (+15,3) |
| PRUEBA26* | S2 mezclado, w = 0,75 | +16,8 [+4,9; +28,7] | 54,3 | +3,87 [+1,4; +6,3] | +8,6 | +14,2 | +24,7 |

\* PRUEBA26 está **contaminada**: se miró una sola vez, con la versión ya congelada, y quedó registrada en
`motor2/registro_prueba26.jsonl`.

**Comparación con M4** (apilado sobre PROD):
- La versión final de M4 lleva RD dentro y no es desplegable. Da Top-15 +1,6 / +1,4 / +1,8 pp y +35 / +28 / +19 mbits
  en AJUSTE, ELECCION y PRUEBA26.
- La versión desplegable de M4 (V1 sin RD) da +1,5 / +0,9 / +0,8 pp y +27 / +7 / +1 mbits.
- **S2 supera a M4 sin RD en Top-15 en ELECCION y en PRUEBA26.** En AJUSTE queda por debajo.

**Fichas netas por día (ELECCION):**
| jugada | S2 mezclado | PROD |
|---|---|---|
| Top-15 ponderado | +39,8 | +24,3 |
| Top-15 plano | +7,0 | +0,3 |
| Top-5 escalonado | +32,8 | +24,0 |

La referencia (REF) es el Top-5 escalonado de PROD con la regla de cambio de RD, jugado en todos los sorteos. En retorno
por ficha, el Top-15 sigue muy por debajo de la REF (+25 %).

## Selector S1 (`selector_S1.npz`, sin reajustar; se juega si P̂ ≥ 0,50)
| jugada | AJUSTE | ELECCION | PRUEBA26* |
|---|---|---|---|
| jugar_PROD (se juega el 99 % de los sorteos en AJUSTE, el 41 % en ELECCION y el 22 % en PRUEBA26) | | | |
| · T15 ponderado de S2: retorno por ficha | +17 % | +21 % | +15 % |
| · T15 ponderado de S2: fichas netas por día | +47 | +24 | +9 |
| · lo mismo con el Top-15 de PROD: retorno por ficha | +18 % | +12 % | +3 % |
| jugar_M4, T15 ponderado de S2 mezclado: fichas netas por día | +51 | +30 | +40 |
| REF: retorno por ficha | +31 % | +25 % | +15 % |
| REF: fichas netas por día | +30 | +24 | +15 |

- El motor S2 mejora lo que el selector elige, porque gana justo en los días relajados que el selector tiende a saltarse.
- Por ficha, ninguna combinación supera a la REF de forma clara.

## Lectura adversarial
1. **La mejora está concentrada en un solo régimen.** En ELECCION, de mié a vie, S2 da +5,7 pp [+2,5; +8,9]; el resto de
   los días, +0,2. En AJUSTE, de mié a vie da −1,0. El motor aprende el modo relajado de 2026 a través del prior, y ese
   modo es justo el que se descubrió mirando 2026.
2. **AJUSTE no acompaña.** S2 solo empata con PROD en Top-15 (+0,04) y pierde 3 pp de retorno en el Top-5 escalonado.
   Solo la mezcla queda en positivo, y con un IC que cruza 0.
3. **La elección entre A, C y las vidas medias es casi ruido** (diferencias < 1 mbit). Con la regla, C-90 y w = 0,75.
   Con w = 0,5 el AJUSTE sale mejor (+1,4 pp [+0,3; +2,6]), pero esa w no fue la elegida.
4. **PRUEBA26 sale bien (+2,9 y +3,9 pp, con IC > 0), pero está contaminada.** El régimen de mié-vie y la regla de RD se
   descubrieron con 2026, y el diseño de los rasgos de régimen viene de ahí. No basta para declarar MEJORA.
5. **Desviaciones del pre-registro:**
   - Se usó una ventana de 600 días para ahorrar CPU.
   - ANTIGUO se calculó con reentreno trimestral; es solo informativo.
   - El CPU total fue de unos 48 min, por encima de los 40 previstos.
   - El historial de RD termina el 2026-09-22, así que la regla RD no se aplicó en las dos últimas semanas.

## VEREDICTO: DUDOSO
- Según la regla pre-registrada, el Top-15 supera a PROD en los dos tramos (ELECCION +2,4 pp, con IC > 0), pero en AJUSTE
  el IC cruza 0 (+0,04). Además, solo la mezcla con PROD mejora con claridad.
- Es el primer motor sin PROD que iguala o supera a PROD en mbits (+12 / +12) y en Top-15. También supera a M4 sin RD en
  2026. No es una mejora "por mucho".
- **Propuesta:** sombra en vivo de S2 mezclado con w = 0,75, con la regla RD aplicada al Top-15, juzgado por el acierto
  del Top-15 pareado contra PROD.
